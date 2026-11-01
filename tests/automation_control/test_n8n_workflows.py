"""Offline structural checks for automation-control's n8n workflows (P-033).

No n8n instance required. The regression this file exists for: the
committed on-stream-start.json workflow reads two env vars via n8n's
`{{$env.X}}` expression syntax, but docker-compose.yml's n8n service never
set either one — every import would fire against an empty URL with no API
key. Nothing caught this because nothing cross-checked the two files
against each other.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO / "modules" / "automation-control" / "n8n" / "workflows"
COMPOSE_FILE = REPO / "docker-compose.yml"
IMPORT_SCRIPT = REPO / "scripts" / "setup" / "n8n_import.sh"


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS_DIR.glob("*.json"))


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: p.name)
def test_workflow_parses(f: Path) -> None:
    json.loads(f.read_text(encoding="utf-8"))


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: p.name)
def test_workflow_has_required_top_level_keys(f: Path) -> None:
    doc = json.loads(f.read_text(encoding="utf-8"))
    for key in ("name", "nodes", "connections"):
        assert key in doc, f"{f.name}: missing top-level {key!r} — not a valid n8n export"


@pytest.mark.parametrize("f", _workflow_files(), ids=lambda p: p.name)
def test_workflow_nodes_referenced_in_connections_exist(f: Path) -> None:
    """A connection naming a node that isn't in `nodes` is the n8n-JSON
    equivalent of a dangling reference — it imports fine and then the
    workflow silently has a broken edge."""
    doc = json.loads(f.read_text(encoding="utf-8"))
    node_names = {n["name"] for n in doc["nodes"]}
    referenced = set(doc.get("connections", {}).keys())
    for targets in doc.get("connections", {}).values():
        for branch in targets.get("main", []):
            for edge in branch:
                referenced.add(edge["node"])
    dangling = referenced - node_names
    assert not dangling, f"{f.name}: connections reference undefined node(s): {dangling}"


def _env_vars_referenced_by_workflows() -> set[str]:
    referenced: set[str] = set()
    for f in _workflow_files():
        body = f.read_text(encoding="utf-8")
        referenced.update(re.findall(r"\$env\.([A-Za-z_][A-Za-z0-9_]*)", body))
    return referenced


def _n8n_service_env_keys() -> set[str]:
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    n8n_env = compose["services"]["n8n"]["environment"]
    # environment can be a dict (key: value) or a list ("KEY=value") depending
    # on compose-file style; this repo uses the dict form for n8n.
    if isinstance(n8n_env, dict):
        return set(n8n_env.keys())
    return {entry.split("=", 1)[0] for entry in n8n_env}


def test_every_workflow_env_var_is_set_on_the_n8n_service() -> None:
    """Regression: on-stream-start.json's {{$env.API_URL}} and
    {{$env.HCP_API_KEY}} were referenced but neither was in docker-compose.yml's
    n8n environment block — the workflow would run against an empty URL and
    no API key. Every `$env.X` any committed workflow reads must actually be
    set there."""
    referenced = _env_vars_referenced_by_workflows()
    available = _n8n_service_env_keys()
    missing = referenced - available
    assert not missing, (
        f"workflow(s) reference $env vars docker-compose.yml's n8n service "
        f"never sets: {missing}"
    )


def test_n8n_blocks_env_access_is_explicitly_disabled() -> None:
    """n8n 1.x blocks $env access in node expressions by default. Any
    workflow using {{$env.X}} needs N8N_BLOCK_ENV_ACCESS_IN_NODE explicitly
    set to "false", or the expression silently resolves to nothing."""
    if not _env_vars_referenced_by_workflows():
        pytest.skip("no committed workflow reads $env — nothing to gate")
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    n8n_env = compose["services"]["n8n"]["environment"]
    value = str(n8n_env.get("N8N_BLOCK_ENV_ACCESS_IN_NODE", "")).strip().lower()
    assert value == "false", (
        "a committed workflow reads $env.* but N8N_BLOCK_ENV_ACCESS_IN_NODE "
        f"is {value!r}, not \"false\" — n8n 1.x blocks env access by default"
    )


def test_import_script_workflow_dir_matches_committed_location() -> None:
    """n8n_import.sh hardcodes the workflow directory it globs — verify
    that path actually points at where the committed JSON lives, not a
    stale location from before a module reshuffle."""
    body = IMPORT_SCRIPT.read_text(encoding="utf-8")
    m = re.search(r'WORKFLOW_DIR="\$REPO_ROOT/([^"]+)"', body)
    assert m, "could not find WORKFLOW_DIR assignment in n8n_import.sh"
    resolved = (REPO / m.group(1)).resolve()
    assert resolved == WORKFLOWS_DIR.resolve(), (
        f"n8n_import.sh's WORKFLOW_DIR resolves to {resolved}, not the real "
        f"workflows dir {WORKFLOWS_DIR}"
    )
