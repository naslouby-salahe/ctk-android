import ast
import re
import subprocess
from collections import Counter

from tests.architecture.source_index import (
    REPO_ROOT,
    SRC_ROOT,
    TESTS_ROOT,
    TYPES_MODULE,
    functions,
    location,
    parse,
    source_files,
)

ALLOWED_LITERALS = {0, 1, 2, -1, 0.5}
GENERIC_MODULES = {"utils", "helpers", "common", "misc", "core"}
FORBIDDEN_TOKENS = re.compile(
    r"TODO|FIXME|XXX|HACK|claim_registry|ClaimRegistry|claim_service|legacy|backward.compat"
    r"|deprecated|compat_shim",
    re.IGNORECASE,
)
DOCKER_FILES = {"dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"}


def _module_constants(tree: ast.Module) -> list[ast.Assign | ast.AnnAssign]:
    return [
        node
        for node in tree.body
        if isinstance(node, ast.Assign | ast.AnnAssign) and _target_name(node).isupper()
    ]


def _target_name(node: ast.Assign | ast.AnnAssign) -> str:
    target = node.targets[0] if isinstance(node, ast.Assign) else node.target
    return target.id if isinstance(target, ast.Name) else ""


def test_no_magic_numeric_literals_inside_function_bodies() -> None:
    offenders: list[str] = []
    for path in source_files():
        tree = parse(path)
        for function in functions(tree):
            for node in ast.walk(function):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, int | float)
                    and not isinstance(node.value, bool)
                    and node.value not in ALLOWED_LITERALS
                ):
                    offenders.append(f"{location(path, node.lineno)} literal {node.value}")
    assert not offenders, offenders


def test_named_constants_have_one_owner_and_are_used() -> None:
    names = Counter[str]()
    for path in source_files():
        names.update(_target_name(node) for node in _module_constants(parse(path)))
    duplicated = sorted(name for name, count in names.items() if count > 1)
    assert not duplicated, duplicated
    referenced = {
        node.id
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    dead = sorted(name for name in names if name not in referenced)
    assert not dead, dead


def test_no_unfinished_markers_shims_or_claim_infrastructure() -> None:
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{number}"
        for root in (SRC_ROOT, TESTS_ROOT.parent / "configs")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".yaml"}
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if FORBIDDEN_TOKENS.search(line)
    ]
    assert not offenders, offenders


def test_no_generic_dumping_ground_modules() -> None:
    offenders = [str(path) for path in SRC_ROOT.rglob("*.py") if path.stem in GENERIC_MODULES]
    assert not offenders, offenders


def test_no_docker_files_or_claims_directories() -> None:
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\n")
    offenders = [
        name
        for name in listed
        if name.rsplit("/", maxsplit=1)[-1].lower() in DOCKER_FILES
        or name.startswith(("claims/", "src/ctk_android/claims"))
    ]
    assert not offenders, offenders


def test_no_narrative_markdown_generation() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.endswith(".md")
    ]
    assert not offenders, offenders


def test_no_duplicate_function_bodies() -> None:
    seen: dict[str, str] = {}
    offenders: list[str] = []
    for path in source_files():
        for function in functions(parse(path)):
            body = function.body
            if len(body) < 3:
                continue
            fingerprint = "".join(ast.dump(statement) for statement in body)
            here = f"{location(path, function.lineno)} {function.name}"
            if fingerprint in seen:
                offenders.append(f"{here} duplicates {seen[fingerprint]}")
            seen[fingerprint] = here
    assert not offenders, offenders


def test_no_wrapper_only_functions() -> None:
    offenders: list[str] = []
    for path in source_files():
        for function in functions(parse(path)):
            body = [
                statement
                for statement in function.body
                if not (
                    isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                )
            ]
            if len(body) != 1 or not isinstance(body[0], ast.Return):
                continue
            call = body[0].value
            parameters = [arg.arg for arg in function.args.args if arg.arg != "self"]
            if (
                isinstance(call, ast.Call)
                and parameters
                and [a.id for a in call.args if isinstance(a, ast.Name)] == parameters
                and len(call.args) == len(parameters)
                and not call.keywords
            ):
                offenders.append(f"{location(path, function.lineno)} {function.name}")
    assert not offenders, offenders


def test_types_module_contains_no_logic_beyond_records() -> None:
    forbidden = [
        location(TYPES_MODULE, node.lineno)
        for node in ast.walk(parse(TYPES_MODULE))
        if isinstance(node, ast.Import | ast.ImportFrom)
        and getattr(node, "module", "") in {"ctk_android.config", "ctk_android.paths"}
    ]
    assert not forbidden, forbidden
