import ast
from pathlib import Path

import pytest

from ctk_android.config import Config, load_config
from ctk_android.enums import ExecutionMode, ExperimentName, FailureReason, RunStatus
from ctk_android.paths import Paths
from ctk_android.types import CtkError, RunKey, RunReport
from ctk_android.workflows import run as workflow
from tests.architecture.source_index import REPO_ROOT, SRC_ROOT, parse

CONFIG = load_config(Paths(REPO_ROOT))
REPORT_OWNED_PATHS = {
    "analysis_file",
    "statistics_file",
    "report_table_file",
    "report_figure_file",
    "results_file",
    "results_root_file",
    "results_at",
    "results_entry",
    "results_listing",
    "results_name",
}


def _record_executions(monkeypatch: pytest.MonkeyPatch) -> list[RunKey]:
    executed: list[RunKey] = []

    def fake(_paths: Paths, _config: Config, key: RunKey, _overwrite: bool) -> RunReport:
        executed.append(key)
        return RunReport(
            key=key, status=RunStatus.COMPLETED, reused=False, directory=Path(key.experiment)
        )

    monkeypatch.setattr(workflow, "execute_run", fake)
    monkeypatch.setattr(workflow, "_require_plans", lambda *_args: None)
    return executed


@pytest.mark.parametrize("experiment", list(CONFIG.experiments.experiments))
def test_run_executes_the_complete_configured_matrix_without_any_caller_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, experiment: ExperimentName
) -> None:
    executed = _record_executions(monkeypatch)
    spec = CONFIG.experiments.experiments[experiment]
    expected = [
        RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
        for mode in ExecutionMode
        if mode is not ExecutionMode.SMOKE and CONFIG.experiments.runs_in(experiment, mode)
        for seed in CONFIG.seeds_for(experiment, mode)
        for salt in spec.salts
    ]
    if not expected:
        with pytest.raises(CtkError) as raised:
            workflow.run_experiment(Paths(tmp_path), CONFIG, experiment, False)
        assert raised.value.reason is FailureReason.NO_ELIGIBLE_TARGETS
        assert not executed
        return
    reports = workflow.run_experiment(Paths(tmp_path), CONFIG, experiment, False)
    assert executed == expected
    assert [report.key for report in reports] == expected


def test_a_multi_scope_experiment_runs_every_scope_with_its_own_seeds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executed = _record_executions(monkeypatch)
    workflow.run_experiment(Paths(tmp_path), CONFIG, ExperimentName.CONTROLLED_EXPOSURE, False)
    by_mode = {mode: [key.seed for key in executed if key.mode is mode] for mode in ExecutionMode}
    assert by_mode[ExecutionMode.DEVELOPMENT] == list(CONFIG.project.seeds.development)
    assert by_mode[ExecutionMode.CONFIRMATORY] == list(CONFIG.project.seeds.confirmatory)
    assert not by_mode[ExecutionMode.SMOKE]


def test_designed_experiments_resolve_their_dedicated_seed_ranges(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executed = _record_executions(monkeypatch)
    workflow.run_experiment(
        Paths(tmp_path), CONFIG, ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY, False
    )
    assert {key.seed for key in executed} == set(CONFIG.project.seeds.extension_dose)
    assert {key.mode for key in executed} == {ExecutionMode.EXTENSION_B}


def test_the_salt_sensitivity_experiment_runs_every_configured_salt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executed = _record_executions(monkeypatch)
    workflow.run_experiment(
        Paths(tmp_path), CONFIG, ExperimentName.PARTITION_SALT_SENSITIVITY, False
    )
    salts = CONFIG.experiments.experiments[ExperimentName.PARTITION_SALT_SENSITIVITY].salts
    assert {key.salt for key in executed} == set(salts)
    assert len(executed) == len(salts) * len(CONFIG.project.seeds.confirmatory)


def test_smoke_only_experiments_are_not_runnable_through_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executed = _record_executions(monkeypatch)
    with pytest.raises(CtkError):
        workflow.run_experiment(Paths(tmp_path), CONFIG, ExperimentName.END_TO_END, False)
    assert not executed


def test_run_needs_a_plan_for_every_mode_it_will_execute(tmp_path: Path) -> None:
    with pytest.raises(CtkError) as raised:
        workflow.run_experiment(Paths(tmp_path), CONFIG, ExperimentName.CONTROLLED_EXPOSURE, False)
    assert raised.value.reason is FailureReason.NO_ELIGIBLE_TARGETS
    assert "plan" in f"{raised.value}"


def test_run_never_builds_a_shared_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _record_executions(monkeypatch)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("run must not build a shared report")

    monkeypatch.setattr(workflow, "run_mode_report", forbidden)
    workflow.run_experiment(Paths(tmp_path), CONFIG, ExperimentName.NATURAL_SCARCITY, False)


def test_the_run_module_writes_only_run_artifacts_and_reads_plans() -> None:
    accessed = {
        node.attr
        for node in ast.walk(parse(SRC_ROOT / "workflows" / "run.py"))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "paths"
    }
    assert not accessed & REPORT_OWNED_PATHS


def test_no_experiment_shares_a_run_directory_with_another() -> None:
    directories = {
        Paths(REPO_ROOT).run_dir(key)
        for experiment in CONFIG.experiments.experiments
        for key in CONFIG.experiment_keys(experiment)
    }
    keys = [
        key
        for experiment in CONFIG.experiments.experiments
        for key in CONFIG.experiment_keys(experiment)
    ]
    assert len(directories) == len(keys)


def test_smoke_runs_the_whole_configured_smoke_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    executed = _record_executions(monkeypatch)
    monkeypatch.setattr(workflow, "run_plan", lambda *_args: [])
    monkeypatch.setattr(workflow, "run_mode_report", lambda *_args: None)
    monkeypatch.setattr(
        workflow.pl, "read_parquet", lambda *_args: workflow.pl.DataFrame({"value": [1.0]})
    )
    workflow.run_smoke(Paths(tmp_path), CONFIG, False)
    assert tuple(executed) == CONFIG.mode_keys(ExecutionMode.SMOKE)
    assert {key.experiment for key in executed} > {ExperimentName.END_TO_END}
