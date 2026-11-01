"""Offline structural checks for creator-experience's committed OBS assets.

No OBS required — these validate the committed scene-collection JSON and
plugin-pin table stay consistent with the docs that describe them, so a
future edit to one side doesn't silently drift from the other. They do
NOT verify OBS itself (that needs a real install — `make test-obs`,
scripts/setup/test_obs_websocket.py, owner-only per P-027).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "modules" / "creator-experience"


def test_default_scene_collection_parses() -> None:
    json.loads((MODULE / "scenes" / "default.json").read_text(encoding="utf-8"))


def test_default_scene_collection_matches_documented_scene_table() -> None:
    """scenes/README.md's numbered table is the source of truth for which
    scenes should exist and in what order — default.json (placeholder or
    real export) must match it, or the two have drifted."""
    readme = (MODULE / "scenes" / "README.md").read_text(encoding="utf-8")
    # Table rows look like: | 7 | Vertical Output | 1080x1920 ... |
    table_rows = re.findall(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|", readme, re.MULTILINE)
    documented_scenes = [s.strip() for s in table_rows]
    assert documented_scenes, "couldn't find the numbered scene table in scenes/README.md"

    doc = json.loads((MODULE / "scenes" / "default.json").read_text(encoding="utf-8"))
    actual_scenes = [s["name"] for s in doc["scenes"]]

    assert actual_scenes == documented_scenes, (
        f"default.json's scenes {actual_scenes} do not match the documented "
        f"table {documented_scenes} in scenes/README.md — update whichever "
        f"one is stale"
    )


def test_every_core_software_plugin_is_pinned() -> None:
    """setup/manual.md's 'Core software' table lists the plugins to install;
    obs-config/plugins.md pins a version for each. A plugin named in one but
    not the other means an install step nobody can actually follow exactly."""
    manual = (MODULE / "setup" / "manual.md").read_text(encoding="utf-8")
    plugins_doc = (MODULE / "obs-config" / "plugins.md").read_text(encoding="utf-8")

    # Core software table: | Tool | Purpose | Install |
    core_table_match = re.search(
        r"## Core software\n\n(.*?)\n\n", manual, re.DOTALL
    )
    assert core_table_match, "couldn't find the 'Core software' table in setup/manual.md"
    core_rows = re.findall(r"^\|\s*([^|]+?)\s*\|", core_table_match.group(1), re.MULTILINE)
    # First row is the header ("Tool"); drop it. Strip markdown emphasis/links.
    core_tools = [
        re.sub(r"[*_]|\(.*?\)", "", t).strip()
        for t in core_rows[1:]
        if "---" not in t
    ]
    # obs-websocket is "bundled in OBS 28+" per manual.md, not a separately
    # pinned plugin install step there — but it *is* pinned in plugins.md
    # (5.5.x, bundled in OBS 30+), so it is excluded from this direction of
    # the check only, not from plugins.md itself.
    pinned_names = plugins_doc.lower()

    # The base application, not a plugin — never expected in plugins.md.
    not_a_plugin = {"obs studio"}

    missing = [
        tool for tool in core_tools
        if tool.split(" (")[0].strip().lower() not in pinned_names
        and tool.split(" (")[0].strip().lower() not in not_a_plugin
    ]
    assert not missing, (
        f"plugin(s) listed in setup/manual.md's Core software table have no "
        f"pinned version in obs-config/plugins.md: {missing}"
    )
