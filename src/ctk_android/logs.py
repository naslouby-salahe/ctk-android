import logging
import time

import structlog

from ctk_android.enums import CliCommand, LibraryOption, LogEvent, LogLevel, TextEncoding
from ctk_android.paths import Paths
from ctk_android.types import LogFields, Seconds


class Stopwatch:
    def __init__(self) -> None:
        self._started = time.perf_counter()

    def seconds(self) -> Seconds:
        return time.perf_counter() - self._started


def configure_logging(paths: Paths, command: CliCommand, level: LogLevel) -> None:
    shared: list[structlog.typing.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt=LibraryOption.TIMESTAMP_ISO),
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    target = paths.log_file(command)
    target.parent.mkdir(parents=True, exist_ok=True)
    console = logging.StreamHandler()
    console.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=False), foreign_pre_chain=shared
        )
    )
    disk = logging.FileHandler(target, encoding=TextEncoding.UTF8)
    disk.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(), foreign_pre_chain=shared
        )
    )
    root = logging.getLogger()
    root.handlers = [console, disk]
    root.setLevel(logging.getLevelNamesMapping()[level])


def emit(level: LogLevel, event: LogEvent, fields: LogFields) -> None:
    structlog.get_logger().log(logging.getLevelNamesMapping()[level], event, **fields)


def bind(fields: LogFields) -> None:
    structlog.contextvars.bind_contextvars(**fields)


def debug(event: LogEvent, fields: LogFields) -> None:
    emit(LogLevel.DEBUG, event, fields)


def info(event: LogEvent, fields: LogFields) -> None:
    emit(LogLevel.INFO, event, fields)


def warning(event: LogEvent, fields: LogFields) -> None:
    emit(LogLevel.WARNING, event, fields)


def error(event: LogEvent, fields: LogFields) -> None:
    emit(LogLevel.ERROR, event, fields)
