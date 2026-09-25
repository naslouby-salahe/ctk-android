import polars as pl

from ctk_android.analysis.extension_effects import (
    arm_difference,
    arm_selector,
    contrast_effects,
    design_experiments,
    difference_of_differences,
    seed_recalls,
    with_holm,
)
from ctk_android.config import Config
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    Aggregation,
    Column,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExtensionContrast,
    ExtensionHypothesis,
    Learner,
    SignTail,
)
from ctk_android.types import (
    ContrastEffects,
    ContrastHeader,
    Effect,
    ExtensionEffectRow,
    ExtensionTable,
    ExtensionVerdictRow,
    FamilyCountsTable,
    PlaceboTable,
    SeedRecallTable,
    SelectorPair,
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


def _cell(
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
        placebo = _cell(here, ExtensionContrast.PLACEBO_EFFECT)
        beyond = _cell(here, ExtensionContrast.CTK_MINUS_PLACEBO)
        ctk = _cell(here, ExtensionContrast.CTK_TRIMMED) + _cell(here, ExtensionContrast.CTK_MEDIAN)
        noninferior = _cell(here, ExtensionContrast.TRIMMED_MINUS_MEAN) + _cell(
            here, ExtensionContrast.MEDIAN_MINUS_MEAN
        )
        specific = bool(placebo and beyond and placebo[0].within_band and beyond[0].above_margin)
        robust = bool(
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
