//! Shared Tauri bridge for the local-only Social Management service.

use fs2::FileExt;
use local_settings::LocalSettings;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    fs::OpenOptions,
    path::{Path, PathBuf},
    process::Stdio,
    sync::Arc,
};
use tauri::{Manager, Runtime};
use tokio::{
    net::TcpStream,
    process::{Child, Command},
    sync::Mutex,
    time::{sleep, Duration},
};

include!(concat!(env!("OUT_DIR"), "/assets.rs"));

const HOST: &str = "127.0.0.1";
const PORT: u16 = 8765;

struct SocialManager {
    root: Result<PathBuf, String>,
    child: Arc<Mutex<Option<Child>>>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
struct ActiveSelection {
    kind: String,
    profile_id: String,
    brand_id: String,
    provider_id: String,
    capability: String,
    connection_id: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct SelectionState {
    schema_version: u8,
    #[serde(default)]
    active: BTreeMap<String, String>,
    #[serde(default)]
    preferences: BTreeMap<String, ActiveSelection>,
}

impl Default for SelectionState {
    fn default() -> Self {
        Self {
            schema_version: 1,
            active: BTreeMap::new(),
            preferences: BTreeMap::new(),
        }
    }
}

#[derive(Serialize)]
struct ServiceStatus {
    running: bool,
    url: String,
}

fn service_url() -> String {
    format!("http://{HOST}:{PORT}")
}

fn catalog() -> Result<Value, String> {
    serde_json::from_str(CATALOG_JSON)
        .map_err(|_| "Bundled Social Management catalog is invalid".into())
}

fn validate_kind(kind: &str) -> Result<(), String> {
    if matches!(kind, "stream" | "content") {
        Ok(())
    } else {
        Err("Profile workspace must be stream or content".into())
    }
}

fn selection_key(kind: &str, profile_id: &str) -> String {
    format!("{kind}:{profile_id}")
}

fn default_selection(
    catalog: &Value,
    kind: &str,
    profile_id: Option<&str>,
) -> Result<ActiveSelection, String> {
    validate_kind(kind)?;
    let profiles = catalog["profiles"]
        .as_array()
        .ok_or("Bundled profile catalog is invalid")?;
    let profile = match profile_id {
        Some(id) => profiles.iter().find(|profile| profile["id"] == id),
        None => profiles.iter().find(|profile| profile["kind"] == kind),
    }
    .filter(|profile| profile["kind"] == kind || profile["kind"] == "hybrid")
    .ok_or("Profile does not belong to this workspace")?;
    let destination = profile["destinations"]
        .as_array()
        .and_then(|items| items.first())
        .ok_or("Profile has no destination")?;
    let capability = destination["capabilities"]
        .as_array()
        .and_then(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .find(|value| *value != "account-read")
                .or_else(|| items.first().and_then(Value::as_str))
        })
        .ok_or("Profile destination has no capability")?;
    Ok(ActiveSelection {
        kind: kind.into(),
        profile_id: profile["id"]
            .as_str()
            .ok_or("Profile ID is invalid")?
            .into(),
        brand_id: profile["default_brand_id"]
            .as_str()
            .ok_or("Profile brand is invalid")?
            .into(),
        provider_id: destination["provider_id"]
            .as_str()
            .ok_or("Profile provider is invalid")?
            .into(),
        capability: capability.into(),
        connection_id: None,
    })
}

fn validate_selection(catalog: &Value, selection: &ActiveSelection) -> Result<(), String> {
    validate_kind(&selection.kind)?;
    for value in [
        selection.profile_id.as_str(),
        selection.brand_id.as_str(),
        selection.provider_id.as_str(),
        selection.capability.as_str(),
    ] {
        if !valid_id(value) {
            return Err("Invalid profile workspace selection".into());
        }
    }
    if selection
        .connection_id
        .as_deref()
        .is_some_and(|value| !valid_id(value))
    {
        return Err("Invalid connected account selection".into());
    }
    let profile = catalog["profiles"]
        .as_array()
        .and_then(|items| items.iter().find(|item| item["id"] == selection.profile_id))
        .filter(|item| item["kind"] == selection.kind || item["kind"] == "hybrid")
        .ok_or("Profile does not belong to this workspace")?;
    let brands = profile["brand_ids"]
        .as_array()
        .ok_or("Profile brands are invalid")?;
    if !brands.iter().any(|item| item == &selection.brand_id) {
        return Err("Brand is not available to this profile".into());
    }
    let destination = profile["destinations"]
        .as_array()
        .and_then(|items| {
            items
                .iter()
                .find(|item| item["provider_id"] == selection.provider_id)
        })
        .ok_or("Destination is not available to this profile")?;
    let capabilities = destination["capabilities"]
        .as_array()
        .ok_or("Destination capabilities are invalid")?;
    if !capabilities
        .iter()
        .any(|item| item == &selection.capability)
    {
        return Err("Capability is not available to this profile destination".into());
    }
    Ok(())
}

fn with_selection_state<T>(
    root: &Path,
    operation: impl FnOnce(&LocalSettings, &mut SelectionState) -> Result<T, String>,
) -> Result<T, String> {
    fs::create_dir_all(root).map_err(|_| "Cannot create profile workspace storage")?;
    let lock = OpenOptions::new()
        .create(true)
        .read(true)
        .write(true)
        .open(root.join("profile-selections.lock"))
        .map_err(|_| "Cannot open profile workspace storage")?;
    lock.lock_exclusive()
        .map_err(|_| "Profile workspace storage is busy")?;
    let settings =
        LocalSettings::new(root, "profile-selections").map_err(|error| error.to_string())?;
    let mut state = settings
        .load::<SelectionState>()
        .map_err(|error| error.to_string())?;
    let result = if state.schema_version == 1 {
        operation(&settings, &mut state)
    } else {
        Err("Profile workspace schema is unsupported".into())
    };
    let _ = FileExt::unlock(&lock);
    result
}

fn read_selection(root: &Path, kind: &str) -> Result<ActiveSelection, String> {
    let catalog = catalog()?;
    with_selection_state(root, |settings, state| {
        let active = state.active.get(kind).cloned();
        let mut selection = active
            .as_deref()
            .and_then(|profile| {
                state
                    .preferences
                    .get(&selection_key(kind, profile))
                    .cloned()
            })
            .unwrap_or(default_selection(&catalog, kind, active.as_deref())?);
        if validate_selection(&catalog, &selection).is_err() {
            selection = default_selection(&catalog, kind, None)?;
            state
                .active
                .insert(kind.into(), selection.profile_id.clone());
            state.preferences.insert(
                selection_key(kind, &selection.profile_id),
                selection.clone(),
            );
            settings.save(state).map_err(|error| error.to_string())?;
        }
        Ok(selection)
    })
}

fn write_selection(root: &Path, selection: ActiveSelection) -> Result<ActiveSelection, String> {
    let catalog = catalog()?;
    validate_selection(&catalog, &selection)?;
    with_selection_state(root, |settings, state| {
        state
            .active
            .insert(selection.kind.clone(), selection.profile_id.clone());
        state.preferences.insert(
            selection_key(&selection.kind, &selection.profile_id),
            selection.clone(),
        );
        settings.save(state).map_err(|error| error.to_string())?;
        Ok(selection)
    })
}

fn activate(root: &Path, kind: &str, profile_id: &str) -> Result<ActiveSelection, String> {
    let catalog = catalog()?;
    validate_kind(kind)?;
    if !valid_id(profile_id) {
        return Err("Invalid profile workspace selection".into());
    }
    with_selection_state(root, |settings, state| {
        let key = selection_key(kind, profile_id);
        let selection = state
            .preferences
            .get(&key)
            .cloned()
            .unwrap_or(default_selection(&catalog, kind, Some(profile_id))?);
        validate_selection(&catalog, &selection)?;
        state.active.insert(kind.into(), profile_id.into());
        state.preferences.insert(key, selection.clone());
        settings.save(state).map_err(|error| error.to_string())?;
        Ok(selection)
    })
}

fn unpack(root: &Path) -> Result<PathBuf, String> {
    let runtime = root.join("runtime").join(ASSET_VERSION);
    for (path, contents) in ASSETS {
        let target = runtime.join(path);
        if target.is_file() {
            continue;
        }
        fs::create_dir_all(
            target
                .parent()
                .ok_or("Invalid bundled Social Management path")?,
        )
        .map_err(|_| "Cannot prepare Social Management resources")?;
        fs::write(&target, contents).map_err(|_| "Cannot write Social Management resources")?;
    }
    Ok(runtime)
}

fn module_python(root: &Path) -> Result<PathBuf, String> {
    let setup_root = root
        .parent()
        .ok_or("Cannot locate shared module setup storage")?
        .join("module-setup")
        .join(".venv-modules")
        .join("social-management");
    #[cfg(target_os = "windows")]
    let executable = setup_root.join("Scripts/python.exe");
    #[cfg(not(target_os = "windows"))]
    let executable = setup_root.join("bin/python");
    executable.is_file().then_some(executable).ok_or_else(|| {
        "Install Social Management in Module setup before connecting accounts".into()
    })
}

async fn running() -> bool {
    if TcpStream::connect((HOST, PORT)).await.is_err() {
        return false;
    }
    let Ok(client) = reqwest::Client::builder()
        .timeout(Duration::from_secs(1))
        .build()
    else {
        return false;
    };
    let Ok(response) = client
        .get(format!("{}/api/health", service_url()))
        .send()
        .await
    else {
        return false;
    };
    if !response.status().is_success() {
        return false;
    }
    let Ok(body) = response.json::<Value>().await else {
        return false;
    };
    body["service"] == "hybrid-creator-social" && body["schema_version"] == 1
}

#[tauri::command]
fn snapshot() -> Result<Value, String> {
    let catalog = catalog()?;
    let logos = LOGOS
        .iter()
        .map(|(path, data)| ((*path).to_string(), Value::String((*data).to_string())))
        .collect::<serde_json::Map<_, _>>();
    Ok(json!({"catalog": catalog, "logos": logos}))
}

#[tauri::command]
fn selection(
    state: tauri::State<'_, SocialManager>,
    kind: String,
) -> Result<ActiveSelection, String> {
    let root = state.root.as_ref().map_err(Clone::clone)?;
    read_selection(root, &kind)
}

#[tauri::command]
fn activate_profile(
    state: tauri::State<'_, SocialManager>,
    kind: String,
    profile: String,
) -> Result<ActiveSelection, String> {
    let root = state.root.as_ref().map_err(Clone::clone)?;
    activate(root, &kind, &profile)
}

#[tauri::command]
fn save_selection(
    state: tauri::State<'_, SocialManager>,
    selection: ActiveSelection,
) -> Result<ActiveSelection, String> {
    let root = state.root.as_ref().map_err(Clone::clone)?;
    write_selection(root, selection)
}

#[tauri::command]
async fn status() -> ServiceStatus {
    ServiceStatus {
        running: running().await,
        url: service_url(),
    }
}

#[tauri::command]
async fn start(state: tauri::State<'_, SocialManager>) -> Result<ServiceStatus, String> {
    if running().await {
        return Ok(ServiceStatus {
            running: true,
            url: service_url(),
        });
    }
    let root = state.root.as_ref().map_err(Clone::clone)?;
    let runtime = unpack(root)?;
    let executable = module_python(root)?;
    let module = runtime.join("modules/social-management");
    let log = root.join("social-manager.log");
    fs::create_dir_all(root).map_err(|_| "Cannot create Social Management storage")?;
    let stderr = fs::File::create(log).map_err(|_| "Cannot create Social Management log")?;
    let mut guard = state.child.lock().await;
    if let Some(child) = guard.as_mut() {
        if child
            .try_wait()
            .map_err(|_| "Cannot inspect Social Management service")?
            .is_none()
        {
            drop(guard);
            return Ok(status().await);
        }
    }
    let child = Command::new(executable)
        .args(["-m", "social_management", "serve", "--no-browser", "--port"])
        .arg(PORT.to_string())
        .env("PYTHONPATH", &module)
        .env("PYTHONUTF8", "1")
        .current_dir(module)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(stderr)
        .spawn()
        .map_err(|_| "Could not start the local Social Management service")?;
    *guard = Some(child);
    drop(guard);
    for _ in 0..50 {
        if running().await {
            return Ok(ServiceStatus {
                running: true,
                url: service_url(),
            });
        }
        sleep(Duration::from_millis(100)).await;
    }
    Err("Social Management did not start; inspect the local service log".into())
}

fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || b"_-".contains(&byte))
}

async fn local_json(path: &str, query: &[(&str, &str)]) -> Result<Value, String> {
    local_json_method(reqwest::Method::GET, path, query).await
}

async fn local_json_method(
    method: reqwest::Method,
    path: &str,
    query: &[(&str, &str)],
) -> Result<Value, String> {
    if !running().await {
        return Err("Start Social Management before connecting accounts".into());
    }
    let response = reqwest::Client::new()
        .request(method, format!("{}{path}", service_url()))
        .query(query)
        .send()
        .await
        .map_err(|_| "The local Social Management service did not answer")?;
    let status = response.status();
    let body: Value = response
        .json()
        .await
        .map_err(|_| "The local Social Management service returned invalid data")?;
    if !status.is_success() {
        return Err(body["error"]
            .as_str()
            .unwrap_or("Social Management request failed")
            .to_string());
    }
    Ok(body)
}

#[tauri::command]
async fn authorize(
    profile: String,
    provider: String,
    capability: String,
) -> Result<String, String> {
    if !valid_id(&profile) || !valid_id(&provider) || !valid_id(&capability) {
        return Err("Invalid Social Management selection".into());
    }
    let body = local_json(
        "/api/authorize",
        &[
            ("profile", &profile),
            ("provider", &provider),
            ("capability", &capability),
        ],
    )
    .await?;
    let authorization_url = body["authorization_url"]
        .as_str()
        .filter(|value| value.starts_with("https://"))
        .map(str::to_string)
        .ok_or_else(|| "Provider returned no secure authorization URL".to_string())?;
    let catalog: Value = serde_json::from_str(CATALOG_JSON)
        .map_err(|_| "Bundled Social Management catalog is invalid")?;
    let expected = catalog["providers"]
        .as_array()
        .and_then(|providers| providers.iter().find(|item| item["id"] == provider))
        .and_then(|item| item["oauth"]["authorize_url"].as_str())
        .ok_or_else(|| "Provider has no bundled authorization contract".to_string())?;
    if !authorization_url.starts_with(&format!("{expected}?")) {
        return Err("Local service returned an unexpected provider authorization URL".into());
    }
    Ok(authorization_url)
}

#[tauri::command]
async fn connections() -> Result<Value, String> {
    local_json("/api/connections", &[]).await
}

#[tauri::command]
async fn disconnect(connection: String) -> Result<Value, String> {
    if !valid_id(&connection) {
        return Err("Invalid connected account selection".into());
    }
    local_json_method(
        reqwest::Method::DELETE,
        &format!("/api/connections/{connection}"),
        &[],
    )
    .await
}

pub fn init<R: Runtime>() -> tauri::plugin::TauriPlugin<R> {
    tauri::plugin::Builder::new("social-manager")
        .invoke_handler(tauri::generate_handler![
            snapshot,
            selection,
            activate_profile,
            save_selection,
            start,
            status,
            authorize,
            connections,
            disconnect
        ])
        .setup(|app, _| {
            let root = app
                .path()
                .local_data_dir()
                .map(|path| path.join("HybridCreatorPlatform").join("social-manager"))
                .map_err(|_| "Cannot locate Social Management storage".into());
            app.manage(SocialManager {
                root,
                child: Arc::new(Mutex::new(None)),
            });
            Ok(())
        })
        .build()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bundled_catalog_and_logos_are_complete() {
        let value = snapshot().unwrap();
        assert_eq!(value["catalog"]["schema_version"], 1);
        assert_eq!(value["catalog"]["brands"].as_array().unwrap().len(), 4);
        assert_eq!(value["logos"].as_object().unwrap().len(), 4);
        assert!(value["logos"]["assets/brands/opentechapp.svg"]
            .as_str()
            .unwrap()
            .starts_with("data:image/svg+xml;base64,"));
    }

    #[test]
    fn command_ids_are_strict() {
        assert!(valid_id("opentech-marketing"));
        assert!(valid_id("post-text"));
        assert!(!valid_id("../social"));
        assert!(!valid_id("YouTube"));
    }

    #[test]
    fn active_workspace_remembers_each_profiles_account_route() {
        let root =
            std::env::temp_dir().join(format!("hcp-social-selections-{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        let initial = read_selection(&root, "stream").unwrap();
        assert_eq!(initial.profile_id, "stream-main");
        let mut main = initial.clone();
        main.provider_id = "youtube".into();
        main.capability = "live-stream".into();
        main.connection_id = Some("stream-main-youtube-abc123".into());
        write_selection(&root, main.clone()).unwrap();

        let labs = activate(&root, "stream", "agent-labs").unwrap();
        assert_eq!(labs.profile_id, "agent-labs");
        let restored = activate(&root, "stream", "stream-main").unwrap();
        assert_eq!(restored, main);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn profile_workspace_rejects_cross_kind_and_unavailable_routes() {
        let root =
            std::env::temp_dir().join(format!("hcp-social-validation-{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        assert!(activate(&root, "stream", "content-main").is_err());
        let mut selection = read_selection(&root, "content").unwrap();
        selection.brand_id = "stream-extend".into();
        assert!(write_selection(&root, selection).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
