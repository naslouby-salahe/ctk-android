import polars as pl

from ctk_android import logs
from ctk_android.analysis.controls_extension import controls_experiments
from ctk_android.analysis.diagnostics_controls import control_cells, control_diagnostics
from ctk_android.analysis.diagnostics_dose import dose_diagnostics
from ctk_android.analysis.diagnostics_influence import influence_tables
from ctk_android.analysis.diagnostics_representation import (
    equal_fpr_effects,
    score_health,
    scored_targets,
)
from ctk_android.analysis.diagnostics_statistics import labelled
from ctk_android.analysis.diagnostics_synthesis import (
    synthesis_cells,
    synthesis_diagnostics,
    synthesis_experiments,
)
from ctk_android.analysis.dose_extension import dose_experiments
from ctk_android.analysis.representation_extension import representation_experiments
from ctk_android.config import Config
from ctk_android.data import partitions
from ctk_android.data.cache import read_record, write_table
from ctk_android.enums import (
    AnalysisStage,
    Artifact,
    Column,
    ErrorMessage,
    EvidenceClass,
    ExecutionMode,
    ExperimentName,
    ExtensionStudy,
    FailureReason,
    LogEvent,
    LogField,
    ReportTable,
    ResultsFile,
    RunStatus,
    Stage,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.promotion import promote_diagnostics
from ctk_android.reporting.records import collect_evidence, collect_placebo_pairs
from ctk_android.types import (
    CtkError,
    DesignPromotion,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    PartitionKey,
    Promote,
    PromotedOutput,
    PromotionDecision,
    RepresentationDiagnostics,
    RunIndexTable,
    RunKey,
    RunManifest,
    ScoredRun,
    StudyCache,
    StudyTable,
    TargetsTable,
)


def _study(
    paths: Paths, config: Config, experiment: ExperimentName, key: PartitionKey
) -> StudyTable:
    spec = config.experiments.experiments[experiment]
    return partitions.study_table(
        pl.read_parquet(paths.representation_file(Artifact.OVERLAP)),
        pl.read_parquet(paths.representation_file(Artifact.COMPONENTS)),
        pl.read_parquet(paths.representation_partition_file(key, Artifact.ASSIGNMENTS)),
        key,
        config.data,
        spec.family_labels,
        config.experiments.permutation_seed_offset,
    )


def _representation(
    paths: Paths, config: Config, mode: ExecutionMode, experiments: tuple[ExperimentName, ...]
) -> RepresentationDiagnostics:
    # Re-reads the stored per-row test scores of every representation run; no retraining.
    studies: StudyCache = {}
    targets: DiagnosticRows = []
    health: DiagnosticRows = []
    for experiment in experiments:
        spec = config.experiments.experiments[experiment]
        representation = spec.representation
        if representation is None:
            continue
        for seed in config.seeds_for(experiment, mode):
            key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=0)
            partition = PartitionKey(
                seed=seed, salt=0, grouping=spec.grouping, profile=spec.eligibility
            )
            if partition not in studies:
                studies[partition] = _study(paths, config, experiment, partition)
            manifest = read_record(paths.run_file(key, Artifact.MANIFEST), RunManifest)
            run = ScoredRun(
                representation=representation,
                seed=seed,
                targets=manifest.targets,
                study=studies[partition],
                thresholds=pl.read_parquet(paths.run_file(key, Artifact.THRESHOLDS)),
                families=pl.read_parquet(paths.run_metric_file(key, Artifact.FAMILY_METRICS)),
                operating=pl.read_parquet(paths.run_metric_file(key, Artifact.OPERATING_POINTS)),
                scores={
                    arm.label(): pl.read_parquet(paths.run_scores_file(key, arm))
                    for arm in manifest.arms
                },
            )
            targets += scored_targets(run, config)
            health += score_health(run)
    evidence = EvidenceClass.POST_HOC_DIAGNOSTIC
    table = labelled(targets, evidence)
    return RepresentationDiagnostics(
        targets=table,
        health=labelled(health, evidence),
        effects=equal_fpr_effects(table, config),
    )


def _targets(paths: Paths, index: RunIndexTable) -> TargetsTable:
    rows: DiagnosticRows = []
    for row in index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED).iter_rows(named=True):
        key = RunKey(
            mode=ExecutionMode.CONFIRMATORY,
            experiment=row[Column.EXPERIMENT],
            seed=row[Column.SEED],
            salt=row[Column.SALT],
        )
        manifest = read_record(paths.run_file(key, Artifact.MANIFEST), RunManifest)
        for target in manifest.targets:
            pair: DiagnosticRow = {
                Column.EXPERIMENT: key.experiment,
                Column.SEED: key.seed,
                Column.CLIENT: target.client,
                Column.FAMILY: target.family,
            }
            rows.append(pair)
    return pl.DataFrame(rows)


def run_diagnostics(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    dose = dose_experiments(config, mode)
    controls = controls_experiments(config, mode)
    representation = representation_experiments(config, mode)
    experiments = (*config.experiments.extension_b_experiments, *dose, *controls, *representation)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0 or not (dose and controls and representation):
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    confirmatory = collect_evidence(
        paths, config, ExecutionMode.CONFIRMATORY, fairness=False, only=synthesis_experiments()
    )

    def only(frame: DiagnosticTable, names: tuple[ExperimentName, ...]) -> DiagnosticTable:
        return frame.filter(pl.col(Column.EXPERIMENT).is_in(list(names)))

    large = (
        pl.read_parquet(paths.analysis_file(mode, Artifact.LARGE_FAMILY_CTK)),
        pl.read_parquet(paths.analysis_file(mode, Artifact.LARGE_FAMILY_SEED_CTK)),
    )
    influence = influence_tables(
        large[0],
        large[1],
        pl.read_parquet(paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY)),
        config,
    )
    doses = dose_diagnostics(
        only(evidence.families, dose),
        only(evidence.novelty, dose),
        pl.read_csv(paths.report_table_file(ExecutionMode.CONFIRMATORY, ReportTable.FAMILY_LEVEL)),
        config,
        dose,
    )
    index = only(evidence.index, controls)
    control = control_diagnostics(
        control_cells(
            only(evidence.families, controls),
            only(evidence.exposure, controls),
            only(evidence.novelty, controls),
            collect_placebo_pairs(paths, index, mode),
            config,
            controls,
        ),
        config,
        controls,
    )
    reps = _representation(paths, config, mode, representation)
    synthesis = synthesis_diagnostics(
        synthesis_cells(
            confirmatory.families,
            confirmatory.exposure,
            confirmatory.novelty,
            _targets(paths, confirmatory.index),
            config,
        ),
        large[1],
        large[0],
        pl.read_parquet(paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION)),
        config,
    )
    diagnostic, confirmatory_class = (
        EvidenceClass.POST_HOC_DIAGNOSTIC,
        EvidenceClass.POST_CONFIRMATORY,
    )
    outputs = (
        (Artifact.DIAGNOSTIC_REP_TARGETS, reps.targets, diagnostic),
        (Artifact.DIAGNOSTIC_REP_HEALTH, reps.health, diagnostic),
        (Artifact.DIAGNOSTIC_REP_EFFECTS, reps.effects, diagnostic),
        (Artifact.DIAGNOSTIC_LFAM_INFLUENCE, influence.families, diagnostic),
        (Artifact.DIAGNOSTIC_LFAM_STABILITY, influence.summary, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_CURVE, doses.curve, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_INCREMENTS, doses.increments, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_FAMILY_CURVES, doses.family_curves, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_FAMILY_SUMMARY, doses.family_summary, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_ASSOCIATIONS, doses.associations, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_CLIENT_CURVES, doses.client_curves, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_MODEL_FITS, doses.model_fits, diagnostic),
        (Artifact.DIAGNOSTIC_DOSE_HETEROGENEITY, doses.heterogeneity, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_STRATA, control.strata, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_CLIENTS, control.clients, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_REALLOCATION, control.reallocation, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_SLOPES, control.slopes, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_ASSOCIATIONS, control.associations, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_PLACEBO_PAIRS, control.placebo_pairs, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_FAMILIES, control.families, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_SUPPORT_LEVELS, control.support_levels, diagnostic),
        (Artifact.DIAGNOSTIC_CTRL_SUPPORT, control.support, diagnostic),
        (Artifact.DIAGNOSTIC_SYNTH_CELLS, synthesis.cells, confirmatory_class),
        (Artifact.DIAGNOSTIC_SYNTH_TAXONOMY, synthesis.taxonomy, confirmatory_class),
        (Artifact.DIAGNOSTIC_SYNTH_FAMILY_CTK, synthesis.family_ctk, confirmatory_class),
        (Artifact.DIAGNOSTIC_SYNTH_LARGE_CTK, synthesis.large_family_ctk, diagnostic),
        (Artifact.DIAGNOSTIC_SYNTH_LARGE_TAXONOMY, synthesis.large_taxonomy, diagnostic),
        (Artifact.DIAGNOSTIC_SYNTH_RANK, synthesis.rank_concordance, diagnostic),
        (Artifact.DIAGNOSTIC_SYNTH_LARGE_ASSOCIATIONS, synthesis.large_associations, diagnostic),
    )
    write_table(evidence.index, paths.analysis_file(mode, Artifact.DIAGNOSTICS_RUN_INDEX))
    for artifact, table, _ in outputs:
        write_table(table, paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.DIAGNOSTICS, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_diagnostics(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.DIAGNOSTICS,
            experiments=experiments,
            index_artifact=Artifact.DIAGNOSTICS_RUN_INDEX,
            outputs=tuple(
                PromotedOutput(artifact=artifact, evidence_class=evidence_class)
                for artifact, _, evidence_class in outputs
            ),
            code_file=ResultsFile.DIAGNOSTICS_CODE,
        ),
    )
