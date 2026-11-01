//! Creator Extend — Tauri 2 desktop + mobile app.
//!
//! Wraps ComfyUI workflows, Blender integration, Krita AI editing,
//! sports CV replay, and image/video editing into one app.
//! Connects to the relay for remote access + subscriptions.

mod blender;
pub mod blender_jobs;
pub mod comfyui; // pub so tests/comfyui_contract.rs (an external integration test) can call it directly
pub mod connection_settings;
mod krita;
mod posture;
mod relay;
mod tool_runtime;
pub mod workflow_inputs;

use std::sync::{Arc, Mutex};

use command_error::ErrorEnvelope;
use connection_settings::{
    ConnectionPersistence, ConnectionSettingsUpdate, ConnectionSettingsView,
};
use recording_library::{RecordingLibrary, RecordingOrigin, RecordingStatus, RecordingView};
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
use tauri::Manager;

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    /// ComfyUI API URL (default: http://localhost:8188).
    pub comfyui_url: String,
    /// MinIO/S3 endpoint (default: http://localhost:9000).
    pub minio_endpoint: String,
    /// MinIO access key.
    pub minio_access_key: Option<String>,
    /// MinIO secret key.
    pub minio_secret_key: Option<String>,
    /// Blender executable path (auto-detected if on PATH).
    pub blender_path: Option<String>,
    /// Krita executable path (auto-detected if on PATH).
    pub krita_path: Option<String>,
    /// FastAPI backend URL.
    pub api_url: String,
    /// Relay configuration.
    pub relay: RelayConfig,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            comfyui_url: "http://localhost:8188".into(),
            minio_endpoint: "http://localhost:9000".into(),
            minio_access_key: None,
            minio_secret_key: None,
            blender_path: None,
            krita_path: None,
            api_url: "http://localhost:8000".into(),
            relay: RelayConfig {
                mode: RelayMode::Local,
                product: Product::CreatorExtend,
                ..RelayConfig::default()
            },
        }
    }
}

type ConfigState<'r> = tauri::State<'r, Arc<Mutex<AppConfig>>>;
type PersistenceState<'r> = tauri::State<'r, ConnectionPersistence>;
type RemoteSettingsState<'r> = tauri::State<'r, Arc<Mutex<RemoteSettings>>>;
type RemotePersistenceState<'r> = tauri::State<'r, RemotePersistence>;
type RemoteControlState<'r> = tauri::State<'r, Arc<relay::CreatorRemoteControl>>;
type ToolRuntimeState<'r> = tauri::State<'r, tool_runtime::ToolRuntime>;
type SetupEngineState<'r> = tauri::State<'r, SetupEngine>;
type RecordingLibraryState<'r> = tauri::State<'r, RecordingLibrary>;

// ---------------------------------------------------------------------------
// Tauri commands
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_config(state: ConfigState<'_>) -> ConnectionSettingsView {
    ConnectionSettingsView::from(&*state.lock().unwrap())
}

#[tauri::command]
async fn set_config(
    state: ConfigState<'_>,
    persistence: PersistenceState<'_>,
    config: ConnectionSettingsUpdate,
) -> Result<ConnectionSettingsView, String> {
    let current = state.lock().unwrap().clone();
    let store = persistence.inner().clone();
    let next = tauri::async_runtime::spawn_blocking(move || store.save(&current, config))
        .await
        .map_err(|_| "Connection settings could not be saved".to_string())??;
    *state.lock().unwrap() = next.clone();
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
    } = settings.relay_config(Product::CreatorExtend)?.mode
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
    engine: SetupEngineState<'_>,
) -> Result<ReadinessSnapshot, String> {
    let url = config.lock().unwrap().comfyui_url.clone();
    let status = comfyui::get_status(&url)
        .await
        .map_err(|_| "ComfyUI readiness check failed".to_string())?;
    let mut api_evidence = Map::new();
    if let Some(value) = status.gpu_name.clone() {
        api_evidence.insert("gpuBackend".into(), Value::String(value));
    }
    if let Some(value) = status.vram_total_mb {
        api_evidence.insert("vramTotalMb".into(), Value::from(value));
    }
    let api = if status.connected {
        CheckObservation::ready(
            "creator.comfyui.api",
            "ComfyUI answered system and queue requests",
            api_evidence,
        )
    } else {
        CheckObservation::blocked(
            "creator.comfyui.api",
            "Start ComfyUI and verify the saved local endpoint",
        )
    };
    let catalog = match comfyui::list_committed_workflows() {
        Ok(items) if !items.is_empty() => {
            let mut evidence = Map::new();
            evidence.insert("workflowCount".into(), Value::from(items.len() as u64));
            CheckObservation::ready(
                "creator.comfyui.workflows",
                "The app loaded its committed workflow catalog",
                evidence,
            )
        }
        Ok(_) => CheckObservation::blocked(
            "creator.comfyui.workflows",
            "No runnable committed workflows are bundled",
        ),
        Err(_) => CheckObservation::failed(
            "creator.comfyui.workflows",
            "The committed workflow catalog could not be read",
        ),
    };
    let machine_id = engine.settings()?.machine_id;
    let manifest = ReadinessManifest::parse(include_str!(
        "../../../../configs/setup/creator-extend.json"
    ))?;
    engine.save_snapshot(ReadinessSnapshot::from_manifest(
        &machine_id,
        vec![api, catalog],
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
fn recordings_list(library: RecordingLibraryState<'_>) -> Result<Vec<RecordingView>, String> {
    library.list()
}

#[tauri::command]
fn recordings_import(
    library: RecordingLibraryState<'_>,
    path: String,
    content_profile_id: Option<String>,
) -> Result<RecordingView, String> {
    library.register(
        path,
        RecordingOrigin::ManualImport,
        None,
        content_profile_id.as_deref(),
    )
}

#[tauri::command]
fn recordings_update(
    library: RecordingLibraryState<'_>,
    id: String,
    status: RecordingStatus,
    content_profile_id: Option<String>,
) -> Result<RecordingView, String> {
    library.update(&id, status, content_profile_id.as_deref())
}

#[tauri::command]
fn recordings_reveal(library: RecordingLibraryState<'_>, id: String) -> Result<(), String> {
    library.reveal(&id)
}

#[tauri::command]
async fn setup_sync_now(engine: SetupEngineState<'_>) -> Result<SyncReport, String> {
    engine.inner().clone().publish_latest().await
}

#[tauri::command]
fn comfyui_upload_target(state: ConfigState<'_>) -> Result<String, ErrorEnvelope> {
    workflow_inputs::upload_target(&state.lock().unwrap().comfyui_url)
}

/// Expose editable inputs from one approved committed template.
#[tauri::command]
fn comfyui_workflow_inputs(
    workflow_path: String,
) -> Result<Vec<workflow_inputs::InputField>, ErrorEnvelope> {
    workflow_inputs::fields(&comfyui::load_workflow_json(&workflow_path)?)
}

/// Reload the approved template and apply only supported per-run values.
#[tauri::command]
async fn comfyui_queue_configured(
    state: ConfigState<'_>,
    workflow_path: String,
    edits: Vec<workflow_inputs::InputEdit>,
) -> Result<String, ErrorEnvelope> {
    let raw = comfyui::load_workflow_json(&workflow_path)?;
    let prepared = workflow_inputs::prepare(&raw, &edits)?;
    let url = state.lock().unwrap().comfyui_url.clone();
    comfyui::require_compatible_workflow(&url, &prepared).await?;
    comfyui::queue_prompt(&url, &prepared).await
}

#[tauri::command]
async fn comfyui_upload_image(
    state: ConfigState<'_>,
    bytes: Vec<u8>,
) -> Result<String, ErrorEnvelope> {
    let url = state.lock().unwrap().comfyui_url.clone();
    workflow_inputs::upload_image(&url, bytes).await
}

/// Check ComfyUI availability and get system info.
#[tauri::command]
async fn comfyui_status(state: ConfigState<'_>) -> Result<comfyui::ComfyStatus, String> {
    let config = state.lock().unwrap().clone();
    comfyui::get_status(&config.comfyui_url)
        .await
        .map_err(|e| e.to_string())
}

/// Inspect one approved bundled workflow against the live ComfyUI node and
/// model inventory before its input editor can queue it.
#[tauri::command]
async fn comfyui_preflight(
    state: ConfigState<'_>,
    workflow_path: String,
) -> Result<comfyui::WorkflowPreflight, ErrorEnvelope> {
    let workflow = comfyui::load_workflow_json(&workflow_path)?;
    let url = state.lock().unwrap().comfyui_url.clone();
    comfyui::preflight_workflow(&url, &workflow).await
}

/// List this app's committed ComfyUI workflows (not whatever a live
/// ComfyUI's own userdata happens to have saved — see comfyui.rs).
#[tauri::command]
fn comfyui_workflows() -> Result<Vec<comfyui::WorkflowInfo>, ErrorEnvelope> {
    comfyui::list_committed_workflows()
}

/// Load one committed workflow's real JSON by the `path` a caller got from
/// `comfyui_workflows`.
#[tauri::command]
fn comfyui_load_workflow(workflow_path: String) -> Result<String, ErrorEnvelope> {
    comfyui::load_workflow_json(&workflow_path)
}

/// Queue a ComfyUI workflow — `workflow_json` should be the real graph
/// loaded via `comfyui_load_workflow`, not a placeholder.
#[tauri::command]
async fn comfyui_queue(
    state: ConfigState<'_>,
    workflow_json: String,
) -> Result<String, ErrorEnvelope> {
    let config = state.lock().unwrap().clone();
    comfyui::require_compatible_workflow(&config.comfyui_url, &workflow_json).await?;
    comfyui::queue_prompt(&config.comfyui_url, &workflow_json).await
}

/// Poll a queued prompt's terminal state.
#[tauri::command]
async fn comfyui_prompt_status(
    state: ConfigState<'_>,
    prompt_id: String,
) -> Result<comfyui::PromptStatus, ErrorEnvelope> {
    let config = state.lock().unwrap().clone();
    comfyui::get_prompt_status(&config.comfyui_url, &prompt_id).await
}

#[tauri::command]
async fn comfyui_output_preview(
    state: ConfigState<'_>,
    output: comfyui::PromptOutputRef,
) -> Result<comfyui::OutputPreview, ErrorEnvelope> {
    let url = state.lock().unwrap().comfyui_url.clone();
    comfyui::get_output_preview(&url, &output).await
}

/// Launch Blender with a project file.
#[tauri::command]
async fn blender_open(state: ConfigState<'_>, project_path: Option<String>) -> Result<(), String> {
    let config = state.lock().unwrap().clone();
    blender::open(config.blender_path.as_deref(), project_path.as_deref())
        .await
        .map_err(|e| e.to_string())
}

/// Run the packaged Blender batch-render planner against explicit user paths.
#[tauri::command]
async fn blender_batch_render(
    state: ConfigState<'_>,
    runtime: ToolRuntimeState<'_>,
    project_path: String,
    output_path: String,
    dry_run: bool,
) -> Result<String, String> {
    let config = state.lock().unwrap().clone();
    let root = runtime.unpack()?;
    blender::batch_render(
        config.blender_path.as_deref(),
        &root,
        &project_path,
        &output_path,
        dry_run,
    )
    .await
    .map_err(|e| e.to_string())
}

fn blender_executable(state: &ConfigState<'_>) -> Result<String, String> {
    state
        .lock()
        .unwrap()
        .blender_path
        .clone()
        .or_else(blender::detect_blender)
        .ok_or("Install Blender or choose its executable in Settings".into())
}

#[tauri::command]
async fn blender_job_start(
    state: ConfigState<'_>,
    runtime: ToolRuntimeState<'_>,
    jobs: tauri::State<'_, blender_jobs::BlenderJobs>,
    project_path: String,
    output_path: String,
    scenes: Vec<String>,
) -> Result<String, String> {
    let executable = blender_executable(&state)?;
    let script = runtime
        .unpack()?
        .join("modules/content-creation/blender/scripts/batch_render.py");
    jobs.start(
        &executable,
        &script,
        &project_path,
        &output_path,
        scenes,
        None,
    )
    .await
}

#[tauri::command]
async fn blender_job_status(
    jobs: tauri::State<'_, blender_jobs::BlenderJobs>,
    job_id: String,
) -> Result<Value, String> {
    jobs.status(&job_id).await
}

#[tauri::command]
async fn blender_job_list(
    jobs: tauri::State<'_, blender_jobs::BlenderJobs>,
) -> Result<Vec<Value>, String> {
    jobs.list().await
}

#[tauri::command]
async fn blender_job_cancel(
    jobs: tauri::State<'_, blender_jobs::BlenderJobs>,
    job_id: String,
) -> Result<(), String> {
    jobs.cancel(&job_id).await
}

#[tauri::command]
async fn blender_job_retry(
    state: ConfigState<'_>,
    runtime: ToolRuntimeState<'_>,
    jobs: tauri::State<'_, blender_jobs::BlenderJobs>,
    job_id: String,
    interrupted_confirmed: bool,
) -> Result<String, String> {
    let executable = blender_executable(&state)?;
    let script = runtime
        .unpack()?
        .join("modules/content-creation/blender/scripts/batch_render.py");
    jobs.retry(&executable, &script, &job_id, interrupted_confirmed)
        .await
}

/// Open Krita with a file.
#[tauri::command]
async fn krita_open(state: ConfigState<'_>, file_path: Option<String>) -> Result<(), String> {
    let config = state.lock().unwrap().clone();
    krita::open(config.krita_path.as_deref(), file_path.as_deref())
        .await
        .map_err(|e| e.to_string())
}

/// Run a Krita automation script (batch upscale, style transfer, etc.).
#[tauri::command]
async fn krita_run_script(
    runtime: ToolRuntimeState<'_>,
    script_name: String,
    args: Vec<String>,
) -> Result<String, String> {
    let root = runtime.unpack()?;
    let interpreter = runtime
        .interpreter_for("image-editing")
        .ok_or("No Python interpreter found for image-editing actions")?;
    krita::run_script(&root, &script_name, &args, &interpreter)
        .await
        .map_err(|e| e.to_string())
}

/// Check the packaged Creator scripts without modifying user files or
/// contacting ComfyUI/MinIO. A successful check only proves the script can
/// start with its selected Python environment; the real DCC workflow still
/// needs live acceptance.
#[tauri::command]
fn creator_tool_status(
    config: ConfigState<'_>,
    runtime: ToolRuntimeState<'_>,
) -> Result<Vec<tool_runtime::ToolCheck>, String> {
    let mut checks = runtime.check()?;
    if let Some(addon) = checks.iter_mut().find(|check| check.id == "blender-addon") {
        let configured = config.lock().unwrap().blender_path.clone();
        let blender = configured
            .filter(|path| std::path::Path::new(path).is_file())
            .or_else(blender::detect_blender);
        match blender {
            Some(path) => {
                addon.interpreter = Some(path);
                addon.detail =
                    "Addon payload is packaged; Blender was found. Install and enable the addon from Blender."
                        .into();
            }
            None => {
                addon.ready = false;
                addon.detail =
                    "Addon payload is packaged, but Blender was not found. Install Blender or set its path in Connections."
                        .into();
            }
        }
    }
    Ok(checks)
}

/// Prepare the bundled Blender addon as a ZIP for Blender's Add-ons installer.
#[tauri::command]
fn creator_tool_archive_blender_addon(runtime: ToolRuntimeState<'_>) -> Result<String, String> {
    runtime
        .archive_blender_addon()
        .map(|path| path.to_string_lossy().into_owned())
}

/// Analyze an uploaded photo for posture (view: "front" | "side" | "back").
#[tauri::command]
async fn posture_analyze(
    runtime: ToolRuntimeState<'_>,
    image_path: String,
    view: String,
) -> Result<serde_json::Value, String> {
    let root = runtime.unpack()?;
    let interpreter = runtime
        .interpreter_for("sports-analytics")
        .ok_or("No Python interpreter found for sports-analytics")?;
    posture::analyze(&root, &image_path, &view, &interpreter)
        .await
        .map_err(|e| e.to_string())
}

// ---------------------------------------------------------------------------
// App entry
// ---------------------------------------------------------------------------

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tracing_subscriber::fmt::init();

    tauri::Builder::default()
        .plugin(setup_wizard::init())
        .plugin(social_manager::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            get_config,
            set_config,
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
            recordings_list,
            recordings_import,
            recordings_update,
            recordings_reveal,
            comfyui_status,
            comfyui_preflight,
            comfyui_workflows,
            comfyui_load_workflow,
            comfyui_workflow_inputs,
            comfyui_upload_target,
            comfyui_queue_configured,
            comfyui_upload_image,
            comfyui_queue,
            comfyui_prompt_status,
            comfyui_output_preview,
            blender_open,
            blender_batch_render,
            blender_job_start,
            blender_job_status,
            blender_job_list,
            blender_job_cancel,
            blender_job_retry,
            krita_open,
            krita_run_script,
            creator_tool_status,
            creator_tool_archive_blender_addon,
            posture_analyze,
        ])
        .setup(|app| {
            let product = app.config().identifier.clone();
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
            let recording_library = RecordingLibrary::new(
                app.path()
                    .local_data_dir()
                    .map_err(|_| "Cannot locate recording library storage")?
                    .join("HybridCreatorPlatform")
                    .join("recording-library"),
            )?;
            let tool_runtime = tool_runtime::ToolRuntime::new(
                app.path()
                    .local_data_dir()
                    .map_err(|_| "Cannot locate Creator tool storage")?
                    .join("HybridCreatorPlatform")
                    .join("creator-tools"),
            );
            let persistence =
                ConnectionPersistence::new(&root, &product).map_err(|error| error.to_string())?;
            let remote_persistence =
                RemotePersistence::new(&root, &product).map_err(|error| error.to_string())?;
            let mut config = persistence.load_public().unwrap_or_else(|error| {
                tracing::warn!("Could not load public connection settings: {error}");
                AppConfig::default()
            });
            match persistence.load_credentials() {
                Ok((access_key, secret_key)) => {
                    config.minio_access_key = access_key;
                    config.minio_secret_key = secret_key;
                }
                Err(error) => tracing::warn!("Could not load MinIO credentials: {error}"),
            }
            let app_config = Arc::new(Mutex::new(config));
            let remote_settings = remote_persistence.load().unwrap_or_else(|error| {
                tracing::warn!("Could not load remote settings: {error}");
                RemoteSettings {
                    public: Default::default(),
                    hosted_token: None,
                    self_hosted_token: None,
                }
            });
            let remote_control = Arc::new(relay::CreatorRemoteControl::new(app_config.clone()));
            let auto_settings = remote_settings.clone();
            let auto_control = remote_control.clone();
            app.manage(app_config);
            app.manage(persistence);
            app.manage(Arc::new(Mutex::new(remote_settings)));
            app.manage(remote_persistence);
            app.manage(remote_control);
            app.manage(setup_engine);
            app.manage(recording_library);
            app.manage(tool_runtime);
            app.manage(blender_jobs::BlenderJobs::new(
                app.path()
                    .local_data_dir()?
                    .join("HybridCreatorPlatform")
                    .join("blender-jobs"),
            ));
            tracing::info!("Creator Extend starting up");
            tauri::async_runtime::spawn(async move {
                if auto_settings.public.enabled {
                    if let Err(error) = auto_control.connect(&auto_settings).await {
                        tracing::warn!("Remote auto-connect failed: {error}");
                    }
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Creator Extend");
}
