import numpy as np
import polars as pl

from ctk_android.enums import (
    ClientId,
    Column,
    EligibilityReason,
    ExposureCondition,
    ExposureMode,
    FailureReason,
    SplitRole,
    ValidationCheck,
)
from ctk_android.types import (
    BoolArray,
    ArmKey,
    CtkError,
    ExposureSpec,
    FamilyName,
    IntArray,
    RowCount,
    Seed,
    Salt,
    StudyData,
    SupportCount,
    TargetPair,
    TrainingRows,
    ValidationRecord,
)


def family_masks(study: StudyData, families: tuple[FamilyName, ...]) -> dict[FamilyName, BoolArray]:
    table = study.table
    malware = table[Column.LABEL].to_numpy() == 1
    names = table[Column.FAMILY]
    return {family: malware & (names == family).to_numpy() for family in families}


def client_rows(study: StudyData, client: ClientId, role: SplitRole) -> IntArray:
    table = study.table
    mask = (table[Column.CLIENT] == client) & (table[Column.ROLE] == role)
    return np.flatnonzero(mask.to_numpy())


def training_orders(study: StudyData, seed: Seed, salt: Salt) -> TrainingRows:
    orders: TrainingRows = {}
    for index, client in enumerate(ClientId):
        rows = client_rows(study, client, SplitRole.FIT)
        rng = np.random.default_rng(np.random.SeedSequence([seed, salt, index]))
        orders[client] = rows[rng.permutation(rows.size)]
    return orders


def row_priorities(study: StudyData, seed: Seed, salt: Salt) -> np.ndarray:
    rng = np.random.default_rng(np.random.SeedSequence([seed, salt, len(ClientId)]))
    return rng.random(study.table.height)


def exposure_spec(
    arm: ArmKey,
    mode: ExposureMode,
    targets: tuple[TargetPair, ...],
) -> ExposureSpec:
    families = tuple(dict.fromkeys(pair.family for pair in targets))
    hide = mode is ExposureMode.HIDE_FROM_TARGET
    excluded: dict[ClientId, tuple[FamilyName, ...]] = {client: () for client in ClientId}
    if arm.condition is ExposureCondition.FAMILY_ABSENT_EVERYWHERE:
        excluded = {client: families for client in ClientId}
    elif hide and arm.condition is ExposureCondition.PEER_PRESENT:
        excluded = {
            client: tuple(pair.family for pair in targets if pair.client is client)
            for client in ClientId
        }
    dose_caps: dict[FamilyName, SupportCount] = {}
    dose_targets: dict[FamilyName, ClientId] = {}
    if arm.dose is not None and arm.condition is ExposureCondition.PEER_PRESENT:
        for pair in targets:
            dose_caps[pair.family] = arm.dose
            dose_targets[pair.family] = pair.client
    return ExposureSpec(excluded=excluded, dose_caps=dose_caps, dose_targets=dose_targets)


def allowed_dose_rows(
    study: StudyData,
    masks: dict[FamilyName, BoolArray],
    spec: ExposureSpec,
    priorities: np.ndarray,
) -> dict[FamilyName, BoolArray]:
    table = study.table
    fit = (table[Column.ROLE] == SplitRole.FIT).to_numpy()
    allowed: dict[FamilyName, BoolArray] = {}
    for family, cap in spec.dose_caps.items():
        target = spec.dose_targets[family]
        peer = (table[Column.CLIENT] != target).to_numpy()
        candidates = np.flatnonzero(masks[family] & fit & peer)
        ranked = candidates[np.argsort(priorities[candidates], kind="stable")][:cap]
        mask = np.zeros(table.height, dtype=bool)
        mask[ranked] = True
        allowed[family] = mask
    return allowed


def select_training(
    orders: TrainingRows,
    masks: dict[FamilyName, BoolArray],
    spec: ExposureSpec,
    allowed: dict[FamilyName, BoolArray],
    budget: RowCount,
) -> TrainingRows:
    selected: TrainingRows = {}
    for client, order in orders.items():
        keep = np.ones(order.size, dtype=bool)
        for family in spec.excluded[client]:
            keep &= ~masks[family][order]
        for family, permitted in allowed.items():
            if family not in spec.excluded[client]:
                keep &= ~masks[family][order] | permitted[order]
        selected[client] = order[keep][:budget]
    return selected


def exposure_counts(
    study: StudyData,
    training: TrainingRows,
    masks: dict[FamilyName, BoolArray],
    arm: ArmKey,
) -> pl.DataFrame:
    rows = [
        {
            Column.LEARNER: arm.learner,
            Column.CONDITION: arm.condition,
            Column.DOSE: -1 if arm.dose is None else arm.dose,
            Column.CLIENT: client,
            Column.FAMILY: family,
            Column.ROWS: int(mask[selected].sum()),
            Column.TRAIN_ROWS: selected.size,
        }
        for client, selected in training.items()
        for family, mask in masks.items()
    ]
    return pl.DataFrame(rows)


def validate_exposure(
    study: StudyData,
    training: dict[ArmKey, TrainingRows],
    masks: dict[FamilyName, BoolArray],
    targets: tuple[TargetPair, ...],
    mode: ExposureMode,
    peer_min_fit: SupportCount,
    fit_pool: TrainingRows,
) -> list[ValidationRecord]:
    roles = study.table[Column.ROLE].to_numpy()
    hidden_zero = True
    peer_present = True
    absent_zero = True
    sizes: dict[ClientId, set[int]] = {client: set() for client in ClientId}
    only_fit = True
    for arm, per_client in training.items():
        for client, rows in per_client.items():
            sizes[client].add(rows.size)
            only_fit &= bool((roles[rows] == SplitRole.FIT).all())
        if arm.condition is ExposureCondition.PEER_PRESENT and mode is ExposureMode.HIDE_FROM_TARGET:
            for pair in targets:
                hidden_zero &= not bool(masks[pair.family][per_client[pair.client]].any())
                if arm.dose is None:
                    peers = sum(
                        int(masks[pair.family][rows].sum())
                        for client, rows in per_client.items()
                        if client is not pair.client
                    )
                    available = sum(
                        int(masks[pair.family][rows].sum())
                        for client, rows in fit_pool.items()
                        if client is not pair.client
                    )
                    peer_present &= peers > 0 and available >= peer_min_fit
        if arm.condition is ExposureCondition.FAMILY_ABSENT_EVERYWHERE:
            for pair in targets:
                absent_zero &= not any(
                    bool(masks[pair.family][rows].any()) for rows in per_client.values()
                )
    matched = all(len(values) == 1 for values in sizes.values())
    return [
        ValidationRecord(
            check=ValidationCheck.HIDDEN_FAMILY_ABSENT_FROM_TARGET,
            passed=hidden_zero,
            detail="target training exposure to hidden families is zero",
        ),
        ValidationRecord(
            check=ValidationCheck.PEER_FAMILY_PRESENT,
            passed=peer_present,
            detail=f"peer support >= {peer_min_fit} in fit pool and present in training",
        ),
        ValidationRecord(
            check=ValidationCheck.FAMILY_ABSENT_EVERYWHERE,
            passed=absent_zero,
            detail="target families absent from every client in the absent-everywhere arms",
        ),
        ValidationRecord(
            check=ValidationCheck.SAMPLE_SIZE_MATCHED,
            passed=matched,
            detail=f"per-client training sizes {sorted(map(sorted, sizes.values()))}",
        ),
        ValidationRecord(
            check=ValidationCheck.TRAINING_EXCLUDES_TEST,
            passed=only_fit,
            detail="all training rows belong to the fit role",
        ),
    ]


def require_targets(targets: tuple[TargetPair, ...]) -> None:
    if not targets:
        raise CtkError(FailureReason.NO_ELIGIBLE_TARGETS, "no eligible target client-family pairs")


NAMED = EligibilityReason.ELIGIBLE
