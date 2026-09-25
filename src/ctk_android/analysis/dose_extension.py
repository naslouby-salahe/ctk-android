from itertools import pairwise

import polars as pl

from ctk_android.analysis.extension_effects import (
    arm_difference,
    arm_selector,
    contrast_effects,
    design_experiments,
    seed_recalls,
    with_holm,
)
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    ConsistencyMeasure,
    DoseAnchor,
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
    ConsistencyRow,
    ContrastEffects,
    ContrastHeader,
    DoseRequest,
    ExposureTable,
    ExtensionEffectRow,
    ExtensionTable,
    ExtensionVerdictRow,
    FamilyCountsTable,
    SeedRecallTable,
)


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
        rises = bool(exact) and all(
            later.mean >= earlier.mean for earlier, later in pairwise(exact)
        )
        significant = bool(top and top[0].p_holm is not None and top[0].p_holm < alpha)
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
