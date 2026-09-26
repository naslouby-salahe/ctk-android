import ast
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "ctk_android"
PRODUCTION_ROOT = REPO_ROOT / "src"
TESTS_ROOT = REPO_ROOT / "tests"
TYPES_MODULE = SRC_ROOT / "types.py"
ENUMS_MODULE = SRC_ROOT / "enums.py"
CONFIG_MODULE = SRC_ROOT / "config.py"
PATHS_MODULE = SRC_ROOT / "paths.py"
CLI_MODULE = SRC_ROOT / "cli.py"


def discover_source_files(root: Path = PRODUCTION_ROOT) -> list[Path]:
    """Discover every Python source below the repository's production source root."""
    if not root.is_dir():
        raise FileNotFoundError(f"production source root does not exist: {root}")
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def assert_complete_scan(expected: set[Path], scanned: set[Path]) -> None:
    """Fail closed when source discovery and the architecture scanner diverge."""
    missing = sorted(path.as_posix() for path in expected - scanned)
    unexpected = sorted(path.as_posix() for path in scanned - expected)
    if missing or unexpected:
        raise AssertionError(
            f"architecture source scan mismatch; missing={missing}, unexpected={unexpected}"
        )


def scan_source_tree(root: Path) -> dict[Path, ast.Module]:
    """Parse an entire source tree; syntax or read failures are fatal."""
    expected = set(discover_source_files(root))
    scanned = {path: parse(path) for path in sorted(expected)}
    assert_complete_scan(expected, set(scanned))
    return scanned


def scan_production_sources() -> dict[Path, ast.Module]:
    """Parse the complete production tree; syntax or read failures are fatal."""
    return scan_source_tree(PRODUCTION_ROOT)


def source_files(*excluded: Path) -> list[Path]:
    return [path for path in discover_source_files() if path not in excluded]


@cache
def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def location(path: Path, line: int) -> str:
    return f"{path.relative_to(REPO_ROOT)}:{line}"


def annotation_names(annotation: ast.expr | None) -> list[str]:
    if annotation is None:
        return []
    names: list[str] = []
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    return names


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
