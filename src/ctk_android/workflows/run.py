import platform
import sys
from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import polars as pl
import structlog
import torch

from ctk_android.config import Config, ExperimentSpec, TrainingConfig
from ctk_android.data import partitions
from ctk_android.data.cache import (
    combine_fingerprints,
    fingerprint_document,
    fingerprint_source_tree,
    is_reusable,
    write_json,
    write_provenance,
    write_table,
)
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExposureMode,
    FailureReason,
    Learner,
    LogEvent,
    OperatingPointStatus,
    RunStatus,
    SplitRole,
    Stage,
    ValidationCheck,
)
from ctk_android.experiment import evaluation, exposure, metrics, training
from ctk_android.experiment.models import resolve_device
from ctk_android.paths import Paths
from ctk_android.types import (
    ArmKey,
    ArmScores,
    CtkError,
    Directory,
    DoseRequest,
    Fingerprint,
    IntArray,
    PartitionKey,
    Provenance,
    RunKey,
    RunReport,
    Scorer,
    Seed,
    StudyData,
    TargetPair,
    TrainingRows,
    ValidationRecord,
)
from ctk_android.workflows.plan import planned_targets

log = structlog.get_logger()
STATUS_FILE = "status.json"
LOCAL_ARM = ArmKey(learner=Learner.LOCAL, condition=ExposureCondition.PEER_PRESENT, dose=None)
GLOBAL_LEARNERS = (Learner.CENTRAL, Learner.FEDAVG, Learner.FEDPROX, Learner.FEDAVG_FINETUNE, Learner.BLEND)
STREAM_BY_LEARNER = {learner: index + 1 for index, learner in enumerate(Learner)}


@dataclass(frozen=True)
class ArmResult:
    scores: ArmScores
    scorers: dict[ClientId, Scorer]


def training_config(config: Config, mode: ExecutionMode) -> TrainingConfig:
    if mode is ExecutionMode.SMOKE:
        return config.experiments.smoke_training
    return config.experiments.training


def settings_for(spec: ExperimentSpec, config: Config) -> list[tuple[ExposureCondition, DoseRequest]]:
    if spec.dose_sweep:
        doses: list[DoseRequest] = list(config.experiments.dose_levels)
        if config.experiments.dose_include_all_available:
            doses.append(None)
        return [(ExposureCondition.PEER_PRESENT, dose) for dose in doses]
    return [(condition, None) for condition in spec.conditions]


def run_provenance(paths: Paths, config: Config, key: RunKey, targets: tuple[TargetPair, ...]) -> Provenance:
    spec = config.experiments.experiments[key.experiment]
    partition_key = PartitionKey(
        seed=key.seed, salt=key.salt, grouping=spec.grouping, profile=spec.eligibility
    )
    document = {
        "key": key.model_dump(mode="json"),
        "partition": (paths.partition(partition_key) / "provenance.json").read_text(encoding="utf-8"),
        "config": config.fingerprint(),
        "targets": [pair.model_dump(mode="json") for pair in targets],
    }
    return Provenance(
        stage=Stage.RUN,
        inputs=fingerprint_document(document),
        code=fingerprint_source_tree(paths.root / "src" / "ctk_android"),
    )


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
    stream = STREAM_BY_LEARNER[learner]
    if learner is Learner.CENTRAL:
        scorer = training.train_scorer(context, training.pooled_rows(rows), config.central_epochs, stream)
        return ArmResult(evaluation.score_shared(scorer, study, pools), dict.fromkeys(ClientId, scorer))
    if learner in (Learner.FEDAVG, Learner.FEDPROX):
        scorer = training.train_federated(context, rows, learner, stream)
        return ArmResult(evaluation.score_shared(scorer, study, pools), dict.fromkeys(ClientId, scorer))
    if federated is None or federated.scorers is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, f"{learner} needs a federated model")
    if learner is Learner.FEDAVG_FINETUNE:
        tuned = {
            client: training.finetune(
                context, federated.scorers[client], rows[client], stream * 10 + index
            )
            for index, client in enumerate(ClientId)
        }
        return ArmResult(evaluation.score_per_client(tuned, study, pools), tuned)
    if local is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, "blend needs local models")
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
            context, rows[client], context.config.local_epochs, STREAM_BY_LEARNER[Learner.LOCAL] * 10 + index
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
        calibration_ok &= bool((own[calibration] & (labels[calibration] == 0)).all())
        unseen = np.zeros(rows.size, dtype=bool)
        for family in evaluation.target_families(targets, client):
            unseen |= attributes.masks[family][rows]
        hidden_test_only &= bool((roles[unseen] == SplitRole.TEST).all())
    return [
        ValidationRecord(
            check=ValidationCheck.THRESHOLD_FROM_BENIGN_CALIBRATION,
            passed=calibration_ok,
            detail="calibration rows are own-client benign calibration rows",
        ),
        ValidationRecord(
            check=ValidationCheck.HIDDEN_ROWS_IN_TEST_ONLY,
            passed=hidden_test_only,
            detail="evaluated hidden-family rows belong to the test partition",
        ),
    ]


def _operating_validation(
    summary: pl.DataFrame, config: Config
) -> ValidationRecord:
    fpr = summary.filter(
        (pl.col(Column.METRIC) == "realised-fpr")
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.VALID)
    )
    deviation = (
        (fpr[Column.VALUE] - config.experiments.operating.primary_alpha).abs().max()
        if fpr.height
        else None
    )
    tolerance = config.statistics.gates.operating_point_tolerance
    return ValidationRecord(
        check=ValidationCheck.OPERATING_POINT_REALISED,
        passed=deviation is not None and deviation <= tolerance,
        detail=f"max |realised FPR - alpha| = {deviation}",
    )


def _save_models(directory: Directory, arm: ArmKey, scorers: dict[ClientId, Scorer]) -> None:
    states = {
        client: scorer.network.state_dict()
        for client, scorer in scorers.items()
        if scorer.network is not None
    }
    if states:
        directory.mkdir(parents=True, exist_ok=True)
        torch.save(states, directory / f"{arm.label()}.pt")


def _environment(device: str) -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": version("numpy"),
        "polars": version("polars"),
        "scikit-learn": version("scikit-learn"),
        "device": device,
    }


def execute_run(paths: Paths, config: Config, key: RunKey, overwrite: bool) -> RunReport:
    directory = paths.run(key)
    planned_status, targets = planned_targets(paths, key)
    provenance = run_provenance(paths, config, key, targets)
    if not overwrite and is_reusable(directory, provenance):
        log.info(LogEvent.RUN_REUSED, experiment=key.experiment, seed=key.seed)
        return RunReport(key=key, status=RunStatus.COMPLETED, reused=True, directory=directory)
    if planned_status is RunStatus.INFEASIBLE:
        write_json(
            directory / STATUS_FILE,
            {"status": RunStatus.INFEASIBLE, "reason": FailureReason.NO_ELIGIBLE_TARGETS},
        )
        write_provenance(directory, provenance)
        return RunReport(key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory)
    log.info(LogEvent.RUN_STARTED, experiment=key.experiment, seed=key.seed, salt=key.salt)
    spec = config.experiments.experiments[key.experiment]
    train_config = training_config(config, key.mode)
    partition_key = PartitionKey(
        seed=key.seed, salt=key.salt, grouping=spec.grouping, profile=spec.eligibility
    )
    study = partitions.load_study(
        paths, partition_key, config.data, spec.family_labels, config.experiments.permutation_seed_offset
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
        seed=key.seed * 1000 + key.salt,
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
            orders, masks, exposure.exposure_spec(LOCAL_ARM, spec.exposure_mode, targets), {}, budget
        )
        local = _train_local(context, local_rows, study, pools)
        if Learner.LOCAL in spec.learners:
            results[LOCAL_ARM] = local
            trainings[LOCAL_ARM] = local_rows
    reported = tuple(learner for learner in GLOBAL_LEARNERS if learner in spec.learners)
    for condition, dose in settings_for(spec, config):
        base = ArmKey(learner=Learner.CENTRAL, condition=condition, dose=dose)
        exposure_spec = exposure.exposure_spec(base, spec.exposure_mode, targets)
        allowed = exposure.allowed_dose_rows(study, masks, exposure_spec, priorities)
        rows = exposure.select_training(orders, masks, exposure_spec, allowed, budget)
        federated: ArmResult | None = None
        for learner in GLOBAL_LEARNERS:
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
    discrimination = pl.concat([item.discrimination for item in evaluations if item.discrimination.height])
    rule = config.data.eligibility[spec.eligibility]
    summary = metrics.summarize(clients, family_table, discrimination, operating, rule.own_domain_min_test)

    exposure_table = pl.concat(
        [exposure.exposure_counts(study, trainings[arm], masks, arm) for arm in trainings]
    )
    validations = [
        *exposure.validate_exposure(
            study, trainings, masks, targets, spec.exposure_mode, rule.peer_min_fit, fit_pool
        ),
        *_pool_validations(attributes, pools, targets),
    ]
    validations.append(_operating_validation(summary, config))
    structural = [v for v in validations if v.check is not ValidationCheck.OPERATING_POINT_REALISED]
    status = RunStatus.COMPLETED if all(v.passed for v in structural) else RunStatus.FAILED_VALIDATION

    write_table(exposure_table, directory / "exposure.parquet")
    write_table(operating, directory / "thresholds.parquet")
    write_table(summary, directory / "metrics" / "summary.parquet")
    write_table(clients, directory / "metrics" / "clients.parquet")
    write_table(family_table, directory / "metrics" / "families.parquet")
    write_table(discrimination, directory / "metrics" / "discrimination.parquet")
    benign = clients.filter(pl.col(Column.POPULATION) == EvaluationPopulation.BENIGN)
    write_table(
        operating.join(
            benign.select(
                *metrics.ARM_COLUMNS, Column.CLIENT, Column.ALPHA, Column.HITS, Column.TRIALS
            ),
            on=[*metrics.ARM_COLUMNS, Column.CLIENT, Column.ALPHA],
        ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.VALUE)),
        directory / "metrics" / "operating-points.parquet",
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
            directory / "scores" / f"{arm.label()}.parquet",
        )
        _save_models(directory / "models", arm, result.scorers)
    write_json(
        directory / "validation.json",
        {"validations": [record.model_dump(mode="json") for record in validations]},
    )
    write_json(directory / STATUS_FILE, {"status": status, "reason": None})
    write_json(
        directory / "manifest.json",
        {
            "key": key.model_dump(mode="json"),
            "partition": partition_key.model_dump(mode="json"),
            "targets": [pair.model_dump(mode="json") for pair in targets],
            "arms": [arm.label() for arm in results],
            "budget": budget,
            "training": train_config.model_dump(mode="json"),
            "config_fingerprint": config.fingerprint(),
            "provenance": provenance.model_dump(mode="json"),
            "environment": _environment(str(device)),
            "status": status,
        },
    )
    write_provenance(directory, provenance)
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
        raise CtkError(FailureReason.NO_ELIGIBLE_TARGETS, f"{experiment} is not defined for {mode}")
    reports: list[RunReport] = []
    for seed in seeds:
        for salt in spec.salts:
            key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
            try:
                reports.append(execute_run(paths, config, key, overwrite))
            except CtkError as error:
                directory = paths.run(key)
                write_json(directory / STATUS_FILE, {"status": RunStatus.INFEASIBLE, "reason": error.reason})
                log.error(LogEvent.STAGE_FAILED, experiment=experiment, seed=seed, reason=error.reason)
                reports.append(
                    RunReport(key=key, status=RunStatus.INFEASIBLE, reused=False, directory=directory)
                )
    return reports


