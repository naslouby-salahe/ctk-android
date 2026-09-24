import polars as pl

from ctk_android.enums import (
    Column,
    DoseLevel,
    EvaluationPopulation,
    ExposureCondition,
    LibraryOption,
)
from ctk_android.types import (
    Alpha,
    DoseCurveTable,
    DoseLevelTable,
    DoseRecallTable,
    EffectiveDoseCount,
    EffectiveDoseTable,
    ExposureTable,
    FamilyCountsTable,
    TargetsTable,
)


def _keys() -> list[Column]:
    return [Column.EXPERIMENT, Column.SEED, Column.SALT, Column.LEARNER, Column.DOSE, Column.FAMILY]


def dose_recall(families: FamilyCountsTable, alpha: Alpha) -> DoseRecallTable:
    return (
        families.filter(
            (pl.col(Column.ALPHA) == alpha)
            & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
            & (pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
            & (pl.col(Column.TRIALS) > 0)
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .select(*_keys(), Column.CLIENT, Column.RECALL)
    )


def effective_peer_dose(exposure: ExposureTable, targets: TargetsTable) -> EffectiveDoseTable:
    keys = [Column.EXPERIMENT, Column.SEED, Column.SALT, Column.FAMILY]
    target_clients = (
        targets.select(*keys, Column.CLIENT).unique().rename({Column.CLIENT: Column.TARGET_CLIENT})
    )
    return (
        exposure.filter(pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
        .join(target_clients, on=keys)
        .filter(pl.col(Column.CLIENT) != pl.col(Column.TARGET_CLIENT))
        .group_by(*_keys())
        .agg(pl.col(Column.ROWS).sum().alias(Column.EFFECTIVE_DOSE))
    )


def dose_curve(recalls: DoseRecallTable, effective: EffectiveDoseTable) -> DoseCurveTable:
    joined = recalls.join(effective, on=_keys(), how=LibraryOption.JOIN_LEFT, nulls_equal=True)
    zero = joined.filter(pl.col(Column.DOSE) == 0).select(
        Column.EXPERIMENT,
        Column.SEED,
        Column.SALT,
        Column.LEARNER,
        Column.FAMILY,
        pl.col(Column.RECALL).alias(Column.ABSENT_RECALL),
    )
    return joined.join(
        zero, on=[Column.EXPERIMENT, Column.SEED, Column.SALT, Column.LEARNER, Column.FAMILY]
    ).with_columns((pl.col(Column.RECALL) - pl.col(Column.ABSENT_RECALL)).alias(Column.CTK_GAIN))


def with_level_exposure(curve: DoseCurveTable) -> DoseCurveTable:
    return curve.with_columns(
        pl.col(Column.EFFECTIVE_DOSE)
        .mean()
        .over(Column.LEARNER, Column.DOSE)
        .alias(Column.LEVEL_EFFECTIVE_DOSE)
    )


def dose_levels(curve: DoseCurveTable, minimum_peers: EffectiveDoseCount) -> DoseLevelTable:
    """One row per learner and requested level, ordered by realised exposure.

    The ``all available`` level has no requested dose (null); it is a level like any other and
    qualifies whenever its realised exposure reaches ``minimum_peers``.
    """
    return (
        with_level_exposure(curve)
        .group_by(Column.LEARNER, Column.DOSE)
        .agg(
            pl.col(Column.LEVEL_EFFECTIVE_DOSE).first().alias(Column.EFFECTIVE_DOSE),
            pl.col(Column.RECALL).mean(),
            pl.col(Column.RECALL).std().alias(Column.RECALL_STD),
            pl.col(Column.CTK_GAIN).mean(),
            (pl.col(Column.EFFECTIVE_DOSE) >= minimum_peers).sum().alias(Column.OBSERVATIONS_MET),
            pl.len().alias(Column.OBSERVATIONS),
        )
        .with_columns(
            pl.when(pl.col(Column.DOSE).is_null())
            .then(pl.lit(DoseLevel.ALL_AVAILABLE))
            .otherwise(pl.col(Column.DOSE).cast(pl.String))
            .alias(Column.DOSE_LEVEL),
            (pl.col(Column.EFFECTIVE_DOSE) >= minimum_peers).alias(Column.MEETS_DOSE_CRITERION),
        )
        .sort(Column.LEARNER, Column.EFFECTIVE_DOSE)
    )
