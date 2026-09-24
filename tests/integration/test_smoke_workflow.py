import polars as pl
import pytest
from structlog.testing import capture_logs

from ctk_android.config import load_config
from ctk_android.enums import (
    Artifact,
    Column,
    ExecutionMode,
    LogEvent,
    LogField,
    Metric,
    RunStatus,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.workflows.smoke import run_smoke
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)


def test_smoke_workflow_completes_with_metrics_and_is_idempotent() -> None:
    if not PATHS.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file():
        pytest.skip("preprocessing outputs are not available; run `ctk-android preprocess`")
    config = load_config(PATHS)
    first = run_smoke(PATHS, config, overwrite=False)
    second = run_smoke(PATHS, config, overwrite=False)
    assert first.status is RunStatus.COMPLETED
    assert second.reused
    summary = pl.read_parquet(PATHS.run_metric_file(first.key, Artifact.SUMMARY))
    assert summary.filter(pl.col(Column.METRIC) == Metric.FEDERATION_UNSEEN_RECALL).height > 0
    assert first.key.mode is ExecutionMode.SMOKE


def test_smoke_run_logs_its_full_lifecycle_with_counts_and_timings() -> None:
    if not PATHS.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file():
        pytest.skip("preprocessing outputs are not available; run `ctk-android preprocess`")
    config = load_config(PATHS)
    with capture_logs() as forced:
        run_smoke(PATHS, config, overwrite=True)
    events = [entry["event"] for entry in forced]
    assert events.index(LogEvent.PLAN_WRITTEN) < events.index(LogEvent.RUN_STARTED)
    for expected in (
        LogEvent.RUN_STARTED,
        LogEvent.EXPOSURE_SELECTED,
        LogEvent.ARM_TRAINED,
        LogEvent.EVALUATION_FINISHED,
        LogEvent.VALIDATION_PASSED,
        LogEvent.RUN_FINISHED,
    ):
        assert expected in events, expected
    assert events.index(LogEvent.RUN_STARTED) < events.index(LogEvent.ARM_TRAINED)
    assert events.index(LogEvent.ARM_TRAINED) < events.index(LogEvent.RUN_FINISHED)
    trained = [entry for entry in forced if entry["event"] == LogEvent.ARM_TRAINED]
    assert len(trained) >= 7
    assert all(entry[LogField.SECONDS] >= 0 and entry[LogField.TRAIN_ROWS] > 0 for entry in trained)
    finished = next(entry for entry in forced if entry["event"] == LogEvent.RUN_FINISHED)
    assert finished[LogField.STATUS] == RunStatus.COMPLETED
    with capture_logs() as reused:
        run_smoke(PATHS, config, overwrite=False)
    assert LogEvent.RUN_REUSED in [entry["event"] for entry in reused]
    assert LogEvent.ARM_TRAINED not in [entry["event"] for entry in reused]
