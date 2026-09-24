import ast
from collections import Counter
from pathlib import Path

from tests.architecture.source_index import (
    ENUMS_MODULE,
    TYPES_MODULE,
    location,
    parse,
    source_files,
    string_constants,
)

GENERIC_CONSTRAINED_ALIASES = {
    "NonNegativeInt",
    "PositiveInt",
    "SignedInt",
    "NonNegativeFloat",
    "PositiveFloat",
    "FiniteFloat",
    "UnitInterval",
    "OpenUnitInterval",
}
ENUM_BASES = {"Enum", "StrEnum", "IntEnum", "Flag"}


def _is_alias_target(node: ast.Assign) -> bool:
    return (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id[:1].isupper()
        and not node.targets[0].id.isupper()
        and isinstance(node.value, ast.Subscript | ast.BinOp | ast.Name)
    )


def _enum_classes(path: Path) -> list[ast.ClassDef]:
    return [
        node
        for node in ast.walk(parse(path))
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id in ENUM_BASES for base in node.bases)
    ]


def _members(enum: ast.ClassDef) -> dict[str, str]:
    return {
        item.targets[0].id: item.value.value
        for item in enum.body
        if isinstance(item, ast.Assign)
        and isinstance(item.targets[0], ast.Name)
        and isinstance(item.value, ast.Constant)
        and isinstance(item.value.value, str)
    }


def test_type_aliases_are_defined_only_in_types_py() -> None:
    offenders = [
        location(path, node.lineno)
        for path in source_files(TYPES_MODULE)
        for node in parse(path).body
        if isinstance(node, ast.Assign) and _is_alias_target(node)
    ]
    assert not offenders, offenders


def test_constrained_scalars_and_newtypes_only_in_types_py() -> None:
    offenders: list[str] = []
    for path in source_files(TYPES_MODULE):
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                keywords = {keyword.arg for keyword in node.keywords}
                if node.func.id == "NewType" or (
                    node.func.id == "Field" and keywords & {"ge", "gt", "le", "lt"}
                ):
                    offenders.append(location(path, node.lineno))
    assert not offenders, offenders


def test_generic_constrained_aliases_are_not_referenced_outside_types_py() -> None:
    offenders = [
        f"{location(path, node.lineno)} references {node.id}"
        for path in source_files(TYPES_MODULE)
        for node in ast.walk(parse(path))
        if isinstance(node, ast.Name) and node.id in GENERIC_CONSTRAINED_ALIASES
    ]
    assert not offenders, offenders


def test_aliases_in_types_py_are_unique() -> None:
    names = Counter(
        node.targets[0].id
        for node in parse(TYPES_MODULE).body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and _is_alias_target(node)
    )
    duplicated = [name for name, count in names.items() if count > 1]
    assert not duplicated, duplicated


def test_enums_are_defined_only_in_enums_py() -> None:
    offenders = [
        f"{location(path, enum.lineno)} {enum.name}"
        for path in source_files(ENUMS_MODULE)
        for enum in _enum_classes(path)
    ]
    assert not offenders, offenders


def test_no_duplicate_enums_for_one_concept() -> None:
    enums = _enum_classes(ENUMS_MODULE)
    names = Counter(enum.name for enum in enums)
    assert not [name for name, count in names.items() if count > 1]
    value_sets: dict[frozenset[str], str] = {}
    duplicates: list[str] = []
    for enum in enums:
        values = frozenset(_members(enum).values())
        if values in value_sets:
            duplicates.append(f"{enum.name} duplicates {value_sets[values]}")
        value_sets[values] = enum.name
    assert not duplicates, duplicates


def test_no_categorical_string_literals_outside_enums_py() -> None:
    categorical = {
        value for enum in _enum_classes(ENUMS_MODULE) for value in _members(enum).values()
    }
    offenders = [
        f"{location(path, line)} hardcodes {text!r}"
        for path in source_files(ENUMS_MODULE)
        for line, text in string_constants(parse(path))
        if text in categorical
    ]
    assert not offenders, offenders
