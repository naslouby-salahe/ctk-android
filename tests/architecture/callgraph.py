import ast
from dataclasses import dataclass
from pathlib import Path

from tests.architecture.source_index import SRC_ROOT, parse, source_files


@dataclass(frozen=True)
class Definition:
    module: str
    name: str
    line: int
    path: Path
    kind: str = "function"


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)


def _has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr in names:
            return True
        if isinstance(target, ast.Name) and target.id in names:
            return True
    return False


def is_framework_entry(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # Only registered Typer commands are graph roots. Model validators are reached from
    # their constructed model; magic methods are reached from the operation that invokes them.
    return _has_decorator(node, {"command"})


def references(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            names.add(child.attr)
    return names


def build() -> tuple[dict[str, list[Definition]], dict[Definition, set[str]], list[Definition]]:
    by_name: dict[str, list[Definition]] = {}
    edges: dict[Definition, set[str]] = {}
    roots: list[Definition] = []
    for path in source_files():
        tree = parse(path)
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if (
                not isinstance(target, ast.Name)
                or not target.id[:1].isupper()
                or target.id.isupper()
            ):
                continue
            definition = Definition(module_name(path), target.id, node.lineno, path, "alias")
            by_name.setdefault(target.id, []).append(definition)
            edges[definition] = references(node.value) - {target.id}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                definition = Definition(module_name(path), node.name, node.lineno, path, "class")
                by_name.setdefault(node.name, []).append(definition)
                callbacks = {
                    method.name
                    for method in node.body
                    if isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                    and (
                        method.name == "__init__"
                        or _has_decorator(method, {"model_validator", "field_validator"})
                    )
                }
                type_dependencies = {name for base in node.bases for name in references(base)}
                type_dependencies.update(
                    name
                    for field in node.body
                    if isinstance(field, ast.AnnAssign)
                    for name in references(field.annotation)
                )
                edges[definition] = callbacks | type_dependencies
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                definition = Definition(module_name(path), node.name, node.lineno, path)
                by_name.setdefault(node.name, []).append(definition)
                edges[definition] = references(node) - {node.name} | _decorator_references(node)
                if is_framework_entry(node):
                    roots.append(definition)
    return by_name, edges, roots


def _decorator_references(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {name for decorator in node.decorator_list for name in references(decorator)}


def reachable(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> set[Definition]:
    seen: set[Definition] = set()
    pending = list(roots)
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for name in edges[current]:
            pending.extend(by_name.get(name, []))
    return seen


def shortest_paths(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> dict[Definition, tuple[Definition, ...]]:
    paths: dict[Definition, tuple[Definition, ...]] = {root: (root,) for root in roots}
    pending = list(roots)
    while pending:
        current = pending.pop(0)
        for name in sorted(edges[current]):
            for target in by_name.get(name, []):
                if target not in paths:
                    paths[target] = (*paths[current], target)
                    pending.append(target)
    return paths


def direct_callers(
    by_name: dict[str, list[Definition]], edges: dict[Definition, set[str]]
) -> dict[Definition, set[Definition]]:
    callers: dict[Definition, set[Definition]] = {definition: set() for definition in edges}
    for caller, names in edges.items():
        for name in names:
            for target in by_name.get(name, []):
                if caller != target:
                    callers[target].add(caller)
    return callers


def orphan_diagnostics(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> list[str]:
    paths = shortest_paths(by_name, edges, roots)
    callers = direct_callers(by_name, edges)
    diagnostics: list[str] = []
    for definition in sorted(set(edges) - set(paths), key=lambda item: (item.module, item.line)):
        where = f"{definition.module}.{definition.name} ({definition.path}:{definition.line})"
        direct = sorted(f"{item.module}.{item.name}" for item in callers[definition])
        root_names = sorted(f"{item.module}.{item.name}" for item in roots)
        diagnostics.append(
            f"{where}; direct callers={direct or ['none']}; CLI roots={root_names}; "
            "shortest CLI path=none; reason=not reachable from a registered CLI command"
        )
    return diagnostics
