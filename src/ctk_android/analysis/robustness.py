import polars as pl

from ctk_android.analysis.statistics import paired_effect
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    ExposureCondition,
    Learner,
    Sensitivity,
)
from ctk_android.types import (
    Alpha,
    FamilyCountsTable,
    FamilyName,
    MicroGainTable,
    PooledRecallTable,
    RobustnessRow,
    RobustnessTable,
    SupportCount,
)


def top_support_families(families: FamilyCountsTable, count: SupportCount) -> list[FamilyName]:
    ranked = (
        families.filter(pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.TRIALS).mean())
        .sort([Column.TRIALS, Column.FAMILY], descending=[True, False])
    )
    return ranked[Column.FAMILY].head(count).to_list()


def micro_ctk_by_seed(
    families: FamilyCountsTable, alpha: Alpha, excluded: list[FamilyName]
) -> MicroGainTable:
    def pooled(condition: ExposureCondition, name: Column) -> PooledRecallTable:
        return (
            families.filter(
                (pl.col(Column.LEARNER) == Learner.FEDAVG)
                & (pl.col(Column.CONDITION) == condition)
                & pl.col(Column.DOSE).is_null()
                & (pl.col(Column.ALPHA) == alpha)
                & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
                & ~is_one_of(Column.FAMILY, excluded)
            )
            .group_by(Column.EXPERIMENT, Column.SEED, Column.SALT)
            .agg((pl.col(Column.HITS).sum() / pl.col(Column.TRIALS).sum()).alias(name))
        )

    return (
        pooled(ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            pooled(ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL),
            on=[Column.EXPERIMENT, Column.SEED, Column.SALT],
        )
        .with_columns(
            (pl.col(Column.PEER_RECALL) - pl.col(Column.ABSENT_RECALL)).alias(Column.CTK_GAIN)
        )
    )


def robustness_table(families: FamilyCountsTable, config: Config) -> RobustnessTable:
    alpha = config.experiments.operating.primary_alpha
    removed = top_support_families(families, config.experiments.top_family_removal_count)
    rows: list[RobustnessRow] = []
    for sensitivity, excluded in (
        (Sensitivity.ALL_FAMILIES, []),
        (Sensitivity.TOP_FAMILY_REMOVAL, removed),
    ):
        gains = micro_ctk_by_seed(families, alpha, excluded)
        for experiment in gains[Column.EXPERIMENT].unique():
            values = gains.filter(pl.col(Column.EXPERIMENT) == experiment)[
                Column.CTK_GAIN
            ].to_numpy()
            effect = paired_effect(values, config.statistics)
            rows.append(
                RobustnessRow(
                    experiment=experiment,
                    sensitivity=sensitivity,
                    mean_difference=effect.mean,
                    ci_low=effect.interval.low if effect.interval else None,
                    ci_high=effect.interval.high if effect.interval else None,
                    seed_count=effect.seeds,
                )
            )
    return records_to_frame(rows)
