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


def test_recording_slice_has_no_live_stream_render_remote_oauth_or_publish_command():
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


def test_all_app_commands_have_explicit_local_main_acl_and_operational_origin_checks():
    source = (PREVIEW / "src-tauri/src/lib.rs").read_text()
    registered = {item.strip() for item in re.search(r"generate_handler!\[([\s\S]*?)\]", source).group(1).split(",") if item.strip()}
    capability = json.loads((PREVIEW / "src-tauri/capabilities/preview.json").read_text())
    expected = {"allow-" + command.replace("_", "-") for command in registered}
    assert expected <= set(capability["permissions"])
    build = (PREVIEW / "src-tauri/build.rs").read_text()
    for command in registered:
        assert f'"{command}"' in build
    for command in registered:
        if command.startswith("production_"):
            body = source.split(f"async fn {command}(", 1)[1].split("#[tauri::command]", 1)[0]
            assert "production_admit(&window)?" in body
    for command in ("production_stop_recording", "production_recover"):
        body = source.split(f"async fn {command}(", 1)[1].split("#[tauri::command]", 1)[0]
        assert "state.preferences()" not in body
        assert "credentials" not in body
    start = source.split("async fn production_start_recording(", 1)[1].split("#[tauri::command]", 1)[0]
    assert "state.idle_production_connection()?" in start
    assert start.index("production::admit_managed_recording()?") < start.index("state.idle_production_connection()?")
    idle = source.split("fn idle_production_connection(", 1)[1].split("#[tauri::command]", 1)[0]
    assert 'require_pack("stream")' in idle
    assert "self.preferences()?" in idle
    for command in ("production_status", "production_audio_inputs", "production_scenes"):
        body = source.split(f"async fn {command}(", 1)[1].split("#[tauri::command]", 1)[0]
        assert "|| state.idle_production_connection()" in body
        assert "state.production.lock().await" not in body
    production = (PREVIEW / "src-tauri/src/production.rs").read_text()
    for command, helper in (("production_set_mute", "set_observed_mute"), ("production_switch_scene", "switch_observed_scene")):
        body = source.split(f"async fn {command}(", 1)[1].split("#[tauri::command]", 1)[0].split("pub fn run", 1)[0]
        assert "expected_context_id: String" in body
        assert "expected_context_id: Option" not in body
        assert f"production::{helper}" in body
        assert "|| state.idle_production_connection()" in body
        admission = production.split(f"pub async fn {helper}(", 1)[1].split("\n}", 1)[0]
        assert admission.index("controller.lock().await") < admission.index("admit_observed_mutation(&expected)?") < admission.index("resolve_connection(load)?")
    assert "social_manager::recording_profiles" in start



def test_native_safety_and_presentation_survive_navigation_independently():
    source = (PREVIEW / "src-tauri/src/lib.rs").read_text()
    assert "production: tokio::sync::Mutex<production::Controller>" in source
    assert "controller.allow_preferences" in source
    assert "controller.allow_password_change" in source
    save = source.split("async fn preview_save_preferences(", 1)[1].split("#[tauri::command]", 1)[0]
    password = source.split("async fn preview_set_obs_password(", 1)[1].split("#[tauri::command]", 1)[0]
    assert "invalidate_idle_observations()" in save
    assert "invalidate_idle_observations()" in password
    assert save.index("invalidate_idle_observations()") < save.index(".save(&preferences)")
    assert password.index("invalidate_idle_observations()") < password.index('.set("obs-password"')
    page = (PREVIEW / "src/routes/+page.svelte").read_text()
    assert page.index("<ProductionControls") < page.index("{:else if preferences.active_page")
    assert page.count("<ProductionControls") == 1
    control = (PREVIEW / "src/lib/ProductionControls.svelte").read_text()
    assert control.index("production_stop_recording") < control.index("{#if showTasks}")
    assert 'class="stop" disabled={view.working}' in control
    assert 'disabled={view.working || view.inspecting}' not in control
    assert "disabled={view.working || view.audioLoading}" not in control
    assert "sessionId: status?.session_id" in control
