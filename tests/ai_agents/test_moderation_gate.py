"""Offline checks for ai-agents' inline moderation gate (P-039).

No Ollama/Redis/Postgres required. `regex_check` itself is a pure
function (no async, no network) so it's tested directly; the two-sided
gate in agent.py (incoming text checked before generate(), the generated
reply checked before it's published) is checked at the AST level, since
importing agent.py itself pulls in memory.py -> asyncpg, which isn't
installed in every environment this suite runs in.

This is the regression test for a real gap: setup/manual.md says
moderation must run "on both directions — what reaches the agent and
what the agent says. An unmoderated agent on a live stream is a
liability, not a feature" — but agent.py never called moderator.py at
all, and moderator.py never checked the agent's own output either.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCAL_LLM = REPO / "modules" / "ai-agents" / "local-llm"
AGENT_PY = LOCAL_LLM / "agent.py"

sys.path.insert(0, str(LOCAL_LLM))

from moderator import regex_check  # noqa: E402


# ── regex_check itself ───────────────────────────────────────────────

def test_regex_check_flags_known_spam_pattern():
    assert regex_check("click here for a free nitro gift") == ["spam"]


def test_regex_check_flags_spam_link_tld():
    assert regex_check("check this out http://totally-legit.tk/offer") == ["spam"]


def test_regex_check_passes_ordinary_text():
    assert regex_check("hey, nice shot on that par 5!") == []


# ── agent.py wiring (AST-level, no live import) ──────────────────────

def _agent_source() -> str:
    return AGENT_PY.read_text(encoding="utf-8")


def test_agent_imports_regex_check_from_moderator():
    tree = ast.parse(_agent_source())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "moderator":
            if any(alias.name == "regex_check" for alias in node.names):
                found = True
    assert found, "agent.py no longer imports regex_check from moderator — moderation gate removed?"


def test_agent_calls_regex_check_at_least_twice():
    """Once for the incoming message, once for the generated reply — the
    two directions setup/manual.md's Moderation section requires."""
    tree = ast.parse(_agent_source())
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "regex_check"
    ]
    assert len(calls) >= 2, (
        f"agent.py calls regex_check {len(calls)} time(s) — expected at least 2 "
        f"(incoming text, generated reply)"
    )


def test_flagged_reply_branch_continues_before_publishing_agent_reply():
    """Regression: a flagged reply must never reach `redis.publish("agent.reply", ...)`.
    Checked by source position: the reply_flags branch's `continue` must
    appear before the `agent.reply` publish call, not after — if someone
    moves the check after the publish, this catches it."""
    body = _agent_source()
    reply_check_idx = body.index("reply_flags = regex_check(reply)")
    # The literal `redis.publish("agent.reply", ...)` call — searched with
    # the trailing comma to disambiguate from two other "agent.reply"
    # occurrences in the file: the module docstring's prose mention, and
    # the `"source": "agent.reply"` tag inside the chat.moderation payload
    # for a flagged reply. Both would match a bare '"agent.reply"' search
    # and land before the real publish call, making the check meaningless.
    agent_reply_publish_idx = body.index('"agent.reply",', reply_check_idx)
    continue_after_check = body.index("continue", reply_check_idx)
    assert continue_after_check < agent_reply_publish_idx, (
        "the reply-flagged branch's `continue` appears after the agent.reply "
        "publish in source order — a flagged reply could reach the publish call"
    )
