"""Editorial approval, routing and recovery contracts; no real accounts or network."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

import pytest
from pydantic import ValidationError

MODULE = Path(__file__).resolve().parents[2] / "modules/social-management"
sys.path.insert(0, str(MODULE))

from social_management.cli import main  # noqa: E402
from social_management.editorial import (  # noqa: E402
    ChannelCatalog,
    ConceptDraft,
    EditorialStore,
    SourceReference,
    load_channels,
)
from social_management.models import ConnectionRecord  # noqa: E402
from social_management.registry import load_catalog  # noqa: E402


def draft(**changes) -> ConceptDraft:
    return ConceptDraft.model_validate(
        {
            "channel_id": "ai-content",
            "title": "Build a small offline assistant",
            "audience": "People trying local AI",
            "hook": "What still works with Wi-Fi off?",
            "original_contribution": "Demonstrate a new measured offline experiment.",
            "outline": ["Question", "Controlled experiment", "Results and limitations"],
            "format": "long-form",
            "sources": [
                {
                    "kind": "blog-post",
                    "repository": "Example/Blog",
                    "revision": "abc1234",
                    "path": "content/local-ai.mdx",
                    "note": "Synthetic source for a contract test",
                }
            ],
            "rights_note": "Use original recorded results and licensed assets.",
            "effort": "small",
            **changes,
        }
    )


@pytest.fixture
def store(tmp_path: Path) -> EditorialStore:
    return EditorialStore(tmp_path / "private/editorial.sqlite3", load_channels(load_catalog()))


def decide(store, item, decision="approve"):
    return store.decide(
        item["id"],
        item["revision"],
        decision,
        actor="owner",
        reason="Synthetic explicit owner decision",
        confirmation=f"{item['id']}@{item['revision']}",
    )


def connection(identity="one", profile="content-main", account="synthetic-channel"):
    return ConnectionRecord(
        id=identity,
        profile_id=profile,
        provider_id="youtube",
        account_id=account,
        account_name="Test channel",
        scopes=["read"],
        connected_at=datetime.now(timezone.utc),
        verified_at=datetime.now(timezone.utc),
    )


def test_first_run_lists_three_unbound_channels_and_no_publish_permission(store):
    report = store.report([])
    assert {c["purpose"] for c in report["channels"]} == {
        "walkthroughs",
        "original-content",
        "gaming",
    }
    assert {c["connection_state"] for c in report["channels"]} == {"unbound"}
    assert report["concepts"] == []
    assert report["publication"] == "separate-final-approval-required"
    assert report["analytics"] == "not-connected"


def test_approval_survives_restart_but_edit_invalidates_it_and_retains_history(store):
    first = store.submit(draft())
    with pytest.raises(ValueError, match="approved concept"):
        store.brief(first["id"], 1)
    approved = decide(store, first)
    reopened = EditorialStore(store.path, load_channels(load_catalog()))
    brief = reopened.brief(first["id"], approved["revision"])
    assert brief["publication_approved"] is False
    assert brief["profile_id"] == "content-main"
    edited = reopened.edit(first["id"], approved["revision"], draft(title="Changed experiment"))
    assert edited["state"] == "awaiting-approval"
    with pytest.raises(ValueError, match="approved concept"):
        reopened.brief(first["id"], edited["revision"])
    history = reopened.history(first["id"])
    assert [e["action"] for e in history] == ["submit", "approve", "edit"]
    assert history[0]["record"]["draft"]["title"] != edited["draft"]["title"]
    assert history[1]["reviewed_revision"] == 1
    if sys.platform != "win32":
        assert store.path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("action,state", [("reject", "rejected"), ("revise", "changes-requested")])
def test_negative_decision_revokes_production_permission(store, action, state):
    approved = decide(store, store.submit(draft()))
    result = decide(store, approved, action)
    assert result["state"] == state
    with pytest.raises(ValueError, match="approved concept"):
        store.brief(result["id"], result["revision"])


def test_exact_confirmation_and_stale_decision_fail_without_mutation(store):
    item = store.submit(draft())
    with pytest.raises(ValueError, match="exact"):
        store.decide(
            item["id"], 1, "approve", actor="owner", reason="Approve", confirmation="wrong"
        )
    assert len(store.history(item["id"])) == 1
    decide(store, item)
    with pytest.raises(ValueError, match="stale"):
        decide(store, item)
    assert len(store.history(item["id"])) == 2


def test_two_simultaneous_decisions_cannot_both_apply(store):
    item = store.submit(draft())

    def attempt():
        try:
            return decide(store, item)["state"]
        except ValueError:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["approved", "stale"]
    assert len(store.history(item["id"])) == 2


def test_channel_config_change_and_pause_block_old_briefs(store):
    item = decide(store, store.submit(draft()))
    store.pause("ai-content", True)
    with pytest.raises(ValueError, match="paused"):
        store.brief(item["id"], item["revision"])
    store.pause("ai-content", False)
    assert store.brief(item["id"], item["revision"])
    catalog = load_channels(load_catalog()).model_dump()
    catalog["channels"][1]["description"] = "A new editorial direction"
    changed = EditorialStore(store.path, ChannelCatalog.model_validate(catalog))
    with pytest.raises(ValueError, match="configuration changed"):
        changed.brief(item["id"], item["revision"])
    with pytest.raises(ValueError, match="configuration changed"):
        decide(changed, item)
    assert changed.report([])["concepts"][0]["configuration_current"] is False
    revised = changed.edit(item["id"], item["revision"], draft())
    new_approval = decide(changed, revised)
    assert changed.brief(item["id"], new_approval["revision"])


def test_channel_and_source_validation_precedes_state_creation(store):
    with pytest.raises(ValueError, match="unknown channel"):
        store.submit(draft(channel_id="missing"))
    with pytest.raises(ValueError, match="source kind"):
        store.submit(draft(channel_id="gaming"))
    assert not store.path.exists()
    with pytest.raises(ValidationError):
        draft(outline=[""])
    with pytest.raises(ValidationError):
        SourceReference(
            kind="blog-post",
            repository="Example/Blog",
            revision="abc1234",
            path="../../secret",
            note="Not permitted",
        )


def test_bind_rejects_wrong_profile_and_duplicate_remote_account_and_redacts_report(store):
    first = connection()
    with pytest.raises(ValueError, match="match"):
        store.bind("opentechnology", first)
    store.bind("ai-content", first)
    duplicate = connection("two", "stream-main")
    with pytest.raises(ValueError, match="already bound"):
        store.bind("gaming", duplicate)
    report = store.report([first])
    assert report["channels"][1]["connection_state"] == "locally-bound"
    assert first.account_id not in json.dumps(report)
    assert first.account_name not in json.dumps(report)
    assert store.report([])["channels"][1]["connection_state"] == "reconnect-required"
    changed = connection(account="another-channel")
    assert store.report([changed])["channels"][1]["connection_state"] == "reconnect-required"
    store.unbind("ai-content")
    store.bind("gaming", duplicate)
    assert store.report([duplicate])["channels"][2]["connection_state"] == "locally-bound"


def test_unknown_database_version_and_corruption_are_not_reset(store):
    store.report([])
    with sqlite3.connect(store.path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="unsupported"):
        store.report([])
    store.path.write_bytes(b"corrupt database")
    with pytest.raises(sqlite3.DatabaseError):
        store.report([])
    assert store.path.read_bytes() == b"corrupt database"


def test_invalid_decisions_and_missing_concepts_leave_history_intact(store):
    item = store.submit(draft())
    for action, actor, reason in [
        ("invalid", "owner", "answer"),
        ("approve", "", "answer"),
        ("approve", "owner", ""),
    ]:
        with pytest.raises(ValueError):
            store.decide(
                item["id"], 1, action, actor=actor, reason=reason, confirmation=f"{item['id']}@1"
            )
    with pytest.raises(ValueError, match="unknown concept"):
        store.brief("missing", 1)
    assert len(store.history(item["id"])) == 1


def test_catalog_rejects_duplicate_channels_and_missing_profile(tmp_path):
    import yaml

    value = load_channels(load_catalog()).model_dump()
    value["channels"].append(value["channels"][0])
    with pytest.raises(ValueError, match="unique"):
        ChannelCatalog.model_validate(value)
    value["channels"].pop()
    value["channels"][0]["profile_id"] = "missing"
    path = tmp_path / "channels.yaml"
    path.write_text(yaml.safe_dump(value))
    with pytest.raises(ValueError, match="social profile"):
        load_channels(load_catalog(), path)


def test_cli_input_limit_and_markdown_cannot_embed_source_html(tmp_path, capsys):
    source = tmp_path / "draft.json"
    source.write_text("x" * 128001)
    prefix = ["portfolio", "--state-dir", str(tmp_path / "state")]
    assert main([*prefix, "submit", str(source)]) == 2
    assert "128 KB" in capsys.readouterr().err
    source.write_text(draft(title="<script>example</script>").model_dump_json())
    assert main([*prefix, "submit", str(source)]) == 0
    capsys.readouterr()
    assert main([*prefix, "report", "--format", "markdown"]) == 0
    output = capsys.readouterr().out
    assert "<script>" not in output
    assert "&#60;script&#62;" in output


def test_malformed_channel_yaml_fails_cleanly_before_state_creation(tmp_path, capsys):
    config = tmp_path / "channels.yaml"
    config.write_text("channels: [\n")
    state = tmp_path / "state"
    assert (
        main(["portfolio", "--state-dir", str(state), "--channels", str(config), "channels"]) == 2
    )
    assert json.loads(capsys.readouterr().err) == {"error": "invalid channel YAML"}
    assert not state.exists()


def test_cli_roundtrip_reports_real_state_and_returns_errors_without_success(tmp_path, capsys):
    source = tmp_path / "draft.json"
    source.write_text(draft().model_dump_json())
    prefix = ["portfolio", "--state-dir", str(tmp_path / "state")]
    assert main([*prefix, "submit", str(source)]) == 0
    item = json.loads(capsys.readouterr().out)
    assert main([*prefix, "brief", item["id"], "--revision", "1"]) == 2
    assert "approved concept" in capsys.readouterr().err
    assert (
        main(
            [
                *prefix,
                "decide",
                item["id"],
                "approve",
                "--revision",
                "1",
                "--confirm",
                f"{item['id']}@1",
                "--actor",
                "owner",
                "--reason",
                "Approve the synthetic concept",
            ]
        )
        == 0
    )
    approved = json.loads(capsys.readouterr().out)
    assert main([*prefix, "brief", item["id"], "--revision", str(approved["revision"])]) == 0
    assert json.loads(capsys.readouterr().out)["publication_approved"] is False
    assert main([*prefix, "report", "--format", "markdown"]) == 0
    assert "approved" in capsys.readouterr().out
    assert main([*prefix, "bind", "ai-content", "missing-connection"]) == 2
    assert "unknown connection" in capsys.readouterr().err
