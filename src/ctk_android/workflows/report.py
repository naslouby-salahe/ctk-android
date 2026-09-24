import numpy as np
import polars as pl
import structlog

from ctk_android.analysis import novelty
from ctk_android.analysis.decomposition import decompose, family_effects, family_seed_effects
from ctk_android.analysis.dose_response import dose_curve, dose_recall, effective_peer_dose
from ctk_android.analysis.gates import evaluate_claims
from ctk_android.analysis.robustness import robustness_table
from ctk_android.analysis.statistics import cluster_bootstrap_difference, paired_effect_table
from ctk_android.config import Config
from ctk_android.data import partitions
from ctk_android.data.cache import read_record, records_to_frame, write_table
from ctk_android.enums import (
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
    RunStatus,
    SplitRole,
)
from ctk_android.paths import Paths
from ctk_android.reporting.figures import build_figures
from ctk_android.reporting.promotion import promote
from ctk_android.reporting.records import collect_evidence
from ctk_android.reporting.tables import build_tables
from ctk_android.types import (
    ArmKey,
    AssociationRow,
    ClusterRow,
    CtkError,
    GateEvidence,
    IntArray,
    NoveltyAssociation,
    PromotionDecision,
    RunEvidence,
    RunKey,
    RunManifest,
)

log = structlog.get_logger()


def _associations(
    evidence: RunEvidence, family_table: pl.DataFrame, config: Config
) -> dict[ExperimentName, NoveltyAssociation | None]:
    result: dict[ExperimentName, NoveltyAssociation | None] = {}
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


def _cluster_intervals(
    paths: Paths, config: Config, mode: ExecutionMode, evidence: RunEvidence
) -> pl.DataFrame:
    alpha = config.experiments.operating.primary_alpha
    rows: list[ClusterRow] = []
    completed = evidence.index.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.STATUS) == RunStatus.COMPLETED)
    )
    for record in completed.iter_rows(named=True):
        key = RunKey(
            mode=mode,
            experiment=record[Column.EXPERIMENT],
            seed=record[Column.SEED],
            salt=record[Column.SALT],
        )
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
            (pl.col(Column.LEARNER) == Learner.FEDAVG) & (pl.col(Column.ALPHA) == alpha)
        )
        hits: dict[ExposureCondition, list[IntArray]] = {
            ExposureCondition.PEER_PRESENT: [],
            ExposureCondition.FAMILY_ABSENT_EVERYWHERE: [],
        }
        groups: list[IntArray] = []
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
                threshold = thresholds.filter(pl.col(Column.CLIENT) == client)[
                    Column.THRESHOLD
                ].item()
                collected.append(
                    (own[Column.SCORE].to_numpy()[unseen] > threshold).astype(np.int64)
                )
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
        if interval is not None:
            rows.append(
                ClusterRow(
                    experiment=key.experiment,
                    seed=key.seed,
                    salt=key.salt,
                    ci_low=interval.low,
                    ci_high=interval.high,
                )
            )
    return records_to_frame(rows)


def run_analysis(paths: Paths, config: Config, mode: ExecutionMode) -> pl.DataFrame:
    evidence = collect_evidence(paths, config, mode)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    alpha = config.experiments.operating.primary_alpha
    decomposition = decompose(evidence.summary)
    effects = paired_effect_table(decomposition, config)
    family_seed = family_seed_effects(evidence.families, alpha)
    family_table = family_effects(family_seed)
    dose = dose_curve(
        dose_recall(
            evidence.families.filter(
                pl.col(Column.EXPERIMENT) == ExperimentName.PEER_DOSE_RESPONSE
            ),
            alpha,
        ),
        effective_peer_dose(
            evidence.exposure.filter(
                pl.col(Column.EXPERIMENT) == ExperimentName.PEER_DOSE_RESPONSE
            ),
            evidence.families.filter(pl.col(Column.EXPERIMENT) == ExperimentName.PEER_DOSE_RESPONSE)
            .select(Column.EXPERIMENT, Column.SEED, Column.SALT, Column.CLIENT, Column.FAMILY)
            .unique(),
        ),
    )
    associations = _associations(evidence, family_table, config)
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
    write_table(
        robustness_table(evidence.families, config), paths.analysis_file(mode, Artifact.ROBUSTNESS)
    )
    write_table(effects, paths.statistics_file(mode, Artifact.PAIRED_EFFECTS))
    write_table(
        _cluster_intervals(paths, config, mode, evidence),
        paths.statistics_file(mode, Artifact.CLUSTER_BOOTSTRAP),
    )
    write_table(claims, paths.statistics_file(mode, Artifact.CLAIM_GATES))
    log.info(LogEvent.REPORT_WRITTEN, mode=mode)
    return claims


def run_report(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: bool
) -> PromotionDecision | None:
    run_analysis(paths, config, mode)
    for name, table in build_tables(paths, config, mode).items():
        target = paths.report_table_file(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        table.write_csv(target)
    build_figures(paths, config, mode)
    return promote(paths, config, mode) if promote_evidence else None
