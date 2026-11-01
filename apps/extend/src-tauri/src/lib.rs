//! Private shell preview. Existing native adapters are reused for observations only.
#[allow(dead_code)]
#[path = "../../../creator-extend/src-tauri/src/comfyui.rs"]
mod comfyui;
#[allow(dead_code)]
#[path = "../../../stream-extend/src-tauri/src/obs.rs"]
mod obs;
mod preferences;

use local_settings::{LocalSettings, OsCredentials};
use preferences::Preferences;
use recording_library::{RecordingLibrary, RecordingOrigin, RecordingStatus, RecordingView};
use setup_engine::{
    CheckObservation, ReadinessManifest, ReadinessSnapshot, SetupEngine, SyncSettingsView,
};
use tauri::Manager;

struct Preview {
    preferences: LocalSettings,
    credentials: OsCredentials,
    readiness: SetupEngine,
    obs: obs::ObsClientCache,
    recordings: RecordingLibrary,
}
impl Preview {
    fn preferences(&self) -> Result<Preferences, String> {
        let value = if self.preferences.path().exists() {
            self.preferences
                .load()
                .map_err(|_| "Preview settings need recovery; original apps are unaffected")?
        } else {
            Preferences::initial()
        };
        value.validate()?;
        Ok(value)
    }
    fn list_recordings(&self) -> Result<Vec<RecordingView>, String> {
        self.preferences()?.require_pack("content")?;
        self.recordings.list()
    }
}

async fn observe(
    prefs: &Preferences,
    cache: &obs::ObsClientCache,
    password: Result<Option<String>, String>,
) -> Vec<CheckObservation> {
    let mut checks = Vec::new();
    if prefs.require_pack("stream").is_ok() {
        match password {
            Ok(password) => {
                let status =
                    obs::get_status(cache, &prefs.obs_host, prefs.obs_port, password.as_deref())
                        .await;
                checks.push(if status.connected {
                    CheckObservation::ready(
                        "stream.obs.websocket",
                        "Authenticated OBS connection",
                        Default::default(),
                    )
                } else {
                    CheckObservation::blocked(
                        "stream.obs.websocket",
                        "Open OBS and verify WebSocket settings",
                    )
                });
                let scenes = if status.connected {
                    obs::get_scenes(cache, &prefs.obs_host, prefs.obs_port, password.as_deref())
                        .await
                        .ok()
                } else {
                    None
                };
                checks.push(if scenes.is_some_and(|value| !value.is_empty()) {
                    CheckObservation::ready(
                        "stream.obs.scenes",
                        "OBS scene collection observed",
                        Default::default(),
                    )
                } else {
                    CheckObservation::blocked(
                        "stream.obs.scenes",
                        "OBS scene verification is pending",
                    )
                });
            }
            Err(_) => {
                checks.push(CheckObservation::blocked(
                    "stream.obs.websocket",
                    "OS credential manager unavailable; reconnect when unlocked",
                ));
                checks.push(CheckObservation::blocked(
                    "stream.obs.scenes",
                    "OBS scene verification is pending",
                ));
            }
        }
    }
    if prefs.require_pack("content").is_ok() {
        let connected = comfyui::get_status(&prefs.comfyui_url)
            .await
            .is_ok_and(|status| status.connected);
        checks.push(if connected {
            CheckObservation::ready(
                "creator.comfyui.api",
                "ComfyUI API observed",
                Default::default(),
            )
        } else {
            CheckObservation::blocked(
                "creator.comfyui.api",
                "Start ComfyUI or check its connection",
            )
        });
        checks.push(
            if comfyui::list_committed_workflows().is_ok_and(|items| !items.is_empty()) {
                CheckObservation::ready(
                    "creator.comfyui.workflows",
                    "Bundled workflow catalog loaded",
                    Default::default(),
                )
            } else {
                CheckObservation::blocked(
                    "creator.comfyui.workflows",
                    "Bundled catalog is unavailable",
                )
            },
        );
    }
    checks
}

#[tauri::command]
fn preview_preferences(state: tauri::State<'_, Preview>) -> Result<Preferences, String> {
    state.preferences()
}
#[tauri::command]
async fn preview_save_preferences(
    state: tauri::State<'_, Preview>,
    preferences: Preferences,
) -> Result<Preferences, String> {
    preferences.validate()?;
    state
        .preferences
        .save(&preferences)
        .map_err(|_| "Could not save preview settings")?;
    state.obs.clear().await;
    Ok(preferences)
}
#[tauri::command]
async fn preview_set_obs_password(
    state: tauri::State<'_, Preview>,
    password: String,
) -> Result<(), String> {
    state.preferences()?.require_pack("stream")?;
    if password.is_empty() || password.len() > 4096 {
        return Err("Enter a valid OBS password".into());
    }
    state
        .credentials
        .set("obs-password", &password)
        .map_err(|_| "Could not save password in the OS credential manager")?;
    state.obs.clear().await;
    Ok(())
}
#[tauri::command]
fn setup_last_readiness(
    state: tauri::State<'_, Preview>,
) -> Result<Option<ReadinessSnapshot>, String> {
    // Never display stale observations for a pack that has just been disabled.
    let prefs = state.preferences()?;
    Ok(state.readiness.latest()?.map(|mut value| {
        value.checks.retain(|item| {
            (item.check_id.starts_with("stream.") && prefs.require_pack("stream").is_ok())
                || (item.check_id.starts_with("creator.") && prefs.require_pack("content").is_ok())
        });
        value.capabilities.retain(|item| {
            (item.capability_id == "obs-control" && prefs.require_pack("stream").is_ok())
                || (item.capability_id == "comfy-workflows"
                    && prefs.require_pack("content").is_ok())
        });
        value
    }))
}
#[tauri::command]
async fn setup_refresh_readiness(
    state: tauri::State<'_, Preview>,
) -> Result<ReadinessSnapshot, String> {
    let prefs = state.preferences()?;
    let mut manifest = ReadinessManifest::parse(include_str!(
        "../../../../configs/setup/extend-preview.json"
    ))?;
    let password = if prefs.require_pack("stream").is_ok() {
        state
            .credentials
            .get("obs-password")
            .map_err(|_| "OS credential manager unavailable".to_string())
    } else {
        Ok(None)
    };
    let checks = observe(&prefs, &state.obs, password).await;
    manifest.capabilities.retain(|item| {
        (item.id == "obs-control" && prefs.require_pack("stream").is_ok())
            || (item.id == "comfy-workflows" && prefs.require_pack("content").is_ok())
    });
    state
        .readiness
        .save_snapshot(ReadinessSnapshot::from_manifest(
            "preview", checks, &manifest,
        ))
}
#[tauri::command]
fn setup_sync_settings() -> SyncSettingsView {
    SyncSettingsView {
        enabled: false,
        base_url: String::new(),
        project_id: String::new(),
        machine_id: "preview".into(),
        api_key_set: false,
    }
}
#[tauri::command]
fn setup_save_sync_settings() -> Result<(), String> {
    Err("Cloud sync is unavailable in this private preview".into())
}
#[tauri::command]
fn setup_sync_now() -> Result<(), String> {
    Err("Cloud sync is unavailable in this private preview".into())
}
#[tauri::command]
async fn obs_connection_diagnostic(
    state: tauri::State<'_, Preview>,
) -> Result<obs::ObsConnectionDiagnostic, String> {
    let prefs = state.preferences()?;
    prefs.require_pack("stream")?;
    let password = state
        .credentials
        .get("obs-password")
        .map_err(|_| "OS credential manager unavailable")?;
    Ok(obs::diagnose_connection(&prefs.obs_host, prefs.obs_port, password.as_deref()).await)
}
#[tauri::command]
fn obs_recording_test() -> Result<(), String> {
    Err("Use Stream Extend for recordings during this preview".into())
}
#[tauri::command]
fn preview_workflows(
    state: tauri::State<'_, Preview>,
) -> Result<Vec<comfyui::WorkflowInfo>, String> {
    state.preferences()?.require_pack("content")?;
    comfyui::list_committed_workflows().map_err(|_| "Bundled workflow catalog unavailable".into())
}
#[tauri::command]
fn recordings_list(state: tauri::State<'_, Preview>) -> Result<Vec<RecordingView>, String> {
    state.list_recordings()
}
#[tauri::command]
fn recordings_import(
    state: tauri::State<'_, Preview>,
    path: String,
    content_profile_id: Option<String>,
) -> Result<RecordingView, String> {
    state.preferences()?.require_pack("content")?;
    state.recordings.register(
        path,
        RecordingOrigin::ManualImport,
        None,
        content_profile_id.as_deref(),
    )
}
#[tauri::command]
fn recordings_update(
    state: tauri::State<'_, Preview>,
    id: String,
    status: RecordingStatus,
    content_profile_id: Option<String>,
) -> Result<RecordingView, String> {
    state.preferences()?.require_pack("content")?;
    if matches!(
        status,
        RecordingStatus::Editing | RecordingStatus::Published
    ) {
        return Err("Editing and publishing remain in Creator Extend during this preview".into());
    }
    state
        .recordings
        .update(&id, status, content_profile_id.as_deref())
}
#[tauri::command]
fn recordings_reveal(state: tauri::State<'_, Preview>, id: String) -> Result<(), String> {
    state.preferences()?.require_pack("content")?;
    state.recordings.reveal(&id)
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(setup_wizard::init())
        .plugin(social_manager::init())
        .invoke_handler(tauri::generate_handler![
            preview_preferences,
            preview_save_preferences,
            preview_set_obs_password,
            setup_last_readiness,
            setup_refresh_readiness,
            setup_sync_settings,
            setup_save_sync_settings,
            setup_sync_now,
            obs_connection_diagnostic,
            obs_recording_test,
            preview_workflows,
            recordings_list,
            recordings_import,
            recordings_update,
            recordings_reveal
        ])
        .setup(|app| {
            let root = app.path().local_data_dir()?.join("HybridCreatorPlatform");
            let identity = app.config().identifier.clone();
            app.manage(Preview {
                preferences: LocalSettings::new(root.join("extend-preview"), "preferences")?,
                credentials: OsCredentials::new("HybridCreatorPlatform", &identity)?,
                readiness: SetupEngine::new(&root.join("extend-preview"), &identity)?,
                obs: obs::ObsClientCache::new(),
                recordings: RecordingLibrary::new(root.join("recording-library"))?,
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Extend Preview could not start");
}

#[cfg(test)]
mod preview_tests {
    use super::*;
    use wiremock::matchers::{method, path};
    use wiremock::{Mock, MockServer, ResponseTemplate};

    #[tokio::test]
    async fn locked_obs_credentials_do_not_block_create_readiness() {
        let server = MockServer::start().await;
        Mock::given(method("GET"))
            .and(path("/system_stats"))
            .respond_with(
                ResponseTemplate::new(200).set_body_json(serde_json::json!({"devices": []})),
            )
            .mount(&server)
            .await;
        Mock::given(method("GET"))
            .and(path("/queue"))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({"queue_pending": []})))
            .mount(&server).await;
        let mut prefs = Preferences::initial();
        prefs.comfyui_url = server.uri();
        let checks = observe(
            &prefs,
            &obs::ObsClientCache::new(),
            Err("synthetic vault failure".into()),
        )
        .await;
        let status = |id| {
            checks
                .iter()
                .find(|item| item.check_id == id)
                .unwrap()
                .status
                .clone()
        };
        assert_eq!(
            status("stream.obs.websocket"),
            setup_engine::ReadinessStatus::Blocked
        );
        assert_eq!(
            status("creator.comfyui.api"),
            setup_engine::ReadinessStatus::Ready
        );
    }

    #[tokio::test]
    async fn create_only_never_checks_obs_or_exposes_unrelated_failure() {
        let mut prefs = Preferences::initial();
        prefs.enabled_packs = vec!["content".into()];
        prefs.comfyui_url = "http://127.0.0.1:1".into();
        let checks = observe(
            &prefs,
            &obs::ObsClientCache::new(),
            Err("vault must not be used".into()),
        )
        .await;
        assert_eq!(checks.len(), 2);
        assert!(checks
            .iter()
            .all(|item| item.check_id.starts_with("creator.")));
    }

    #[test]
    fn disabled_create_pack_rejects_the_native_library_operation() {
        let root = std::env::temp_dir().join(format!("hcp-preview-{}", uuid::Uuid::new_v4()));
        let store = LocalSettings::new(root.join("preview"), "preferences").unwrap();
        let mut prefs = Preferences::initial();
        prefs.enabled_packs = vec!["stream".into()];
        store.save(&prefs).unwrap();
        let preview = Preview {
            preferences: store,
            credentials: OsCredentials::new("HybridCreatorPlatform", "test-preview").unwrap(),
            readiness: SetupEngine::new(&root, "test-preview").unwrap(),
            obs: obs::ObsClientCache::new(),
            recordings: RecordingLibrary::new(root.join("recordings")).unwrap(),
        };
        assert!(preview.list_recordings().is_err());
        prefs.enabled_packs = vec!["content".into()];
        preview.preferences.save(&prefs).unwrap();
        assert!(preview.list_recordings().unwrap().is_empty());
        std::fs::remove_dir_all(root).unwrap();
    }
}
