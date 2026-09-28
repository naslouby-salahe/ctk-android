import json

import pytest
from typer.testing import CliRunner

import ctk_android.cli as cli
from ctk_android.cli import app
from ctk_android.config import Config, load_config
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
    RunStatus,
    Stage,
    Verdict,
)
from ctk_android.paths import Paths

runner = CliRunner()


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


def test_root_help_lists_the_public_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert all(command in result.output for command in CliCommand)


@pytest.mark.parametrize("command", list(CliCommand))
def test_each_command_builds_and_shows_help(command: CliCommand) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, result.output


def test_a_command_writes_start_and_finish_events_to_its_log_file(
    in_preprocessed_workspace: Paths,
) -> None:
    result = runner.invoke(app, [CliCommand.STATUS])
    assert result.exit_code == 0, result.output
    lines = [
        json.loads(line)
        for line in in_preprocessed_workspace.log_file(CliCommand.STATUS)
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    events = [line["event"] for line in lines]
    assert LogEvent.COMMAND_STARTED in events
    assert events[-1] == LogEvent.COMMAND_FINISHED
    assert lines[-1][LogField.STATUS] == Verdict.PASS
    assert lines[-1][LogField.SECONDS] >= 0


def test_status_summarises_the_whole_configured_matrix_without_arguments(
    in_preprocessed_workspace: Paths,
) -> None:
    result = runner.invoke(app, [CliCommand.STATUS])
    assert result.exit_code == 0, result.output
    config = load_config(in_preprocessed_workspace)
    assert "total" in result.output
    for experiment in config.experiments.experiments:
        if config.experiments.campaign_modes(experiment):
            assert experiment in result.output
    assert not in_preprocessed_workspace.outputs.joinpath(Stage.RUNS).exists()


def test_smoke_command_builds_the_smoke_evidence_but_run_never_builds_reports(
    in_preprocessed_workspace: Paths, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = in_preprocessed_workspace
    if not paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file():
        pytest.skip("preprocessing outputs are not available; run `ctk-android preprocess`")
    monkeypatch.setattr(cli, "load_config", lambda paths: _end_to_end_only(load_config(paths)))
    result = runner.invoke(app, [CliCommand.SMOKE])
    assert result.exit_code == 0, result.output
    for table in ReportTable:
        assert paths.report_table_file(ExecutionMode.SMOKE, table).stat().st_size > 0
    for figure in ReportFigure:
        assert paths.report_figure_file(ExecutionMode.SMOKE, figure, FileSuffix.PNG).is_file()
    assert RunStatus.COMPLETED in result.output
    assert not (paths.root / "results").exists()
