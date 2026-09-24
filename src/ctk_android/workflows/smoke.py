import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import read_record
from ctk_android.enums import (
    Artifact,
    Column,
    ErrorMessage,
    ExecutionMode,
    ExperimentName,
    FailureReason,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.types import CtkError, Overwrite, RunReport, ValidationDocument
from ctk_android.workflows.plan import run_plan
from ctk_android.workflows.run import run_experiment


def run_smoke(paths: Paths, config: Config, overwrite: Overwrite) -> RunReport:
    run_plan(paths, config, ExecutionMode.SMOKE)
    reports = run_experiment(
        paths,
        config,
        ExperimentName.END_TO_END,
        ExecutionMode.SMOKE,
        config.project.seeds.smoke,
        overwrite,
    )
    report = reports[0]
    summary = pl.read_parquet(paths.run_metric_file(report.key, Artifact.SUMMARY))
    if (
        report.status is not RunStatus.COMPLETED
        or summary.filter(pl.col(Column.VALUE).is_null()).height
    ):
        detail = read_record(paths.run_file(report.key, Artifact.VALIDATION), ValidationDocument)
        raise CtkError(
            FailureReason.NO_ELIGIBLE_TARGETS, ErrorMessage.SMOKE_INCOMPLETE.format(detail=detail)
        )
    return report
