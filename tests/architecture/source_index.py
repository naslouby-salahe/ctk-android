import ast
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "ctk_android"
TESTS_ROOT = REPO_ROOT / "tests"
TYPES_MODULE = SRC_ROOT / "types.py"
ENUMS_MODULE = SRC_ROOT / "enums.py"
CONFIG_MODULE = SRC_ROOT / "config.py"
PATHS_MODULE = SRC_ROOT / "paths.py"
CLI_MODULE = SRC_ROOT / "cli.py"


def source_files(*excluded: Path) -> list[Path]:
    return sorted(path for path in SRC_ROOT.rglob("*.py") if path not in excluded)


@cache
def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def location(path: Path, line: int) -> str:
    return f"{path.relative_to(REPO_ROOT)}:{line}"


def annotation_names(annotation: ast.expr | None) -> list[str]:
    if annotation is None:
        return []
    return [node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)]


def function_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.expr | None]:
    arguments = node.args
    return [
        *(arg.annotation for arg in arguments.posonlyargs),
        *(arg.annotation for arg in arguments.args),
        *(arg.annotation for arg in arguments.kwonlyargs),
        arguments.vararg.annotation if arguments.vararg else None,
        arguments.kwarg.annotation if arguments.kwarg else None,
        node.returns,
    ]


def functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def string_constants(tree: ast.AST) -> list[tuple[int, str]]:
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstrings.add(id(body[0].value))
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]
