import pytest
from typer.testing import CliRunner

from ctk_android.cli import app
from ctk_android.enums import CliCommand

runner = CliRunner()


def test_root_help_lists_the_public_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert all(
        command in result.output for command in CliCommand if command is not CliCommand.REPORT
    )


@pytest.mark.parametrize("command", [c for c in CliCommand if c is not CliCommand.REPORT])
def test_each_command_builds_and_shows_help(command: CliCommand) -> None:
    result = runner.invoke(app, [command, "--help"])
    assert result.exit_code == 0, result.output
