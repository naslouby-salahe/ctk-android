from collections.abc import Callable
from pathlib import Path

# Pyright cannot infer callback signatures for monkeypatch lambda stubs.
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false
from types import SimpleNamespace

import pytest

import ctk_android.cli as cli
from ctk_android.config import load_config
from ctk_android.enums import (
    ExecutionMode,
    ExperimentName,
    FailureReason,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import CtkError
from tests.architecture.source_index import REPO_ROOT


@pytest.fixture
def context(tmp_path: Path) -> cli.CliContext:
    return cli.CliContext(
        paths=Paths(tmp_path), config=load_config(Paths(REPO_ROOT)), watch=Stopwatch()
    )


def _bind_success(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext, calls: list[str]
) -> None:
    monkeypatch.setattr(cli, "_context", lambda _command: context)
    monkeypatch.setattr(cli, "_finished", lambda _context, _verdict: None)
    monkeypatch.setattr(cli, "_failed", lambda _context, _error: None)
    workflows = {
        cli.maintenance_workflow: (
            "run_doctor",
            "run_plan",
            "run_status",
        ),
        cli.preprocess_workflow: ("run_preprocess", "run_representation_preprocess"),
        cli.run_workflow: ("run_and_report", "run_smoke"),
        cli.report_workflow: (
            "run_report",
            "run_posthoc",
            "run_large_family",
            "run_dose_extension",
            "run_controls_extension",
            "run_representation_extension",
            "run_diagnostics",
        ),
    }
    for workflow, names in workflows.items():
        for name in names:
            monkeypatch.setattr(
                workflow,
                name,
                lambda *_args, _name=name, **_kwargs: calls.append(_name) or _success_result(_name),
            )


def _success_result(name: str) -> object:
    if name == "run_doctor":
        return [SimpleNamespace(passed=True, check="check", detail="ok")]
    if name == "run_smoke":
        return SimpleNamespace(status="completed", directory="runs/smoke")
    if name == "run_status":
        return "status"
    if name in {
        "run_report",
        "run_posthoc",
        "run_large_family",
        "run_dose_extension",
        "run_controls_extension",
        "run_representation_extension",
        "run_diagnostics",
    }:
        return None
    return []


def test_every_command_handler_delegates_to_its_workflow(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext
) -> None:
    calls: list[str] = []
    _bind_success(monkeypatch, context, calls)

    cli.doctor()
    cli.preprocess()
    cli.plan(ExecutionMode.DEVELOPMENT)
    cli.smoke()
    cli.run(ExperimentName.END_TO_END, ExecutionMode.DEVELOPMENT, 1)
    cli.status(ExecutionMode.DEVELOPMENT)
    cli.report(ExecutionMode.CONFIRMATORY)
    cli.posthoc(ExecutionMode.CONFIRMATORY)
    cli.large_family(ExecutionMode.EXTENSION_B)
    cli.dose_extension(ExecutionMode.EXTENSION_B)
    cli.controls_extension(ExecutionMode.EXTENSION_B)
    cli.representation_preprocess()
    cli.representation_extension(ExecutionMode.EXTENSION_B)
    cli.diagnostics(ExecutionMode.EXTENSION_B)

    assert calls == [
        "run_doctor",
        "run_preprocess",
        "run_plan",
        "run_smoke",
        "run_and_report",
        "run_status",
        "run_report",
        "run_posthoc",
        "run_large_family",
        "run_dose_extension",
        "run_controls_extension",
        "run_representation_preprocess",
        "run_representation_extension",
        "run_diagnostics",
    ]


def test_workflow_errors_are_logged_and_converted_to_cli_exits(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext
) -> None:
    failure = CtkError(FailureReason.NO_COMPLETED_RUNS, "no completed runs")
    failed: list[CtkError] = []
    monkeypatch.setattr(cli, "_context", lambda _command: context)
    monkeypatch.setattr(cli, "_failed", lambda _context, error: failed.append(error))

    def fail(*_args: object, **_kwargs: object) -> object:
        raise failure

    monkeypatch.setattr(cli.preprocess_workflow, "run_preprocess", fail)
    monkeypatch.setattr(cli.maintenance_workflow, "run_plan", fail)
    monkeypatch.setattr(cli.run_workflow, "run_smoke", fail)
    monkeypatch.setattr(cli.run_workflow, "run_and_report", fail)
    for name in (
        "run_report",
        "run_posthoc",
        "run_large_family",
        "run_dose_extension",
        "run_controls_extension",
        "run_representation_extension",
        "run_diagnostics",
    ):
        monkeypatch.setattr(cli.report_workflow, name, fail)
    monkeypatch.setattr(cli.preprocess_workflow, "run_representation_preprocess", fail)

    handlers: tuple[Callable[[], None], ...] = (
        cli.preprocess,
        lambda: cli.plan(ExecutionMode.DEVELOPMENT),
        cli.smoke,
        lambda: cli.run(ExperimentName.END_TO_END, ExecutionMode.DEVELOPMENT, 1),
        lambda: cli.report(ExecutionMode.CONFIRMATORY),
        lambda: cli.posthoc(ExecutionMode.CONFIRMATORY),
        lambda: cli.large_family(ExecutionMode.EXTENSION_B),
        lambda: cli.dose_extension(ExecutionMode.EXTENSION_B),
        lambda: cli.controls_extension(ExecutionMode.EXTENSION_B),
        cli.representation_preprocess,
        lambda: cli.representation_extension(ExecutionMode.EXTENSION_B),
        lambda: cli.diagnostics(ExecutionMode.EXTENSION_B),
    )
    for handler in handlers:
        with pytest.raises(cli.typer.Exit) as raised:
            handler()
        assert raised.value.exit_code == 1
    assert failed == [failure] * len(handlers)
