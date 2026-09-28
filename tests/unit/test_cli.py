import inspect
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

import ctk_android.cli as cli
from ctk_android.config import load_config
from ctk_android.enums import (
    CliCommand,
    CompletionState,
    ExecutionMode,
    ExperimentName,
    FailureReason,
    RunStatus,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import CtkError, StatusCounts
from tests.architecture.source_index import REPO_ROOT

runner = CliRunner()

FINAL_COMMANDS = ("doctor", "preprocess", "plan", "smoke", "run", "status", "report")
REMOVED_COMMANDS = (
    "posthoc",
    "large-family",
    "dose-extension",
    "controls-extension",
    "representation-preprocess",
    "representation-extension",
    "diagnostics",
)


def _typed_callback(callback: Callable[..., Any]) -> Callable[..., Any]:
    return callback


@pytest.fixture
def context(tmp_path: Path) -> cli.CliContext:
    return cli.CliContext(
        paths=Paths(tmp_path), config=load_config(Paths(REPO_ROOT)), watch=Stopwatch()
    )


def _bind_success(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext, calls: list[str]
) -> None:
    monkeypatch.setattr(cli, "_context", _typed_callback(lambda _command: context))
    monkeypatch.setattr(cli, "_finished", _typed_callback(lambda _context, _verdict: None))
    monkeypatch.setattr(cli, "_failed", _typed_callback(lambda _context, _error: None))
    workflows = {
        cli.maintenance_workflow: ("run_doctor", "run_plan", "run_status"),
        cli.preprocess_workflow: ("run_preprocess",),
        cli.run_workflow: ("run_experiment", "run_smoke"),
        cli.report_workflow: ("run_report",),
    }
    for workflow, names in workflows.items():
        for name in names:
            monkeypatch.setattr(
                workflow,
                name,
                _typed_callback(
                    lambda *_args, _name=name, **_kwargs: (
                        calls.append(_name) or _success_result(_name)
                    )
                ),
            )


def _success_result(name: str) -> object:
    if name == "run_doctor":
        return [SimpleNamespace(passed=True, check="check", detail="ok")]
    if name == "run_status":
        counts = StatusCounts(
            expected=0,
            completed=0,
            missing=0,
            failed=0,
            infeasible=0,
            invalid=0,
            state=CompletionState.COMPLETE,
        )
        return SimpleNamespace(experiments=(), total=counts)
    return []


def test_the_public_command_surface_is_exactly_the_seven_final_commands() -> None:
    assert tuple(command.value for command in CliCommand) == FINAL_COMMANDS
    assert [command.name for command in cli.app.registered_commands] == list(FINAL_COMMANDS)
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert all(command in result.output for command in FINAL_COMMANDS)


@pytest.mark.parametrize("command", REMOVED_COMMANDS)
def test_removed_commands_are_not_registered(command: str) -> None:
    result = runner.invoke(cli.app, [command, "--help"])
    assert result.exit_code == 2
    assert "No such command" in result.output


def _options(command: str) -> set[str]:
    result = runner.invoke(cli.app, [command, "--help"])
    assert result.exit_code == 0, result.output
    return {word for word in result.output.split() if word.startswith("--")}


@pytest.mark.parametrize(
    ("command", "allowed"),
    [
        ("doctor", {"--help"}),
        ("preprocess", {"--overwrite", "--no-overwrite", "--help"}),
        ("plan", {"--help"}),
        ("smoke", {"--overwrite", "--no-overwrite", "--help"}),
        ("run", {"--overwrite", "--no-overwrite", "--help"}),
        ("status", {"--help"}),
        ("report", {"--help"}),
    ],
)
def test_no_command_exposes_scientific_or_scope_options(command: str, allowed: set[str]) -> None:
    assert _options(command) == allowed


@pytest.mark.parametrize(
    "arguments",
    [
        ["run", ExperimentName.CONTROLLED_EXPOSURE, "--mode", ExecutionMode.CONFIRMATORY],
        ["run", ExperimentName.CONTROLLED_EXPOSURE, "--seed", "100"],
        ["preprocess", "--mode", ExecutionMode.DEVELOPMENT],
        ["smoke", "--mode", ExecutionMode.SMOKE],
        ["smoke", "--seed", "0"],
        ["status", "--mode", ExecutionMode.CONFIRMATORY],
        ["report", "--mode", ExecutionMode.CONFIRMATORY],
        ["report", "--promote"],
        ["report", "--no-promote"],
        ["doctor", "--mode", ExecutionMode.SMOKE],
        ["plan", ExecutionMode.SMOKE, "--seed", "0"],
    ],
)
def test_obsolete_options_are_rejected(arguments: list[str]) -> None:
    result = runner.invoke(cli.app, arguments)
    assert result.exit_code == 2
    assert "No such option" in result.output


def test_plan_is_the_only_command_that_takes_a_mode() -> None:
    parameters = {
        command.name: set(inspect.signature(command.callback).parameters)
        for command in cli.app.registered_commands
        if command.callback is not None
    }
    assert {name for name, names in parameters.items() if "mode" in names} == {"plan"}
    assert not {name for name, names in parameters.items() if "seed" in names}
    assert "experiment" in parameters["run"] and parameters["run"] == {"experiment", "overwrite"}


def test_every_command_handler_delegates_to_its_workflow(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext
) -> None:
    calls: list[str] = []
    _bind_success(monkeypatch, context, calls)

    cli.doctor()
    cli.preprocess()
    cli.plan(ExecutionMode.DEVELOPMENT)
    cli.smoke()
    cli.run(ExperimentName.CONTROLLED_EXPOSURE)
    cli.status()
    cli.report()

    assert calls == [
        "run_doctor",
        "run_preprocess",
        "run_plan",
        "run_smoke",
        "run_experiment",
        "run_status",
        "run_report",
    ]


def test_run_exits_non_zero_when_any_configured_run_did_not_complete(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext
) -> None:
    monkeypatch.setattr(cli, "_context", _typed_callback(lambda _command: context))
    monkeypatch.setattr(cli, "_finished", _typed_callback(lambda _context, _verdict: None))
    key = SimpleNamespace(
        experiment=ExperimentName.CONTROLLED_EXPOSURE,
        mode=ExecutionMode.CONFIRMATORY,
        seed=100,
        salt=0,
    )
    unfinished = SimpleNamespace(key=key, status=RunStatus.FAILED_VALIDATION)
    monkeypatch.setattr(
        cli.run_workflow, "run_experiment", _typed_callback(lambda *_args: [unfinished])
    )
    with pytest.raises(cli.typer.Exit) as raised:
        cli.run(ExperimentName.CONTROLLED_EXPOSURE)
    assert raised.value.exit_code == 1


def test_workflow_errors_are_logged_and_converted_to_cli_exits(
    monkeypatch: pytest.MonkeyPatch, context: cli.CliContext
) -> None:
    failure = CtkError(FailureReason.NO_COMPLETED_RUNS, "no completed runs")
    failed: list[CtkError] = []
    monkeypatch.setattr(cli, "_context", _typed_callback(lambda _command: context))
    monkeypatch.setattr(
        cli, "_failed", _typed_callback(lambda _context, error: failed.append(error))
    )

    def fail(*_args: object, **_kwargs: object) -> object:
        raise failure

    monkeypatch.setattr(cli.preprocess_workflow, "run_preprocess", fail)
    monkeypatch.setattr(cli.maintenance_workflow, "run_plan", fail)
    monkeypatch.setattr(cli.run_workflow, "run_smoke", fail)
    monkeypatch.setattr(cli.run_workflow, "run_experiment", fail)
    monkeypatch.setattr(cli.report_workflow, "run_report", fail)

    handlers: tuple[Callable[[], None], ...] = (
        cli.preprocess,
        lambda: cli.plan(ExecutionMode.DEVELOPMENT),
        cli.smoke,
        lambda: cli.run(ExperimentName.CONTROLLED_EXPOSURE),
        cli.report,
    )
    for handler in handlers:
        with pytest.raises(cli.typer.Exit) as raised:
            handler()
        assert raised.value.exit_code == 1
    assert failed == [failure] * len(handlers)
