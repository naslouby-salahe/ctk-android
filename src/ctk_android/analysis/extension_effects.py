import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.statistics import bca_interval, holm_adjust
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of
from ctk_android.enums import (
    Aggregation,
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExtensionContrast,
    ExtensionScope,
    FamilySetName,
    Learner,
    LibraryOption,
    SignTail,
)
from ctk_android.types import (
    ArmSelector,
    ContrastEffects,
    ContrastHeader,
    DoseRequest,
    Effect,
    EffectCell,
    ExtensionEffectRow,
    ExtensionTable,
    FamilyCountsTable,
    HolmIndex,
    PValue,
    ScopeExperiments,
    SeedEffects,
    SeedRecallTable,
)


def arm_keys() -> list[Column]:
    return [Column.LEARNER, Column.CONDITION, Column.DOSE, Column.PARAMETER, Column.TUNING_VALUE]


def cell_keys() -> list[Column]:
    return [Column.SCOPE, Column.POPULATION, Column.ALPHA]


def scope_experiments(config: Config, experiments: tuple[ExperimentName, ...]) -> ScopeExperiments:
    named = {
        ExtensionScope.PRIMARY_SET: FamilySetName.PRIMARY,
        ExtensionScope.REPLICATION_SET: FamilySetName.REPLICATION,
    }
    scopes = {
        scope: tuple(
            name for name in experiments if config.experiments.experiments[name].family_set == fam
        )
        for scope, fam in named.items()
    }
    return {ExtensionScope.POOLED: experiments, **scopes}


def seed_recalls(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> SeedRecallTable:
    if families.height == 0:
        return pl.DataFrame()
    minima = pl.DataFrame(
        {
            Column.EXPERIMENT: pl.Series(list(experiments), dtype=pl.String),
            Column.MIN_TRIALS: [
                config.data.eligibility[
                    config.experiments.experiments[name].eligibility
                ].own_domain_min_test
                for name in experiments
            ],
        }
    )
    federation = pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE
    usable = (
        families.filter(
            is_one_of(Column.EXPERIMENT, list(experiments))
            & is_one_of(
                Column.POPULATION,
                [EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN],
            )
        )
        .join(minima, on=Column.EXPERIMENT)
        .filter(
            pl.col(Column.TRIALS)
            >= pl.when(federation).then(1).otherwise(pl.col(Column.MIN_TRIALS))
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    )
    parts = [
        usable.filter(is_one_of(Column.EXPERIMENT, list(names)))
        .group_by(Column.SEED, *arm_keys(), Column.POPULATION, Column.ALPHA, maintain_order=True)
        .agg(pl.col(Column.RECALL).mean(), pl.len().alias(Column.FAMILIES))
        .with_columns(pl.lit(scope).alias(Column.SCOPE))
        for scope, names in scope_experiments(config, experiments).items()
        if names
    ]
    return pl.concat(parts)


def _arm(recalls: SeedRecallTable, learner: Learner, arm: ArmSelector) -> SeedRecallTable:
    dose = pl.col(Column.DOSE).is_null() if arm.dose is None else pl.col(Column.DOSE) == arm.dose
    tuned = (
        pl.col(Column.PARAMETER).is_null()
        if arm.aggregation is None
        else pl.col(Column.TUNING_VALUE) == arm.aggregation
    )
    return recalls.filter(
        (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.CONDITION) == arm.condition)
        & dose
        & tuned
    ).select(*cell_keys(), Column.SEED, Column.RECALL)


def arm_difference(
    recalls: SeedRecallTable, learner: Learner, minuend: ArmSelector, subtrahend: ArmSelector
) -> ExtensionTable:
    if recalls.height == 0:
        return pl.DataFrame()
    keys = [*cell_keys(), Column.SEED]
    return (
        _arm(recalls, learner, minuend)
        .join(
            _arm(recalls, learner, subtrahend).rename({Column.RECALL: Column.SUBTRAHEND}),
            on=keys,
        )
        .select(*keys, (pl.col(Column.RECALL) - pl.col(Column.SUBTRAHEND)).alias(Column.DIFFERENCE))
    )


def difference_of_differences(first: ExtensionTable, second: ExtensionTable) -> ExtensionTable:
    if first.height == 0 or second.height == 0:
        return pl.DataFrame()
    keys = [*cell_keys(), Column.SEED]
    return first.join(second.rename({Column.DIFFERENCE: Column.SUBTRAHEND}), on=keys).select(
        *keys, (pl.col(Column.DIFFERENCE) - pl.col(Column.SUBTRAHEND)).alias(Column.DIFFERENCE)
    )


def shifted_wilcoxon(differences: SeedEffects, reference: Effect, tail: SignTail) -> PValue:
    shifted = differences - reference
    if not np.any(shifted):
        return 1.0
    alternative = (
        LibraryOption.WILCOXON_GREATER
        if tail is SignTail.GREATER
        else LibraryOption.WILCOXON_TWO_SIDED
    )
    return stats.wilcoxon(
        shifted, alternative=alternative, method=LibraryOption.WILCOXON_EXACT
    ).pvalue.item()


def _row(
    header: ContrastHeader,
    cell: EffectCell,
    values: SeedEffects,
    config: Config,
) -> ExtensionEffectRow:
    margin = config.statistics.gates.ctk_min_gain
    interval = bca_interval(values, config.statistics)
    low, high = (None, None) if interval is None else (interval.low, interval.high)
    return ExtensionEffectRow(
        hypothesis=header.hypothesis,
        scope=cell.scope,
        learner=header.learner,
        population=cell.population,
        alpha=cell.alpha,
        contrast=header.contrast,
        level=header.level,
        seed_count=values.size,
        mean=values.mean().item(),
        median=np.median(values).item(),
        positive_seeds=(values > 0).sum().item(),
        ci_low=low,
        ci_high=high,
        alternative=header.tail,
        null_reference=header.reference,
        p_value=shifted_wilcoxon(values, header.reference, header.tail),
        p_holm=None,
        margin=margin,
        above_margin=low is not None and low > margin,
        within_band=low is not None and high is not None and low >= -margin and high <= margin,
        above_noninferiority=low is not None and low > -margin,
    )


def contrast_effects(
    differences: ExtensionTable, header: ContrastHeader, config: Config
) -> ContrastEffects:
    if differences.height == 0:
        return ContrastEffects(seeds=pl.DataFrame(), rows=())
    rows: list[ExtensionEffectRow] = []
    for cell, group in (
        differences.sort(Column.SEED)
        .partition_by(cell_keys(), as_dict=True, maintain_order=True)
        .items()
    ):
        scope, population, alpha = cell
        rows.append(
            _row(
                header,
                EffectCell(
                    scope=ExtensionScope(scope),
                    population=EvaluationPopulation(population),
                    alpha=alpha,
                ),
                group[Column.DIFFERENCE].to_numpy(),
                config,
            )
        )
    return ContrastEffects(
        seeds=differences.with_columns(
            pl.lit(header.learner).alias(Column.LEARNER),
            pl.lit(header.contrast).alias(Column.CONTRAST),
            pl.lit(header.level, dtype=pl.Int64).alias(Column.LEVEL),
        ),
        rows=tuple(rows),
    )


def holm_group(contrast: ExtensionContrast) -> ExtensionContrast | None:
    if contrast in (ExtensionContrast.DOSE_CTK, ExtensionContrast.NATURAL_CTK):
        return ExtensionContrast.DOSE_CTK
    if contrast in (ExtensionContrast.CTK_TRIMMED, ExtensionContrast.CTK_MEDIAN):
        return ExtensionContrast.CTK_TRIMMED
    if contrast in (ExtensionContrast.TRIMMED_MINUS_MEAN, ExtensionContrast.MEDIAN_MINUS_MEAN):
        return ExtensionContrast.TRIMMED_MINUS_MEAN
    return None


def with_holm(rows: list[ExtensionEffectRow]) -> list[ExtensionEffectRow]:
    families: HolmIndex = {}
    for index, row in enumerate(rows):
        group = holm_group(row.contrast)
        if group is not None:
            key = (row.hypothesis, row.scope, row.learner, row.population, row.alpha, group)
            families.setdefault(key, []).append(index)
    adjusted = list(rows)
    for members in families.values():
        holm = holm_adjust(np.array([rows[index].p_value for index in members]))
        for index, p_value in zip(members, holm.tolist(), strict=True):
            adjusted[index] = rows[index].model_copy(update={Column.P_HOLM: p_value})
    return adjusted


def arm_selector(
    condition: ExposureCondition,
    dose: DoseRequest = None,
    aggregation: Aggregation | None = None,
) -> ArmSelector:
    return ArmSelector(condition=condition, dose=dose, aggregation=aggregation)


def design_experiments(
    config: Config, design: ExperimentDesign, mode: ExecutionMode
) -> tuple[ExperimentName, ...]:
    return tuple(
        name
        for name, spec in config.experiments.experiments.items()
        if spec.design is design and config.experiments.runs_in(name, mode)
    )
