import polars as pl

from ctk_android.enums import (
    Column,
    Estimand,
    EvaluationPopulation,
    ExposureCondition,
    Learner,
    LibraryOption,
    Metric,
)
from ctk_android.types import Alpha


def decomposed_learners() -> tuple[Learner, Learner]:
    return (Learner.CENTRAL, Learner.FEDAVG)


def decomposed_metrics() -> list[Metric]:
    return [
        Metric.OWN_DOMAIN_UNSEEN_RECALL,
        Metric.FEDERATION_UNSEEN_RECALL,
        Metric.FAMILY_MACRO_UNSEEN_RECALL,
        Metric.WORST_CLIENT_UNSEEN_RECALL,
    ]


def _keys() -> list[Column]:
    return [Column.EXPERIMENT, Column.SEED, Column.SALT, Column.ALPHA, Column.METRIC]


def _arm(summary: pl.DataFrame, learner: Learner, condition: ExposureCondition) -> pl.DataFrame:
    return summary.filter(
        (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.CONDITION) == condition)
        & pl.col(Column.DOSE).is_null()
        & pl.col(Column.METRIC).is_in(decomposed_metrics())
    ).select(*_keys(), Column.VALUE)


def decompose(summary: pl.DataFrame) -> pl.DataFrame:
    local = _arm(summary, Learner.LOCAL, ExposureCondition.PEER_PRESENT).rename(
        {Column.VALUE: Column.LOCAL_RECALL}
    )
    full = _arm(summary, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE).rename(
        {Column.VALUE: Column.FULL_RECALL}
    )
    parts: list[pl.DataFrame] = []
    for learner in decomposed_learners():
        peer = _arm(summary, learner, ExposureCondition.PEER_PRESENT).rename(
            {Column.VALUE: Column.PEER_RECALL}
        )
        absent = _arm(summary, learner, ExposureCondition.FAMILY_ABSENT_EVERYWHERE).rename(
            {Column.VALUE: Column.ABSENT_RECALL}
        )
        wide = (
            peer.join(absent, on=_keys())
            .join(local, on=_keys())
            .join(full, on=_keys(), how=LibraryOption.JOIN_LEFT)
            .with_columns(pl.lit(learner).alias(Column.LEARNER))
        )
        peer_recall = pl.col(Column.PEER_RECALL)
        absent_recall = pl.col(Column.ABSENT_RECALL)
        local_recall = pl.col(Column.LOCAL_RECALL)
        headroom = pl.col(Column.FULL_RECALL) - local_recall
        estimands = {
            Estimand.TOTAL_GAIN: peer_recall - local_recall,
            Estimand.POOLING_GAIN: absent_recall - local_recall,
            Estimand.CTK_GAIN: peer_recall - absent_recall,
            Estimand.ORACLE_GAP_RECOVERY: pl.when(headroom.abs() > 0)
            .then((peer_recall - local_recall) / headroom)
            .otherwise(None),
        }
        if learner is Learner.CENTRAL:
            estimands[Estimand.LOCAL_DEFICIT] = pl.col(Column.FULL_RECALL) - local_recall
        parts.extend(
            wide.select(*_keys(), Column.LEARNER, expression.alias(Column.VALUE)).with_columns(
                pl.lit(estimand).alias(Column.ESTIMAND)
            )
            for estimand, expression in estimands.items()
        )
    return pl.concat(parts).sort(*_keys(), Column.LEARNER, Column.ESTIMAND)


def family_seed_effects(families: pl.DataFrame, alpha: Alpha) -> pl.DataFrame:
    keys = [Column.EXPERIMENT, Column.SEED, Column.SALT, Column.CLIENT, Column.FAMILY]
    recalls = (
        families.filter(
            (pl.col(Column.ALPHA) == alpha)
            & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
            & pl.col(Column.DOSE).is_null()
            & (pl.col(Column.TRIALS) > 0)
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .select(*keys, Column.LEARNER, Column.CONDITION, Column.RECALL, Column.TRIALS)
    )

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> pl.DataFrame:
        return recalls.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(*keys, pl.col(Column.RECALL).alias(name), Column.TRIALS)

    local = arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL)
    parts: list[pl.DataFrame] = []
    for learner in decomposed_learners():
        wide = (
            arm(learner, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
            .join(
                arm(learner, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL).drop(
                    Column.TRIALS
                ),
                on=keys,
            )
            .join(
                arm(learner, ExposureCondition.FULL_EXPOSURE, Column.FULL_RECALL).drop(
                    Column.TRIALS
                ),
                on=keys,
                how=LibraryOption.JOIN_LEFT,
            )
            .join(local.drop(Column.TRIALS), on=keys)
        )
        parts.append(
            wide.with_columns(
                pl.lit(learner).alias(Column.LEARNER),
                (pl.col(Column.PEER_RECALL) - pl.col(Column.ABSENT_RECALL)).alias(Column.CTK_GAIN),
            )
        )
    return pl.concat(parts)


def family_effects(seed_effects: pl.DataFrame) -> pl.DataFrame:
    return (
        seed_effects.group_by(Column.EXPERIMENT, Column.FAMILY, Column.LEARNER)
        .agg(
            pl.col(Column.LOCAL_RECALL).mean(),
            pl.col(Column.ABSENT_RECALL).mean(),
            pl.col(Column.PEER_RECALL).mean(),
            pl.col(Column.FULL_RECALL).mean(),
            pl.col(Column.CTK_GAIN).mean(),
            pl.col(Column.TRIALS).mean(),
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
        )
        .sort(Column.EXPERIMENT, Column.LEARNER, Column.FAMILY)
    )
