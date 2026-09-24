import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import Artifact, Column, ExecutionMode, Metric, RunStatus, Stage
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
