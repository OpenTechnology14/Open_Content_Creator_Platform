//! Blender integration for Creator Extend.
//!
//! Launches Blender as a subprocess, manages project files,
//! and triggers render jobs (local or cloud burst).

use std::{path::Path, process::Command};

/// Auto-detect Blender path by platform.
pub fn detect_blender() -> Option<String> {
    let candidates = if cfg!(target_os = "macos") {
        vec![
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/opt/homebrew/bin/blender",
        ]
    } else if cfg!(target_os = "windows") {
        vec![
            "C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
            "C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
        ]
    } else {
        vec!["/usr/bin/blender", "/snap/bin/blender"]
    };

    // Check PATH first
    if let Ok(output) = Command::new("which").arg("blender").output() {
        if output.status.success() {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !path.is_empty() {
                return Some(path);
            }
        }
    }

    // Check known locations
    for candidate in candidates {
        if std::path::Path::new(candidate).exists() {
            return Some(candidate.to_string());
        }
    }

    None
}

/// Open Blender, optionally with a project file.
pub async fn open(
    blender_path: Option<&str>,
    project_path: Option<&str>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let path = blender_path
        .map(String::from)
        .or_else(detect_blender)
        .ok_or("Blender not found. Install Blender or set the path in settings.")?;

    let mut cmd = Command::new(&path);

    if let Some(project) = project_path {
        cmd.arg(project);
    }

    cmd.spawn()
        .map_err(|e| format!("Failed to launch Blender at {}: {}", path, e))?;

    Ok(())
}

/// Run a Blender Python script in background mode (no GUI).
pub async fn run_script(
    blender_path: Option<&str>,
    script_path: &str,
    args: &[String],
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let path = blender_path
        .map(String::from)
        .or_else(detect_blender)
        .ok_or("Blender not found")?;

    let mut cmd = Command::new(&path);
    cmd.arg("--background")
        .arg("--python")
        .arg(script_path)
        .arg("--");

    for arg in args {
        cmd.arg(arg);
    }

    let output = cmd
        .output()
        .map_err(|e| format!("Failed to run Blender script: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Blender script failed: {}", stderr).into());
    }

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

/// Run the packaged batch-render planner against an operator-selected
/// project. Dry-run mode only inspects scenes and emits a JSON plan.
pub async fn batch_render(
    blender_path: Option<&str>,
    runtime_root: &Path,
    project_path: &str,
    output_path: &str,
    dry_run: bool,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    if !dry_run {
        return Err("Use the owned Blender job command with explicit scene selection".into());
    }
    if project_path.len() > 4096
        || project_path.chars().any(char::is_control)
        || !project_path.to_ascii_lowercase().ends_with(".blend")
    {
        return Err("Choose a Blender .blend project file".into());
    }
    if !Path::new(project_path).is_file() {
        return Err("The selected Blender project file does not exist".into());
    }
    if output_path.is_empty()
        || output_path.len() > 4096
        || output_path.chars().any(char::is_control)
    {
        return Err("Choose a valid output directory".into());
    }
    let script = runtime_root.join("modules/content-creation/blender/scripts/batch_render.py");
    if !script.is_file() {
        return Err("Blender batch-render job is unavailable in the Creator tool runtime".into());
    }
    let path = blender_path
        .map(String::from)
        .or_else(detect_blender)
        .ok_or("Blender not found. Install Blender or set the path in settings.")?;
    let mut cmd = Command::new(&path);
    cmd.arg("--background")
        .arg("--factory-startup")
        .arg("--disable-autoexec")
        .arg(project_path)
        .arg("--python")
        .arg(script)
        .arg("--")
        .arg("--output")
        .arg(output_path);
    if dry_run {
        cmd.arg("--dry-run");
    }
    let output = cmd
        .output()
        .map_err(|e| format!("Failed to run Blender batch job: {e}"))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Blender batch job failed: {stderr}").into());
    }
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
