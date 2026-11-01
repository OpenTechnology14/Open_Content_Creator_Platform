//! Stream Extend — Tauri 2 desktop + mobile app.
//!
//! Wraps OBS WebSocket, AI effects, overlays, audio monitoring,
//! AI agent management, and Grafana dashboards into one app.
//! Connects to the relay for remote access + subscriptions.

mod autopilot;
mod autopilot_control;
pub mod connection_settings;
pub mod obs; // pub so tests/obs_contract.rs (an external integration test) can call it directly
mod relay;
mod voice_studio;

use std::sync::{Arc, Mutex};

use command_error::ErrorEnvelope;
use connection_settings::{
    ConnectionPersistence, ConnectionSettingsUpdate, ConnectionSettingsView,
};
use recording_library::{RecordingLibrary, RecordingOrigin, RecordingView};
use relay_client::control::{
    RemotePersistence, RemoteRuntimeView, RemoteSettings, RemoteSettingsUpdate, RemoteSettingsView,
};
use relay_client::{Product, RelayConfig, RelayMode};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use setup_engine::{
    CheckObservation, ReadinessManifest, ReadinessSnapshot, SetupEngine, SyncReport,
    SyncSettingsUpdate, SyncSettingsView,
};
use tauri::{Emitter, Manager};

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// OBS WebSocket host (default: localhost).
    pub obs_host: String,
    /// OBS WebSocket port (default: 4455).
    pub obs_port: u16,
    /// OBS WebSocket password (if set).
    pub obs_password: Option<String>,
    /// ComfyUI API URL (default: http://localhost:8188).
    pub comfyui_url: String,
    /// Grafana URL (default: http://localhost:3000).
    pub grafana_url: String,
    /// FastAPI backend URL (default: http://localhost:8000).
    pub api_url: String,
    /// Relay configuration.
    pub relay: RelayConfig,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            obs_host: "localhost".into(),
            obs_port: 4455,
            obs_password: None,
            comfyui_url: "http://localhost:8188".into(),
            grafana_url: "http://localhost:3000".into(),
            api_url: "http://localhost:8000".into(),
            relay: RelayConfig {
                mode: RelayMode::Local,
                product: Product::StreamExtend,
                ..RelayConfig::default()
            },
        }
    }
}

type ConfigState<'r> = tauri::State<'r, Arc<Mutex<AppConfig>>>;
type ObsCacheState<'r> = tauri::State<'r, Arc<obs::ObsClientCache>>;
type ObsSessionState<'r> = tauri::State<'r, obs::ObsSessionState>;
type RecordingLibraryState<'r> = tauri::State<'r, RecordingLibrary>;
type PersistenceState<'r> = tauri::State<'r, ConnectionPersistence>;
type RemoteSettingsState<'r> = tauri::State<'r, Arc<Mutex<RemoteSettings>>>;
type RemotePersistenceState<'r> = tauri::State<'r, RemotePersistence>;
type RemoteControlState<'r> = tauri::State<'r, Arc<relay::StreamRemoteControl>>;
type SetupEngineState<'r> = tauri::State<'r, SetupEngine>;

// ---------------------------------------------------------------------------
// Tauri commands (called from frontend)
// ---------------------------------------------------------------------------

/// Get persisted connection settings. Secret values never cross this boundary.
#[tauri::command]
fn get_config(state: ConfigState<'_>) -> ConnectionSettingsView {
    ConnectionSettingsView::from(&*state.lock().unwrap())
}

/// Persist validated endpoints and optional credential updates, then reconnect lazily.
#[tauri::command]
async fn set_config(
    state: ConfigState<'_>,
    persistence: PersistenceState<'_>,
    obs_cache: ObsCacheState<'_>,
    config: ConnectionSettingsUpdate,
) -> Result<ConnectionSettingsView, String> {
    let current = state.lock().unwrap().clone();
    let store = persistence.inner().clone();
    let next = tauri::async_runtime::spawn_blocking(move || store.save(&current, config))
        .await
        .map_err(|_| "Connection settings could not be saved".to_string())??;
    let obs_changed = {
        let old = state.lock().unwrap();
        old.obs_host != next.obs_host
            || old.obs_port != next.obs_port
            || old.obs_password != next.obs_password
    };
    *state.lock().unwrap() = next.clone();
    if obs_changed {
        obs_cache.clear().await;
    }
    Ok(ConnectionSettingsView::from(&next))
}

#[tauri::command]
fn remote_get_settings(state: RemoteSettingsState<'_>) -> RemoteSettingsView {
    state.lock().unwrap().view()
}

#[tauri::command]
async fn remote_save_settings(
    state: RemoteSettingsState<'_>,
    persistence: RemotePersistenceState<'_>,
    control: RemoteControlState<'_>,
    settings: RemoteSettingsUpdate,
) -> Result<RemoteSettingsView, String> {
    let current = state.lock().unwrap().clone();
    let store = persistence.inner().clone();
    let next = tauri::async_runtime::spawn_blocking(move || store.save(&current, settings))
        .await
        .map_err(|_| "Remote settings could not be saved".to_string())??;
    *state.lock().unwrap() = next.clone();
    control.disconnect().await;
    Ok(next.view())
}

#[tauri::command]
async fn remote_connect(
    state: RemoteSettingsState<'_>,
    control: RemoteControlState<'_>,
) -> Result<RemoteRuntimeView, String> {
    let settings = state.lock().unwrap().clone();
    if let RelayMode::SelfHosted {
        ref url,
        ref api_key,
    } = settings.relay_config(Product::StreamExtend)?.mode
    {
        relay_client::auth::validate_self_hosted(url, api_key.as_deref())
            .await
            .map_err(|error| error.to_string())?;
    }
    control.connect(&settings).await?;
    Ok(control.status().await)
}

#[tauri::command]
async fn remote_disconnect(control: RemoteControlState<'_>) -> Result<RemoteRuntimeView, String> {
    control.disconnect().await;
    Ok(control.status().await)
}

#[tauri::command]
async fn remote_status(control: RemoteControlState<'_>) -> Result<RemoteRuntimeView, String> {
    Ok(control.status().await)
}

#[tauri::command]
async fn remote_approve(
    control: RemoteControlState<'_>,
    id: String,
) -> Result<serde_json::Value, String> {
    control.approve(&id).await
}

#[tauri::command]
async fn remote_deny(control: RemoteControlState<'_>, id: String) -> Result<(), String> {
    control.deny(&id).await
}

#[tauri::command]
async fn remote_request(
    control: RemoteControlState<'_>,
    target_device_id: String,
    target: String,
    action: String,
    payload: serde_json::Value,
) -> Result<String, String> {
    control
        .request(target_device_id, target, action, payload)
        .await
}

#[tauri::command]
fn setup_last_readiness(engine: SetupEngineState<'_>) -> Result<Option<ReadinessSnapshot>, String> {
    engine.latest()
}

#[tauri::command]
async fn setup_refresh_readiness(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
    engine: SetupEngineState<'_>,
) -> Result<ReadinessSnapshot, String> {
    let (host, port, password) = {
        let value = config.lock().unwrap();
        (
            value.obs_host.clone(),
            value.obs_port,
            value.obs_password.clone(),
        )
    };
    let diagnostic = obs::diagnose_connection(&host, port, password.as_deref()).await;
    let mut version_evidence = Map::new();
    if let Some(value) = diagnostic.obs_version.clone() {
        version_evidence.insert("detectedVersion".into(), Value::String(value));
    }
    if let Some(value) = diagnostic.websocket_version.clone() {
        version_evidence.insert("webSocketVersion".into(), Value::String(value));
    }
    version_evidence.insert(
        "diagnosticState".into(),
        Value::String(diagnostic.state.clone()),
    );
    let websocket = if diagnostic.state == "connected" {
        CheckObservation::ready(
            "stream.obs.websocket",
            "Authenticated to OBS WebSocket and read its version",
            version_evidence,
        )
    } else {
        CheckObservation::blocked("stream.obs.websocket", &diagnostic.detail)
    };
    let scenes = if diagnostic.state == "connected" {
        match obs::get_scenes(&obs_cache, &host, port, password.as_deref()).await {
            Ok(items) if !items.is_empty() => {
                let mut evidence = Map::new();
                evidence.insert("sceneCount".into(), Value::from(items.len() as u64));
                CheckObservation::ready(
                    "stream.obs.scenes",
                    "OBS returned a non-empty scene collection",
                    evidence,
                )
            }
            Ok(_) => CheckObservation::blocked(
                "stream.obs.scenes",
                "Create or import at least one OBS scene",
            ),
            Err(_) => CheckObservation::failed(
                "stream.obs.scenes",
                "OBS connected but its scene-list verification failed",
            ),
        }
    } else {
        CheckObservation::blocked(
            "stream.obs.scenes",
            "Scene verification waits for the OBS WebSocket check",
        )
    };
    let machine_id = engine.settings()?.machine_id;
    let manifest =
        ReadinessManifest::parse(include_str!("../../../../configs/setup/stream-extend.json"))?;
    engine.save_snapshot(ReadinessSnapshot::from_manifest(
        &machine_id,
        vec![websocket, scenes],
        &manifest,
    ))
}

#[tauri::command]
fn setup_sync_settings(engine: SetupEngineState<'_>) -> Result<SyncSettingsView, String> {
    engine.settings()
}

#[tauri::command]
fn setup_save_sync_settings(
    engine: SetupEngineState<'_>,
    settings: SyncSettingsUpdate,
) -> Result<SyncSettingsView, String> {
    engine.save_settings(settings)
}

#[tauri::command]
async fn setup_sync_now(engine: SetupEngineState<'_>) -> Result<SyncReport, String> {
    engine.inner().clone().publish_latest().await
}

/// Get OBS connection status. `obs::get_status` itself never errors — it
/// degrades to `connected: false` on any failure, since this is polled
/// every ~2s and shouldn't surface error UI for the routine "OBS isn't open
/// yet." The `Result` wrapper here is purely to satisfy Tauri's own
/// requirement that async commands taking `State` reference params return
/// `Result` — the `Err` arm is structurally unreachable.
#[tauri::command]
async fn obs_status(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
) -> Result<obs::ObsStatus, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    Ok(obs::get_status(&obs_cache, &host, port, password.as_deref()).await)
}

#[tauri::command]
async fn obs_connection_diagnostic(
    config: ConfigState<'_>,
) -> Result<obs::ObsConnectionDiagnostic, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    Ok(obs::diagnose_connection(&host, port, password.as_deref()).await)
}

#[tauri::command]
async fn obs_recording_test(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
) -> Result<obs::ObsRecordingReport, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    obs::run_recording_test(
        &obs_cache,
        &host,
        port,
        password.as_deref(),
        std::time::Duration::from_secs(3),
    )
    .await
}

/// Get current OBS scene list, each with its real `is_current` flag.
#[tauri::command]
async fn obs_scenes(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
) -> Result<Vec<obs::SceneInfo>, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    obs::get_scenes(&obs_cache, &host, port, password.as_deref()).await
}

/// Switch OBS scene. Returns the freshly-observed scene list — `obws`'s
/// `SetCurrentProgramScene` has no response data, so the real "observed
/// result" is a follow-up scene list, not `Ok(())`.
#[tauri::command]
async fn obs_switch_scene(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
    scene_name: String,
) -> Result<Vec<obs::SceneInfo>, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    obs::switch_scene(&obs_cache, &host, port, password.as_deref(), &scene_name).await
}

/// Get streaming status from OBS.
#[tauri::command]
async fn obs_stream_status(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
) -> Result<obs::StreamStatus, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    obs::get_stream_status(&obs_cache, &host, port, password.as_deref()).await
}

/// Local authoring only; preview playback is blocked when OBS is on air or unknown.
#[tauri::command]
async fn voice_studio_request(
    bridge: tauri::State<'_, voice_studio::VoiceStudio>,
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
    request: Value,
) -> Result<Value, String> {
    if request["action"] == "audio" {
        let (host, port, password) = {
            let c = config.lock().unwrap();
            (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
        };
        let status = obs::get_stream_status(&obs_cache, &host, port, password.as_deref())
            .await
            .map_err(|_| "Connect OBS and verify it is off air before auditioning")?;
        if status.active {
            return Err("Stop the broadcast before auditioning draft audio".into());
        }
    }
    bridge.call(request).await
}

/// Start/stop OBS stream. Returns OBS's own authoritative new state.
#[tauri::command]
async fn obs_toggle_stream(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
) -> Result<bool, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    obs::toggle_stream(&obs_cache, &host, port, password.as_deref()).await
}

#[derive(Debug, Clone, Serialize)]
struct StreamSessionReport {
    stream_active: bool,
    recording_active: bool,
    recording_owned: bool,
    detail: String,
    handoff: Option<RecordingView>,
}

#[tauri::command]
async fn obs_start_stream_session(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
    session: ObsSessionState<'_>,
    source_profile_id: Option<String>,
    content_profile_id: Option<String>,
) -> Result<StreamSessionReport, ErrorEnvelope> {
    for value in [source_profile_id.as_deref(), content_profile_id.as_deref()]
        .into_iter()
        .flatten()
    {
        if value.is_empty()
            || value.len() > 64
            || !value.bytes().all(|byte| {
                byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'-' | b'_')
            })
        {
            return Err(ErrorEnvelope::invalid_request(
                "Invalid profile selected for the live session.",
            ));
        }
    }
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    let result = obs::start_live_session(
        &obs_cache,
        &session,
        &host,
        port,
        password.as_deref(),
        source_profile_id,
        content_profile_id,
    )
    .await?;
    Ok(StreamSessionReport {
        stream_active: result.stream_active,
        recording_active: result.recording_active,
        recording_owned: result.recording_owned,
        detail: result.detail,
        handoff: None,
    })
}

#[tauri::command]
async fn obs_stop_stream_session(
    config: ConfigState<'_>,
    obs_cache: ObsCacheState<'_>,
    session: ObsSessionState<'_>,
    library: RecordingLibraryState<'_>,
) -> Result<StreamSessionReport, ErrorEnvelope> {
    let (host, port, password) = {
        let c = config.lock().unwrap();
        (c.obs_host.clone(), c.obs_port, c.obs_password.clone())
    };
    let result =
        obs::stop_live_session(&obs_cache, &session, &host, port, password.as_deref()).await?;
    let mut detail = result.detail;
    let handoff = match result.recording_path.as_deref() {
        Some(path) => match library.register(
            path,
            RecordingOrigin::StreamSession,
            result.source_profile_id.as_deref(),
            result.content_profile_id.as_deref(),
        ) {
            Ok(recording) => {
                detail = format!(
                    "Recording {} is ready in Creator Extend.",
                    recording.record.file_name
                );
                Some(recording)
            }
            Err(error) => {
                detail = format!(
                    "OBS finalized the recording, but Creator Extend inbox registration failed: {error}. Import the file manually in Creator Extend."
                );
                None
            }
        },
        None => None,
    };
    Ok(StreamSessionReport {
        stream_active: result.stream_active,
        recording_active: result.recording_active,
        recording_owned: result.recording_owned,
        detail,
        handoff,
    })
}

// ---------------------------------------------------------------------------
// App entry
// ---------------------------------------------------------------------------

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt::init();

    let desktop = tauri::Builder::default()
        .plugin(setup_wizard::init())
        .plugin(social_manager::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_http::init())
        .invoke_handler(tauri::generate_handler![
            get_config,
            set_config,
            autopilot::autopilot_status,
            autopilot::autopilot_rehearse,
            autopilot_control::autopilot_production_status,
            autopilot_control::autopilot_production_action,
            autopilot_control::autopilot_production_disconnect,
            autopilot_control::autopilot_prepare_game,
            voice_studio_request,
            remote_get_settings,
            remote_save_settings,
            remote_connect,
            remote_disconnect,
            remote_status,
            remote_approve,
            remote_deny,
            remote_request,
            setup_last_readiness,
            setup_refresh_readiness,
            setup_sync_settings,
            setup_save_sync_settings,
            setup_sync_now,
            obs_status,
            obs_connection_diagnostic,
            obs_recording_test,
            obs_scenes,
            obs_switch_scene,
            obs_stream_status,
            obs_toggle_stream,
            obs_start_stream_session,
            obs_stop_stream_session,
        ])
        .setup(|app| {
            let product = app.config().identifier.clone();
            let local_data = app
                .path()
                .local_data_dir()
                .map_err(|_| "Cannot locate local application storage")?;
            app.manage(autopilot::AutopilotBridge::new(
                local_data
                    .join("HybridCreatorPlatform")
                    .join("stream-autopilot"),
                local_data
                    .join("HybridCreatorPlatform")
                    .join("module-setup"),
            ));
            app.manage(voice_studio::VoiceStudio::new(
                local_data
                    .join("HybridCreatorPlatform")
                    .join("voice-studio"),
                local_data
                    .join("HybridCreatorPlatform")
                    .join("module-setup"),
            ));
            let root = app
                .path()
                .local_data_dir()
                .map_err(|_| "Cannot locate local connection settings")?
                .join("HybridCreatorPlatform")
                .join("connections");
            let setup_engine = SetupEngine::new(
                &app.path()
                    .local_data_dir()
                    .map_err(|_| "Cannot locate local readiness storage")?
                    .join("HybridCreatorPlatform"),
                &product,
            )
            .map_err(|error| error.to_string())?;
            let persistence =
                ConnectionPersistence::new(&root, &product).map_err(|error| error.to_string())?;
            let remote_persistence =
                RemotePersistence::new(&root, &product).map_err(|error| error.to_string())?;
            let mut config = persistence.load_public().unwrap_or_else(|error| {
                tracing::warn!("Could not load public connection settings: {error}");
                AppConfig::default()
            });
            match persistence.load_password() {
                Ok(password) => config.obs_password = password,
                Err(error) => tracing::warn!("Could not load OBS credential: {error}"),
            }
            let app_config = Arc::new(Mutex::new(config));
            let obs_cache = Arc::new(obs::ObsClientCache::new());
            let recording_library = RecordingLibrary::new(
                app.path()
                    .local_data_dir()
                    .map_err(|_| "Cannot locate recording library storage")?
                    .join("HybridCreatorPlatform")
                    .join("recording-library"),
            )?;
            let remote_settings = remote_persistence.load().unwrap_or_else(|error| {
                tracing::warn!("Could not load remote settings: {error}");
                RemoteSettings {
                    public: Default::default(),
                    hosted_token: None,
                    self_hosted_token: None,
                }
            });
            let remote_control = Arc::new(relay::StreamRemoteControl::new(
                app_config.clone(),
                obs_cache.clone(),
            ));
            let auto_settings = remote_settings.clone();
            let auto_control = remote_control.clone();
            app.manage(autopilot_control::ProductionBridge::new(
                local_data
                    .join("HybridCreatorPlatform")
                    .join("stream-autopilot-production"),
                local_data
                    .join("HybridCreatorPlatform")
                    .join("module-setup"),
                app_config.clone(),
            ));
            app.manage(app_config);
            app.manage(obs_cache);
            app.manage(obs::ObsSessionState::new());
            app.manage(recording_library);
            app.manage(persistence);
            app.manage(Arc::new(Mutex::new(remote_settings)));
            app.manage(remote_persistence);
            app.manage(remote_control);
            app.manage(setup_engine);
            tracing::info!("Stream Extend starting up");

            // Load saved config from Tauri store
            tauri::async_runtime::spawn(async move {
                if auto_settings.public.enabled {
                    if let Err(error) = auto_control.connect(&auto_settings).await {
                        tracing::warn!("Remote auto-connect failed: {error}");
                    }
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Stream Extend");
    static QUITTING: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
    desktop.run(|handle, event| {
        if let tauri::RunEvent::ExitRequested { api, .. } = event {
            if !QUITTING.swap(true, std::sync::atomic::Ordering::SeqCst) {
                api.prevent_exit();
                let handle = handle.clone();
                tauri::async_runtime::spawn(async move {
                    let result = handle
                        .state::<autopilot_control::ProductionBridge>()
                        .shutdown()
                        .await;
                    match result {
                        Ok(()) => handle.exit(0),
                        Err(message) => {
                            QUITTING.store(false, std::sync::atomic::Ordering::SeqCst);
                            let _ = handle.emit("autopilot-shutdown-error", message);
                        }
                    }
                });
            }
        }
    });
}
