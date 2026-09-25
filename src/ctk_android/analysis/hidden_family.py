import numpy as np
import polars as pl
from scipy import linalg, optimize
from threadpoolctl import threadpool_limits

from ctk_android.analysis.gates import federated_arms, frozen_family_set_experiments
from ctk_android.analysis.post_confirmatory import summarize_seeds
from ctk_android.analysis.statistics import paired_effect
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    IntervalVerdict,
    Learner,
    LibraryOption,
    MaskingContrast,
    Metric,
    OperatingPointStatus,
    StatisticsLimit,
    Tolerance,
    TransferScope,
    VarianceComponent,
)
from ctk_android.types import (
    Alpha,
    ArmPair,
    ArmSpec,
    CellTable,
    Confidence,
    ContrastSpec,
    Correlation,
    DevianceAndGradient,
    Effect,
    FamilyCountsTable,
    GroupCodes,
    HeterogeneityRow,
    HeterogeneityTable,
    Interval,
    MaskingRow,
    MaskingTable,
    MetricPair,
    Passed,
    RandomEffectsDesign,
    ResampleCount,
    RowCount,
    SeedEffects,
    SeedSummary,
    SummaryTable,
    Table,
    TransferRow,
    TransferScopeSpec,
    TransferTable,
    ValueSeries,
    VarianceEstimate,
    VarianceVector,
)


def hidden_populations() -> tuple[EvaluationPopulation, ...]:
    return (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE)


def variance_components() -> tuple[VarianceComponent, ...]:
    return (
        VarianceComponent.FAMILY,
        VarianceComponent.CLIENT,
        VarianceComponent.FAMILY_BY_CLIENT,
        VarianceComponent.SEED,
        VarianceComponent.RESIDUAL,
    )


def transfer_scopes() -> tuple[TransferScopeSpec, ...]:
    return (
        TransferScopeSpec(scope=TransferScope.CELL, keys=(Column.CLIENT, Column.FAMILY)),
        TransferScopeSpec(scope=TransferScope.FAMILY, keys=(Column.FAMILY,)),
        TransferScopeSpec(scope=TransferScope.CLIENT, keys=(Column.CLIENT,)),
        TransferScopeSpec(scope=TransferScope.OVERALL, keys=()),
    )


def masking_arms() -> tuple[Learner, ...]:
    return (*federated_arms(), Learner.BLEND)


def masking_aggregates() -> tuple[Metric, ...]:
    return (Metric.AUROC, Metric.AUPRC)


def masking_recalls() -> tuple[Metric, ...]:
    return (Metric.OWN_DOMAIN_UNSEEN_RECALL, Metric.FEDERATION_UNSEEN_RECALL)


def hidden_cells(families: FamilyCountsTable, alpha: Alpha) -> CellTable:
    keys = [
        Column.EXPERIMENT,
        Column.SEED,
        Column.SALT,
        Column.POPULATION,
        Column.CLIENT,
        Column.FAMILY,
    ]
    recalls = families.filter(
        is_one_of(Column.EXPERIMENT, list(frozen_family_set_experiments()))
        & is_one_of(Column.POPULATION, list(hidden_populations()))
        & is_one_of(Column.LEARNER, [Learner.LOCAL, Learner.FEDAVG])
        & (pl.col(Column.ALPHA) == alpha)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.TRIALS) > 0)
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> CellTable:
        return recalls.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(*keys, pl.col(Column.RECALL).alias(name), Column.TRIALS)

    peer = pl.col(Column.PEER_RECALL)
    absent = pl.col(Column.ABSENT_RECALL)
    local = pl.col(Column.LOCAL_RECALL)
    wide = (
        arm(Learner.FEDAVG, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            arm(
                Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL
            ).drop(Column.TRIALS),
            on=keys,
        )
        .join(
            arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL).drop(
                Column.TRIALS
            ),
            on=keys,
        )
        .with_columns(
            (absent - local).alias(Column.POOLING_GAIN),
            (peer - local).alias(Column.TOTAL_GAIN),
            (peer - absent).alias(Column.CTK_GAIN),
        )
    )
    gain = pl.max_horizontal(pl.col(Column.CTK_GAIN), pl.lit(0))
    repair = pl.min_horizontal(gain, pl.max_horizontal(-pl.col(Column.POOLING_GAIN), pl.lit(0)))
    return (
        wide.with_columns(repair.alias(Column.REPAIR))
        .with_columns(
            (gain - pl.col(Column.REPAIR)).alias(Column.NEW_CAPABILITY),
            pl.min_horizontal(pl.col(Column.CTK_GAIN), pl.lit(0)).alias(Column.CTK_HARM),
        )
        .sort(*keys)
    )


def _codes(labels: ValueSeries) -> GroupCodes:
    return np.unique(labels.to_numpy(), return_inverse=True)[1].reshape(-1).astype(np.int64)


def _pair_codes(first: GroupCodes, second: GroupCodes) -> GroupCodes:
    stacked = np.stack([first, second], axis=1)
    return np.unique(stacked, axis=0, return_inverse=True)[1].reshape(-1).astype(np.int64)


def _design(cells: CellTable) -> RandomEffectsDesign:
    family = _codes(cells[Column.FAMILY])
    client = _codes(cells[Column.CLIENT])
    return RandomEffectsDesign(
        response=cells[Column.CTK_GAIN].to_numpy().astype(np.float64),
        factors=(family, client, _pair_codes(family, client), _codes(cells[Column.SEED])),
    )


def _reml_deviance(
    variances: VarianceVector, response: SeedEffects, grams: list[SeedEffects]
) -> DevianceAndGradient:
    covariance = sum(
        (weight * gram for weight, gram in zip(variances, grams, strict=True)),
        np.eye(response.size) * Tolerance.VARIANCE_FLOOR,
    )
    factor = linalg.cho_factor(covariance, lower=True)
    inverse = linalg.cho_solve(factor, np.eye(response.size))
    inverse_ones = inverse.sum(axis=1)
    total = inverse_ones.sum()
    projection = inverse - np.outer(inverse_ones, inverse_ones) / total
    projected = projection @ response
    deviance = 2 * np.log(np.diag(factor[0])).sum() + np.log(total) + response @ projected
    gradient = np.array(
        [(projection * gram).sum() - projected @ gram @ projected for gram in grams]
    )
    return deviance.item(), gradient


def _reml(design: RandomEffectsDesign, warm: VarianceVector | None) -> VarianceEstimate:
    centred = design.response - design.response.mean()
    scale = centred.var().item()
    count = len(design.factors) + 1
    if scale <= 0:
        return VarianceEstimate(variances=np.zeros(count), converged=True)
    response = centred / np.sqrt(scale)
    grams = [(codes[:, None] == codes[None, :]).astype(np.float64) for codes in design.factors]
    grams.append(np.eye(response.size))
    starts = (
        (np.full(count, 1 / count), np.append(np.full(count - 1, 0.5 / count), 0.5))
        if warm is None
        else (np.maximum(warm, Tolerance.WARM_START_FLOOR),)
    )
    fits = [
        optimize.minimize(
            _reml_deviance,
            start,
            args=(response, grams),
            jac=True,
            method=LibraryOption.LBFGSB,
            bounds=optimize.Bounds(0, np.inf),
        )
        for start in starts
    ]
    best = min(fits, key=lambda fit: fit.fun)
    return VarianceEstimate(variances=best.x * scale, converged=bool(best.success))


def _shares(estimate: VarianceEstimate) -> VarianceVector:
    total = estimate.variances.sum()
    return estimate.variances / total if total > 0 else np.zeros(estimate.variances.size)


def _resampled(design: RandomEffectsDesign, rng: np.random.Generator) -> RandomEffectsDesign:
    seed_codes = design.factors[-1]
    draws = rng.choice(np.unique(seed_codes), size=np.unique(seed_codes).size)
    rows: list[GroupCodes] = [np.flatnonzero(seed_codes == draw) for draw in draws]
    relabelled = np.concatenate([np.full(part.size, index) for index, part in enumerate(rows)])
    chosen = np.concatenate(rows)
    return RandomEffectsDesign(
        response=design.response[chosen],
        factors=(*(codes[chosen] for codes in design.factors[:-1]), relabelled.astype(np.int64)),
    )


def _share_interval(
    design: RandomEffectsDesign,
    warm: VarianceVector,
    resamples: ResampleCount,
    seed: RowCount,
    level: Confidence,
) -> list[Interval]:
    rng = np.random.default_rng(seed)
    with threadpool_limits(limits=1):
        draws = np.stack([_shares(_reml(_resampled(design, rng), warm)) for _ in range(resamples)])
    low, high = np.quantile(draws, [(1 - level) / 2, (1 + level) / 2], axis=0)
    return [
        Interval(low=lower.item(), high=upper.item())
        for lower, upper in zip(low, high, strict=True)
    ]


def _sampling_noise(cells: CellTable) -> Effect:
    peer = cells[Column.PEER_RECALL].to_numpy()
    absent = cells[Column.ABSENT_RECALL].to_numpy()
    trials = cells[Column.TRIALS].to_numpy()
    return ((peer * (1 - peer) + absent * (1 - absent)) / trials).mean().item()


def ctk_heterogeneity_components(cells: CellTable, config: Config) -> HeterogeneityTable:
    rows: list[HeterogeneityRow] = []
    for experiment in frozen_family_set_experiments():
        for population in hidden_populations():
            scoped = cells.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.POPULATION) == population)
            )
            if scoped.height == 0 or scoped[Column.SEED].n_unique() < StatisticsLimit.BCA_SEEDS:
                continue
            design = _design(scoped)
            with threadpool_limits(limits=1):
                estimate = _reml(design, None)
            shares = _shares(estimate)
            intervals = _share_interval(
                design,
                shares,
                config.statistics.cluster_bootstrap_resamples,
                config.statistics.statistics_seed,
                config.statistics.confidence_level,
            )
            pair_sizes = np.bincount(design.factors[2])
            for index, component in enumerate(variance_components()):
                interval = intervals[index]
                rows.append(
                    HeterogeneityRow(
                        evidence_class=EvidenceClass.POST_CONFIRMATORY,
                        experiment=experiment,
                        population=population,
                        component=component,
                        variance=estimate.variances[index].item(),
                        share=shares[index].item(),
                        share_ci_low=interval.low,
                        share_ci_high=interval.high,
                        observations=scoped.height,
                        cells=pair_sizes.size,
                        replicated_cells=(pair_sizes > 1).sum().item(),
                        seeds=scoped[Column.SEED].n_unique(),
                        families=scoped[Column.FAMILY].n_unique(),
                        clients=scoped[Column.CLIENT].n_unique(),
                        sampling_noise_reference=_sampling_noise(scoped),
                        converged=estimate.converged,
                        bootstrap_resamples=config.statistics.cluster_bootstrap_resamples,
                    )
                )
    return records_to_frame(rows)


def _verdict(interval: Interval | None, reference: Effect) -> IntervalVerdict:
    if interval is None:
        return IntervalVerdict.INCONCLUSIVE
    if interval.low > reference:
        return IntervalVerdict.POSITIVE
    if interval.high < reference:
        return IntervalVerdict.NEGATIVE
    return IntervalVerdict.INCONCLUSIVE


def _metric_by_seed(
    summary: SummaryTable,
    experiment: ExperimentName,
    arm: ArmSpec,
    metric: Metric,
    alpha: Alpha,
    name: Column,
) -> Table:
    return summary.filter(
        (pl.col(Column.EXPERIMENT) == experiment)
        & (pl.col(Column.LEARNER) == arm.learner)
        & (pl.col(Column.CONDITION) == arm.condition)
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ALPHA) == alpha)
        & (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.VALID)
        & pl.col(Column.DOSE).is_null()
        & pl.col(Column.VALUE).is_finite()
    ).select(Column.SEED, pl.col(Column.VALUE).alias(name))


def _seed_difference(
    summary: SummaryTable,
    experiment: ExperimentName,
    arms: ArmPair,
    metric: Metric,
    alpha: Alpha,
) -> Table:
    minuend = _metric_by_seed(summary, experiment, arms.minuend, metric, alpha, Column.MINUEND)
    subtrahend = _metric_by_seed(
        summary, experiment, arms.subtrahend, metric, alpha, Column.SUBTRAHEND
    )
    return minuend.join(subtrahend, on=Column.SEED).select(
        Column.SEED, (pl.col(Column.MINUEND) - pl.col(Column.SUBTRAHEND)).alias(Column.DIFFERENCE)
    )


def _opposed(first: IntervalVerdict, second: IntervalVerdict) -> Passed:
    return {first, second} == {IntervalVerdict.POSITIVE, IntervalVerdict.NEGATIVE}


def _seed_correlation(aggregate: SeedEffects, recall: SeedEffects) -> Correlation | None:
    if aggregate.size < StatisticsLimit.BCA_SEEDS or np.ptp(aggregate) == 0 or np.ptp(recall) == 0:
        return None
    return np.corrcoef(aggregate, recall)[0, 1].item()


def _masking_row(
    experiment: ExperimentName,
    learner: Learner,
    contrast: MaskingContrast,
    metrics: MetricPair,
    aggregate_differences: Table,
    recall_differences: Table,
    config: Config,
) -> MaskingRow | None:
    paired = aggregate_differences.join(
        recall_differences, on=Column.SEED, suffix=Column.SUBTRAHEND
    )
    if paired.height == 0:
        return None
    aggregate = paired[Column.DIFFERENCE].to_numpy()
    recall = paired[f"{Column.DIFFERENCE}{Column.SUBTRAHEND}"].to_numpy()
    aggregate_effect = paired_effect(aggregate, config.statistics)
    recall_effect = paired_effect(recall, config.statistics)
    threshold = config.statistics.gates.ctk_min_gain
    aggregate_verdict = _verdict(aggregate_effect.interval, 0)
    recall_verdict = _verdict(recall_effect.interval, 0)
    missed = ((recall >= threshold) & (aggregate <= 0)).sum().item()
    reassured = ((recall <= -threshold) & (aggregate >= 0)).sum().item()
    low = recall_effect.interval.low if recall_effect.interval else None
    high = recall_effect.interval.high if recall_effect.interval else None
    return MaskingRow(
        evidence_class=EvidenceClass.POST_CONFIRMATORY,
        experiment=experiment,
        learner=learner,
        contrast=contrast,
        aggregate_metric=metrics.aggregate,
        recall_metric=metrics.recall,
        seed_count=paired.height,
        aggregate_mean=aggregate_effect.mean,
        aggregate_ci_low=aggregate_effect.interval.low if aggregate_effect.interval else None,
        aggregate_ci_high=aggregate_effect.interval.high if aggregate_effect.interval else None,
        aggregate_verdict=aggregate_verdict,
        recall_mean=recall_effect.mean,
        recall_ci_low=low,
        recall_ci_high=high,
        recall_verdict=recall_verdict,
        material_gain_threshold=threshold,
        verdicts_opposed=_opposed(aggregate_verdict, recall_verdict),
        masked_gain=low is not None
        and low > threshold
        and aggregate_verdict is not IntervalVerdict.POSITIVE,
        masked_loss=high is not None
        and high < -threshold
        and aggregate_verdict is not IntervalVerdict.NEGATIVE,
        sign_disagreement_seeds=(np.sign(aggregate) * np.sign(recall) < 0).sum().item(),
        gain_missed_seeds=missed,
        false_reassurance_seeds=reassured,
        opposite_conclusion_seeds=missed + reassured,
        seed_correlation=_seed_correlation(aggregate, recall),
    )


def aggregate_metric_masking(summary: SummaryTable, config: Config) -> MaskingTable:
    alpha = config.experiments.operating.primary_alpha
    peer = ExposureCondition.PEER_PRESENT
    absent = ExposureCondition.FAMILY_ABSENT_EVERYWHERE
    local = ArmSpec(learner=Learner.LOCAL, condition=peer)
    rows: list[MaskingRow] = []
    for experiment in frozen_family_set_experiments():
        for learner in masking_arms():
            present = ArmSpec(learner=learner, condition=peer)
            contrasts = (
                ContrastSpec(
                    contrast=MaskingContrast.PEER_VERSUS_LOCAL,
                    arms=ArmPair(minuend=present, subtrahend=local),
                ),
                ContrastSpec(
                    contrast=MaskingContrast.PEER_VERSUS_FAMILY_ABSENT,
                    arms=ArmPair(
                        minuend=present, subtrahend=ArmSpec(learner=learner, condition=absent)
                    ),
                ),
            )
            for spec in contrasts:
                for aggregate in masking_aggregates():
                    for recall in masking_recalls():
                        row = _masking_row(
                            experiment,
                            learner,
                            spec.contrast,
                            MetricPair(aggregate=aggregate, recall=recall),
                            _seed_difference(summary, experiment, spec.arms, aggregate, alpha),
                            _seed_difference(summary, experiment, spec.arms, recall, alpha),
                            config,
                        )
                        if row is not None:
                            rows.append(row)
    return records_to_frame(rows)


def _transfer_row(
    experiment: ExperimentName,
    population: EvaluationPopulation,
    spec: TransferScopeSpec,
    group: CellTable,
    config: Config,
) -> TransferRow | None:
    per_seed = group.group_by(Column.SEED, maintain_order=True).agg(
        pl.col(Column.POOLING_GAIN).mean(),
        pl.col(Column.CTK_GAIN).mean(),
        pl.col(Column.REPAIR).mean(),
        pl.col(Column.NEW_CAPABILITY).mean(),
        pl.col(Column.CTK_HARM).mean(),
    )

    def summary(column: Column) -> SeedSummary | None:
        return summarize_seeds(per_seed[column].to_numpy(), config.statistics)

    pooling = summary(Column.POOLING_GAIN)
    ctk = summary(Column.CTK_GAIN)
    repair = summary(Column.REPAIR)
    new = summary(Column.NEW_CAPABILITY)
    harm = summary(Column.CTK_HARM)
    if pooling is None or ctk is None or repair is None or new is None or harm is None:
        return None
    head = group.row(0, named=True)
    gross = repair.mean_difference + new.mean_difference
    return TransferRow(
        evidence_class=EvidenceClass.POST_CONFIRMATORY,
        experiment=experiment,
        population=population,
        scope=spec.scope,
        client=head[Column.CLIENT] if Column.CLIENT in spec.keys else None,
        family=head[Column.FAMILY] if Column.FAMILY in spec.keys else None,
        seed_count=per_seed.height,
        observations=group.height,
        cells=group.select(Column.CLIENT, Column.FAMILY).n_unique(),
        pooling_mean=pooling.mean_difference,
        pooling_ci_low=pooling.ci_low,
        pooling_ci_high=pooling.ci_high,
        hurt_seeds=(per_seed[Column.POOLING_GAIN].to_numpy() < 0).sum().item(),
        hurts=pooling.mean_difference < 0,
        hurts_interval_below_zero=pooling.ci_high is not None and pooling.ci_high < 0,
        ctk_mean=ctk.mean_difference,
        ctk_ci_low=ctk.ci_low,
        ctk_ci_high=ctk.ci_high,
        repair_mean=repair.mean_difference,
        repair_ci_low=repair.ci_low,
        repair_ci_high=repair.ci_high,
        new_capability_mean=new.mean_difference,
        new_capability_ci_low=new.ci_low,
        new_capability_ci_high=new.ci_high,
        harm_mean=harm.mean_difference,
        harm_ci_low=harm.ci_low,
        harm_ci_high=harm.ci_high,
        repair_share=repair.mean_difference / gross if gross > 0 else None,
    )


def negative_transfer_decomposition(cells: CellTable, config: Config) -> TransferTable:
    rows: list[TransferRow | None] = []
    for experiment in frozen_family_set_experiments():
        for population in hidden_populations():
            scoped = cells.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.POPULATION) == population)
            )
            if scoped.height == 0:
                continue
            for spec in transfer_scopes():
                groups = (
                    scoped.partition_by(*spec.keys, maintain_order=True) if spec.keys else [scoped]
                )
                rows.extend(
                    _transfer_row(experiment, population, spec, group, config) for group in groups
                )
    return records_to_frame([row for row in rows if row is not None])
