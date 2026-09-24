import polars as pl
import structlog

from ctk_android.config import Config, ExperimentSpec
from ctk_android.data import families, partitions
from ctk_android.data.cache import write_record, write_table
from ctk_android.enums import (
    Artifact,
    Column,
    ErrorMessage,
    ExecutionMode,
    ExperimentName,
    ExposureMode,
    FailureReason,
    FamilyLabelSource,
    FamilySetName,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    FamilyName,
    PartitionKey,
    PlannedRun,
    PlanSummary,
    RunKey,
    Seed,
    TargetPair,
)
from ctk_android.workflows.preprocess import read_family_set

log = structlog.get_logger()


def experiments_for(config: Config, mode: ExecutionMode) -> list[ExperimentName]:
    return [name for name, spec in config.experiments.experiments.items() if mode in spec.modes]


def set_members(
    paths: Paths, config: Config, spec: ExperimentSpec, mode: ExecutionMode
) -> tuple[FamilyName, ...]:
    members = read_family_set(paths, spec.family_set)
    if mode is ExecutionMode.SMOKE:
        return members[: config.data.smoke_family_set_size]
    return members


def _pair_tables(
    paths: Paths, config: Config, spec: ExperimentSpec, key: PartitionKey
) -> tuple[pl.DataFrame, pl.DataFrame]:
    if spec.family_labels is FamilyLabelSource.OBSERVED:
        return (
            pl.read_parquet(paths.partition_file(key, Artifact.CONTROLLED_PAIRS)),
            pl.read_parquet(paths.partition_file(key, Artifact.NATURAL_PAIRS)),
        )
    study = partitions.load_study(
        paths, key, config.data, spec.family_labels, config.experiments.permutation_seed_offset
    )
    universe = (
        *read_family_set(paths, FamilySetName.PRIMARY),
        *read_family_set(paths, FamilySetName.REPLICATION),
    )
    return partitions.evaluate_partition(
        study.table, study.table[Column.ROLE], universe, config.data, key
    )


def plan_run(
    paths: Paths, config: Config, name: ExperimentName, mode: ExecutionMode, seed: Seed, salt: Seed
) -> PlannedRun:
    spec = config.experiments.experiments[name]
    key = PartitionKey(seed=seed, salt=salt, grouping=spec.grouping, profile=spec.eligibility)
    run_key = RunKey(mode=mode, experiment=name, seed=seed, salt=salt)
    members = set_members(paths, config, spec, mode)
    controlled, natural = _pair_tables(paths, config, spec, key)
    if spec.exposure_mode is ExposureMode.HIDE_FROM_TARGET:
        chosen = families.assign_targets(
            controlled.filter(pl.col(Column.FAMILY).is_in(list(members))),
            seed,
            members,
            config.data.eligibility[spec.eligibility],
        )
        targets = tuple(TargetPair(client=client, family=family) for client, family in chosen)
    else:
        eligible = natural.filter(
            pl.col(Column.ELIGIBLE) & pl.col(Column.FAMILY).is_in(list(members))
        )
        targets = tuple(
            TargetPair(client=row[Column.CLIENT], family=row[Column.FAMILY])
            for row in eligible.iter_rows(named=True)
        )
    return PlannedRun(
        key=run_key,
        partition=key,
        targets=targets,
        status=RunStatus.COMPLETED if targets else RunStatus.INFEASIBLE,
        reason=None if targets else FailureReason.NO_ELIGIBLE_TARGETS,
    )


def run_plan(paths: Paths, config: Config, mode: ExecutionMode) -> list[PlannedRun]:
    planned = [
        plan_run(paths, config, name, mode, seed, salt)
        for name in experiments_for(config, mode)
        for seed in config.project.seeds.for_mode(mode)
        for salt in config.experiments.experiments[name].salts
    ]
    write_table(
        pl.DataFrame(
            [
                {
                    Column.EXPERIMENT: run.key.experiment,
                    Column.SEED: run.key.seed,
                    Column.SALT: run.key.salt,
                    Column.TARGET_CLIENT: len(run.targets),
                    Column.STATUS: run.status,
                    Column.REASON: run.reason,
                }
                for run in planned
            ]
        ),
        paths.plan_file(mode, Artifact.RUN_MATRIX),
    )
    write_table(
        pl.DataFrame(
            [
                {
                    Column.EXPERIMENT: run.key.experiment,
                    Column.SEED: run.key.seed,
                    Column.SALT: run.key.salt,
                    Column.CLIENT: pair.client,
                    Column.FAMILY: pair.family,
                }
                for run in planned
                for pair in run.targets
            ],
            schema={
                Column.EXPERIMENT: pl.String,
                Column.SEED: pl.Int64,
                Column.SALT: pl.Int64,
                Column.CLIENT: pl.String,
                Column.FAMILY: pl.String,
            },
        ),
        paths.plan_file(mode, Artifact.FAMILY_ASSIGNMENTS),
    )
    write_record(
        paths.plan_file(mode, Artifact.PLAN),
        PlanSummary(
            mode=mode,
            config_fingerprint=config.fingerprint(),
            runs=len(planned),
            infeasible=sum(run.status is RunStatus.INFEASIBLE for run in planned),
            seeds=config.project.seeds.for_mode(mode),
        ),
    )
    return planned


def planned_targets(paths: Paths, key: RunKey) -> tuple[RunStatus, tuple[TargetPair, ...]]:
    matrix_path = paths.plan_file(key.mode, Artifact.RUN_MATRIX)
    if not matrix_path.is_file():
        raise CtkError(
            FailureReason.NO_ELIGIBLE_TARGETS, ErrorMessage.PLAN_MISSING.format(mode=key.mode)
        )
    matrix = pl.read_parquet(matrix_path).filter(
        (pl.col(Column.EXPERIMENT) == key.experiment)
        & (pl.col(Column.SEED) == key.seed)
        & (pl.col(Column.SALT) == key.salt)
    )
    if matrix.height != 1:
        raise CtkError(
            FailureReason.NO_ELIGIBLE_TARGETS,
            ErrorMessage.RUN_NOT_PLANNED.format(
                experiment=key.experiment, seed=key.seed, mode=key.mode
            ),
        )
    assignments = pl.read_parquet(paths.plan_file(key.mode, Artifact.FAMILY_ASSIGNMENTS)).filter(
        (pl.col(Column.EXPERIMENT) == key.experiment)
        & (pl.col(Column.SEED) == key.seed)
        & (pl.col(Column.SALT) == key.salt)
    )
    targets = tuple(
        TargetPair(client=row[Column.CLIENT], family=row[Column.FAMILY])
        for row in assignments.iter_rows(named=True)
    )
    return RunStatus(matrix[Column.STATUS][0]), targets
