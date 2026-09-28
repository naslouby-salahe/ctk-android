import ast
import io
import tokenize
import tomllib
from pathlib import Path

import pytest

from tests.architecture.source_index import (
    PRODUCTION_ROOT,
    REPO_ROOT,
    TESTS_ROOT,
    assert_complete_scan,
    discover_source_files,
    scan_production_sources,
    scan_source_tree,
)


def _package_roots_are_scanned(scanner_root: Path, roots: set[Path]) -> bool:
    return all(root == scanner_root or scanner_root in root.parents for root in roots)


def _comment_and_docstring_lines(source: str) -> list[int]:
    offenders = [
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    ]
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            offenders.append(node.body[0].lineno)
    return sorted(offenders)


def test_python_project_code_has_no_comments_or_docstrings() -> None:
    roots = (REPO_ROOT / "src", TESTS_ROOT, REPO_ROOT / "typings")
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{line}"
        for root in roots
        for path in sorted((*root.rglob("*.py"), *root.rglob("*.pyi")))
        if path.is_file()
        for line in _comment_and_docstring_lines(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, offenders


def test_comment_and_docstring_scanner_detects_mutations() -> None:
    source = '# comment\ndef value():\n    """description"""\n    return 1\n'
    assert _comment_and_docstring_lines(source) == [1, 3]


def test_scanner_covers_every_production_python_file() -> None:
    expected = set(discover_source_files(PRODUCTION_ROOT))
    scanned = scan_production_sources()
    assert set(scanned) == expected
    assert all(isinstance(tree, ast.Module) for tree in scanned.values())


def test_every_wheel_package_root_is_inside_the_scanned_production_root() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_paths = project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    roots = {REPO_ROOT / package for package in package_paths}

    assert roots
    assert _package_roots_are_scanned(PRODUCTION_ROOT, roots)
    assert all(set(discover_source_files(root)) <= set(scan_production_sources()) for root in roots)
    assert not _package_roots_are_scanned(PRODUCTION_ROOT, {REPO_ROOT / "other_source_root"})


def test_new_nested_source_file_is_discovered(tmp_path: Path) -> None:
    nested = tmp_path / "new_package" / "deeply" / "nested.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("VALUE = 1\n", encoding="utf-8")

    assert discover_source_files(tmp_path) == [nested]
    assert set(scan_source_tree(tmp_path)) == {nested}


def test_scanner_fails_when_a_production_file_is_omitted(tmp_path: Path) -> None:
    first = tmp_path / "first.py"
    second = tmp_path / "second.py"
    first.write_text("first = 1\n", encoding="utf-8")
    second.write_text("second = 2\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="missing="):
        assert_complete_scan({first, second}, {first})


def test_scanner_fails_closed_on_parse_errors(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.py"
    invalid.write_text("def broken(:\n    pass\n", encoding="utf-8")

    with pytest.raises(SyntaxError):
        scan_source_tree(tmp_path)


def test_valid_source_is_scanned_without_blanket_rejection(tmp_path: Path) -> None:
    valid = tmp_path / "valid.py"
    valid.write_text("def value() -> int:\n    return 1\n", encoding="utf-8")

    scanned = scan_source_tree(tmp_path)
    assert scanned[valid].body
