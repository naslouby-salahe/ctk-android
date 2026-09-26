from dataclasses import dataclass
from itertools import pairwise
from statistics import NormalDist

import numpy as np
import polars as pl
import scipy.sparse as sp
from scipy import stats

from ctk_android.analysis.decomposition import family_seed_effects
from ctk_android.analysis.statistics import bca_interval, holm_adjust
from ctk_android.config import Config, NoveltyConfig, StatisticsConfig
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Aggregation,
    Column,
    ConsistencyMeasure,
    DoseAnchor,
    DrawStream,
    EligibilityReason,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExtensionContrast,
    ExtensionHypothesis,
    ExtensionScope,
    FamilySetName,
    HiddadStatus,
    LargeFamilyMeasure,
    Learner,
    LibraryOption,
    NoveltyDescriptor,
    PrecisionRho,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    RepresentationOutcome,
    SignTail,
    SplitRole,
    StatisticsLimit,
    Tolerance,
)
from ctk_android.types import (
    ActiveMask,
    ArmSelector,
    AssociationMeasures,
    AttributeColumn,
    ConsistencyRow,
    ContrastEffects,
    ContrastHeader,
    Correlation,
    DescriptorRow,
    DescriptorScoreTable,
    DescriptorTable,
    DescriptorValues,
    DoseRequest,
    Effect,
    EffectCell,
    EligibilityStabilityTable,
    ExposureTable,
    ExtensionEffectRow,
    ExtensionTable,
    ExtensionVerdictRow,
    FamilyCentroids,
    FamilyCountsTable,
    FamilyFitRows,
    FamilyMasks,
    FamilyName,
    FamilySeedTable,
    Fraction,
    GainVector,
    HolmIndex,
    Interval,
    LargeFamilyRow,
    LargeFamilyTable,
    LargeSelectionTable,
    LargeStabilityRow,
    LargeSummaryRow,
    LargeSummaryTable,
    MetVerdict,
    NoveltyAssociation,
    NoveltyTable,
    NoveltyVector,
    PlaceboChoice,
    PlaceboTable,
    PlannedTargetsBySeed,
    Prevalence,
    PValue,
    Rate,
    RecallArm,
    Relatedness,
    RepresentationEffectRow,
    RepresentationLevelRow,
    RepresentationOf,
    RepresentationTable,
    RepresentationTables,
    RepresentationVerdictRow,
    RowCount,
    RowIndices,
    ScopeExperiments,
    Score,
    SeedCountVector,
    SeedEffects,
    SeedPairsTables,
    SeedRecallTable,
    SelectorPair,
    SpreadVector,
    StabilitySeedTable,
    StudyData,
    SupportCount,
    Table,
    TargetPair,
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


def _contrast_row(
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
            _contrast_row(
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


def controls_experiments(config: Config, mode: ExecutionMode) -> tuple[ExperimentName, ...]:
    return design_experiments(config, ExperimentDesign.PLACEBO_ROBUST, mode)


def _pair(aggregation: Aggregation | None) -> SelectorPair:
    return SelectorPair(
        minuend=arm_selector(ExposureCondition.PEER_PRESENT, None, aggregation),
        subtrahend=arm_selector(ExposureCondition.FAMILY_ABSENT_EVERYWHERE, None, aggregation),
    )


def _header(
    hypothesis: ExtensionHypothesis,
    contrast: ExtensionContrast,
    tail: SignTail,
    reference: Effect,
) -> ContrastHeader:
    return ContrastHeader(
        hypothesis=hypothesis,
        learner=Learner.FEDAVG,
        contrast=contrast,
        level=None,
        tail=tail,
        reference=reference,
    )


def _ctk(recalls: SeedRecallTable, aggregation: Aggregation | None) -> ExtensionTable:
    pair = _pair(aggregation)
    return arm_difference(recalls, Learner.FEDAVG, pair.minuend, pair.subtrahend)


def controls_effects(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> ContrastEffects:
    recalls = seed_recalls(families, config, experiments)
    margin = config.statistics.gates.ctk_min_gain
    placebo = arm_selector(ExposureCondition.PLACEBO)
    absent = arm_selector(ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    present = arm_selector(ExposureCondition.PEER_PRESENT)
    mean = _ctk(recalls, None)
    trimmed = _ctk(recalls, Aggregation.TRIMMED_MEAN)
    median = _ctk(recalls, Aggregation.COORDINATE_MEDIAN)
    first, second = ExtensionHypothesis.PLACEBO, ExtensionHypothesis.ROBUST_AGGREGATION
    contrasts = [
        contrast_effects(
            arm_difference(recalls, Learner.FEDAVG, placebo, absent),
            _header(first, ExtensionContrast.PLACEBO_EFFECT, SignTail.TWO_SIDED, 0.0),
            config,
        ),
        contrast_effects(
            arm_difference(recalls, Learner.FEDAVG, present, placebo),
            _header(first, ExtensionContrast.CTK_MINUS_PLACEBO, SignTail.GREATER, margin),
            config,
        ),
        contrast_effects(
            mean,
            _header(
                ExtensionHypothesis.DESCRIPTIVE,
                ExtensionContrast.CTK_MEAN,
                SignTail.GREATER,
                0.0,
            ),
            config,
        ),
        contrast_effects(
            trimmed,
            _header(second, ExtensionContrast.CTK_TRIMMED, SignTail.GREATER, margin),
            config,
        ),
        contrast_effects(
            median,
            _header(second, ExtensionContrast.CTK_MEDIAN, SignTail.GREATER, margin),
            config,
        ),
        contrast_effects(
            difference_of_differences(trimmed, mean),
            _header(second, ExtensionContrast.TRIMMED_MINUS_MEAN, SignTail.GREATER, -margin),
            config,
        ),
        contrast_effects(
            difference_of_differences(median, mean),
            _header(second, ExtensionContrast.MEDIAN_MINUS_MEAN, SignTail.GREATER, -margin),
            config,
        ),
    ]
    seeds = [effect.seeds for effect in contrasts if effect.seeds.height]
    return ContrastEffects(
        seeds=pl.concat(seeds) if seeds else pl.DataFrame(),
        rows=tuple(with_holm([row for effect in contrasts for row in effect.rows])),
    )


def _control_cell(
    rows: tuple[ExtensionEffectRow, ...], contrast: ExtensionContrast
) -> list[ExtensionEffectRow]:
    return [row for row in rows if row.contrast is contrast]


def controls_verdicts(effects: tuple[ExtensionEffectRow, ...], config: Config) -> ExtensionTable:
    level = 1.0 - config.statistics.confidence_level
    cells = sorted({(row.scope, row.population, row.alpha) for row in effects})
    verdicts: list[ExtensionVerdictRow] = []
    for scope, population, alpha in cells:
        here = tuple(
            row
            for row in effects
            if (row.scope, row.population, row.alpha) == (scope, population, alpha)
        )
        placebo = _control_cell(here, ExtensionContrast.PLACEBO_EFFECT)
        beyond = _control_cell(here, ExtensionContrast.CTK_MINUS_PLACEBO)
        ctk = _control_cell(here, ExtensionContrast.CTK_TRIMMED) + _control_cell(
            here, ExtensionContrast.CTK_MEDIAN
        )
        noninferior = _control_cell(here, ExtensionContrast.TRIMMED_MINUS_MEAN) + _control_cell(
            here, ExtensionContrast.MEDIAN_MINUS_MEAN
        )
        specific = (
            len(placebo) > 0
            and len(beyond) > 0
            and placebo[0].within_band
            and beyond[0].above_margin
        )
        robust = (
            len(ctk) == len(noninferior) > 0
            and all(row.above_margin and (row.p_holm or 1.0) < level for row in ctk)
            and all(row.above_noninferiority for row in noninferior)
        )
        for hypothesis, met in (
            (ExtensionHypothesis.PLACEBO, specific),
            (ExtensionHypothesis.ROBUST_AGGREGATION, robust),
        ):
            verdicts.append(
                ExtensionVerdictRow(
                    hypothesis=hypothesis,
                    scope=scope,
                    learner=Learner.FEDAVG,
                    population=population,
                    alpha=alpha,
                    met=met,
                    onset_level=None,
                )
            )
    return records_to_frame(verdicts)


def placebo_table(placebo: PlaceboTable) -> PlaceboTable:
    if placebo.height == 0:
        return placebo
    return placebo.sort(Column.EXPERIMENT, Column.SEED, Column.FAMILY)


def dose_experiments(config: Config, mode: ExecutionMode) -> tuple[ExperimentName, ...]:
    return design_experiments(config, ExperimentDesign.EXACT_DOSE, mode)


def _difference(
    recalls: SeedRecallTable, learner: Learner, upper: DoseRequest, lower: DoseRequest
) -> ExtensionTable:
    return arm_difference(
        recalls,
        learner,
        arm_selector(ExposureCondition.EXACT_DOSE, upper),
        arm_selector(ExposureCondition.EXACT_DOSE, lower),
    )


def dose_contrasts(
    recalls: SeedRecallTable, learner: Learner, config: Config
) -> list[ContrastEffects]:
    levels = [level for level in config.experiments.exact_dose_levels if level != DoseAnchor.ZERO]
    zero = DoseAnchor.ZERO
    onset = ExtensionHypothesis.DOSE_ONSET
    results: list[ContrastEffects] = [
        contrast_effects(
            _difference(recalls, learner, level, zero),
            ContrastHeader(
                hypothesis=onset,
                learner=learner,
                contrast=ExtensionContrast.DOSE_CTK,
                level=level,
                tail=SignTail.GREATER,
                reference=0.0,
            ),
            config,
        )
        for level in levels
    ]
    results.append(
        contrast_effects(
            arm_difference(
                recalls,
                learner,
                arm_selector(ExposureCondition.PEER_PRESENT),
                arm_selector(ExposureCondition.EXACT_DOSE, zero),
            ),
            ContrastHeader(
                hypothesis=onset,
                learner=learner,
                contrast=ExtensionContrast.NATURAL_CTK,
                level=None,
                tail=SignTail.GREATER,
                reference=0.0,
            ),
            config,
        )
    )
    for lower, upper, contrast, hypothesis in (
        (
            DoseAnchor.LOW,
            DoseAnchor.MID,
            ExtensionContrast.INCREMENT_50_100,
            ExtensionHypothesis.DESCRIPTIVE,
        ),
        (
            DoseAnchor.MID,
            DoseAnchor.HIGH,
            ExtensionContrast.INCREMENT_100_200,
            ExtensionHypothesis.DOSE_SATURATION,
        ),
    ):
        results.append(
            contrast_effects(
                _difference(recalls, learner, upper, lower),
                ContrastHeader(
                    hypothesis=hypothesis,
                    learner=learner,
                    contrast=contrast,
                    level=upper,
                    tail=SignTail.TWO_SIDED,
                    reference=0.0,
                ),
                config,
            )
        )
    results.append(
        contrast_effects(
            arm_difference(
                recalls,
                learner,
                arm_selector(ExposureCondition.EXACT_DOSE, zero),
                arm_selector(ExposureCondition.FAMILY_ABSENT_EVERYWHERE),
            ),
            ContrastHeader(
                hypothesis=ExtensionHypothesis.DESCRIPTIVE,
                learner=learner,
                contrast=ExtensionContrast.ZERO_VERSUS_ABSENT,
                level=zero,
                tail=SignTail.TWO_SIDED,
                reference=0.0,
            ),
            config,
        )
    )
    return results


def dose_effects(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> ContrastEffects:
    recalls = seed_recalls(families, config, experiments)
    learners = dict.fromkeys(
        learner for name in experiments for learner in config.experiments.experiments[name].learners
    )
    contrasts = [
        effect for learner in learners for effect in dose_contrasts(recalls, learner, config)
    ]
    seeds = [effect.seeds for effect in contrasts if effect.seeds.height]
    return ContrastEffects(
        seeds=pl.concat(seeds) if seeds else pl.DataFrame(),
        rows=tuple(with_holm([row for effect in contrasts for row in effect.rows])),
    )


def dose_family_curves(
    families: FamilyCountsTable, experiments: tuple[ExperimentName, ...]
) -> ExtensionTable:
    if families.height == 0 or not experiments:
        return pl.DataFrame()
    keys = [
        Column.EXPERIMENT,
        Column.SEED,
        Column.SALT,
        Column.CLIENT,
        Column.FAMILY,
        Column.LEARNER,
        Column.POPULATION,
        Column.ALPHA,
    ]
    recalls = (
        families.filter(
            is_one_of(Column.EXPERIMENT, list(experiments)) & (pl.col(Column.TRIALS) > 0)
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .select(*keys, Column.CONDITION, Column.DOSE, Column.RECALL)
    )
    zero = recalls.filter(
        (pl.col(Column.CONDITION) == ExposureCondition.EXACT_DOSE)
        & (pl.col(Column.DOSE) == DoseAnchor.ZERO)
    ).select(*keys, pl.col(Column.RECALL).alias(Column.SUBTRAHEND))
    exact = recalls.filter(pl.col(Column.CONDITION) == ExposureCondition.EXACT_DOSE)
    return (
        exact.join(zero, on=keys)
        .with_columns((pl.col(Column.RECALL) - pl.col(Column.SUBTRAHEND)).alias(Column.CTK_GAIN))
        .group_by(
            Column.EXPERIMENT,
            Column.FAMILY,
            Column.LEARNER,
            Column.POPULATION,
            Column.ALPHA,
            Column.DOSE,
            maintain_order=True,
        )
        .agg(
            pl.col(Column.CTK_GAIN).mean().alias(Column.MEAN_CTK),
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
        )
        .sort(
            Column.EXPERIMENT,
            Column.FAMILY,
            Column.LEARNER,
            Column.POPULATION,
            Column.ALPHA,
            Column.DOSE,
        )
    )


def _targets(families: FamilyCountsTable) -> ExtensionTable:
    return (
        families.select(Column.EXPERIMENT, Column.SEED, Column.SALT, Column.CLIENT, Column.FAMILY)
        .unique()
        .rename({Column.CLIENT: Column.TARGET_CLIENT})
    )


def dose_consistency(
    exposure: ExposureTable, families: FamilyCountsTable, experiments: tuple[ExperimentName, ...]
) -> ExtensionTable:
    if exposure.height == 0 or not experiments:
        return pl.DataFrame()
    keys = [Column.EXPERIMENT, Column.SEED, Column.SALT, Column.FAMILY]
    exact = (
        exposure.filter(
            is_one_of(Column.EXPERIMENT, list(experiments))
            & (pl.col(Column.CONDITION) == ExposureCondition.EXACT_DOSE)
            & (pl.col(Column.LEARNER) == Learner.FEDAVG)
        )
        .join(_targets(families), on=keys)
        .with_columns((pl.col(Column.CLIENT) == pl.col(Column.TARGET_CLIENT)).alias(Column.SCOPE))
    )
    per_pair = exact.group_by(*keys, Column.DOSE, maintain_order=True).agg(
        pl.col(Column.ROWS).filter(~pl.col(Column.SCOPE)).sum().alias(Column.PEER_ROWS),
        pl.col(Column.ROWS).filter(pl.col(Column.SCOPE)).sum().alias(Column.TARGET_ROWS),
    )
    rows: list[ConsistencyRow] = []
    for experiment in experiments:
        scoped = per_pair.filter(pl.col(Column.EXPERIMENT) == experiment)
        for level in sorted(scoped[Column.DOSE].unique().to_list()):
            at_level = scoped.filter(pl.col(Column.DOSE) == level)
            rows.append(
                ConsistencyRow(
                    experiment=experiment,
                    measure=ConsistencyMeasure.REALISED_DOSE,
                    level=level,
                    checked=at_level.height,
                    mismatched=at_level.filter(pl.col(Column.PEER_ROWS) != level).height,
                    rows=at_level[Column.PEER_ROWS].to_numpy().sum().item(),
                )
            )
            rows.append(
                ConsistencyRow(
                    experiment=experiment,
                    measure=ConsistencyMeasure.TARGET_ZERO,
                    level=level,
                    checked=at_level.height,
                    mismatched=at_level.filter(pl.col(Column.TARGET_ROWS) != 0).height,
                    rows=at_level[Column.TARGET_ROWS].to_numpy().sum().item(),
                )
            )
        volume = (
            exposure.filter(pl.col(Column.EXPERIMENT) == experiment)
            .group_by(Column.SEED, Column.SALT, Column.CLIENT, Column.FAMILY, maintain_order=True)
            .agg(pl.col(Column.TRAIN_ROWS).n_unique().alias(Column.VOLUME_IDENTICAL))
        )
        rows.append(
            ConsistencyRow(
                experiment=experiment,
                measure=ConsistencyMeasure.VOLUME,
                level=None,
                checked=volume.height,
                mismatched=volume.filter(pl.col(Column.VOLUME_IDENTICAL) != 1).height,
                rows=0,
            )
        )
    return records_to_frame(rows)


def _onset(rows: list[ExtensionEffectRow]) -> DoseRequest:
    hits = [row.level for row in rows if row.above_margin and row.level is not None]
    return min(hits) if hits else None


def dose_verdicts(effects: tuple[ExtensionEffectRow, ...], config: Config) -> ExtensionTable:
    alpha = 1.0 - config.statistics.confidence_level
    cells = {(row.scope, row.learner, row.population, row.alpha) for row in effects}
    verdicts: list[ExtensionVerdictRow] = []
    for scope, learner, population, cell_alpha in sorted(cells):
        cell = [
            row
            for row in effects
            if (row.scope, row.learner, row.population, row.alpha)
            == (scope, learner, population, cell_alpha)
        ]
        ctk = [row for row in cell if row.contrast is ExtensionContrast.DOSE_CTK]
        saturation = [row for row in cell if row.contrast is ExtensionContrast.INCREMENT_100_200]
        top = [row for row in ctk if row.level == DoseAnchor.HIGH]
        # Amendment A1: family-macro CTK non-decreasing across the exact levels (the natural
        # level has no exact dose and is not ordered).
        exact = sorted(
            (row for row in ctk if row.level is not None), key=lambda row: row.level or 0
        )
        rises = len(exact) > 0 and all(
            later.mean >= earlier.mean for earlier, later in pairwise(exact)
        )
        significant = len(top) > 0 and top[0].p_holm is not None and top[0].p_holm < alpha
        verdicts.append(
            ExtensionVerdictRow(
                hypothesis=ExtensionHypothesis.DOSE_ONSET,
                scope=scope,
                learner=learner,
                population=population,
                alpha=cell_alpha,
                met=significant and rises,
                onset_level=_onset(ctk),
            )
        )
        verdicts.append(
            ExtensionVerdictRow(
                hypothesis=ExtensionHypothesis.DOSE_SATURATION,
                scope=scope,
                learner=learner,
                population=population,
                alpha=cell_alpha,
                met=saturation[0].within_band if saturation else None,
                onset_level=None,
            )
        )
    return records_to_frame(verdicts)


def representation_experiments(config: Config, mode: ExecutionMode) -> tuple[ExperimentName, ...]:
    return design_experiments(config, ExperimentDesign.REPRESENTATION, mode)


def representation_map(config: Config, experiments: tuple[ExperimentName, ...]) -> RepresentationOf:
    return {
        name: representation
        for name in experiments
        if (representation := config.experiments.experiments[name].representation) is not None
    }


def _recalls(
    families: FamilyCountsTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    arm: RecallArm,
) -> RepresentationTable:
    experiments_config = config.experiments
    minimum = config.data.eligibility[
        experiments_config.experiments[experiments[0]].eligibility
    ].own_domain_min_test
    federation = pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE
    learner, condition = arm.learner, arm.condition
    return (
        families.filter(
            is_one_of(Column.EXPERIMENT, list(experiments))
            & is_one_of(
                Column.POPULATION,
                [EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN],
            )
            & (pl.col(Column.ALPHA) == experiments_config.operating.primary_alpha)
            & (pl.col(Column.LEARNER) == learner)
            & (pl.col(Column.CONDITION) == condition)
            & pl.col(Column.DOSE).is_null()
            & (
                pl.col(Column.TRIALS)
                >= pl.when(federation).then(pl.lit(1)).otherwise(pl.lit(minimum))
            )
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.VALUE))
        .group_by(
            Column.EXPERIMENT, Column.SEED, Column.FAMILY, Column.POPULATION, maintain_order=True
        )
        .agg(pl.col(Column.VALUE).mean())
    )


def _measure(
    families: FamilyCountsTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    measure: RepresentationMeasure,
) -> RepresentationTable:
    if measure is RepresentationMeasure.FULL_EXPOSURE_RECALL:
        return _recalls(
            families,
            config,
            experiments,
            RecallArm(learner=Learner.CENTRAL, condition=ExposureCondition.FULL_EXPOSURE),
        )
    keys = [Column.EXPERIMENT, Column.SEED, Column.FAMILY, Column.POPULATION]
    peer = _recalls(
        families,
        config,
        experiments,
        RecallArm(learner=Learner.FEDAVG, condition=ExposureCondition.PEER_PRESENT),
    )
    absent = _recalls(
        families,
        config,
        experiments,
        RecallArm(learner=Learner.FEDAVG, condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE),
    ).rename({Column.VALUE: Column.BASELINE})
    return peer.join(absent, on=keys).select(
        *keys, (pl.col(Column.VALUE) - pl.col(Column.BASELINE)).alias(Column.VALUE)
    )


def _tagged(values: RepresentationTable, mapping: RepresentationOf) -> RepresentationTable:
    names = pl.DataFrame(
        {
            Column.EXPERIMENT: pl.Series(list(mapping), dtype=pl.String),
            Column.REPRESENTATION: pl.Series(list(mapping.values()), dtype=pl.String),
        }
    )
    return values.join(names, on=Column.EXPERIMENT).drop(Column.EXPERIMENT)


def _paired(values: RepresentationTable) -> RepresentationTable:
    reference = values.filter(pl.col(Column.REPRESENTATION) == Representation.LAMDA_STATIC).select(
        Column.SEED, Column.FAMILY, Column.POPULATION, pl.col(Column.VALUE).alias(Column.BASELINE)
    )
    return (
        values.filter(pl.col(Column.REPRESENTATION) != Representation.LAMDA_STATIC)
        .join(reference, on=[Column.SEED, Column.FAMILY, Column.POPULATION])
        .with_columns((pl.col(Column.VALUE) - pl.col(Column.BASELINE)).alias(Column.DIFFERENCE))
    )


def _cells(values: RepresentationTable, config: Config) -> RepresentationTable:
    experiments = config.experiments
    listed = (
        *experiments.representation_priority_families,
        *experiments.representation_contrast_families,
        *experiments.representation_separate_families,
    )
    numeric = [
        column
        for column in (Column.VALUE, Column.BASELINE, Column.DIFFERENCE)
        if column in values.columns
    ]
    order = [Column.REPRESENTATION, Column.GROUP, Column.FAMILY, Column.POPULATION, Column.SEED]
    parts = [
        values.filter(is_one_of(Column.FAMILY, listed))
        .with_columns(pl.lit(RepresentationGroup.FAMILY).alias(Column.GROUP))
        .select(*order, *numeric)
    ]
    for group, names in (
        (RepresentationGroup.PRIORITY_MACRO, experiments.representation_priority_families),
        (RepresentationGroup.CONTRAST_MACRO, experiments.representation_contrast_families),
    ):
        parts.append(
            values.filter(is_one_of(Column.FAMILY, names))
            .group_by(Column.REPRESENTATION, Column.POPULATION, Column.SEED, maintain_order=True)
            .agg(*(pl.col(column).mean() for column in numeric))
            .with_columns(
                pl.lit(group).alias(Column.GROUP),
                pl.lit(None, dtype=pl.String).alias(Column.FAMILY),
            )
            .select(*order, *numeric)
        )
    return pl.concat(parts).sort(*order)


def _cell_groups(cells: RepresentationTable) -> list[Table]:
    return cells.partition_by(
        [Column.REPRESENTATION, Column.GROUP, Column.FAMILY, Column.POPULATION], maintain_order=True
    )


def _effect_row(
    measure: RepresentationMeasure, group: Table, config: Config
) -> RepresentationEffectRow:
    margin = config.statistics.gates.ctk_min_gain
    values: SeedEffects = group[Column.DIFFERENCE].to_numpy()
    interval = bca_interval(values, config.statistics)
    low, high = (None, None) if interval is None else (interval.low, interval.high)
    head = group.row(0, named=True)
    return RepresentationEffectRow(
        measure=measure,
        representation=head[Column.REPRESENTATION],
        group=head[Column.GROUP],
        family=head[Column.FAMILY],
        population=head[Column.POPULATION],
        alpha=config.experiments.operating.primary_alpha,
        seed_count=values.size,
        mean_level=group[Column.VALUE].to_numpy().mean().item(),
        mean_baseline=group[Column.BASELINE].to_numpy().mean().item(),
        mean=values.mean().item(),
        median=np.median(values).item(),
        positive_seeds=(values > 0).sum().item(),
        ci_low=low,
        ci_high=high,
        p_value=shifted_wilcoxon(values, 0.0, SignTail.TWO_SIDED),
        p_margin=shifted_wilcoxon(values, margin, SignTail.GREATER),
        p_holm=None,
        margin=margin,
        above_margin=low is not None and low > margin,
        below_margin=high is not None and high < margin,
        within_band=low is not None and high is not None and low >= -margin and high <= margin,
    )


def _level_row(
    measure: RepresentationMeasure, group: Table, config: Config
) -> RepresentationLevelRow:
    values: SeedEffects = group[Column.VALUE].to_numpy()
    interval = bca_interval(values, config.statistics)
    head = group.row(0, named=True)
    return RepresentationLevelRow(
        measure=measure,
        representation=head[Column.REPRESENTATION],
        group=head[Column.GROUP],
        family=head[Column.FAMILY],
        population=head[Column.POPULATION],
        alpha=config.experiments.operating.primary_alpha,
        seed_count=values.size,
        mean=values.mean().item(),
        ci_low=None if interval is None else interval.low,
        ci_high=None if interval is None else interval.high,
    )


def holm_rows(rows: list[RepresentationEffectRow], config: Config) -> list[RepresentationEffectRow]:
    priority = config.experiments.representation_priority_families
    members = [
        index
        for index, row in enumerate(rows)
        if row.measure is RepresentationMeasure.FULL_EXPOSURE_RECALL
        and row.group is RepresentationGroup.FAMILY
        and row.family in priority
        and row.population is EvaluationPopulation.FEDERATION_WIDE
    ]
    adjusted = list(rows)
    if members:
        holm = holm_adjust(np.array([rows[index].p_value for index in members]))
        for index, p_value in zip(members, holm.tolist(), strict=True):
            adjusted[index] = rows[index].model_copy(update={Column.P_HOLM: p_value})
    return adjusted


def representation_tables(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> RepresentationTables:
    mapping = representation_map(config, experiments)
    seeds: list[RepresentationTable] = []
    effects: list[RepresentationEffectRow] = []
    levels: list[RepresentationLevelRow] = []
    for measure in RepresentationMeasure:
        values = _tagged(_measure(families, config, experiments, measure), mapping)
        if values.height == 0:
            continue
        paired = _cells(_paired(values), config)
        seeds.append(paired.with_columns(pl.lit(measure).alias(Column.MEASURE)))
        effects.extend(_effect_row(measure, group, config) for group in _cell_groups(paired))
        levels.extend(
            _level_row(measure, group, config) for group in _cell_groups(_cells(values, config))
        )
    return RepresentationTables(
        seeds=pl.concat(seeds) if seeds else pl.DataFrame(),
        effects=tuple(holm_rows(effects, config)),
        levels=tuple(levels),
    )


def _representation_cell(
    rows: tuple[RepresentationEffectRow, ...],
    representation: Representation,
    group: RepresentationGroup,
    family: FamilyName | None,
) -> RepresentationEffectRow | None:
    matching = [
        row
        for row in rows
        if row.measure is RepresentationMeasure.FULL_EXPOSURE_RECALL
        and row.population is EvaluationPopulation.FEDERATION_WIDE
        and row.representation is representation
        and row.group is group
        and row.family == family
    ]
    return matching[0] if matching else None


def _low(row: RepresentationEffectRow | None) -> Effect | None:
    return None if row is None else row.ci_low


def _high(row: RepresentationEffectRow | None) -> Effect | None:
    return None if row is None else row.ci_high


def representation_verdicts(effects: tuple[RepresentationEffectRow, ...], config: Config) -> Table:
    margin = config.statistics.gates.ctk_min_gain
    priority = _representation_cell(
        effects,
        Representation.MCNDROID_STATIC,
        RepresentationGroup.PRIORITY_MACRO,
        None,
    )
    lower = _low(priority)
    first: MetVerdict = None if lower is None else lower > margin
    focus = config.experiments.representation_focus_family
    hiddad = [
        _representation_cell(effects, representation, RepresentationGroup.FAMILY, focus)
        for representation in (
            Representation.MCNDROID_STATIC,
            Representation.CALL_GRAPH,
            Representation.REPORT_JSON,
        )
    ]
    uppers = [_high(row) for row in hiddad]
    second: MetVerdict = (
        None
        if any(value is None for value in uppers)
        else all(value is not None and value < margin for value in uppers)
    )
    status = _hiddad_status([_low(row) for row in hiddad], second, margin)
    return records_to_frame(
        [
            RepresentationVerdictRow(
                hypothesis=ExtensionHypothesis.REPRESENTATION_RESCUE,
                representation=Representation.MCNDROID_STATIC,
                met=first,
                outcome=None,
            ),
            RepresentationVerdictRow(
                hypothesis=ExtensionHypothesis.REPRESENTATION_HIDDAD,
                representation=None,
                met=second,
                outcome=status,
            ),
            RepresentationVerdictRow(
                hypothesis=ExtensionHypothesis.REPRESENTATION_OUTCOME,
                representation=None,
                met=None,
                outcome=_outcome(first, status),
            ),
        ]
    )


# Failing H-REP-2 (no upper bound below the margin) is not evidence of a rescue. A rescue needs
# an interval above the margin, symmetric with H-REP-1; otherwise the hiddad status is unresolved.
def _hiddad_status(
    lowers: list[Effect | None], second: MetVerdict, margin: Effect
) -> HiddadStatus | None:
    if second is None:
        return None
    if second:
        return HiddadStatus.NOT_RESCUED
    if any(value is not None and value > margin for value in lowers):
        return HiddadStatus.RESCUED
    return HiddadStatus.UNRESOLVED


def _outcome(first: MetVerdict, status: HiddadStatus | None) -> RepresentationOutcome:
    if first is None or status is None:
        return RepresentationOutcome.UNDETERMINED
    if not first:
        return RepresentationOutcome.LIMITS_STAND
    return {
        HiddadStatus.NOT_RESCUED: RepresentationOutcome.FAMILY_SPECIFIC_LIMITS,
        HiddadStatus.RESCUED: RepresentationOutcome.HIDDAD_RESCUED,
        HiddadStatus.UNRESOLVED: RepresentationOutcome.HIDDAD_UNRESOLVED,
    }[status]


def eligibility_table(
    planned: PlannedTargetsBySeed, members: tuple[FamilyName, ...]
) -> RepresentationTable:
    cells = [
        (seed, family, {pair.family: pair.client for pair in targets})
        for seed, targets in sorted(planned.items())
        for family in members
    ]
    return pl.DataFrame(
        {
            Column.SEED: [seed for seed, _, _ in cells],
            Column.FAMILY_SET: [FamilySetName.PRIMARY] * len(cells),
            Column.FAMILY: [family for _, family, _ in cells],
            Column.ELIGIBLE: [family in clients for _, family, clients in cells],
            Column.CLIENT: [clients.get(family) for _, family, clients in cells],
        },
        schema={
            Column.SEED: pl.Int64,
            Column.FAMILY_SET: pl.String,
            Column.FAMILY: pl.String,
            Column.ELIGIBLE: pl.Boolean,
            Column.CLIENT: pl.String,
        },
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


def _summary_row(
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
        _summary_row(LargeFamilyMeasure.CTK_MEAN, ctk.mean().item()),
        _summary_row(LargeFamilyMeasure.CTK_SD, np.sqrt(between).item()),
        _summary_row(LargeFamilyMeasure.CTK_NOISE_SD, np.sqrt(noise).item()),
        _summary_row(LargeFamilyMeasure.CTK_SIGNAL_SD, np.sqrt(signal).item()),
        _summary_row(LargeFamilyMeasure.CTK_RELIABILITY, signal / between if between > 0 else 0.0),
    ]


def _descriptor_rows(scores: NoveltyVector) -> list[LargeSummaryRow]:
    return [
        _summary_row(LargeFamilyMeasure.DESCRIPTOR_SD, np.std(scores, ddof=1).item()),
        _summary_row(
            LargeFamilyMeasure.DESCRIPTOR_IQR,
            np.asarray(stats.iqr(scores)).item(),
        ),
        _summary_row(LargeFamilyMeasure.DESCRIPTOR_DISTINCT, np.unique(scores).size),
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
    rows = [_summary_row(rho, association.rho), _summary_row(p_value, association.p_value)]
    interval: Interval | None = association.interval
    if interval is not None:
        rows += [
            _summary_row(low, interval.low),
            _summary_row(high, interval.high),
            _summary_row(width, interval.high - interval.low),
        ]
    return rows


def _precision_rows(families: RowCount, config: Config) -> list[LargeSummaryRow]:
    if families <= StatisticsLimit.ASSOCIATION_FAMILIES:
        return []
    z = _z(config)
    return [
        _summary_row(
            LargeFamilyMeasure.EXPECTED_CI_WIDTH,
            expected_ci_width(rho, families, z),
            rho,
        )
        for rho in PrecisionRho
    ] + [_summary_row(LargeFamilyMeasure.MIN_DETECTABLE_RHO, _detectable_rho(families, z))]


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
        _summary_row(LargeFamilyMeasure.FAMILIES_PLANNED, planned),
        _summary_row(LargeFamilyMeasure.FAMILIES_DEFINED, table.height),
        _summary_row(LargeFamilyMeasure.FAMILIES_WITH_DESCRIPTOR, scored.height),
        _summary_row(
            LargeFamilyMeasure.MEAN_SUPPORT, table[Column.TRIALS].to_numpy().mean().item()
        ),
        _summary_row(
            LargeFamilyMeasure.MIN_SUPPORT, table[Column.MIN_TRIALS].to_numpy().min().item()
        ),
        _summary_row(
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
    return [_summary_row(LargeFamilyMeasure.RHO_PERMUTATION_P, (1 + extreme) / (1 + draws))]


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
        _summary_row(LargeFamilyMeasure.SEEDS_WITH_RHO, seeds.size),
        _summary_row(LargeFamilyMeasure.SEED_RHO_MIN, seeds.min().item()),
        _summary_row(LargeFamilyMeasure.SEED_RHO_MEDIAN, np.median(seeds).item()),
        _summary_row(LargeFamilyMeasure.SEED_RHO_MAX, seeds.max().item()),
        _summary_row(LargeFamilyMeasure.SEED_RHO_POSITIVE, (seeds > 0).sum().item()),
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
        _summary_row(LargeFamilyMeasure.STABILITY_FAMILIES, stability.height),
        _summary_row(
            LargeFamilyMeasure.STABILITY_SEEDS, stability[Column.SEED_COUNT].to_numpy().max().item()
        ),
        _summary_row(LargeFamilyMeasure.STABLE_FAMILIES, len(stable)),
        _summary_row(LargeFamilyMeasure.MEAN_ELIGIBLE_FRACTION, fractions.mean().item()),
        _summary_row(LargeFamilyMeasure.MIN_ELIGIBLE_FRACTION, fractions.min().item()),
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


def _prevalence(study: StudyData, rows: RowIndices) -> Prevalence:
    block = study.features[rows]
    if sp.issparse(block):
        return np.asarray(block.mean(axis=0, dtype=np.float64)).ravel()
    return np.asarray(block, dtype=np.float64).mean(axis=0)


def _active(prevalence: Prevalence, threshold: Fraction) -> ActiveMask:
    return prevalence >= threshold


def _jaccard(left: ActiveMask, right: ActiveMask) -> Rate:
    union = np.logical_or(left, right).sum().item()
    return 1.0 if union == 0 else np.logical_and(left, right).sum().item() / union


def _distance(left: Prevalence, right: Prevalence) -> Score:
    return np.linalg.norm(left - right).item()


@dataclass(frozen=True)
class KnownFamilyGaps:
    distances: list[Score]
    jaccards: list[Rate]


def _known_family_gaps(
    study: StudyData,
    target: Prevalence,
    known_named: ActiveMask,
    family: AttributeColumn,
    config: NoveltyConfig,
) -> KnownFamilyGaps:
    target_active = _active(target, config.min_active_prevalence)
    distances: list[Score] = []
    jaccards: list[Rate] = []
    for name in np.unique(family[known_named]):
        group = np.flatnonzero(known_named & (family == name))
        if group.size < config.min_known_family_rows:
            continue
        centroid = _prevalence(study, group)
        distances.append(_distance(target, centroid))
        jaccards.append(_jaccard(target_active, _active(centroid, config.min_active_prevalence)))
    return KnownFamilyGaps(distances=distances, jaccards=jaccards)


def family_descriptors(
    study: StudyData,
    targets: tuple[TargetPair, ...],
    masks: FamilyMasks,
    config: NoveltyConfig,
) -> DescriptorTable:
    table = study.table
    fit = (table[Column.ROLE] == SplitRole.FIT).to_numpy()
    malware = (table[Column.LABEL] == 1).to_numpy()
    named = (table[Column.REASON] == EligibilityReason.ELIGIBLE).to_numpy()
    client = table[Column.CLIENT].to_numpy()
    family = table[Column.FAMILY].to_numpy()
    rows: list[DescriptorRow] = []
    for pair in targets:
        own = client == pair.client
        hidden = np.zeros(table.height, dtype=bool)
        for other in (p.family for p in targets if p.client is pair.client):
            hidden |= masks[other]
        peer_rows = np.flatnonzero(masks[pair.family] & fit & ~own)
        known_mask = own & fit & malware & ~hidden & ~masks[pair.family]
        known_rows = np.flatnonzero(known_mask)
        benign_rows = np.flatnonzero(own & fit & ~malware)
        if peer_rows.size == 0 or known_rows.size == 0 or benign_rows.size == 0:
            continue
        target = _prevalence(study, peer_rows)
        known_centroid = _prevalence(study, known_rows)
        target_active = _active(target, config.min_active_prevalence)
        gaps = _known_family_gaps(study, target, known_mask & named, family, config)
        distances, jaccards = gaps.distances, gaps.jaccards
        represented = np.logical_and(
            target_active, _active(known_centroid, config.min_active_prevalence)
        ).sum()
        values: DescriptorValues = {
            NoveltyDescriptor.CENTROID_DISTANCE_TO_KNOWN_MALWARE: _distance(target, known_centroid),
            NoveltyDescriptor.DISTANCE_TO_BENIGN_CENTROID: _distance(
                target, _prevalence(study, benign_rows)
            ),
            NoveltyDescriptor.FRACTION_ACTIVE_FEATURES_KNOWN: represented.item()
            / max(target_active.sum().item(), 1),
        }
        if distances:
            values[NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE] = min(distances)
            values[NoveltyDescriptor.MAX_JACCARD_TO_KNOWN_FAMILY] = max(jaccards)
        rows.extend(
            DescriptorRow(
                client=pair.client, family=pair.family, descriptor=descriptor, value=value
            )
            for descriptor, value in values.items()
        )
    return records_to_frame(rows)


def descriptor_by_family(
    novelty: NoveltyTable, descriptor: NoveltyDescriptor
) -> DescriptorScoreTable:
    return (
        novelty.filter(pl.col(Column.DESCRIPTOR) == descriptor)
        .sort(Column.FAMILY, Column.CLIENT)
        .group_by(Column.FAMILY, maintain_order=True)
        .agg(pl.col(Column.VALUE).mean().alias(Column.NOVELTY))
    )


def _rank_correlation(first: NoveltyVector, second: GainVector) -> Correlation:
    return np.corrcoef(stats.rankdata(first), stats.rankdata(second))[0, 1].item()


def novelty_association(
    gains: GainVector, scores: NoveltyVector, config: StatisticsConfig
) -> NoveltyAssociation | None:
    if gains.size < StatisticsLimit.ASSOCIATION_FAMILIES:
        return None
    result = stats.spearmanr(scores, gains)
    rng = np.random.default_rng(config.statistics_seed)
    picks = rng.integers(0, gains.size, size=(config.bootstrap_resamples, gains.size))
    resampled = np.array(
        [_rank_correlation(scores[pick], gains[pick]) for pick in picks], dtype=np.float64
    )
    resampled = resampled[np.isfinite(resampled)]
    tail = (1.0 - config.confidence_level) / 2.0
    interval = (
        Interval(
            low=np.quantile(resampled, tail).item(), high=np.quantile(resampled, 1.0 - tail).item()
        )
        if resampled.size
        else None
    )
    return NoveltyAssociation(
        rho=result.statistic.item(),
        p_value=result.pvalue.item(),
        interval=interval,
        families=gains.size,
    )


def _centroid(study: StudyData, rows: RowIndices) -> Prevalence:
    block = study.features[np.sort(rows)]
    if sp.issparse(block):
        return np.asarray(block.mean(axis=0, dtype=np.float64)).ravel()
    return np.asarray(block).mean(axis=0, dtype=np.float64)


def _all_fit_rows(fit: FamilyFitRows, family: FamilyName) -> RowIndices:
    return np.concatenate(list(fit[family].values()))


def known_family_centroids(
    study: StudyData, fit: FamilyFitRows, excluded: frozenset[FamilyName], config: NoveltyConfig
) -> FamilyCentroids:
    return {
        family: _centroid(study, _all_fit_rows(fit, family))
        for family in sorted(fit)
        if family not in excluded
        and sum(rows.size for rows in fit[family].values()) >= config.min_known_family_rows
    }


def family_relatedness(
    study: StudyData,
    fit: FamilyFitRows,
    centroids: FamilyCentroids,
    choice: PlaceboChoice,
) -> Relatedness:
    hidden = _centroid(study, _all_fit_rows(fit, choice.family))
    distances = {name: _distance(hidden, centroid) for name, centroid in centroids.items()}
    ranked = sorted(distances, key=lambda name: (distances[name], name))
    return Relatedness(
        centroid_distance=_distance(hidden, _centroid(study, _all_fit_rows(fit, choice.placebo))),
        nearest_known_distance=distances[ranked[0]] if ranked else None,
        placebo_rank=ranked.index(choice.placebo) + 1 if choice.placebo in distances else None,
        known_families=len(ranked),
    )
