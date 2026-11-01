"""Offline structural checks for the Creator Extend Blender addon (P-036).

No Blender required — `bpy` isn't installed or importable here, so these
are AST-level checks: every file parses, `bl_info` has the fields Blender
requires, the `classes` registration list in `__init__.py` matches what's
actually defined across the addon (a class present in one but not the
other either silently never registers, or crashes `register()` on an
AttributeError), and every operator's `bl_idname` is unique (a duplicate
crashes Blender's own class registration at runtime).

Also the regression test for the finding that prompted this file:
`modules/content-creation/setup/automated.md` claimed this addon didn't
exist ("None of it is in this repo today... unwritten") when it actually
does, mostly working. See docs/PROPOSALS.md P-036.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ADDON_DIR = REPO / "plugins" / "blender-addon"
CONTENT_CREATION_AUTOMATED = REPO / "modules" / "content-creation" / "setup" / "automated.md"

REQUIRED_BL_INFO_KEYS = {"name", "author", "version", "blender", "location", "description", "category"}


def _addon_files() -> list[Path]:
    return sorted(ADDON_DIR.rglob("*.py"))


@pytest.mark.parametrize("f", _addon_files(), ids=lambda p: str(p.relative_to(ADDON_DIR)))
def test_addon_file_parses(f: Path) -> None:
    ast.parse(f.read_text(encoding="utf-8"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def test_bl_info_has_required_keys() -> None:
    tree = _parse(ADDON_DIR / "__init__.py")
    bl_info_node = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.Assign)
         and any(isinstance(t, ast.Name) and t.id == "bl_info" for t in n.targets)),
        None,
    )
    assert bl_info_node is not None, "no bl_info = {...} assignment found in __init__.py"
    assert isinstance(bl_info_node.value, ast.Dict)
    keys = {
        k.value for k in bl_info_node.value.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    missing = REQUIRED_BL_INFO_KEYS - keys
    assert not missing, f"bl_info is missing required key(s): {missing}"


def _class_names_in(path: Path) -> set[str]:
    tree = _parse(path)
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


def _registration_list_names() -> list[str]:
    """Extract the bare names inside `classes = [...]` in __init__.py."""
    tree = _parse(ADDON_DIR / "__init__.py")
    classes_node = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.Assign)
         and any(isinstance(t, ast.Name) and t.id == "classes" for t in n.targets)),
        None,
    )
    assert classes_node is not None, "no classes = [...] assignment found in __init__.py"
    assert isinstance(classes_node.value, ast.List)
    names = []
    for elt in classes_node.value.elts:
        # Each entry is `module.ClassName` (an ast.Attribute) — the part
        # after registration cares about is the attribute name.
        if isinstance(elt, ast.Attribute):
            names.append(elt.attr)
        elif isinstance(elt, ast.Name):
            names.append(elt.id)
    return names


def test_every_registered_class_is_actually_defined() -> None:
    """A class in `classes = [...]` that isn't defined anywhere would raise
    AttributeError the moment Blender calls register() — this is the AST
    equivalent of actually running register()."""
    registered = _registration_list_names()
    assert registered, "classes list in __init__.py is empty — check the extraction"

    defined: set[str] = set()
    for f in _addon_files():
        if f.name == "__init__.py" and f.parent == ADDON_DIR:
            continue
        defined |= _class_names_in(f)

    missing = set(registered) - defined
    assert not missing, f"classes list registers undefined class(es): {missing}"


def test_no_class_defined_but_never_registered() -> None:
    """The inverse check: a Panel/Operator subclass that exists but was
    never added to `classes` silently never appears in Blender at all."""
    registered = set(_registration_list_names())
    defined: set[str] = set()
    for f in _addon_files():
        if f.name == "__init__.py" and f.parent == ADDON_DIR:
            continue
        defined |= {
            name for name in _class_names_in(f)
            if name.startswith("CE_")  # this addon's own naming convention
        }

    unregistered = defined - registered
    assert not unregistered, f"class(es) defined but never added to classes list: {unregistered}"


def _bl_idnames() -> list[str]:
    """Every `bl_idname = "..."` class attribute across the addon's operator
    files — Blender crashes at registration if two classes share one."""
    idnames = []
    for f in _addon_files():
        tree = _parse(f)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if (
                        isinstance(item, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "bl_idname" for t in item.targets)
                        and isinstance(item.value, ast.Constant)
                    ):
                        idnames.append(item.value.value)
    return idnames


def test_bl_idnames_are_unique() -> None:
    idnames = _bl_idnames()
    assert idnames, "found no bl_idname assignments — check the extraction"
    dupes = {name for name in idnames if idnames.count(name) > 1}
    assert not dupes, f"duplicate bl_idname(s) would crash Blender's class registration: {dupes}"


def test_content_creation_docs_no_longer_claim_the_addon_is_unwritten() -> None:
    """Regression: automated.md used to say 'None of it is in this repo
    today' / 'unwritten' about this exact addon, which has existed with
    working code the whole time nobody cross-checked."""
    body = CONTENT_CREATION_AUTOMATED.read_text(encoding="utf-8")
    assert "None of it is in this repo today" not in body
    assert "Both\nare unwritten" not in body
    assert "plugins/blender-addon" in body, (
        "automated.md should point at the real addon location now that it's documented"
    )
