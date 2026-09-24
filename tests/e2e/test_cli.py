import json

import pytest
from typer.testing import CliRunner

from ctk_android.cli import app
from ctk_android.enums import (
    Artifact,
    CliCommand,
    ExecutionMode,
    ExperimentName,
    FileSuffix,
    LogEvent,
    LogField,
    ReportFigure,
    ReportTable,
    Stage,
    Verdict,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

runner = CliRunner()


def test_root_help_lists_the_public_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert all(command in result.output for command in CliCommand)


@pytest.mark.parametrize("command", list(CliCommand))
def test_each_command_builds_and_shows_help(command: CliCommand) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, result.output


def test_a_command_writes_start_and_finish_events_to_its_log_file() -> None:
    result = runner.invoke(app, [CliCommand.STATUS, "--mode", ExecutionMode.SMOKE])
    assert result.exit_code == 0, result.output
    lines = [
        json.loads(line)
        for line in Paths(REPO_ROOT)
        .log_file(CliCommand.STATUS)
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    events = [line["event"] for line in lines]
    assert LogEvent.COMMAND_STARTED in events
    assert events[-1] == LogEvent.COMMAND_FINISHED
    assert lines[-1][LogField.STATUS] == Verdict.PASS
    assert lines[-1][LogField.SECONDS] >= 0


def test_run_command_writes_tables_and_figures_for_the_mode_when_it_finishes() -> None:
    paths = Paths(REPO_ROOT)
    if not paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file():
        pytest.skip("preprocessing outputs are not available; run `ctk-android preprocess`")
    assert runner.invoke(app, [CliCommand.PLAN, ExecutionMode.SMOKE]).exit_code == 0
    result = runner.invoke(
        app, [CliCommand.RUN, ExperimentName.END_TO_END, "--mode", ExecutionMode.SMOKE]
    )
    assert result.exit_code == 0, result.output
    for table in ReportTable:
        assert paths.report_table_file(ExecutionMode.SMOKE, table).stat().st_size > 0
    for figure in ReportFigure:
        assert paths.report_figure_file(ExecutionMode.SMOKE, figure, FileSuffix.PNG).is_file()
