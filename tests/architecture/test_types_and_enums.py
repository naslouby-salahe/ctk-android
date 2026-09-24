import ast
from collections import Counter
from pathlib import Path

from tests.architecture.source_index import (
    CONFIG_MODULE,
    ENUMS_MODULE,
    REPO_ROOT,
    TYPES_MODULE,
    location,
    parse,
    source_files,
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
        if not values:
            continue
        if values in value_sets:
            duplicates.append(f"{enum.name} duplicates {value_sets[values]}")
        value_sets[values] = enum.name
    assert not duplicates, duplicates


def _used_enum_members() -> tuple[set[tuple[str, str]], set[str]]:
    members: set[tuple[str, str]] = set()
    iterated: set[str] = set()
    for path in source_files(ENUMS_MODULE):
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                members.add((node.value.id, node.attr))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                iterated.add(node.id)
    return members, iterated


def test_every_enum_member_is_used_by_code_or_configuration() -> None:
    configuration = " ".join(
        path.read_text(encoding="utf-8") for path in (REPO_ROOT / "configs").glob("*.yaml")
    )
    used, referenced = _used_enum_members()
    selectable = {node.id for node in ast.walk(parse(CONFIG_MODULE)) if isinstance(node, ast.Name)}
    unused = [
        f"{enum.name}.{member}"
        for enum in _enum_classes(ENUMS_MODULE)
        for member, value in _members(enum).items()
        if (enum.name, member) not in used
        and enum.name not in selectable
        and not (
            enum.name in referenced and (enum.name, member) not in used and _iterated(enum.name)
        )
        and value not in configuration
    ]
    assert not unused, unused


def _iterated(name: str) -> bool:
    for path in source_files(ENUMS_MODULE):
        for node in ast.walk(parse(path)):
            if (
                isinstance(node, ast.For)
                and isinstance(node.iter, ast.Name)
                and node.iter.id == name
            ):
                return True
            if (
                isinstance(node, ast.comprehension)
                and isinstance(node.iter, ast.Name)
                and node.iter.id == name
            ):
                return True
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"list", "set", "tuple", "sorted"}
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == name
            ):
                return True
    return False
