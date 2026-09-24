import numpy as np
import polars as pl

from ctk_android import logs
from ctk_android.analysis import novelty
from ctk_android.analysis.decomposition import decompose, family_effects, family_seed_effects
from ctk_android.analysis.dose_response import dose_curve, dose_recall, effective_peer_dose
from ctk_android.analysis.fairness import frozen_drift, select_hyperparameters
from ctk_android.analysis.gates import evaluate_claims
from ctk_android.analysis.robustness import robustness_table
from ctk_android.analysis.statistics import cluster_bootstrap_difference, paired_effect_table
from ctk_android.config import Config
from ctk_android.data import partitions
from ctk_android.data.cache import read_record, records_to_frame, write_table
from ctk_android.enums import (
    AnalysisStage,
    Artifact,
    ClientId,
    Column,
    ErrorMessage,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    FailureReason,
    FamilyLabelSource,
    Learner,
    LibraryOption,
    LogEvent,
    LogField,
    ReportFigure,
    RunStatus,
    Separator,
    SplitRole,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.figures import build_figures
from ctk_android.reporting.promotion import promote
from ctk_android.reporting.records import collect_evidence
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
    FamilyEffectsTable,
    GateEvidence,
    GroupIds,
    HitVectors,
    Promote,
    PromotionDecision,
    RunEvidence,
    RunKey,
    RunManifest,
    SelectionTable,
)


def _associations(
    evidence: RunEvidence, family_table: FamilyEffectsTable, config: Config
) -> AssociationMap:
    result: AssociationMap = {}
    for experiment in (ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET):
        gains = family_table.filter(
            (pl.col(Column.EXPERIMENT) == experiment) & (pl.col(Column.LEARNER) == Learner.FEDAVG)
        ).select(Column.FAMILY, Column.CTK_GAIN)
        scores = novelty.descriptor_by_family(
            evidence.novelty.filter(pl.col(Column.EXPERIMENT) == experiment),
            config.experiments.novelty.primary_descriptor,
        )
        joined = gains.join(scores, on=Column.FAMILY)
        result[experiment] = novelty.novelty_association(
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
    write_table(evidence.index, paths.analysis_file(mode, Artifact.RUN_INDEX))
    write_table(evidence.summary, paths.analysis_file(mode, Artifact.ARM_METRICS))
    write_table(decomposition, paths.analysis_file(mode, Artifact.COLLABORATION_DECOMPOSITION))
    write_table(
        family_table.join(
            novelty.descriptor_by_family(
                evidence.novelty, config.experiments.novelty.primary_descriptor
            ),
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
