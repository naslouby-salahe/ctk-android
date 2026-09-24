import polars as pl

from ctk_android.enums import Column, EvaluationPopulation, ExposureCondition, LibraryOption
from ctk_android.types import (
    Alpha,
    DoseCurveTable,
    DoseRecallTable,
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
