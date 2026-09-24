import ast
import re
import subprocess

import yaml
from pydantic import BaseModel

from ctk_android.config import Config, ExperimentsConfig
from ctk_android.enums import ExperimentName
from tests.architecture.source_index import (
    CONFIG_MODULE,
    ENUMS_MODULE,
    PATHS_MODULE,
    REPO_ROOT,
    SRC_ROOT,
    location,
    parse,
    source_files,
    string_constants,
)

APPROVED_CONFIGS = {"data.yaml", "experiments.yaml", "project.yaml", "statistics.yaml"}
MAX_YAML_FILES = 6
FILE_LITERAL = re.compile(r"\.(parquet|json|npy|csv|gz|pt|yaml|yml|md)$|/")
REPOSITORY_ROOTS = {"outputs", "results", "configs", "data", "src", "docs", "quality", "tests"}


def _tracked_yaml() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.yaml", "*.yml"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [name for name in listed if not name.startswith((".venv", "docs/"))]


def test_yaml_is_parsed_only_by_the_config_layer() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files(CONFIG_MODULE)
        for node in ast.walk(parse(path))
        if (isinstance(node, ast.Import) and any(alias.name == "yaml" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "yaml")
    ]
    assert not offenders, offenders


def test_yaml_surface_is_limited_and_approved() -> None:
    tracked = _tracked_yaml()
    assert len(tracked) <= MAX_YAML_FILES, tracked
    configs = {name.split("/")[-1] for name in tracked if name.startswith("configs/")}
    assert configs <= APPROVED_CONFIGS, configs


def test_experiment_enum_and_configuration_agree() -> None:
    document = yaml.safe_load((REPO_ROOT / "configs" / "experiments.yaml").read_text("utf-8"))
    assert set(document["experiments"]) == {member.value for member in ExperimentName}


def test_every_configuration_field_is_consumed() -> None:
    referenced = {
        node.attr
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Attribute)
    }
    fields: set[str] = set()
    for model in _models(Config):
        fields |= set(model.model_fields)
    unused = sorted(fields - referenced - {"model_config"})
    assert not unused, unused


def _models(root: type[BaseModel]) -> list[type[BaseModel]]:
    found: list[type[BaseModel]] = []
    pending: list[type[BaseModel]] = [root, ExperimentsConfig]
    while pending:
        model = pending.pop()
        if model in found:
            continue
        found.append(model)
        for field in model.model_fields.values():
            pending.extend(
                argument
                for argument in _flatten(field.annotation)
                if isinstance(argument, type) and issubclass(argument, BaseModel)
            )
    return found


def _flatten(annotation: object) -> list[object]:
    arguments: tuple[object, ...] = getattr(annotation, "__args__", ())
    return [annotation, *(leaf for argument in arguments for leaf in _flatten(argument))]


def test_configuration_models_have_no_hidden_defaults() -> None:
    offenders = [
        f"{location(CONFIG_MODULE, node.lineno)}"
        for node in ast.walk(parse(CONFIG_MODULE))
        if isinstance(node, ast.AnnAssign) and node.value is not None
    ]
    assert not offenders, offenders


def test_no_numeric_defaults_in_function_signatures() -> None:
    offenders = [
        f"{location(path, node.lineno)} {node.name}"
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.FunctionDef)
        for default in [*node.args.defaults, *node.args.kw_defaults]
        if isinstance(default, ast.Constant)
        and isinstance(default.value, int | float)
        and not isinstance(default.value, bool)
    ]
    assert not offenders, offenders


def test_path_literals_and_construction_belong_to_paths_py() -> None:
    offenders: list[str] = []
    for path in source_files(PATHS_MODULE, ENUMS_MODULE):
        tree = parse(path)
        for line, text in string_constants(tree):
            if FILE_LITERAL.search(text) or text in REPOSITORY_ROOTS:
                offenders.append(f"{location(path, line)} literal {text!r}")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Div)
                and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str)
            ):
                offenders.append(f"{location(path, node.lineno)} manual path concatenation")
    assert not offenders, offenders


def test_results_are_referenced_only_by_the_promotion_module() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files(PATHS_MODULE)
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Attribute)
        and node.attr.startswith("results")
        and path.name != "promotion.py"
    ]
    assert not offenders, offenders


def test_source_tree_layout_matches_the_approved_areas() -> None:
    packages = {
        path.name for path in SRC_ROOT.iterdir() if path.is_dir() and path.name != "__pycache__"
    }
    assert packages <= {"data", "experiment", "analysis", "reporting", "workflows"}, packages
