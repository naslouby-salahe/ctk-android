from statistics import NormalDist

import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.decomposition import family_seed_effects
from ctk_android.analysis.novelty import descriptor_by_family, novelty_association
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    DrawStream,
    LargeFamilyMeasure,
    Learner,
    LibraryOption,
    PrecisionRho,
    StatisticsLimit,
    Tolerance,
)
from ctk_android.types import (
    AssociationMeasures,
    Correlation,
    EligibilityStabilityTable,
    FamilyCountsTable,
    FamilySeedTable,
    GainVector,
    Interval,
    LargeFamilyRow,
    LargeFamilyTable,
    LargeSelectionTable,
    LargeStabilityRow,
    LargeSummaryRow,
    LargeSummaryTable,
    NoveltyTable,
    NoveltyVector,
    RowCount,
    Score,
    SeedCountVector,
    SeedPairsTables,
    SpreadVector,
    StabilitySeedTable,
    SupportCount,
)


def frozen_association() -> AssociationMeasures:
    return (
        LargeFamilyMeasure.RHO,
        LargeFamilyMeasure.RHO_P_VALUE,
        LargeFamilyMeasure.RHO_CI_LOW,
        LargeFamilyMeasure.RHO_CI_HIGH,
        LargeFamilyMeasure.RHO_CI_WIDTH,
    )


def stable_association() -> AssociationMeasures:
    # Same statistics as the frozen result, under sensitivity-labelled measure names.
    return (
        LargeFamilyMeasure.STABLE_RHO,
        LargeFamilyMeasure.STABLE_RHO_P_VALUE,
        LargeFamilyMeasure.STABLE_RHO_CI_LOW,
        LargeFamilyMeasure.STABLE_RHO_CI_HIGH,
        LargeFamilyMeasure.STABLE_RHO_CI_WIDTH,
    )


def _normal() -> NormalDist:
    return NormalDist()


def large_seed_effects(families: FamilyCountsTable, config: Config) -> FamilySeedTable:
    large = list(config.experiments.extension_b_experiments)
    return family_seed_effects(
        families.filter(is_one_of(Column.EXPERIMENT, large)),
        config.experiments.operating.primary_alpha,
    ).filter(pl.col(Column.LEARNER) == Learner.FEDAVG)


def large_family_table(
    seed_effects: FamilySeedTable, novelty: NoveltyTable, config: Config
) -> LargeFamilyTable:
    if seed_effects.height == 0:
        return pl.DataFrame()
    scores = descriptor_by_family(
        novelty.filter(
            is_one_of(Column.EXPERIMENT, list(config.experiments.extension_b_experiments))
        ),
        config.experiments.novelty.primary_descriptor,
    )
    threshold = config.statistics.gates.ctk_min_gain
    per_family = (
        seed_effects.group_by(Column.EXPERIMENT, Column.FAMILY, maintain_order=True)
        .agg(
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
            pl.col(Column.CTK_GAIN).mean(),
            pl.col(Column.CTK_GAIN).std().alias(Column.CTK_SD),
            pl.col(Column.LOCAL_RECALL).mean(),
            pl.col(Column.ABSENT_RECALL).mean(),
            pl.col(Column.PEER_RECALL).mean(),
            pl.col(Column.TRIALS).mean(),
            pl.col(Column.TRIALS).min().alias(Column.MIN_TRIALS),
        )
        .join(scores, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .sort(Column.EXPERIMENT, Column.FAMILY)
    )
    return records_to_frame(
        [
            LargeFamilyRow(
                experiment=row[Column.EXPERIMENT],
                family=row[Column.FAMILY],
                seed_count=row[Column.SEED_COUNT],
                ctk_gain=row[Column.CTK_GAIN],
                ctk_sd=row[Column.CTK_SD],
                local_recall=row[Column.LOCAL_RECALL],
                absent_recall=row[Column.ABSENT_RECALL],
                peer_recall=row[Column.PEER_RECALL],
                trials=row[Column.TRIALS],
                min_trials=row[Column.MIN_TRIALS],
                novelty=row[Column.NOVELTY],
                meets_threshold=abs(row[Column.CTK_GAIN]) >= threshold,
            )
            for row in per_family.iter_rows(named=True)
        ]
    )


def _z(config: Config) -> Score:
    return _normal().inv_cdf(1.0 - (1.0 - config.statistics.confidence_level) / 2.0)


def expected_ci_width(rho: Correlation, families: RowCount, z: Score) -> Score:
    standard_error = np.sqrt((1.0 + rho**2 / 2.0) / (families - StatisticsLimit.FISHER_OFFSET))
    centre = np.arctanh(rho)
    return (np.tanh(centre + z * standard_error) - np.tanh(centre - z * standard_error)).item()


def _detectable_rho(families: RowCount, z: Score) -> Correlation:
    return np.tanh(
        (z + _normal().inv_cdf(Tolerance.TARGET_POWER))
        / np.sqrt(families - StatisticsLimit.FISHER_OFFSET)
    ).item()


def _row(
    measure: LargeFamilyMeasure, value: Score, rho: Correlation | None = None
) -> LargeSummaryRow:
    return LargeSummaryRow(measure=measure, assumed_rho=rho, value=value)


def _spread_rows(
    ctk: GainVector, sds: SpreadVector, seeds: SeedCountVector
) -> list[LargeSummaryRow]:
    between = np.var(ctk, ddof=1).item() if ctk.size > 1 else 0.0
    noise = np.mean(sds**2 / seeds).item() if sds.size else 0.0
    signal = max(between - noise, 0.0)
    return [
        _row(LargeFamilyMeasure.CTK_MEAN, ctk.mean().item()),
        _row(LargeFamilyMeasure.CTK_SD, np.sqrt(between).item()),
        _row(LargeFamilyMeasure.CTK_NOISE_SD, np.sqrt(noise).item()),
        _row(LargeFamilyMeasure.CTK_SIGNAL_SD, np.sqrt(signal).item()),
        _row(LargeFamilyMeasure.CTK_RELIABILITY, signal / between if between > 0 else 0.0),
    ]


def _descriptor_rows(scores: NoveltyVector) -> list[LargeSummaryRow]:
    return [
        _row(LargeFamilyMeasure.DESCRIPTOR_SD, np.std(scores, ddof=1).item()),
        _row(
            LargeFamilyMeasure.DESCRIPTOR_IQR,
            np.asarray(stats.iqr(scores)).item(),
        ),
        _row(LargeFamilyMeasure.DESCRIPTOR_DISTINCT, np.unique(scores).size),
    ]


def _association_rows(
    gains: GainVector,
    scores: NoveltyVector,
    config: Config,
    measures: AssociationMeasures | None = None,
) -> list[LargeSummaryRow]:
    association = novelty_association(gains, scores, config.statistics)
    if association is None:
        return []
    rho, p_value, low, high, width = measures or frozen_association()
    rows = [_row(rho, association.rho), _row(p_value, association.p_value)]
    interval: Interval | None = association.interval
    if interval is not None:
        rows += [
            _row(low, interval.low),
            _row(high, interval.high),
            _row(width, interval.high - interval.low),
        ]
    return rows


def _precision_rows(families: RowCount, config: Config) -> list[LargeSummaryRow]:
    if families <= StatisticsLimit.ASSOCIATION_FAMILIES:
        return []
    z = _z(config)
    return [
        _row(
            LargeFamilyMeasure.EXPECTED_CI_WIDTH,
            expected_ci_width(rho, families, z),
            rho,
        )
        for rho in PrecisionRho
    ] + [_row(LargeFamilyMeasure.MIN_DETECTABLE_RHO, _detectable_rho(families, z))]


def large_family_summary(
    table: LargeFamilyTable,
    planned: SupportCount,
    config: Config,
    seed_effects: FamilySeedTable,
) -> LargeSummaryTable:
    if table.height == 0:
        return pl.DataFrame()
    scored = table.filter(pl.col(Column.NOVELTY).is_not_null())
    rows = [
        _row(LargeFamilyMeasure.FAMILIES_PLANNED, planned),
        _row(LargeFamilyMeasure.FAMILIES_DEFINED, table.height),
        _row(LargeFamilyMeasure.FAMILIES_WITH_DESCRIPTOR, scored.height),
        _row(LargeFamilyMeasure.MEAN_SUPPORT, table[Column.TRIALS].to_numpy().mean().item()),
        _row(LargeFamilyMeasure.MIN_SUPPORT, table[Column.MIN_TRIALS].to_numpy().min().item()),
        _row(
            LargeFamilyMeasure.FAMILIES_ABOVE_THRESHOLD,
            table.filter(pl.col(Column.MEETS_THRESHOLD)).height,
        ),
        *_spread_rows(
            table[Column.CTK_GAIN].to_numpy(),
            table[Column.CTK_SD].drop_nulls().to_numpy(),
            table.filter(pl.col(Column.CTK_SD).is_not_null())[Column.SEED_COUNT].to_numpy(),
        ),
    ]
    if scored.height > 1:
        rows += _descriptor_rows(scored[Column.NOVELTY].to_numpy())
    rows += _association_rows(
        scored[Column.CTK_GAIN].to_numpy(), scored[Column.NOVELTY].to_numpy(), config
    )
    rows += _permutation_rows(
        scored[Column.CTK_GAIN].to_numpy(), scored[Column.NOVELTY].to_numpy(), config
    )
    rows += _seed_rho_rows(seed_effects, scored)
    rows += _precision_rows(scored.height, config)
    return records_to_frame(rows)


def _rho(gains: GainVector, scores: NoveltyVector) -> Correlation:
    return stats.spearmanr(gains, scores).statistic.item()


# Frozen protocol: permutation p for the family-level rho. 32! orderings cannot be enumerated,
# so descriptors are permuted over families (Monte Carlo, the bootstrap resample count, fixed
# stream); two-sided, p = (1 + count of |rho*| >= |rho|) / (1 + draws).
def _permutation_rows(
    gains: GainVector, scores: NoveltyVector, config: Config
) -> list[LargeSummaryRow]:
    if gains.size <= StatisticsLimit.ASSOCIATION_FAMILIES:
        return []
    observed = abs(_rho(gains, scores))
    draws = config.statistics.bootstrap_resamples
    generator = np.random.default_rng(DrawStream.LARGE_FAMILY_PERMUTATION)
    extreme = sum(abs(_rho(gains, generator.permutation(scores))) >= observed for _ in range(draws))
    return [_row(LargeFamilyMeasure.RHO_PERMUTATION_P, (1 + extreme) / (1 + draws))]


# Frozen protocol: seed-level rho distribution (descriptive), one rho per fresh seed over the
# families measured in that seed, against the family descriptor.
def _seed_rho_rows(
    seed_effects: FamilySeedTable, scored: LargeFamilyTable
) -> list[LargeSummaryRow]:
    joined = seed_effects.join(
        scored.select(Column.FAMILY, Column.NOVELTY), on=Column.FAMILY, how=LibraryOption.JOIN_INNER
    )
    values = [
        _rho(part[Column.CTK_GAIN].to_numpy(), part[Column.NOVELTY].to_numpy())
        for _, part in joined.group_by(Column.SEED, maintain_order=True)
        if part.height > StatisticsLimit.ASSOCIATION_FAMILIES
    ]
    if not values:
        return []
    seeds = np.array(values)
    return [
        _row(LargeFamilyMeasure.SEEDS_WITH_RHO, seeds.size),
        _row(LargeFamilyMeasure.SEED_RHO_MIN, seeds.min().item()),
        _row(LargeFamilyMeasure.SEED_RHO_MEDIAN, np.median(seeds).item()),
        _row(LargeFamilyMeasure.SEED_RHO_MAX, seeds.max().item()),
        _row(LargeFamilyMeasure.SEED_RHO_POSITIVE, (seeds > 0).sum().item()),
    ]


# Eligibility-stability sensitivity (no training): the 32 families were frozen from the
# seed-000 partition; this re-reads the fresh-seed partitions built by the same rule and
# asks how often each frozen family stays structurally eligible. The frozen result stays
# primary; the stable-family association is reported only as a labelled sensitivity.


def stability_seed_table(
    pairs: SeedPairsTables, selection: LargeSelectionTable
) -> StabilitySeedTable:
    if not pairs:
        return pl.DataFrame()
    grid = selection.select(Column.FAMILY).join(
        pl.DataFrame({Column.SEED: sorted(pairs)}, schema={Column.SEED: pl.Int64}),
        how=LibraryOption.JOIN_CROSS,
    )
    support = pl.concat(
        [
            table.filter(pl.col(Column.ELIGIBLE))
            .group_by(Column.FAMILY, maintain_order=True)
            .agg(
                pl.len().cast(pl.Int64).alias(Column.ELIGIBLE_PAIRS),
                pl.col(Column.TARGET_TEST_ROWS)
                .sum()
                .cast(pl.Int64)
                .alias(Column.ELIGIBLE_TEST_ROWS),
            )
            .with_columns(pl.lit(seed, dtype=pl.Int64).alias(Column.SEED))
            for seed, table in pairs.items()
        ]
    )
    # A family absent from a seed's eligible pairs keeps a zero-support row.
    return (
        grid.join(support, on=[Column.FAMILY, Column.SEED], how=LibraryOption.JOIN_LEFT)
        .with_columns(pl.col(Column.ELIGIBLE_PAIRS, Column.ELIGIBLE_TEST_ROWS).fill_null(0))
        .with_columns((pl.col(Column.ELIGIBLE_PAIRS) > 0).alias(Column.ELIGIBLE))
        .sort(Column.FAMILY, Column.SEED)
    )


def eligibility_stability_table(
    per_seed: StabilitySeedTable, selection: LargeSelectionTable, seed_effects: FamilySeedTable
) -> EligibilityStabilityTable:
    if per_seed.height == 0:
        return pl.DataFrame()
    measured = seed_effects.group_by(Column.FAMILY, maintain_order=True).agg(
        pl.col(Column.SEED).n_unique().alias(Column.MEASURED_SEEDS)
    )
    per_family = (
        per_seed.group_by(Column.FAMILY, maintain_order=True)
        .agg(
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
            pl.col(Column.ELIGIBLE).sum().alias(Column.ELIGIBLE_SEEDS),
            pl.col(Column.ELIGIBLE_PAIRS).min().alias(Column.MIN_ELIGIBLE_PAIRS),
            pl.col(Column.ELIGIBLE_PAIRS).mean().alias(Column.MEAN_ELIGIBLE_PAIRS),
            pl.col(Column.ELIGIBLE_PAIRS).max().alias(Column.MAX_ELIGIBLE_PAIRS),
            pl.col(Column.ELIGIBLE_TEST_ROWS).min().alias(Column.MIN_ELIGIBLE_TEST_ROWS),
            pl.col(Column.ELIGIBLE_TEST_ROWS).mean().alias(Column.MEAN_ELIGIBLE_TEST_ROWS),
        )
        .join(selection.select(Column.FAMILY, Column.FAMILY_SET, Column.RANK), on=Column.FAMILY)
        .join(measured, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .sort(Column.RANK)
    )
    return records_to_frame(
        [
            LargeStabilityRow(
                family=row[Column.FAMILY],
                family_set=row[Column.FAMILY_SET],
                rank=row[Column.RANK],
                seed_count=row[Column.SEED_COUNT],
                eligible_seeds=row[Column.ELIGIBLE_SEEDS],
                eligible_seed_fraction=row[Column.ELIGIBLE_SEEDS] / row[Column.SEED_COUNT],
                eligible_in_every_seed=row[Column.ELIGIBLE_SEEDS] == row[Column.SEED_COUNT],
                measured_seeds=row[Column.MEASURED_SEEDS] or 0,
                min_eligible_pairs=row[Column.MIN_ELIGIBLE_PAIRS],
                mean_eligible_pairs=row[Column.MEAN_ELIGIBLE_PAIRS],
                max_eligible_pairs=row[Column.MAX_ELIGIBLE_PAIRS],
                min_eligible_target_test_rows=row[Column.MIN_ELIGIBLE_TEST_ROWS],
                mean_eligible_target_test_rows=row[Column.MEAN_ELIGIBLE_TEST_ROWS],
            )
            for row in per_family.iter_rows(named=True)
        ]
    )


def eligibility_stability_summary(
    stability: EligibilityStabilityTable, table: LargeFamilyTable, config: Config
) -> LargeSummaryTable:
    if stability.height == 0 or table.height == 0:
        return pl.DataFrame()
    stable = stability.filter(pl.col(Column.STABLE))[Column.FAMILY].to_list()
    # Frozen family-mean CTK and descriptor, restricted to families eligible in every seed.
    scored = table.filter(is_one_of(Column.FAMILY, stable) & pl.col(Column.NOVELTY).is_not_null())
    fractions = stability[Column.ELIGIBLE_FRACTION].to_numpy()
    rows = [
        _row(LargeFamilyMeasure.STABILITY_FAMILIES, stability.height),
        _row(
            LargeFamilyMeasure.STABILITY_SEEDS, stability[Column.SEED_COUNT].to_numpy().max().item()
        ),
        _row(LargeFamilyMeasure.STABLE_FAMILIES, len(stable)),
        _row(LargeFamilyMeasure.MEAN_ELIGIBLE_FRACTION, fractions.mean().item()),
        _row(LargeFamilyMeasure.MIN_ELIGIBLE_FRACTION, fractions.min().item()),
    ]
    return records_to_frame(
        rows
        + _association_rows(
            scored[Column.CTK_GAIN].to_numpy(),
            scored[Column.NOVELTY].to_numpy(),
            config,
            stable_association(),
        )
    )
