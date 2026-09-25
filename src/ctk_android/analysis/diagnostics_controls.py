import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.diagnostics_statistics import (
    interval_high,
    interval_low,
    labelled,
    ordered_scopes,
    own_domain_minimum,
    scope_members,
    seeded_bca,
    set_labels,
    spearman,
    spearman_p,
    with_class,
)
from ctk_android.config import Config
from ctk_android.enums import (
    Aggregation,
    Column,
    ControlArm,
    DiagnosticColumn,
    DiagnosticLimit,
    DiagnosticResamples,
    DiagnosticSeed,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    Learner,
    LibraryOption,
    NoveltyDescriptor,
    PeerShare,
    ReallocationStratum,
    SupportStratum,
)
from ctk_android.types import (
    ControlDiagnostics,
    ControlStratum,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    Effect,
    ExposureTable,
    FamilyCountsTable,
    NoveltyTable,
    Passed,
    PlaceboTable,
    StratumTables,
)


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


def _summary(values: DiagnosticVector, config: Config) -> DiagnosticRow:
    interval = seeded_bca(values, config, DiagnosticSeed.CONTROLS, DiagnosticLimit.CLIENT_SEEDS)
    return {
        DiagnosticColumn.N: values.size,
        DiagnosticColumn.MEAN: values.mean().item() if values.size else None,
        DiagnosticColumn.MEDIAN: np.median(values).item() if values.size else None,
        DiagnosticColumn.POSITIVE: (values > 0).sum().item(),
        Column.CI_LOW: interval_low(interval),
        Column.CI_HIGH: interval_high(interval),
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


def _gate(contrast: DiagnosticColumn, row: DiagnosticRow, config: Config) -> Passed:
    margin = config.statistics.gates.ctk_min_gain
    low, high = row[Column.CI_LOW], row[Column.CI_HIGH]
    if low is None:
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
                    **summary,
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
                        f"{contrast}{DiagnosticColumn.MEAN_SUFFIX}": summary[DiagnosticColumn.MEAN],
                        f"{contrast}{DiagnosticColumn.LOW_SUFFIX}": summary[Column.CI_LOW],
                        f"{contrast}{DiagnosticColumn.HIGH_SUFFIX}": summary[Column.CI_HIGH],
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
            low, high = placebo[Column.CI_LOW], placebo[Column.CI_HIGH]
            rows.append(
                {
                    **_tag(stratum),
                    DiagnosticColumn.STRATUM: label,
                    DiagnosticColumn.SEEDS: means[label].height,
                    DiagnosticColumn.CELLS: subset.height,
                    DiagnosticColumn.MEAN: placebo[DiagnosticColumn.MEAN],
                    Column.CI_LOW: low,
                    Column.CI_HIGH: high,
                    DiagnosticColumn.EQUIVALENT: low is not None
                    and low >= -margin
                    and high <= margin,
                    DiagnosticColumn.BEYOND_MEAN: beyond[DiagnosticColumn.MEAN],
                    DiagnosticColumn.BEYOND_LOW: beyond[Column.CI_LOW],
                    DiagnosticColumn.BEYOND: beyond[Column.CI_LOW] is not None
                    and beyond[Column.CI_LOW] > margin,
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
                DiagnosticColumn.MEAN: difference[DiagnosticColumn.MEAN],
                Column.CI_LOW: difference[Column.CI_LOW],
                Column.CI_HIGH: difference[Column.CI_HIGH],
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
                        DiagnosticColumn.MEAN: summary[DiagnosticColumn.MEAN],
                        Column.CI_LOW: summary[Column.CI_LOW],
                        Column.CI_HIGH: summary[Column.CI_HIGH],
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
