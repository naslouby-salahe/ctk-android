import numpy as np
import polars as pl

from ctk_android.analysis.extension_effects import design_experiments, shifted_wilcoxon
from ctk_android.analysis.statistics import bca_interval, holm_adjust
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExtensionHypothesis,
    FamilySetName,
    HiddadStatus,
    Learner,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    RepresentationOutcome,
    SignTail,
)
from ctk_android.types import (
    Effect,
    FamilyCountsTable,
    FamilyName,
    MetVerdict,
    PlannedTargetsBySeed,
    RecallArm,
    RepresentationEffectRow,
    RepresentationLevelRow,
    RepresentationOf,
    RepresentationTable,
    RepresentationTables,
    RepresentationVerdictRow,
    SeedEffects,
    Table,
)


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


def _cell(
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
    priority = _cell(
        effects,
        Representation.MCNDROID_STATIC,
        RepresentationGroup.PRIORITY_MACRO,
        None,
    )
    lower = _low(priority)
    first: MetVerdict = None if lower is None else lower > margin
    focus = config.experiments.representation_focus_family
    hiddad = [
        _cell(effects, representation, RepresentationGroup.FAMILY, focus)
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
