import ast

from ctk_android.cli import app
from tests.architecture import callgraph
from tests.architecture.source_index import (
    CLI_MODULE,
    SRC_ROOT,
    location,
    parse,
    source_files,
)

LOGS_MODULE = SRC_ROOT / "logs.py"
LEVELS = {"debug", "info", "warning", "error"}
STDLIB_LOGGING = {"logging", "structlog"}


def _emit_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in LEVELS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "logs"
    ]


def _report_aliases(tree: ast.AST) -> list[ast.Call]:
    """Calls made through a local alias such as `report = logs.info; report(...)`."""
    aliases = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.IfExp)
        and any(
            isinstance(branch, ast.Attribute) and branch.attr in LEVELS
            for branch in (node.value.body, node.value.orelse)
        )
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in aliases
    ]


def _logging_calls(tree: ast.AST) -> list[ast.Call]:
    return _emit_calls(tree) + _report_aliases(tree)


def _called_names(tree: ast.AST) -> set[str]:
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def _print_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]


def _has_cli_lifecycle(tree: ast.AST) -> bool:
    names = _called_names(tree)
    return "_context" in names and "_finished" in names


def _silently_caught(tree: ast.AST) -> bool:
    for handler in (node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)):
        if any(isinstance(node, ast.Raise) for node in ast.walk(handler)):
            continue
        if _logging_calls(handler):
            continue
        return True
    return False


def test_only_the_logs_module_touches_the_logging_libraries() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files(LOGS_MODULE)
        for node in ast.walk(parse(path))
        if (
            isinstance(node, ast.Import)
            and any(alias.name.split(".")[0] in STDLIB_LOGGING for alias in node.names)
        )
        or (
            isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in STDLIB_LOGGING
        )
    ]
    assert not offenders, offenders


def test_no_print_statements() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    assert not offenders, offenders


def test_every_log_call_uses_an_event_enum_and_field_enum_keys() -> None:
    offenders: list[str] = []
    for path in source_files(LOGS_MODULE):
        for call in _logging_calls(parse(path)):
            where = location(path, call.lineno)
            if len(call.args) != 2 or call.keywords:
                offenders.append(f"{where} must pass exactly (event, fields)")
                continue
            event, fields = call.args
            if not (
                isinstance(event, ast.Attribute)
                and isinstance(event.value, ast.Name)
                and event.value.id == "LogEvent"
            ) and not isinstance(event, ast.IfExp):
                offenders.append(f"{where} event is not a LogEvent member")
            if isinstance(fields, ast.Dict):
                for key in fields.keys:
                    is_field = (
                        isinstance(key, ast.Attribute)
                        and isinstance(key.value, ast.Name)
                        and key.value.id == "LogField"
                    )
                    if key is not None and not is_field:
                        offenders.append(f"{where} field key is not a LogField member")
    assert not offenders, offenders


def _emitting_functions() -> set[str]:
    return {
        node.name
        for path in source_files(LOGS_MODULE)
        for node in ast.walk(parse(path))
        if isinstance(node, ast.FunctionDef) and _logging_calls(node)
    }


def _workflow_entry_points() -> set[str]:
    return {
        node.func.attr
        for node in ast.walk(parse(CLI_MODULE))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id.endswith("_workflow")
    }


def _cli_handler_functions() -> list[ast.FunctionDef]:
    return [
        node
        for node in parse(CLI_MODULE).body
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "command"
            for decorator in node.decorator_list
        )
    ]


def test_every_cli_entry_point_reaches_a_log_emission() -> None:
    by_name, edges, _ = callgraph.build()
    emitting = _emitting_functions()
    silent: list[str] = []
    for entry in sorted(_workflow_entry_points()):
        roots = by_name.get(entry, [])
        reached = callgraph.reachable(by_name, edges, roots)
        if not any(definition.name in emitting for definition in reached):
            silent.append(entry)
    assert _workflow_entry_points()
    assert not silent, silent


def test_every_registered_cli_handler_has_start_and_finish_logging() -> None:
    handlers = _cli_handler_functions()
    missing = [node.name for node in handlers if not _has_cli_lifecycle(node)]
    assert {node.name for node in handlers} == _registered_cli_names()
    assert not missing, missing


def _registered_cli_names() -> set[str]:
    return {command.callback.__name__ for command in app.registered_commands if command.callback}


def test_cli_logging_mutation_without_lifecycle_is_rejected() -> None:
    silent_command = ast.parse("def command():\n    run_workflow()\n")
    logged_command = ast.parse(
        "def command():\n    context = _context()\n    run_workflow()\n    _finished(context)\n"
    )
    assert not _has_cli_lifecycle(silent_command)
    assert _has_cli_lifecycle(logged_command)


def test_operational_print_mutation_is_rejected() -> None:
    noisy = ast.parse("def workflow():\n    print('starting')\n")
    structured = ast.parse(
        "def workflow():\n    logs.info(LogEvent.PLAN_WRITTEN, {LogField.RUNS: 1})\n"
    )
    assert _print_calls(noisy.body[0])
    assert not _print_calls(structured.body[0])
    assert _logging_calls(structured.body[0])


def test_expensive_workflow_logging_mutation_is_rejected() -> None:
    silent = ast.parse("def run_workflow():\n    train_all_clients()\n")
    observable = ast.parse(
        "def run_workflow():\n"
        "    logs.info(LogEvent.RUN_STARTED, {LogField.RUNS: 1})\n"
        "    train_all_clients()\n"
        "    logs.info(LogEvent.RUN_FINISHED, {LogField.RUNS: 1})\n"
    )
    assert not _logging_calls(silent.body[0])
    assert len(_logging_calls(observable.body[0])) == 2


def test_silent_exception_mutation_is_rejected_but_reported_failure_is_valid() -> None:
    silent = ast.parse(
        "def workflow():\n    try:\n        run()\n    except Exception:\n        pass\n"
    )
    reported = ast.parse(
        "def workflow():\n"
        "    try:\n        run()\n"
        "    except Exception:\n        logs.error(LogEvent.COMMAND_FAILED, {})\n"
        "        raise\n"
    )
    assert _silently_caught(silent.body[0])
    assert not _silently_caught(reported.body[0])


def test_pure_helper_does_not_need_meaningless_logging() -> None:
    pure = ast.parse("def threshold(values):\n    return max(values)\n")
    assert not _has_cli_lifecycle(pure.body[0])
    assert not _silently_caught(pure.body[0])


def test_every_preprocessing_stage_function_logs_its_outcome() -> None:
    by_name, edges, _ = callgraph.build()
    emitting = _emitting_functions()
    stages = [
        name
        for name in by_name
        if name.endswith("_stage") or name in {"source_audit", "run_preprocess"}
    ]
    silent = [
        name
        for name in stages
        if not any(
            definition.name in emitting
            for definition in callgraph.reachable(by_name, edges, by_name[name])
        )
    ]
    assert stages
    assert not silent, silent


def test_log_calls_carry_timing_or_counts_for_long_operations() -> None:
    timed = {"SECONDS", "COUNT", "ROWS", "RUNS", "FILES", "ARMS"}
    offenders: list[str] = []
    for path in source_files(LOGS_MODULE):
        for call in _logging_calls(parse(path)):
            fields = call.args[1] if len(call.args) == 2 else None
            event = call.args[0] if call.args else None
            if not isinstance(event, ast.Attribute) or event.attr not in {
                "STAGE_BUILT",
                "RUN_FINISHED",
                "ARM_TRAINED",
                "LAMDA_LOADED",
                "ANDROZOO_SCANNED",
            }:
                continue
            keys = {
                key.attr for key in getattr(fields, "keys", []) if isinstance(key, ast.Attribute)
            }
            if not keys & timed:
                offenders.append(location(path, call.lineno))
    assert not offenders, offenders
