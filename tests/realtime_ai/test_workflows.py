"""Offline structural checks for committed ComfyUI workflow JSONs (P-028).

No ComfyUI or GPU required — these validate the node-graph shape: every
node has the fields ComfyUI's API format requires, every reference from
one node's `inputs` to another (`["nodeId", outputIndex]`) actually points
at a node that exists in the same file. This catches a typo'd node id or
a copy-paste graph edit that leaves a dangling reference — the kind of
mistake that only otherwise surfaces when someone loads the file into a
real ComfyUI and it fails to run.

It does NOT verify a workflow actually produces correct output, that a
referenced `class_type` is spelled the way the installed custom node pack
expects, or that referenced models exist. That needs a real ComfyUI + GPU
run, which is owner work — see docs/PROPOSALS.md P-028 and each file's own
`_meta.status`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
WORKFLOW_DIRS = [
    REPO / "modules" / "realtime-ai" / "comfyui" / "workflows",
    REPO / "modules" / "image-editing" / "workflows",
]


def _workflow_files() -> list[Path]:
    files = []
    for d in WORKFLOW_DIRS:
        files.extend(sorted(d.glob("*.json")))
    return files


def _node_entries(doc: dict) -> dict:
    """Every top-level key except `_meta` is a node, keyed by its id string."""
    return {k: v for k, v in doc.items() if k != "_meta"}


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_workflow_parses(f: Path) -> None:
    json.loads(f.read_text(encoding="utf-8"))


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_workflow_has_meta_block(f: Path) -> None:
    """00-starter.json is the one documented exception — it's an intentional
    empty stub to copy, not a real workflow, so it carries no _meta."""
    if f.name == "00-starter.json":
        pytest.skip("00-starter.json is an intentional empty stub, not a workflow")
    doc = json.loads(f.read_text(encoding="utf-8"))
    assert "_meta" in doc, f"{f.name}: no _meta block documenting purpose/models/nodes"


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_node_has_class_type(f: Path) -> None:
    if f.name == "00-starter.json":
        pytest.skip("00-starter.json is ComfyUI's UI/graph export format, not API format")
    doc = json.loads(f.read_text(encoding="utf-8"))
    nodes = _node_entries(doc)
    missing = [nid for nid, n in nodes.items() if "class_type" not in n]
    assert not missing, f"{f.name}: node(s) with no class_type: {missing}"


_REF_RE = re.compile(r'^\["?(\w+)"?,\s*\d+\]$')


def _find_refs(value) -> list[str]:
    """Recursively find `["nodeId", outputIndex]`-shaped references inside a
    node's `inputs` dict — these are the only place ComfyUI's API format
    links one node's output to another node's input."""
    refs = []
    if (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    ):
        refs.append(value[0])
    elif isinstance(value, dict):
        for v in value.values():
            refs.extend(_find_refs(v))
    return refs


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_node_references_resolve(f: Path) -> None:
    """A node referencing an id that doesn't exist in the file is a dangling
    reference — ComfyUI would refuse to load the graph at all."""
    if f.name == "00-starter.json":
        pytest.skip("00-starter.json is ComfyUI's UI/graph export format, not API format")
    doc = json.loads(f.read_text(encoding="utf-8"))
    nodes = _node_entries(doc)
    node_ids = set(nodes.keys())

    dangling: dict[str, list[str]] = {}
    for nid, node in nodes.items():
        referenced = _find_refs(node.get("inputs", {}))
        bad = [r for r in referenced if r not in node_ids]
        if bad:
            dangling[nid] = bad

    assert not dangling, f"{f.name}: node(s) reference nonexistent node ids: {dangling}"


def test_index_readme_lists_every_committed_workflow() -> None:
    """The realtime-ai workflows README's 'Index accuracy' table is the
    documented source of truth for what's on disk — a file added here
    without a row there is exactly the drift that table exists to prevent."""
    readme = (
        REPO / "modules" / "realtime-ai" / "comfyui" / "workflows" / "README.md"
    ).read_text(encoding="utf-8")
    index_section = readme.split("## Index accuracy", 1)[1]

    on_disk = {f.name for f in _workflow_files()}
    missing_from_readme = [name for name in on_disk if f"`{name}`" not in index_section]
    assert not missing_from_readme, (
        f"workflow file(s) on disk have no row in the 'Index accuracy' table: "
        f"{missing_from_readme}"
    )
