//! Versioned, allowlisted source files used by Creator's local tool actions.
//!
//! The application ships these sources with its binary and reconstructs them
//! under private app data. No action resolves a file from the repository or a
//! webview-supplied path.

use std::{fs, path::PathBuf, process::Command};

use serde::Serialize;

include!(concat!(env!("OUT_DIR"), "/tool_catalog.rs"));

#[derive(Clone)]
pub struct ToolRuntime {
    root: PathBuf,
}

#[derive(Debug, Clone, Serialize)]
pub struct ToolCheck {
    pub id: String,
    pub label: String,
    pub packaged: bool,
    pub interpreter: Option<String>,
    pub ready: bool,
    pub detail: String,
}

#[cfg(target_os = "windows")]
fn background_command(program: &str) -> Command {
    let mut command = Command::new(program);
    use std::os::windows::process::CommandExt;
    command.creation_flags(0x08000000); // CREATE_NO_WINDOW
    command
}

#[cfg(not(target_os = "windows"))]
fn background_command(program: &str) -> Command {
    Command::new(program)
}

impl ToolRuntime {
    pub fn new(root: PathBuf) -> Self {
        Self { root }
    }

    pub fn unpack(&self) -> Result<PathBuf, String> {
        let runtime = self.root.join("runtime-v1");
        for (relative, contents) in BUNDLED_TOOL_FILES {
            let target = runtime.join(relative);
            let parent = target
                .parent()
                .ok_or("Cannot prepare Creator tool runtime")?;
            fs::create_dir_all(parent).map_err(|_| "Cannot prepare Creator tool runtime")?;
            fs::write(target, contents).map_err(|_| "Cannot prepare Creator tool runtime")?;
        }
        Ok(runtime)
    }

    /// Run side-effect-free `--help` checks for the fixed scripts shipped in
    /// the app. This proves the package can start each script and that its
    /// imports are available without touching a user's files or services.
    pub fn check(&self) -> Result<Vec<ToolCheck>, String> {
        let runtime = self.unpack()?;
        let specs = [
            (
                "batch-upscale",
                "Batch Upscale",
                "modules/image-editing/krita/scripts/batch_upscale.py",
                "image-editing",
            ),
            (
                "style-transfer",
                "Style Transfer",
                "modules/image-editing/krita/scripts/apply_style.py",
                "image-editing",
            ),
            (
                "minio-export",
                "MinIO Export",
                "modules/image-editing/krita/scripts/export_to_minio.py",
                "image-editing",
            ),
            (
                "posture-screen",
                "Posture Screen",
                "modules/sports-analytics/pose-estimation/posture_screen.py",
                "sports-analytics",
            ),
        ];
        let mut checks = specs
            .into_iter()
            .map(|(id, label, relative, module)| {
                let script = runtime.join(relative);
                let interpreter = self.interpreter_for(module);
                let (ready, detail) = match interpreter.as_deref() {
                    Some(executable) if script.is_file() => match background_command(executable)
                        .arg(&script)
                        .arg("--help")
                        .output()
                    {
                        Ok(output) if output.status.success() => (
                            true,
                            "Packaged script and Python imports are ready.".to_string(),
                        ),
                        Ok(output) => {
                            let detail = String::from_utf8_lossy(&output.stderr)
                                .lines()
                                .last()
                                .unwrap_or_default()
                                .trim()
                                .to_string();
                            let detail = dependency_detail(&detail);
                            (
                                false,
                                if detail.is_empty() {
                                    "The script could not load; install its module dependencies."
                                        .into()
                                } else {
                                    format!("Dependency check failed: {detail}")
                                },
                            )
                        }
                        Err(error) => (false, format!("Python could not start: {error}")),
                    },
                    Some(_) => (
                        false,
                        "The packaged script is missing from app data.".into(),
                    ),
                    None => (
                        false,
                        "Install Python 3.11+ from Module setup, then check again.".into(),
                    ),
                };
                ToolCheck {
                    id: id.into(),
                    label: label.into(),
                    packaged: script.is_file(),
                    interpreter,
                    ready,
                    detail,
                }
            })
            .collect::<Vec<_>>();
        let addon_files = [
            "plugins/blender-addon/__init__.py",
            "plugins/blender-addon/preferences.py",
            "plugins/blender-addon/panels.py",
            "plugins/blender-addon/operators/__init__.py",
        ];
        let addon_packaged = addon_files.iter().all(|path| runtime.join(path).is_file());
        checks.push(ToolCheck {
            id: "blender-addon".into(),
            label: "Blender addon".into(),
            packaged: addon_packaged,
            interpreter: None,
            ready: addon_packaged,
            detail: if addon_packaged {
                "Packaged addon payload is ready; install and enable it from Blender.".into()
            } else {
                "The packaged Blender addon payload is incomplete.".into()
            },
        });
        let batch_job = runtime.join("modules/content-creation/blender/scripts/batch_render.py");
        checks.push(ToolCheck {
            id: "blender-batch-job".into(),
            label: "Blender batch render job".into(),
            packaged: batch_job.is_file(),
            interpreter: None,
            ready: batch_job.is_file(),
            detail: if batch_job.is_file() {
                "Dry-run render planner is packaged; choose a .blend file and output folder to use it."
                    .into()
            } else {
                "The packaged Blender batch-render job is missing.".into()
            },
        });
        Ok(checks)
    }

    /// Create a deterministic Blender addon ZIP in private app data. The ZIP
    /// is intended for Blender's normal Add-ons → Install flow.
    pub fn archive_blender_addon(&self) -> Result<PathBuf, String> {
        let runtime = self.unpack()?;
        let source = runtime.join("plugins/blender-addon");
        if !source.is_dir() {
            return Err("Blender addon is unavailable in the Creator tool runtime".into());
        }
        let executable = self
            .interpreter_for("image-editing")
            .ok_or("Install Python from Module setup before preparing the Blender addon")?;
        let archive = self.root.join("blender-addon.zip");
        let script = r#"
import os, sys, zipfile
source, target, worker = sys.argv[1:4]
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as bundle:
    for directory, _, files in os.walk(source):
        for name in sorted(files):
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, source)
            bundle.write(path, os.path.join("creator_extend", relative))
    bundle.write(worker, "creator_extend/render_worker.py")
"#;
        background_command(&executable)
            .arg("-c")
            .arg(script)
            .arg(&source)
            .arg(&archive)
            .arg(runtime.join("modules/content-creation/blender/scripts/batch_render.py"))
            .output()
            .map_err(|error| format!("Could not prepare Blender addon package: {error}"))
            .and_then(|output| {
                if output.status.success() && archive.is_file() {
                    Ok(archive)
                } else {
                    Err("Could not prepare Blender addon package".into())
                }
            })
    }

    /// Resolve the interpreter for a module, preferring the shared module
    /// virtualenv created by Module setup and falling back to a system Python.
    pub fn interpreter_for(&self, module: &str) -> Option<String> {
        let environment = self
            .root
            .parent()?
            .join("module-setup")
            .join(".venv-modules")
            .join(module);
        let virtualenv = if cfg!(windows) {
            environment.join("Scripts/python.exe")
        } else {
            environment.join("bin/python")
        };
        if virtualenv.is_file() {
            return Some(virtualenv.to_string_lossy().into_owned());
        }
        let candidates = if cfg!(windows) {
            ["python", "py"]
        } else {
            ["python3", "python"]
        };
        candidates
            .into_iter()
            .find(|candidate| {
                background_command(candidate)
                    .arg("--version")
                    .output()
                    .is_ok_and(|output| output.status.success())
            })
            .map(String::from)
    }
}

fn dependency_detail(detail: &str) -> String {
    for (module, name) in [
        ("cv2", "OpenCV"),
        ("mediapipe", "MediaPipe"),
        ("requests", "Requests"),
        ("minio", "MinIO SDK"),
    ] {
        if detail.contains(&format!("No module named '{module}'")) {
            return format!(
                "Missing {name}. Select the owning module in Module setup and install its Python dependencies."
            );
        }
    }
    detail.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bundles_only_fixed_creator_tool_sources() {
        assert_eq!(BUNDLED_TOOL_FILES.len(), 11);
        assert!(BUNDLED_TOOL_FILES.iter().all(|(path, contents)| {
            !path.contains("..")
                && !contents.is_empty()
                && (path.ends_with(".py") || path.ends_with("__init__.py"))
        }));
    }

    #[test]
    fn unpacks_tool_sources_without_a_repository_working_directory() {
        let root = std::env::temp_dir().join(format!("hcp-creator-tools-{}", std::process::id()));
        let runtime = ToolRuntime::new(root.clone()).unpack().unwrap();
        assert!(runtime
            .join("modules/image-editing/krita/scripts/batch_upscale.py")
            .is_file());
        assert!(runtime
            .join("modules/sports-analytics/pose-estimation/posture_screen.py")
            .is_file());
        assert!(runtime
            .join("modules/asset-pipeline/asset_pipeline/client.py")
            .is_file());
        assert!(runtime
            .join("plugins/blender-addon/operators/__init__.py")
            .is_file());
        assert!(runtime
            .join("modules/content-creation/blender/scripts/batch_render.py")
            .is_file());
        let _ = fs::remove_dir_all(root);
    }
}
