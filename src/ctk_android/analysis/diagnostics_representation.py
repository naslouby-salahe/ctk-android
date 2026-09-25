import numpy as np
import polars as pl
from sklearn.metrics import roc_curve

from ctk_android.analysis.diagnostics_statistics import interval_high, interval_low, labelled
from ctk_android.analysis.statistics import bca_interval
from ctk_android.config import Config
from ctk_android.enums import (
    Column,
    DiagnosticColumn,
    EvaluationPopulation,
    EvidenceClass,
    ExposureCondition,
    Learner,
    NameFragment,
    OperatingReading,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    ScoreMagnitude,
    SplitRole,
)
from ctk_android.types import (
    Alpha,
    ArmKey,
    ArmName,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    Effect,
    ScoredRun,
)


def equal_fpr_arms() -> tuple[ArmKey, ...]:
    return (
        ArmKey(learner=Learner.CENTRAL, condition=ExposureCondition.FULL_EXPOSURE, dose=None),
        ArmKey(learner=Learner.FEDAVG, condition=ExposureCondition.PEER_PRESENT, dose=None),
        ArmKey(
            learner=Learner.FEDAVG,
            condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE,
            dose=None,
        ),
    )


def arm_name(arm: ArmKey) -> ArmName:
    return f"{arm.learner}{NameFragment.ARM_SEPARATOR}{arm.condition}"


def recall_at_fpr(negatives: DiagnosticVector, positives: DiagnosticVector, fpr: Alpha) -> Effect:
    # Empirical ROC over the target's own-domain test benign rows and the hidden family's
    # federation-wide test rows; TPR is linearly interpolated at the requested FPR.
    truth = np.r_[np.zeros(negatives.size), np.ones(positives.size)]
    false_rate, true_rate, _ = roc_curve(
        truth, np.r_[negatives, positives], drop_intermediate=False
    )
    return np.interp(fpr, false_rate, true_rate).item()


def _arm_filter(arm: ArmKey, client: pl.Expr) -> pl.Expr:
    return (
        (pl.col(Column.LEARNER) == arm.learner)
        & (pl.col(Column.CONDITION) == arm.condition)
        & (pl.col(Column.CLIENT) == client)
    )


def scored_targets(run: ScoredRun, config: Config) -> DiagnosticRows:
    alpha = config.experiments.operating.primary_alpha
    study = run.study
    label = study[Column.LABEL].to_numpy()
    client = study[Column.CLIENT].cast(pl.String).to_numpy()
    role = study[Column.ROLE].cast(pl.String).to_numpy()
    family = study[Column.FAMILY].to_numpy()
    at_alpha = (pl.col(Column.ALPHA) == alpha) & pl.col(Column.DOSE).is_null()
    thresholds = run.thresholds.filter(at_alpha)
    families = run.families.filter(
        at_alpha & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    )
    operating = run.operating.filter(at_alpha)
    rows: DiagnosticRows = []
    for arm in equal_fpr_arms():
        scores = run.scores[arm.label()]
        for target in run.targets:
            part = scores.filter(pl.col(Column.TARGET_CLIENT) == target.client)
            index = part[Column.ROW].to_numpy()
            values = part[Column.SCORE].to_numpy().astype(np.float64)
            test = role[index] == SplitRole.TEST
            negatives = values[test & (client[index] == target.client) & (label[index] == 0)]
            positives = values[test & (label[index] == 1) & (family[index] == target.family)]
            key = _arm_filter(arm, pl.lit(target.client))
            threshold = thresholds.filter(key)[Column.THRESHOLD].item()
            stored = families.filter(key & (pl.col(Column.FAMILY) == target.family)).row(
                0, named=True
            )
            trials = stored[Column.TRIALS]
            rows.append(
                {
                    Column.REPRESENTATION: run.representation,
                    Column.SEED: run.seed,
                    DiagnosticColumn.ARM: arm_name(arm),
                    Column.CLIENT: target.client,
                    Column.FAMILY: target.family,
                    DiagnosticColumn.BENIGN_TEST: negatives.size,
                    DiagnosticColumn.POSITIVE_TEST: positives.size,
                    Column.THRESHOLD: threshold,
                    DiagnosticColumn.CALIBRATED_RECALL: (positives > threshold).mean().item()
                    if positives.size
                    else np.nan,
                    DiagnosticColumn.CALIBRATED_FPR: (negatives > threshold).mean().item(),
                    DiagnosticColumn.EQUAL_FPR_RECALL: recall_at_fpr(negatives, positives, alpha)
                    if positives.size
                    else np.nan,
                    DiagnosticColumn.STORED_RECALL: stored[Column.HITS] / trials
                    if trials
                    else np.nan,
                    DiagnosticColumn.STORED_FPR: operating.filter(key)[Column.VALUE].item(),
                    DiagnosticColumn.STORED_TRIALS: trials,
                }
            )
    return rows


def score_health(run: ScoredRun) -> DiagnosticRows:
    rows: DiagnosticRows = []
    for name in sorted(run.scores):
        values = run.scores[name][Column.SCORE].to_numpy().astype(np.float64)
        magnitude = np.abs(values)
        rows.append(
            {
                Column.REPRESENTATION: run.representation,
                Column.SEED: run.seed,
                DiagnosticColumn.ARM: name,
                DiagnosticColumn.SCORES: values.size,
                DiagnosticColumn.NONFINITE: (~np.isfinite(values)).sum().item(),
                DiagnosticColumn.MINIMUM: np.nanmin(values).item(),
                DiagnosticColumn.MAXIMUM: np.nanmax(values).item(),
                DiagnosticColumn.ABOVE_LARGE: (magnitude > ScoreMagnitude.LARGE).sum().item(),
                DiagnosticColumn.ABOVE_EXTREME: (magnitude > ScoreMagnitude.EXTREME).sum().item(),
            }
        )
    return rows


def _groups(targets: DiagnosticTable, value: DiagnosticColumn, config: Config) -> DiagnosticTable:
    keys = [Column.REPRESENTATION, Column.SEED, DiagnosticColumn.ARM]
    experiments = config.experiments
    by_family = targets.group_by(*keys, Column.FAMILY, maintain_order=True).agg(
        pl.col(value).mean()
    )
    single = [
        *experiments.representation_priority_families,
        *experiments.representation_separate_families,
    ]
    parts = [
        by_family.filter(pl.col(Column.FAMILY).is_in(single)).rename({Column.FAMILY: Column.GROUP})
    ]
    for group, members in (
        (RepresentationGroup.PRIORITY_MACRO, experiments.representation_priority_families),
        (RepresentationGroup.CONTRAST_MACRO, experiments.representation_contrast_families),
    ):
        parts.append(
            by_family.filter(pl.col(Column.FAMILY).is_in(list(members)))
            .group_by(*keys, maintain_order=True)
            .agg(pl.col(value).mean())
            .with_columns(pl.lit(group).alias(Column.GROUP))
            .select(parts[0].columns)
        )
    return pl.concat(parts)


def _effect_rows(
    cells: DiagnosticTable, value: DiagnosticColumn, reading: OperatingReading, config: Config
) -> DiagnosticRows:
    keys = [Column.SEED, DiagnosticColumn.ARM, Column.GROUP]
    reference = cells.filter(pl.col(Column.REPRESENTATION) == Representation.LAMDA_STATIC).select(
        *keys, pl.col(value).alias(DiagnosticColumn.REFERENCE)
    )
    paired = cells.filter(pl.col(Column.REPRESENTATION) != Representation.LAMDA_STATIC).join(
        reference, on=keys
    )
    rows: DiagnosticRows = []
    for group in paired.sort(Column.SEED).partition_by(
        Column.REPRESENTATION, DiagnosticColumn.ARM, Column.GROUP, maintain_order=True
    ):
        head = group.row(0, named=True)
        differences = (group[value] - group[DiagnosticColumn.REFERENCE]).to_numpy()
        interval = bca_interval(differences, config.statistics)
        row: DiagnosticRow = {
            DiagnosticColumn.READING: reading,
            DiagnosticColumn.ARM: head[DiagnosticColumn.ARM],
            Column.GROUP: head[Column.GROUP],
            Column.REPRESENTATION: head[Column.REPRESENTATION],
            DiagnosticColumn.SEEDS: differences.size,
            Column.LEVEL: group[value].mean(),
            DiagnosticColumn.REFERENCE: group[DiagnosticColumn.REFERENCE].mean(),
            DiagnosticColumn.DIFF: differences.mean().item(),
            DiagnosticColumn.POSITIVE: (differences > 0).sum().item(),
            Column.CI_LOW: interval_low(interval),
            Column.CI_HIGH: interval_high(interval),
        }
        rows.append(row)
    return rows


def equal_fpr_effects(targets: DiagnosticTable, config: Config) -> DiagnosticTable:
    present, absent = (arm_name(arm) for arm in equal_fpr_arms()[1:])
    rows: DiagnosticRows = []
    for value, reading in (
        (DiagnosticColumn.CALIBRATED_RECALL, OperatingReading.CALIBRATED),
        (DiagnosticColumn.EQUAL_FPR_RECALL, OperatingReading.EQUAL_TEST_FPR),
    ):
        cells = _groups(targets, value, config)
        rows += _effect_rows(cells, value, reading, config)
        wide = cells.filter(pl.col(DiagnosticColumn.ARM).is_in([present, absent])).pivot(
            on=DiagnosticColumn.ARM,
            index=[Column.REPRESENTATION, Column.SEED, Column.GROUP],
            values=value,
        )
        ctk = wide.select(
            Column.REPRESENTATION,
            Column.SEED,
            Column.GROUP,
            (pl.col(present) - pl.col(absent)).alias(value),
        ).with_columns(pl.lit(RepresentationMeasure.CTK).alias(DiagnosticColumn.ARM))
        rows += _effect_rows(ctk, value, reading, config)
    return labelled(rows, EvidenceClass.POST_HOC_DIAGNOSTIC).sort(
        DiagnosticColumn.ARM, Column.GROUP, Column.REPRESENTATION, DiagnosticColumn.READING
    )
