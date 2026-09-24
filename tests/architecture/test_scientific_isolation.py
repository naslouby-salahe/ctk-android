import ast

from tests.architecture.source_index import SRC_ROOT, location, parse

TRAINING_MODULES = ("experiment/training.py", "experiment/models.py", "data/identity.py")
FORBIDDEN_ROLES = {"TEST", "CALIBRATION"}
REPORTING_FORBIDDEN_IMPORTS = {
    "ctk_android.experiment.training",
    "ctk_android.experiment.models",
    "ctk_android.workflows.run",
}


def _role_references(relative: str) -> list[str]:
    path = SRC_ROOT / relative
    return [
        f"{location(path, node.lineno)} references SplitRole.{node.attr}"
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "SplitRole"
        and node.attr in FORBIDDEN_ROLES
    ]


def test_training_code_never_references_test_or_calibration_roles() -> None:
    offenders = [hit for relative in TRAINING_MODULES for hit in _role_references(relative)]
    assert not offenders, offenders


def test_training_row_selection_reads_only_the_fit_role() -> None:
    path = SRC_ROOT / "experiment" / "exposure.py"
    function = next(
        node
        for node in ast.walk(parse(path))
        if isinstance(node, ast.FunctionDef) and node.name == "training_orders"
    )
    roles = {
        node.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "SplitRole"
    }
    assert roles == {"FIT"}


def test_thresholds_use_only_benign_calibration_scores() -> None:
    path = SRC_ROOT / "experiment" / "thresholds.py"
    names = {node.id for node in ast.walk(parse(path)) if isinstance(node, ast.Name)}
    assert "SplitRole" not in names
    tree = parse(path)
    calibrate = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "calibrate"
    )
    assert [arg.arg for arg in calibrate.args.args] == ["benign_scores", "alpha", "min_exceedances"]


def test_reporting_never_imports_training_or_run_workflows() -> None:
    offenders: list[str] = []
    for path in [*(SRC_ROOT / "reporting").glob("*.py"), SRC_ROOT / "workflows" / "report.py"]:
        if not path.exists():
            continue
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.ImportFrom) and node.module in REPORTING_FORBIDDEN_IMPORTS:
                offenders.append(location(path, node.lineno))
    assert not offenders, offenders


def test_partitions_assign_by_group_never_by_row() -> None:
    path = SRC_ROOT / "data" / "partitions.py"
    function = next(
        node
        for node in ast.walk(parse(path))
        if isinstance(node, ast.FunctionDef) and node.name == "assign_roles"
    )
    assert "group_ids" in {arg.arg for arg in function.args.args}


def test_novelty_descriptors_use_only_training_rows() -> None:
    path = SRC_ROOT / "analysis" / "novelty.py"
    roles = {
        node.attr
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "SplitRole"
    }
    assert roles == {"FIT"}
