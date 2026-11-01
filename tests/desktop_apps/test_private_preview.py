"""Private preview IPC and packaging boundaries; no public or legacy replacement claims."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / "apps/extend"


def test_private_identity_and_permissions_do_not_merge_legacy_trust_boundaries():
    config = json.loads((PREVIEW / "src-tauri/tauri.conf.json").read_text())
    assert config["identifier"] not in {"com.streamextend.app", "com.creatorextend.app"}
    assert config["app"]["security"]["csp"]
    permissions = json.loads((PREVIEW / "src-tauri/capabilities/preview.json").read_text())
    assert permissions["windows"] == ["main"]
    assert not permissions.get("remote")
    assert "social-manager:default" not in permissions["permissions"]
    assert all("*" not in item for item in permissions["permissions"])


def test_preview_has_no_broadcast_render_remote_oauth_or_publish_command():
    source = (PREVIEW / "src-tauri/src/lib.rs").read_text()
    handler = re.search(r"generate_handler!\[([\s\S]*?)\]", source).group(1)
    forbidden = {"obs_toggle_stream", "obs_start_stream_session", "obs_stop_stream_session",
                 "comfyui_queue", "comfyui_queue_configured", "blender_job_start",
                 "remote_connect", "remote_approve", "remote_request"}
    registered = {item.strip() for item in handler.split(",")}
    assert not registered & forbidden
    assert "RecordingStatus::Editing | RecordingStatus::Published" in source


def test_discovery_mapping_matches_every_real_module_once():
    navigation = json.loads((ROOT / "configs/ui/combined-navigation.json").read_text())
    listed = [item for group in navigation["groups"] for item in group["modules"]]
    actual = {item.name for item in (ROOT / "modules").iterdir() if item.is_dir() and (item / "README.md").exists()}
    assert len(listed) == len(set(listed))
    assert set(listed) == actual
