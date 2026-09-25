import warnings

import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.diagnostics_statistics import labelled, percentile_limits, spearman
from ctk_android.config import Config
from ctk_android.enums import (
    Column,
    DiagnosticColumn,
    DiagnosticResamples,
    DiagnosticSeed,
    EvidenceClass,
    InfluenceStatistic,
    KendallConstant,
    LibraryOption,
    Separator,
)
from ctk_android.types import (
    Correlation,
    DiagnosticMatrix,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    InfluenceTables,
    Interval,
    LargeFamilyTable,
    ResampleCount,
    Seed,
    SupportCount,
)


def _bootstrap_rho(
    first: DiagnosticVector,
    second: DiagnosticVector,
    rng: np.random.Generator,
    resamples: ResampleCount,
    config: Config,
) -> Interval | None:
    size = first.size
    draws = [rng.integers(0, size, size) for _ in range(resamples)]
    return percentile_limits(np.array([spearman(first[i], second[i]) for i in draws]), config)


def weighted_spearman(
    first: DiagnosticVector, second: DiagnosticVector, weights: DiagnosticVector
) -> Correlation:
    first_rank, second_rank = stats.rankdata(first), stats.rankdata(second)
    share = weights / weights.sum()
    first_mean, second_mean = (share * first_rank).sum(), (share * second_rank).sum()
    covariance = (share * (first_rank - first_mean) * (second_rank - second_mean)).sum()
    scale = np.sqrt(
        (share * (first_rank - first_mean) ** 2).sum()
        * (share * (second_rank - second_mean) ** 2).sum()
    )
    return (covariance / scale).item()


def kendall_w(ranks: DiagnosticMatrix) -> Correlation:
    items, raters = ranks.shape
    spread = ((ranks.sum(1) - raters * (items + 1) / 2) ** 2).sum()
    return (
        KendallConstant.NUMERATOR * spread / (raters**2 * (items**KendallConstant.CUBE - items))
    ).item()


def leave_one_out(first: DiagnosticVector, second: DiagnosticVector) -> DiagnosticVector:
    return np.array(
        [spearman(np.delete(first, i), np.delete(second, i)) for i in range(first.size)]
    )


def _statistic(
    statistic: InfluenceStatistic,
    value: Correlation,
    count: SupportCount | None = None,
    interval: Interval | None = None,
    seed: Seed | None = None,
) -> DiagnosticRow:
    return {
        DiagnosticColumn.STATISTIC: statistic,
        Column.SEED: seed,
        DiagnosticColumn.N: count,
        Column.VALUE: value,
        Column.CI_LOW: None if interval is None else interval.low,
        Column.CI_HIGH: None if interval is None else interval.high,
    }


def _seed_matrix(seeds: LargeFamilyTable) -> DiagnosticTable:
    return seeds.pivot(
        on=Column.SEED,
        index=Column.FAMILY,
        values=Column.CTK_GAIN,
        aggregate_function=LibraryOption.AGGREGATE_MEAN,
    ).sort(Column.FAMILY)


def influence_tables(
    families: LargeFamilyTable,
    seeds: LargeFamilyTable,
    stability: LargeFamilyTable,
    config: Config,
) -> InfluenceTables:
    table = families.sort(Column.FAMILY)
    names = table[Column.FAMILY].to_list()
    count = len(names)
    novelty = table[Column.NOVELTY].to_numpy()
    ctk = table[Column.CTK_GAIN].to_numpy()
    seed_count = table[Column.SEED_COUNT].to_numpy()
    spread = table[Column.CTK_SD].to_numpy()
    rng = np.random.default_rng(DiagnosticSeed.INFLUENCE)
    resamples = DiagnosticResamples.INFLUENCE
    rho = spearman(novelty, ctk)
    unstable = set(stability.filter(~pl.col(Column.STABLE))[Column.FAMILY].to_list())
    stable = np.array([name not in unstable for name in names])
    summary: DiagnosticRows = [
        _statistic(
            InfluenceStatistic.RHO_ALL,
            rho,
            count,
            _bootstrap_rho(novelty, ctk, rng, resamples, config),
        ),
        _statistic(
            InfluenceStatistic.RHO_STABLE,
            spearman(novelty[stable], ctk[stable]),
            stable.sum().item(),
            _bootstrap_rho(novelty[stable], ctk[stable], rng, resamples, config),
        ),
    ]
    loo = leave_one_out(novelty, ctk)
    jackknife = np.sqrt((count - 1) / count * ((loo - loo.mean()) ** 2).sum()).item()
    rank_novelty, rank_ctk = stats.rankdata(novelty), stats.rankdata(ctk)
    centre = (count + 1) / 2
    influence = rho - loo
    order = np.argsort(-influence)
    influence_rank = np.empty(count, np.int64)
    influence_rank[order] = np.arange(1, count + 1)
    leverage = np.sqrt(((rank_novelty - centre) / count) ** 2 + ((rank_ctk - centre) / count) ** 2)
    summary += [
        _statistic(InfluenceStatistic.JACKKNIFE_SE, jackknife, count),
        _statistic(
            InfluenceStatistic.JACKKNIFE_BIAS_CORRECTED,
            count * rho - (count - 1) * loo.mean().item(),
            count,
        ),
        _statistic(InfluenceStatistic.LOO_MIN, loo.min().item(), count),
        _statistic(InfluenceStatistic.LOO_MEDIAN, np.median(loo).item(), count),
        _statistic(InfluenceStatistic.LOO_MAX, loo.max().item(), count),
    ]
    by_family = seeds.group_by(Column.FAMILY, maintain_order=True).agg(
        pl.col(Column.SEED).n_unique().alias(Column.MEASURED_SEEDS),
        pl.len().alias(DiagnosticColumn.PAIRS),
        pl.col(Column.CLIENT).unique().sort().str.join(Separator.COMMA).alias(Column.CLIENTS),
        pl.col(Column.TRIALS).sum().alias(DiagnosticColumn.TOTAL_TRIALS),
        pl.col(Column.TRIALS).mean().alias(DiagnosticColumn.MEAN_TRIALS),
    )
    total_trials = (
        table.select(Column.FAMILY)
        .join(by_family, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)[
            DiagnosticColumn.TOTAL_TRIALS
        ]
        .to_numpy()
        .astype(np.float64)
    )
    summary += [
        _statistic(
            InfluenceStatistic.WEIGHTED_SEED_COUNT,
            weighted_spearman(novelty, ctk, seed_count.astype(np.float64)),
            count,
        ),
        _statistic(
            InfluenceStatistic.WEIGHTED_SQRT_TRIALS,
            weighted_spearman(novelty, ctk, np.sqrt(total_trials)),
            count,
        ),
        _statistic(
            InfluenceStatistic.WEIGHTED_INVERSE_VARIANCE,
            weighted_spearman(novelty, ctk, seed_count / np.mean(spread**2)),
            count,
        ),
    ]
    summary += _seed_statistics(seeds, table, rng)
    loo_table = (
        pl.DataFrame(
            {
                Column.FAMILY: names,
                DiagnosticColumn.UNSTABLE: [name in unstable for name in names],
                Column.NOVELTY: novelty,
                DiagnosticColumn.CTK: ctk,
                Column.CTK_SD: spread,
                Column.SEED_COUNT: seed_count,
                DiagnosticColumn.RANK_NOVELTY: rank_novelty,
                DiagnosticColumn.RANK_CTK: rank_ctk,
                DiagnosticColumn.RANK_PRODUCT: (rank_novelty - centre) * (rank_ctk - centre),
                DiagnosticColumn.LOO_RHO: loo,
                DiagnosticColumn.INFLUENCE: influence,
                DiagnosticColumn.INFLUENCE_RANK: influence_rank,
                DiagnosticColumn.LEVERAGE: leverage,
                DiagnosticColumn.COOK_LIKE: (influence / jackknife) ** 2,
            }
        )
        .join(
            stability.select(Column.FAMILY, Column.ELIGIBLE_SEEDS),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        )
        .join(by_family, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .sort(DiagnosticColumn.INFLUENCE_RANK)
        .with_columns(pl.lit(EvidenceClass.POST_HOC_DIAGNOSTIC).alias(Column.EVIDENCE_CLASS))
    )
    return InfluenceTables(
        families=loo_table, summary=labelled(summary, EvidenceClass.POST_HOC_DIAGNOSTIC)
    )


def _seed_statistics(
    seeds: LargeFamilyTable, table: LargeFamilyTable, rng: np.random.Generator
) -> DiagnosticRows:
    wide = _seed_matrix(seeds)
    seed_values: list[Seed] = seeds[Column.SEED].unique(maintain_order=True).to_list()
    seed_names = [f"{seed}" for seed in seed_values]
    matrix = wide.select(seed_names).to_numpy().astype(np.float64)
    lookup = dict(zip(table[Column.FAMILY].to_list(), table[Column.NOVELTY].to_list(), strict=True))
    novelty = np.array([lookup[name] for name in wide[Column.FAMILY].to_list()])
    rows: DiagnosticRows = []
    for column, seed in enumerate(seed_values):
        present = ~np.isnan(matrix[:, column])
        rows.append(
            _statistic(
                InfluenceStatistic.SEED_RHO,
                spearman(novelty[present], matrix[present, column]),
                present.sum().item(),
                seed=seed,
            )
        )
    pairs: list[Correlation] = []
    for first in range(len(seed_names)):
        for second in range(first + 1, len(seed_names)):
            present = ~np.isnan(matrix[:, first]) & ~np.isnan(matrix[:, second])
            pairs.append(spearman(matrix[present, first], matrix[present, second]))
    concordance = np.array(pairs)
    rows += [
        _statistic(InfluenceStatistic.SEED_PAIR_MIN, concordance.min().item(), len(pairs)),
        _statistic(InfluenceStatistic.SEED_PAIR_MEDIAN, np.median(concordance).item(), len(pairs)),
        _statistic(InfluenceStatistic.SEED_PAIR_MEAN, concordance.mean().item(), len(pairs)),
        _statistic(InfluenceStatistic.SEED_PAIR_MAX, concordance.max().item(), len(pairs)),
        _statistic(
            InfluenceStatistic.SEED_PAIR_NEGATIVE, (concordance < 0).sum().item(), len(pairs)
        ),
    ]
    complete = matrix[~np.isnan(matrix).any(axis=1)]
    ranks = np.apply_along_axis(stats.rankdata, 0, complete)
    items, raters = ranks.shape
    agreement = kendall_w(ranks)
    chi2 = raters * (items - 1) * agreement
    rows += [
        _statistic(InfluenceStatistic.KENDALL_W, agreement, items),
        _statistic(
            InfluenceStatistic.KENDALL_IMPLIED_RHO, (raters * agreement - 1) / (raters - 1), items
        ),
        _statistic(InfluenceStatistic.KENDALL_CHI2, chi2, items),
        _statistic(
            InfluenceStatistic.KENDALL_P,
            np.float64(stats.chi2.sf(np.float64(chi2), items - 1)).item(),
            items,
        ),
    ]
    ctk = table[Column.CTK_GAIN].to_numpy()
    spread = table[Column.CTK_SD].to_numpy()
    seed_count = table[Column.SEED_COUNT].to_numpy()
    observed = ctk.var(ddof=1).item()
    within = np.nanmean(spread**2).item()
    error = np.nanmean(spread**2 / seed_count).item()
    reliability = (observed - error) / observed
    half = len(seed_names) // 2
    halves: list[Correlation] = []
    for _ in range(DiagnosticResamples.SPLIT_HALF):
        order = rng.permutation(len(seed_names))
        # Families measured in no seed of a half are all-NaN rows and are dropped below.
        with warnings.catch_warnings():
            warnings.simplefilter(LibraryOption.WARNINGS_IGNORE, RuntimeWarning)
            first = np.nanmean(matrix[:, order[:half]], 1)
            second = np.nanmean(matrix[:, order[half:]], 1)
        present = ~np.isnan(first) & ~np.isnan(second)
        agreement_half = spearman(first[present], second[present])
        halves.append(2 * agreement_half / (1 + agreement_half))
    split_half = np.mean(halves).item()
    rho = spearman(table[Column.NOVELTY].to_numpy(), ctk)
    count = ctk.size
    rows += [
        _statistic(InfluenceStatistic.VARIANCE_BETWEEN, observed, count),
        _statistic(InfluenceStatistic.VARIANCE_WITHIN, within, count),
        _statistic(InfluenceStatistic.ERROR_VARIANCE, error, count),
        _statistic(InfluenceStatistic.VARIANCE_RELIABILITY, reliability, count),
        _statistic(InfluenceStatistic.SPLIT_HALF_RELIABILITY, split_half, count),
        _statistic(
            InfluenceStatistic.DISATTENUATED_VARIANCE, rho / np.sqrt(reliability).item(), count
        ),
        _statistic(InfluenceStatistic.DISATTENUATED_RANK, rho / np.sqrt(split_half).item(), count),
    ]
    return rows
