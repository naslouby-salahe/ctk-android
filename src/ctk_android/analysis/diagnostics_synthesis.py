import numpy as np
import polars as pl

from ctk_android.analysis.diagnostics_statistics import (
    interval_high,
    interval_low,
    labelled,
    percentile_limits,
    spearman,
    with_class,
)
from ctk_android.config import Config
from ctk_android.enums import (
    Column,
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
    Separator,
    TaxonomyLabel,
)
from ctk_android.types import (
    ArmName,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    ExposureTable,
    FamilyCountsTable,
    LargeFamilyTable,
    NoveltyTable,
    SynthesisDiagnostics,
    TargetsTable,
)


def synthesis_experiments() -> tuple[ExperimentName, ...]:
    return (
        ExperimentName.CONTROLLED_EXPOSURE,
        ExperimentName.REPLICATION_FAMILY_SET,
        ExperimentName.NATURAL_SCARCITY,
        ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR,
        ExperimentName.MODEL_FAMILY_REPLICATION_TREES,
    )


def _arm(learner: Learner, condition: ExposureCondition) -> ArmName:
    return f"{learner}{Separator.PIPE}{condition}"


def _support(exposure: ExposureTable, targets: TargetsTable) -> DiagnosticTable:
    learner = (
        Learner.FEDAVG if (exposure[Column.LEARNER] == Learner.FEDAVG).any() else Learner.CENTRAL
    )
    rows = exposure.filter(pl.col(Column.LEARNER) == learner)
    present = pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT
    full = pl.col(Column.CONDITION) == ExposureCondition.FULL_EXPOSURE
    records: DiagnosticRows = []
    for target in targets.iter_rows(named=True):
        client, family = target[Column.CLIENT], target[Column.FAMILY]
        own = rows.filter(pl.col(Column.FAMILY) == family)
        mine = pl.col(Column.CLIENT) == client
        records.append(
            {
                Column.CLIENT: client,
                Column.FAMILY: family,
                DiagnosticColumn.PEER_SUPPORT: own.filter(present & ~mine)[Column.ROWS].sum(),
                DiagnosticColumn.TARGET_SUPPORT_PRESENT: own.filter(present & mine)[
                    Column.ROWS
                ].sum(),
                DiagnosticColumn.TARGET_SUPPORT_FULL: own.filter(full & mine)[Column.ROWS].sum(),
            }
        )
    return pl.DataFrame(records)


def _run_cells(
    families: FamilyCountsTable,
    exposure: ExposureTable,
    novelty: NoveltyTable,
    targets: TargetsTable,
    config: Config,
) -> DiagnosticTable:
    pairs = targets.select(Column.CLIENT, Column.FAMILY)
    usable = (
        families.filter(
            (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
            & pl.col(Column.DOSE).is_null()
            & pl.col(Column.PARAMETER).is_null()
            & (pl.col(Column.TRIALS) > 0)
        )
        .join(pairs, on=[Column.CLIENT, Column.FAMILY], maintain_order=LibraryOption.JOIN_LEFT)
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    )
    index = [Column.CLIENT, Column.FAMILY, Column.POPULATION]
    wide = usable.with_columns(
        (pl.col(Column.LEARNER) + Separator.PIPE + pl.col(Column.CONDITION)).alias(
            DiagnosticColumn.ARM
        )
    ).pivot(on=DiagnosticColumn.ARM, index=index, values=Column.RECALL)
    trials = usable.filter(pl.col(Column.LEARNER) == Learner.LOCAL).select(*index, Column.TRIALS)
    descriptors = novelty.select(
        Column.CLIENT, Column.FAMILY, Column.DESCRIPTOR, Column.VALUE
    ).pivot(on=Column.DESCRIPTOR, index=[Column.CLIENT, Column.FAMILY], values=Column.VALUE)
    arms = exposure.filter(pl.col(Column.DOSE).is_null() & pl.col(Column.PARAMETER).is_null())
    return (
        wide.join(trials, on=index, how=LibraryOption.JOIN_LEFT)
        .join(
            _support(arms, targets), on=[Column.CLIENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT
        )
        .join(descriptors, on=[Column.CLIENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT)
    )


def _arm_column(cells: DiagnosticTable, learner: Learner, condition: ExposureCondition) -> pl.Expr:
    name = _arm(learner, condition)
    return pl.col(name) if name in cells.columns else pl.lit(None, pl.Float64)


def synthesis_cells(
    families: FamilyCountsTable,
    exposure: ExposureTable,
    novelty: NoveltyTable,
    targets: TargetsTable,
    config: Config,
) -> DiagnosticTable:
    # Cell-level table (experiment x seed x target client x family x population x learner);
    # CTK = peer - absent, pooling = absent - local, total = peer - local.
    runs: list[DiagnosticTable] = []
    for experiment in synthesis_experiments():
        here = pl.col(Column.EXPERIMENT) == experiment
        for seed in sorted(targets.filter(here)[Column.SEED].unique().to_list()):
            run = here & (pl.col(Column.SEED) == seed)
            runs.append(
                _run_cells(
                    families.filter(run),
                    exposure.filter(run),
                    novelty.filter(run),
                    targets.filter(run),
                    config,
                ).with_columns(
                    pl.lit(experiment).alias(Column.EXPERIMENT), pl.lit(seed).alias(Column.SEED)
                )
            )
    cells = pl.concat(runs, how=LibraryOption.CONCAT_DIAGONAL_RELAXED)
    parts: list[DiagnosticTable] = []
    for learner in (
        Learner.FEDAVG,
        Learner.CENTRAL,
        Learner.FEDPROX,
        Learner.FEDAVG_FINETUNE,
        Learner.BLEND,
    ):
        parts.append(
            cells.select(
                Column.EXPERIMENT,
                Column.SEED,
                Column.CLIENT,
                Column.FAMILY,
                Column.POPULATION,
                Column.TRIALS,
                DiagnosticColumn.PEER_SUPPORT,
                DiagnosticColumn.TARGET_SUPPORT_PRESENT,
                DiagnosticColumn.TARGET_SUPPORT_FULL,
                *(pl.col(descriptor) for descriptor in NoveltyDescriptor),
                pl.lit(learner).alias(Column.LEARNER),
                _arm_column(cells, Learner.LOCAL, ExposureCondition.PEER_PRESENT).alias(
                    Column.LOCAL_RECALL
                ),
                _arm_column(cells, learner, ExposureCondition.PEER_PRESENT).alias(
                    Column.PEER_RECALL
                ),
                _arm_column(cells, learner, ExposureCondition.FAMILY_ABSENT_EVERYWHERE).alias(
                    Column.ABSENT_RECALL
                ),
                _arm_column(cells, learner, ExposureCondition.FULL_EXPOSURE).alias(
                    Column.FULL_RECALL
                ),
                _arm_column(cells, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE).alias(
                    DiagnosticColumn.CENTRAL_FULL_RECALL
                ),
            )
        )
    peer, absent = pl.col(Column.PEER_RECALL), pl.col(Column.ABSENT_RECALL)
    local, full = pl.col(Column.LOCAL_RECALL), pl.col(Column.FULL_RECALL)
    return with_class(
        pl.concat(parts)
        .filter(peer.is_not_null())
        .with_columns(
            (peer - absent).alias(DiagnosticColumn.CTK),
            (absent - local).alias(DiagnosticColumn.POOLING),
            (peer - local).alias(DiagnosticColumn.TOTAL),
            (full - local).alias(DiagnosticColumn.HEADROOM),
            (full - peer).alias(DiagnosticColumn.RESIDUAL_GAP),
        ),
        EvidenceClass.POST_CONFIRMATORY,
    )


def seed_interval(
    table: DiagnosticTable,
    column: DiagnosticColumn | Column,
    keys: list[Column],
    rng: np.random.Generator,
    config: Config,
) -> DiagnosticTable:
    # Mean over seeds of per-seed means with a percentile bootstrap over seeds.
    rows: DiagnosticRows = []
    for group in table.partition_by(keys, maintain_order=True):
        head = group.row(0, named=True)
        means = (
            group.group_by(Column.SEED, maintain_order=True)
            .agg(pl.col(column).mean())
            .sort(Column.SEED)[column]
            .drop_nulls()
            .to_numpy()
            .astype(np.float64)
        )
        if means.size == 0:
            continue
        draws = rng.choice(means, (DiagnosticResamples.TAXONOMY, means.size)).mean(1)
        interval = percentile_limits(draws, config)
        rows.append(
            {
                **{key: head[key] for key in keys},
                column: means.mean().item(),
                f"{column}{DiagnosticColumn.LOW_SUFFIX}": interval_low(interval),
                f"{column}{DiagnosticColumn.HIGH_SUFFIX}": interval_high(interval),
                f"{column}{DiagnosticColumn.SEEDS_SUFFIX}": means.size,
                f"{column}{DiagnosticColumn.POSITIVE_SUFFIX}": (means > 0).sum().item(),
            }
        )
    return pl.DataFrame(rows)


def _labels(flags: tuple[TaxonomyLabel, ...]) -> list[pl.Expr]:
    return [
        pl.sum_horizontal([pl.col(flag).cast(pl.Int32) for flag in flags]).alias(
            DiagnosticColumn.LABEL_COUNT
        ),
        pl.concat_list(
            [pl.when(pl.col(flag)).then(pl.lit(flag)).otherwise(pl.lit(None)) for flag in flags]
        )
        .list.drop_nulls()
        .list.join(Separator.SPACE)
        .alias(DiagnosticColumn.LABELS),
    ]


def family_taxonomy(
    cells: DiagnosticTable, config: Config, rng: np.random.Generator
) -> DiagnosticTable:
    margin = config.statistics.gates.ctk_min_gain
    poor = config.statistics.gates.poor_full_recall
    keys = [Column.EXPERIMENT, Column.POPULATION, Column.FAMILY]
    fedavg = cells.filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & pl.col(Column.EXPERIMENT).is_in(
            [ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET]
        )
    )
    table = seed_interval(fedavg, DiagnosticColumn.CTK, keys, rng, config)
    for column in (
        DiagnosticColumn.POOLING,
        Column.LOCAL_RECALL,
        Column.FULL_RECALL,
        DiagnosticColumn.HEADROOM,
        Column.PEER_RECALL,
        Column.ABSENT_RECALL,
    ):
        lower = f"{column}{DiagnosticColumn.LOW_SUFFIX}"
        upper = f"{column}{DiagnosticColumn.HIGH_SUFFIX}"
        table = table.join(
            seed_interval(fedavg, column, keys, rng, config).select(*keys, column, lower, upper),
            on=keys,
        )

    def full(
        learner: Learner, experiment: ExperimentName | None, name: DiagnosticColumn
    ) -> DiagnosticTable:
        selected = cells.filter(pl.col(Column.LEARNER) == learner)
        by = [Column.POPULATION, Column.FAMILY]
        if experiment is None:
            by = [Column.EXPERIMENT, *by]
        else:
            selected = selected.filter(pl.col(Column.EXPERIMENT) == experiment)
        return selected.group_by(by, maintain_order=True).agg(
            pl.col(Column.FULL_RECALL).mean().alias(name)
        )

    table = (
        table.join(
            full(Learner.CENTRAL, None, DiagnosticColumn.FULL_CENTRAL),
            on=keys,
            how=LibraryOption.JOIN_LEFT,
        )
        .join(
            full(
                Learner.FEDAVG,
                ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR,
                DiagnosticColumn.FULL_LINEAR,
            ),
            on=[Column.POPULATION, Column.FAMILY],
            how=LibraryOption.JOIN_LEFT,
        )
        .join(
            full(
                Learner.FEDAVG,
                ExperimentName.MODEL_FAMILY_REPLICATION_TREES,
                DiagnosticColumn.FULL_TREES,
            ),
            on=[Column.POPULATION, Column.FAMILY],
            how=LibraryOption.JOIN_LEFT,
        )
    )
    classes = (
        Column.FULL_RECALL,
        DiagnosticColumn.FULL_CENTRAL,
        DiagnosticColumn.FULL_LINEAR,
        DiagnosticColumn.FULL_TREES,
    )
    ctk, pooling = pl.col(DiagnosticColumn.CTK), pl.col(DiagnosticColumn.POOLING)
    headroom, recall = pl.col(DiagnosticColumn.HEADROOM), pl.col(Column.FULL_RECALL)

    def low(column: DiagnosticColumn) -> pl.Expr:
        return pl.col(f"{column}{DiagnosticColumn.LOW_SUFFIX}")

    def high(column: DiagnosticColumn) -> pl.Expr:
        return pl.col(f"{column}{DiagnosticColumn.HIGH_SUFFIX}")

    table = table.with_columns(
        pl.sum_horizontal(
            [(pl.col(name) < poor).cast(pl.Int32).fill_null(0) for name in classes]
        ).alias(DiagnosticColumn.POOR_CLASSES),
        pl.sum_horizontal([pl.col(name).is_not_null().cast(pl.Int32) for name in classes]).alias(
            DiagnosticColumn.CLASSES
        ),
    ).with_columns(
        (headroom < margin).alias(TaxonomyLabel.LOW_HEADROOM),
        ((headroom >= margin) & (recall >= poor) & (ctk >= margin)).alias(
            TaxonomyLabel.EXPOSURE_LIMITED
        ),
        (pl.col(DiagnosticColumn.POOR_CLASSES) >= DiagnosticLimit.POOR_CLASSES).alias(
            TaxonomyLabel.REPRESENTATION_LIMITED
        ),
        (pooling >= margin).alias(TaxonomyLabel.POOLING_RESPONSIVE),
        ((pooling <= -margin) & (ctk >= margin)).alias(TaxonomyLabel.NEGATIVE_TRANSFER_SENSITIVE),
        (
            (low(DiagnosticColumn.CTK) > 0)
            & (ctk >= margin)
            & (low(DiagnosticColumn.HEADROOM) > 0)
            & (recall >= poor)
        ).alias(TaxonomyLabel.EXPOSURE_LIMITED_INTERVAL),
        (
            (high(DiagnosticColumn.POOLING) < 0)
            & (pooling <= -margin)
            & (low(DiagnosticColumn.CTK) > 0)
        ).alias(TaxonomyLabel.NEGATIVE_TRANSFER_INTERVAL),
        ((low(DiagnosticColumn.POOLING) > 0) & (pooling >= margin)).alias(
            TaxonomyLabel.POOLING_RESPONSIVE_INTERVAL
        ),
    )
    return with_class(
        table.with_columns(
            _labels(
                (
                    TaxonomyLabel.EXPOSURE_LIMITED,
                    TaxonomyLabel.REPRESENTATION_LIMITED,
                    TaxonomyLabel.LOW_HEADROOM,
                    TaxonomyLabel.POOLING_RESPONSIVE,
                    TaxonomyLabel.NEGATIVE_TRANSFER_SENSITIVE,
                )
            )
        ).sort(keys),
        EvidenceClass.POST_CONFIRMATORY,
    )


def large_family_table(
    seeds: LargeFamilyTable, families: LargeFamilyTable, selection: LargeFamilyTable
) -> DiagnosticTable:
    return (
        seeds.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
        .group_by(Column.FAMILY, maintain_order=True)
        .agg(
            pl.col(Column.CTK_GAIN).mean().alias(DiagnosticColumn.CTK),
            pl.col(Column.LOCAL_RECALL).mean(),
            pl.col(Column.FULL_RECALL).mean(),
            pl.col(Column.ABSENT_RECALL).mean(),
            pl.col(Column.PEER_RECALL).mean(),
            pl.col(Column.TRIALS).mean(),
            pl.len().alias(DiagnosticColumn.CELLS),
            pl.col(Column.SEED).n_unique().alias(DiagnosticColumn.SEEDS),
        )
        .join(
            families.select(
                Column.FAMILY, Column.NOVELTY, Column.MIN_TRIALS, Column.MEETS_THRESHOLD
            ),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        )
        .join(
            selection.select(Column.FAMILY, Column.ROWS, Column.FAMILY_SET),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        )
        .with_columns(
            (pl.col(Column.FULL_RECALL) - pl.col(Column.LOCAL_RECALL)).alias(
                DiagnosticColumn.HEADROOM
            ),
            (pl.col(Column.ABSENT_RECALL) - pl.col(Column.LOCAL_RECALL)).alias(
                DiagnosticColumn.POOLING
            ),
            pl.col(Column.ROWS).cast(pl.Float64).log().alias(DiagnosticColumn.LOG_ROWS),
        )
        .sort(Column.FAMILY)
    )


def large_family_taxonomy(table: DiagnosticTable, config: Config) -> DiagnosticTable:
    margin = config.statistics.gates.ctk_min_gain
    poor = config.statistics.gates.poor_full_recall
    ctk, pooling = pl.col(DiagnosticColumn.CTK), pl.col(DiagnosticColumn.POOLING)
    headroom, recall = pl.col(DiagnosticColumn.HEADROOM), pl.col(Column.FULL_RECALL)
    flags = (
        TaxonomyLabel.EXPOSURE_LIMITED,
        TaxonomyLabel.POOR_FULL_SINGLE_CLASS,
        TaxonomyLabel.LOW_HEADROOM,
        TaxonomyLabel.POOLING_RESPONSIVE,
        TaxonomyLabel.NEGATIVE_TRANSFER_SENSITIVE,
    )
    return with_class(
        table.with_columns(
            (headroom < margin).alias(TaxonomyLabel.LOW_HEADROOM),
            ((headroom >= margin) & (recall >= poor) & (ctk >= margin)).alias(
                TaxonomyLabel.EXPOSURE_LIMITED
            ),
            (recall < poor).alias(TaxonomyLabel.POOR_FULL_SINGLE_CLASS),
            (pooling >= margin).alias(TaxonomyLabel.POOLING_RESPONSIVE),
            ((pooling <= -margin) & (ctk >= margin)).alias(
                TaxonomyLabel.NEGATIVE_TRANSFER_SENSITIVE
            ),
        ).with_columns(_labels(flags)),
        EvidenceClass.POST_HOC_DIAGNOSTIC,
    )


def _bootstrap_spearman(
    first: DiagnosticVector,
    second: DiagnosticVector,
    rng: np.random.Generator,
) -> DiagnosticVector:
    size = first.size
    return np.array(
        [
            spearman(first[draw], second[draw])
            for draw in (
                rng.integers(0, size, size) for _ in range(DiagnosticResamples.RANK_CONCORDANCE)
            )
        ]
    )


def rank_concordance(
    family_ctk: DiagnosticTable, large: DiagnosticTable, config: Config
) -> DiagnosticRows:
    rng = np.random.default_rng(DiagnosticSeed.RANK_CONCORDANCE)
    reference = large.select(
        Column.FAMILY, pl.col(Column.CTK_GAIN).alias(DiagnosticColumn.LARGE_FAMILY_CTK)
    )
    fedavg = family_ctk.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
    rows: DiagnosticRows = []
    for experiment in sorted(fedavg[Column.EXPERIMENT].unique().to_list()):
        for population in (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE):
            joined = fedavg.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.POPULATION) == population)
            ).join(reference, on=Column.FAMILY, maintain_order=LibraryOption.JOIN_LEFT)
            first = joined[DiagnosticColumn.CTK].to_numpy().astype(np.float64)
            second = joined[DiagnosticColumn.LARGE_FAMILY_CTK].to_numpy().astype(np.float64)
            interval = percentile_limits(_bootstrap_spearman(first, second, rng), config)
            rows.append(
                {
                    Column.EXPERIMENT: experiment,
                    Column.POPULATION: population,
                    Column.FAMILIES: first.size,
                    DiagnosticColumn.RHO: spearman(first, second),
                    Column.CI_LOW: interval_low(interval),
                    Column.CI_HIGH: interval_high(interval),
                }
            )
    return rows


def large_family_associations(table: DiagnosticTable, config: Config) -> DiagnosticRows:
    rng = np.random.default_rng(DiagnosticSeed.ASSOCIATION)
    rows: DiagnosticRows = []
    for predictor in (
        Column.LOCAL_RECALL,
        Column.FULL_RECALL,
        DiagnosticColumn.HEADROOM,
        DiagnosticColumn.POOLING,
        Column.NOVELTY,
        DiagnosticColumn.LOG_ROWS,
        Column.TRIALS,
    ):
        present = table.drop_nulls([predictor, DiagnosticColumn.CTK])
        first = present[predictor].to_numpy().astype(np.float64)
        second = present[DiagnosticColumn.CTK].to_numpy().astype(np.float64)
        interval = percentile_limits(_bootstrap_spearman(first, second, rng), config)
        rows.append(
            {
                DiagnosticColumn.PREDICTOR: predictor,
                Column.FAMILIES: first.size,
                DiagnosticColumn.RHO: spearman(first, second),
                Column.CI_LOW: interval_low(interval),
                Column.CI_HIGH: interval_high(interval),
            }
        )
    return rows


def synthesis_diagnostics(
    cells: DiagnosticTable,
    large_seeds: LargeFamilyTable,
    large_families: LargeFamilyTable,
    selection: LargeFamilyTable,
    config: Config,
) -> SynthesisDiagnostics:
    rng = np.random.default_rng(DiagnosticSeed.TAXONOMY)
    taxonomy = family_taxonomy(cells, config, rng)
    family_ctk = with_class(
        seed_interval(
            cells,
            DiagnosticColumn.CTK,
            [Column.EXPERIMENT, Column.LEARNER, Column.POPULATION, Column.FAMILY],
            rng,
            config,
        ),
        EvidenceClass.POST_CONFIRMATORY,
    )
    large_ctk = seed_interval(
        large_seeds.filter(pl.col(Column.LEARNER) == Learner.FEDAVG),
        Column.CTK_GAIN,
        [Column.FAMILY],
        rng,
        config,
    )
    large = large_family_table(large_seeds, large_families, selection)
    evidence = EvidenceClass.POST_HOC_DIAGNOSTIC
    return SynthesisDiagnostics(
        cells=cells,
        taxonomy=taxonomy,
        family_ctk=family_ctk,
        large_family_ctk=with_class(large_ctk, evidence),
        large_taxonomy=large_family_taxonomy(large, config),
        rank_concordance=labelled(rank_concordance(family_ctk, large_ctk, config), evidence),
        large_associations=labelled(large_family_associations(large, config), evidence),
    )
