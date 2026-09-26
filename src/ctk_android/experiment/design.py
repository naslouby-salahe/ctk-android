from dataclasses import dataclass

import numpy as np
import polars as pl
from numpy.random import Generator

from ctk_android import logs
from ctk_android.analysis.extensions import family_relatedness, known_family_centroids
from ctk_android.config import Config
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    Aggregation,
    ClientId,
    Column,
    DetailMessage,
    DrawStream,
    EligibilityReason,
    ErrorMessage,
    ExperimentDesign,
    ExposureCondition,
    ExposureMode,
    FailureReason,
    Learner,
    LibraryOption,
    LogEvent,
    LogField,
    SplitRole,
    TunedParameter,
    ValidationCheck,
)
from ctk_android.experiment import evaluation, training
from ctk_android.experiment.training import learner_stream
from ctk_android.logs import Stopwatch
from ctk_android.types import (
    AggregationRule,
    ArmKey,
    ArmResult,
    ClientPieces,
    ClientPools,
    ClientRowCounts,
    CtkError,
    DesignSetting,
    DoseCaps,
    DoseDraw,
    DoseRequest,
    DoseTargets,
    ExcludedFamilies,
    ExperimentSpec,
    ExposureRow,
    ExposureSpec,
    ExposureTable,
    FamilyFitRows,
    FamilyMasks,
    FamilyName,
    FamilyRows,
    FamilyRowTotals,
    LevelRows,
    LogFields,
    MalwareRowsTable,
    Passed,
    PlaceboChoice,
    PlaceboOption,
    PlaceboPairRow,
    Priorities,
    RandomSeed,
    ResultsByArm,
    RowCount,
    RowIndices,
    RunKey,
    Salt,
    StudyData,
    SupportCount,
    Table,
    TargetPair,
    TrainingByArm,
    TrainingRows,
    TrainingSizes,
    TuningPoint,
    ValidationRecord,
)


def family_masks(study: StudyData, families: tuple[FamilyName, ...]) -> FamilyMasks:
    table = study.table
    malware = table[Column.LABEL].to_numpy() == 1
    names = table[Column.FAMILY]
    return {family: malware & (names == family).to_numpy() for family in families}


def client_rows(study: StudyData, client: ClientId, role: SplitRole) -> RowIndices:
    table = study.table
    mask = (table[Column.CLIENT] == client) & (table[Column.ROLE] == role)
    return np.flatnonzero(mask.to_numpy())


def training_orders(study: StudyData, seed: RandomSeed, salt: Salt) -> TrainingRows:
    orders: TrainingRows = {}
    for index, client in enumerate(ClientId):
        rows = client_rows(study, client, SplitRole.FIT)
        rng = np.random.default_rng(np.random.SeedSequence([seed, salt, index]))
        orders[client] = rows[rng.permutation(rows.size)]
    return orders


def row_priorities(study: StudyData, seed: RandomSeed, salt: Salt) -> Priorities:
    rng = np.random.default_rng(np.random.SeedSequence([seed, salt, len(ClientId)]))
    return rng.random(study.table.height)


def _excluded_families(
    arm: ArmKey, mode: ExposureMode, targets: tuple[TargetPair, ...]
) -> ExcludedFamilies:
    if arm.condition is ExposureCondition.FAMILY_ABSENT_EVERYWHERE:
        families = tuple(dict.fromkeys(pair.family for pair in targets))
        return dict.fromkeys(ClientId, families)
    if mode is ExposureMode.HIDE_FROM_TARGET and arm.condition is ExposureCondition.PEER_PRESENT:
        return {
            client: tuple(pair.family for pair in targets if pair.client is client)
            for client in ClientId
        }
    return dict.fromkeys(ClientId, ())


def exposure_spec(
    arm: ArmKey,
    mode: ExposureMode,
    targets: tuple[TargetPair, ...],
) -> ExposureSpec:
    dose_caps: DoseCaps = {}
    dose_targets: DoseTargets = {}
    if arm.dose is not None and arm.condition is ExposureCondition.PEER_PRESENT:
        for pair in targets:
            dose_caps[pair.family] = arm.dose
            dose_targets[pair.family] = pair.client
    return ExposureSpec(
        excluded=_excluded_families(arm, mode, targets),
        dose_caps=dose_caps,
        dose_targets=dose_targets,
    )


def allowed_dose_rows(
    study: StudyData,
    masks: FamilyMasks,
    spec: ExposureSpec,
    priorities: Priorities,
) -> FamilyMasks:
    table = study.table
    fit = (table[Column.ROLE] == SplitRole.FIT).to_numpy()
    allowed: FamilyMasks = {}
    for family, cap in spec.dose_caps.items():
        target = spec.dose_targets[family]
        peer = (table[Column.CLIENT] != target).to_numpy()
        candidates = np.flatnonzero(masks[family] & fit & peer)
        ranked = candidates[np.argsort(priorities[candidates], kind=LibraryOption.SORT_STABLE)][
            :cap
        ]
        mask = np.zeros(table.height, dtype=bool)
        mask[ranked] = True
        allowed[family] = mask
    return allowed


def select_training(
    orders: TrainingRows,
    masks: FamilyMasks,
    spec: ExposureSpec,
    allowed: FamilyMasks,
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
    training: TrainingRows,
    masks: FamilyMasks,
    arm: ArmKey,
) -> ExposureTable:
    return records_to_frame(
        [
            ExposureRow(
                **arm.columns().model_dump(),
                client=client,
                family=family,
                rows=mask[selected].sum().item(),
                train_rows=selected.size,
            )
            for client, selected in training.items()
            for family, mask in masks.items()
        ]
    )


def _hidden_absent(
    per_client: TrainingRows, masks: FamilyMasks, targets: tuple[TargetPair, ...]
) -> Passed:
    return all(not masks[pair.family][per_client[pair.client]].any().item() for pair in targets)


def _peer_supported(
    per_client: TrainingRows,
    masks: FamilyMasks,
    targets: tuple[TargetPair, ...],
    fit_pool: TrainingRows,
    peer_min_fit: SupportCount,
) -> Passed:
    def peer_rows(pool: TrainingRows, pair: TargetPair) -> RowCount:
        return sum(
            masks[pair.family][rows].sum().item()
            for client, rows in pool.items()
            if client is not pair.client
        )

    return all(
        peer_rows(per_client, pair) > 0 and peer_rows(fit_pool, pair) >= peer_min_fit
        for pair in targets
    )


def _absent_everywhere(
    per_client: TrainingRows, masks: FamilyMasks, targets: tuple[TargetPair, ...]
) -> Passed:
    return not any(
        masks[pair.family][rows].any().item() for pair in targets for rows in per_client.values()
    )


def validate_exposure(
    study: StudyData,
    training: TrainingByArm,
    masks: FamilyMasks,
    targets: tuple[TargetPair, ...],
    mode: ExposureMode,
    peer_min_fit: SupportCount,
    fit_pool: TrainingRows,
) -> list[ValidationRecord]:
    roles = study.table[Column.ROLE].to_numpy()
    hidden_zero = True
    peer_present = True
    absent_zero = True
    sizes: TrainingSizes = {client: set() for client in ClientId}
    only_fit = True
    for arm, per_client in training.items():
        for client, rows in per_client.items():
            sizes[client].add(rows.size)
            only_fit &= (roles[rows] == SplitRole.FIT).all().item()
        if (
            arm.condition is ExposureCondition.PEER_PRESENT
            and mode is ExposureMode.HIDE_FROM_TARGET
        ):
            hidden_zero &= _hidden_absent(per_client, masks, targets)
            if arm.dose is None:
                peer_present &= _peer_supported(per_client, masks, targets, fit_pool, peer_min_fit)
        if arm.condition is ExposureCondition.FAMILY_ABSENT_EVERYWHERE:
            absent_zero &= _absent_everywhere(per_client, masks, targets)
    matched = all(len(values) == 1 for values in sizes.values())
    return [
        ValidationRecord(
            check=ValidationCheck.HIDDEN_FAMILY_ABSENT_FROM_TARGET,
            passed=hidden_zero,
            detail=DetailMessage.HIDDEN_ZERO,
        ),
        ValidationRecord(
            check=ValidationCheck.PEER_FAMILY_PRESENT,
            passed=peer_present,
            detail=DetailMessage.PEER_SUPPORT.format(minimum=peer_min_fit),
        ),
        ValidationRecord(
            check=ValidationCheck.FAMILY_ABSENT_EVERYWHERE,
            passed=absent_zero,
            detail=DetailMessage.ABSENT_EVERYWHERE,
        ),
        ValidationRecord(
            check=ValidationCheck.SAMPLE_SIZE_MATCHED,
            passed=matched,
            detail=DetailMessage.SIZES.format(sizes=sorted(map(sorted, sizes.values()))),
        ),
        ValidationRecord(
            check=ValidationCheck.TRAINING_EXCLUDES_TEST,
            passed=only_fit,
            detail=DetailMessage.FIT_ONLY,
        ),
    ]


def _named_malware(study: StudyData) -> MalwareRowsTable:
    return (
        study.table.with_row_index(Column.ROW_POSITION)
        .filter((pl.col(Column.LABEL) == 1) & (pl.col(Column.REASON) == EligibilityReason.ELIGIBLE))
        .select(Column.ROW_POSITION, Column.CLIENT, Column.FAMILY, Column.ROLE)
    )


def family_fit_rows(study: StudyData) -> FamilyFitRows:
    grouped = (
        _named_malware(study)
        .filter(pl.col(Column.ROLE) == SplitRole.FIT)
        .group_by(Column.FAMILY, Column.CLIENT)
        .agg(pl.col(Column.ROW_POSITION))
    )
    rows: FamilyFitRows = {}
    for record in grouped.iter_rows(named=True):
        rows.setdefault(record[Column.FAMILY], {})[ClientId(record[Column.CLIENT])] = np.sort(
            np.asarray(record[Column.ROW_POSITION], dtype=np.int64)
        )
    return rows


def family_totals(study: StudyData) -> FamilyRowTotals:
    counted = _named_malware(study).group_by(Column.FAMILY).agg(pl.len().alias(Column.ROWS))
    return dict(zip(counted[Column.FAMILY].to_list(), counted[Column.ROWS].to_list(), strict=True))


def _peer_rows(fit: FamilyFitRows, family: FamilyName, target: ClientId) -> TrainingRows:
    empty: RowIndices = np.empty(0, dtype=np.int64)
    return {
        client: fit.get(family, {}).get(client, empty)
        for client in ClientId
        if client is not target
    }


def draw_dose(
    fit: FamilyFitRows, base: TrainingRows, targets: tuple[TargetPair, ...], rng: Generator
) -> DoseDraw:
    pooled: FamilyRows = {}
    owners: FamilyRows = {}
    clients = list(ClientId)
    for pair in targets:
        peers = _peer_rows(fit, pair.family, pair.client)
        rows = np.concatenate(list(peers.values()))
        holder = np.concatenate(
            [np.full(part.size, clients.index(client)) for client, part in peers.items()]
        )
        order = rng.permutation(rows.size)
        pooled[pair.family] = rows[order]
        owners[pair.family] = holder[order]
    return DoseDraw(
        pooled=pooled,
        owners=owners,
        replacement_order={client: rng.permutation(rows.size) for client, rows in base.items()},
    )


def dose_extras(
    draw: DoseDraw, targets: tuple[TargetPair, ...], dose: SupportCount
) -> TrainingRows:
    clients = list(ClientId)
    parts: ClientPieces = {client: [] for client in clients}
    for pair in targets:
        rows, holder = draw.pooled[pair.family][:dose], draw.owners[pair.family][:dose]
        for index, client in enumerate(clients):
            parts[client].append(rows[holder == index])
    return {
        client: np.concatenate(pieces) if pieces else np.empty(0, dtype=np.int64)
        for client, pieces in parts.items()
    }


def substitute(base: TrainingRows, extras: TrainingRows, order: TrainingRows) -> TrainingRows:
    result: TrainingRows = {}
    for client, rows in base.items():
        added = extras[client]
        replaced = rows.copy()
        replaced[order[client][: added.size]] = added
        result[client] = replaced
    return result


def _counts(masks: FamilyMasks, peer: TrainingRows, pair: TargetPair) -> ClientRowCounts:
    return {
        client: masks[pair.family][rows].sum().item()
        for client, rows in peer.items()
        if client is not pair.client
    }


def _available(
    fit: FamilyFitRows, base: TrainingRows, family: FamilyName, target: ClientId
) -> TrainingRows:
    return {
        client: np.setdiff1d(rows, base[client])
        for client, rows in _peer_rows(fit, family, target).items()
    }


def _allocate(counts: ClientRowCounts, free: TrainingRows) -> ClientRowCounts:
    allocated = {client: min(count, free[client].size) for client, count in counts.items()}
    remaining = sum(counts.values()) - sum(allocated.values())
    for client in allocated:
        moved = min(free[client].size - allocated[client], remaining)
        allocated[client] += moved
        remaining -= moved
    return allocated


def _hidden_fit(fit: FamilyFitRows, pair: TargetPair) -> RowCount:
    return sum(rows.size for rows in _peer_rows(fit, pair.family, pair.client).values())


def choose_placebos(
    fit: FamilyFitRows,
    totals: FamilyRowTotals,
    masks: FamilyMasks,
    peer: TrainingRows,
    base: TrainingRows,
    targets: tuple[TargetPair, ...],
    minimum: SupportCount,
) -> tuple[PlaceboChoice, ...]:
    taken = {pair.family for pair in targets}
    choices: list[PlaceboChoice] = []
    for pair in sorted(targets, key=lambda item: (-_hidden_fit(fit, item), item.family)):
        counts = _counts(masks, peer, pair)
        need: RowCount = sum(counts.values())
        hidden_fit = _hidden_fit(fit, pair)
        options: list[PlaceboOption] = []
        for family in sorted(totals):
            if family in taken or totals[family] < minimum:
                continue
            free = _available(fit, base, family, pair.client)
            if sum(rows.size for rows in free.values()) >= need:
                peer_fit = sum(rows.size for rows in _peer_rows(fit, family, pair.client).values())
                options.append(
                    PlaceboOption(
                        distance=abs(peer_fit - hidden_fit), family=family, peer_fit=peer_fit
                    )
                )
        if not options:
            raise CtkError(
                FailureReason.NO_ELIGIBLE_TARGETS,
                ErrorMessage.NO_PLACEBO.format(family=pair.family, need=need),
            )
        best = min(options, key=lambda option: (option.distance, option.family))
        taken.add(best.family)
        allocated = _allocate(counts, _available(fit, base, best.family, pair.client))
        choices.append(
            PlaceboChoice(
                client=pair.client,
                family=pair.family,
                placebo=best.family,
                counts=counts,
                allocated=allocated,
                reallocated=sum(
                    max(allocated[client] - count, 0) for client, count in counts.items()
                ),
                hidden_peer_fit=hidden_fit,
                placebo_peer_fit=best.peer_fit,
            )
        )
    return tuple(choices)


def placebo_extras(
    fit: FamilyFitRows,
    base: TrainingRows,
    choices: tuple[PlaceboChoice, ...],
    rng: Generator,
) -> TrainingRows:
    parts: ClientPieces = {client: [] for client in ClientId}
    for choice in choices:
        free = _available(fit, base, choice.placebo, choice.client)
        for client, count in choice.allocated.items():
            parts[client].append(rng.permutation(free[client])[:count])
    return {
        client: np.concatenate(pieces) if pieces else np.empty(0, dtype=np.int64)
        for client, pieces in parts.items()
    }


@dataclass(frozen=True)
class DesignArms:
    arms: ResultsByArm
    trainings: TrainingByArm
    checks: tuple[ValidationRecord, ...]
    placebo: Table | None


@dataclass(frozen=True)
class DesignInputs:
    spec: ExperimentSpec
    config: Config
    key: RunKey
    context: training.TrainingContext
    study: StudyData
    masks: FamilyMasks
    pools: ClientPools
    orders: TrainingRows
    targets: tuple[TargetPair, ...]
    budget: SupportCount


def run_fields(key: RunKey) -> LogFields:
    return {
        LogField.EXPERIMENT: key.experiment,
        LogField.MODE: key.mode,
        LogField.SEED: key.seed,
        LogField.SALT: key.salt,
    }


def aggregation_rule(kind: Aggregation, trim_per_side: SupportCount) -> AggregationRule:
    return AggregationRule(rule=kind, trim_per_side=trim_per_side)


def _arm(
    learner: Learner,
    condition: ExposureCondition,
    dose: DoseRequest,
    aggregation: Aggregation | None,
) -> ArmKey:
    tuning = (
        None
        if aggregation is None
        else TuningPoint(parameter=TunedParameter.AGGREGATION, level=aggregation)
    )
    return ArmKey(learner=learner, condition=condition, dose=dose, tuning=tuning)


def _train(
    inputs: DesignInputs, arm: ArmKey, rows: TrainingRows, aggregation: Aggregation | None
) -> ArmResult:
    context = inputs.context
    watch = Stopwatch()
    stream = learner_stream(arm.learner)
    if arm.learner is Learner.CENTRAL:
        scorer = training.train_scorer(
            context, training.pooled_rows(rows), context.config.central_epochs, stream
        )
    else:
        rule = (
            None
            if aggregation is None
            else aggregation_rule(aggregation, inputs.config.experiments.robust_trim_per_side)
        )
        scorer = training.train_federated(context, rows, arm.learner, 0.0, stream, rule)
    logs.info(
        LogEvent.ARM_TRAINED,
        {
            **run_fields(inputs.key),
            LogField.ARM: arm.label(),
            LogField.TRAIN_ROWS: sum(chosen.size for chosen in rows.values()),
            LogField.SECONDS: watch.seconds(),
        },
    )
    return ArmResult(
        scores=evaluation.score_shared(scorer, inputs.study, inputs.pools),
        scorers=dict.fromkeys(ClientId, scorer),
    )


def _standard_rows(inputs: DesignInputs, condition: ExposureCondition) -> TrainingRows:
    base = ArmKey(learner=Learner.CENTRAL, condition=condition, dose=None)
    spec = exposure_spec(base, inputs.spec.exposure_mode, inputs.targets)
    return select_training(inputs.orders, inputs.masks, spec, {}, inputs.budget)


def _peer_rows_of(rows: TrainingRows, masks: FamilyMasks, pair: TargetPair) -> RowCount:
    return sum(
        masks[pair.family][chosen].sum().item()
        for client, chosen in rows.items()
        if client is not pair.client
    )


def _dose_checks(
    inputs: DesignInputs, levels: LevelRows, absent: TrainingRows
) -> tuple[ValidationRecord, ...]:
    masks, targets = inputs.masks, inputs.targets
    checks: list[ValidationRecord] = []
    for dose, rows in levels.items():
        realised: Passed = all(_peer_rows_of(rows, masks, pair) == dose for pair in targets)
        target_zero: Passed = all(
            not masks[pair.family][rows[pair.client]].any().item() for pair in targets
        )
        checks.append(
            ValidationRecord(
                check=ValidationCheck.EXACT_DOSE_REALISED,
                passed=realised,
                detail=DetailMessage.DOSE_REALISED.format(dose=dose),
            )
        )
        checks.append(
            ValidationRecord(
                check=ValidationCheck.EXACT_DOSE_TARGET_ZERO,
                passed=target_zero,
                detail=DetailMessage.DOSE_TARGET_ZERO.format(dose=dose),
            )
        )
    identical: Passed = (
        all(np.array_equal(levels[0][client], absent[client]) for client in ClientId)
        if 0 in levels
        else True
    )
    checks.append(
        ValidationRecord(
            check=ValidationCheck.DOSE_ZERO_IS_ABSENT,
            passed=identical,
            detail=DetailMessage.DOSE_ZERO_IS_ABSENT,
        )
    )
    return tuple(checks)


def _train_dose(inputs: DesignInputs) -> DesignArms:
    config, spec = inputs.config, inputs.spec
    peer = _standard_rows(inputs, ExposureCondition.PEER_PRESENT)
    absent = _standard_rows(inputs, ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    fit = family_fit_rows(inputs.study)
    seeds = [inputs.key.seed, inputs.key.salt, DrawStream.DOSE]
    draw = draw_dose(
        fit, absent, inputs.targets, np.random.default_rng(np.random.SeedSequence(seeds))
    )
    levels: LevelRows = {
        dose: substitute(
            absent,
            dose_extras(draw, inputs.targets, dose),
            draw.replacement_order,
        )
        for dose in config.experiments.exact_dose_levels
    }
    settings = [
        DesignSetting(
            condition=ExposureCondition.PEER_PRESENT, dose=None, aggregation=None, rows=peer
        ),
        DesignSetting(
            condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE,
            dose=None,
            aggregation=None,
            rows=absent,
        ),
        *(
            DesignSetting(
                condition=ExposureCondition.EXACT_DOSE, dose=dose, aggregation=None, rows=rows
            )
            for dose, rows in levels.items()
        ),
    ]
    arms: ResultsByArm = {}
    trainings: TrainingByArm = {}
    for setting in settings:
        for learner in spec.learners:
            arm = _arm(learner, setting.condition, setting.dose, None)
            arms[arm] = _train(inputs, arm, setting.rows, None)
            trainings[arm] = setting.rows
    return DesignArms(
        arms=arms,
        trainings=trainings,
        checks=_dose_checks(inputs, levels, absent),
        placebo=None,
    )


def _placebo_checks(
    inputs: DesignInputs,
    fit: FamilyFitRows,
    choices: tuple[PlaceboChoice, ...],
    rows: TrainingRows,
    absent: TrainingRows,
) -> tuple[ValidationRecord, ...]:
    hidden = {pair.family for pair in inputs.targets}
    placebos = [choice.placebo for choice in choices]
    valid: Passed = len(set(placebos)) == len(placebos) and not hidden & set(placebos)
    matched: Passed = True
    for client in ClientId:
        added = np.setdiff1d(rows[client], absent[client])
        pools = [fit[choice.placebo].get(client, np.empty(0, dtype=np.int64)) for choice in choices]
        expected = sum(choice.allocated.get(client, 0) for choice in choices)
        matched &= added.size == expected and np.isin(added, np.concatenate(pools)).all().item()
    hidden_zero: Passed = all(
        not inputs.masks[pair.family][chosen].any().item()
        for pair in inputs.targets
        for chosen in rows.values()
    )
    return (
        ValidationRecord(
            check=ValidationCheck.PLACEBO_COUNTS_MATCHED,
            passed=matched,
            detail=DetailMessage.PLACEBO_COUNTS,
        ),
        ValidationRecord(
            check=ValidationCheck.PLACEBO_FAMILY_VALID,
            passed=valid,
            detail=DetailMessage.PLACEBO_VALID,
        ),
        ValidationRecord(
            check=ValidationCheck.PLACEBO_HIDDEN_ABSENT,
            passed=hidden_zero,
            detail=DetailMessage.PLACEBO_HIDDEN_ZERO,
        ),
    )


def _placebo_table(
    inputs: DesignInputs, fit: FamilyFitRows, choices: tuple[PlaceboChoice, ...]
) -> Table:
    hidden = frozenset(pair.family for pair in inputs.targets)
    centroids = known_family_centroids(inputs.study, fit, hidden, inputs.config.experiments.novelty)
    rows: list[PlaceboPairRow] = []
    for choice in choices:
        related = family_relatedness(inputs.study, fit, centroids, choice)
        rows.append(
            PlaceboPairRow(
                client=choice.client,
                family=choice.family,
                placebo_family=choice.placebo,
                need=sum(choice.counts.values()),
                reallocated=choice.reallocated,
                hidden_peer_fit=choice.hidden_peer_fit,
                placebo_peer_fit=choice.placebo_peer_fit,
                centroid_distance=related.centroid_distance,
                nearest_known_distance=related.nearest_known_distance,
                placebo_rank=related.placebo_rank,
                known_families=related.known_families,
            )
        )
    return records_to_frame(rows)


def _placebo_settings(
    peer: TrainingRows, absent: TrainingRows, placebo: TrainingRows
) -> list[DesignSetting]:
    plain = [
        DesignSetting(condition=condition, dose=None, aggregation=None, rows=rows)
        for condition, rows in (
            (ExposureCondition.PEER_PRESENT, peer),
            (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, absent),
            (ExposureCondition.PLACEBO, placebo),
        )
    ]
    robust = [
        DesignSetting(condition=condition, dose=None, aggregation=rule, rows=rows)
        for rule in Aggregation
        for condition, rows in (
            (ExposureCondition.PEER_PRESENT, peer),
            (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, absent),
        )
    ]
    return [*plain, *robust]


def _train_placebo(inputs: DesignInputs) -> DesignArms:
    config = inputs.config
    peer = _standard_rows(inputs, ExposureCondition.PEER_PRESENT)
    absent = _standard_rows(inputs, ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    fit = family_fit_rows(inputs.study)
    choices = choose_placebos(
        fit,
        family_totals(inputs.study),
        inputs.masks,
        peer,
        absent,
        inputs.targets,
        config.experiments.placebo_min_malware_rows,
    )
    seeds = [inputs.key.seed, inputs.key.salt, DrawStream.PLACEBO]
    rng = np.random.default_rng(np.random.SeedSequence(seeds))
    order = {client: rng.permutation(rows.size) for client, rows in absent.items()}
    placebo = substitute(absent, placebo_extras(fit, absent, choices, rng), order)
    arms: ResultsByArm = {}
    trainings: TrainingByArm = {}
    for setting in _placebo_settings(peer, absent, placebo):
        arm = _arm(Learner.FEDAVG, setting.condition, None, setting.aggregation)
        arms[arm] = _train(inputs, arm, setting.rows, setting.aggregation)
        trainings[arm] = setting.rows
    return DesignArms(
        arms=arms,
        trainings=trainings,
        checks=_placebo_checks(inputs, fit, choices, placebo, absent),
        placebo=_placebo_table(inputs, fit, choices),
    )


def train_design_arms(inputs: DesignInputs) -> DesignArms:
    if inputs.spec.design is ExperimentDesign.EXACT_DOSE:
        return _train_dose(inputs)
    return _train_placebo(inputs)
