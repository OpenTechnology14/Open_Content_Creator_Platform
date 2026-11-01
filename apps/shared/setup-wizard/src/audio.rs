//! Read-only audio installation evidence and compiled routing references.
use serde_json::{json, Value};
use std::path::PathBuf;

const CONFIG: &str = include_str!("../../../../configs/local/audio-setup.json");

fn expand_path(path: &str, variable: &impl Fn(&str) -> Option<String>) -> Option<PathBuf> {
    if let Some(rest) = path.strip_prefix("${") {
        let (key, suffix) = rest.split_once('}')?;
        let root = variable(key)?;
        if root.is_empty() {
            return None;
        }
        Some(PathBuf::from(format!("{root}{suffix}")))
    } else {
        Some(PathBuf::from(path))
    }
}

fn report(
    platform: &str,
    variable: impl Fn(&str) -> Option<String>,
    exists: impl Fn(&std::path::Path) -> bool,
) -> Result<Value, String> {
    let config: Value = serde_json::from_str(CONFIG).map_err(|_| "Invalid audio setup catalog")?;
    let recipe = config["platforms"]
        .get(platform)
        .ok_or("Audio setup guidance is unavailable on this platform")?;
    let checks: Vec<Value> = recipe["tools"]
        .as_array()
        .ok_or("Invalid audio tool catalog")?
        .iter()
        .map(|tool| {
            let found = tool["paths"].as_array().into_iter().flatten()
                .filter_map(|path| expand_path(path.as_str()?, &variable))
                .find(|path| exists(path));
            json!({"name":tool["label"], "status":if found.is_some() {"found"} else {"not_found"},
                "path":found.map(|path| path.to_string_lossy().into_owned()),
                "detail":"Standard-location presence only; driver operation and routing are not verified."})
        })
        .collect();
    let path = recipe["reference"]
        .as_str()
        .ok_or("Missing audio reference")?;
    let contents = super::ASSETS
        .iter()
        .find(|(key, _)| *key == path)
        .map(|(_, contents)| *contents)
        .ok_or("Audio reference is not bundled")?;
    Ok(
        json!({"schema_version":1,"platform":platform,"checked_at":std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default().as_secs(),
        "capability_status":"not_verified", "checks":checks,
        "guidance":recipe["guidance"], "reference":{"path":path,"contents":contents},
        "acceptance":config["acceptance"],
        "scope":"Read-only installation evidence. No drivers installed, routes changed, audio recorded or hotkeys triggered. Not found means absent from standard locations; custom installations may exist."}),
    )
}

#[tauri::command]
pub fn audio_setup_status() -> Result<Value, String> {
    report(
        std::env::consts::OS,
        |key| std::env::var(key).ok(),
        |path| path.exists(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_tools_leave_audio_unverified_and_keep_guidance_available() {
        for platform in ["macos", "windows", "linux"] {
            let value = report(platform, |_| None, |_| false).unwrap();
            assert_eq!(value["capability_status"], "not_verified");
            assert!(value["checks"]
                .as_array()
                .unwrap()
                .iter()
                .all(|check| check["status"] == "not_found"));
            assert!(!value["reference"]["contents"].as_str().unwrap().is_empty());
            assert_eq!(value["acceptance"].as_array().unwrap().len(), 4);
        }
        assert!(report("other", |_| None, |_| false).is_err());
    }

    #[test]
    fn installed_driver_is_presence_not_signal_or_acceptance() {
        let value = report(
            "macos",
            |_| None,
            |path| path == std::path::Path::new("/Library/Audio/Plug-Ins/HAL/BlackHole16ch.driver"),
        )
        .unwrap();
        assert_eq!(value["checks"][0]["status"], "found");
        assert_eq!(value["checks"][1]["status"], "not_found");
        assert_eq!(value["capability_status"], "not_verified");
        assert!(value.get("accepted").is_none());
    }

    #[test]
    fn windows_environment_roots_resolve_without_executing_anything() {
        let value = report(
            "windows",
            |key| (key == "ProgramFiles(x86)").then(|| "D:/Apps".into()),
            |path| path == std::path::Path::new("D:/Apps/VB/Voicemeeter/voicemeeter8x64.exe"),
        )
        .unwrap();
        assert_eq!(value["checks"][0]["status"], "found");
        assert!(expand_path("${UNKNOWN}/tool", &|_| None).is_none());
        assert!(expand_path("${HOME}/tool", &|_| Some(String::new())).is_none());
    }

    #[test]
    fn current_host_probe_is_read_only() {
        let value = audio_setup_status().unwrap();
        assert_eq!(value["platform"], std::env::consts::OS);
        assert_eq!(value["capability_status"], "not_verified");
        println!(
            "Audio probe: platform={}, checks={}",
            value["platform"], value["checks"]
        );
    }
}
