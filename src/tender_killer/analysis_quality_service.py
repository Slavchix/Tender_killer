from __future__ import annotations

import ast
from pathlib import Path
from typing import TypedDict


class UnusedImportIssue(TypedDict):
    path: str
    line: int
    name: str


def find_unused_direct_imports(paths: list[Path]) -> list[UnusedImportIssue]:
    issues: list[UnusedImportIssue] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = _imported_names(tree)
        used = _used_names(tree)
        for name, line in imported:
            if name not in used:
                issues.append({"path": str(path), "line": line, "name": name})
    return issues


def _imported_names(tree: ast.AST) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(((alias.asname or alias.name.split(".")[0]), node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for alias in node.names:
                if alias.name == "*":
                    continue
                names.append(((alias.asname or alias.name), node.lineno))
    return names


def _used_names(tree: ast.AST) -> set[str]:
    used: set[str] = _all_export_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and not _is_import_name(node):
            used.add(node.id)
    return used


def _all_export_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and any(_is_all_target(target) for target in node.targets):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and _is_all_target(node.target):
            value = node.value
        if value is None:
            continue
        names.update(_literal_string_items(value))
    return names


def _is_all_target(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and node.id == "__all__"


def _literal_string_items(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return set()
    return {item.value for item in node.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)}


def _is_import_name(node: ast.Name) -> bool:
    return isinstance(getattr(node, "ctx", None), ast.Store)
