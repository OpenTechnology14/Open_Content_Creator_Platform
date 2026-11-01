//! Krita integration for Creator Extend.
//!
//! Launches Krita, runs automation scripts (batch upscale, style transfer,
//! export to MinIO), and manages the AI Diffusion plugin connection.

use std::{path::Path, process::Command};

/// Auto-detect Krita path by platform.
pub fn detect_krita() -> Option<String> {
    let candidates = if cfg!(target_os = "macos") {
        vec![
            "/Applications/krita.app/Contents/MacOS/krita",
            "/opt/homebrew/bin/krita",
        ]
    } else if cfg!(target_os = "windows") {
        vec![
            "C:\\Program Files\\Krita (x64)\\bin\\krita.exe",
            "C:\\Program Files\\Krita\\bin\\krita.exe",
        ]
    } else {
        vec!["/usr/bin/krita", "/snap/bin/krita"]
    };

    if let Ok(output) = Command::new("which").arg("krita").output() {
        if output.status.success() {
            let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !path.is_empty() {
                return Some(path);
            }
        }
    }

    for candidate in candidates {
        if std::path::Path::new(candidate).exists() {
            return Some(candidate.to_string());
        }
    }

    None
}

/// Open Krita, optionally with a file.
pub async fn open(
    krita_path: Option<&str>,
    file_path: Option<&str>,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let path = krita_path
        .map(String::from)
        .or_else(detect_krita)
        .ok_or("Krita not found. Install Krita or set the path in settings.")?;

    let mut cmd = Command::new(&path);

    if let Some(file) = file_path {
        cmd.arg(file);
    }

    cmd.spawn()
        .map_err(|e| format!("Failed to launch Krita at {}: {}", path, e))?;

    Ok(())
}

/// Run a Krita automation script.
///
/// Available scripts (from modules/image-editing/krita/scripts/):
/// - batch_upscale — Bulk upscale images via ComfyUI
/// - apply_style — IPAdapter style transfer
/// - export_to_minio — Upload to MinIO/S3
pub async fn run_script(
    runtime_root: &Path,
    script_name: &str,
    args: &[String],
    interpreter: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    if !matches!(
        script_name,
        "batch_upscale" | "apply_style" | "export_to_minio"
    ) {
        return Err(
            "Unknown Creator tool. Available: batch_upscale, apply_style, export_to_minio".into(),
        );
    }
    if args != ["--dry-run"] {
        return Err("Creator tool actions only support the built-in dry-run check".into());
    }
    let script_path = runtime_root
        .join("modules/image-editing/krita/scripts")
        .join(format!("{script_name}.py"));

    let mut cmd = Command::new(interpreter);
    cmd.arg(&script_path);
    cmd.env("PYTHONPATH", runtime_root.join("modules/asset-pipeline"));

    for arg in args {
        cmd.arg(arg);
    }

    let output = cmd
        .output()
        .map_err(|e| format!("Failed to run script: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Script failed: {}", stderr).into());
    }

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
