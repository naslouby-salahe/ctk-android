from pathlib import Path

from tests.architecture.callgraph import (
    Definition,
    orphan_diagnostics,
    reachable,
    shortest_paths,
)


def _definition(name: str, kind: str = "function") -> Definition:
    return Definition("synthetic", name, 1, Path(f"{name}.py"), kind)


def test_orphan_function_mutation_is_reported() -> None:
    root, live, orphan = (_definition(name) for name in ("cli", "service", "orphan"))
    by_name: dict[str, list[Definition]] = {item.name: [item] for item in (root, live, orphan)}
    edges: dict[Definition, set[str]] = {
        root: {"service"},
        live: set(),
        orphan: set(),
    }

    report = orphan_diagnostics(by_name, edges, [root])

    assert len(report) == 1
    assert "synthetic.orphan" in report[0]
    assert "CLI roots=['synthetic.cli']" in report[0]
    assert "shortest CLI path=none" in report[0]


def test_helper_used_only_by_a_dead_function_remains_orphaned() -> None:
    root, dead, helper = (_definition(name) for name in ("cli", "dead", "helper"))
    by_name: dict[str, list[Definition]] = {item.name: [item] for item in (root, dead, helper)}
    edges: dict[Definition, set[str]] = {root: set(), dead: {"helper"}, helper: set()}

    report = orphan_diagnostics(by_name, edges, [root])

    assert len(report) == 2
    assert any(
        "synthetic.helper" in item and "direct callers=['synthetic.dead']" in item
        for item in report
    )


def test_dead_class_and_its_method_are_both_reported() -> None:
    root = _definition("cli")
    dead_class = _definition("DeadClass", "class")
    dead_method = _definition("method")
    by_name: dict[str, list[Definition]] = {
        "cli": [root],
        "DeadClass": [dead_class],
        "method": [dead_method],
    }
    edges: dict[Definition, set[str]] = {
        root: set(),
        dead_class: {"method"},
        dead_method: set(),
    }

    report = orphan_diagnostics(by_name, edges, [root])

    assert len(report) == 2
    assert any("synthetic.DeadClass" in item for item in report)
    assert any("synthetic.method" in item for item in report)


def test_disconnected_module_mutation_is_reported() -> None:
    root = _definition("cli")
    module = _definition("dead_module", "module")
    by_name: dict[str, list[Definition]] = {"cli": [root], "dead_module": [module]}
    edges: dict[Definition, set[str]] = {root: set(), module: set()}

    report = orphan_diagnostics(by_name, edges, [root])

    assert len(report) == 1
    assert "synthetic.dead_module" in report[0]


def test_valid_cli_path_and_shortest_distance_are_preserved() -> None:
    root, service, leaf = (_definition(name) for name in ("cli", "service", "leaf"))
    by_name: dict[str, list[Definition]] = {item.name: [item] for item in (root, service, leaf)}
    edges: dict[Definition, set[str]] = {
        root: {"service"},
        service: {"leaf"},
        leaf: set(),
    }

    paths = shortest_paths(by_name, edges, [root])

    assert reachable(by_name, edges, [root]) == {root, service, leaf}
    assert paths[leaf] == (root, service, leaf)
    assert not orphan_diagnostics(by_name, edges, [root])
