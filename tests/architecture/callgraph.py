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
    dunder = node.name.startswith("__") and node.name.endswith("__")
    return dunder or _has_decorator(node, {"command", "model_validator", "field_validator"})


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
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
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
