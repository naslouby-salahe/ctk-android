import numpy as np
import polars as pl
from scipy import stats

from ctk_android.config import Config, StatisticsConfig
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    ContrastFamily,
    Estimand,
    ExperimentName,
    Learner,
    LibraryOption,
    Metric,
    StatisticsLimit,
)
from ctk_android.types import (
    Alpha,
    Axis,
    DecompositionTable,
    Effect,
    EffectRow,
    EffectsTable,
    Fraction,
    GroupIds,
    GroupTable,
    HitVector,
    Interval,
    PairedEffect,
    PValue,
    PValueVector,
    RandomSeed,
    ResampleCount,
    SeedEffects,
    TrialVector,
)


def _finite_interval(low: Effect, high: Effect) -> Interval | None:
    return Interval(low=low, high=high) if np.isfinite(low) and np.isfinite(high) else None


def bca_interval(values: SeedEffects, config: StatisticsConfig) -> Interval | None:
    if values.size < StatisticsLimit.BCA_SEEDS or np.ptp(values) == 0:
        return None
    result = stats.bootstrap(
        (values,),
        np.mean,
        confidence_level=config.confidence_level,
        n_resamples=config.bootstrap_resamples,
        method=LibraryOption.BCA,
        random_state=np.random.default_rng(config.statistics_seed),
    )
    return _finite_interval(
        result.confidence_interval.low.item(), result.confidence_interval.high.item()
    )


def exact_wilcoxon(differences: SeedEffects) -> PValue:
    if not np.any(differences):
        return 1.0
    return stats.wilcoxon(differences, method=LibraryOption.WILCOXON_EXACT).pvalue.item()


def paired_effect(differences: SeedEffects, config: StatisticsConfig) -> PairedEffect:
    spread = differences.std(ddof=1) if differences.size > 1 else 0.0
    return PairedEffect(
        mean=differences.mean().item(),
        median=np.median(differences).item(),
        positive_seeds=(differences > 0).sum().item(),
        seeds=differences.size,
        effect_size=(differences.mean() / spread).item() if spread > 0 else None,
        interval=bca_interval(differences, config),
        p_value=exact_wilcoxon(differences),
    )


def holm_adjust(p_values: PValueVector) -> PValueVector:
    order = np.argsort(p_values, kind=LibraryOption.SORT_STABLE)
    scaled = (p_values.size - np.arange(p_values.size)) * p_values[order]
    adjusted = np.minimum(np.maximum.accumulate(scaled), 1.0)
    result = np.empty_like(adjusted)
    result[order] = adjusted
    return result


def ratio_interval(
    numerator: SeedEffects,
    denominator: SeedEffects,
    minimum_denominator: Fraction,
    config: StatisticsConfig,
) -> Interval | None:
    if numerator.size < StatisticsLimit.BCA_SEEDS or abs(denominator.mean()) < minimum_denominator:
        return None

    def ratio_of_means(top: SeedEffects, bottom: SeedEffects, axis: Axis) -> SeedEffects:
        return top.mean(axis=axis) / bottom.mean(axis=axis)

    result = stats.bootstrap(
        (numerator, denominator),
        ratio_of_means,
        paired=True,
        vectorized=True,
        confidence_level=config.confidence_level,
        n_resamples=config.bootstrap_resamples,
        method=LibraryOption.BCA,
        random_state=np.random.default_rng(config.statistics_seed),
    )
    return _finite_interval(
        result.confidence_interval.low.item(), result.confidence_interval.high.item()
    )


def cluster_bootstrap_difference(
    hits_first: HitVector,
    hits_second: HitVector,
    trials: TrialVector,
    groups: GroupIds,
    resamples: ResampleCount,
    seed: RandomSeed,
    level: Fraction,
) -> Interval | None:
    group_count = groups.max(initial=-1).item() + 1
    first = np.bincount(groups, weights=hits_first, minlength=group_count)
    second = np.bincount(groups, weights=hits_second, minlength=group_count)
    total = np.bincount(groups, weights=trials, minlength=group_count)
    present = total > 0
    first, second, total = first[present], second[present], total[present]
    if total.size < 2 or total.sum() == 0:
        return None
    rng = np.random.default_rng(seed)
    differences = np.empty(resamples)
    for start in range(0, resamples, StatisticsLimit.CLUSTER_CHUNK):
        size = min(StatisticsLimit.CLUSTER_CHUNK, resamples - start)
        picked = rng.integers(0, total.size, size=(size, total.size))
        denominator = total[picked].sum(axis=1)
        differences[start : start + size] = (
            first[picked].sum(axis=1) - second[picked].sum(axis=1)
        ) / denominator
    tail = (1.0 - level) / 2.0
    low, high = np.quantile(differences, [tail, 1.0 - tail])
    return _finite_interval(low.item(), high.item())


def contrast_family(
    experiment: ExperimentName,
    alpha: Alpha,
    metric: Metric,
    learner: Learner,
    estimand: Estimand,
    primary_alpha: Alpha,
) -> ContrastFamily:
    in_scope = (
        experiment == ExperimentName.CONTROLLED_EXPOSURE
        and alpha == primary_alpha
        and metric == Metric.FEDERATION_UNSEEN_RECALL
        and estimand in (Estimand.TOTAL_GAIN, Estimand.POOLING_GAIN, Estimand.CTK_GAIN)
    )
    if in_scope and learner == Learner.FEDAVG:
        return ContrastFamily.PRIMARY
    if in_scope and learner == Learner.CENTRAL:
        return ContrastFamily.REFERENCE
    return ContrastFamily.EXPLORATORY


def _effect_row(group: GroupTable, config: Config) -> EffectRow:
    head = group.row(0, named=True)
    experiment, alpha = head[Column.EXPERIMENT], head[Column.ALPHA]
    metric, learner, estimand = head[Column.METRIC], head[Column.LEARNER], head[Column.ESTIMAND]
    effect = paired_effect(group[Column.VALUE].to_numpy(), config.statistics)
    return EffectRow(
        experiment=experiment,
        salt=head[Column.SALT],
        alpha=alpha,
        metric=metric,
        learner=learner,
        estimand=estimand,
        contrast_family=contrast_family(
            experiment, alpha, metric, learner, estimand, config.experiments.operating.primary_alpha
        ),
        mean_difference=effect.mean,
        median_difference=effect.median,
        positive_seeds=effect.positive_seeds,
        seed_count=effect.seeds,
        effect_size=effect.effect_size,
        ci_low=effect.interval.low if effect.interval else None,
        ci_high=effect.interval.high if effect.interval else None,
        p_value=effect.p_value,
        p_holm=None,
    )


def _share_rows(decomposition: DecompositionTable, config: Config) -> list[EffectRow]:
    keys = [Column.EXPERIMENT, Column.SALT, Column.ALPHA, Column.METRIC, Column.LEARNER]
    rows: list[EffectRow] = []
    for group in decomposition.sort(Column.SEED).partition_by(keys):
        head = group.row(0, named=True)

        def seeds(estimand: Estimand, frame: GroupTable = group) -> SeedEffects:
            return frame.filter(pl.col(Column.ESTIMAND) == estimand)[Column.VALUE].to_numpy()

        total = seeds(Estimand.TOTAL_GAIN)
        for share, part in (
            (Estimand.CTK_SHARE, Estimand.CTK_GAIN),
            (Estimand.POOLING_SHARE, Estimand.POOLING_GAIN),
        ):
            numerator = seeds(part)
            if total.mean() == 0:
                continue
            interval = ratio_interval(
                numerator, total, config.statistics.share_min_total_gain, config.statistics
            )
            rows.append(
                EffectRow(
                    experiment=head[Column.EXPERIMENT],
                    salt=head[Column.SALT],
                    alpha=head[Column.ALPHA],
                    metric=head[Column.METRIC],
                    learner=head[Column.LEARNER],
                    estimand=share,
                    contrast_family=ContrastFamily.EXPLORATORY,
                    mean_difference=numerator.mean() / total.mean(),
                    median_difference=None,
                    positive_seeds=None,
                    seed_count=total.size,
                    effect_size=None,
                    ci_low=interval.low if interval else None,
                    ci_high=interval.high if interval else None,
                    p_value=None,
                    p_holm=None,
                )
            )
    return rows


def paired_effect_table(decomposition: DecompositionTable, config: Config) -> EffectsTable:
    keys = [
        Column.EXPERIMENT,
        Column.SALT,
        Column.ALPHA,
        Column.METRIC,
        Column.LEARNER,
        Column.ESTIMAND,
    ]
    resolved = decomposition.filter(pl.col(Column.VALUE).is_not_null()).sort(Column.SEED)
    rows = [_effect_row(group, config) for group in resolved.partition_by(keys)]
    shares = _share_rows(
        resolved.filter(
            is_one_of(
                Column.ESTIMAND, [Estimand.TOTAL_GAIN, Estimand.CTK_GAIN, Estimand.POOLING_GAIN]
            )
        ),
        config,
    )
    primary = [
        index for index, row in enumerate(rows) if row.contrast_family is ContrastFamily.PRIMARY
    ]
    adjusted = holm_adjust(np.array([rows[index].p_value for index in primary], dtype=np.float64))
    for index, p_holm in zip(primary, adjusted, strict=True):
        rows[index] = rows[index].model_copy(update={Column.P_HOLM: p_holm.item()})
    return records_to_frame([*rows, *shares])
