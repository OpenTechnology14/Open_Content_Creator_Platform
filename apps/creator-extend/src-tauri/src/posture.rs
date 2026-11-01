//! Posture screening for Creator Extend.
//!
//! Runs a single uploaded photo through the MediaPipe-based still-image
//! analyzer in modules/sports-analytics/pose-estimation/posture_screen.py
//! and returns landmarks + derived posture metrics for the frontend to
//! render as an overlay.

use std::{path::Path, process::Command};

/// Analyze one uploaded photo for posture. `view` must be "front", "side",
/// or "back" — the analyzer computes different metrics per view.
pub async fn analyze(
    runtime_root: &Path,
    image_path: &str,
    view: &str,
    interpreter: &str,
) -> Result<serde_json::Value, Box<dyn std::error::Error + Send + Sync>> {
    if !matches!(view, "front" | "side" | "back") {
        return Err(format!("Unknown view '{}': expected front, side, or back", view).into());
    }

    let script_path =
        runtime_root.join("modules/sports-analytics/pose-estimation/posture_screen.py");
    if !script_path.is_file() {
        return Err("Posture analyzer is unavailable in the Creator tool runtime".into());
    }

    let output = Command::new(interpreter)
        .arg(script_path)
        .arg("--image")
        .arg(image_path)
        .arg("--view")
        .arg(view)
        .output()
        .map_err(|e| format!("Failed to run posture analyzer: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout);

    // The script always prints one JSON object to stdout, on both success
    // and handled failure (e.g. "no person detected") — parse it either way
    // rather than branching solely on exit status.
    let parsed: serde_json::Value = serde_json::from_str(stdout.trim()).map_err(|e| {
        let stderr = String::from_utf8_lossy(&output.stderr);
        format!(
            "Posture analyzer returned unparseable output: {} (stderr: {})",
            e, stderr
        )
    })?;

    Ok(parsed)
}
