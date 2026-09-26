import ast
from dataclasses import dataclass
from pathlib import Path

from tests.architecture.source_index import SRC_ROOT, parse, source_files


@dataclass(frozen=True)
class Definition:
    module: str
    name: str
    line: int
    path: Path
    kind: str = "function"


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)


def _has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr in names:
            return True
        if isinstance(target, ast.Name) and target.id in names:
            return True
    return False


def is_framework_entry(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # Only registered Typer commands are graph roots. Model validators are reached from
    # their constructed model; magic methods are reached from the operation that invokes them.
    return _has_decorator(node, {"command"})


def references(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            names.add(child.attr)
    return names


def loaded_names(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }


def _scope_nodes(node: ast.AST) -> list[ast.AST]:
    pending = [node]
    found: list[ast.AST] = []
    while pending:
        current = pending.pop()
        found.append(current)
        if current is not node and isinstance(
            current, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
        ):
            continue
        pending.extend(ast.iter_child_nodes(current))
    return found


def _local_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    arguments = node.args
    names = {
        argument.arg
        for argument in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
    }
    if arguments.vararg:
        names.add(arguments.vararg.arg)
    if arguments.kwarg:
        names.add(arguments.kwarg.arg)
    for child in _scope_nodes(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
        elif isinstance(child, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in child.names)
        elif isinstance(child, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in child.names)
        elif child is not node and isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(child.name)
    return names


def _enum_classes(paths: list[Path]) -> set[str]:
    enum_bases = {"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag"}
    return {
        node.name
        for path in paths
        for node in ast.walk(parse(path))
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id in enum_bases for base in node.bases)
    }


def _protocol_class(node: ast.ClassDef) -> bool:
    return any(
        (isinstance(base, ast.Name) and base.id == "Protocol")
        or (isinstance(base, ast.Attribute) and base.attr == "Protocol")
        for base in node.bases
    )


def _import_targets(tree: ast.Module) -> dict[str, str]:
    """Map local import names to their fully qualified project targets."""
    targets: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("ctk_android")
        ):
            for alias in node.names:
                local = alias.asname or alias.name
                base = (
                    "" if node.module == "ctk_android" else node.module.removeprefix("ctk_android.")
                )
                targets[local] = ".".join(part for part in (base, alias.name) if part)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("ctk_android."):
                    local = alias.asname or alias.name.split(".")[0]
                    targets[local] = alias.name.removeprefix("ctk_android.")
    return targets


def _attribute_chain(node: ast.AST) -> list[str]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return list(reversed(parts))


def _qualified_definition(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    module: str,
    parents: dict[ast.AST, ast.AST],
) -> tuple[str, bool]:
    scope: list[str] = []
    nested_function = False
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef | ast.AsyncFunctionDef):
            scope.append(parent.name)
            nested_function = True
        elif isinstance(parent, ast.ClassDef):
            scope.append(parent.name)
        parent = parents.get(parent)
    return ".".join((module, *reversed(scope), node.name)), nested_function


def _resolve_name(
    name: str, module: str, imports: dict[str, str], by_name: dict[str, list[Definition]]
) -> str | None:
    imported = imports.get(name)
    if imported is not None:
        return imported
    local = f"{module}.{name}"
    if local in by_name:
        return local
    candidates = by_name.get(name, [])
    return name if len(candidates) == 1 else None


def _class_target(
    expression: ast.AST | None,
    module: str,
    imports: dict[str, str],
    class_names: set[str],
) -> str | None:
    if isinstance(expression, ast.Name):
        imported = imports.get(expression.id)
        local = f"{module}.{expression.id}"
        candidate = imported or local
        return candidate if candidate in class_names else None
    if isinstance(expression, ast.Attribute):
        chain = _attribute_chain(expression)
        if chain and chain[0] in imports:
            candidate = ".".join((imports[chain[0]], *chain[1:]))
            return candidate if candidate in class_names else None
    return None


def _expression_type(
    expression: ast.AST,
    module: str,
    imports: dict[str, str],
    class_names: set[str],
    local_types: dict[str, str],
    class_fields: dict[str, dict[str, str]],
) -> str | None:
    if isinstance(expression, ast.Call):
        return _class_target(expression.func, module, imports, class_names)
    if isinstance(expression, ast.Name):
        return local_types.get(expression.id)
    if isinstance(expression, ast.Attribute):
        chain = _attribute_chain(expression)
        if chain and chain[0] in imports:
            receiver_type = imports[chain[0]]
            members = chain[1:]
            if receiver_type in class_names:
                members = [chain[1], *chain[2:]] if len(chain) > 1 else []
            else:
                receiver_type = ""
        else:
            receiver_type = local_types.get(chain[0], "") if chain else ""
            members = chain[1:]
        for member in members:
            receiver_type = class_fields.get(receiver_type, {}).get(member, "")
            if not receiver_type:
                return None
        return receiver_type or None
    return None


def _local_types(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    module: str,
    imports: dict[str, str],
    class_names: set[str],
    enclosing_class: str | None,
    parents: dict[ast.AST, ast.AST],
    class_fields: dict[str, dict[str, str]],
) -> dict[str, str]:
    types: dict[str, str] = {}
    if enclosing_class:
        types["self"] = f"{module}.{enclosing_class}"
        types["cls"] = f"{module}.{enclosing_class}"

    enclosing_functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, ast.FunctionDef | ast.AsyncFunctionDef):
            enclosing_functions.append(parent)
        parent = parents.get(parent)
    for outer in reversed(enclosing_functions):
        for argument in (
            *outer.args.posonlyargs,
            *outer.args.args,
            *outer.args.kwonlyargs,
            *((outer.args.vararg,) if outer.args.vararg else ()),
            *((outer.args.kwarg,) if outer.args.kwarg else ()),
        ):
            target = _class_target(argument.annotation, module, imports, class_names)
            if target:
                types[argument.arg] = target
        for child in _scope_nodes(outer):
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                target = _class_target(child.annotation, module, imports, class_names)
                if target:
                    types[child.target.id] = target
            elif (
                isinstance(child, ast.Assign)
                and isinstance(child.value, ast.Call)
                and (target := _class_target(child.value.func, module, imports, class_names))
            ):
                for assigned in child.targets:
                    if isinstance(assigned, ast.Name):
                        types[assigned.id] = target
    arguments = (
        *node.args.posonlyargs,
        *node.args.args,
        *node.args.kwonlyargs,
        *((node.args.vararg,) if node.args.vararg else ()),
        *((node.args.kwarg,) if node.args.kwarg else ()),
    )
    for argument in arguments:
        target = _class_target(argument.annotation, module, imports, class_names)
        if target:
            types[argument.arg] = target
    scope = _scope_nodes(node)
    for _ in range(2):
        for child in scope:
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                target = _class_target(child.annotation, module, imports, class_names)
                if target:
                    types[child.target.id] = target
            elif isinstance(child, ast.Assign):
                target = _expression_type(
                    child.value, module, imports, class_names, types, class_fields
                )
                if target:
                    for assigned in child.targets:
                        if isinstance(assigned, ast.Name):
                            types[assigned.id] = target
                elif isinstance(child.value, ast.Tuple):
                    for assigned in child.targets:
                        if isinstance(assigned, ast.Tuple):
                            for name, value in zip(assigned.elts, child.value.elts, strict=False):
                                item_type = _expression_type(
                                    value, module, imports, class_names, types, class_fields
                                )
                                if isinstance(name, ast.Name) and item_type:
                                    types[name.id] = item_type
    return types


def resolve_attribute(
    node: ast.Attribute,
    imports: dict[str, str],
    by_name: dict[str, list[Definition]],
    local_types: dict[str, str],
    class_fields: dict[str, dict[str, str]],
) -> str | None:
    chain = _attribute_chain(node)
    if not chain:
        return None
    imported = imports.get(chain[0])
    if imported is not None:
        qualified = ".".join((imported, *chain[1:]))
        if qualified in by_name:
            return qualified
        # ``from ctk_android import logs`` resolves to the package submodule.
        return None
    receiver_type = local_types.get(chain[0])
    if receiver_type:
        for member in chain[1:]:
            qualified = f"{receiver_type}.{member}"
            if qualified in by_name:
                receiver_type = qualified
                continue
            receiver_type = class_fields.get(receiver_type, {}).get(member, "")
            if not receiver_type:
                return None
        return receiver_type or None
    # Arbitrary object and external module attributes are not project edges.
    # Resolve those only when their receiver type is known; guessing from a
    # matching method spelling makes calls such as subprocess.run look local.
    return None


def build() -> tuple[dict[str, list[Definition]], dict[Definition, set[str]], list[Definition]]:
    by_name: dict[str, list[Definition]] = {}
    edges: dict[Definition, set[str]] = {}
    roots: list[Definition] = []
    imports_by_module: dict[str, dict[str, str]] = {}
    class_by_node: dict[int, str] = {}
    scope_by_definition: dict[Definition, str] = {}
    class_fields: dict[str, dict[str, str]] = {}
    class_names: set[str] = set()
    parents_by_node: dict[ast.AST, ast.AST] = {}
    paths = source_files()
    nodes: dict[Definition, ast.AST] = {}
    for path in paths:
        tree = parse(path)
        module = module_name(path)
        imports_by_module[module] = _import_targets(tree)
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent
        parents_by_node.update(parents)
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if (
                not isinstance(target, ast.Name)
                or not target.id[:1].isupper()
                or target.id.isupper()
            ):
                continue
            definition = Definition(module_name(path), target.id, node.lineno, path, "alias")
            by_name.setdefault(target.id, []).append(definition)
            by_name.setdefault(f"{module}.{target.id}", []).append(definition)
            edges[definition] = set()
            nodes[definition] = node.value
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                definition = Definition(module_name(path), node.name, node.lineno, path, "class")
                qualified, nested = _qualified_definition(node, module, parents)
                if not nested:
                    by_name.setdefault(node.name, []).append(definition)
                by_name.setdefault(qualified, []).append(definition)
                class_names.add(qualified)
                edges[definition] = set()
                nodes[definition] = node
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                parent = parents.get(node)
                while parent is not None and not isinstance(parent, ast.ClassDef):
                    parent = parents.get(parent)
                definition = Definition(module_name(path), node.name, node.lineno, path)
                qualified, nested = _qualified_definition(node, module, parents)
                if not nested:
                    by_name.setdefault(node.name, []).append(definition)
                by_name.setdefault(qualified, []).append(definition)
                scope_by_definition[definition] = qualified
                edges[definition] = set()
                nodes[definition] = node
                class_by_node[id(node)] = parent.name if isinstance(parent, ast.ClassDef) else ""
                if is_framework_entry(node):
                    roots.append(definition)

    for definition, node in nodes.items():
        if not isinstance(node, ast.ClassDef):
            continue
        fields: dict[str, str] = {}
        module_imports = imports_by_module[definition.module]
        for field in node.body:
            if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name):
                target = _class_target(
                    field.annotation, definition.module, module_imports, class_names
                )
                if target:
                    fields[field.target.id] = target
        class_key = scope_by_definition.get(definition, f"{definition.module}.{definition.name}")
        class_fields[class_key] = fields

    enum_names = _enum_classes(paths)
    for definition, node in nodes.items():
        module_imports = imports_by_module[definition.module]
        if definition.kind == "alias":
            edges[definition].update(
                target
                for name in references(node) - {definition.name}
                if (target := _resolve_name(name, definition.module, module_imports, by_name))
            )
            continue
        if isinstance(node, ast.ClassDef):
            edges[definition].update(
                target
                for base in node.bases
                for name in references(base)
                if (target := _resolve_name(name, definition.module, module_imports, by_name))
            )
            for field in node.body:
                if isinstance(field, ast.AnnAssign):
                    edges[definition].update(
                        target
                        for name in references(field.annotation)
                        if (
                            target := _resolve_name(
                                name, definition.module, module_imports, by_name
                            )
                        )
                    )
                if isinstance(field, ast.FunctionDef | ast.AsyncFunctionDef) and (
                    field.name == "__init__"
                    or _has_decorator(field, {"model_validator", "field_validator"})
                    or _protocol_class(node)
                ):
                    edges[definition].add(f"{definition.module}.{definition.name}.{field.name}")
            continue

        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            local_names = _local_names(node)
            enclosing_class = class_by_node.get(id(node)) or None
            local_types = _local_types(
                node,
                definition.module,
                module_imports,
                class_names,
                enclosing_class,
                parents_by_node,
                class_fields,
            )
            nested_callable_names = {
                child.name
                for child in _scope_nodes(node)
                if child is not node and isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
            }
            for annotation in (
                *(argument.annotation for argument in node.args.posonlyargs),
                *(argument.annotation for argument in node.args.args),
                *(argument.annotation for argument in node.args.kwonlyargs),
                node.args.vararg.annotation if node.args.vararg else None,
                node.args.kwarg.annotation if node.args.kwarg else None,
                node.returns,
            ):
                if annotation is not None:
                    edges[definition].update(
                        target
                        for name in references(annotation)
                        if (
                            target := _resolve_name(
                                name, definition.module, module_imports, by_name
                            )
                        )
                    )
            edges[definition].update(
                target
                for name in _decorator_references(node)
                if (target := _resolve_name(name, definition.module, module_imports, by_name))
            )
            for child in _scope_nodes(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        if (
                            child.func.id not in local_names
                            or child.func.id in nested_callable_names
                        ):
                            target = (
                                f"{scope_by_definition[definition]}.{child.func.id}"
                                if child.func.id in nested_callable_names
                                else _resolve_name(
                                    child.func.id, definition.module, module_imports, by_name
                                )
                            )
                            if target:
                                edges[definition].add(target)
                    elif isinstance(child.func, ast.Attribute):
                        target = resolve_attribute(
                            child.func,
                            module_imports,
                            by_name,
                            local_types,
                            class_fields,
                        )
                        if target:
                            edges[definition].add(target)
                    for argument in (
                        *child.args,
                        *(keyword.value for keyword in child.keywords),
                    ):
                        edges[definition].update(
                            target
                            for name in loaded_names(argument)
                            if (name not in local_names or name in nested_callable_names)
                            if (
                                target := (
                                    f"{scope_by_definition[definition]}.{name}"
                                    if name in nested_callable_names
                                    else _resolve_name(
                                        name, definition.module, module_imports, by_name
                                    )
                                )
                            )
                        )
                elif isinstance(child, ast.Attribute):
                    target = resolve_attribute(
                        child,
                        module_imports,
                        by_name,
                        local_types,
                        class_fields,
                    )
                    if target:
                        edges[definition].add(target)
                elif isinstance(child, ast.Name) and child.id in enum_names:
                    target = _resolve_name(child.id, definition.module, module_imports, by_name)
                    if target:
                        edges[definition].add(target)
                elif isinstance(child, ast.AnnAssign):
                    edges[definition].update(
                        target
                        for name in references(child.annotation)
                        if (
                            target := _resolve_name(
                                name, definition.module, module_imports, by_name
                            )
                        )
                    )
    return by_name, edges, roots


def _decorator_references(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {name for decorator in node.decorator_list for name in references(decorator)}


def reachable(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> set[Definition]:
    seen: set[Definition] = set()
    pending = list(roots)
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        for name in edges[current]:
            pending.extend(by_name.get(name, []))
    return seen


def shortest_paths(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> dict[Definition, tuple[Definition, ...]]:
    paths: dict[Definition, tuple[Definition, ...]] = {root: (root,) for root in roots}
    pending = list(roots)
    while pending:
        current = pending.pop(0)
        for name in sorted(edges[current]):
            for target in by_name.get(name, []):
                if target not in paths:
                    paths[target] = (*paths[current], target)
                    pending.append(target)
    return paths


def direct_callers(
    by_name: dict[str, list[Definition]], edges: dict[Definition, set[str]]
) -> dict[Definition, set[Definition]]:
    callers: dict[Definition, set[Definition]] = {definition: set() for definition in edges}
    for caller, names in edges.items():
        for name in names:
            for target in by_name.get(name, []):
                if caller != target:
                    callers[target].add(caller)
    return callers


def orphan_diagnostics(
    by_name: dict[str, list[Definition]],
    edges: dict[Definition, set[str]],
    roots: list[Definition],
) -> list[str]:
    paths = shortest_paths(by_name, edges, roots)
    callers = direct_callers(by_name, edges)
    diagnostics: list[str] = []
    for definition in sorted(set(edges) - set(paths), key=lambda item: (item.module, item.line)):
        where = f"{definition.module}.{definition.name} ({definition.path}:{definition.line})"
        direct = sorted(f"{item.module}.{item.name}" for item in callers[definition])
        root_names = sorted(f"{item.module}.{item.name}" for item in roots)
        diagnostics.append(
            f"{where}; direct callers={direct or ['none']}; CLI roots={root_names}; "
            "shortest CLI path=none; reason=not reachable from a registered CLI command"
        )
    return diagnostics
