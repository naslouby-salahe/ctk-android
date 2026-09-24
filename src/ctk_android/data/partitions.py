import numpy as np
import polars as pl

from ctk_android.config import DataConfig
from ctk_android.data.cache import load_features
from ctk_android.data.families import (
    classify_labels,
    controlled_pairs,
    natural_pairs,
    permute_family_labels,
    role_counts,
)
from ctk_android.enums import (
    Artifact,
    Column,
    DetailMessage,
    ErrorMessage,
    FailureReason,
    FamilyLabelSource,
    Grouping,
    LibraryOption,
    SplitRole,
    Stage,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    ClientFitRowsTable,
    CtkError,
    FamilyName,
    GroupIds,
    IdentitiesTable,
    LabelledTable,
    PairTables,
    PartitionKey,
    PartitionResult,
    Rank,
    RoleSeries,
    RowCount,
    Seed,
    StudyData,
    ValidationRecord,
)


def assign_roles(
    group_ids: GroupIds, key: PartitionKey, attempt: Rank, config: DataConfig
) -> RoleSeries:
    group_count = group_ids.max(initial=-1).item() + 1
    rng = np.random.default_rng(np.random.SeedSequence([key.seed, key.salt, attempt]))
    position = np.empty(group_count, dtype=np.int64)
    position[rng.permutation(group_count)] = np.arange(group_count)
    group_rows = np.bincount(group_ids, minlength=group_count)
    order = np.argsort(position, kind=LibraryOption.SORT_STABLE)
    started = np.cumsum(group_rows[order]) - group_rows[order]
    fraction = started / group_ids.size
    fit_edge = config.partition.fit
    calibration_edge = fit_edge + config.partition.calibration
    role_of_ordered = np.where(fraction < fit_edge, 0, np.where(fraction < calibration_edge, 1, 2))
    role_of_group = np.empty(group_count, dtype=np.int64)
    role_of_group[order] = role_of_ordered
    codes = role_of_group[group_ids]
    role_order = list(SplitRole)
    return pl.Series(Column.ROLE, [role_order[code] for code in codes], dtype=pl.String)


def client_fit_rows(labelled: LabelledTable, roles: RoleSeries) -> ClientFitRowsTable:
    return (
        labelled.with_columns(roles.alias(Column.ROLE))
        .filter(pl.col(Column.ROLE) == SplitRole.FIT)
        .group_by(Column.CLIENT)
        .agg(pl.len().alias(Column.FIT_ROWS))
    )


def evaluate_partition(
    labelled: LabelledTable,
    roles: RoleSeries,
    families: tuple[FamilyName, ...],
    config: DataConfig,
    key: PartitionKey,
) -> PairTables:
    counts = role_counts(labelled, roles, families)
    fit_rows = client_fit_rows(labelled, roles)
    controlled = controlled_pairs(counts, fit_rows, config.eligibility[key.profile])
    natural = natural_pairs(
        counts,
        fit_rows,
        config.natural_scarcity.max_target_share,
        config.natural_scarcity.peer_min_fit,
        config.natural_scarcity.own_domain_min_test,
    )
    return PairTables(controlled=controlled, natural=natural)


def validate_partition(
    identities: IdentitiesTable, roles: RoleSeries, grouping: Grouping
) -> tuple[ValidationRecord, ...]:
    frame = identities.with_columns(roles.alias(Column.ROLE))

    def crossing(column: Column) -> RowCount:
        return (
            frame.group_by(column)
            .agg(pl.col(Column.ROLE).n_unique().alias(Column.ROWS))
            .filter(pl.col(Column.ROWS) > 1)
            .height
        )

    sha_cross = frame.group_by(Column.SHA256).agg(pl.col(Column.ROLE).n_unique().alias(Column.ROWS))
    sha_crossing = sha_cross.filter(pl.col(Column.ROWS) > 1).height
    component_column = Column.COMPONENT if grouping is Grouping.COMPONENT else Column.PACKAGE_ID
    feature_expected = grouping is Grouping.COMPONENT
    feature_crossing = crossing(Column.FEATURE_ID)
    return (
        ValidationRecord(
            check=ValidationCheck.PARTITION_SHA_DISJOINT,
            passed=sha_crossing == 0,
            detail=DetailMessage.CROSSING.format(crossing=sha_crossing),
        ),
        ValidationRecord(
            check=ValidationCheck.PARTITION_COMPONENT_DISJOINT,
            passed=crossing(component_column) == 0,
            detail=DetailMessage.GROUP_CROSSING.format(
                grouping=grouping, crossing=crossing(component_column)
            ),
        ),
        ValidationRecord(
            check=ValidationCheck.PARTITION_FEATURE_DISJOINT,
            passed=feature_crossing == 0 or not feature_expected,
            detail=DetailMessage.FEATURE_CROSSING.format(
                crossing=feature_crossing, enforced=feature_expected
            ),
        ),
    )


def build_partition(
    labelled: LabelledTable,
    identities: IdentitiesTable,
    group_ids: GroupIds,
    families: tuple[FamilyName, ...],
    key: PartitionKey,
    config: DataConfig,
) -> PartitionResult:
    best_score: RowCount = 0
    best_attempt: Rank = 0
    best_roles: RoleSeries | None = None
    for attempt in range(config.partition.attempts):
        roles = assign_roles(group_ids, key, attempt, config)
        tables = evaluate_partition(labelled, roles, families, config, key)
        score = (
            tables.controlled.filter(pl.col(Column.ELIGIBLE)).height
            + tables.natural.filter(pl.col(Column.ELIGIBLE)).height
        )
        if best_roles is None or score > best_score:
            best_score, best_attempt, best_roles = score, attempt, roles
    if best_roles is None:
        raise CtkError(FailureReason.NO_ELIGIBLE_TARGETS, ErrorMessage.PARTITION_ATTEMPTS)
    tables = evaluate_partition(labelled, best_roles, families, config, key)
    return PartitionResult(
        roles=best_roles,
        attempt=best_attempt,
        controlled=tables.controlled,
        natural=tables.natural,
        validations=validate_partition(identities, best_roles, key.grouping),
    )


def load_study(
    paths: Paths,
    key: PartitionKey,
    config: DataConfig,
    labels: FamilyLabelSource,
    permutation_offset: Seed,
) -> StudyData:
    assignments = pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    identities = pl.read_parquet(paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS))
    roles = pl.read_parquet(paths.partition_file(key, Artifact.ASSIGNMENTS))
    labelled = classify_labels(assignments, config)
    if labels is FamilyLabelSource.PERMUTED:
        labelled = permute_family_labels(labelled, key.seed, permutation_offset)
    group = Column.COMPONENT if key.grouping is Grouping.COMPONENT else Column.PACKAGE_ID
    table = (
        labelled.join(roles, on=Column.ROW)
        .join(identities.select(Column.ROW, group, Column.FEATURE_ID), on=Column.ROW)
        .rename({group: Column.COMPONENT})
        .sort(Column.ROW)
    )
    return StudyData(table=table, features=load_features(paths.cache_file(Artifact.FEATURES)))
