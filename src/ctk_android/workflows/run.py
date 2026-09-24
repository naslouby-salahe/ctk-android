import platform
import sys
from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import polars as pl
import structlog
import torch

from ctk_android.analysis.novelty import family_descriptors
from ctk_android.config import Config, ExperimentSpec, TrainingConfig
from ctk_android.data import partitions
from ctk_android.data.cache import (
    fingerprint_model,
    is_reusable,
    run_provenance,
    write_provenance,
    write_record,
    write_table,
)
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    DetailMessage,
    Device,
    ErrorMessage,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    FailureReason,
    Learner,
    LogEvent,
    Metric,
    OperatingPointStatus,
    RunStatus,
    SplitRole,
    TrackedPackage,
    ValidationCheck,
)
from ctk_android.experiment import evaluation, exposure, metrics, training
from ctk_android.experiment.models import resolve_device
from ctk_android.paths import Paths
from ctk_android.types import (
    ArmKey,
    ArmScores,
    CtkError,
    DoseRequest,
    EnvironmentRecord,
    File,
    IntArray,
    PartitionKey,
    RunKey,
    RunManifest,
    RunReport,
    RunStatusDocument,
    Scorer,
    Seed,
    StudyData,
    TargetPair,
    TrainingRows,
    ValidationDocument,
    ValidationRecord,
)
from ctk_android.workflows.plan import planned_targets

log = structlog.get_logger()


def local_arm() -> ArmKey:
    return ArmKey(learner=Learner.LOCAL, condition=ExposureCondition.PEER_PRESENT, dose=None)


def global_learners() -> list[Learner]:
    return [learner for learner in Learner if learner is not Learner.LOCAL]


def learner_stream(learner: Learner) -> Seed:
    return list(Learner).index(learner) + 1


@dataclass(frozen=True)
class ArmResult:
    scores: ArmScores
    scorers: dict[ClientId, Scorer]


def training_config(config: Config, mode: ExecutionMode) -> TrainingConfig:
    if mode is ExecutionMode.SMOKE:
        return config.experiments.smoke_training
    return config.experiments.training


def settings_for(
    spec: ExperimentSpec, config: Config
) -> list[tuple[ExposureCondition, DoseRequest]]:
    if spec.dose_sweep:
        doses: list[DoseRequest] = list(config.experiments.dose_levels)
        if config.experiments.dose_include_all_available:
            doses.append(None)
        return [(ExposureCondition.PEER_PRESENT, dose) for dose in doses]
    return [(condition, None) for condition in spec.conditions]


def _train_learner(
    learner: Learner,
    context: training.TrainingContext,
    rows: TrainingRows,
    study: StudyData,
    pools: dict[ClientId, IntArray],
    local: ArmResult | None,
    federated: ArmResult | None,
) -> ArmResult:
    config = context.config
    stream = learner_stream(learner)
    if learner is Learner.CENTRAL:
        scorer = training.train_scorer(
            context, training.pooled_rows(rows), config.central_epochs, stream
        )
        return ArmResult(
            evaluation.score_shared(scorer, study, pools), dict.fromkeys(ClientId, scorer)
        )
    if learner in (Learner.FEDAVG, Learner.FEDPROX):
        scorer = training.train_federated(context, rows, learner, stream)
        return ArmResult(
            evaluation.score_shared(scorer, study, pools), dict.fromkeys(ClientId, scorer)
        )
    if federated is None:
        raise CtkError(
            FailureReason.NOT_APPLICABLE_MODEL_FAMILY,
            ErrorMessage.NEEDS_FEDERATED.format(learner=learner),
        )
    if learner is Learner.FEDAVG_FINETUNE:
        tuned = {
            client: training.finetune(
                context,
                federated.scorers[client],
                rows[client],
                training.derive_seed(stream, index),
            )
            for index, client in enumerate(ClientId)
        }
        return ArmResult(evaluation.score_per_client(tuned, study, pools), tuned)
    if local is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.NEEDS_LOCAL)
    return ArmResult(
        evaluation.blend_scores(local.scores, federated.scores, config.blend_weight), {}
    )


def _train_local(
    context: training.TrainingContext,
    rows: TrainingRows,
    study: StudyData,
    pools: dict[ClientId, IntArray],
) -> ArmResult:
    scorers = {
        client: training.train_scorer(
            context,
            rows[client],
            context.config.local_epochs,
            training.derive_seed(learner_stream(Learner.LOCAL), index),
        )
        for index, client in enumerate(ClientId)
    }
    return ArmResult(evaluation.score_per_client(scorers, study, pools), scorers)


def _pool_validations(
    attributes: evaluation.RowAttributes,
    pools: dict[ClientId, IntArray],
    targets: tuple[TargetPair, ...],
) -> list[ValidationRecord]:
    calibration_ok = True
    hidden_test_only = True
    for client, rows in pools.items():
        roles = attributes.roles[rows]
        labels = attributes.labels[rows]
        own = attributes.clients[rows] == client
        calibration = roles == SplitRole.CALIBRATION
        calibration_ok &= (own[calibration] & (labels[calibration] == 0)).all().item()
        unseen = np.zeros(rows.size, dtype=bool)
        for family in evaluation.target_families(targets, client):
            unseen |= attributes.masks[family][rows]
        hidden_test_only &= (roles[unseen] == SplitRole.TEST).all().item()
    return [
        ValidationRecord(
            check=ValidationCheck.THRESHOLD_FROM_BENIGN_CALIBRATION,
            passed=calibration_ok,
            detail=DetailMessage.CALIBRATION_ROWS,
        ),
        ValidationRecord(
            check=ValidationCheck.HIDDEN_ROWS_IN_TEST_ONLY,
            passed=hidden_test_only,
            detail=DetailMessage.HIDDEN_TEST_ONLY,
        ),
    ]


def _operating_validation(summary: pl.DataFrame, config: Config) -> ValidationRecord:
    fpr = summary.filter(
        (pl.col(Column.METRIC) == Metric.REALISED_FPR)
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.VALID)
    )
    values = fpr[Column.VALUE].to_numpy()
    deviation = (
        np.abs(values - config.experiments.operating.primary_alpha).max() if values.size else None
    )
    tolerance = config.experiments.operating.realised_fpr_tolerance
    return ValidationRecord(
        check=ValidationCheck.OPERATING_POINT_REALISED,
        passed=deviation is not None and (deviation <= tolerance).item(),
        detail=DetailMessage.OPERATING_DEVIATION.format(deviation=deviation),
    )


def _save_models(file: File, scorers: dict[ClientId, Scorer]) -> None:
    states = {
        client: scorer.network.state_dict()
        for client, scorer in scorers.items()
        if scorer.network is not None
    }
    if states:
        file.parent.mkdir(parents=True, exist_ok=True)
        torch.save(states, file)


def _environment(device: Device) -> EnvironmentRecord:
    return EnvironmentRecord(
        python=sys.version.split()[0],
        platform=platform.platform(),
        torch=torch.__version__,
        numpy=version(TrackedPackage.NUMPY),
        polars=version(TrackedPackage.POLARS),
        scikit_learn=version(TrackedPackage.SCIKIT_LEARN),
        device=device,
    )


def execute_run(paths: Paths, config: Config, key: RunKey, overwrite: bool) -> RunReport:
    directory = paths.run_dir(key)
    planned_status, targets = planned_targets(paths, key)
    provenance = run_provenance(paths, config, key, targets)
    if not overwrite and is_reusable(paths.provenance_file(directory), provenance):
        log.info(LogEvent.RUN_REUSED, experiment=key.experiment, seed=key.seed)
        return RunReport(key=key, status=RunStatus.COMPLETED, reused=True, directory=directory)
    if planned_status is RunStatus.INFEASIBLE:
        write_record(
            paths.run_file(key, Artifact.STATUS),
            RunStatusDocument(
                status=RunStatus.INFEASIBLE, reason=FailureReason.NO_ELIGIBLE_TARGETS
            ),
        )
        write_provenance(paths.provenance_file(directory), provenance)
        return RunReport(key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory)
    log.info(LogEvent.RUN_STARTED, experiment=key.experiment, seed=key.seed, salt=key.salt)
    spec = config.experiments.experiments[key.experiment]
    train_config = training_config(config, key.mode)
    partition_key = PartitionKey(
        seed=key.seed, salt=key.salt, grouping=spec.grouping, profile=spec.eligibility
    )
    study = partitions.load_study(
        paths,
        partition_key,
        config.data,
        spec.family_labels,
        config.experiments.permutation_seed_offset,
    )
    families = tuple(dict.fromkeys(pair.family for pair in targets))
    masks = exposure.family_masks(study, families)
    attributes = evaluation.row_attributes(study, masks)
    pools = evaluation.build_pools(attributes, targets)
    device = resolve_device(config.project.device)
    context = training.TrainingContext(
        features=study.features,
        labels=attributes.labels,
        config=train_config,
        family=spec.model_family,
        device=device,
        seed=training.derive_seed(key.seed, key.salt),
    )
    orders = exposure.training_orders(study, key.seed, key.salt)
    priorities = exposure.row_priorities(study, key.seed, key.salt)
    budget = config.experiments.budgets[spec.budget]

    results: dict[ArmKey, ArmResult] = {}
    trainings: dict[ArmKey, TrainingRows] = {}
    fit_pool = orders
    need_local = Learner.LOCAL in spec.learners or Learner.BLEND in spec.learners
    local: ArmResult | None = None
    if need_local:
        local_rows = exposure.select_training(
            orders,
            masks,
            exposure.exposure_spec(local_arm(), spec.exposure_mode, targets),
            {},
            budget,
        )
        local = _train_local(context, local_rows, study, pools)
        if Learner.LOCAL in spec.learners:
            results[local_arm()] = local
            trainings[local_arm()] = local_rows
    reported = tuple(learner for learner in global_learners() if learner in spec.learners)
    for condition, dose in settings_for(spec, config):
        base = ArmKey(learner=Learner.CENTRAL, condition=condition, dose=dose)
        exposure_spec = exposure.exposure_spec(base, spec.exposure_mode, targets)
        allowed = exposure.allowed_dose_rows(study, masks, exposure_spec, priorities)
        rows = exposure.select_training(orders, masks, exposure_spec, allowed, budget)
        federated: ArmResult | None = None
        for learner in global_learners():
            needed = learner in reported or (
                learner is Learner.FEDAVG
                and {Learner.FEDAVG_FINETUNE, Learner.BLEND} & set(reported)
            )
            if not needed:
                continue
            result = _train_learner(learner, context, rows, study, pools, local, federated)
            if learner is Learner.FEDAVG:
                federated = result
            if learner in reported:
                arm = ArmKey(learner=learner, condition=condition, dose=dose)
                results[arm] = result
                trainings[arm] = rows
                log.info(LogEvent.ARM_TRAINED, arm=arm.label(), seed=key.seed)

    evaluations = [
        evaluation.evaluate_arm(
            arm, result.scores, pools, attributes, targets, config.experiments.operating
        )
        for arm, result in results.items()
    ]
    operating = pl.concat([item.operating for item in evaluations])
    clients = pl.concat([item.clients for item in evaluations])
    family_table = pl.concat([item.families for item in evaluations if item.families.height])
    discrimination = pl.concat(
        [item.discrimination for item in evaluations if item.discrimination.height]
    )
    rule = config.data.eligibility[spec.eligibility]
    summary = metrics.summarize(
        clients, family_table, discrimination, operating, rule.own_domain_min_test
    )

    exposure_table = pl.concat(
        [exposure.exposure_counts(trainings[arm], masks, arm) for arm in trainings]
    )
    validations = [
        *exposure.validate_exposure(
            study, trainings, masks, targets, spec.exposure_mode, rule.peer_min_fit, fit_pool
        ),
        *_pool_validations(attributes, pools, targets),
    ]
    validations.append(_operating_validation(summary, config))
    structural = [v for v in validations if v.check is not ValidationCheck.OPERATING_POINT_REALISED]
    status = (
        RunStatus.COMPLETED if all(v.passed for v in structural) else RunStatus.FAILED_VALIDATION
    )

    write_table(
        family_descriptors(study, targets, masks, config.experiments.novelty),
        paths.run_file(key, Artifact.NOVELTY),
    )
    write_table(exposure_table, paths.run_file(key, Artifact.EXPOSURE))
    write_table(operating, paths.run_file(key, Artifact.THRESHOLDS))
    write_table(summary, paths.run_metric_file(key, Artifact.SUMMARY))
    write_table(clients, paths.run_metric_file(key, Artifact.CLIENT_METRICS))
    write_table(family_table, paths.run_metric_file(key, Artifact.FAMILY_METRICS))
    write_table(discrimination, paths.run_metric_file(key, Artifact.DISCRIMINATION))
    benign = clients.filter(pl.col(Column.POPULATION) == EvaluationPopulation.BENIGN)
    write_table(
        operating.join(
            benign.select(
                *metrics.arm_columns(), Column.CLIENT, Column.ALPHA, Column.HITS, Column.TRIALS
            ),
            on=[*metrics.arm_columns(), Column.CLIENT, Column.ALPHA],
        ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.VALUE)),
        paths.run_metric_file(key, Artifact.OPERATING_POINTS),
    )
    for arm, result in results.items():
        write_table(
            pl.concat(
                [
                    pl.DataFrame(
                        {
                            Column.TARGET_CLIENT: [client] * pools[client].size,
                            Column.ROW: pools[client],
                            Column.SCORE: result.scores[client].astype(np.float32),
                        }
                    )
                    for client in ClientId
                ]
            ),
            paths.run_scores_file(key, arm),
        )
        _save_models(paths.run_models_file(key, arm), result.scorers)
    write_record(
        paths.run_file(key, Artifact.VALIDATION), ValidationDocument(validations=tuple(validations))
    )
    write_record(
        paths.run_file(key, Artifact.STATUS), RunStatusDocument(status=status, reason=None)
    )
    write_record(
        paths.run_file(key, Artifact.MANIFEST),
        RunManifest(
            key=key,
            partition=partition_key,
            targets=targets,
            arms=tuple(results),
            budget=budget,
            training=fingerprint_model(train_config),
            config=config.fingerprint(),
            provenance=provenance,
            environment=_environment(device),
            status=status,
        ),
    )
    write_provenance(paths.provenance_file(directory), provenance)
    log.info(LogEvent.RUN_FINISHED, experiment=key.experiment, seed=key.seed, status=status)
    return RunReport(key=key, status=status, reused=False, directory=directory)


def run_experiment(
    paths: Paths,
    config: Config,
    experiment: ExperimentName,
    mode: ExecutionMode,
    seeds: tuple[Seed, ...],
    overwrite: bool,
) -> list[RunReport]:
    spec = config.experiments.experiments[experiment]
    if mode not in spec.modes:
        raise CtkError(
            FailureReason.NO_ELIGIBLE_TARGETS,
            ErrorMessage.EXPERIMENT_MODE.format(experiment=experiment, mode=mode),
        )
    outside = [seed for seed in seeds if seed not in config.project.seeds.for_mode(mode)]
    if outside:
        raise CtkError(
            FailureReason.NO_ELIGIBLE_TARGETS,
            ErrorMessage.SEED_OUTSIDE_PLAN.format(seed=outside[0], mode=mode),
        )
    reports: list[RunReport] = []
    for seed in seeds:
        for salt in spec.salts:
            key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
            try:
                reports.append(execute_run(paths, config, key, overwrite))
            except CtkError as error:
                directory = paths.run_dir(key)
                write_record(
                    paths.run_file(key, Artifact.STATUS),
                    RunStatusDocument(status=RunStatus.INFEASIBLE, reason=error.reason),
                )
                log.error(
                    LogEvent.STAGE_FAILED, experiment=experiment, seed=seed, reason=error.reason
                )
                reports.append(
                    RunReport(
                        key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory
                    )
                )
    return reports
