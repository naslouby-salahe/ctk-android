import json
import logging
from pathlib import Path

from structlog.testing import capture_logs

from ctk_android import logs
from ctk_android.enums import CliCommand, LogEvent, LogField, LogLevel
from ctk_android.paths import Paths


def test_levels_events_and_fields_are_routed_as_structured_data() -> None:
    with capture_logs() as captured:
        logs.debug(LogEvent.FEDERATED_ROUND, {LogField.ROUND: 1})
        logs.info(LogEvent.RUN_STARTED, {LogField.SEED: 100, LogField.EXPERIMENT: "controlled"})
        logs.warning(LogEvent.VALIDATION_FAILED, {LogField.CHECK: "sample-size-matched"})
        logs.error(LogEvent.COMMAND_FAILED, {LogField.REASON: "boom"})
    assert [entry["log_level"] for entry in captured] == ["debug", "info", "warning", "error"]
    assert [entry["event"] for entry in captured] == [
        LogEvent.FEDERATED_ROUND,
        LogEvent.RUN_STARTED,
        LogEvent.VALIDATION_FAILED,
        LogEvent.COMMAND_FAILED,
    ]
    assert captured[1][LogField.SEED] == 100
    assert captured[2][LogField.CHECK] == "sample-size-matched"


def test_stopwatch_measures_non_negative_increasing_time() -> None:
    watch = logs.Stopwatch()
    first = watch.seconds()
    assert 0.0 <= first <= watch.seconds()


def test_configured_logging_writes_json_lines_with_timestamp_and_level(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    root = logging.getLogger()
    saved = list(root.handlers), root.level
    try:
        logs.configure_logging(paths, CliCommand.DOCTOR, LogLevel.INFO)
        logs.info(LogEvent.COMMAND_STARTED, {LogField.COMMAND: CliCommand.DOCTOR})
        logs.debug(LogEvent.FEDERATED_ROUND, {LogField.ROUND: 3})
        for handler in root.handlers:
            handler.flush()
    finally:
        for handler in root.handlers:
            handler.close()
        root.handlers, root.level = saved[0], saved[1]
    lines = [
        json.loads(line)
        for line in paths.log_file(CliCommand.DOCTOR).read_text(encoding="utf-8").splitlines()
    ]
    assert [line["event"] for line in lines] == [LogEvent.COMMAND_STARTED]
    assert lines[0]["level"] == "info"
    assert lines[0][LogField.COMMAND] == CliCommand.DOCTOR
    assert "timestamp" in lines[0]


def test_debug_events_are_emitted_when_the_level_is_debug(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    root = logging.getLogger()
    saved = list(root.handlers), root.level
    try:
        logs.configure_logging(paths, CliCommand.PLAN, LogLevel.DEBUG)
        logs.debug(LogEvent.FEDERATED_ROUND, {LogField.ROUND: 3})
        for handler in root.handlers:
            handler.flush()
    finally:
        for handler in root.handlers:
            handler.close()
        root.handlers, root.level = saved[0], saved[1]
    text = paths.log_file(CliCommand.PLAN).read_text(encoding="utf-8")
    assert LogEvent.FEDERATED_ROUND in text
