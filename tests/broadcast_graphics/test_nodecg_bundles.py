"""Offline structural checks for broadcast-graphics's NodeCG bundles (P-034).

No NodeCG instance required. Two regression classes:

1. `nodecg/README.md` claimed the Redis bridge listens on channels
   (`overlay.scoreboard.update`, `overlay.lowerthird.update`,
   `overlay.sponsor.update`) that don't match what `redis-bridge.js`
   actually does (`pSubscribe('overlay.*', ...)` then a bare
   `channel.replace(/^overlay\\./, '')` lookup against the replicant keys
   `index.js` defines — no `.update` suffix, and `lowerThird` is camelCase).
   Publishing to the documented channel names would have every message
   silently dropped with a "no replicant for overlay" warning log nobody
   watches. Fixed in the README; this file is the regression test.

2. A bundle's `package.json` can declare a `dashboardPanels[].file` or
   `graphics[].file` that doesn't exist on disk — `hcp-alerts` does this
   today, but its own README already says `Status: Scaffolded`, so that
   specific case is an expected, disclosed gap (xfail), not a silent one.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
BUNDLES_DIR = REPO / "modules" / "broadcast-graphics" / "nodecg" / "bundles"
NODECG_README = REPO / "modules" / "broadcast-graphics" / "nodecg" / "README.md"
INDEX_JS = BUNDLES_DIR / "hcp-starter" / "extension" / "index.js"
REDIS_BRIDGE_JS = BUNDLES_DIR / "hcp-starter" / "extension" / "redis-bridge.js"
COMPOSE_FILE = REPO / "docker-compose.yml"


def _bundle_dirs() -> list[Path]:
    return sorted(p for p in BUNDLES_DIR.iterdir() if p.is_dir())


def _package_json(bundle_dir: Path) -> dict:
    return json.loads((bundle_dir / "package.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("bundle_dir", _bundle_dirs(), ids=lambda p: p.name)
def test_package_json_parses(bundle_dir: Path) -> None:
    _package_json(bundle_dir)


@pytest.mark.parametrize("bundle_dir", _bundle_dirs(), ids=lambda p: p.name)
def test_declared_dashboard_and_graphics_files_exist(bundle_dir: Path) -> None:
    if bundle_dir.name == "hcp-alerts":
        pytest.xfail(
            "hcp-alerts/README.md says 'Status: Scaffolded — skeleton in place, "
            "ready for implementation'; package.json declares files that don't "
            "exist yet by design, not by accident. Building the bundle out is a "
            "real feature, not a docs fix — see docs/PROPOSALS.md."
        )

    pkg = _package_json(bundle_dir)
    nodecg_cfg = pkg.get("nodecg", {})

    missing = []
    for panel in nodecg_cfg.get("dashboardPanels", []):
        if not (bundle_dir / "dashboard" / panel["file"]).is_file():
            missing.append(f"dashboard/{panel['file']}")
    for graphic in nodecg_cfg.get("graphics", []):
        if not (bundle_dir / "graphics" / graphic["file"]).is_file():
            missing.append(f"graphics/{graphic['file']}")

    assert not missing, f"{bundle_dir.name}: package.json declares missing file(s): {missing}"


def _replicant_keys() -> set[str]:
    """Extract every `nodecg.Replicant('name', ...)` key from index.js —
    a plain regex, not a JS parser, but the file is small and this is the
    same style of static check tests/*_workflows.py already use for JSON."""
    body = INDEX_JS.read_text(encoding="utf-8")
    return set(re.findall(r"nodecg\.Replicant\(\s*['\"]([^'\"]+)['\"]", body))


def _documented_channels() -> list[str]:
    r"""Only the bulleted list entries (`- \`overlay.x\` ...`), not every
    backtick-quoted `overlay.*` mention in the surrounding prose — the
    section also names a deliberate counter-example (what NOT to publish
    to) inside a parenthetical, which isn't a channel this bridge listens
    on and shouldn't be checked as though it were."""
    body = NODECG_README.read_text(encoding="utf-8")
    section = body.split("## Redis bridge", 1)[1].split("## OBS integration", 1)[0]
    return [
        m.group(1)
        for line in section.splitlines()
        if line.strip().startswith("- ")
        for m in [re.search(r"`(overlay\.[A-Za-z0-9_.]+)`", line)]
        if m
    ]


def test_documented_redis_channels_match_replicant_keys() -> None:
    """Regression: the README previously listed overlay.scoreboard.update /
    overlay.lowerthird.update / overlay.sponsor.update — none of which the
    bridge's channel.replace(/^overlay\\./, '') + replicants[name] lookup
    would actually resolve to a real replicant."""
    replicants = _replicant_keys()
    assert replicants, "found no nodecg.Replicant(...) calls in index.js — check the regex/path"

    channels = _documented_channels()
    assert channels, "found no `overlay.X` channel names documented in nodecg/README.md"

    for channel in channels:
        name = channel.removeprefix("overlay.")
        assert "." not in name, (
            f"{channel!r}: redis-bridge.js's channel.replace(/^overlay\\./, '') extracts "
            f"everything after the first dot, including further dots — a channel name with "
            f"an extra segment (like a trailing '.update') will never match a replicant key"
        )
        assert name in replicants, (
            f"{channel!r} names replicant {name!r}, which index.js never defines "
            f"(defined: {sorted(replicants)}) — the bridge would drop every message on this "
            f"channel with a 'no replicant for overlay' warning"
        )


def _env_vars_read_by_redis_bridge() -> set[str]:
    body = REDIS_BRIDGE_JS.read_text(encoding="utf-8")
    return set(re.findall(r"process\.env\.([A-Za-z_][A-Za-z0-9_]*)", body))


def _nodecg_service_env_keys() -> set[str]:
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    nodecg_env = compose["services"]["nodecg"].get("environment", {})
    if isinstance(nodecg_env, dict):
        return set(nodecg_env.keys())
    return {entry.split("=", 1)[0] for entry in nodecg_env}


def test_nodecg_service_sets_every_env_var_the_redis_bridge_reads() -> None:
    """Regression: docker-compose.yml's nodecg service had no `environment:`
    block at all — REDIS_URL was never set, so redis-bridge.js's own
    `if (!url) { ...warn...; return; }` guard always fired and the live-
    update bridge this module exists for never connected on
    `docker compose --profile graphics up -d nodecg` (P-034)."""
    needed = _env_vars_read_by_redis_bridge()
    assert needed, "found no process.env.X reads in redis-bridge.js — check the regex/path"

    available = _nodecg_service_env_keys()
    missing = needed - available
    assert not missing, (
        f"redis-bridge.js reads {missing} from the environment, but docker-compose.yml's "
        f"nodecg service never sets it — the bridge will silently no-op"
    )
