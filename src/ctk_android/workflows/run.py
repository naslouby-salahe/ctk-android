import platform
import sys
from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import polars as pl
import torch

from ctk_android import logs
from ctk_android.analysis.novelty import family_descriptors
from ctk_android.config import Config, FairnessGrids
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
    LogField,
    Metric,
    OperatingPointStatus,
    RunStatus,
    SplitRole,
    TrackedPackage,
    TunedParameter,
    ValidationCheck,
)
from ctk_android.experiment import evaluation, exposure, metrics, training
from ctk_android.experiment.models import resolve_device
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import (
    ArmKey,
    ArmResult,
    ClientCountsTable,
    ClientPools,
    ClientScorers,
    CtkError,
    DiscriminationTable,
    DoseRequest,
    EnvironmentRecord,
    Epochs,
    ExperimentSpec,
    ExposureSetting,
    ExposureTable,
    FamilyCountsTable,
    FamilyMasks,
    File,
    LogFields,
    OperatingTable,
    Overwrite,
    PartitionKey,
    Priorities,
    Provenance,
    ProximalStrength,
    ResultsByArm,
    RowCount,
    RunKey,
    RunManifest,
    RunReport,
    RunStatusDocument,
    Seed,
    StudyData,
    SummaryTable,
    SupportCount,
    TargetPair,
    TrainingByArm,
    TrainingRows,
    TuningPoint,
    ValidationDocument,
    ValidationRecord,
)
from ctk_android.workflows.plan import planned_targets
from ctk_android.workflows.report import run_report


def local_arm() -> ArmKey:
    return ArmKey(learner=Learner.LOCAL, condition=ExposureCondition.PEER_PRESENT, dose=None)


def global_learners() -> list[Learner]:
    return [learner for learner in Learner if learner is not Learner.LOCAL]


def learner_stream(learner: Learner) -> Seed:
    return list(Learner).index(learner) + 1


def planned_arm_count(spec: ExperimentSpec, config: Config) -> RowCount:
    if spec.fairness_grid:
        grids = config.experiments.fairness_grids
        return 1 + len(grids.local_epochs) + len(grids.fedprox_mu) + len(grids.finetune_epochs)
    local = 1 if Learner.LOCAL in spec.learners else 0
    shared = sum(learner is not Learner.LOCAL for learner in spec.learners)
    return local + shared * len(settings_for(spec, config))


def _run_fields(key: RunKey) -> LogFields:
    return {
        LogField.EXPERIMENT: key.experiment,
        LogField.MODE: key.mode,
        LogField.SEED: key.seed,
        LogField.SALT: key.salt,
    }


def settings_for(spec: ExperimentSpec, config: Config) -> list[ExposureSetting]:
    if spec.fairness_grid:
        return []
    if spec.dose_sweep:
        doses: list[DoseRequest] = list(config.experiments.dose_levels)
        if config.experiments.dose_include_all_available:
            doses.append(None)
        return [
            ExposureSetting(condition=ExposureCondition.PEER_PRESENT, dose=dose) for dose in doses
        ]
    return [ExposureSetting(condition=condition, dose=None) for condition in spec.conditions]


def _federated_arm(
    context: training.TrainingContext,
    rows: TrainingRows,
    learner: Learner,
    strength: ProximalStrength,
    study: StudyData,
    pools: ClientPools,
) -> ArmResult:
    scorer = training.train_federated(context, rows, learner, strength, learner_stream(learner))
    return ArmResult(
        scores=evaluation.score_shared(scorer, study, pools),
        scorers=dict.fromkeys(ClientId, scorer),
    )


def _finetune_arm(
    context: training.TrainingContext,
    federated: ArmResult,
    rows: TrainingRows,
    epochs: Epochs,
    study: StudyData,
    pools: ClientPools,
) -> ArmResult:
    stream = learner_stream(Learner.FEDAVG_FINETUNE)
    tuned = {
        client: training.finetune(
            context,
            federated.scorers[client],
            rows[client],
            epochs,
            training.derive_seed(stream, index),
        )
        for index, client in enumerate(ClientId)
    }
    return ArmResult(scores=evaluation.score_per_client(tuned, study, pools), scorers=tuned)


def _train_learner(
    learner: Learner,
    context: training.TrainingContext,
    rows: TrainingRows,
    study: StudyData,
    pools: ClientPools,
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
            scores=evaluation.score_shared(scorer, study, pools),
            scorers=dict.fromkeys(ClientId, scorer),
        )
    if learner in (Learner.FEDAVG, Learner.FEDPROX):
        return _federated_arm(context, rows, learner, config.fedprox_mu, study, pools)
    if federated is None:
        raise CtkError(
            FailureReason.NOT_APPLICABLE_MODEL_FAMILY,
            ErrorMessage.NEEDS_FEDERATED.format(learner=learner),
        )
    if learner is Learner.FEDAVG_FINETUNE:
        return _finetune_arm(context, federated, rows, config.finetune_epochs, study, pools)
    if local is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.NEEDS_LOCAL)
    return ArmResult(
        scores=evaluation.blend_scores(local.scores, federated.scores, config.blend_weight),
        scorers={},
    )


def _train_local(
    context: training.TrainingContext,
    rows: TrainingRows,
    study: StudyData,
    pools: ClientPools,
    epochs: Epochs,
) -> ArmResult:
    scorers = {
        client: training.train_scorer(
            context,
            rows[client],
            epochs,
            training.derive_seed(learner_stream(Learner.LOCAL), index),
        )
        for index, client in enumerate(ClientId)
    }
    return ArmResult(scores=evaluation.score_per_client(scorers, study, pools), scorers=scorers)


def _log_arm(key: RunKey, arm: ArmKey, rows: TrainingRows, watch: Stopwatch) -> None:
    logs.info(
        LogEvent.ARM_TRAINED,
        {
            **_run_fields(key),
            LogField.ARM: arm.label(),
            LogField.TRAIN_ROWS: sum(chosen.size for chosen in rows.values()),
            LogField.SECONDS: watch.seconds(),
        },
    )


def _train_grid(
    context: training.TrainingContext,
    rows: TrainingRows,
    study: StudyData,
    pools: ClientPools,
    grids: FairnessGrids,
    key: RunKey,
) -> ResultsByArm:
    condition = ExposureCondition.PEER_PRESENT
    results: ResultsByArm = {}
    watch = Stopwatch()
    baseline = ArmKey(learner=Learner.FEDAVG, condition=condition, dose=None)
    federated = _federated_arm(context, rows, Learner.FEDAVG, 0.0, study, pools)
    results[baseline] = federated
    _log_arm(key, baseline, rows, watch)
    for epochs in grids.local_epochs:
        watch = Stopwatch()
        point = TuningPoint(parameter=TunedParameter.LOCAL_EPOCHS, level=epochs)
        arm = ArmKey(learner=Learner.LOCAL, condition=condition, dose=None, tuning=point)
        results[arm] = _train_local(context, rows, study, pools, epochs)
        _log_arm(key, arm, rows, watch)
    for strength in grids.fedprox_mu:
        watch = Stopwatch()
        point = TuningPoint(parameter=TunedParameter.FEDPROX_STRENGTH, level=strength)
        arm = ArmKey(learner=Learner.FEDPROX, condition=condition, dose=None, tuning=point)
        results[arm] = _federated_arm(context, rows, Learner.FEDPROX, strength, study, pools)
        _log_arm(key, arm, rows, watch)
    for epochs in grids.finetune_epochs:
        watch = Stopwatch()
        point = TuningPoint(parameter=TunedParameter.FINETUNE_EPOCHS, level=epochs)
        arm = ArmKey(learner=Learner.FEDAVG_FINETUNE, condition=condition, dose=None, tuning=point)
        results[arm] = _finetune_arm(context, federated, rows, epochs, study, pools)
        _log_arm(key, arm, rows, watch)
    return results


def _pool_validations(
    attributes: evaluation.RowAttributes,
    pools: ClientPools,
    evaluations: list[evaluation.ArmEvaluation],
) -> list[ValidationRecord]:
    calibration_ok = True
    for client, rows in pools.items():
        roles = attributes.roles[rows]
        own = attributes.clients[rows] == client
        calibration = roles == SplitRole.CALIBRATION
        calibration_ok &= own[calibration].all().item()
    hidden = np.concatenate([item.hidden_rows for item in evaluations])
    hidden_test_only = (attributes.roles[hidden] == SplitRole.TEST).all().item()
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


def _operating_validation(summary: SummaryTable, config: Config) -> ValidationRecord:
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


def _save_models(file: File, scorers: ClientScorers) -> None:
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


@dataclass(frozen=True)
class LocalArm:
    result: ArmResult
    rows: TrainingRows


@dataclass(frozen=True)
class TrainedArms:
    arms: ResultsByArm
    trainings: TrainingByArm


@dataclass(frozen=True)
class RunTables:
    operating: OperatingTable
    summary: SummaryTable
    clients: ClientCountsTable
    families: FamilyCountsTable
    discrimination: DiscriminationTable


def _run_local(
    spec: ExperimentSpec,
    key: RunKey,
    context: training.TrainingContext,
    study: StudyData,
    masks: FamilyMasks,
    pools: ClientPools,
    orders: TrainingRows,
    targets: tuple[TargetPair, ...],
    budget: SupportCount,
) -> LocalArm:
    local_rows = exposure.select_training(
        orders,
        masks,
        exposure.exposure_spec(local_arm(), spec.exposure_mode, targets),
        {},
        budget,
    )
    arm_watch = Stopwatch()
    local = _train_local(context, local_rows, study, pools, context.config.local_epochs)
    logs.info(
        LogEvent.ARM_TRAINED,
        {
            **_run_fields(key),
            LogField.ARM: local_arm().label(),
            LogField.TRAIN_ROWS: sum(rows.size for rows in local_rows.values()),
            LogField.SECONDS: arm_watch.seconds(),
        },
    )
    return LocalArm(result=local, rows=local_rows)


def _train_setting(
    spec: ExperimentSpec,
    key: RunKey,
    context: training.TrainingContext,
    study: StudyData,
    pools: ClientPools,
    setting: ExposureSetting,
    rows: TrainingRows,
    local: ArmResult | None,
) -> ResultsByArm:
    condition, dose = setting.condition, setting.dose
    reported = tuple(learner for learner in global_learners() if learner in spec.learners)
    results: ResultsByArm = {}
    federated: ArmResult | None = None
    for learner in global_learners():
        needed = learner in reported or (
            learner is Learner.FEDAVG and {Learner.FEDAVG_FINETUNE, Learner.BLEND} & set(reported)
        )
        if not needed:
            continue
        arm_watch = Stopwatch()
        result = _train_learner(learner, context, rows, study, pools, local, federated)
        if learner is Learner.FEDAVG:
            federated = result
        if learner in reported:
            arm = ArmKey(learner=learner, condition=condition, dose=dose)
            results[arm] = result
            logs.info(
                LogEvent.ARM_TRAINED,
                {
                    **_run_fields(key),
                    LogField.ARM: arm.label(),
                    LogField.TRAIN_ROWS: sum(chosen.size for chosen in rows.values()),
                    LogField.SECONDS: arm_watch.seconds(),
                },
            )
    return results


def _train_arms(
    spec: ExperimentSpec,
    config: Config,
    key: RunKey,
    context: training.TrainingContext,
    study: StudyData,
    masks: FamilyMasks,
    pools: ClientPools,
    orders: TrainingRows,
    priorities: Priorities,
    targets: tuple[TargetPair, ...],
    budget: SupportCount,
) -> TrainedArms:
    results: ResultsByArm = {}
    trainings: TrainingByArm = {}
    if spec.fairness_grid:
        grid_rows = exposure.select_training(
            orders,
            masks,
            exposure.exposure_spec(local_arm(), spec.exposure_mode, targets),
            {},
            budget,
        )
        results.update(
            _train_grid(context, grid_rows, study, pools, config.experiments.fairness_grids, key)
        )
        trainings.update(dict.fromkeys(results, grid_rows))
    local: ArmResult | None = None
    if not spec.fairness_grid and {Learner.LOCAL, Learner.BLEND} & set(spec.learners):
        trained_local = _run_local(spec, key, context, study, masks, pools, orders, targets, budget)
        local, local_rows = trained_local.result, trained_local.rows
        if Learner.LOCAL in spec.learners:
            results[local_arm()] = local
            trainings[local_arm()] = local_rows
    for setting in settings_for(spec, config):
        base = ArmKey(learner=Learner.CENTRAL, condition=setting.condition, dose=setting.dose)
        exposure_spec = exposure.exposure_spec(base, spec.exposure_mode, targets)
        allowed = exposure.allowed_dose_rows(study, masks, exposure_spec, priorities)
        rows = exposure.select_training(orders, masks, exposure_spec, allowed, budget)
        logs.info(
            LogEvent.EXPOSURE_SELECTED,
            {
                **_run_fields(key),
                LogField.CONDITION: setting.condition,
                LogField.DOSE: setting.dose,
                LogField.TRAIN_ROWS: sum(chosen.size for chosen in rows.values()),
            },
        )
        trained = _train_setting(spec, key, context, study, pools, setting, rows, local)
        results.update(trained)
        trainings.update(dict.fromkeys(trained, rows))
    return TrainedArms(arms=results, trainings=trainings)


def _write_tables(
    paths: Paths,
    key: RunKey,
    config: Config,
    study: StudyData,
    targets: tuple[TargetPair, ...],
    masks: FamilyMasks,
    pools: ClientPools,
    results: ResultsByArm,
    tables: RunTables,
    exposure_table: ExposureTable,
) -> None:
    operating, summary = tables.operating, tables.summary
    clients, family_table, discrimination = tables.clients, tables.families, tables.discrimination
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
            nulls_equal=True,
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


@dataclass(frozen=True)
class EvaluatedArms:
    evaluations: list[evaluation.ArmEvaluation]
    tables: RunTables


def _evaluate_arms(
    results: ResultsByArm,
    pools: ClientPools,
    attributes: evaluation.RowAttributes,
    targets: tuple[TargetPair, ...],
    config: Config,
    spec: ExperimentSpec,
) -> EvaluatedArms:
    evaluations = [
        evaluation.evaluate_arm(
            arm, result.scores, pools, attributes, targets, config.experiments.operating
        )
        for arm, result in results.items()
    ]
    operating = pl.concat([item.operating for item in evaluations])
    clients = pl.concat([item.clients for item in evaluations])
    families = pl.concat([item.families for item in evaluations if item.families.height])
    discrimination = pl.concat(
        [item.discrimination for item in evaluations if item.discrimination.height]
    )
    rule = config.data.eligibility[spec.eligibility]
    summary = metrics.summarize(
        clients, families, discrimination, operating, rule.own_domain_min_test
    )
    return EvaluatedArms(
        evaluations=evaluations,
        tables=RunTables(
            operating=operating,
            summary=summary,
            clients=clients,
            families=families,
            discrimination=discrimination,
        ),
    )


def _record_infeasible(paths: Paths, key: RunKey, provenance: Provenance) -> RunReport:
    directory = paths.run_dir(key)
    write_record(
        paths.run_file(key, Artifact.STATUS),
        RunStatusDocument(status=RunStatus.INFEASIBLE, reason=FailureReason.NO_ELIGIBLE_TARGETS),
    )
    logs.warning(
        LogEvent.RUN_INFEASIBLE,
        {**_run_fields(key), LogField.REASON: FailureReason.NO_ELIGIBLE_TARGETS},
    )
    write_provenance(paths.provenance_file(directory), provenance)
    return RunReport(key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory)


def _log_validations(
    key: RunKey, validations: list[ValidationRecord], summary: SummaryTable
) -> None:
    for record in validations:
        report = logs.info if record.passed else logs.warning
        report(
            LogEvent.VALIDATION_PASSED if record.passed else LogEvent.VALIDATION_FAILED,
            {
                **_run_fields(key),
                LogField.CHECK: record.check,
                LogField.DETAIL: record.detail,
            },
        )
    unresolved = summary.filter(
        pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.INSUFFICIENT_EVIDENCE
    )[Column.ALPHA].unique()
    for alpha in unresolved.to_list():
        logs.warning(
            LogEvent.OPERATING_POINT_UNRESOLVED, {**_run_fields(key), LogField.ALPHA: alpha}
        )


def execute_run(paths: Paths, config: Config, key: RunKey, overwrite: Overwrite) -> RunReport:
    directory = paths.run_dir(key)
    planned = planned_targets(paths, key)
    planned_status, targets = planned.status, planned.targets
    provenance = run_provenance(paths, config, key, targets)
    if not overwrite and is_reusable(paths.provenance_file(directory), provenance):
        logs.info(LogEvent.RUN_REUSED, _run_fields(key))
        return RunReport(key=key, status=RunStatus.COMPLETED, reused=True, directory=directory)
    if planned_status is RunStatus.INFEASIBLE:
        return _record_infeasible(paths, key, provenance)
    spec = config.experiments.experiments[key.experiment]
    train_config = config.training_for(key.mode)
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
    watch = Stopwatch()
    logs.info(
        LogEvent.RUN_STARTED,
        {
            **_run_fields(key),
            LogField.DEVICE: device,
            LogField.TARGETS: len(targets),
            LogField.BUDGET: budget,
            LogField.ARMS: planned_arm_count(spec, config),
        },
    )

    trained = _train_arms(
        spec, config, key, context, study, masks, pools, orders, priorities, targets, budget
    )
    results, trainings = trained.arms, trained.trainings
    fit_pool = orders

    evaluation_watch = Stopwatch()
    evaluated = _evaluate_arms(results, pools, attributes, targets, config, spec)
    evaluations, summary = evaluated.evaluations, evaluated.tables.summary
    rule = config.data.eligibility[spec.eligibility]

    logs.info(
        LogEvent.EVALUATION_FINISHED,
        {
            **_run_fields(key),
            LogField.ARMS: len(results),
            LogField.SECONDS: evaluation_watch.seconds(),
        },
    )
    exposure_table = pl.concat(
        [exposure.exposure_counts(trainings[arm], masks, arm) for arm in trainings]
    )
    validations = [
        *exposure.validate_exposure(
            study, trainings, masks, targets, spec.exposure_mode, rule.peer_min_fit, fit_pool
        ),
        *_pool_validations(attributes, pools, evaluations),
    ]
    validations.append(_operating_validation(summary, config))
    _log_validations(key, validations, summary)
    structural = [v for v in validations if v.check is not ValidationCheck.OPERATING_POINT_REALISED]
    status = (
        RunStatus.COMPLETED if all(v.passed for v in structural) else RunStatus.FAILED_VALIDATION
    )

    _write_tables(
        paths,
        key,
        config,
        study,
        targets,
        masks,
        pools,
        results,
        evaluated.tables,
        exposure_table,
    )
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
            config=config.run_fingerprint(spec, key.mode),
            provenance=provenance,
            environment=_environment(device),
            status=status,
        ),
    )
    write_provenance(paths.provenance_file(directory), provenance)
    logs.info(
        LogEvent.RUN_FINISHED,
        {
            **_run_fields(key),
            LogField.STATUS: status,
            LogField.ARMS: len(results),
            LogField.SECONDS: watch.seconds(),
        },
    )
    return RunReport(key=key, status=status, reused=False, directory=directory)


def run_experiment(
    paths: Paths,
    config: Config,
    experiment: ExperimentName,
    mode: ExecutionMode,
    seeds: tuple[Seed, ...],
    overwrite: Overwrite,
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
                logs.error(
                    LogEvent.RUN_INFEASIBLE,
                    {**_run_fields(key), LogField.REASON: error.reason, LogField.ERROR: f"{error}"},
                )
                reports.append(
                    RunReport(
                        key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory
                    )
                )
    return reports


def run_and_report(
    paths: Paths,
    config: Config,
    experiment: ExperimentName,
    mode: ExecutionMode,
    seeds: tuple[Seed, ...],
    overwrite: Overwrite,
) -> list[RunReport]:
    reports = run_experiment(paths, config, experiment, mode, seeds, overwrite)
    run_report(paths, config, mode, promote_evidence=False)
    return reports
