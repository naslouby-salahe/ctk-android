import hashlib

import polars as pl
import pytest
from structlog.testing import capture_logs

from ctk_android.config import Config, load_config
from ctk_android.data.cache import read_record
from ctk_android.enums import (
    Artifact,
    Column,
    ExecutionMode,
    ExperimentName,
    Learner,
    LogEvent,
    LogField,
    Metric,
    OptimizationStatus,
    ReportTable,
    RunStatus,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import RunManifest, RunReport
from ctk_android.workflows.report import run_analysis
from ctk_android.workflows.run import run_smoke


def _require_preprocessing(paths: Paths) -> None:
    if not paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file():
        pytest.skip("preprocessing outputs are not available; run `ctk-android preprocess`")


def _end_to_end_only(config: Config) -> Config:
    return config.model_copy(
        update={
            "experiments": config.experiments.model_copy(
                update={
                    "experiments": {
                        ExperimentName.END_TO_END: config.experiments.experiments[
                            ExperimentName.END_TO_END
                        ]
                    }
                }
            )
        }
    )


@pytest.fixture(scope="module")
def smoke_reports(preprocessed_workspace: Paths) -> list[RunReport]:
    _require_preprocessing(preprocessed_workspace)
    return run_smoke(preprocessed_workspace, load_config(preprocessed_workspace), overwrite=False)


def test_smoke_executes_every_configured_smoke_run_and_they_all_pass_validation(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    config = load_config(preprocessed_workspace)
    assert tuple(report.key for report in smoke_reports) == config.mode_keys(ExecutionMode.SMOKE)
    assert len({report.key.experiment for report in smoke_reports}) > 1
    assert all(report.status is RunStatus.COMPLETED for report in smoke_reports)
    assert all(report.key.mode is ExecutionMode.SMOKE for report in smoke_reports)


def test_smoke_workflow_writes_metrics_and_is_idempotent(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    paths = preprocessed_workspace
    config = load_config(paths)
    first = next(
        report for report in smoke_reports if report.key.experiment is ExperimentName.END_TO_END
    )
    summary = pl.read_parquet(paths.run_metric_file(first.key, Artifact.SUMMARY))
    assert summary.filter(pl.col(Column.METRIC) == Metric.FEDERATION_UNSEEN_RECALL).height > 0
    again = run_smoke(paths, config, overwrite=False)
    assert all(report.reused for report in again)


def test_every_smoke_manifest_records_execution_provenance_and_a_verifiable_configuration(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    paths = preprocessed_workspace
    config = load_config(paths)
    for report in smoke_reports:
        manifest = read_record(paths.run_file(report.key, Artifact.MANIFEST), RunManifest)
        execution = manifest.execution
        assert execution is not None
        spec = config.experiments.experiments[report.key.experiment]
        assert execution.protocol == config.fingerprint()
        assert execution.resolved_configuration == config.resolved_configuration(
            spec, report.key.mode
        )
        assert manifest.config == config.run_fingerprint(spec, report.key.mode)
        assert hashlib.sha256(execution.resolved_configuration.encode()).hexdigest() == (
            manifest.config
        )
        assert execution.revision
        assert execution.data.lamda and execution.data.androzoo
        assert manifest.key == report.key


def test_every_smoke_run_writes_a_training_record_for_each_trained_arm(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    paths = preprocessed_workspace
    for report in smoke_reports:
        training = pl.read_parquet(paths.run_file(report.key, Artifact.TRAINING))
        manifest = read_record(paths.run_file(report.key, Artifact.MANIFEST), RunManifest)
        trained = {arm.learner for arm in manifest.arms} - {Learner.BLEND}
        assert trained <= set(training[Column.LEARNER].to_list()), report.key
        assert training[Column.NONFINITE_BATCHES].sum() == 0
        assert training[Column.PARAMETERS_FINITE].all()
        assert set(training[Column.STATUS].unique().to_list()) == {OptimizationStatus.COMPLETED}


def test_smoke_builds_its_own_mode_report_but_never_writes_results(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    assert smoke_reports
    paths = preprocessed_workspace
    for table in ReportTable:
        assert paths.report_table_file(ExecutionMode.SMOKE, table).stat().st_size > 0
    assert not (paths.root / "results").exists()


def test_smoke_run_logs_its_full_lifecycle_with_counts_and_timings(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    assert smoke_reports
    paths = preprocessed_workspace
    config = _end_to_end_only(load_config(paths))
    with capture_logs() as forced:
        run_smoke(paths, config, overwrite=True)
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
        run_smoke(paths, config, overwrite=False)
    assert LogEvent.RUN_REUSED in [entry["event"] for entry in reused]
    assert LogEvent.ARM_TRAINED not in [entry["event"] for entry in reused]


def test_analysis_handles_single_seed_smoke_evidence_from_every_experiment(
    preprocessed_workspace: Paths, smoke_reports: list[RunReport]
) -> None:
    assert smoke_reports
    run_analysis(preprocessed_workspace, load_config(preprocessed_workspace), ExecutionMode.SMOKE)
