import sys

import polars as pl
import torch

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data.cache import (
    read_record,
    records_to_frame,
    write_record,
    write_table,
)
from ctk_android.enums import (
    Artifact,
    Column,
    DetailMessage,
    Device,
    Display,
    DoctorCheck,
    ExecutionMode,
    LogEvent,
    LogField,
    PythonRequirement,
    RunStatus,
)
from ctk_android.experiment import planning
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.provenance import git_revision as repository_revision
from ctk_android.types import (
    DoctorResult,
    LogFields,
    PlannedRun,
    PlanSummary,
    RunKey,
    RunStatusDocument,
    StatusCountsTable,
    StatusRow,
)


def git_revision(paths: Paths) -> DoctorResult:
    revision = repository_revision(paths)
    return DoctorResult(
        check=DoctorCheck.GIT_REVISION,
        passed=revision != DetailMessage.NOT_A_CHECKOUT,
        detail=revision,
    )


def _raw_lamda(paths: Paths, config: Config) -> DoctorResult:
    files = paths.lamda_release_files(config.data.lamda_release)
    missing = [path for path in files if not path.is_file()]
    return DoctorResult(
        check=DoctorCheck.RAW_LAMDA,
        passed=not missing,
        detail=DetailMessage.FILE_COUNT.format(count=len(files), missing=len(missing)),
    )


def run_doctor(paths: Paths, config: Config) -> list[DoctorResult]:
    results = _checks(paths, config)
    for result in results:
        report = logs.info if result.passed else logs.warning
        report(
            LogEvent.DOCTOR_CHECKED,
            {
                LogField.CHECK: result.check,
                LogField.PASSED: result.passed,
                LogField.DETAIL: result.detail,
            },
        )
    return results


def _checks(paths: Paths, config: Config) -> list[DoctorResult]:
    archive = paths.androzoo_archive()
    device = Device.CUDA if torch.cuda.is_available() else Device.CPU
    return [
        DoctorResult(
            check=DoctorCheck.PYTHON_VERSION,
            passed=sys.version_info[:2] >= (PythonRequirement.MAJOR, PythonRequirement.MINOR),
            detail=sys.version.split()[0],
        ),
        DoctorResult(
            check=DoctorCheck.CONFIG_VALID,
            passed=True,
            detail=DetailMessage.CONFIG_FINGERPRINT.format(
                prefix=config.fingerprint()[: Display.FINGERPRINT_PREFIX]
            ),
        ),
        _raw_lamda(paths, config),
        DoctorResult(
            check=DoctorCheck.RAW_ANDROZOO,
            passed=archive.is_file(),
            detail=f"{archive}",
        ),
        DoctorResult(
            check=DoctorCheck.COMPUTE_DEVICE,
            passed=device is config.project.device or device is Device.CPU,
            detail=DetailMessage.DEVICE.format(available=device, configured=config.project.device),
        ),
        git_revision(paths),
    ]


def run_status(paths: Paths, mode: ExecutionMode) -> StatusCountsTable:
    matrix_path = paths.plan_file(mode, Artifact.RUN_MATRIX)
    if not matrix_path.is_file():
        logs.warning(LogEvent.STATUS_SUMMARIZED, {LogField.MODE: mode, LogField.RUNS: 0})
        return pl.DataFrame(schema={Column.EXPERIMENT: pl.String, Column.STATUS: pl.String})
    rows: list[StatusRow] = []
    for row in pl.read_parquet(matrix_path).iter_rows(named=True):
        key = RunKey(
            mode=mode,
            experiment=row[Column.EXPERIMENT],
            seed=row[Column.SEED],
            salt=row[Column.SALT],
        )
        status_path = paths.run_file(key, Artifact.STATUS)
        state = (
            read_record(status_path, RunStatusDocument).status
            if status_path.is_file()
            else RunStatus.INCOMPLETE
        )
        rows.append(StatusRow(experiment=key.experiment, status=state))
    summary = (
        records_to_frame(rows)
        .group_by(Column.EXPERIMENT, Column.STATUS)
        .agg(pl.len().alias(Column.ROWS))
        .sort(Column.EXPERIMENT, Column.STATUS)
    )
    logs.info(
        LogEvent.STATUS_SUMMARIZED,
        {
            LogField.MODE: mode,
            LogField.RUNS: len(rows),
            LogField.COMPLETED: sum(row.status is RunStatus.COMPLETED for row in rows),
        },
    )
    return summary


def run_plan(paths: Paths, config: Config, mode: ExecutionMode) -> list[PlannedRun]:
    watch = Stopwatch()
    planned = [
        planning.plan_run(paths, config, name, mode, seed, salt)
        for name in planning.experiments_for(config, mode)
        for seed in config.seeds_for(name, mode)
        for salt in config.experiments.experiments[name].salts
    ]
    for run in planned:
        fields: LogFields = {
            LogField.EXPERIMENT: run.key.experiment,
            LogField.SEED: run.key.seed,
            LogField.SALT: run.key.salt,
            LogField.TARGETS: len(run.targets),
        }
        if run.status is RunStatus.INFEASIBLE:
            logs.warning(LogEvent.RUN_PLANNED_INFEASIBLE, {**fields, LogField.REASON: run.reason})
        else:
            logs.debug(LogEvent.RUN_PLANNED, fields)
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
            seeds=tuple(sorted({run.key.seed for run in planned})),
        ),
    )
    logs.info(
        LogEvent.PLAN_WRITTEN,
        {
            LogField.MODE: mode,
            LogField.RUNS: len(planned),
            LogField.INFEASIBLE: sum(run.status is RunStatus.INFEASIBLE for run in planned),
            LogField.SECONDS: watch.seconds(),
        },
    )
    return planned
