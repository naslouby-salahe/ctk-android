import ast
from pathlib import Path

from tests.architecture.source_index import (
    TYPES_MODULE,
    annotation_names,
    function_annotations,
    functions,
    location,
    parse,
    source_files,
)

FORBIDDEN_PRIMITIVES = {"int", "float", "str", "object", "Any", "bool", "bytes", "complex"}
FORBIDDEN_ARRAYS = {"ndarray", "NDArray"}
FORBIDDEN_INLINE_CONTAINERS = {"dict", "Mapping", "Sequence", "Callable"}
UNPARAMETERISED_CONTAINERS = {"dict", "list", "tuple", "set", "frozenset"}
HIDING_CALLS = {"float", "int", "str", "cast"}
PLOT_ANY_METHODS = {
    "PlotAxes": {
        "bar",
        "plot",
        "scatter",
        "errorbar",
        "imshow",
        "annotate",
        "axhline",
        "axvline",
        "set_ylim",
        "tick_params",
        "grid",
        "set_xticks",
        "set_yticks",
        "set_xlabel",
        "set_ylabel",
        "set_title",
        "set_xscale",
        "legend",
    },
    "PlotFigure": {"add_subplot", "suptitle", "subplots_adjust", "colorbar", "savefig"},
}
PLOT_OBJECT_RETURN_METHODS = {
    "PlotAxes": PLOT_ANY_METHODS["PlotAxes"],
    "PlotFigure": PLOT_ANY_METHODS["PlotFigure"] - {"add_subplot"},
}


def _outside_types() -> list[Path]:
    return source_files(TYPES_MODULE)


def _bare_container(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    return any(
        isinstance(node, ast.Name)
        and node.id in UNPARAMETERISED_CONTAINERS
        and not _is_subscript_base(annotation, node)
        for node in ast.walk(annotation)
    )


def _is_subscript_base(root: ast.expr, name: ast.Name) -> bool:
    return any(isinstance(node, ast.Subscript) and node.value is name for node in ast.walk(root))


def test_no_primitive_function_boundaries_outside_types_py() -> None:
    offenders = [
        f"{location(path, node.lineno)} {node.name} uses raw '{name}'"
        for path in _outside_types()
        for node in functions(parse(path))
        for annotation in function_annotations(node)
        for name in annotation_names(annotation)
        if name in FORBIDDEN_PRIMITIVES
    ]
    assert not offenders, offenders


def test_no_primitive_variable_or_field_annotations_outside_types_py() -> None:
    offenders = [
        f"{location(path, node.lineno)} uses raw '{name}'"
        for path in _outside_types()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.AnnAssign)
        for name in annotation_names(node.annotation)
        if name in FORBIDDEN_PRIMITIVES
    ]
    assert not offenders, offenders


def test_no_bare_container_annotations() -> None:
    offenders = [
        f"{location(path, node.lineno)} {node.name}"
        for path in source_files()
        for node in functions(parse(path))
        for annotation in function_annotations(node)
        if _bare_container(annotation)
    ]
    assert not offenders, offenders


def test_no_any_or_object_imports_outside_types_py() -> None:
    offenders = [
        location(path, node.lineno)
        for path in _outside_types()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.ImportFrom)
        and node.module == "typing"
        and any(alias.name == "Any" for alias in node.names)
    ]
    assert not offenders, offenders


def _unapproved_any_sites(tree: ast.Module) -> list[int]:
    allowed: set[int] = set()
    for owner in ast.walk(tree):
        if not isinstance(owner, ast.ClassDef) or owner.name not in PLOT_ANY_METHODS:
            continue
        for method in owner.body:
            if (
                not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                or method.name not in PLOT_ANY_METHODS[owner.name]
            ):
                continue
            for argument in (method.args.vararg, method.args.kwarg):
                if (
                    argument
                    and isinstance(argument.annotation, ast.Name)
                    and argument.annotation.id == "Any"
                ):
                    allowed.add(id(argument.annotation))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "Any" and id(node) not in allowed
    ]


def test_any_is_confined_to_variadic_plotting_parameters() -> None:
    assert not _unapproved_any_sites(parse(TYPES_MODULE))
    mutation = ast.parse("class PlotAxes:\n    def plot(self, *args: Any) -> Any: ...\n")
    assert _unapproved_any_sites(mutation)
    non_variadic = ast.parse("class PlotAxes:\n    def plot(self, args: Any) -> object: ...\n")
    assert _unapproved_any_sites(non_variadic)
    unknown_method = ast.parse("class PlotAxes:\n    def draw(self, *args: Any) -> object: ...\n")
    assert _unapproved_any_sites(unknown_method)


def _unapproved_object_sites(tree: ast.Module) -> list[int]:
    allowed: set[int] = set()
    for owner in ast.walk(tree):
        if not isinstance(owner, ast.ClassDef) or owner.name not in PLOT_OBJECT_RETURN_METHODS:
            continue
        for method in owner.body:
            if (
                isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                and method.name in PLOT_OBJECT_RETURN_METHODS[owner.name]
                and isinstance(method.returns, ast.Name)
                and method.returns.id == "object"
            ):
                allowed.add(id(method.returns))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "object" and id(node) not in allowed
    ]


def test_opaque_object_returns_stay_at_plotting_boundary() -> None:
    assert not _unapproved_object_sites(parse(TYPES_MODULE))
    mutation = ast.parse("class Payload:\n    data: object\n")
    assert _unapproved_object_sites(mutation)


def test_no_type_hiding_calls() -> None:
    offenders = [
        f"{location(path, node.lineno)} calls {node.func.id}()"
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in HIDING_CALLS
    ]
    assert not offenders, offenders


def test_no_type_suppression_comments() -> None:
    offenders = [
        f"{path.name}:{number}"
        for path in source_files()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if "type: ignore" in line or "pyright: ignore" in line or "noqa" in line
    ]
    assert not offenders, offenders


def test_no_value_attribute_escape_from_enums() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Attribute) and node.attr == "value"
    ]
    assert not offenders, offenders


def test_no_wrapper_only_classes() -> None:
    offenders: list[str] = []
    for path in source_files():
        local_classes = {
            node.name for node in ast.walk(parse(path)) if isinstance(node, ast.ClassDef)
        }
        for node in ast.walk(parse(path)):
            if not isinstance(node, ast.ClassDef):
                continue
            fields = [item for item in node.body if isinstance(item, ast.AnnAssign)]
            methods = [item for item in node.body if isinstance(item, ast.FunctionDef)]
            sibling_bases = {
                base.id
                for base in node.bases
                if isinstance(base, ast.Name) and base.id in local_classes
            }
            if len(fields) == 1 and not methods and not sibling_bases:
                offenders.append(f"{location(path, node.lineno)} {node.name}")
    assert not offenders, offenders


def _annotations_outside_types() -> list[tuple[str, ast.expr]]:
    found: list[tuple[str, ast.expr]] = []
    for path in _outside_types():
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                where = f"{location(path, node.lineno)} {node.name}"
                found.extend((where, a) for a in function_annotations(node) if a is not None)
            elif isinstance(node, ast.AnnAssign):
                found.append((location(path, node.lineno), node.annotation))
    return found


def _attribute_names(annotation: ast.expr) -> set[str]:
    return {node.attr for node in ast.walk(annotation) if isinstance(node, ast.Attribute)}


def _fixed_tuple(annotation: ast.expr) -> bool:
    for node in ast.walk(annotation):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "tuple"
            and isinstance(node.slice, ast.Tuple)
        ):
            elements = node.slice.elts
            variadic = (
                len(elements) == 2
                and isinstance(elements[1], ast.Constant)
                and elements[1].value is Ellipsis
            )
            if not variadic:
                return True
    return False


def test_no_raw_numpy_arrays_outside_types_py() -> None:
    offenders = [
        f"{where} uses raw numpy array annotation"
        for where, annotation in _annotations_outside_types()
        if (set(annotation_names(annotation)) | _attribute_names(annotation)) & FORBIDDEN_ARRAYS
    ]
    assert not offenders, offenders


def test_no_anonymous_fixed_tuples_as_domain_bundles() -> None:
    offenders = [
        f"{where}: {ast.unparse(annotation)}"
        for where, annotation in _annotations_outside_types()
        if _fixed_tuple(annotation)
    ]
    assert not offenders, offenders


def test_no_inline_mapping_or_callable_annotations() -> None:
    offenders = [
        f"{where}: {ast.unparse(annotation)}"
        for where, annotation in _annotations_outside_types()
        if set(annotation_names(annotation)) & FORBIDDEN_INLINE_CONTAINERS
    ]
    assert not offenders, offenders


def test_type_aliases_in_types_py_are_all_referenced() -> None:
    aliases = {
        node.targets[0].id
        for node in parse(TYPES_MODULE).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id[:1].isupper()
        and not node.targets[0].id.isupper()
    }
    referenced = {
        node.id
        for path in source_files()
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    unused = sorted(alias for alias in aliases if alias not in referenced)
    assert not unused, unused


GENERIC_ARRAY_ALIASES = {
    "FloatArray",
    "Float32Array",
    "IntArray",
    "BoolArray",
    "ByteMatrix",
    "ObjectArray",
}
RAW_FRAME_TYPES = {"DataFrame", "Series", "LazyFrame"}


def test_signatures_use_semantic_array_aliases_not_generic_ones() -> None:
    offenders = [
        f"{where}: {ast.unparse(annotation)}"
        for where, annotation in _annotations_outside_types()
        if set(annotation_names(annotation)) & GENERIC_ARRAY_ALIASES
    ]
    assert not offenders, offenders


def test_signatures_use_named_table_aliases_not_raw_polars_types() -> None:
    offenders = [
        f"{where}: {ast.unparse(annotation)}"
        for where, annotation in _annotations_outside_types()
        if (_attribute_names(annotation) | set(annotation_names(annotation))) & RAW_FRAME_TYPES
    ]
    assert not offenders, offenders
