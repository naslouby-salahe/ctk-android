import polars as pl
from pydantic import ValidationError

from ctk_android.config import Config
from ctk_android.data import partitions, preparation
from ctk_android.data.cache import is_one_of, read_record
from ctk_android.enums import (
    Artifact,
    Column,
    CompletionState,
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
    CampaignStatus,
    CtkError,
    ExperimentSpec,
    ExperimentStatus,
    FamilyName,
    PairTables,
    PartitionKey,
    PlannedRun,
    PlannedTargets,
    RandomSeed,
    RunKey,
    RunState,
    RunStatusDocument,
    Salt,
    StatusCounts,
    TargetPair,
)


def run_state(paths: Paths, key: RunKey) -> RunState:
    status_file = paths.run_file(key, Artifact.STATUS)
    if not status_file.is_file():
        return RunState(key=key, status=RunStatus.INCOMPLETE, intact=True)
    try:
        status = read_record(status_file, RunStatusDocument).status
    except ValidationError:
        return RunState(key=key, status=RunStatus.INCOMPLETE, intact=False)
    required = (
        paths.run_file(key, Artifact.MANIFEST),
        paths.run_file(key, Artifact.VALIDATION),
        paths.provenance_file(paths.run_dir(key)),
        paths.run_metric_file(key, Artifact.SUMMARY),
    )
    intact = status is not RunStatus.COMPLETED or all(file.is_file() for file in required)
    return RunState(key=key, status=status, intact=intact)


def campaign_states(paths: Paths, config: Config) -> list[RunState]:
    return [
        run_state(paths, key)
        for experiment in config.experiments.experiments
        for key in config.campaign_keys(experiment)
    ]


def _counts(states: list[RunState]) -> StatusCounts:
    sound = [state.status for state in states if state.intact]
    missing = sound.count(RunStatus.INCOMPLETE)
    failed = sound.count(RunStatus.FAILED_VALIDATION)
    infeasible = sound.count(RunStatus.INFEASIBLE)
    invalid = sum(not state.intact for state in states)
    if failed or infeasible or invalid:
        state = CompletionState.ATTENTION
    else:
        state = CompletionState.INCOMPLETE if missing else CompletionState.COMPLETE
    return StatusCounts(
        expected=len(states),
        completed=sound.count(RunStatus.COMPLETED),
        missing=missing,
        failed=failed,
        infeasible=infeasible,
        invalid=invalid,
        state=state,
    )


def campaign_status(paths: Paths, config: Config) -> CampaignStatus:
    states = campaign_states(paths, config)
    experiments = [
        ExperimentStatus(
            experiment=experiment,
            modes=config.experiments.campaign_modes(experiment),
            counts=_counts([state for state in states if state.key.experiment == experiment]),
        )
        for experiment in config.experiments.experiments
        if config.experiments.campaign_modes(experiment)
    ]
    return CampaignStatus(experiments=tuple(experiments), total=_counts(states))


def set_members(
    paths: Paths, config: Config, spec: ExperimentSpec, mode: ExecutionMode
) -> tuple[FamilyName, ...]:
    members = preparation.read_family_set(paths, spec.family_set)
    if mode is ExecutionMode.SMOKE:
        return members[: config.data.smoke_family_set_size]
    return members


def _pair_tables(
    paths: Paths, config: Config, spec: ExperimentSpec, key: PartitionKey
) -> PairTables:
    if spec.representation is not None:
        return PairTables(
            controlled=pl.read_parquet(
                paths.representation_partition_file(key, Artifact.CONTROLLED_PAIRS)
            ),
            natural=pl.read_parquet(
                paths.representation_partition_file(key, Artifact.NATURAL_PAIRS)
            ),
        )
    if spec.family_set in preparation.large_family_sets():
        return PairTables(
            controlled=pl.read_parquet(paths.partition_file(key, Artifact.LARGE_CONTROLLED_PAIRS)),
            natural=pl.read_parquet(paths.partition_file(key, Artifact.LARGE_NATURAL_PAIRS)),
        )
    if spec.family_labels is FamilyLabelSource.OBSERVED:
        return PairTables(
            controlled=pl.read_parquet(paths.partition_file(key, Artifact.CONTROLLED_PAIRS)),
            natural=pl.read_parquet(paths.partition_file(key, Artifact.NATURAL_PAIRS)),
        )
    study = partitions.load_study(
        paths, key, config.data, spec.family_labels, config.experiments.permutation_seed_offset
    )
    universe = (
        *preparation.read_family_set(paths, FamilySetName.PRIMARY),
        *preparation.read_family_set(paths, FamilySetName.REPLICATION),
    )
    return partitions.evaluate_partition(
        study.table, study.table[Column.ROLE], universe, config.data, key
    )


def plan_run(
    paths: Paths,
    config: Config,
    name: ExperimentName,
    mode: ExecutionMode,
    seed: RandomSeed,
    salt: Salt,
) -> PlannedRun:
    spec = config.experiments.experiments[name]
    key = PartitionKey(seed=seed, salt=salt, grouping=spec.grouping, profile=spec.eligibility)
    run_key = RunKey(mode=mode, experiment=name, seed=seed, salt=salt)
    members = set_members(paths, config, spec, mode)
    pair_tables = _pair_tables(paths, config, spec, key)
    if spec.exposure_mode is ExposureMode.HIDE_FROM_TARGET:
        chosen = preparation.assign_targets(
            pair_tables.controlled.filter(is_one_of(Column.FAMILY, members)),
            seed,
            members,
            config.data.eligibility[spec.eligibility],
        )
        targets = tuple(chosen)
    else:
        eligible = pair_tables.natural.filter(
            pl.col(Column.ELIGIBLE) & is_one_of(Column.FAMILY, members)
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


def planned_targets(paths: Paths, key: RunKey) -> PlannedTargets:
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
    return PlannedTargets(status=RunStatus(matrix[Column.STATUS][0]), targets=targets)
