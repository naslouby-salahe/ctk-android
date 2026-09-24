import ast

from ctk_android.cli import app
from ctk_android.enums import CliCommand
from tests.architecture import callgraph
from tests.architecture.source_index import CLI_MODULE, SRC_ROOT, location, parse

WORKFLOWS_PACKAGE = "ctk_android.workflows"
CLI_ALLOWED_PACKAGES = {"ctk_android.workflows", "ctk_android.config", "ctk_android.enums"}
CLI_ALLOWED_MODULES = {"ctk_android.paths", "ctk_android.types", "ctk_android.cli"}
COMMAND_WORKFLOW = {
    CliCommand.DOCTOR: "doctor_workflow",
    CliCommand.PREPROCESS: "preprocess_workflow",
    CliCommand.PLAN: "plan_workflow",
    CliCommand.SMOKE: "smoke_workflow",
    CliCommand.RUN: "run_workflow",
    CliCommand.STATUS: "status_workflow",
    CliCommand.REPORT: "report_workflow",
}


def _registered() -> set[str]:
    return {command.name for command in app.registered_commands if command.name}


def _command_functions() -> list[ast.FunctionDef]:
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


def _workflow_targets(function: ast.FunctionDef) -> set[str]:
    return {
        node.func.value.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id.endswith("_workflow")
    }


def test_registered_commands_are_exactly_the_public_cli() -> None:
    assert _registered() == {member.value for member in CliCommand}


def test_each_cli_command_delegates_to_its_single_workflow() -> None:
    actual = {
        command.name: _workflow_targets(node)
        for node in _command_functions()
        for command in [
            next(
                c
                for c in app.registered_commands
                if c.callback is not None and c.callback.__name__ == node.name
            )
        ]
    }
    expected = {command.value: {workflow} for command, workflow in COMMAND_WORKFLOW.items()}
    assert actual == expected


def test_every_workflow_module_is_used_by_the_cli() -> None:
    modules = {
        path.stem for path in (SRC_ROOT / "workflows").glob("*.py") if path.stem != "__init__"
    }
    aliased = {
        alias.name
        for node in ast.walk(parse(CLI_MODULE))
        if isinstance(node, ast.ImportFrom) and node.module == WORKFLOWS_PACKAGE
        for alias in node.names
    }
    assert modules == aliased, (modules, aliased)


def test_cli_holds_no_scientific_imports() -> None:
    offenders = [
        f"{location(CLI_MODULE, node.lineno)} imports {node.module}"
        for node in ast.walk(parse(CLI_MODULE))
        if isinstance(node, ast.ImportFrom)
        and node.module
        and node.module.startswith("ctk_android")
        and node.module not in CLI_ALLOWED_PACKAGES | CLI_ALLOWED_MODULES
    ]
    assert not offenders, offenders


def test_every_function_is_reachable_from_the_cli() -> None:
    by_name, edges, roots = callgraph.build()
    cli_roots = [
        root for root in roots if root.module == "cli" and root.name in _registered_names()
    ]
    reached = callgraph.reachable(by_name, edges, cli_roots)
    framework = {definition for definition in edges if definition in set(roots)}
    unreachable = sorted(
        f"{definition.module}.{definition.name}:{definition.line}"
        for definition in edges
        if definition not in reached and definition not in framework
    )
    assert not unreachable, unreachable


def _registered_names() -> set[str]:
    return {command.callback.__name__ for command in app.registered_commands if command.callback}
