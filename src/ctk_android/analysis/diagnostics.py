import warnings
from itertools import pairwise

import numpy as np
import polars as pl
from scipy import optimize, stats
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_curve

from ctk_android.analysis.extensions import scope_experiments
from ctk_android.analysis.statistics import bca_interval
from ctk_android.config import Config
from ctk_android.enums import (
    Aggregation,
    Column,
    ControlArm,
    DiagnosticColumn,
    DiagnosticLimit,
    DiagnosticResamples,
    DiagnosticSeed,
    DoseCode,
    DoseFitLevel,
    DoseLevel,
    DoseModel,
    DoseResponseClass,
    DoseRole,
    EmaxBound,
    EmaxStart,
    ErrorMessage,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    ExtensionScope,
    Learner,
    LibraryOption,
    NameFragment,
    NoveltyDescriptor,
    OperatingReading,
    PeerShare,
    ReallocationStratum,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    ScoreMagnitude,
    Separator,
    SplitRole,
    StatisticsLimit,
    SupportStratum,
)
from ctk_android.types import (
    Alpha,
    ArmKey,
    ArmLabel,
    ControlDiagnostics,
    ControlStratum,
    Correlation,
    DiagnosticColumnName,
    DiagnosticInterval,
    DiagnosticMatrix,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticSummary,
    DiagnosticTable,
    DiagnosticVector,
    DoseDiagnostics,
    DoseFit,
    DoseLabel,
    Effect,
    ExposureTable,
    FamilyCountsTable,
    FamilyLevelTable,
    Interval,
    NoveltyTable,
    Passed,
    PlaceboTable,
    PValue,
    ScopedExperiments,
    ScoredRun,
    StratumTables,
    SupportCount,
)


def seeded_bca(
    values: DiagnosticVector, config: Config, seed: DiagnosticSeed, minimum: SupportCount
) -> Interval | None:
    # Seed-level BCa interval as in the frozen scratch diagnostics: NaNs dropped, degenerate
    # samples and non-finite limits yield no interval.
    finite = values[~np.isnan(values)]
    if finite.size < minimum or np.ptp(finite) == 0:
        return None
    result = stats.bootstrap(
        (finite,),
        np.mean,
        confidence_level=config.statistics.confidence_level,
        n_resamples=config.statistics.bootstrap_resamples,
        method=LibraryOption.BCA,
        random_state=np.random.default_rng(seed),
    )
    low = result.confidence_interval.low.item()
    high = result.confidence_interval.high.item()
    return Interval(low=low, high=high) if np.isfinite(low) and np.isfinite(high) else None


def interval_low(interval: Interval | None) -> Correlation | None:
    return None if interval is None else interval.low


def interval_high(interval: Interval | None) -> Correlation | None:
    return None if interval is None else interval.high


def percentile_limits(values: DiagnosticVector, config: Config) -> Interval | None:
    finite = values[~np.isnan(values)]
    if finite.size == 0:
        return None
    tail = (1.0 - config.statistics.confidence_level) / 2.0
    low, high = np.quantile(finite, [tail, 1.0 - tail])
    return Interval(low=low.item(), high=high.item())


def spearman(first: DiagnosticVector, second: DiagnosticVector) -> Correlation:
    return stats.spearmanr(first, second).statistic.item()


def spearman_p(first: DiagnosticVector, second: DiagnosticVector) -> PValue:
    return stats.spearmanr(first, second).pvalue.item()


def labelled(rows: DiagnosticRows, evidence: EvidenceClass) -> DiagnosticTable:
    if not rows:
        return pl.DataFrame()
    return pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.lit(evidence).alias(Column.EVIDENCE_CLASS)
    )


def with_class(table: DiagnosticTable, evidence: EvidenceClass) -> DiagnosticTable:
    return table.with_columns(pl.lit(evidence).alias(Column.EVIDENCE_CLASS))


def ordered_scopes(
    config: Config, experiments: tuple[ExperimentName, ...]
) -> list[ScopedExperiments]:
    scopes = scope_experiments(config, experiments)
    return [
        ScopedExperiments(scope=scope, experiments=scopes[scope])
        for scope in (
            ExtensionScope.PRIMARY_SET,
            ExtensionScope.REPLICATION_SET,
            ExtensionScope.POOLED,
        )
        if scopes[scope]
    ]


def set_labels(config: Config, experiments: tuple[ExperimentName, ...]) -> DiagnosticTable:
    return pl.DataFrame(
        [
            {Column.EXPERIMENT: name, DiagnosticColumn.SET: scoped.scope}
            for scoped in ordered_scopes(config, experiments)
            if scoped.scope is not ExtensionScope.POOLED
            for name in scoped.experiments
        ]
    )


def own_domain_minimum(config: Config, experiments: tuple[ExperimentName, ...]) -> SupportCount:
    profile = config.experiments.experiments[experiments[0]].eligibility
    return config.data.eligibility[profile].own_domain_min_test


def scope_members(scope: ExtensionScope) -> list[ExtensionScope]:
    return [
        label
        for label in (ExtensionScope.PRIMARY_SET, ExtensionScope.REPLICATION_SET)
        if scope in (label, ExtensionScope.POOLED)
    ]


def _arm_label() -> pl.Expr:
    condition, tuning = pl.col(Column.CONDITION), pl.col(Column.TUNING_VALUE)
    trimmed = tuning == Aggregation.TRIMMED_MEAN
    return (
        pl.when((condition == ExposureCondition.PLACEBO) & tuning.is_null())
        .then(pl.lit(ControlArm.PLACEBO))
        .when(condition == ExposureCondition.PEER_PRESENT)
        .then(
            pl.when(tuning.is_null())
            .then(pl.lit(ControlArm.PRESENT_MEAN))
            .when(trimmed)
            .then(pl.lit(ControlArm.PRESENT_TRIMMED))
            .otherwise(pl.lit(ControlArm.PRESENT_MEDIAN))
        )
        .when(condition == ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
        .then(
            pl.when(tuning.is_null())
            .then(pl.lit(ControlArm.ABSENT_MEAN))
            .when(trimmed)
            .then(pl.lit(ControlArm.ABSENT_TRIMMED))
            .otherwise(pl.lit(ControlArm.ABSENT_MEDIAN))
        )
    )


def contrasts() -> tuple[DiagnosticColumn, ...]:
    return (
        DiagnosticColumn.PLACEBO_EFFECT,
        DiagnosticColumn.CTK_MINUS_PLACEBO,
        DiagnosticColumn.CTK_MEAN,
        DiagnosticColumn.CTK_TRIMMED,
        DiagnosticColumn.CTK_MEDIAN,
        DiagnosticColumn.TRIMMED_MINUS_MEAN,
        DiagnosticColumn.MEDIAN_MINUS_MEAN,
    )


def _differences() -> list[pl.Expr]:
    def minus(first: ControlArm, second: ControlArm, name: DiagnosticColumn) -> pl.Expr:
        return (pl.col(first) - pl.col(second)).alias(name)

    return [
        minus(ControlArm.PLACEBO, ControlArm.ABSENT_MEAN, DiagnosticColumn.PLACEBO_EFFECT),
        minus(ControlArm.PRESENT_MEAN, ControlArm.PLACEBO, DiagnosticColumn.CTK_MINUS_PLACEBO),
        minus(ControlArm.PRESENT_MEAN, ControlArm.ABSENT_MEAN, DiagnosticColumn.CTK_MEAN),
        minus(ControlArm.PRESENT_TRIMMED, ControlArm.ABSENT_TRIMMED, DiagnosticColumn.CTK_TRIMMED),
        minus(ControlArm.PRESENT_MEDIAN, ControlArm.ABSENT_MEDIAN, DiagnosticColumn.CTK_MEDIAN),
    ]


def control_cells(
    families: FamilyCountsTable,
    exposure: ExposureTable,
    novelty: NoveltyTable,
    placebo: PlaceboTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
) -> DiagnosticTable:
    # One row per (set, seed, target client, hidden family, population, alpha): recall per
    # arm, placebo and aggregation contrasts, reallocation, peer support and relatedness.
    labels = set_labels(config, experiments)
    federation = pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE
    usable = (
        families.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
        .with_columns(_arm_label().alias(DiagnosticColumn.ARM))
        .filter(pl.col(DiagnosticColumn.ARM).is_not_null())
        .filter(
            pl.col(Column.TRIALS)
            >= pl.when(federation).then(1).otherwise(own_domain_minimum(config, experiments))
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .join(labels, on=Column.EXPERIMENT)
    )
    keys = [DiagnosticColumn.SET, Column.SEED, Column.CLIENT, Column.FAMILY]
    cells = (
        usable.pivot(
            on=DiagnosticColumn.ARM,
            index=[*keys, Column.POPULATION, Column.ALPHA],
            values=Column.RECALL,
        )
        .with_columns(_differences())
        .with_columns(
            (pl.col(DiagnosticColumn.CTK_TRIMMED) - pl.col(DiagnosticColumn.CTK_MEAN)).alias(
                DiagnosticColumn.TRIMMED_MINUS_MEAN
            ),
            (pl.col(DiagnosticColumn.CTK_MEDIAN) - pl.col(DiagnosticColumn.CTK_MEAN)).alias(
                DiagnosticColumn.MEDIAN_MINUS_MEAN
            ),
        )
    )
    pairs = placebo.join(labels, on=Column.EXPERIMENT).with_columns(
        (pl.col(DiagnosticColumn.REALLOCATED) / pl.col(DiagnosticColumn.NEED)).alias(
            DiagnosticColumn.REALLOCATED_SHARE
        ),
        (pl.col(DiagnosticColumn.REALLOCATED) > 0).alias(DiagnosticColumn.IS_REALLOCATED),
    )
    peers = (
        exposure.filter(
            (pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
            & pl.col(Column.TUNING_VALUE).is_null()
        )
        .join(labels, on=Column.EXPERIMENT)
        .join(
            pairs.select(
                DiagnosticColumn.SET,
                Column.SEED,
                Column.FAMILY,
                pl.col(Column.CLIENT).alias(Column.TARGET_CLIENT),
            ),
            on=[DiagnosticColumn.SET, Column.SEED, Column.FAMILY],
        )
        .filter(pl.col(Column.CLIENT) != pl.col(Column.TARGET_CLIENT))
        .group_by(
            DiagnosticColumn.SET,
            Column.SEED,
            Column.FAMILY,
            Column.TARGET_CLIENT,
            maintain_order=True,
        )
        .agg(
            (pl.col(Column.ROWS) > 0).sum().alias(DiagnosticColumn.PEERS),
            (pl.col(Column.ROWS) >= DiagnosticLimit.PEER_MIN_ROWS)
            .sum()
            .alias(DiagnosticColumn.SUBSTANTIAL_PEERS),
            (pl.col(Column.ROWS).max() / pl.col(Column.ROWS).sum()).alias(
                DiagnosticColumn.TOP_SHARE
            ),
            pl.col(Column.ROWS).sum().alias(Column.PEER_ROWS),
        )
        .rename({Column.TARGET_CLIENT: Column.CLIENT})
    )
    descriptors = (
        novelty.join(labels, on=Column.EXPERIMENT)
        .select(*keys, Column.DESCRIPTOR, Column.VALUE)
        .pivot(on=Column.DESCRIPTOR, index=keys, values=Column.VALUE)
    )
    return (
        cells.join(
            pairs.select(
                *keys,
                DiagnosticColumn.PLACEBO_FAMILY,
                DiagnosticColumn.NEED,
                DiagnosticColumn.REALLOCATED,
                DiagnosticColumn.REALLOCATED_SHARE,
                DiagnosticColumn.IS_REALLOCATED,
                DiagnosticColumn.CENTROID_DISTANCE,
                DiagnosticColumn.NEAREST_KNOWN_DISTANCE,
                DiagnosticColumn.PLACEBO_RANK,
                DiagnosticColumn.HIDDEN_PEER_FIT,
                DiagnosticColumn.PLACEBO_PEER_FIT,
            ),
            on=keys,
            how=LibraryOption.JOIN_LEFT,
        )
        .join(peers, on=keys, how=LibraryOption.JOIN_LEFT)
        .join(descriptors, on=keys, how=LibraryOption.JOIN_LEFT)
        .with_columns(
            (
                pl.col(DiagnosticColumn.PLACEBO_PEER_FIT) / pl.col(DiagnosticColumn.HIDDEN_PEER_FIT)
            ).alias(DiagnosticColumn.FIT_RATIO)
        )
    )


def _summary(values: DiagnosticVector, config: Config) -> DiagnosticSummary:
    interval = seeded_bca(values, config, DiagnosticSeed.CONTROLS, DiagnosticLimit.CLIENT_SEEDS)
    return DiagnosticSummary(
        count=values.size,
        mean=values.mean().item() if values.size else None,
        median=np.median(values).item() if values.size else None,
        positive_count=(values > 0).sum().item(),
        low=interval_low(interval),
        high=interval_high(interval),
    )


def _summary_row(summary: DiagnosticSummary) -> DiagnosticRow:
    return {
        DiagnosticColumn.N: summary.count,
        DiagnosticColumn.MEAN: summary.mean,
        DiagnosticColumn.MEDIAN: summary.median,
        DiagnosticColumn.POSITIVE: summary.positive_count,
        Column.CI_LOW: summary.low,
        Column.CI_HIGH: summary.high,
    }


def _seed_means(cells: DiagnosticTable, columns: tuple[DiagnosticColumn, ...]) -> DiagnosticTable:
    return (
        cells.group_by(Column.SEED, maintain_order=True)
        .agg(*(pl.col(column).mean() for column in columns), pl.len().alias(DiagnosticColumn.N))
        .sort(Column.SEED)
    )


def _vector(table: DiagnosticTable, column: DiagnosticColumn) -> DiagnosticVector:
    return table[column].drop_nulls().to_numpy().astype(np.float64)


def _stratum(cells: DiagnosticTable, stratum: ControlStratum) -> DiagnosticTable:
    return cells.filter(
        pl.col(DiagnosticColumn.SET).is_in(scope_members(stratum.scoped.scope))
        & (pl.col(Column.POPULATION) == stratum.population)
        & (pl.col(Column.ALPHA) == stratum.alpha)
    )


def _tag(stratum: ControlStratum) -> DiagnosticRow:
    return {
        DiagnosticColumn.SET: stratum.scoped.scope,
        Column.POPULATION: stratum.population,
        Column.ALPHA: stratum.alpha,
    }


def _strata(config: Config, experiments: tuple[ExperimentName, ...]) -> list[ControlStratum]:
    return [
        ControlStratum(scoped=scoped, population=population, alpha=alpha)
        for scoped in ordered_scopes(config, experiments)
        for population in (EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN)
        for alpha in config.experiments.operating.alphas
    ]


def _gate(contrast: DiagnosticColumn, row: DiagnosticSummary, config: Config) -> Passed:
    margin = config.statistics.gates.ctk_min_gain
    low, high = row.low, row.high
    if low is None or high is None:
        return False
    if contrast is DiagnosticColumn.PLACEBO_EFFECT:
        return low >= -margin and high <= margin
    if contrast in (DiagnosticColumn.TRIMMED_MINUS_MEAN, DiagnosticColumn.MEDIAN_MINUS_MEAN):
        return low > -margin
    return low > margin


def strata_effects(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        means = _seed_means(
            _stratum(cells, stratum),
            contrasts(),
        )
        for contrast in contrasts():
            summary = _summary(_vector(means, contrast), config)
            rows.append(
                {
                    **_tag(stratum),
                    Column.CONTRAST: contrast,
                    **_summary_row(summary),
                    DiagnosticColumn.GATE: _gate(contrast, summary, config),
                }
            )
    return rows


def client_effects(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    pair = (DiagnosticColumn.PLACEBO_EFFECT, DiagnosticColumn.CTK_MINUS_PLACEBO)
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        selected = _stratum(cells, stratum)
        for client in sorted(selected[Column.CLIENT].unique().to_list()):
            means = _seed_means(selected.filter(pl.col(Column.CLIENT) == client), pair)
            row: DiagnosticRow = {
                **_tag(stratum),
                Column.CLIENT: client,
                DiagnosticColumn.SEEDS: means.height,
            }
            if means.height >= DiagnosticLimit.CLIENT_SEEDS:
                for contrast in pair:
                    summary = _summary(means[contrast].to_numpy().astype(np.float64), config)
                    row |= {
                        DiagnosticColumnName(
                            f"{contrast}{DiagnosticColumn.MEAN_SUFFIX}"
                        ): summary.mean,
                        DiagnosticColumnName(
                            f"{contrast}{DiagnosticColumn.LOW_SUFFIX}"
                        ): summary.low,
                        DiagnosticColumnName(
                            f"{contrast}{DiagnosticColumn.HIGH_SUFFIX}"
                        ): summary.high,
                    }
            rows.append(row)
    return rows


def reallocation_effects(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    margin = config.statistics.gates.ctk_min_gain
    pair = (DiagnosticColumn.PLACEBO_EFFECT, DiagnosticColumn.CTK_MINUS_PLACEBO)
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        selected = _stratum(cells, stratum)
        means: StratumTables = {}
        for label, keep in (
            (ReallocationStratum.REALLOCATED, pl.col(DiagnosticColumn.IS_REALLOCATED)),
            (ReallocationStratum.NOT_REALLOCATED, ~pl.col(DiagnosticColumn.IS_REALLOCATED)),
        ):
            subset = selected.filter(keep)
            means[label] = _seed_means(subset, pair)
            placebo = _summary(_vector(means[label], pair[0]), config)
            beyond = _summary(_vector(means[label], pair[1]), config)
            low, high = placebo.low, placebo.high
            rows.append(
                {
                    **_tag(stratum),
                    DiagnosticColumn.STRATUM: label,
                    DiagnosticColumn.SEEDS: means[label].height,
                    DiagnosticColumn.CELLS: subset.height,
                    DiagnosticColumn.MEAN: placebo.mean,
                    Column.CI_LOW: low,
                    Column.CI_HIGH: high,
                    DiagnosticColumn.EQUIVALENT: low is not None
                    and high is not None
                    and low >= -margin
                    and high <= margin,
                    DiagnosticColumn.BEYOND_MEAN: beyond.mean,
                    DiagnosticColumn.BEYOND_LOW: beyond.low,
                    DiagnosticColumn.BEYOND: beyond.low is not None and beyond.low > margin,
                }
            )
        joined = means[ReallocationStratum.REALLOCATED].join(
            means[ReallocationStratum.NOT_REALLOCATED],
            on=Column.SEED,
            suffix=DiagnosticColumn.OTHER_SUFFIX,
        )
        difference = _summary(
            (joined[pair[0]] - joined[f"{pair[0]}{DiagnosticColumn.OTHER_SUFFIX}"])
            .to_numpy()
            .astype(np.float64),
            config,
        )
        rows.append(
            {
                **_tag(stratum),
                DiagnosticColumn.STRATUM: ReallocationStratum.DIFFERENCE,
                DiagnosticColumn.SEEDS: joined.height,
                DiagnosticColumn.MEAN: difference.mean,
                Column.CI_LOW: difference.low,
                Column.CI_HIGH: difference.high,
            }
        )
    return rows


def reallocation_slopes(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    tail = (1.0 - config.statistics.confidence_level) / 2.0
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        selected = _stratum(cells, stratum).drop_nulls(
            [DiagnosticColumn.PLACEBO_EFFECT, DiagnosticColumn.REALLOCATED_SHARE]
        )
        share = selected[DiagnosticColumn.REALLOCATED_SHARE].to_numpy().astype(np.float64)
        effect = selected[DiagnosticColumn.PLACEBO_EFFECT].to_numpy().astype(np.float64)
        fit = stats.linregress(share, effect)
        seeds = np.array(sorted(selected[Column.SEED].unique().to_list()))
        by_seed = {seed: selected.filter(pl.col(Column.SEED) == seed) for seed in seeds.tolist()}
        rng = np.random.default_rng(DiagnosticSeed.SLOPE)
        slopes: list[Effect] = []
        for _ in range(DiagnosticResamples.SLOPE):
            drawn = pl.concat([by_seed[seed] for seed in rng.choice(seeds, seeds.size).tolist()])
            x = drawn[DiagnosticColumn.REALLOCATED_SHARE].to_numpy().astype(np.float64)
            if np.ptp(x) > 0:
                y = drawn[DiagnosticColumn.PLACEBO_EFFECT].to_numpy().astype(np.float64)
                slopes.append(stats.linregress(x, y).slope.item())
        low, high = np.quantile(slopes, [tail, 1.0 - tail])
        rows.append(
            {
                **_tag(stratum),
                DiagnosticColumn.N: share.size,
                DiagnosticColumn.SLOPE: fit.slope.item(),
                DiagnosticColumn.SLOPE_LOW: low.item(),
                DiagnosticColumn.SLOPE_HIGH: high.item(),
                DiagnosticColumn.INTERCEPT: fit.intercept.item(),
                DiagnosticColumn.RHO: spearman(share, effect),
                Column.P_VALUE: spearman_p(share, effect),
            }
        )
    return rows


def _associations(
    selected: DiagnosticTable,
    outcome: DiagnosticColumn,
    descriptors: tuple[DiagnosticColumn | NoveltyDescriptor | Column, ...],
) -> DiagnosticRows:
    rows: DiagnosticRows = []
    for descriptor in descriptors:
        present = selected.drop_nulls([descriptor, outcome])
        first = present[descriptor].to_numpy().astype(np.float64)
        second = present[outcome].to_numpy().astype(np.float64)
        rows.append(
            {
                DiagnosticColumn.OUTCOME: outcome,
                DiagnosticColumn.PREDICTOR: descriptor,
                DiagnosticColumn.RHO: spearman(first, second),
                Column.P_VALUE: spearman_p(first, second),
            }
        )
    return rows


def associations(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    relatedness = (
        DiagnosticColumn.CENTROID_DISTANCE,
        DiagnosticColumn.PLACEBO_RANK,
        DiagnosticColumn.NEAREST_KNOWN_DISTANCE,
        DiagnosticColumn.FIT_RATIO,
        NoveltyDescriptor.CENTROID_DISTANCE_TO_KNOWN_MALWARE,
        NoveltyDescriptor.MAX_JACCARD_TO_KNOWN_FAMILY,
    )
    support = (
        DiagnosticColumn.TOP_SHARE,
        DiagnosticColumn.PEERS,
        DiagnosticColumn.SUBSTANTIAL_PEERS,
        Column.PEER_ROWS,
    )
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        selected = _stratum(cells, stratum)
        rows += [
            {**_tag(stratum), DiagnosticColumn.CELLS: selected.height, **row}
            for row in _associations(selected, DiagnosticColumn.PLACEBO_EFFECT, relatedness)
        ]
        attenuation = selected.drop_nulls(
            [DiagnosticColumn.TRIMMED_MINUS_MEAN, DiagnosticColumn.TOP_SHARE]
        )
        for outcome in (DiagnosticColumn.TRIMMED_MINUS_MEAN, DiagnosticColumn.MEDIAN_MINUS_MEAN):
            rows += [
                {**_tag(stratum), DiagnosticColumn.CELLS: attenuation.height, **row}
                for row in _associations(attenuation, outcome, support)
            ]
    return rows


def placebo_pairs(cells: DiagnosticTable, config: Config) -> DiagnosticTable:
    return with_class(
        cells.filter(pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        .group_by(
            DiagnosticColumn.SET,
            Column.POPULATION,
            Column.FAMILY,
            DiagnosticColumn.PLACEBO_FAMILY,
            maintain_order=True,
        )
        .agg(
            pl.len().alias(DiagnosticColumn.N),
            pl.col(DiagnosticColumn.PLACEBO_EFFECT).mean(),
            pl.col(DiagnosticColumn.CENTROID_DISTANCE).mean(),
            pl.col(DiagnosticColumn.PLACEBO_RANK).mean(),
        )
        .sort(
            DiagnosticColumn.SET,
            Column.POPULATION,
            DiagnosticColumn.PLACEBO_EFFECT,
            Column.FAMILY,
            DiagnosticColumn.PLACEBO_FAMILY,
        ),
        EvidenceClass.POST_HOC_DIAGNOSTIC,
    )


def family_effects(cells: DiagnosticTable) -> DiagnosticTable:
    means = (
        DiagnosticColumn.PLACEBO_EFFECT,
        DiagnosticColumn.CTK_MINUS_PLACEBO,
        DiagnosticColumn.CTK_MEAN,
        DiagnosticColumn.CTK_TRIMMED,
        DiagnosticColumn.CTK_MEDIAN,
        DiagnosticColumn.TRIMMED_MINUS_MEAN,
        DiagnosticColumn.MEDIAN_MINUS_MEAN,
        DiagnosticColumn.PEERS,
        DiagnosticColumn.SUBSTANTIAL_PEERS,
        DiagnosticColumn.TOP_SHARE,
        Column.PEER_ROWS,
    )
    return with_class(
        cells.group_by(
            DiagnosticColumn.SET,
            Column.POPULATION,
            Column.ALPHA,
            Column.FAMILY,
            maintain_order=True,
        )
        .agg(pl.len().alias(DiagnosticColumn.CELLS), *(pl.col(name).mean() for name in means))
        .sort(DiagnosticColumn.SET, Column.POPULATION, Column.ALPHA, Column.FAMILY),
        EvidenceClass.POST_HOC_DIAGNOSTIC,
    )


def _aggregation_columns() -> tuple[DiagnosticColumn, ...]:
    return contrasts()[2:]


def support_levels(cells: DiagnosticTable) -> DiagnosticTable:
    share = pl.col(DiagnosticColumn.TOP_SHARE)
    return with_class(
        cells.with_columns(
            pl.when(share >= PeerShare.SINGLE)
            .then(pl.lit(SupportStratum.SINGLE))
            .when(share >= PeerShare.DOMINANT)
            .then(pl.lit(SupportStratum.DOMINANT))
            .otherwise(pl.lit(SupportStratum.SPREAD))
            .alias(DiagnosticColumn.STRATUM)
        )
        .group_by(
            DiagnosticColumn.SET,
            Column.POPULATION,
            Column.ALPHA,
            DiagnosticColumn.STRATUM,
            maintain_order=True,
        )
        .agg(
            pl.len().alias(DiagnosticColumn.CELLS),
            *(pl.col(name).mean() for name in _aggregation_columns()),
        )
        .sort(DiagnosticColumn.SET, Column.POPULATION, Column.ALPHA, DiagnosticColumn.STRATUM),
        EvidenceClass.POST_HOC_DIAGNOSTIC,
    )


def support_effects(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    share = pl.col(DiagnosticColumn.TOP_SHARE)
    rows: DiagnosticRows = []
    for stratum in _strata(config, experiments):
        selected = _stratum(cells, stratum)
        for label, keep in (
            (SupportStratum.SINGLE_PEER, share >= PeerShare.SINGLE),
            (SupportStratum.MULTI_PEER, share < PeerShare.SINGLE),
        ):
            means = _seed_means(selected.filter(keep), _aggregation_columns())
            for contrast in _aggregation_columns():
                summary = _summary(means[contrast].to_numpy().astype(np.float64), config)
                rows.append(
                    {
                        **_tag(stratum),
                        DiagnosticColumn.STRATUM: label,
                        Column.CONTRAST: contrast,
                        DiagnosticColumn.SEEDS: means.height,
                        DiagnosticColumn.MEAN: summary.mean,
                        Column.CI_LOW: summary.low,
                        Column.CI_HIGH: summary.high,
                    }
                )
    return rows


def control_diagnostics(
    cells: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> ControlDiagnostics:
    evidence = EvidenceClass.POST_HOC_DIAGNOSTIC
    return ControlDiagnostics(
        strata=labelled(strata_effects(cells, config, experiments), evidence),
        clients=labelled(client_effects(cells, config, experiments), evidence),
        reallocation=labelled(reallocation_effects(cells, config, experiments), evidence),
        slopes=labelled(reallocation_slopes(cells, config, experiments), evidence),
        associations=labelled(associations(cells, config, experiments), evidence),
        placebo_pairs=placebo_pairs(cells, config),
        families=family_effects(cells),
        support_levels=support_levels(cells),
        support=labelled(support_effects(cells, config, experiments), evidence),
    )


def pair_ctk(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticTable:
    # CTK(d) = recall(d) - recall(dose 0) per target (client, family) pair; the natural
    # peer-present arm is carried as dose code -1.
    usable = families.filter(
        pl.col(Column.TRIALS)
        >= pl.when(pl.col(Column.POPULATION) == EvaluationPopulation.OWN_DOMAIN)
        .then(own_domain_minimum(config, experiments))
        .otherwise(1)
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    keys = [
        Column.EXPERIMENT,
        Column.SEED,
        Column.LEARNER,
        Column.POPULATION,
        Column.ALPHA,
        Column.CLIENT,
        Column.FAMILY,
    ]
    base = usable.filter(
        (pl.col(Column.CONDITION) == ExposureCondition.EXACT_DOSE) & (pl.col(Column.DOSE) == 0)
    ).select(*keys, pl.col(Column.RECALL).alias(Column.BASELINE))
    arms = usable.filter(
        pl.col(Column.CONDITION).is_in(
            [ExposureCondition.EXACT_DOSE, ExposureCondition.PEER_PRESENT]
        )
    ).with_columns(
        pl.when(pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
        .then(pl.lit(DoseCode.NATURAL, dtype=pl.Int64))
        .otherwise(pl.col(Column.DOSE))
        .alias(DiagnosticColumn.DOSE_CODE)
    )
    return (
        arms.join(base, on=keys)
        .with_columns((pl.col(Column.RECALL) - pl.col(Column.BASELINE)).alias(DiagnosticColumn.CTK))
        .join(set_labels(config, experiments), on=Column.EXPERIMENT)
    )


def seed_level(pairs: DiagnosticTable, scoped: ScopedExperiments) -> DiagnosticTable:
    # Pooled rows follow the official seed-paired convention: the family macro is taken over
    # the target pairs of both family sets within a seed.
    return (
        pairs.filter(pl.col(Column.EXPERIMENT).is_in(list(scoped.experiments)))
        .group_by(
            Column.SEED,
            Column.LEARNER,
            Column.POPULATION,
            Column.ALPHA,
            DiagnosticColumn.DOSE_CODE,
            maintain_order=True,
        )
        .agg(pl.col(DiagnosticColumn.CTK).mean())
    )


def family_seed_level(pairs: DiagnosticTable) -> DiagnosticTable:
    return pairs.group_by(
        DiagnosticColumn.SET,
        Column.SEED,
        Column.LEARNER,
        Column.POPULATION,
        Column.ALPHA,
        Column.FAMILY,
        DiagnosticColumn.DOSE_CODE,
        maintain_order=True,
    ).agg(pl.col(DiagnosticColumn.CTK).mean())


def dose_name(dose: SupportCount) -> DoseLabel:
    return DoseLabel(DoseLevel.NATURAL if dose == DoseCode.NATURAL else f"{dose}")


def wide_by_dose(table: DiagnosticTable) -> DiagnosticTable:
    return table.pivot(
        on=DiagnosticColumn.DOSE_CODE, index=Column.SEED, values=DiagnosticColumn.CTK
    ).sort(Column.SEED)


def _column(wide: DiagnosticTable, dose: SupportCount) -> DiagnosticVector:
    return wide[f"{dose}"].to_numpy().astype(np.float64)


def _bca(values: DiagnosticVector, config: Config) -> DiagnosticInterval:
    interval = seeded_bca(values, config, DiagnosticSeed.DOSE, StatisticsLimit.BCA_SEEDS)
    return DiagnosticInterval(low=interval_low(interval), high=interval_high(interval))


def _bca_row(interval: DiagnosticInterval) -> DiagnosticRow:
    return {Column.CI_LOW: interval.low, Column.CI_HIGH: interval.high}


def _role(
    learner: Learner, population: EvaluationPopulation, alpha: Alpha, config: Config
) -> DoseRole:
    primary = (
        learner is Learner.FEDAVG
        and population is EvaluationPopulation.FEDERATION_WIDE
        and alpha == config.experiments.operating.primary_alpha
    )
    return DoseRole.PRIMARY if primary else DoseRole.SECONDARY


def _selected(
    table: DiagnosticTable, learner: Learner, population: EvaluationPopulation, alpha: Alpha
) -> DiagnosticTable:
    return table.filter(
        (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.POPULATION) == population)
        & (pl.col(Column.ALPHA) == alpha)
    )


def _populations() -> tuple[EvaluationPopulation, ...]:
    return (EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN)


def ctk_by_dose(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = seed_level(pairs, scoped)
        for learner in (Learner.FEDAVG, Learner.CENTRAL):
            for population in _populations():
                for alpha in config.experiments.operating.alphas:
                    wide = wide_by_dose(_selected(level, learner, population, alpha))
                    for dose in (*doses, DoseCode.NATURAL):
                        values = _column(wide, dose)
                        rows.append(
                            {
                                DiagnosticColumn.SET: scoped.scope,
                                Column.LEARNER: learner,
                                Column.POPULATION: population,
                                Column.ALPHA: alpha,
                                Column.ROLE: _role(learner, population, alpha, config),
                                Column.DOSE: dose_name(dose),
                                DiagnosticColumn.N: values.size,
                                Column.MEAN_CTK: values.mean().item(),
                                **_bca_row(_bca(values, config)),
                                Column.POSITIVE_SEEDS: (values > 0).sum().item(),
                            }
                        )
    return rows


def dose_increments(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = seed_level(pairs, scoped)
        for learner in (Learner.FEDAVG, Learner.CENTRAL):
            for population in _populations():
                for alpha in config.experiments.operating.alphas:
                    wide = wide_by_dose(_selected(level, learner, population, alpha))
                    for low, high in pairwise(doses):
                        values = _column(wide, high) - _column(wide, low)
                        interval = _bca(values, config)
                        scale = DiagnosticLimit.DOSE_UNIT / (high - low)
                        lower, upper = interval.low, interval.high
                        rows.append(
                            {
                                DiagnosticColumn.SET: scoped.scope,
                                Column.LEARNER: learner,
                                Column.POPULATION: population,
                                Column.ALPHA: alpha,
                                Column.ROLE: _role(learner, population, alpha, config),
                                DiagnosticColumn.SEGMENT: f"{low}{Separator.ARROW}{high}",
                                DiagnosticColumn.N: values.size,
                                DiagnosticColumn.INCREMENT: values.mean().item(),
                                Column.CI_LOW: lower,
                                Column.CI_HIGH: upper,
                                DiagnosticColumn.PER_UNIT: values.mean().item() * scale,
                                DiagnosticColumn.PER_UNIT_LOW: None
                                if lower is None
                                else lower * scale,
                                DiagnosticColumn.PER_UNIT_HIGH: None
                                if upper is None
                                else upper * scale,
                            }
                        )
    return rows


def family_curves(families: DiagnosticTable, config: Config) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for population in _populations():
        selected = _selected(
            families, Learner.FEDAVG, population, config.experiments.operating.primary_alpha
        ).sort(DiagnosticColumn.SET, Column.FAMILY, maintain_order=True)
        for group in selected.partition_by(
            DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
        ):
            head = group.row(0, named=True)
            wide = wide_by_dose(group)
            for dose in (*doses, DoseCode.NATURAL):
                if f"{dose}" not in wide.columns:
                    continue
                values = wide[f"{dose}"].drop_nulls().to_numpy().astype(np.float64)
                rows.append(
                    {
                        DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                        Column.POPULATION: population,
                        Column.FAMILY: head[Column.FAMILY],
                        DiagnosticColumn.DOSE_CODE: dose,
                        Column.DOSE: dose_name(dose),
                        DiagnosticColumn.SEEDS: values.size,
                        Column.MEAN_CTK: values.mean().item(),
                        **_bca_row(_bca(values, config)),
                    }
                )
    return rows


def _onset(group: DiagnosticTable, criterion: pl.Expr) -> SupportCount | None:
    hits = group.filter((pl.col(DiagnosticColumn.DOSE_CODE) > 0) & criterion)
    return None if hits.height == 0 else hits[DiagnosticColumn.DOSE_CODE].item(0)


def family_summary(curves: DiagnosticTable, config: Config) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    onset = config.statistics.gates.ctk_min_gain
    rows: DiagnosticRows = []
    for group in curves.partition_by(
        Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
    ):
        head = group.row(0, named=True)
        means = {row[DiagnosticColumn.DOSE_CODE]: row for row in group.iter_rows(named=True)}
        end = means[doses[-1]]
        lower = end[Column.CI_LOW]
        first_mean = _onset(group, pl.col(Column.MEAN_CTK) >= onset)
        first_interval = _onset(
            group, pl.col(Column.CI_LOW).is_not_null() & (pl.col(Column.CI_LOW) > 0)
        )
        responsive = not (end[Column.MEAN_CTK] < onset or lower is None or lower <= 0)
        early = first_mean is not None and first_mean <= DiagnosticLimit.EARLY_ONSET
        response = (
            DoseResponseClass.NONRESPONSIVE
            if not responsive
            else DoseResponseClass.EARLY
            if early
            else DoseResponseClass.LATE
        )
        rows.append(
            {
                DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                Column.POPULATION: head[Column.POPULATION],
                Column.FAMILY: head[Column.FAMILY],
                DiagnosticColumn.SEEDS: end[DiagnosticColumn.SEEDS],
                **{
                    DiagnosticColumnName(f"{DiagnosticColumn.CTK}{dose}"): means[dose][
                        Column.MEAN_CTK
                    ]
                    for dose in doses[1:]
                },
                DiagnosticColumn.CTK_TOP_LOW: lower,
                DiagnosticColumn.CTK_TOP_HIGH: end[Column.CI_HIGH],
                DiagnosticColumn.NATURAL_CTK: means[DoseCode.NATURAL][Column.MEAN_CTK],
                DiagnosticColumn.ONSET_MEAN: first_mean,
                DiagnosticColumn.ONSET_INTERVAL: first_interval,
                DiagnosticColumn.RESPONSE_CLASS: response,
            }
        )
    return rows


def with_family_context(
    summary: DiagnosticTable, family_level: FamilyLevelTable, novelty: NoveltyTable
) -> DiagnosticTable:
    confirmatory = family_level.filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & pl.col(Column.EXPERIMENT).is_in(
            [ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET]
        )
    ).select(
        Column.FAMILY,
        Column.LOCAL_RECALL,
        Column.FULL_RECALL,
        pl.col(Column.CTK_GAIN).alias(DiagnosticColumn.CONFIRMATORY_CTK),
        pl.col(Column.NOVELTY).alias(DiagnosticColumn.CONFIRMATORY_NOVELTY),
    )
    dose_novelty = (
        novelty.filter(pl.col(Column.DESCRIPTOR) == NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE)
        .group_by(Column.FAMILY, maintain_order=True)
        .agg(pl.col(Column.VALUE).mean().alias(DiagnosticColumn.DOSE_NOVELTY))
    )
    return (
        summary.join(confirmatory, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .join(dose_novelty, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .sort(Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY)
    )


def family_associations(summary: DiagnosticTable, config: Config) -> DiagnosticRows:
    top = f"{DiagnosticColumn.CTK}{config.experiments.exact_dose_levels[-1]}"
    wide = summary.filter(pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    rows: DiagnosticRows = []
    for outcome in (top, DiagnosticColumn.ONSET_MEAN):
        for predictor in (
            Column.LOCAL_RECALL,
            Column.FULL_RECALL,
            DiagnosticColumn.CONFIRMATORY_CTK,
            DiagnosticColumn.NATURAL_CTK,
            DiagnosticColumn.CONFIRMATORY_NOVELTY,
            DiagnosticColumn.DOSE_NOVELTY,
        ):
            pair = wide.select(predictor, outcome).drop_nulls().to_numpy().astype(np.float64)
            if len(pair) < StatisticsLimit.ASSOCIATION_FAMILIES:
                continue
            rows.append(
                {
                    DiagnosticColumn.OUTCOME: outcome,
                    DiagnosticColumn.PREDICTOR: predictor,
                    Column.FAMILIES: len(pair),
                    DiagnosticColumn.RHO: spearman(pair[:, 0], pair[:, 1]),
                    Column.P_VALUE: spearman_p(pair[:, 0], pair[:, 1]),
                }
            )
    return rows


def client_curves(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    selected = pairs.filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(DiagnosticColumn.DOSE_CODE) >= 0)
    )
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = (
            selected.filter(pl.col(Column.EXPERIMENT).is_in(list(scoped.experiments)))
            .group_by(
                Column.SEED,
                Column.POPULATION,
                Column.CLIENT,
                DiagnosticColumn.DOSE_CODE,
                maintain_order=True,
            )
            .agg(pl.col(DiagnosticColumn.CTK).mean())
            .sort(Column.POPULATION, Column.CLIENT, maintain_order=True)
        )
        for group in level.partition_by(Column.POPULATION, Column.CLIENT, maintain_order=True):
            head = group.row(0, named=True)
            wide = wide_by_dose(group)
            if wide.height < DiagnosticLimit.CLIENT_SEEDS:
                continue
            for dose in doses[1:]:
                values = wide[f"{dose}"].drop_nulls().to_numpy().astype(np.float64)
                rows.append(
                    {
                        DiagnosticColumn.SET: scoped.scope,
                        Column.POPULATION: head[Column.POPULATION],
                        Column.CLIENT: head[Column.CLIENT],
                        DiagnosticColumn.SEEDS: wide.height,
                        Column.DOSE: dose_name(dose),
                        Column.MEAN_CTK: values.mean().item(),
                        **_bca_row(_bca(values, config)),
                    }
                )
    return rows


def log_linear(doses: DiagnosticVector, slope: Effect) -> DiagnosticVector:
    return slope * np.log1p(doses)


def emax_curve(doses: DiagnosticVector, top: Effect, half: Effect) -> DiagnosticVector:
    return top * doses / (half + doses)


def fit_curve(curves: DiagnosticMatrix, doses: DiagnosticVector, model: DoseModel) -> DoseFit:
    # Descriptive dose-response fits on the units x doses matrix (NaN cells dropped).
    level = np.tile(doses, curves.shape[0])
    outcome = curves.ravel()
    present = ~np.isnan(outcome)
    level, outcome = level[present], outcome[present]
    if model is DoseModel.LOG_LINEAR:
        transformed = np.log1p(level)
        slope = ((transformed @ outcome) / (transformed @ transformed)).item()
        return DoseFit(parameters=(slope,), predicted=log_linear(doses, slope))
    if model is DoseModel.EMAX:
        best: DoseFit | None = None
        best_error = np.inf
        for start in EmaxStart:
            with warnings.catch_warnings():
                warnings.simplefilter(LibraryOption.WARNINGS_IGNORE)
                try:
                    parameters, _ = optimize.curve_fit(
                        emax_curve,
                        level,
                        outcome,
                        p0=(max(outcome.max().item(), EmaxBound.START_FLOOR), start),
                        bounds=(
                            [EmaxBound.TOP_LOW, EmaxBound.HALF_LOW],
                            [EmaxBound.TOP_HIGH, EmaxBound.HALF_HIGH],
                        ),
                        maxfev=DiagnosticLimit.EMAX_EVALUATIONS,
                    )
                except (RuntimeError, ValueError):
                    continue
            top, half = parameters[0].item(), parameters[1].item()
            error = ((outcome - emax_curve(level, top, half)) ** 2).sum().item()
            if best is None or error < best_error:
                best_error = error
                best = DoseFit(parameters=(top, half), predicted=emax_curve(doses, top, half))
        if best is None:
            return DoseFit(parameters=(np.nan, np.nan), predicted=np.full(doses.size, np.nan))
        return best
    weights = (~np.isnan(curves)).sum(0)
    isotonic = IsotonicRegression(increasing=True).fit(
        doses, np.nanmean(curves, axis=0), sample_weight=weights
    )
    return DoseFit(parameters=(), predicted=isotonic.predict(doses))


def akaike(
    curves: DiagnosticMatrix, predicted: DiagnosticVector, parameters: SupportCount
) -> Effect:
    residuals = (curves - predicted[None, :]).ravel()
    residuals = residuals[~np.isnan(residuals)]
    size = residuals.size
    return (size * np.log((residuals**2).sum() / size) + 2 * (parameters + 1)).item()


def cross_validated(curves: DiagnosticMatrix, doses: DiagnosticVector, model: DoseModel) -> Effect:
    errors: list[Effect] = []
    for unit in range(curves.shape[0]):
        predicted = fit_curve(np.delete(curves, unit, 0), doses, model).predicted
        residual: DiagnosticVector = curves[unit] - predicted
        errors.append(np.nanmean(residual**2).item())
    return np.mean(errors).item()


def equivalent_dose(curve: DiagnosticVector, natural: Effect, doses: DiagnosticVector) -> Effect:
    # First dose at which the piecewise-linear mean curve reaches the natural-arm CTK.
    if natural <= curve[0]:
        return 0.0
    for index in range(1, doses.size):
        if curve[index] >= natural:
            low, high = curve[index - 1], curve[index]
            step = doses[index] - doses[index - 1]
            return (doses[index - 1] + (natural - low) / (high - low) * step).item()
    return np.inf


def _model_parameters(model: DoseModel, fit: DoseFit) -> SupportCount:
    if model is DoseModel.LOG_LINEAR:
        return 1
    if model is DoseModel.EMAX:
        return 2
    return np.unique(np.round(fit.predicted, DiagnosticLimit.ISOTONIC_DECIMALS)).size


def model_block(
    wide: DiagnosticTable,
    label: DoseLabel | ExtensionScope,
    config: Config,
    rng: np.random.Generator,
) -> DiagnosticRow:
    doses = config.experiments.exact_dose_levels
    grid = np.array(doses, dtype=np.float64)
    top = doses[-1]
    curves = wide.select([f"{dose}" for dose in doses]).to_numpy().astype(np.float64)
    natural = (
        wide[DoseCode.NATURAL].to_numpy().astype(np.float64)
        if DoseCode.NATURAL in wide.columns
        else None
    )
    units = curves.shape[0]
    row: DiagnosticRow = {DiagnosticColumn.CURVE: label, DiagnosticColumn.UNITS: units}
    for model in DoseModel:
        fit = fit_curve(curves, grid, model)
        row[DiagnosticColumnName(f"{DiagnosticColumn.AIC}{model}")] = akaike(
            curves, fit.predicted, _model_parameters(model, fit)
        )
        row[DiagnosticColumnName(f"{DiagnosticColumn.CV_MSE}{model}")] = (
            cross_validated(curves, grid, model) if units >= StatisticsLimit.BCA_SEEDS else np.nan
        )
        if model is DoseModel.EMAX:
            row[DiagnosticColumn.EMAX] = fit.parameters[0]
            row[DiagnosticColumn.ED50] = fit.parameters[1]
        if model is DoseModel.LOG_LINEAR:
            row[DiagnosticColumn.LOG_SLOPE] = fit.parameters[0]
    tops: list[Effect] = []
    halves: list[Effect] = []
    equivalents: list[Effect] = []
    for _ in range(DiagnosticResamples.DOSE_FIT):
        draw = rng.integers(0, units, units)
        fit = fit_curve(curves[draw], grid, DoseModel.EMAX)
        tops.append(fit.parameters[0])
        halves.append(fit.parameters[1])
        if natural is not None:
            equivalents.append(
                equivalent_dose(np.nanmean(curves[draw], 0), np.nanmean(natural[draw]).item(), grid)
            )
    tail = (1.0 - config.statistics.confidence_level) / 2.0
    top_limits = np.quantile(tops, [tail, 1.0 - tail])
    half_values = np.array(halves)
    half_limits = np.quantile(half_values, [tail, 1.0 - tail])
    at_bound = (half_values > EmaxBound.HALF_AT_BOUND).mean().item()
    row |= {
        DiagnosticColumn.EMAX_LOW: top_limits[0].item(),
        DiagnosticColumn.EMAX_HIGH: top_limits[1].item(),
        DiagnosticColumn.ED50_LOW: half_limits[0].item(),
        DiagnosticColumn.ED50_HIGH: half_limits[1].item(),
        DiagnosticColumn.ED50_BEYOND_TOP: (half_values > top).mean().item(),
        DiagnosticColumn.ED50_AT_BOUND: at_bound,
        DiagnosticColumn.ED50_IDENTIFIED: half_limits[1].item() <= top and at_bound < tail,
    }
    if natural is not None:
        mean_curve = np.nanmean(curves, 0)
        equivalent = np.array(equivalents)
        # Resamples that never reach the natural CTK are +inf; their limits stay inf/NaN.
        with np.errstate(invalid=LibraryOption.WARNINGS_IGNORE):
            limits = np.quantile(equivalent, [tail, 1.0 - tail])
        row |= {
            DiagnosticColumn.NATURAL_CTK: np.nanmean(natural).item(),
            DiagnosticColumnName(f"{DiagnosticColumn.CTK}{top}"): mean_curve[-1].item(),
            DiagnosticColumn.EQUIVALENT_DOSE: equivalent_dose(
                mean_curve, np.nanmean(natural).item(), grid
            ),
            DiagnosticColumn.EQUIVALENT_LOW: limits[0].item(),
            DiagnosticColumn.EQUIVALENT_HIGH: limits[1].item(),
            DiagnosticColumn.EQUIVALENT_BEYOND_TOP: np.isinf(equivalent).mean().item(),
        }
    return row


def model_fits(
    pairs: DiagnosticTable,
    families: DiagnosticTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    rng: np.random.Generator,
) -> DiagnosticRows:
    alpha = config.experiments.operating.primary_alpha
    population = EvaluationPopulation.FEDERATION_WIDE
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        wide = wide_by_dose(_selected(seed_level(pairs, scoped), Learner.FEDAVG, population, alpha))
        rows.append(
            {
                DiagnosticColumn.FIT_LEVEL: DoseFitLevel.FAMILY_MACRO,
                DiagnosticColumn.SET: scoped.scope,
                **model_block(wide, scoped.scope, config, rng),
            }
        )
    selected = _selected(families, Learner.FEDAVG, population, alpha).sort(
        DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
    )
    for group in selected.partition_by(DiagnosticColumn.SET, Column.FAMILY, maintain_order=True):
        head = group.row(0, named=True)
        wide = wide_by_dose(group)
        if wide.height >= DiagnosticLimit.FIT_SEEDS:
            rows.append(
                {
                    DiagnosticColumn.FIT_LEVEL: DoseFitLevel.FAMILY,
                    DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                    **model_block(wide, head[Column.FAMILY], config, rng),
                }
            )
    return rows


def _between_within(groups: list[DiagnosticVector]) -> DiagnosticVector:
    count = len(groups)
    total = sum(group.size for group in groups)
    grand = np.concatenate(groups).mean()
    between = sum(group.size * (group.mean() - grand) ** 2 for group in groups)
    within = sum(((group - group.mean()) ** 2).sum() for group in groups)
    size = (total - sum(group.size**2 for group in groups) / total) / (count - 1)
    return np.array([between, within, between / (count - 1), within / (total - count), size])


def _icc(groups: list[DiagnosticVector]) -> Effect:
    _, _, between, within, size = _between_within(groups)
    component = max((between - within) / size, 0.0)
    return (component / (component + within)).item() if component + within > 0 else np.nan


def heterogeneity(
    families: DiagnosticTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    rng: np.random.Generator,
) -> DiagnosticRows:
    top = config.experiments.exact_dose_levels[-1]
    alpha = config.experiments.operating.primary_alpha
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        members = scope_members(scoped.scope)
        for population in _populations():
            selected = (
                _selected(families, Learner.FEDAVG, population, alpha)
                .filter(
                    (pl.col(DiagnosticColumn.DOSE_CODE) == top)
                    & pl.col(DiagnosticColumn.SET).is_in(members)
                )
                .sort(DiagnosticColumn.SET, Column.FAMILY, Column.SEED, maintain_order=True)
            )
            groups = [
                group[DiagnosticColumn.CTK].to_numpy().astype(np.float64)
                for group in selected.partition_by(
                    DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
                )
            ]
            count = len(groups)
            between_sum, within_sum, between, within, size = _between_within(groups)
            component = max((between - within) / size, 0.0)
            resampled = np.array(
                [
                    _icc([groups[index] for index in rng.integers(0, count, count)])
                    for _ in range(DiagnosticResamples.DOSE_FIT)
                ]
            )
            interval = percentile_limits(resampled, config)
            rows.append(
                {
                    DiagnosticColumn.SET: scoped.scope,
                    Column.POPULATION: population,
                    Column.FAMILIES: count,
                    DiagnosticColumn.UNITS: sum(group.size for group in groups),
                    DiagnosticColumn.VARIANCE_BETWEEN: component,
                    DiagnosticColumn.VARIANCE_WITHIN: within.item(),
                    DiagnosticColumn.ICC: (component / (component + within)).item(),
                    DiagnosticColumn.ICC_LOW: interval_low(interval),
                    DiagnosticColumn.ICC_HIGH: interval_high(interval),
                    DiagnosticColumn.ETA_SQUARED: (between_sum / (between_sum + within_sum)).item(),
                    Column.P_VALUE: stats.f_oneway(*groups).pvalue.item(),
                }
            )
    return rows


def dose_diagnostics(
    families: FamilyCountsTable,
    novelty: NoveltyTable,
    family_level: FamilyLevelTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
) -> DoseDiagnostics:
    evidence = EvidenceClass.POST_HOC_DIAGNOSTIC
    pairs = pair_ctk(families, config, experiments)
    by_family = family_seed_level(pairs)
    curves = labelled(family_curves(by_family, config), evidence)
    summary = with_family_context(
        labelled(family_summary(curves, config), evidence), family_level, novelty
    )
    rng = np.random.default_rng(DiagnosticSeed.DOSE)
    return DoseDiagnostics(
        curve=labelled(ctk_by_dose(pairs, config, experiments), evidence),
        increments=labelled(dose_increments(pairs, config, experiments), evidence),
        family_curves=curves.drop(DiagnosticColumn.DOSE_CODE).sort(
            Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY, Column.DOSE
        ),
        family_summary=summary,
        associations=labelled(family_associations(summary, config), evidence),
        client_curves=labelled(client_curves(pairs, config, experiments), evidence),
        model_fits=labelled(model_fits(pairs, by_family, config, experiments, rng), evidence).sort(
            DiagnosticColumn.FIT_LEVEL, DiagnosticColumn.SET, DiagnosticColumn.CURVE
        ),
        heterogeneity=labelled(heterogeneity(by_family, config, experiments, rng), evidence),
    )


def equal_fpr_arms() -> tuple[ArmKey, ...]:
    return (
        ArmKey(learner=Learner.CENTRAL, condition=ExposureCondition.FULL_EXPOSURE, dose=None),
        ArmKey(learner=Learner.FEDAVG, condition=ExposureCondition.PEER_PRESENT, dose=None),
        ArmKey(
            learner=Learner.FEDAVG,
            condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE,
            dose=None,
        ),
    )


def arm_name(arm: ArmKey) -> ArmLabel:
    return ArmLabel(f"{arm.learner}{NameFragment.ARM_SEPARATOR}{arm.condition}")


def recall_at_fpr(negatives: DiagnosticVector, positives: DiagnosticVector, fpr: Alpha) -> Effect:
    # Empirical ROC over the target's own-domain test benign rows and the hidden family's
    # federation-wide test rows; TPR is linearly interpolated at the requested FPR.
    truth = np.r_[np.zeros(negatives.size), np.ones(positives.size)]
    false_rate, true_rate, _ = roc_curve(
        truth, np.r_[negatives, positives], drop_intermediate=False
    )
    return np.interp(fpr, false_rate, true_rate).item()


def _arm_filter(arm: ArmKey, client: pl.Expr) -> pl.Expr:
    return (
        (pl.col(Column.LEARNER) == arm.learner)
        & (pl.col(Column.CONDITION) == arm.condition)
        & (pl.col(Column.CLIENT) == client)
    )


def scored_targets(run: ScoredRun, config: Config) -> DiagnosticRows:
    alpha = config.experiments.operating.primary_alpha
    study = run.study
    label = study[Column.LABEL].to_numpy()
    client = study[Column.CLIENT].cast(pl.String).to_numpy()
    role = study[Column.ROLE].cast(pl.String).to_numpy()
    family = study[Column.FAMILY].to_numpy()
    at_alpha = (pl.col(Column.ALPHA) == alpha) & pl.col(Column.DOSE).is_null()
    thresholds = run.thresholds.filter(at_alpha)
    families = run.families.filter(
        at_alpha & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    )
    operating = run.operating.filter(at_alpha)
    rows: DiagnosticRows = []
    for arm in equal_fpr_arms():
        scores = run.scores[arm.label()]
        for target in run.targets:
            part = scores.filter(pl.col(Column.TARGET_CLIENT) == target.client)
            index = part[Column.ROW].to_numpy()
            values = part[Column.SCORE].to_numpy().astype(np.float64)
            test = role[index] == SplitRole.TEST
            negatives = values[test & (client[index] == target.client) & (label[index] == 0)]
            positives = values[test & (label[index] == 1) & (family[index] == target.family)]
            key = _arm_filter(arm, pl.lit(target.client))
            threshold = thresholds.filter(key)[Column.THRESHOLD].item()
            stored = families.filter(key & (pl.col(Column.FAMILY) == target.family)).row(
                0, named=True
            )
            trials = stored[Column.TRIALS]
            rows.append(
                {
                    Column.REPRESENTATION: run.representation,
                    Column.SEED: run.seed,
                    DiagnosticColumn.ARM: arm_name(arm),
                    Column.CLIENT: target.client,
                    Column.FAMILY: target.family,
                    DiagnosticColumn.BENIGN_TEST: negatives.size,
                    DiagnosticColumn.POSITIVE_TEST: positives.size,
                    Column.THRESHOLD: threshold,
                    DiagnosticColumn.CALIBRATED_RECALL: (positives > threshold).mean().item()
                    if positives.size
                    else np.nan,
                    DiagnosticColumn.CALIBRATED_FPR: (negatives > threshold).mean().item(),
                    DiagnosticColumn.EQUAL_FPR_RECALL: recall_at_fpr(negatives, positives, alpha)
                    if positives.size
                    else np.nan,
                    DiagnosticColumn.STORED_RECALL: stored[Column.HITS] / trials
                    if trials
                    else np.nan,
                    DiagnosticColumn.STORED_FPR: operating.filter(key)[Column.VALUE].item(),
                    DiagnosticColumn.STORED_TRIALS: trials,
                }
            )
    return rows


def score_health(run: ScoredRun) -> DiagnosticRows:
    rows: DiagnosticRows = []
    for name in sorted(run.scores):
        values = run.scores[name][Column.SCORE].to_numpy().astype(np.float64)
        magnitude = np.abs(values)
        rows.append(
            {
                Column.REPRESENTATION: run.representation,
                Column.SEED: run.seed,
                DiagnosticColumn.ARM: name,
                DiagnosticColumn.SCORES: values.size,
                DiagnosticColumn.NONFINITE: (~np.isfinite(values)).sum().item(),
                DiagnosticColumn.MINIMUM: np.nanmin(values).item(),
                DiagnosticColumn.MAXIMUM: np.nanmax(values).item(),
                DiagnosticColumn.ABOVE_LARGE: (magnitude > ScoreMagnitude.LARGE).sum().item(),
                DiagnosticColumn.ABOVE_EXTREME: (magnitude > ScoreMagnitude.EXTREME).sum().item(),
            }
        )
    return rows


def _groups(targets: DiagnosticTable, value: DiagnosticColumn, config: Config) -> DiagnosticTable:
    keys = [Column.REPRESENTATION, Column.SEED, DiagnosticColumn.ARM]
    experiments = config.experiments
    by_family = targets.group_by(*keys, Column.FAMILY, maintain_order=True).agg(
        pl.col(value).mean()
    )
    single = [
        *experiments.representation_priority_families,
        *experiments.representation_separate_families,
    ]
    parts = [
        by_family.filter(pl.col(Column.FAMILY).is_in(single)).rename({Column.FAMILY: Column.GROUP})
    ]
    for group, members in (
        (RepresentationGroup.PRIORITY_MACRO, experiments.representation_priority_families),
        (RepresentationGroup.CONTRAST_MACRO, experiments.representation_contrast_families),
    ):
        parts.append(
            by_family.filter(pl.col(Column.FAMILY).is_in(list(members)))
            .group_by(*keys, maintain_order=True)
            .agg(pl.col(value).mean())
            .with_columns(pl.lit(group).alias(Column.GROUP))
            .select(parts[0].columns)
        )
    return pl.concat(parts)


def _effect_rows(
    cells: DiagnosticTable, value: DiagnosticColumn, reading: OperatingReading, config: Config
) -> DiagnosticRows:
    keys = [Column.SEED, DiagnosticColumn.ARM, Column.GROUP]
    reference = cells.filter(pl.col(Column.REPRESENTATION) == Representation.LAMDA_STATIC).select(
        *keys, pl.col(value).alias(DiagnosticColumn.REFERENCE)
    )
    paired = cells.filter(pl.col(Column.REPRESENTATION) != Representation.LAMDA_STATIC).join(
        reference, on=keys
    )
    rows: DiagnosticRows = []
    for group in paired.sort(Column.SEED).partition_by(
        Column.REPRESENTATION, DiagnosticColumn.ARM, Column.GROUP, maintain_order=True
    ):
        head = group.row(0, named=True)
        differences = (group[value] - group[DiagnosticColumn.REFERENCE]).to_numpy()
        interval = bca_interval(differences, config.statistics)
        level = group[value].mean()
        if not isinstance(level, int | float) or isinstance(level, bool):
            raise ValueError(ErrorMessage.INVALID_DIAGNOSTIC_VALUE)
        reference_level = group[DiagnosticColumn.REFERENCE].mean()
        if not isinstance(reference_level, int | float) or isinstance(reference_level, bool):
            raise ValueError(ErrorMessage.INVALID_DIAGNOSTIC_VALUE)
        row: DiagnosticRow = {
            DiagnosticColumn.READING: reading,
            DiagnosticColumn.ARM: ArmLabel(head[DiagnosticColumn.ARM]),
            Column.GROUP: RepresentationGroup(head[Column.GROUP]),
            Column.REPRESENTATION: Representation(head[Column.REPRESENTATION]),
            DiagnosticColumn.SEEDS: differences.size,
            Column.LEVEL: level,
            DiagnosticColumn.REFERENCE: reference_level,
            DiagnosticColumn.DIFF: differences.mean().item(),
            DiagnosticColumn.POSITIVE: (differences > 0).sum().item(),
            Column.CI_LOW: interval_low(interval),
            Column.CI_HIGH: interval_high(interval),
        }
        rows.append(row)
    return rows


def equal_fpr_effects(targets: DiagnosticTable, config: Config) -> DiagnosticTable:
    present, absent = (arm_name(arm) for arm in equal_fpr_arms()[1:])
    rows: DiagnosticRows = []
    for value, reading in (
        (DiagnosticColumn.CALIBRATED_RECALL, OperatingReading.CALIBRATED),
        (DiagnosticColumn.EQUAL_FPR_RECALL, OperatingReading.EQUAL_TEST_FPR),
    ):
        cells = _groups(targets, value, config)
        rows += _effect_rows(cells, value, reading, config)
        wide = cells.filter(pl.col(DiagnosticColumn.ARM).is_in([present, absent])).pivot(
            on=DiagnosticColumn.ARM,
            index=[Column.REPRESENTATION, Column.SEED, Column.GROUP],
            values=value,
        )
        ctk = wide.select(
            Column.REPRESENTATION,
            Column.SEED,
            Column.GROUP,
            (pl.col(present) - pl.col(absent)).alias(value),
        ).with_columns(pl.lit(RepresentationMeasure.CTK).alias(DiagnosticColumn.ARM))
        rows += _effect_rows(ctk, value, reading, config)
    return labelled(rows, EvidenceClass.POST_HOC_DIAGNOSTIC).sort(
        DiagnosticColumn.ARM, Column.GROUP, Column.REPRESENTATION, DiagnosticColumn.READING
    )
