import polars as pl

from ctk_android import logs
from ctk_android.data.cache import read_record, records_to_frame
from ctk_android.enums import Artifact, Column, ExecutionMode, LogEvent, LogField, RunStatus
from ctk_android.paths import Paths
from ctk_android.types import RunKey, RunStatusDocument, StatusCountsTable, StatusRow


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
