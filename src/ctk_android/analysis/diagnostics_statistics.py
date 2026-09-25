import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.extension_effects import scope_experiments
from ctk_android.config import Config
from ctk_android.enums import (
    Column,
    DiagnosticColumn,
    DiagnosticSeed,
    EvidenceClass,
    ExperimentName,
    ExtensionScope,
    LibraryOption,
)
from ctk_android.types import (
    Correlation,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    Interval,
    PValue,
    ScopedExperiments,
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
