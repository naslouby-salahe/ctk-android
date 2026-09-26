import numpy as np
import polars as pl

from ctk_android import logs
from ctk_android.analysis.decomposition import (
    decompose,
    dose_curve,
    dose_recall,
    effective_peer_dose,
    family_effects,
    family_seed_effects,
)
from ctk_android.analysis.diagnostic_synthesis import (
    influence_tables,
    synthesis_cells,
    synthesis_diagnostics,
    synthesis_experiments,
)
from ctk_android.analysis.diagnostics import (
    control_cells,
    control_diagnostics,
    dose_diagnostics,
    equal_fpr_effects,
    labelled,
    score_health,
    scored_targets,
)
from ctk_android.analysis.extensions import (
    controls_effects,
    controls_experiments,
    controls_verdicts,
    descriptor_by_family,
    dose_consistency,
    dose_effects,
    dose_experiments,
    dose_family_curves,
    dose_verdicts,
    eligibility_stability_summary,
    eligibility_stability_table,
    eligibility_table,
    large_family_summary,
    large_family_table,
    large_seed_effects,
    novelty_association,
    placebo_table,
    representation_experiments,
    representation_tables,
    representation_verdicts,
    stability_seed_table,
)
from ctk_android.analysis.post_confirmatory import (
    aggregate_metric_masking,
    anchored_client_selection,
    anchored_worst_client,
    client_ctk_analysis,
    ctk_heterogeneity_components,
    ctk_robustness_synthesis,
    ctk_variance_components,
    evaluate_claims,
    family_associations,
    family_client_ctk,
    family_mechanism_patterns,
    federated_arm_tradeoff,
    frozen_drift,
    hidden_cells,
    mechanism_headroom,
    natural_scarcity_comparison,
    negative_transfer_decomposition,
    operating_point_fidelity,
    permutation_control_audit,
    robustness_table,
    select_hyperparameters,
)
from ctk_android.analysis.statistics import cluster_bootstrap_difference, paired_effect_table
from ctk_android.config import Config
from ctk_android.data import partitions
from ctk_android.data.cache import read_record, records_to_frame, write_table
from ctk_android.data.preparation import read_family_set
from ctk_android.enums import (
    AnalysisStage,
    Artifact,
    ClientId,
    Column,
    ErrorMessage,
    EvidenceClass,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExtensionStudy,
    FailureReason,
    FamilyLabelSource,
    FamilySetName,
    Learner,
    LibraryOption,
    LogEvent,
    LogField,
    ReportFigure,
    ReportTable,
    ResultsFile,
    RunStatus,
    Separator,
    SplitRole,
    Stage,
)
from ctk_android.experiment.planning import planned_targets
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import (
    collect_evidence,
    collect_placebo_pairs,
    promote,
    promote_diagnostics,
    promote_extension_design,
    promote_hidden_family,
    promote_large_family,
)
from ctk_android.reporting.figures import build_figures
from ctk_android.reporting.tables import build_tables
from ctk_android.types import (
    Alpha,
    ArmKey,
    AssociationMap,
    AssociationRow,
    ClaimsTable,
    ClusterRow,
    ClusterTable,
    CtkError,
    DesignPromotion,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    FamilyEffectsTable,
    GateEvidence,
    GroupIds,
    HitVectors,
    PartitionKey,
    PlannedTargetsBySeed,
    Promote,
    PromotedOutput,
    PromotionDecision,
    RepresentationDiagnostics,
    RunEvidence,
    RunIndexTable,
    RunKey,
    RunManifest,
    ScoredRun,
    SeedPairsTables,
    SelectionTable,
    StudyCache,
    StudyTable,
    SupportCount,
    TargetsTable,
)


def _associations(
    evidence: RunEvidence, family_table: FamilyEffectsTable, config: Config
) -> AssociationMap:
    result: AssociationMap = {}
    for experiment in (ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET):
        gains = family_table.filter(
            (pl.col(Column.EXPERIMENT) == experiment) & (pl.col(Column.LEARNER) == Learner.FEDAVG)
        ).select(Column.FAMILY, Column.CTK_GAIN)
        scores = descriptor_by_family(
            evidence.novelty.filter(pl.col(Column.EXPERIMENT) == experiment),
            config.experiments.novelty.primary_descriptor,
        )
        joined = gains.join(scores, on=Column.FAMILY).sort(Column.FAMILY)
        result[experiment] = novelty_association(
            joined[Column.CTK_GAIN].to_numpy(), joined[Column.NOVELTY].to_numpy(), config.statistics
        )
    return result


def _cluster_row(paths: Paths, config: Config, key: RunKey, alpha: Alpha) -> ClusterRow | None:
    manifest = read_record(paths.run_file(key, Artifact.MANIFEST), RunManifest)
    study = partitions.load_study(
        paths,
        manifest.partition,
        config.data,
        FamilyLabelSource.OBSERVED,
        config.experiments.permutation_seed_offset,
    )
    table = study.table
    roles, labels = table[Column.ROLE].to_numpy(), table[Column.LABEL].to_numpy()
    names, components = table[Column.FAMILY].to_numpy(), table[Column.COMPONENT].to_numpy()
    thresholds = pl.read_parquet(paths.run_file(key, Artifact.THRESHOLDS)).filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & (pl.col(Column.ALPHA) == alpha)
        & pl.col(Column.DOSE).is_null()
    )
    hits: HitVectors = {
        ExposureCondition.PEER_PRESENT: [],
        ExposureCondition.FAMILY_ABSENT_EVERYWHERE: [],
    }
    groups: list[GroupIds] = []
    for condition, collected in hits.items():
        arm = ArmKey(learner=Learner.FEDAVG, condition=condition, dose=None)
        scored = pl.read_parquet(paths.run_scores_file(key, arm))
        for client in ClientId:
            families = [pair.family for pair in manifest.targets if pair.client is client]
            own = scored.filter(pl.col(Column.TARGET_CLIENT) == client)
            pool = own[Column.ROW].to_numpy()
            unseen = (
                (roles[pool] == SplitRole.TEST)
                & (labels[pool] == 1)
                & np.isin(names[pool], families)
            )
            threshold = thresholds.filter(
                (pl.col(Column.CLIENT) == client) & (pl.col(Column.CONDITION) == condition)
            )[Column.THRESHOLD].item()
            collected.append((own[Column.SCORE].to_numpy()[unseen] > threshold).astype(np.int64))
            if condition is ExposureCondition.PEER_PRESENT:
                groups.append(components[pool][unseen].astype(np.int64))
    peer = np.concatenate(hits[ExposureCondition.PEER_PRESENT])
    absent = np.concatenate(hits[ExposureCondition.FAMILY_ABSENT_EVERYWHERE])
    group_ids = np.unique(np.concatenate(groups), return_inverse=True)[1].reshape(-1)
    interval = cluster_bootstrap_difference(
        peer,
        absent,
        np.ones(peer.size, dtype=np.int64),
        group_ids,
        config.statistics.cluster_bootstrap_resamples,
        config.statistics.statistics_seed,
        config.statistics.confidence_level,
    )
    if interval is None:
        return None
    return ClusterRow(
        experiment=key.experiment,
        seed=key.seed,
        salt=key.salt,
        ci_low=interval.low,
        ci_high=interval.high,
    )


def _cluster_intervals(
    paths: Paths, config: Config, mode: ExecutionMode, evidence: RunEvidence
) -> ClusterTable:
    alpha = config.experiments.operating.primary_alpha
    completed = evidence.index.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.STATUS) == RunStatus.COMPLETED)
    )
    rows = [
        _cluster_row(
            paths,
            config,
            RunKey(
                mode=mode,
                experiment=record[Column.EXPERIMENT],
                seed=record[Column.SEED],
                salt=record[Column.SALT],
            ),
            alpha,
        )
        for record in completed.iter_rows(named=True)
    ]
    return records_to_frame([row for row in rows if row is not None])


def _stage_finished(stage: AnalysisStage, watch: Stopwatch) -> None:
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: stage, LogField.SECONDS: watch.seconds()},
    )


def run_analysis(paths: Paths, config: Config, mode: ExecutionMode) -> ClaimsTable:
    evidence = collect_evidence(paths, config, mode, fairness=False)
    logs.info(
        LogEvent.EVIDENCE_COLLECTED,
        {
            LogField.MODE: mode,
            LogField.RUNS: evidence.index.height,
            LogField.COMPLETED: evidence.index.filter(
                pl.col(Column.STATUS) == RunStatus.COMPLETED
            ).height,
            LogField.FAILED: evidence.index.filter(
                pl.col(Column.STATUS) == RunStatus.FAILED_VALIDATION
            ).height,
        },
    )
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    alpha = config.experiments.operating.primary_alpha
    watch = Stopwatch()
    decomposition = decompose(evidence.summary)
    _stage_finished(AnalysisStage.DECOMPOSITION, watch)
    watch = Stopwatch()
    effects = paired_effect_table(decomposition, config)
    _stage_finished(AnalysisStage.STATISTICS, watch)
    watch = Stopwatch()
    family_seed = family_seed_effects(evidence.families, alpha)
    family_table = family_effects(family_seed)
    _stage_finished(AnalysisStage.FAMILY_EFFECTS, watch)
    watch = Stopwatch()
    dose_runs = evidence.families.filter(
        pl.col(Column.EXPERIMENT) == ExperimentName.PEER_DOSE_RESPONSE
    )
    dose = dose_curve(
        dose_recall(dose_runs, alpha),
        effective_peer_dose(
            evidence.exposure.filter(
                pl.col(Column.EXPERIMENT) == ExperimentName.PEER_DOSE_RESPONSE
            ),
            dose_runs.select(
                Column.EXPERIMENT, Column.SEED, Column.SALT, Column.CLIENT, Column.FAMILY
            ).unique(),
        ),
    )
    _stage_finished(AnalysisStage.DOSE_RESPONSE, watch)
    watch = Stopwatch()
    associations = _associations(evidence, family_table, config)
    _stage_finished(AnalysisStage.NOVELTY, watch)
    watch = Stopwatch()
    robustness = robustness_table(evidence.families, config)
    _stage_finished(AnalysisStage.ROBUSTNESS, watch)
    watch = Stopwatch()
    clusters = _cluster_intervals(paths, config, mode, evidence)
    _stage_finished(AnalysisStage.CLUSTER_BOOTSTRAP, watch)
    watch = Stopwatch()
    claims = evaluate_claims(
        GateEvidence(
            effects=effects,
            summary=evidence.summary,
            family_seed=family_seed,
            family_effects=family_table,
            dose=dose,
            associations=associations,
            failed_validation_runs=evidence.index.filter(
                pl.col(Column.STATUS) == RunStatus.FAILED_VALIDATION
            ).height,
        ),
        config,
    )
    _stage_finished(AnalysisStage.CLAIM_GATES, watch)
    for claim in claims.iter_rows(named=True):
        logs.info(
            LogEvent.CLAIM_EVALUATED,
            {
                LogField.CLAIM: claim[Column.CLAIM],
                LogField.STATUS: claim[Column.CLAIM_STATUS],
                LogField.SCOPES_PASSED: claim[Column.SCOPES_PASSED],
                LogField.SCOPES_TOTAL: claim[Column.SCOPES_TOTAL],
            },
        )
    watch = Stopwatch()
    write_table(
        anchored_worst_client(evidence.clients, config),
        paths.analysis_file(mode, Artifact.ANCHORED_WORST_CLIENT),
    )
    write_table(
        client_ctk_analysis(evidence.clients, evidence.families, config),
        paths.analysis_file(mode, Artifact.CLIENT_CTK),
    )
    write_table(
        family_client_ctk(evidence.families, config),
        paths.analysis_file(mode, Artifact.FAMILY_CLIENT_CTK),
    )
    write_table(
        ctk_variance_components(family_seed), paths.analysis_file(mode, Artifact.CTK_VARIANCE)
    )
    write_table(
        family_associations(family_table), paths.analysis_file(mode, Artifact.FAMILY_ASSOCIATIONS)
    )
    write_table(
        anchored_client_selection(evidence.clients, config),
        paths.analysis_file(mode, Artifact.ANCHORED_CLIENT_SELECTION),
    )
    write_table(
        federated_arm_tradeoff(evidence.summary, config),
        paths.analysis_file(mode, Artifact.ARM_TRADEOFF),
    )
    write_table(
        ctk_robustness_synthesis(effects, robustness, config),
        paths.analysis_file(mode, Artifact.ROBUSTNESS_SYNTHESIS),
    )
    write_table(
        family_mechanism_patterns(family_table), paths.analysis_file(mode, Artifact.FAMILY_PATTERNS)
    )
    write_table(
        natural_scarcity_comparison(effects, family_seed, config),
        paths.analysis_file(mode, Artifact.NATURAL_COMPARISON),
    )
    write_table(
        permutation_control_audit(effects, config),
        paths.analysis_file(mode, Artifact.PERMUTATION_AUDIT),
    )
    write_table(
        mechanism_headroom(evidence.summary, config),
        paths.analysis_file(mode, Artifact.MECHANISM_HEADROOM),
    )
    write_table(
        operating_point_fidelity(evidence.summary),
        paths.analysis_file(mode, Artifact.OPERATING_FIDELITY),
    )
    _stage_finished(AnalysisStage.POST_CONFIRMATORY, watch)
    write_table(evidence.index, paths.analysis_file(mode, Artifact.RUN_INDEX))
    write_table(evidence.summary, paths.analysis_file(mode, Artifact.ARM_METRICS))
    write_table(decomposition, paths.analysis_file(mode, Artifact.COLLABORATION_DECOMPOSITION))
    write_table(
        family_table.join(
            descriptor_by_family(evidence.novelty, config.experiments.novelty.primary_descriptor),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        ),
        paths.analysis_file(mode, Artifact.FAMILY_RESCUE),
    )
    write_table(dose, paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE))
    write_table(
        records_to_frame(
            [
                AssociationRow(
                    experiment=experiment,
                    rho=association.rho,
                    p_value=association.p_value,
                    ci_low=association.interval.low if association.interval else None,
                    ci_high=association.interval.high if association.interval else None,
                    families=association.families,
                )
                for experiment, association in associations.items()
                if association is not None
            ]
        ),
        paths.analysis_file(mode, Artifact.FEATURE_NOVELTY),
    )
    write_table(robustness, paths.analysis_file(mode, Artifact.ROBUSTNESS))
    write_table(effects, paths.statistics_file(mode, Artifact.PAIRED_EFFECTS))
    write_table(clusters, paths.statistics_file(mode, Artifact.CLUSTER_BOOTSTRAP))
    write_table(claims, paths.statistics_file(mode, Artifact.CLAIM_GATES))
    return claims


def run_report(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    watch = Stopwatch()
    run_analysis(paths, config, mode)
    run_fairness(paths, config, mode)
    tables = build_tables(paths, config, mode)
    for name, table in tables.items():
        target = paths.report_table_file(mode, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        table.write_csv(target)
    logs.info(LogEvent.TABLES_WRITTEN, {LogField.COUNT: len(tables)})
    directory = build_figures(paths, config, mode)
    logs.info(
        LogEvent.FIGURES_WRITTEN, {LogField.COUNT: len(ReportFigure), LogField.PATH: f"{directory}"}
    )
    decision = promote(paths, config, mode) if promote_evidence else None
    if decision is not None:
        report = logs.warning if decision.blocks else logs.info
        report(
            LogEvent.PROMOTION_DECIDED,
            {
                LogField.STATUS: decision.state,
                LogField.BLOCKS: len(decision.blocks),
                LogField.REASON: Separator.COMMA.join(decision.blocks),
            },
        )
    logs.info(LogEvent.REPORT_WRITTEN, {LogField.MODE: mode, LogField.SECONDS: watch.seconds()})
    return decision


def run_fairness(paths: Paths, config: Config, mode: ExecutionMode) -> SelectionTable | None:
    evidence = collect_evidence(paths, config, mode, fairness=True)
    if evidence.summary.height == 0:
        return None
    watch = Stopwatch()
    selection = select_hyperparameters(evidence.summary, config.experiments.operating.primary_alpha)
    for row in selection.filter(pl.col(Column.SELECTED)).iter_rows(named=True):
        logs.info(
            LogEvent.HYPERPARAMETER_SELECTED,
            {
                LogField.PARAMETER: row[Column.PARAMETER],
                LogField.VALUE: row[Column.TUNING_VALUE],
                LogField.CALIBRATION_AUROC: row[Column.CALIBRATION_AUROC],
                LogField.SECONDS: watch.seconds(),
            },
        )
    if selection.height == 0:
        logs.warning(LogEvent.FAIRNESS_UNAVAILABLE, {LogField.MODE: mode})
        return None
    for parameter in frozen_drift(selection, config.experiments.training):
        logs.warning(LogEvent.FREEZE_DRIFT, {LogField.PARAMETER: parameter})
    write_table(selection, paths.analysis_file(mode, Artifact.FAIRNESS_SELECTION))
    return selection


def run_posthoc(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    evidence = collect_evidence(paths, config, mode, fairness=False)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    cells = hidden_cells(evidence.families, config.experiments.operating.primary_alpha)
    write_table(
        ctk_heterogeneity_components(cells, config),
        paths.analysis_file(mode, Artifact.HETEROGENEITY_COMPONENTS),
    )
    write_table(
        aggregate_metric_masking(evidence.summary, config),
        paths.analysis_file(mode, Artifact.AGGREGATE_MASKING),
    )
    write_table(
        negative_transfer_decomposition(cells, config),
        paths.analysis_file(mode, Artifact.NEGATIVE_TRANSFER),
    )
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.HIDDEN_FAMILY, LogField.SECONDS: watch.seconds()},
    )
    return promote_hidden_family(paths, mode, evidence.index) if promote_evidence else None


def _planned_families(paths: Paths, config: Config, mode: ExecutionMode) -> SupportCount:
    return len(
        {
            pair.family
            for experiment in config.experiments.extension_b_experiments
            for seed in config.seeds_for(experiment, mode)
            for pair in planned_targets(
                paths, RunKey(mode=mode, experiment=experiment, seed=seed, salt=0)
            ).targets
        }
    )


def _fresh_seed_pairs(paths: Paths, config: Config, mode: ExecutionMode) -> SeedPairsTables:
    # Controlled pairs per fresh seed, as built by the partition stage for the frozen universe.
    pairs: SeedPairsTables = {}
    for experiment in config.experiments.extension_b_experiments:
        spec = config.experiments.experiments[experiment]
        for seed in config.seeds_for(experiment, mode):
            key = PartitionKey(seed=seed, salt=0, grouping=spec.grouping, profile=spec.eligibility)
            pairs[seed] = pl.read_parquet(
                paths.partition_file(key, Artifact.LARGE_CONTROLLED_PAIRS)
            )
    return pairs


def run_large_family(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    evidence = collect_evidence(
        paths, config, mode, fairness=False, only=config.experiments.extension_b_experiments
    )
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    seed_effects = large_seed_effects(evidence.families, config)
    table = large_family_table(seed_effects, evidence.novelty, config)
    write_table(evidence.index, paths.analysis_file(mode, Artifact.RUN_INDEX))
    write_table(seed_effects, paths.analysis_file(mode, Artifact.LARGE_FAMILY_SEED_CTK))
    write_table(table, paths.analysis_file(mode, Artifact.LARGE_FAMILY_CTK))
    write_table(
        large_family_summary(table, _planned_families(paths, config, mode), config, seed_effects),
        paths.analysis_file(mode, Artifact.LARGE_FAMILY_SUMMARY),
    )
    selection = pl.read_parquet(paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION))
    per_seed = stability_seed_table(_fresh_seed_pairs(paths, config, mode), selection)
    stability = eligibility_stability_table(per_seed, selection, seed_effects)
    write_table(per_seed, paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY_SEEDS))
    write_table(stability, paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY))
    write_table(
        eligibility_stability_summary(stability, table, config),
        paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY_SUMMARY),
    )
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.LARGE_FAMILY, LogField.SECONDS: watch.seconds()},
    )
    return promote_large_family(paths, config, mode) if promote_evidence else None


def run_dose_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = dose_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    effects = dose_effects(evidence.families, config, experiments)
    outputs = (
        (Artifact.DOSE_RUN_INDEX, evidence.index),
        (Artifact.DOSE_SEED_EFFECTS, effects.seeds),
        (Artifact.DOSE_EFFECTS, records_to_frame(list(effects.rows))),
        (Artifact.DOSE_FAMILY_CURVES, dose_family_curves(evidence.families, experiments)),
        (
            Artifact.DOSE_CONSISTENCY,
            dose_consistency(evidence.exposure, evidence.families, experiments),
        ),
        (Artifact.DOSE_VERDICTS, dose_verdicts(effects.rows, config)),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.DOSE_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.DOSE,
            experiments=experiments,
            index_artifact=Artifact.DOSE_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.DOSE_CODE,
        ),
    )


def run_controls_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = controls_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    effects = controls_effects(evidence.families, config, experiments)
    outputs = (
        (Artifact.CONTROLS_RUN_INDEX, evidence.index),
        (Artifact.CONTROLS_SEED_EFFECTS, effects.seeds),
        (Artifact.CONTROLS_EFFECTS, records_to_frame(list(effects.rows))),
        (
            Artifact.CONTROLS_PLACEBO_PAIRS,
            placebo_table(collect_placebo_pairs(paths, evidence.index, mode)),
        ),
        (Artifact.CONTROLS_VERDICTS, controls_verdicts(effects.rows, config)),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.CONTROLS_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.CONTROLS,
            experiments=experiments,
            index_artifact=Artifact.CONTROLS_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.CONTROLS_CODE,
        ),
    )


def run_representation_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = representation_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    reference = experiments[0]
    planned: PlannedTargetsBySeed = {
        seed: planned_targets(
            paths, RunKey(mode=mode, experiment=reference, seed=seed, salt=0)
        ).targets
        for seed in config.seeds_for(reference, mode)
    }
    tables = representation_tables(evidence.families, config, experiments)
    outputs = (
        (Artifact.REPRESENTATION_RUN_INDEX, evidence.index),
        (Artifact.REPRESENTATION_SEED_EFFECTS, tables.seeds),
        (Artifact.REPRESENTATION_EFFECTS, records_to_frame(list(tables.effects))),
        (Artifact.REPRESENTATION_LEVELS, records_to_frame(list(tables.levels))),
        (Artifact.REPRESENTATION_VERDICTS, representation_verdicts(tables.effects, config)),
        (
            Artifact.REPRESENTATION_ELIGIBILITY,
            eligibility_table(planned, read_family_set(paths, FamilySetName.PRIMARY)),
        ),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.REPRESENTATION_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.REPRESENTATION,
            experiments=experiments,
            index_artifact=Artifact.REPRESENTATION_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.REPRESENTATION_CODE,
        ),
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
