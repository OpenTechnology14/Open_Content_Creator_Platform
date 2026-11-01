//! Fixed-command bridge to the bundled Stream Autopilot lifecycle rehearsal.

use serde_json::Value;
use std::{fs, path::PathBuf, process::Stdio};
use tokio::{
    process::Command,
    time::{timeout, Duration},
};

include!(concat!(env!("OUT_DIR"), "/autopilot-assets.rs"));

pub struct AutopilotBridge {
    root: PathBuf,
    module_setup_root: PathBuf,
}

impl AutopilotBridge {
    pub fn new(root: PathBuf, module_setup_root: PathBuf) -> Self {
        Self {
            root,
            module_setup_root,
        }
    }

    pub(crate) fn unpack(&self) -> Result<PathBuf, String> {
        let runtime = self.root.join("runtime-v1");
        for (relative, contents) in FILES {
            let target = runtime.join(relative);
            fs::create_dir_all(target.parent().unwrap())
                .map_err(|_| "Cannot prepare the Autopilot runtime")?;
            fs::write(target, contents).map_err(|_| "Cannot prepare the Autopilot runtime")?;
        }
        Ok(runtime)
    }

    pub(crate) fn interpreter(&self) -> Result<PathBuf, String> {
        let path = self
            .module_setup_root
            .join(".venv-modules")
            .join("automation-control")
            .join(if cfg!(windows) {
                "Scripts/python.exe"
            } else {
                "bin/python"
            });
        if path.is_file() {
            Ok(path)
        } else {
            Err(
                "Install Automation / Control in Module setup before running Autopilot checks"
                    .into(),
            )
        }
    }

    async fn call(&self, action: &str, session_id: Option<&str>) -> Result<Value, String> {
        if let Some(session_id) = session_id {
            if session_id.is_empty()
                || session_id.len() > 64
                || !session_id
                    .bytes()
                    .all(|value| value.is_ascii_alphanumeric() || value == b'_' || value == b'-')
            {
                return Err("Choose a configured Autopilot session".into());
            }
        }
        let runtime = self.unpack()?;
        let executable = self.interpreter()?;
        let mut command = Command::new(executable);
        command
            .args(["-m", "stream_autopilot"])
            .arg("--config")
            .arg(runtime.join("configs/local/stream-supervisor.yaml"))
            .arg(action)
            .env("PYTHONPATH", runtime.join("modules/automation-control"))
            .env("PYTHONUTF8", "1")
            .current_dir(&runtime)
            .stdin(Stdio::null())
            .kill_on_drop(true);
        if action == "rehearse" {
            command.arg("--state").arg(self.root.join("state.json"));
        }
        if let Some(session_id) = session_id {
            command.arg("--session").arg(session_id);
        }
        let output = timeout(Duration::from_secs(20), command.output())
            .await
            .map_err(|_| "Autopilot check timed out")?
            .map_err(|_| "Could not start the Autopilot runtime")?;
        if !output.status.success() {
            return Err("Autopilot check failed; review its configuration and Module setup".into());
        }
        serde_json::from_slice(&output.stdout)
            .map_err(|_| "Autopilot returned an invalid report".into())
    }
}

#[tauri::command]
pub async fn autopilot_status(bridge: tauri::State<'_, AutopilotBridge>) -> Result<Value, String> {
    bridge.call("status", None).await
}

#[tauri::command]
pub async fn autopilot_rehearse(
    bridge: tauri::State<'_, AutopilotBridge>,
    session_id: String,
) -> Result<Value, String> {
    bridge.call("rehearse", Some(&session_id)).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bundles_only_fixed_supervisor_sources_and_policy() {
        assert!(FILES.len() > 25);
        assert!(FILES
            .iter()
            .any(|(path, _)| *path == "configs/local/stream-runtime.yaml"));
        assert!(FILES
            .iter()
            .all(|(path, contents)| { !path.contains("..") && !contents.is_empty() }));
    }
}
