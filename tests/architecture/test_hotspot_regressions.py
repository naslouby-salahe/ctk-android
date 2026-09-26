import ast
from pathlib import Path

from tests.architecture.source_index import REPO_ROOT, scan_production_sources

MAX_ARGUMENTS = 10
MAX_BRANCH_COMPLEXITY = 30
MAX_FUNCTION_CALLS = 125
MAX_FUNCTION_LINES = 220
MAX_MODULE_DEPENDENCIES = 20


def _function_metrics(tree: ast.AST) -> list[tuple[str, int, int, int, int]]:
    metrics: list[tuple[str, int, int, int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        arguments = (
            len(node.args.posonlyargs)
            + len(node.args.args)
            + len(node.args.kwonlyargs)
            + (node.args.vararg is not None)
            + (node.args.kwarg is not None)
        )
        complexity = 1 + sum(
            isinstance(child, ast.If | ast.For | ast.AsyncFor | ast.While | ast.ExceptHandler)
            for child in ast.walk(node)
        )
        complexity += sum(
            max(len(child.values) - 1, 0)
            for child in ast.walk(node)
            if isinstance(child, ast.BoolOp)
        )
        complexity += sum(
            len(child.cases) for child in ast.walk(node) if isinstance(child, ast.Match)
        )
        calls = sum(isinstance(child, ast.Call) for child in ast.walk(node))
        lines = (node.end_lineno or node.lineno) - node.lineno + 1
        metrics.append((node.name, arguments, complexity, calls, lines))
    return metrics


def _dependency_graph(sources: dict[Path, ast.Module]) -> dict[str, set[str]]:
    root = REPO_ROOT / "src" / "ctk_android"
    modules: dict[str, Path] = {}
    for path in sources:
        if not path.is_relative_to(root):
            continue
        relative = path.relative_to(root).with_suffix("")
        parts = relative.parent.parts if relative.name == "__init__" else relative.parts
        module = "ctk_android" if not parts else "ctk_android." + ".".join(parts)
        modules[module] = path
    graph: dict[str, set[str]] = {module: set() for module in modules}
    for module, path in modules.items():
        tree = sources[path]
        graph[module].update(_dependency_names(tree) & modules.keys())
    return graph


def _dependency_names(tree: ast.AST) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
            targets.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
    return targets


def _cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    found: set[tuple[str, ...]] = set()
    active: list[str] = []
    complete: set[str] = set()

    def visit(module: str) -> None:
        if module in active:
            cycle = [*active[active.index(module) :], module]
            found.add(tuple(cycle))
            return
        if module in complete:
            return
        active.append(module)
        for dependency in sorted(graph[module]):
            visit(dependency)
        active.pop()
        complete.add(module)

    for module in sorted(graph):
        visit(module)
    return sorted(found)


def _violations(tree: ast.AST) -> list[str]:
    found: list[str] = []
    for name, arguments, complexity, calls, lines in _function_metrics(tree):
        if arguments > MAX_ARGUMENTS:
            found.append(f"{name}: {arguments} arguments")
        if complexity > MAX_BRANCH_COMPLEXITY:
            found.append(f"{name}: complexity {complexity}")
        if calls > MAX_FUNCTION_CALLS:
            found.append(f"{name}: {calls} calls")
        if lines > MAX_FUNCTION_LINES:
            found.append(f"{name}: {lines} lines")
    return found


def test_production_functions_stay_within_reviewed_hotspot_limits() -> None:
    sources = scan_production_sources()
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{node.lineno} {problem}"
        for path, tree in sources.items()
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for problem in _violations(node)
    ]
    assert not offenders, offenders


def test_production_dependency_graph_has_no_cycles() -> None:
    graph = _dependency_graph(scan_production_sources())
    cycles = _cycles(graph)
    assert not cycles, cycles
    broad_dependencies = {
        module: sorted(dependencies)
        for module, dependencies in graph.items()
        if len(dependencies) > MAX_MODULE_DEPENDENCIES
    }
    assert not broad_dependencies, broad_dependencies


def test_mutation_examples_trip_argument_complexity_size_and_fanout_guards() -> None:
    too_many_arguments = ast.parse("def broken(a,b,c,d,e,f,g,h,i,j,k):\n    return None\n")
    too_many_calls = ast.parse(
        "def broken():\n" + "\n".join(f"    call_{index}()" for index in range(126))
    )
    too_complex = ast.parse(
        "def broken(value):\n" + "\n".join(f"    if value == {index}: pass" for index in range(31))
    )
    too_large = ast.parse("def broken():\n" + "\n".join("    pass" for _ in range(221)))

    for mutation in (too_many_arguments, too_many_calls, too_complex, too_large):
        assert _violations(mutation)


def test_valid_small_helper_is_not_rejected_by_hotspot_guards() -> None:
    helper = ast.parse("def value(item):\n    return item\n")
    assert not _violations(helper)


def test_dependency_cycle_mutation_is_detected() -> None:
    assert _cycles({"a": {"b"}, "b": {"a"}})
    assert not _cycles({"a": {"b"}, "b": set()})


def test_new_god_module_import_mutation_is_detected() -> None:
    source = ast.parse("\n".join(f"import ctk_android.module_{index}" for index in range(21)))
    assert len(_dependency_names(source)) > MAX_MODULE_DEPENDENCIES
