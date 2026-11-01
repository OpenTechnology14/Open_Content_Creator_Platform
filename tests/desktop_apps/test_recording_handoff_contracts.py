"""Offline desktop contracts for P-065 recording handoff and profile workspaces."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_both_apps_share_one_recording_library_crate() -> None:
    for app in ("stream-extend", "creator-extend"):
        cargo = _read(f"apps/{app}/src-tauri/Cargo.toml")
        assert 'recording-library = { path = "../../shared/recording-library" }' in cargo
    source = _read("apps/shared/recording-library/src/lib.rs")
    assert "lock_exclusive" in source
    assert "canonicalize()" in source
    assert "fs::copy" not in source


def test_stream_session_owns_recording_and_creator_inbox_commands_are_registered() -> None:
    stream = _read("apps/stream-extend/src-tauri/src/lib.rs")
    obs = _read("apps/stream-extend/src-tauri/src/obs.rs")
    creator = _read("apps/creator-extend/src-tauri/src/lib.rs")
    stream_ui = _read("apps/stream-extend/src/routes/+page.svelte")
    creator_ui = _read("apps/creator-extend/src/routes/+page.svelte")
    assert "obs_start_stream_session" in stream and "obs_stop_stream_session" in stream
    start_body = obs.split("pub async fn start_live_session", 1)[1].split(
        "pub async fn stop_live_session", 1
    )[0]
    stop_body = obs.split("pub async fn stop_live_session", 1)[1].split("#[cfg(test)]", 1)[0]
    assert start_body.index("client.recording().start()") < start_body.index(
        "client.streaming().start()"
    )
    assert stop_body.index("client.streaming().stop()") < stop_body.index(
        "client.recording().stop()"
    )
    assert "obs_start_stream_session" in stream_ui
    assert "obs_stop_stream_session" in stream_ui
    for command in (
        "recordings_list",
        "recordings_import",
        "recordings_update",
        "recordings_reveal",
    ):
        assert command in creator
    assert "RecordingLibrary" in creator_ui and "Recordings" in creator_ui


def test_both_apps_expose_persistent_profile_switching_and_account_routing() -> None:
    for app, kind in (("stream-extend", "stream"), ("creator-extend", "content")):
        page = _read(f"apps/{app}/src/routes/+page.svelte")
        assert "ProfileSwitcher" in page
        assert f'kind="{kind}"' in page
    social = _read("apps/shared/ui/SocialManagement.svelte")
    native = _read("apps/shared/social-manager/src/lib.rs")
    for value in ("brand_id", "provider_id", "capability", "connection_id"):
        assert value in social and value in native
    assert "activate_profile" in social
    assert "save_selection" in social
    assert "disconnectAccount" in social
