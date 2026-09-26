import polars as pl

from ctk_android.data.cache import is_one_of
from ctk_android.enums import (
    Column,
    DoseLevel,
    Estimand,
    EvaluationPopulation,
    ExposureCondition,
    Learner,
    LibraryOption,
    Metric,
)
from ctk_android.types import (
    Alpha,
    DecompositionTable,
    DoseCurveTable,
    DoseLevelTable,
    DoseRecallTable,
    EffectiveDoseCount,
    EffectiveDoseTable,
    ExposureTable,
    FamilyArmTable,
    FamilyCountsTable,
    FamilyEffectsTable,
    FamilySeedTable,
    SummaryTable,
    TargetsTable,
)


def decomposed_learners() -> tuple[Learner, ...]:
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


def _arm(summary: SummaryTable, learner: Learner, condition: ExposureCondition) -> SummaryTable:
    return summary.filter(
        (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.CONDITION) == condition)
        & pl.col(Column.DOSE).is_null()
        & is_one_of(Column.METRIC, decomposed_metrics())
    ).select(*_keys(), Column.VALUE)


def decompose(summary: SummaryTable) -> DecompositionTable:
    local = _arm(summary, Learner.LOCAL, ExposureCondition.PEER_PRESENT).rename(
        {Column.VALUE: Column.LOCAL_RECALL}
    )
    full = _arm(summary, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE).rename(
        {Column.VALUE: Column.FULL_RECALL}
    )
    parts: list[DecompositionTable] = []
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


def family_seed_effects(families: FamilyCountsTable, alpha: Alpha) -> FamilySeedTable:
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

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> FamilyArmTable:
        return recalls.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(*keys, pl.col(Column.RECALL).alias(name), Column.TRIALS)

    local = arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL)
    parts: list[FamilySeedTable] = []
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


def family_effects(seed_effects: FamilySeedTable) -> FamilyEffectsTable:
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


def _dose_keys() -> list[Column]:
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
        .select(*_dose_keys(), Column.CLIENT, Column.RECALL)
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
        .group_by(*_dose_keys())
        .agg(pl.col(Column.ROWS).sum().alias(Column.EFFECTIVE_DOSE))
    )


def dose_curve(recalls: DoseRecallTable, effective: EffectiveDoseTable) -> DoseCurveTable:
    joined = recalls.join(effective, on=_dose_keys(), how=LibraryOption.JOIN_LEFT, nulls_equal=True)
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
