//! Shared, local-only setup UI backend. Dependency installation never certifies a module.
mod audio;
use audio::audio_setup_status;
use fs2::FileExt;
use local_settings::OsCredentials;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, HashSet},
    ffi::{OsStr, OsString},
    fs::{self, OpenOptions},
    io::{Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    process::Stdio,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::{SystemTime, UNIX_EPOCH},
};
use tauri::{Manager, Runtime};
#[cfg(any(target_os = "windows", target_os = "macos"))]
use tokio::io::AsyncWriteExt;
use tokio::{
    net::TcpStream,
    process::Command,
    time::{sleep, timeout, Duration},
};
use uuid::Uuid;
include!(concat!(env!("OUT_DIR"), "/assets.rs"));

fn background_command(program: impl AsRef<OsStr>) -> Command {
    #[cfg(target_os = "windows")]
    {
        let mut command = Command::new(program);
        command.creation_flags(0x08000000); // CREATE_NO_WINDOW
        command
    }
    #[cfg(not(target_os = "windows"))]
    {
        Command::new(program)
    }
}

#[derive(Default, Serialize, Deserialize)]
#[serde(default)]
struct Preferences {
    selected: Vec<String>,
    last_job: Option<String>,
    capture_video_id: Option<String>,
    capture_audio_id: Option<String>,
}
struct Wizard {
    root: Result<PathBuf, String>,
    product: String,
    session: String,
    running: Arc<AtomicBool>,
}
impl Wizard {
    fn root(&self) -> Result<&Path, String> {
        self.root.as_deref().map_err(Clone::clone)
    }
    fn preferences_path(&self) -> Result<PathBuf, String> {
        Ok(self.root()?.join(format!("{}.json", self.product)))
    }
    fn preferences(&self) -> Result<Preferences, String> {
        match fs::read(self.preferences_path()?) {
            Ok(bytes) => serde_json::from_slice(&bytes)
                .map_err(|_| "Saved setup choices could not be read".into()),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Preferences::default()),
            Err(_) => Err("Setup storage is unavailable".into()),
        }
    }
}
fn identifier() -> String {
    format!(
        "{}-{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos(),
        std::process::id()
    )
}
fn catalog() -> Value {
    serde_json::from_str(
        ASSETS
            .iter()
            .find(|(p, _)| *p == "configs/local/module-install-catalog.json")
            .unwrap()
            .1,
    )
    .unwrap()
}
fn write_json(path: &Path, value: &impl Serialize) -> Result<(), String> {
    fs::create_dir_all(path.parent().unwrap()).map_err(|_| "Cannot create setup storage")?;
    let temporary = path.with_extension(format!("{}.tmp", identifier()));
    fs::write(
        &temporary,
        serde_json::to_vec_pretty(value).map_err(|_| "Cannot serialize setup state")?,
    )
    .map_err(|_| "Cannot write setup state")?;
    fs::rename(&temporary, path).map_err(|_| "Cannot save setup state".into())
}

fn acquire_install_lock(root: &Path) -> Result<fs::File, String> {
    fs::create_dir_all(root).map_err(|_| "Cannot create setup storage")?;
    let mut lock = OpenOptions::new()
        .create(true)
        .read(true)
        .write(true)
        .open(root.join(".module-install.lock"))
        .map_err(|_| "Cannot open the shared setup lock")?;
    if lock
        .metadata()
        .map_err(|_| "Cannot inspect the shared setup lock")?
        .len()
        == 0
    {
        lock.write_all(b"0")
            .map_err(|_| "Cannot initialize the shared setup lock")?;
        lock.flush()
            .map_err(|_| "Cannot initialize the shared setup lock")?;
    }
    lock.seek(SeekFrom::Start(0))
        .map_err(|_| "Cannot initialize the shared setup lock")?;
    lock.try_lock_exclusive()
        .map_err(|_| "Another setup installation is already running")?;
    Ok(lock)
}
/// Resolve the exact catalog IDs, in dependency order, with duplicate/cycle protection.
pub fn resolve(data: &Value, requested: &[String]) -> Result<Vec<String>, String> {
    fn visit(
        name: &str,
        data: &Value,
        visiting: &mut HashSet<String>,
        out: &mut Vec<String>,
    ) -> Result<(), String> {
        if !data["modules"].as_object().unwrap().contains_key(name) {
            return Err("Unknown module selection".into());
        }
        if out.iter().any(|x| x == name) {
            return Ok(());
        }
        if !visiting.insert(name.into()) {
            return Err("Module dependency cycle".into());
        }
        for dependency in data["modules"][name]["depends_on"].as_array().unwrap() {
            visit(dependency.as_str().unwrap(), data, visiting, out)?;
        }
        visiting.remove(name);
        out.push(name.into());
        Ok(())
    }
    let module_count = data["modules"]
        .as_object()
        .ok_or_else(|| "Module catalog is invalid".to_string())?
        .len();
    if requested.len() > module_count {
        return Err(format!("Select at most {module_count} modules"));
    }
    let mut result = Vec::new();
    for name in requested {
        visit(name, data, &mut HashSet::new(), &mut result)?;
    }
    Ok(result)
}
fn unpack(root: &Path) -> Result<PathBuf, String> {
    let directory = root.join("runtime").join(ASSET_VERSION);
    for (path, contents) in ASSETS {
        let target = directory.join(path);
        if target.is_file() {
            continue;
        }
        fs::create_dir_all(target.parent().unwrap())
            .map_err(|_| "Cannot prepare installer resources")?;
        let temporary = target.with_extension(format!("{}.tmp", identifier()));
        fs::write(&temporary, contents).map_err(|_| "Cannot write installer resources")?;
        if fs::rename(&temporary, &target).is_err() && !target.is_file() {
            return Err("Cannot prepare installer resources".into());
        }
    }
    fs::create_dir_all(directory.join("modules/broadcast-graphics/nodecg/cfg"))
        .map_err(|_| "Cannot prepare Docker configuration resources")?;
    Ok(directory)
}

async fn python() -> Result<String, String> {
    #[cfg(target_os = "windows")]
    let candidates: Vec<(String, Vec<String>)> = {
        let mut values = vec![
            ("py".into(), vec!["-3.12".into()]),
            ("py".into(), vec!["-3.11".into()]),
            ("python".into(), vec![]),
        ];
        if let Ok(root) = std::env::var("LOCALAPPDATA") {
            values.push((
                Path::new(&root)
                    .join("Programs/Python/Python312/python.exe")
                    .to_string_lossy()
                    .into_owned(),
                vec![],
            ));
        }
        if let Ok(root) = std::env::var("ProgramFiles") {
            values.push((
                Path::new(&root)
                    .join("Python312/python.exe")
                    .to_string_lossy()
                    .into_owned(),
                vec![],
            ));
        }
        values
    };
    #[cfg(not(target_os = "windows"))]
    let candidates: Vec<(String, Vec<String>)> = vec![
        ("python3.12".into(), vec![]),
        ("/opt/homebrew/bin/python3.12".into(), vec![]),
        ("/usr/local/bin/python3.12".into(), vec![]),
        ("python3.11".into(), vec![]),
        ("python3".into(), vec![]),
    ];
    for (executable, args) in candidates {
        let result = timeout(
            Duration::from_secs(3),
            background_command(executable)
                .args(args)
                .args([
                    "-I",
                    "-c",
                    "import sys; assert sys.version_info >= (3,11); print(sys.executable)",
                ])
                .stdin(Stdio::null())
                .kill_on_drop(true)
                .output(),
        )
        .await;
        if let Ok(Ok(output)) = result {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_owned();
                if Path::new(&path).is_file() {
                    return Ok(path);
                }
            }
        }
    }
    Err(
        "Install Python 3.12, then reopen the app and retry. No compatible Python was found."
            .into(),
    )
}

fn python_bootstrap_spec(
    system: &str,
    brew: Option<&Path>,
) -> Result<(String, Vec<String>), String> {
    match system {
        "windows" => Ok((
            "winget".into(),
            [
                "install",
                "--id",
                "Python.Python.3.12",
                "--exact",
                "--source",
                "winget",
                "--scope",
                "user",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
                "--disable-interactivity",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )),
        "macos" => brew
            .filter(|path| path.is_file())
            .map(|path| {
                (
                    path.to_string_lossy().into_owned(),
                    vec!["install".into(), "python@3.12".into()],
                )
            })
            .ok_or_else(|| {
                "Install Homebrew to enable the in-app Python bootstrap on macOS".into()
            }),
        _ => Err(
            "The in-app Python bootstrap currently supports Windows and Homebrew on macOS".into(),
        ),
    }
}

fn ffmpeg_bootstrap_spec(
    system: &str,
    brew: Option<&Path>,
) -> Result<(String, Vec<String>), String> {
    match system {
        "windows" => Ok((
            "winget".into(),
            [
                "install",
                "--id",
                "Gyan.FFmpeg",
                "--exact",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
                "--disable-interactivity",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )),
        "macos" => brew
            .filter(|path| path.is_file())
            .map(|path| {
                (
                    path.to_string_lossy().into_owned(),
                    vec!["install".into(), "ffmpeg".into()],
                )
            })
            .ok_or_else(|| {
                "Install Homebrew to enable the in-app FFmpeg bootstrap on macOS".into()
            }),
        _ => Err(
            "The in-app FFmpeg bootstrap currently supports Windows and Homebrew on macOS".into(),
        ),
    }
}

fn ffmpeg_executable() -> Option<PathBuf> {
    let mut candidates = Vec::new();
    #[cfg(target_os = "windows")]
    {
        for variable in ["LOCALAPPDATA", "ProgramFiles"] {
            if let Ok(root) = std::env::var(variable) {
                candidates.push(Path::new(&root).join("Microsoft/WinGet/Links/ffmpeg.exe"));
                candidates.push(Path::new(&root).join("WinGet/Links/ffmpeg.exe"));
            }
        }
    }
    #[cfg(target_os = "macos")]
    {
        candidates.extend(
            [
                "/opt/homebrew/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                "/usr/bin/ffmpeg",
            ]
            .map(PathBuf::from),
        );
    }
    #[cfg(target_os = "linux")]
    {
        candidates.extend(["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"].map(PathBuf::from));
    }
    let name = if cfg!(target_os = "windows") {
        "ffmpeg.exe"
    } else {
        "ffmpeg"
    };
    if let Some(paths) = std::env::var_os("PATH") {
        candidates.extend(std::env::split_paths(&paths).map(|directory| directory.join(name)));
    }
    candidates.into_iter().find(|path| path.is_file())
}

async fn ffmpeg_status_value() -> Value {
    let executable = ffmpeg_executable();
    let probe = if let Some(path) = executable.as_deref() {
        Some(command_probe(path, &["-version"], Duration::from_secs(3)).await)
    } else {
        None
    };
    let installed = probe.as_ref().is_some_and(|result| result.success);
    let spec = ffmpeg_bootstrap_spec(std::env::consts::OS, homebrew().as_deref());
    let bootstrap_available = if installed {
        false
    } else {
        match spec {
            Ok((executable, _)) => executable_available(&executable).await,
            Err(_) => false,
        }
    };
    let version = probe
        .as_ref()
        .filter(|result| result.success)
        .and_then(|result| result.text.lines().next())
        .map(|line| line.trim().to_string());
    let detail = if installed {
        "FFmpeg is ready for local capture and content helpers."
    } else if executable.is_some() {
        "An FFmpeg executable was found but did not return a usable version. Reinstall or repair it."
    } else if bootstrap_available {
        "FFmpeg can be installed locally from Module setup."
    } else if cfg!(target_os = "windows") {
        "FFmpeg is not installed and Windows Package Manager (winget) is unavailable."
    } else if cfg!(target_os = "macos") {
        "FFmpeg is not installed and Homebrew is unavailable."
    } else {
        "Install FFmpeg using the operating system package manager."
    };
    json!({
        "installed": installed,
        "path": executable,
        "version": version,
        "bootstrap_available": bootstrap_available,
        "detail": detail
    })
}

#[tauri::command]
async fn ffmpeg_status() -> Value {
    ffmpeg_status_value().await
}

fn homebrew() -> Option<PathBuf> {
    ["/opt/homebrew/bin/brew", "/usr/local/bin/brew"]
        .into_iter()
        .map(PathBuf::from)
        .find(|path| path.is_file())
}

fn obs_bootstrap_spec(system: &str, brew: Option<&Path>) -> Result<(String, Vec<String>), String> {
    match system {
        "windows" => Ok((
            "winget".into(),
            [
                "install",
                "--id",
                "OBSProject.OBSStudio",
                "--exact",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
                "--disable-interactivity",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )),
        "macos" => brew
            .filter(|path| path.is_file())
            .map(|path| {
                (
                    path.to_string_lossy().into_owned(),
                    vec!["install".into(), "--cask".into(), "obs".into()],
                )
            })
            .ok_or_else(|| "Install Homebrew to enable the in-app OBS bootstrap on macOS".into()),
        _ => {
            Err("The in-app OBS bootstrap currently supports Windows and Homebrew on macOS".into())
        }
    }
}

fn obs_executable() -> Option<PathBuf> {
    let mut candidates = Vec::new();
    #[cfg(target_os = "windows")]
    {
        for variable in ["ProgramFiles", "LOCALAPPDATA"] {
            if let Ok(root) = std::env::var(variable) {
                candidates.push(Path::new(&root).join("obs-studio/bin/64bit/obs64.exe"));
                candidates.push(Path::new(&root).join("Programs/obs-studio/bin/64bit/obs64.exe"));
            }
        }
    }
    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from("/Applications/OBS.app/Contents/MacOS/OBS"));
        if let Ok(root) = std::env::var("HOME") {
            candidates.push(Path::new(&root).join("Applications/OBS.app/Contents/MacOS/OBS"));
        }
    }
    #[cfg(target_os = "linux")]
    {
        candidates.push(PathBuf::from("/usr/bin/obs"));
        candidates.push(PathBuf::from("/usr/local/bin/obs"));
    }
    candidates.into_iter().find(|path| path.is_file())
}

async fn obs_running() -> bool {
    #[cfg(target_os = "windows")]
    let probe = (
        "tasklist",
        vec!["/FI", "IMAGENAME eq obs64.exe", "/FO", "CSV", "/NH"],
    );
    #[cfg(target_os = "macos")]
    let probe = ("pgrep", vec!["-x", "OBS"]);
    #[cfg(target_os = "linux")]
    let probe = ("pgrep", vec!["-x", "obs"]);
    #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
    return false;

    let result = timeout(
        Duration::from_secs(3),
        background_command(probe.0)
            .args(probe.1)
            .stdin(Stdio::null())
            .kill_on_drop(true)
            .output(),
    )
    .await;
    match result {
        Ok(Ok(output)) if output.status.success() => {
            #[cfg(target_os = "windows")]
            return String::from_utf8_lossy(&output.stdout)
                .to_ascii_lowercase()
                .contains("obs64.exe");
            #[cfg(not(target_os = "windows"))]
            return true;
        }
        _ => false,
    }
}

async fn obs_status_value() -> Value {
    let executable = obs_executable();
    let installed = executable.is_some();
    let running = installed && obs_running().await;
    let default_websocket_reachable = running
        && timeout(
            Duration::from_millis(600),
            TcpStream::connect(("127.0.0.1", 4455)),
        )
        .await
        .is_ok_and(|result| result.is_ok());
    let spec = obs_bootstrap_spec(std::env::consts::OS, homebrew().as_deref());
    let bootstrap_available = if installed {
        false
    } else {
        match spec {
            Ok((executable, _)) => executable_available(&executable).await,
            Err(_) => false,
        }
    };
    let (state, detail) = if !installed {
        (
            "missing",
            if bootstrap_available {
                "OBS Studio can be installed from Module setup."
            } else {
                "OBS Studio is not installed and no supported package manager was found."
            },
        )
    } else if !running {
        ("stopped", "OBS Studio is installed but is not running.")
    } else if !default_websocket_reachable {
        (
            "websocket_unreachable",
            "OBS is running. Enable its WebSocket server or check the configured port.",
        )
    } else {
        (
            "websocket_reachable",
            "OBS is running and a service is listening on the default WebSocket port.",
        )
    };
    json!({
        "state": state,
        "installed": installed,
        "path": executable,
        "running": running,
        "default_websocket_reachable": default_websocket_reachable,
        "bootstrap_available": bootstrap_available,
        "detail": detail
    })
}

#[tauri::command]
async fn obs_status() -> Value {
    obs_status_value().await
}

#[tauri::command]
async fn launch_obs() -> Result<Value, String> {
    let executable = obs_executable().ok_or("Install OBS Studio before opening it")?;
    if !obs_running().await {
        let mut command = Command::new(&executable);
        command
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        if let Some(directory) = executable.parent() {
            command.current_dir(directory);
        }
        command.spawn().map_err(|_| "Could not open OBS Studio")?;
        for _ in 0..20 {
            if obs_running().await {
                break;
            }
            sleep(Duration::from_millis(250)).await;
        }
    }
    Ok(obs_status_value().await)
}

#[tauri::command]
fn obs_scene_plan() -> Result<Value, String> {
    let source = ASSETS
        .iter()
        .find(|(path, _)| *path == "modules/creator-experience/scenes/default.json")
        .map(|(_, value)| *value)
        .ok_or("The OBS scene plan is not bundled")?;
    let plan: Value = serde_json::from_str(source).map_err(|_| "The OBS scene plan is invalid")?;
    let scenes: Vec<_> = plan["scenes"]
        .as_array()
        .ok_or("The OBS scene plan has no scenes")?
        .iter()
        .filter_map(|scene| scene["name"].as_str())
        .map(str::to_string)
        .collect();
    Ok(json!({
        "asset_version": ASSET_VERSION,
        "name": plan["name"],
        "scenes": scenes,
        "apply_available": false,
        "detail": "Preview only: the bundled collection is a source-free skeleton, so the app will not overwrite or import OBS configuration."
    }))
}

const DOCKER_SERVICE_ALLOWLIST: &[&str] = &[
    "postgres",
    "redis",
    "minio",
    "fastapi",
    "prometheus",
    "source-health-exporter",
    "loki",
    "promtail",
    "grafana",
    "nodecg",
    "n8n",
];

#[derive(Debug, Default)]
struct CommandProbe {
    available: bool,
    success: bool,
    text: String,
}

fn decode_command_output(bytes: &[u8]) -> String {
    let has_utf16le_bom = bytes.starts_with(&[0xff, 0xfe]);
    let content = if has_utf16le_bom { &bytes[2..] } else { bytes };
    if content.len() >= 2
        && content.len() % 2 == 0
        && (has_utf16le_bom || content[1..].iter().step_by(2).all(|byte| *byte == 0))
    {
        let words: Vec<u16> = content
            .chunks_exact(2)
            .map(|pair| u16::from_le_bytes([pair[0], pair[1]]))
            .collect();
        String::from_utf16_lossy(&words)
    } else {
        String::from_utf8_lossy(bytes).into_owned()
    }
}

async fn command_probe(executable: &Path, args: &[&str], limit: Duration) -> CommandProbe {
    match timeout(
        limit,
        background_command(executable)
            .args(args)
            .stdin(Stdio::null())
            .kill_on_drop(true)
            .output(),
    )
    .await
    {
        Ok(Ok(output)) => CommandProbe {
            available: true,
            success: output.status.success(),
            text: format!(
                "{}\n{}",
                decode_command_output(&output.stdout),
                decode_command_output(&output.stderr)
            )
            .trim()
            .to_string(),
        },
        Ok(Err(_)) => CommandProbe::default(),
        Err(_) => CommandProbe {
            available: true,
            success: false,
            text: "Command timed out".into(),
        },
    }
}

fn docker_bootstrap_spec(
    system: &str,
    brew: Option<&Path>,
) -> Result<(String, Vec<String>), String> {
    match system {
        "windows" => Ok((
            "winget".into(),
            [
                "install",
                "--id",
                "Docker.DockerDesktop",
                "--exact",
                "--source",
                "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
                "--disable-interactivity",
            ]
            .into_iter()
            .map(str::to_string)
            .collect(),
        )),
        "macos" => brew
            .filter(|path| path.is_file())
            .map(|path| {
                (
                    path.to_string_lossy().into_owned(),
                    vec!["install".into(), "--cask".into(), "docker-desktop".into()],
                )
            })
            .ok_or_else(|| {
                "Install Homebrew to enable the in-app Docker Desktop bootstrap on macOS".into()
            }),
        _ => Err(
            "The in-app Docker Desktop bootstrap currently supports Windows and Homebrew on macOS"
                .into(),
        ),
    }
}

fn docker_desktop_executable() -> Option<PathBuf> {
    let mut candidates: Vec<PathBuf> = Vec::new();
    #[cfg(target_os = "windows")]
    {
        if let Ok(root) = std::env::var("ProgramFiles") {
            candidates.push(Path::new(&root).join("Docker/Docker/Docker Desktop.exe"));
        }
        if let Ok(root) = std::env::var("LOCALAPPDATA") {
            candidates.push(Path::new(&root).join("Docker/Docker Desktop.exe"));
        }
    }
    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/Docker.app/Contents/MacOS/Docker Desktop",
        ));
        if let Ok(root) = std::env::var("HOME") {
            candidates.push(
                Path::new(&root).join("Applications/Docker.app/Contents/MacOS/Docker Desktop"),
            );
        }
    }
    candidates.into_iter().find(|path| path.is_file())
}

async fn docker_executable() -> Option<PathBuf> {
    let mut candidates = Vec::new();
    #[cfg(target_os = "windows")]
    if let Ok(root) = std::env::var("ProgramFiles") {
        candidates.push(Path::new(&root).join("Docker/Docker/resources/bin/docker.exe"));
    }
    #[cfg(target_os = "macos")]
    {
        candidates.push(PathBuf::from(
            "/Applications/Docker.app/Contents/Resources/bin/docker",
        ));
        if let Ok(root) = std::env::var("HOME") {
            candidates.push(
                Path::new(&root).join("Applications/Docker.app/Contents/Resources/bin/docker"),
            );
        }
    }
    #[cfg(target_os = "linux")]
    {
        candidates.push(PathBuf::from("/usr/bin/docker"));
        candidates.push(PathBuf::from("/usr/local/bin/docker"));
    }
    if let Some(path) = candidates.into_iter().find(|path| path.is_file()) {
        return Some(path);
    }
    if executable_available("docker").await {
        Some(PathBuf::from("docker"))
    } else {
        None
    }
}

async fn docker_desktop_running() -> bool {
    #[cfg(target_os = "windows")]
    let probe = command_probe(
        Path::new("tasklist"),
        &[
            "/FI",
            "IMAGENAME eq Docker Desktop.exe",
            "/FO",
            "CSV",
            "/NH",
        ],
        Duration::from_secs(3),
    )
    .await;
    #[cfg(target_os = "macos")]
    let probe = command_probe(
        Path::new("pgrep"),
        &["-f", "Docker.app/Contents/MacOS"],
        Duration::from_secs(3),
    )
    .await;
    #[cfg(target_os = "linux")]
    return false;
    #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
    return false;

    #[cfg(target_os = "windows")]
    return probe.success
        && probe
            .text
            .to_ascii_lowercase()
            .contains("docker desktop.exe");
    #[cfg(target_os = "macos")]
    return probe.success;
}

async fn windows_wsl_state() -> (String, String) {
    #[cfg(not(target_os = "windows"))]
    return (
        "not_applicable".into(),
        "WSL applies only to Windows.".into(),
    );
    #[cfg(target_os = "windows")]
    {
        let probe =
            command_probe(Path::new("wsl.exe"), &["--status"], Duration::from_secs(8)).await;
        if !probe.available {
            return (
                "missing".into(),
                "WSL is unavailable. Docker Desktop may instead use Hyper-V where supported."
                    .into(),
            );
        }
        let lower = probe.text.to_ascii_lowercase();
        if probe.success {
            return (
                "ready".into(),
                "WSL reports an available installation.".into(),
            );
        }
        if lower.contains("update") {
            return (
                "update_required".into(),
                "WSL reports that an update is required.".into(),
            );
        }
        if lower.contains("restart") || lower.contains("reboot") {
            return (
                "reboot_required".into(),
                "WSL reports that Windows must restart before setup can continue.".into(),
            );
        }
        if lower.contains("virtual") || lower.contains("hyper-v") {
            return (
                "virtualization_unavailable".into(),
                "WSL reports that virtualization or Virtual Machine Platform is unavailable."
                    .into(),
            );
        }
        (
            "unavailable".into(),
            "WSL status could not be confirmed. Docker Desktop may still use Hyper-V.".into(),
        )
    }
}

fn docker_services(data: &Value, requested: &[String]) -> Result<Vec<String>, String> {
    let modules = resolve(data, requested)?;
    let mut services = Vec::new();
    for module in modules {
        let values = data["modules"][&module]["compose_services"]
            .as_array()
            .ok_or("Module catalog has an invalid Compose service list")?;
        for value in values {
            let service = value
                .as_str()
                .ok_or("Module catalog has an invalid Compose service")?;
            if !DOCKER_SERVICE_ALLOWLIST.contains(&service) {
                return Err("Module catalog requested an unsupported Compose service".into());
            }
            if !services.iter().any(|item| item == service) {
                services.push(service.to_string());
            }
        }
    }
    Ok(services)
}

fn classify_docker_state(
    installed: bool,
    desktop_installed: bool,
    desktop_running: bool,
    daemon_ready: bool,
    compose_ready: bool,
    diagnostic: &str,
    wsl_state: &str,
) -> (&'static str, &'static str) {
    if !installed {
        return (
            "missing",
            "Docker Desktop is not installed. Container-backed setup remains optional.",
        );
    }
    if daemon_ready && !compose_ready {
        return (
            "compose_unavailable",
            "The Docker daemon answered, but Docker Compose is unavailable.",
        );
    }
    if daemon_ready {
        return (
            "ready",
            "Docker Engine and Compose are ready for selected local services.",
        );
    }
    let lower = diagnostic.to_ascii_lowercase();
    if lower.contains("restart") || lower.contains("reboot") || wsl_state == "reboot_required" {
        return (
            "reboot_required",
            "Windows reports that a restart is required before Docker can start.",
        );
    }
    if lower.contains("virtual")
        || lower.contains("hyper-v")
        || wsl_state == "virtualization_unavailable"
    {
        return (
            "virtualization_unavailable",
            "Virtualization or Virtual Machine Platform is unavailable for Docker Desktop.",
        );
    }
    if lower.contains("wsl") && (lower.contains("update") || wsl_state == "update_required") {
        return (
            "wsl_update_required",
            "Docker reports that WSL must be updated before its Linux engine can start.",
        );
    }
    if lower.contains("wsl") && wsl_state == "missing" {
        return (
            "wsl_missing",
            "Docker requested WSL, but WSL is unavailable. Hyper-V may be an alternative on supported Windows editions.",
        );
    }
    if !desktop_running && desktop_installed {
        return (
            "desktop_stopped",
            "Docker Desktop is installed but is not running.",
        );
    }
    (
        "daemon_unreachable",
        "Docker is installed, but its daemon did not answer. Review Docker Desktop for the exact failure.",
    )
}

async fn docker_service_states(executable: &Path) -> BTreeMap<String, String> {
    let probe = command_probe(
        executable,
        &[
            "ps",
            "-a",
            "--filter",
            "label=com.docker.compose.project=hybrid-creator-platform",
            "--format",
            "{{.Label \"com.docker.compose.service\"}}|{{.Status}}",
        ],
        Duration::from_secs(8),
    )
    .await;
    if !probe.success {
        return BTreeMap::new();
    }
    probe
        .text
        .lines()
        .filter_map(|line| line.split_once('|'))
        .map(|(service, status)| (service.trim().to_string(), status.trim().to_string()))
        .filter(|(service, _)| DOCKER_SERVICE_ALLOWLIST.contains(&service.as_str()))
        .collect()
}

fn services_ready(services: &[String], states: &BTreeMap<String, String>) -> bool {
    !services.is_empty()
        && services.iter().all(|service| {
            states.get(service).is_some_and(|status| {
                status.starts_with("Up")
                    && !status.to_ascii_lowercase().contains("unhealthy")
                    && !status.to_ascii_lowercase().contains("health: starting")
            })
        })
}

#[tauri::command]
fn docker_plan(selected: Vec<String>) -> Result<Value, String> {
    let data = catalog();
    let modules = resolve(&data, &selected)?;
    let services = docker_services(&data, &selected)?;
    Ok(json!({
        "asset_version": ASSET_VERSION,
        "modules": modules,
        "services": services,
        "detail": if services.is_empty() {
            "The selected modules do not require local containers."
        } else {
            "The app will start only these allowlisted services from its bundled local Compose project. Images and build dependencies may download on first use."
        }
    }))
}

async fn docker_status_value(selected: &[String]) -> Value {
    let desktop = docker_desktop_executable();
    let docker = docker_executable().await;
    let installed = desktop.is_some() || docker.is_some();
    let desktop_running = docker_desktop_running().await;
    let cli = if let Some(ref executable) = docker {
        command_probe(executable, &["--version"], Duration::from_secs(5)).await
    } else {
        CommandProbe::default()
    };
    let daemon = if let Some(ref executable) = docker {
        command_probe(
            executable,
            &["version", "--format", "{{.Server.Version}}"],
            Duration::from_secs(8),
        )
        .await
    } else {
        CommandProbe::default()
    };
    let compose = if daemon.success {
        command_probe(
            docker.as_ref().unwrap(),
            &["compose", "version", "--short"],
            Duration::from_secs(8),
        )
        .await
    } else {
        CommandProbe::default()
    };
    let (wsl_state, wsl_detail) = windows_wsl_state().await;
    let (state, detail) = classify_docker_state(
        installed,
        desktop.is_some(),
        desktop_running,
        daemon.success,
        compose.success,
        &daemon.text,
        &wsl_state,
    );
    let services = docker_services(&catalog(), selected).unwrap_or_default();
    let service_states = if daemon.success {
        docker_service_states(docker.as_ref().unwrap()).await
    } else {
        BTreeMap::new()
    };
    let bootstrap_available = if desktop.is_none() && !daemon.success {
        match docker_bootstrap_spec(std::env::consts::OS, homebrew().as_deref()) {
            Ok((executable, _)) => executable_available(&executable).await,
            Err(_) => false,
        }
    } else {
        false
    };
    json!({
        "state": state,
        "installed": installed,
        "desktop_installed": desktop.is_some(),
        "desktop_running": desktop_running,
        "desktop_path": desktop,
        "cli_available": cli.available && cli.success,
        "daemon_ready": daemon.success,
        "compose_ready": compose.success,
        "docker_version": cli.text.lines().next(),
        "engine_version": if daemon.success { daemon.text.lines().next() } else { None },
        "compose_version": if compose.success { compose.text.lines().next() } else { None },
        "wsl_state": wsl_state,
        "wsl_detail": wsl_detail,
        "bootstrap_available": bootstrap_available,
        "start_available": daemon.success && compose.success && !services.is_empty(),
        "services_ready": services_ready(&services, &service_states),
        "service_states": service_states,
        "detail": detail
    })
}

#[tauri::command]
async fn docker_status(selected: Vec<String>) -> Value {
    docker_status_value(&selected).await
}

#[tauri::command]
async fn launch_docker_desktop(selected: Vec<String>) -> Result<Value, String> {
    let executable =
        docker_desktop_executable().ok_or("Install Docker Desktop before opening it")?;
    if !docker_desktop_running().await {
        Command::new(&executable)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| "Could not open Docker Desktop")?;
        for _ in 0..40 {
            if let Some(docker) = docker_executable().await {
                if command_probe(
                    &docker,
                    &["version", "--format", "{{.Server.Version}}"],
                    Duration::from_secs(3),
                )
                .await
                .success
                {
                    break;
                }
            }
            sleep(Duration::from_millis(500)).await;
        }
    }
    Ok(docker_status_value(&selected).await)
}

fn local_docker_env_path(root: &Path) -> PathBuf {
    root.join("docker").join("local.env")
}

fn local_secret() -> String {
    format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple())
}

fn ensure_local_docker_env(root: &Path) -> Result<PathBuf, String> {
    let path = local_docker_env_path(root);
    if path.is_file() {
        return Ok(path);
    }
    fs::create_dir_all(path.parent().unwrap())
        .map_err(|_| "Cannot create local Docker configuration storage")?;
    let contents = format!(
        "LOG_LEVEL=INFO\nHCP_API_KEY={}\nPOSTGRES_DB=hcp\nPOSTGRES_USER=hcp\nPOSTGRES_PASSWORD={}\nMINIO_ROOT_USER=hcpadmin\nMINIO_ROOT_PASSWORD={}\nGRAFANA_ADMIN_PASSWORD={}\nN8N_USER=admin\nN8N_PASSWORD={}\nOBS_WEBSOCKET_PASSWORD=\n",
        local_secret(),
        local_secret(),
        local_secret(),
        local_secret(),
        local_secret()
    );
    let temporary = path.with_extension(format!("{}.tmp", identifier()));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)
        .map_err(|_| "Cannot create the private local Docker environment")?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&temporary, fs::Permissions::from_mode(0o600))
            .map_err(|_| "Cannot protect the private local Docker environment")?;
    }
    if file.write_all(contents.as_bytes()).is_err() || file.sync_all().is_err() {
        let _ = fs::remove_file(&temporary);
        return Err("Cannot write the private local Docker environment".into());
    }
    fs::rename(&temporary, &path).map_err(|_| {
        let _ = fs::remove_file(&temporary);
        "Cannot save the private local Docker environment".to_string()
    })?;
    Ok(path)
}

fn docker_environment(path: &Path) -> Result<BTreeMap<String, String>, String> {
    let contents = fs::read_to_string(path)
        .map_err(|_| "The private local Docker environment is unavailable")?;
    let mut values = BTreeMap::new();
    for line in contents.lines() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (name, value) = line
            .split_once('=')
            .ok_or("The private local Docker environment is invalid")?;
        if name.is_empty()
            || !name
                .bytes()
                .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
        {
            return Err("The private local Docker environment is invalid".into());
        }
        values.insert(name.to_string(), value.to_string());
    }
    Ok(values)
}

fn save_local_service_credentials(environment: &Path) -> bool {
    let Ok(values) = docker_environment(environment) else {
        return false;
    };
    let required = [
        ("minio-access-key", "MINIO_ROOT_USER"),
        ("minio-secret-key", "MINIO_ROOT_PASSWORD"),
        ("n8n-user", "N8N_USER"),
        ("n8n-password", "N8N_PASSWORD"),
        ("grafana-password", "GRAFANA_ADMIN_PASSWORD"),
        ("hcp-api-key", "HCP_API_KEY"),
    ];
    let Ok(shared) = OsCredentials::new("HybridCreatorPlatform", "local-services") else {
        return false;
    };
    if required.iter().any(|(name, key)| {
        values
            .get(*key)
            .is_none_or(|value| shared.set(name, value).is_err())
    }) {
        return false;
    }
    let Ok(creator) = OsCredentials::new("HybridCreatorPlatform", "com.creatorextend.app") else {
        return false;
    };
    creator
        .set("minio-access-key", &values["MINIO_ROOT_USER"])
        .and_then(|_| creator.set("minio-secret-key", &values["MINIO_ROOT_PASSWORD"]))
        .is_ok()
}

fn local_credential_key(kind: &str) -> Option<(&'static str, &'static str)> {
    match kind {
        "minio_access_key" => Some(("MINIO_ROOT_USER", "MinIO access key")),
        "minio_secret_key" => Some(("MINIO_ROOT_PASSWORD", "MinIO secret key")),
        "n8n_user" => Some(("N8N_USER", "n8n user")),
        "n8n_password" => Some(("N8N_PASSWORD", "n8n password")),
        "grafana_password" => Some(("GRAFANA_ADMIN_PASSWORD", "Grafana password")),
        "hcp_api_key" => Some(("HCP_API_KEY", "local API key")),
        _ => None,
    }
}

#[tauri::command]
async fn copy_local_credential(
    state: tauri::State<'_, Wizard>,
    kind: String,
) -> Result<Value, String> {
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        let _ = (state, kind);
        Err("Credential copy is supported by the Windows and macOS installers".into())
    }

    #[cfg(any(target_os = "windows", target_os = "macos"))]
    {
        let (key, label) = local_credential_key(&kind).ok_or("Unknown local credential")?;
        let values = docker_environment(&local_docker_env_path(state.root()?))?;
        let secret = values
            .get(key)
            .ok_or("The local credential is unavailable")?;
        #[cfg(target_os = "windows")]
        let executable = "clip.exe";
        #[cfg(target_os = "macos")]
        let executable = "pbcopy";
        let mut child = background_command(executable)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .map_err(|_| "Could not open the system clipboard")?;
        child
            .stdin
            .take()
            .ok_or("Could not open the system clipboard")?
            .write_all(secret.as_bytes())
            .await
            .map_err(|_| "Could not copy the local credential")?;
        let status = timeout(Duration::from_secs(3), child.wait())
            .await
            .map_err(|_| "Copying the local credential timed out")?
            .map_err(|_| "Could not copy the local credential")?;
        if !status.success() {
            return Err("Could not copy the local credential".into());
        }
        Ok(json!({ "copied": true, "label": label }))
    }
}

async fn existing_hcp_project(executable: &Path) -> bool {
    let containers = command_probe(
        executable,
        &[
            "ps",
            "-a",
            "--filter",
            "label=com.docker.compose.project=hybrid-creator-platform",
            "--format",
            "{{.ID}}",
        ],
        Duration::from_secs(8),
    )
    .await;
    if containers.success && !containers.text.trim().is_empty() {
        return true;
    }
    let volumes = command_probe(
        executable,
        &[
            "volume",
            "ls",
            "--filter",
            "label=com.docker.compose.project=hybrid-creator-platform",
            "--quiet",
        ],
        Duration::from_secs(8),
    )
    .await;
    volumes.success && !volumes.text.trim().is_empty()
}

async fn executable_available(executable: &str) -> bool {
    timeout(
        Duration::from_secs(3),
        background_command(executable)
            .arg("--version")
            .stdin(Stdio::null())
            .kill_on_drop(true)
            .output(),
    )
    .await
    .is_ok_and(|result| result.is_ok_and(|output| output.status.success()))
}

#[tauri::command]
async fn python_status() -> Value {
    match python().await {
        Ok(path) => json!({
            "installed": true,
            "path": path,
            "bootstrap_available": true,
            "detail": "Compatible Python is ready for module setup."
        }),
        Err(_) => {
            let spec = python_bootstrap_spec(std::env::consts::OS, homebrew().as_deref());
            let available = match &spec {
                Ok((executable, _)) => executable_available(executable).await,
                Err(_) => false,
            };
            json!({
                "installed": false,
                "path": null,
                "bootstrap_available": available,
                "detail": if available {
                    "Python 3.12 can be installed locally from Module setup."
                } else if cfg!(target_os = "windows") {
                    "Windows Package Manager (winget) is required for the in-app Python bootstrap."
                } else if cfg!(target_os = "macos") {
                    "Homebrew is required for the in-app Python bootstrap."
                } else {
                    "Install Python 3.12 using the operating system package manager."
                }
            })
        }
    }
}
fn process(
    executable: &str,
    runtime: &Path,
    root: &Path,
    action: &str,
    selected: &[String],
) -> Command {
    let mut command = background_command(executable);
    command
        .arg(runtime.join("scripts/setup/modules.py"))
        .arg(action)
        .arg("--modules")
        .args(selected)
        .env("HCP_MODULE_DATA_ROOT", root)
        .env("PYTHONUTF8", "1")
        .current_dir(runtime)
        .stdin(Stdio::null());
    command
}

#[tauri::command]
fn snapshot(state: tauri::State<'_, Wizard>) -> Result<Value, String> {
    let preferences = state.preferences()?;
    let data = catalog();
    let selected: Vec<_> = preferences
        .selected
        .into_iter()
        .filter(|name| data["modules"].get(name).is_some())
        .collect();
    let capture_report = fs::read(
        state
            .root()?
            .join(format!("{}-capture.json", state.product)),
    )
    .ok()
    .and_then(|bytes| serde_json::from_slice::<Value>(&bytes).ok());
    Ok(json!({
        "catalog": data,
        "selected": selected,
        "last_job": preferences.last_job,
        "platform": std::env::consts::OS,
        "capture_video_id": preferences.capture_video_id,
        "capture_audio_id": preferences.capture_audio_id,
        "capture_report": capture_report,
        "capture_test_report": fs::read(
            state
                .root()?
                .join(format!("{}-capture-test.json", state.product)),
        )
        .ok()
        .and_then(|bytes| serde_json::from_slice::<Value>(&bytes).ok())
    }))
}
#[tauri::command]
fn save_selection(
    state: tauri::State<'_, Wizard>,
    selected: Vec<String>,
) -> Result<Vec<String>, String> {
    let resolved = resolve(&catalog(), &selected)?;
    let mut preferences = state.preferences()?;
    preferences.selected = selected;
    write_json(&state.preferences_path()?, &preferences)?;
    Ok(resolved)
}
#[tauri::command]
fn manual(module: String) -> Result<String, String> {
    let data = catalog();
    let path = data["modules"][&module]["manual"]
        .as_str()
        .ok_or("Unknown module")?;
    ASSETS
        .iter()
        .find(|(key, _)| *key == path)
        .map(|(_, text)| (*text).into())
        .ok_or("Setup guide not bundled".into())
}
#[tauri::command]
async fn check(state: tauri::State<'_, Wizard>, selected: Vec<String>) -> Result<Value, String> {
    let selected = resolve(&catalog(), &selected)?;
    if selected.is_empty() {
        return Err("Choose a module first".into());
    }
    let root = state.root()?.to_path_buf();
    let runtime = unpack(&root)?;
    let executable = python().await?;
    let output = timeout(
        Duration::from_secs(180),
        process(&executable, &runtime, &root, "doctor", &selected)
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Dependency checks timed out; retry fewer modules")?
    .map_err(|_| "Could not run dependency checks")?;
    if !output.status.success() {
        return Err("Dependency checks failed; verify Python and retry".into());
    }
    let result: Value =
        serde_json::from_slice(&output.stdout).map_err(|_| "Invalid readiness report")?;
    write_json(
        &root.join(format!("{}-checks.json", state.product)),
        &result,
    )?;
    Ok(result)
}

#[tauri::command]
async fn capture_scan(state: tauri::State<'_, Wizard>) -> Result<Value, String> {
    let root = state.root()?.to_path_buf();
    let runtime = unpack(&root)?;
    let executable = python().await?;
    let output = timeout(
        Duration::from_secs(30),
        background_command(executable)
            .arg(runtime.join("scripts/setup/capture_devices.py"))
            .arg("--json")
            .env("HCP_MODULE_DATA_ROOT", &root)
            .env("PYTHONUTF8", "1")
            .current_dir(runtime)
            .stdin(Stdio::null())
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Capture-device scan timed out")?
    .map_err(|_| "Could not start the capture-device scan")?;
    if !output.status.success() {
        return Err("Capture-device scan failed; verify Python and retry".into());
    }
    let result: Value =
        serde_json::from_slice(&output.stdout).map_err(|_| "Invalid capture-device report")?;
    write_json(
        &root.join(format!("{}-capture.json", state.product)),
        &result,
    )?;
    // A fresh enumeration invalidates any prior signal/recording evidence.
    let _ = fs::remove_file(root.join(format!("{}-capture-test.json", state.product)));
    Ok(result)
}

#[tauri::command]
async fn capture_test(
    state: tauri::State<'_, Wizard>,
    video_id: String,
    audio_id: Option<String>,
) -> Result<Value, String> {
    let root = state.root()?.to_path_buf();
    let report: Value = serde_json::from_slice(
        &fs::read(root.join(format!("{}-capture.json", state.product)))
            .map_err(|_| "Scan capture hardware before testing a device")?,
    )
    .map_err(|_| "Saved capture-device scan is invalid")?;
    if !valid_capture_id(&report, &video_id, "video") {
        return Err("Choose a video device from the latest local scan".into());
    }
    if audio_id
        .as_deref()
        .is_some_and(|id| !valid_capture_id(&report, id, "audio"))
    {
        return Err("Choose an audio device from the latest local scan".into());
    }
    let runtime = unpack(&root)?;
    let executable = python().await?;
    let mut command = background_command(executable);
    command
        .arg(runtime.join("scripts/setup/capture_test.py"))
        .arg("--video-id")
        .arg(&video_id);
    if let Some(id) = audio_id.as_deref() {
        command.arg("--audio-id").arg(id);
    }
    let output = timeout(
        Duration::from_secs(30),
        command
            .arg("--json")
            .env("HCP_MODULE_DATA_ROOT", &root)
            .env("PYTHONUTF8", "1")
            .current_dir(runtime)
            .stdin(Stdio::null())
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Capture test timed out")?
    .map_err(|_| "Could not start the capture test")?;
    if !output.status.success() {
        return Err("Capture test failed to start; verify Python and retry".into());
    }
    let result: Value =
        serde_json::from_slice(&output.stdout).map_err(|_| "Invalid capture-test report")?;
    write_json(
        &root.join(format!("{}-capture-test.json", state.product)),
        &result,
    )?;
    Ok(result)
}

fn valid_capture_id(report: &Value, id: &str, kind: &str) -> bool {
    id.len() <= 512
        && !id.chars().any(char::is_control)
        && report["devices"].as_array().is_some_and(|devices| {
            devices
                .iter()
                .any(|item| item["id"] == id && item["kind"] == kind)
        })
}

#[tauri::command]
fn save_capture_selection(
    state: tauri::State<'_, Wizard>,
    video_id: Option<String>,
    audio_id: Option<String>,
) -> Result<Value, String> {
    let report: Value = serde_json::from_slice(
        &fs::read(
            state
                .root()?
                .join(format!("{}-capture.json", state.product)),
        )
        .map_err(|_| "Scan capture hardware before saving a device")?,
    )
    .map_err(|_| "Saved capture-device scan is invalid")?;
    if video_id
        .as_deref()
        .is_some_and(|id| !valid_capture_id(&report, id, "video"))
        || audio_id
            .as_deref()
            .is_some_and(|id| !valid_capture_id(&report, id, "audio"))
    {
        return Err("Choose devices from the latest local scan".into());
    }
    let mut preferences = state.preferences()?;
    preferences.capture_video_id = video_id;
    preferences.capture_audio_id = audio_id;
    write_json(&state.preferences_path()?, &preferences)?;
    Ok(json!({
        "capture_video_id": preferences.capture_video_id,
        "capture_audio_id": preferences.capture_audio_id
    }))
}

#[tauri::command]
async fn start_python_bootstrap(state: tauri::State<'_, Wizard>) -> Result<String, String> {
    if python().await.is_ok() {
        return Err("A compatible Python installation is already available".into());
    }
    let (executable, args) = python_bootstrap_spec(std::env::consts::OS, homebrew().as_deref())?;
    if !executable_available(&executable).await {
        return Err(if cfg!(target_os = "windows") {
            "Windows Package Manager (winget) is unavailable; install Python 3.12 manually"
        } else {
            "Homebrew is unavailable; install Python 3.12 manually"
        }
        .into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result =
        begin_package_bootstrap(&state, executable, args, lock, BootstrapTarget::Python).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

#[tauri::command]
async fn start_obs_bootstrap(state: tauri::State<'_, Wizard>) -> Result<String, String> {
    if obs_executable().is_some() {
        return Err("OBS Studio is already installed".into());
    }
    let (executable, args) = obs_bootstrap_spec(std::env::consts::OS, homebrew().as_deref())?;
    if !executable_available(&executable).await {
        return Err(if cfg!(target_os = "windows") {
            "Windows Package Manager (winget) is unavailable; install OBS Studio manually"
        } else {
            "Homebrew is unavailable; install OBS Studio manually"
        }
        .into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result =
        begin_package_bootstrap(&state, executable, args, lock, BootstrapTarget::Obs).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

#[tauri::command]
async fn start_ffmpeg_bootstrap(state: tauri::State<'_, Wizard>) -> Result<String, String> {
    if ffmpeg_status_value().await["installed"] == true {
        return Err("A working FFmpeg installation is already available".into());
    }
    let (executable, args) = ffmpeg_bootstrap_spec(std::env::consts::OS, homebrew().as_deref())?;
    if !executable_available(&executable).await {
        return Err(if cfg!(target_os = "windows") {
            "Windows Package Manager (winget) is unavailable; install FFmpeg manually"
        } else {
            "Homebrew is unavailable; install FFmpeg manually"
        }
        .into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result =
        begin_package_bootstrap(&state, executable, args, lock, BootstrapTarget::Ffmpeg).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

#[tauri::command]
async fn start_docker_bootstrap(state: tauri::State<'_, Wizard>) -> Result<String, String> {
    if docker_desktop_executable().is_some() {
        return Err("Docker Desktop is already installed".into());
    }
    let (executable, args) = docker_bootstrap_spec(std::env::consts::OS, homebrew().as_deref())?;
    if !executable_available(&executable).await {
        return Err(if cfg!(target_os = "windows") {
            "Windows Package Manager (winget) is unavailable; install Docker Desktop manually"
        } else {
            "Homebrew is unavailable; install Docker Desktop manually"
        }
        .into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result =
        begin_package_bootstrap(&state, executable, args, lock, BootstrapTarget::Docker).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

#[derive(Clone, Copy)]
enum BootstrapTarget {
    Python,
    Obs,
    Ffmpeg,
    Docker,
}

impl BootstrapTarget {
    fn kind(self) -> &'static str {
        match self {
            Self::Python => "python_bootstrap",
            Self::Obs => "obs_bootstrap",
            Self::Ffmpeg => "ffmpeg_bootstrap",
            Self::Docker => "docker_bootstrap",
        }
    }

    fn package(self) -> &'static str {
        match self {
            Self::Python => "Python 3.12",
            Self::Obs => "OBS Studio",
            Self::Ffmpeg => "FFmpeg",
            Self::Docker => "Docker Desktop",
        }
    }

    async fn verified(self) -> bool {
        match self {
            Self::Python => python().await.is_ok(),
            Self::Obs => obs_executable().is_some(),
            Self::Ffmpeg => ffmpeg_status_value().await["installed"] == true,
            Self::Docker => {
                docker_desktop_executable().is_some() || docker_executable().await.is_some()
            }
        }
    }
}

async fn begin_package_bootstrap(
    state: &Wizard,
    executable: String,
    args: Vec<String>,
    install_lock: fs::File,
    target: BootstrapTarget,
) -> Result<String, String> {
    let root = state.root()?.to_path_buf();
    let id = identifier();
    let jobs = root.join("jobs");
    fs::create_dir_all(&jobs).map_err(|_| "Cannot create setup job")?;
    let log = fs::File::create(jobs.join(format!("{}.log", id)))
        .map_err(|_| "Cannot create package-manager log")?;
    let metadata_path = jobs.join(format!("{}.json", id));
    let mut metadata = json!({
        "id": id,
        "kind": target.kind(),
        "status": "starting",
        "owner_session": state.session,
        "package": target.package()
    });
    write_json(&metadata_path, &metadata)?;
    let mut preferences = state.preferences()?;
    preferences.last_job = Some(id.clone());
    write_json(&state.preferences_path()?, &preferences)?;
    let mut command = background_command(executable);
    command
        .args(args)
        .stdin(Stdio::null())
        .stdout(
            log.try_clone()
                .map_err(|_| "Cannot open package-manager log")?,
        )
        .stderr(log);
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(_) => {
            metadata["status"] = json!("failed");
            let _ = write_json(&metadata_path, &metadata);
            return Err("Could not start the package manager".into());
        }
    };
    metadata["status"] = json!("running");
    let _ = write_json(&metadata_path, &metadata);
    let running = state.running.clone();
    tauri::async_runtime::spawn(async move {
        let _install_lock = install_lock;
        let outcome = child.wait().await;
        let ready = outcome.is_ok_and(|status| status.success()) && target.verified().await;
        metadata["status"] = json!(if ready { "finished" } else { "failed" });
        metadata["verified"] = json!(ready);
        let _ = write_json(&metadata_path, &metadata);
        running.store(false, Ordering::SeqCst);
    });
    Ok(id)
}

#[tauri::command]
async fn start_docker_services(
    state: tauri::State<'_, Wizard>,
    selected: Vec<String>,
) -> Result<String, String> {
    let services = docker_services(&catalog(), &selected)?;
    if services.is_empty() {
        return Err("The selected modules do not require local Docker services".into());
    }
    let executable = docker_executable()
        .await
        .ok_or("Docker CLI is unavailable; install and open Docker Desktop first")?;
    if !command_probe(
        &executable,
        &["version", "--format", "{{.Server.Version}}"],
        Duration::from_secs(8),
    )
    .await
    .success
    {
        return Err(
            "Docker daemon is unavailable; open Docker Desktop and resolve its status first".into(),
        );
    }
    if !command_probe(
        &executable,
        &["compose", "version", "--short"],
        Duration::from_secs(8),
    )
    .await
    .success
    {
        return Err("Docker Compose is unavailable; update Docker Desktop and retry".into());
    }
    let current = docker_service_states(&executable).await;
    if services_ready(&services, &current) {
        return Err("The selected local Docker services are already ready".into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result = begin_docker_services(&state, executable, services, lock).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

async fn begin_docker_services(
    state: &Wizard,
    executable: PathBuf,
    services: Vec<String>,
    install_lock: fs::File,
) -> Result<String, String> {
    let root = state.root()?.to_path_buf();
    let runtime = unpack(&root)?;
    let environment = local_docker_env_path(&root);
    if !environment.is_file() && existing_hcp_project(&executable).await {
        return Err(
            "An existing Open Content Creator Platform Docker project was found. Start it from its original workspace so the app does not replace its credentials."
                .into(),
        );
    }
    let environment = ensure_local_docker_env(&root)?;
    let compose = runtime.join("docker-compose.yml");
    let id = identifier();
    let jobs = root.join("jobs");
    fs::create_dir_all(&jobs).map_err(|_| "Cannot create setup job")?;
    let log = fs::File::create(jobs.join(format!("{}.log", id)))
        .map_err(|_| "Cannot create Docker setup log")?;
    let metadata_path = jobs.join(format!("{}.json", id));
    let mut metadata = json!({
        "id": id,
        "kind": "docker_services",
        "status": "starting",
        "owner_session": state.session,
        "services": services,
        "asset_version": ASSET_VERSION
    });
    write_json(&metadata_path, &metadata)?;
    let mut preferences = state.preferences()?;
    preferences.last_job = Some(id.clone());
    write_json(&state.preferences_path()?, &preferences)?;
    let mut command = background_command(&executable);
    command
        .args(docker_compose_arguments(
            &environment,
            &compose,
            &runtime,
            &services,
        ))
        .current_dir(&runtime)
        .stdin(Stdio::null())
        .stdout(
            log.try_clone()
                .map_err(|_| "Cannot open Docker setup log")?,
        )
        .stderr(log);
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(_) => {
            metadata["status"] = json!("failed");
            let _ = write_json(&metadata_path, &metadata);
            return Err("Could not start Docker Compose".into());
        }
    };
    metadata["status"] = json!("running");
    let _ = write_json(&metadata_path, &metadata);
    let running = state.running.clone();
    tauri::async_runtime::spawn(async move {
        let _install_lock = install_lock;
        let outcome = child.wait().await;
        let mut ready = false;
        let mut states = BTreeMap::new();
        if outcome.is_ok_and(|status| status.success()) {
            for _ in 0..60 {
                states = docker_service_states(&executable).await;
                if services_ready(&services, &states) {
                    ready = true;
                    break;
                }
                if states
                    .values()
                    .any(|status| status.to_ascii_lowercase().contains("unhealthy"))
                {
                    break;
                }
                sleep(Duration::from_secs(2)).await;
            }
        }
        metadata["status"] = json!(if ready { "finished" } else { "failed" });
        metadata["verified"] = json!(ready);
        metadata["service_states"] = json!(states);
        let _ = write_json(&metadata_path, &metadata);
        running.store(false, Ordering::SeqCst);
    });
    Ok(id)
}

fn docker_compose_arguments(
    environment: &Path,
    compose: &Path,
    runtime: &Path,
    services: &[String],
) -> Vec<OsString> {
    let mut arguments = vec![
        OsString::from("compose"),
        OsString::from("--env-file"),
        environment.as_os_str().to_owned(),
        OsString::from("-f"),
        compose.as_os_str().to_owned(),
        OsString::from("--project-directory"),
        runtime.as_os_str().to_owned(),
        OsString::from("up"),
        OsString::from("-d"),
    ];
    arguments.extend(services.iter().map(OsString::from));
    arguments
}

fn docker_bootstrap_steps(services: &[String]) -> Vec<&'static str> {
    let mut steps = Vec::new();
    if services.iter().any(|service| service == "postgres") {
        steps.push("postgres_migrations");
    }
    if services.iter().any(|service| service == "minio") {
        steps.push("minio_buckets");
    }
    if services.iter().any(|service| service == "n8n") {
        steps.push("n8n_workflows");
    }
    steps
}

fn docker_bootstrap_arguments(
    environment: &Path,
    compose: &Path,
    runtime: &Path,
    helper: &str,
) -> Vec<OsString> {
    vec![
        OsString::from("compose"),
        OsString::from("--env-file"),
        environment.as_os_str().to_owned(),
        OsString::from("-f"),
        compose.as_os_str().to_owned(),
        OsString::from("--project-directory"),
        runtime.as_os_str().to_owned(),
        OsString::from("run"),
        OsString::from("--rm"),
        OsString::from("--no-deps"),
        OsString::from(helper),
    ]
}

fn bootstrap_helper(step: &str) -> Option<&'static str> {
    match step {
        "postgres_migrations" => Some("postgres-bootstrap"),
        "minio_buckets" => Some("minio-bootstrap"),
        "n8n_workflows" => Some("n8n-bootstrap"),
        _ => None,
    }
}

#[tauri::command]
async fn start_local_service_bootstrap(
    state: tauri::State<'_, Wizard>,
    selected: Vec<String>,
) -> Result<String, String> {
    let services = docker_services(&catalog(), &selected)?;
    let steps = docker_bootstrap_steps(&services);
    if steps.is_empty() {
        return Err(
            "The selected modules do not require storage or workflow initialization".into(),
        );
    }
    let executable = docker_executable()
        .await
        .ok_or("Docker CLI is unavailable; install and open Docker Desktop first")?;
    let states = docker_service_states(&executable).await;
    let required: Vec<String> = services
        .iter()
        .filter(|service| matches!(service.as_str(), "postgres" | "minio" | "n8n"))
        .cloned()
        .collect();
    if !services_ready(&required, &states) {
        return Err(
            "Start the selected local services and wait for them to become ready first".into(),
        );
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("Another setup job is already running in this app".into());
    }
    let lock = match acquire_install_lock(state.root()?) {
        Ok(lock) => lock,
        Err(error) => {
            state.running.store(false, Ordering::SeqCst);
            return Err(error);
        }
    };
    let result = begin_local_service_bootstrap(&state, executable, services, steps, lock).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}

async fn begin_local_service_bootstrap(
    state: &Wizard,
    executable: PathBuf,
    services: Vec<String>,
    steps: Vec<&'static str>,
    install_lock: fs::File,
) -> Result<String, String> {
    let root = state.root()?.to_path_buf();
    let runtime = unpack(&root)?;
    let environment = local_docker_env_path(&root);
    if !environment.is_file() {
        return Err("Start the app-owned local services before initializing them".into());
    }
    let compose = runtime.join("docker-compose.yml");
    let id = identifier();
    let jobs = root.join("jobs");
    fs::create_dir_all(&jobs).map_err(|_| "Cannot create setup job")?;
    let log_path = jobs.join(format!("{}.log", id));
    let metadata_path = jobs.join(format!("{}.json", id));
    let step_states: BTreeMap<_, _> = steps
        .iter()
        .map(|step| ((*step).to_string(), "pending".to_string()))
        .collect();
    let mut metadata = json!({
        "id": id,
        "kind": "local_service_bootstrap",
        "status": "starting",
        "owner_session": state.session,
        "services": services,
        "steps": step_states,
        "asset_version": ASSET_VERSION,
        "credentials_saved": false
    });
    write_json(&metadata_path, &metadata)?;
    let mut preferences = state.preferences()?;
    preferences.last_job = Some(id.clone());
    write_json(&state.preferences_path()?, &preferences)?;
    let running = state.running.clone();
    tauri::async_runtime::spawn(async move {
        let _install_lock = install_lock;
        metadata["status"] = json!("running");
        let _ = write_json(&metadata_path, &metadata);
        let mut succeeded = true;
        for step in steps {
            metadata["steps"][step] = json!("running");
            let _ = write_json(&metadata_path, &metadata);
            let Some(helper) = bootstrap_helper(step) else {
                succeeded = false;
                metadata["steps"][step] = json!("failed");
                break;
            };
            let log = match OpenOptions::new().create(true).append(true).open(&log_path) {
                Ok(log) => log,
                Err(_) => {
                    succeeded = false;
                    metadata["steps"][step] = json!("failed");
                    break;
                }
            };
            let mut command = background_command(&executable);
            command
                .args(docker_bootstrap_arguments(
                    &environment,
                    &compose,
                    &runtime,
                    helper,
                ))
                .current_dir(&runtime)
                .stdin(Stdio::null())
                .stdout(match log.try_clone() {
                    Ok(file) => file,
                    Err(_) => {
                        succeeded = false;
                        metadata["steps"][step] = json!("failed");
                        break;
                    }
                })
                .stderr(log);
            let result = timeout(
                Duration::from_secs(180),
                command.kill_on_drop(true).status(),
            )
            .await;
            if result.is_ok_and(|result| result.is_ok_and(|status| status.success())) {
                metadata["steps"][step] = json!("finished");
            } else {
                succeeded = false;
                metadata["steps"][step] = json!("failed");
                break;
            }
            let _ = write_json(&metadata_path, &metadata);
        }
        if succeeded {
            metadata["credentials_saved"] = json!(save_local_service_credentials(&environment));
        }
        metadata["status"] = json!(if succeeded { "finished" } else { "failed" });
        metadata["verified"] = json!(succeeded);
        let _ = write_json(&metadata_path, &metadata);
        running.store(false, Ordering::SeqCst);
    });
    Ok(id)
}

#[tauri::command]
async fn start_install(
    state: tauri::State<'_, Wizard>,
    selected: Vec<String>,
) -> Result<String, String> {
    let selected = resolve(&catalog(), &selected)?;
    if selected.is_empty() {
        return Err("Choose a module first".into());
    }
    if state.running.swap(true, Ordering::SeqCst) {
        return Err("An installation is already running in this app".into());
    }
    let result = begin_install(&state, selected).await;
    if result.is_err() {
        state.running.store(false, Ordering::SeqCst);
    }
    result
}
async fn begin_install(state: &Wizard, selected: Vec<String>) -> Result<String, String> {
    let root = state.root()?.to_path_buf();
    let runtime = unpack(&root)?;
    let executable = python().await?;
    let id = identifier();
    let jobs = root.join("jobs");
    fs::create_dir_all(&jobs).map_err(|_| "Cannot create setup job")?;
    let report_directory = jobs.join(format!("{}-report", id));
    let log = fs::File::create(jobs.join(format!("{}.log", id)))
        .map_err(|_| "Cannot create install log")?;
    let mut command = process(&executable, &runtime, &root, "install", &selected);
    command
        .arg("--report-directory")
        .arg(&report_directory)
        .stdout(log.try_clone().map_err(|_| "Cannot open install log")?)
        .stderr(log);
    let metadata_path = jobs.join(format!("{}.json", id));
    let mut metadata = json!({
        "id": id,
        "kind": "module_dependencies",
        "status": "starting",
        "owner_session": state.session,
        "selected": selected
    });
    write_json(&metadata_path, &metadata)?;
    let mut preferences = state.preferences()?;
    preferences.last_job = Some(id.clone());
    write_json(&state.preferences_path()?, &preferences)?;
    // The Python installer holds an OS file lock across both apps. No shell is involved.
    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(_) => {
            metadata["status"] = json!("failed");
            let _ = write_json(&metadata_path, &metadata);
            return Err("Could not start Python installer".into());
        }
    };
    metadata["status"] = json!("running");
    let _ = write_json(&metadata_path, &metadata);
    let running = state.running.clone();
    tauri::async_runtime::spawn(async move {
        let outcome = child.wait().await;
        metadata["status"] = json!(if outcome.is_ok_and(|status| status.success()) {
            "finished"
        } else {
            "failed"
        });
        let _ = write_json(&metadata_path, &metadata);
        running.store(false, Ordering::SeqCst);
    });
    Ok(id)
}
#[tauri::command]
fn job_status(state: tauri::State<'_, Wizard>, id: String) -> Result<Value, String> {
    read_job(state.root()?, &id, &state.session)
}

/// Reconcile durable installer reports after an app restart without inventing completion.
pub fn read_job(root: &Path, id: &str, session: &str) -> Result<Value, String> {
    if id.is_empty() || !id.bytes().all(|b| b.is_ascii_digit() || b == b'-') {
        return Err("Invalid setup job".into());
    }
    let jobs = root.join("jobs");
    let mut job: Value = serde_json::from_slice(
        &fs::read(jobs.join(format!("{}.json", id)))
            .map_err(|_| "Install status is unavailable")?,
    )
    .map_err(|_| "Invalid install status")?;
    let report = fs::read(jobs.join(format!("{}-report/report.json", id)))
        .ok()
        .and_then(|bytes| serde_json::from_slice::<Value>(&bytes).ok());
    if let Some(ref value) = report {
        if value["status"] == "action_required" {
            job["status"] = json!("finished");
        }
        if value["status"] == "failed" {
            job["status"] = json!("failed");
        }
    }
    if matches!(job["status"].as_str(), Some("starting" | "running"))
        && job["owner_session"] != session
    {
        job["status"] = json!("unobserved");
    }
    job["report"] = json!(report);
    job["log_path"] = json!(jobs.join(format!("{}.log", id)));
    job.as_object_mut().unwrap().remove("owner_session");
    Ok(job)
}

pub fn init<R: Runtime>() -> tauri::plugin::TauriPlugin<R> {
    tauri::plugin::Builder::new("module-setup")
        .invoke_handler(tauri::generate_handler![
            snapshot,
            audio_setup_status,
            python_status,
            start_python_bootstrap,
            ffmpeg_status,
            start_ffmpeg_bootstrap,
            obs_status,
            start_obs_bootstrap,
            launch_obs,
            obs_scene_plan,
            docker_status,
            docker_plan,
            start_docker_bootstrap,
            launch_docker_desktop,
            start_docker_services,
            start_local_service_bootstrap,
            copy_local_credential,
            save_selection,
            manual,
            check,
            capture_scan,
            capture_test,
            save_capture_selection,
            start_install,
            job_status
        ])
        .setup(|app, _| {
            let root = app
                .path()
                .local_data_dir()
                .map(|p| p.join("HybridCreatorPlatform").join("module-setup"))
                .map_err(|_| "Cannot locate local setup storage".into());
            app.manage(Wizard {
                root,
                product: app.config().identifier.clone(),
                session: identifier(),
                running: Arc::new(AtomicBool::new(false)),
            });
            Ok(())
        })
        .build()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn resolves_only_requested_and_required_modules() {
        assert_eq!(
            resolve(&catalog(), &["broadcast-graphics".into()]).unwrap(),
            vec!["storage-data", "backend-api", "broadcast-graphics"]
        );
        assert!(resolve(&catalog(), &["../escape".into()]).is_err());
        let mut data = catalog();
        data["modules"]["storage-data"]["depends_on"] = json!(["backend-api"]);
        assert!(resolve(&data, &["backend-api".into()]).is_err());
        let too_many = vec!["storage-data".to_string(); 22];
        assert_eq!(
            resolve(&catalog(), &too_many).unwrap_err(),
            "Select at most 21 modules"
        );
    }
    #[test]
    fn bundles_catalog_guides_and_requirements() {
        let data = catalog();
        assert_eq!(data["modules"].as_object().unwrap().len(), 21);
        for item in data["modules"].as_object().unwrap().values() {
            for key in ["manual", "automated"] {
                assert!(ASSETS
                    .iter()
                    .any(|(p, _)| *p == item[key].as_str().unwrap()));
            }
            for requirement in item["requirements"].as_array().unwrap() {
                assert!(ASSETS
                    .iter()
                    .any(|(p, _)| *p == requirement.as_str().unwrap()));
            }
        }
    }
    #[test]
    fn preferences_round_trip_without_claiming_readiness() {
        let root = std::env::temp_dir().join(identifier());
        let path = root.join("preferences.json");
        write_json(
            &path,
            &Preferences {
                selected: vec!["audio-production".into()],
                last_job: None,
                ..Preferences::default()
            },
        )
        .unwrap();
        let value: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        assert_eq!(value["selected"], json!(["audio-production"]));
        assert!(value.get("ready").is_none());
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn restarted_job_stays_unknown_until_the_installer_reports_completion() {
        let root = std::env::temp_dir().join(identifier());
        let id = "123-456";
        write_json(
            &root.join("jobs/123-456.json"),
            &json!({"id":id,"status":"running","owner_session":"old"}),
        )
        .unwrap();
        assert_eq!(read_job(&root, id, "new").unwrap()["status"], "unobserved");
        write_json(
            &root.join("jobs/123-456-report/report.json"),
            &json!({"status":"action_required","modules":[]}),
        )
        .unwrap();
        assert_eq!(read_job(&root, id, "new").unwrap()["status"], "finished");
        assert!(read_job(&root, "../secret", "new").is_err());
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn capture_selection_requires_a_device_from_the_latest_scan() {
        let report = json!({"devices":[
            {"id":"dshow:video:USB Capture", "kind":"video"},
            {"id":"dshow:audio:Digital Audio", "kind":"audio"}
        ]});
        assert!(valid_capture_id(
            &report,
            "dshow:video:USB Capture",
            "video"
        ));
        assert!(valid_capture_id(
            &report,
            "dshow:audio:Digital Audio",
            "audio"
        ));
        assert!(!valid_capture_id(
            &report,
            "dshow:audio:Digital Audio",
            "video"
        ));
        assert!(!valid_capture_id(&report, "../unscanned", "video"));
    }
    #[test]
    fn python_bootstrap_uses_only_fixed_package_manager_arguments() {
        let (executable, args) = python_bootstrap_spec("windows", None).unwrap();
        assert_eq!(executable, "winget");
        assert_eq!(args[0], "install");
        assert!(args
            .windows(2)
            .any(|pair| pair == ["--id", "Python.Python.3.12"]));
        assert!(args.contains(&"--scope".into()));
        assert!(args.contains(&"user".into()));
        assert!(args.contains(&"--silent".into()));
        assert!(python_bootstrap_spec("linux", None).is_err());
    }

    #[test]
    fn ffmpeg_bootstrap_uses_only_fixed_package_manager_arguments() {
        let (executable, args) = ffmpeg_bootstrap_spec("windows", None).unwrap();
        assert_eq!(executable, "winget");
        assert_eq!(args[0], "install");
        assert!(args.windows(2).any(|pair| pair == ["--id", "Gyan.FFmpeg"]));
        assert!(args.contains(&"--silent".into()));
        assert!(!args.iter().any(|value| value
            .chars()
            .any(|character| matches!(character, ';' | '|' | '&'))));
        assert!(ffmpeg_bootstrap_spec("linux", None).is_err());
    }

    #[test]
    fn python_bootstrap_lock_is_shared_and_released() {
        let root = std::env::temp_dir().join(format!("setup-wizard-lock-{}", identifier()));
        let first = acquire_install_lock(&root).unwrap();
        assert_eq!(
            acquire_install_lock(&root).unwrap_err(),
            "Another setup installation is already running"
        );
        drop(first);
        acquire_install_lock(&root).unwrap();
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn obs_bootstrap_uses_only_fixed_package_manager_arguments() {
        let (executable, args) = obs_bootstrap_spec("windows", None).unwrap();
        assert_eq!(executable, "winget");
        assert_eq!(args[0], "install");
        assert!(args
            .windows(2)
            .any(|pair| pair == ["--id", "OBSProject.OBSStudio"]));
        assert!(args.contains(&"--silent".into()));
        assert!(!args.iter().any(|value| value
            .chars()
            .any(|character| matches!(character, ';' | '|' | '&'))));
        assert!(obs_bootstrap_spec("linux", None).is_err());
    }

    #[test]
    fn bundled_obs_scene_plan_is_preview_only() {
        let plan = obs_scene_plan().unwrap();
        assert_eq!(plan["name"], "HCP Default");
        assert_eq!(plan["scenes"].as_array().unwrap().len(), 8);
        assert_eq!(plan["apply_available"], false);
        assert_eq!(plan["asset_version"], ASSET_VERSION);
    }

    #[test]
    fn docker_bootstrap_uses_only_fixed_package_manager_arguments() {
        let (executable, args) = docker_bootstrap_spec("windows", None).unwrap();
        assert_eq!(executable, "winget");
        assert_eq!(args[0], "install");
        assert!(args
            .windows(2)
            .any(|pair| pair == ["--id", "Docker.DockerDesktop"]));
        assert!(args.contains(&"--silent".into()));
        assert!(!args.iter().any(|value| value
            .chars()
            .any(|character| matches!(character, ';' | '|' | '&'))));
        assert!(docker_bootstrap_spec("linux", None).is_err());
    }

    #[test]
    fn docker_plan_resolves_only_catalog_services_and_dependencies() {
        let data = catalog();
        assert_eq!(
            docker_services(&data, &["broadcast-graphics".into()]).unwrap(),
            vec!["postgres", "redis", "minio", "fastapi", "nodecg"]
        );
        assert_eq!(
            docker_services(&data, &["automation-control".into()]).unwrap(),
            vec!["postgres", "redis", "minio", "fastapi", "n8n"]
        );
        let mut unsafe_data = data;
        unsafe_data["modules"]["storage-data"]["compose_services"] = json!(["../shell"]);
        assert!(docker_services(&unsafe_data, &["storage-data".into()]).is_err());
    }

    #[test]
    fn docker_compose_command_uses_only_bundled_paths_and_allowlisted_services() {
        let services = docker_services(&catalog(), &["automation-control".into()]).unwrap();
        let arguments = docker_compose_arguments(
            Path::new("/private/setup/local.env"),
            Path::new("/private/runtime/docker-compose.yml"),
            Path::new("/private/runtime"),
            &services,
        );
        assert_eq!(
            arguments,
            [
                "compose",
                "--env-file",
                "/private/setup/local.env",
                "-f",
                "/private/runtime/docker-compose.yml",
                "--project-directory",
                "/private/runtime",
                "up",
                "-d",
                "postgres",
                "redis",
                "minio",
                "fastapi",
                "n8n",
            ]
            .into_iter()
            .map(OsString::from)
            .collect::<Vec<_>>()
        );
    }

    #[test]
    fn docker_failure_classifier_does_not_guess_that_wsl_is_required() {
        assert_eq!(
            classify_docker_state(
                true,
                true,
                false,
                false,
                false,
                "engine pipe not found",
                "missing"
            )
            .0,
            "desktop_stopped"
        );
        assert_eq!(
            classify_docker_state(
                true,
                true,
                true,
                false,
                false,
                "Docker WSL backend requires an update",
                "update_required"
            )
            .0,
            "wsl_update_required"
        );
        assert_eq!(
            classify_docker_state(
                true,
                true,
                true,
                false,
                false,
                "restart Windows to continue",
                "ready"
            )
            .0,
            "reboot_required"
        );
        assert_eq!(
            classify_docker_state(
                true,
                true,
                true,
                false,
                false,
                "hardware virtualization is disabled",
                "ready"
            )
            .0,
            "virtualization_unavailable"
        );
    }

    #[test]
    fn docker_local_environment_is_private_and_reused() {
        let root = std::env::temp_dir().join(format!("setup-wizard-docker-{}", identifier()));
        let path = ensure_local_docker_env(&root).unwrap();
        let first = fs::read_to_string(&path).unwrap();
        assert!(first.contains("MINIO_ROOT_USER=hcpadmin"));
        assert!(!first.contains("change-me"));
        assert_eq!(ensure_local_docker_env(&root).unwrap(), path);
        assert_eq!(fs::read_to_string(&path).unwrap(), first);
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            assert_eq!(
                fs::metadata(&path).unwrap().permissions().mode() & 0o777,
                0o600
            );
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn docker_resources_and_windows_utf16_diagnostics_are_bundled() {
        for path in [
            "docker-compose.yml",
            "modules/storage-data/minio/Dockerfile",
            "modules/storage-data/minio/provenance.json",
            "modules/backend-api/fastapi/Dockerfile",
            "modules/observability/prometheus/prometheus.yml",
            "modules/broadcast-graphics/nodecg/bundles/hcp-starter/package.json",
            "scripts/setup/postgres_container_migrate.sh",
        ] {
            assert!(ASSETS.iter().any(|(asset, _)| *asset == path), "{path}");
        }
        let compose = ASSETS
            .iter()
            .find_map(|(path, contents)| (*path == "docker-compose.yml").then_some(*contents))
            .expect("docker-compose.yml is bundled");
        assert!(compose.contains("mc ilm rule import"));
        assert!(!compose.contains("mc ilm import"));
        let utf16: Vec<u8> = [0xff, 0xfe]
            .into_iter()
            .chain(
                "WSL requires an update"
                    .encode_utf16()
                    .flat_map(u16::to_le_bytes),
            )
            .collect();
        assert_eq!(decode_command_output(&utf16), "WSL requires an update");
    }

    #[test]
    fn local_bootstrap_plan_is_bounded_by_selected_services() {
        assert_eq!(
            docker_bootstrap_steps(&["postgres".into(), "redis".into(), "minio".into()]),
            vec!["postgres_migrations", "minio_buckets"]
        );
        assert_eq!(
            docker_bootstrap_steps(&[
                "postgres".into(),
                "redis".into(),
                "minio".into(),
                "fastapi".into(),
                "n8n".into(),
            ]),
            vec!["postgres_migrations", "minio_buckets", "n8n_workflows"]
        );
        assert!(docker_bootstrap_steps(&["redis".into()]).is_empty());
        assert!(bootstrap_helper("arbitrary").is_none());
    }

    #[test]
    fn local_bootstrap_command_uses_only_bundled_paths_and_fixed_helper() {
        let args = docker_bootstrap_arguments(
            Path::new("/private/local.env"),
            Path::new("/bundle/docker-compose.yml"),
            Path::new("/bundle"),
            bootstrap_helper("minio_buckets").unwrap(),
        );
        assert_eq!(
            args,
            vec![
                "compose",
                "--env-file",
                "/private/local.env",
                "-f",
                "/bundle/docker-compose.yml",
                "--project-directory",
                "/bundle",
                "run",
                "--rm",
                "--no-deps",
                "minio-bootstrap",
            ]
            .into_iter()
            .map(OsString::from)
            .collect::<Vec<_>>()
        );
    }

    #[test]
    fn local_environment_parser_keeps_secrets_private_and_rejects_unknown_syntax() {
        let root = std::env::temp_dir().join(format!("setup-wizard-env-{}", identifier()));
        fs::create_dir_all(&root).unwrap();
        let valid = root.join("valid.env");
        fs::write(&valid, "N8N_USER=admin\nN8N_PASSWORD=a=b\n").unwrap();
        let parsed = docker_environment(&valid).unwrap();
        assert_eq!(parsed["N8N_PASSWORD"], "a=b");
        assert_eq!(
            local_credential_key("n8n_password").unwrap().0,
            "N8N_PASSWORD"
        );
        assert_eq!(
            local_credential_key("hcp_api_key").unwrap().0,
            "HCP_API_KEY"
        );
        assert!(local_credential_key("../secret").is_none());
        let invalid = root.join("invalid.env");
        fs::write(&invalid, "lowercase=value\n").unwrap();
        assert!(docker_environment(&invalid).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
