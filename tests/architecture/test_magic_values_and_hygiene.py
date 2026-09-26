import ast
import re
import subprocess

from tests.architecture.source_index import (
    ENUMS_MODULE,
    REPO_ROOT,
    SRC_ROOT,
    TESTS_ROOT,
    TYPES_MODULE,
    functions,
    location,
    parse,
    source_files,
    string_constants,
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


def _domain_string_comparisons(tree: ast.AST) -> list[int]:
    offenders: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            if any(
                isinstance(value, ast.Constant) and isinstance(value.value, str)
                for expression in [node.left, *node.comparators]
                for value in ast.walk(expression)
            ):
                offenders.append(node.lineno)
        elif isinstance(node, ast.Match) and any(
            isinstance(pattern, ast.MatchValue)
            and isinstance(pattern.value, ast.Constant)
            and isinstance(pattern.value.value, str)
            for case in node.cases
            for pattern in ast.walk(case.pattern)
        ):
            offenders.append(node.lineno)
    return offenders


def _semantic_constant_assignments(tree: ast.Module) -> list[str]:
    return [
        _target_name(node)
        for node in _module_constants(tree)
        if (
            (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))
            or isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
        )
    ]


def test_numeric_literals_live_in_enums_or_are_trivial() -> None:
    offenders = [
        f"{location(path, node.lineno)} literal {node.value}"
        for path in source_files(ENUMS_MODULE, TYPES_MODULE)
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
        and node.value not in ALLOWED_LITERALS
    ]
    assert not offenders, offenders


def test_constants_are_enum_members_not_module_level_names() -> None:
    offenders = [
        f"{location(path, node.lineno)} {_target_name(node)}"
        for path in source_files(ENUMS_MODULE)
        for node in _module_constants(parse(path))
    ]
    assert not offenders, offenders


def test_synthetic_magic_string_comparison_mutations_are_detected() -> None:
    snippets = (
        'if policy == "local":\n    pass\n',
        'match status:\n    case "done":\n        pass\n',
        'if strategy in {"a", "b"}:\n    pass\n',
        'if mode == "confirmatory":\n    pass\n',
        'if objective == "threshold_raise":\n    pass\n',
        'if dataset == "androzoo":\n    pass\n',
    )
    for snippet in snippets:
        assert _domain_string_comparisons(ast.parse(snippet))


def test_free_form_string_does_not_count_as_a_domain_comparison() -> None:
    tree = ast.parse('message = "analysis complete"\n')
    assert not _domain_string_comparisons(tree)


def test_synthetic_semantic_constant_mutations_are_detected() -> None:
    tree = ast.parse('LOCAL_POLICY = "local"\nSTRATEGIES = ("a", "b")\n')
    assert _semantic_constant_assignments(tree) == ["LOCAL_POLICY", "STRATEGIES"]


def test_mathematical_constant_is_not_misclassified_as_a_domain_choice() -> None:
    tree = ast.parse("PI = 3.141592653589793\n")
    assert not _semantic_constant_assignments(tree)


def test_no_string_literals_outside_enums_py() -> None:
    def module_strings(tree: ast.Module) -> list[tuple[int, str]]:
        newtype_names = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "NewType"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        return [
            (line, value) for line, value in string_constants(tree) if value not in newtype_names
        ]

    offenders = [
        f"{location(path, line)} hardcodes {text!r}"
        for path in source_files(ENUMS_MODULE)
        for line, text in module_strings(parse(path))
    ]
    assert not offenders, offenders


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
        for path in source_files(ENUMS_MODULE)
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
