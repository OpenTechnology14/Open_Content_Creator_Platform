"""Offline checks for character-avatar's agent -> avatar control bridge (P-042).

No VTube Studio / Redis required. `parse_agent_reply`, `load_avatar_mapping`,
`hotkey_for_persona`, and `estimate_talk_seconds` are pure functions, tested
directly — importing avatar_control.py itself needs no `websockets`/`redis`
because both are imported lazily inside `run()`, not at module level (see
that function's own docstring for why). `run()`'s actual loop behavior
(trigger talk, wait, trigger idle — not skipped, not reordered) isn't
something a static import proves, so it's checked at the source-position
level instead, the same approach `tests/ai_agents/test_moderation_gate.py`
uses for `agent.py`'s moderation gate.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
VTUBE = REPO / "modules" / "character-avatar" / "vtube"
AVATAR_CONTROL_PY = VTUBE / "avatar_control.py"
MAPPING_YAML = VTUBE / "avatar_mapping.yaml"

sys.path.insert(0, str(VTUBE))

from avatar_control import (  # noqa: E402
    estimate_talk_seconds,
    hotkey_for_persona,
    load_avatar_mapping,
    parse_agent_reply,
)


# ── parse_agent_reply ────────────────────────────────────────────────

def test_parse_agent_reply_valid_payload():
    raw = '{"persona": "caddy", "to": "viewer1", "text": "nice shot"}'
    assert parse_agent_reply(raw) == {"persona": "caddy", "to": "viewer1", "text": "nice shot"}


def test_parse_agent_reply_rejects_malformed_json():
    assert parse_agent_reply("{not json") is None


def test_parse_agent_reply_rejects_non_object_json():
    assert parse_agent_reply("[1, 2, 3]") is None


def test_parse_agent_reply_rejects_missing_persona():
    assert parse_agent_reply('{"to": "viewer1", "text": "hi"}') is None


def test_parse_agent_reply_rejects_missing_text():
    assert parse_agent_reply('{"persona": "caddy", "to": "viewer1"}') is None


def test_parse_agent_reply_rejects_empty_text():
    assert parse_agent_reply('{"persona": "caddy", "to": "v", "text": ""}') is None


def test_parse_agent_reply_rejects_none_input():
    assert parse_agent_reply(None) is None


# ── load_avatar_mapping / hotkey_for_persona ─────────────────────────

def test_committed_mapping_file_loads_and_has_default():
    mapping = load_avatar_mapping(MAPPING_YAML)
    assert mapping["default"]["talk_hotkey"]
    assert mapping["default"]["idle_hotkey"]


def test_load_avatar_mapping_requires_default_section(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("personas:\n  caddy:\n    talk_hotkey: X\n")
    with pytest.raises(ValueError):
        load_avatar_mapping(bad)


def test_load_avatar_mapping_requires_both_default_keys(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("default:\n  talk_hotkey: X\n")
    with pytest.raises(ValueError):
        load_avatar_mapping(bad)


def test_hotkey_for_persona_uses_override_when_present():
    mapping = {
        "default": {"talk_hotkey": "D-Talk", "idle_hotkey": "D-Idle"},
        "personas": {"caddy": {"talk_hotkey": "C-Talk", "idle_hotkey": "C-Idle"}},
    }
    assert hotkey_for_persona("caddy", mapping, "talk_hotkey") == "C-Talk"


def test_hotkey_for_persona_falls_back_to_default_for_unknown_persona():
    mapping = {"default": {"talk_hotkey": "D-Talk", "idle_hotkey": "D-Idle"}, "personas": {}}
    assert hotkey_for_persona("someone-else", mapping, "talk_hotkey") == "D-Talk"


def test_hotkey_for_persona_falls_back_when_personas_key_missing_entirely():
    mapping = {"default": {"talk_hotkey": "D-Talk", "idle_hotkey": "D-Idle"}}
    assert hotkey_for_persona("caddy", mapping, "idle_hotkey") == "D-Idle"


def test_committed_mapping_covers_the_real_caddy_persona():
    """Regression: modules/ai-agents/local-llm/personas/caddy.yaml's `name:
    caddy` is the only persona shipped today. If the mapping's persona key
    ever drifted from the real persona name, every reply would silently
    fall back to `default` instead of failing loudly — the fallback test
    above would still pass, so this checks the real key is actually
    present rather than relying on the fallback to mask a typo."""
    mapping = load_avatar_mapping(MAPPING_YAML)
    assert "caddy" in mapping.get("personas", {})


# ── estimate_talk_seconds ─────────────────────────────────────────────

def test_estimate_talk_seconds_scales_with_word_count():
    short = estimate_talk_seconds("nice shot")
    long = estimate_talk_seconds(" ".join(["word"] * 40))
    assert long > short


def test_estimate_talk_seconds_clamps_to_minimum():
    assert estimate_talk_seconds("") == pytest.approx(0.6)


def test_estimate_talk_seconds_clamps_to_maximum():
    huge = " ".join(["word"] * 1000)
    assert estimate_talk_seconds(huge) == pytest.approx(8.0)


# ── run() wiring (AST / source-position, no live Redis/VTS) ──────────

def _source() -> str:
    return AVATAR_CONTROL_PY.read_text(encoding="utf-8")


def test_run_imports_redis_and_vts_client_lazily_not_at_module_level():
    """Regression guard for the reason the pure functions above are
    importable without `websockets`/`redis` installed at all: those
    imports must live inside run(), not at module top level."""
    tree = ast.parse(_source())
    top_level_names = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                top_level_names.add(alias.asname or alias.name)
    assert "VTSClient" not in top_level_names
    assert "aioredis" not in top_level_names


def test_run_triggers_talk_hotkey_before_idle_hotkey():
    body = _source()
    talk_idx = body.index("trigger_hotkey(talk_hotkey)")
    idle_idx = body.index("trigger_hotkey(idle_hotkey)")
    assert talk_idx < idle_idx, (
        "idle hotkey triggers before talk hotkey — the avatar would look "
        "idle while the agent is actually speaking"
    )


def test_run_sleeps_for_the_estimated_duration_between_hotkeys():
    body = _source()
    talk_idx = body.index("trigger_hotkey(talk_hotkey)")
    sleep_idx = body.index("asyncio.sleep(duration)")
    idle_idx = body.index("trigger_hotkey(idle_hotkey)")
    assert talk_idx < sleep_idx < idle_idx, (
        "the sleep between hotkeys must sit strictly between the talk and "
        "idle triggers, or the hold duration does nothing"
    )
