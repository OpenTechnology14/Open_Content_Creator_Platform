//! ComfyUI API client for Creator Extend.
//!
//! Connects to the local ComfyUI instance for workflow management,
//! prompt queueing, and output retrieval.

use std::path::Path;
#[cfg(test)]
use std::path::PathBuf;

include!(concat!(env!("OUT_DIR"), "/workflow_catalog.rs"));

use base64::{engine::general_purpose::STANDARD as BASE64, Engine};
use command_error::ErrorEnvelope;
use serde::{Deserialize, Serialize};

const MAX_OUTPUT_BYTES: u64 = 8 * 1024 * 1024;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComfyStatus {
    pub connected: bool,
    pub queue_remaining: u32,
    pub gpu_name: Option<String>,
    pub vram_total_mb: Option<u64>,
    pub vram_free_mb: Option<u64>,
}

/// A bounded compatibility check for one of Creator Extend's bundled workflows.
///
/// This is deliberately an inventory check, rather than a prompt submission: it
/// reads ComfyUI's node schema and the selected model values before the operator
/// spends time configuring an input or queues a job. VRAM is reported from the
/// live server but is never converted into an unsupported blanket "enough"
/// assertion; the eventual prompt and output remain the acceptance proof.
#[derive(Debug, Clone, Serialize)]
pub struct WorkflowPreflight {
    pub connected: bool,
    pub compatible: bool,
    pub gpu_name: Option<String>,
    pub vram_total_mb: Option<u64>,
    pub vram_free_mb: Option<u64>,
    pub missing_nodes: Vec<String>,
    pub missing_models: Vec<String>,
    pub checked_models: Vec<String>,
    pub unchecked_models: Vec<String>,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowInfo {
    pub name: String,
    pub path: String,
    pub category: String, // "inpaint", "upscale", "stylize", "segment", "video"
    pub description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptStatus {
    pub completed: bool,
    pub success: bool,
    pub error: Option<String>,
    pub outputs: Vec<PromptOutputRef>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PromptOutputRef {
    pub node_id: String,
    pub filename: String,
    pub subfolder: String,
    pub folder_type: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct OutputPreview {
    pub data_url: String,
    pub media_type: String,
}

/// Check if ComfyUI is running and get system info.
pub async fn get_status(
    comfyui_url: &str,
) -> Result<ComfyStatus, Box<dyn std::error::Error + Send + Sync>> {
    let client = reqwest::Client::new();

    // Check /system_stats endpoint
    let response = client
        .get(format!("{}/system_stats", comfyui_url))
        .timeout(std::time::Duration::from_secs(3))
        .send()
        .await;

    match response {
        Ok(resp) if resp.status().is_success() => {
            let body: serde_json::Value = resp.json().await?;

            // Parse GPU info from system_stats
            let devices = body.get("devices").and_then(|d| d.as_array());
            let (gpu_name, vram_total, vram_free) = if let Some(devs) = devices {
                if let Some(dev) = devs.first() {
                    (
                        dev.get("name").and_then(|n| n.as_str()).map(String::from),
                        dev.get("vram_total")
                            .and_then(|v| v.as_u64())
                            .map(|v| v / 1_048_576),
                        dev.get("vram_free")
                            .and_then(|v| v.as_u64())
                            .map(|v| v / 1_048_576),
                    )
                } else {
                    (None, None, None)
                }
            } else {
                (None, None, None)
            };

            // Check queue
            let queue_resp = client.get(format!("{}/queue", comfyui_url))
                .timeout(std::time::Duration::from_secs(3)).send().await?;
            let queue: serde_json::Value = queue_resp.json().await?;
            let pending = queue
                .get("queue_pending")
                .and_then(|q| q.as_array())
                .map(|a| a.len() as u32)
                .unwrap_or(0);

            Ok(ComfyStatus {
                connected: true,
                queue_remaining: pending,
                gpu_name,
                vram_total_mb: vram_total,
                vram_free_mb: vram_free,
            })
        }
        _ => Ok(ComfyStatus {
            connected: false,
            queue_remaining: 0,
            gpu_name: None,
            vram_total_mb: None,
            vram_free_mb: None,
        }),
    }
}

/// Check whether the exact node classes and fixed model choices in a bundled
/// graph are currently exposed by the configured ComfyUI endpoint.
pub async fn preflight_workflow(
    comfyui_url: &str,
    workflow_json: &str,
) -> Result<WorkflowPreflight, ErrorEnvelope> {
    let workflow: serde_json::Value = serde_json::from_str(workflow_json)
        .map_err(|_| ErrorEnvelope::internal("Invalid bundled workflow JSON"))?;
    let status = get_status(comfyui_url)
        .await
        .map_err(|_| ErrorEnvelope::dependency_unreachable("ComfyUI readiness check failed"))?;
    if !status.connected {
        return Ok(WorkflowPreflight {
            connected: false,
            compatible: false,
            gpu_name: None,
            vram_total_mb: None,
            vram_free_mb: None,
            missing_nodes: Vec::new(),
            missing_models: Vec::new(),
            checked_models: Vec::new(),
            unchecked_models: Vec::new(),
            summary: "Start ComfyUI and verify the saved local endpoint".into(),
        });
    }

    let client = reqwest::Client::new();
    let object_info = client
        .get(format!("{}/object_info", comfyui_url))
        .timeout(std::time::Duration::from_secs(8))
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                ErrorEnvelope::timeout("ComfyUI did not return its node inventory")
            } else {
                ErrorEnvelope::dependency_unreachable("ComfyUI node inventory is unavailable")
            }
        })?;
    if !object_info.status().is_success() {
        return Err(ErrorEnvelope::dependency_unreachable(format!(
            "ComfyUI returned {} for /object_info",
            object_info.status()
        )));
    }
    let inventory: serde_json::Value = object_info
        .json()
        .await
        .map_err(|_| ErrorEnvelope::internal("ComfyUI returned an invalid node inventory"))?;

    Ok(evaluate_workflow_preflight(&workflow, &inventory, status))
}

/// Reject a queue request that has not passed the same bounded inventory
/// preflight exposed in the UI. This closes the race between a visible
/// preflight and a later queue request after node/model changes.
pub async fn require_compatible_workflow(
    comfyui_url: &str,
    workflow_json: &str,
) -> Result<(), ErrorEnvelope> {
    let preflight = preflight_workflow(comfyui_url, workflow_json).await?;
    if preflight.compatible {
        Ok(())
    } else {
        Err(ErrorEnvelope::invalid_request(format!(
            "ComfyUI workflow preflight blocked this queue request: {}",
            preflight.summary
        )))
    }
}

fn evaluate_workflow_preflight(
    workflow: &serde_json::Value,
    inventory: &serde_json::Value,
    status: ComfyStatus,
) -> WorkflowPreflight {
    let mut missing_nodes = Vec::new();
    let mut missing_models = Vec::new();
    let mut checked_models = Vec::new();
    let mut unchecked_models = Vec::new();

    let Some(nodes) = workflow.as_object() else {
        return WorkflowPreflight {
            connected: status.connected,
            compatible: false,
            gpu_name: status.gpu_name,
            vram_total_mb: status.vram_total_mb,
            vram_free_mb: status.vram_free_mb,
            missing_nodes,
            missing_models,
            checked_models,
            unchecked_models,
            summary: "The bundled workflow is not a node graph".into(),
        };
    };

    for (id, node) in nodes {
        if id == "_meta" {
            continue;
        }
        let Some(class_type) = node.get("class_type").and_then(|value| value.as_str()) else {
            continue;
        };
        let Some(node_info) = inventory.get(class_type) else {
            missing_nodes.push(class_type.into());
            continue;
        };
        let Some(inputs) = node.get("inputs").and_then(|value| value.as_object()) else {
            continue;
        };
        for (input_name, input_value) in inputs {
            let Some(model_name) = input_value.as_str() else {
                continue;
            };
            if !is_model_input(input_name) {
                continue;
            }
            let Some(choices) = model_choices(node_info, input_name) else {
                unchecked_models.push(model_name.into());
                continue;
            };
            if choices.iter().any(|choice| *choice == model_name) {
                checked_models.push(model_name.into());
            } else {
                missing_models.push(model_name.into());
            }
        }
    }

    missing_nodes.sort();
    missing_nodes.dedup();
    missing_models.sort();
    missing_models.dedup();
    checked_models.sort();
    checked_models.dedup();
    unchecked_models.sort();
    unchecked_models.dedup();

    let compatible = status.connected
        && missing_nodes.is_empty()
        && missing_models.is_empty()
        && unchecked_models.is_empty();
    let summary = if compatible {
        if checked_models.is_empty() {
            "Required node classes are available. This graph has no fixed model choice to inventory; VRAM and output quality still need a real run.".into()
        } else {
            "Required node classes and fixed model choices are available. VRAM is reported below; output quality still needs a real run.".into()
        }
    } else if !missing_nodes.is_empty() {
        format!("Missing node classes: {}", missing_nodes.join(", "))
    } else if !missing_models.is_empty() {
        format!("Missing configured models: {}", missing_models.join(", "))
    } else {
        format!(
            "ComfyUI did not expose selectable model inventory for: {}",
            unchecked_models.join(", ")
        )
    };

    WorkflowPreflight {
        connected: status.connected,
        compatible,
        gpu_name: status.gpu_name,
        vram_total_mb: status.vram_total_mb,
        vram_free_mb: status.vram_free_mb,
        missing_nodes,
        missing_models,
        checked_models,
        unchecked_models,
        summary,
    }
}

/// ComfyUI represents selectable model inputs as `[ ["model-a", ...], ... ]`.
/// A non-list schema (text, number, connection, or a custom node's opaque
/// value) is intentionally not treated as a missing model.
fn model_choices<'a>(node_info: &'a serde_json::Value, input_name: &str) -> Option<Vec<&'a str>> {
    node_info
        .get("input")?
        .get("required")?
        .get(input_name)?
        .as_array()?
        .first()?
        .as_array()?
        .iter()
        .filter_map(serde_json::Value::as_str)
        .collect::<Vec<_>>()
        .into()
}

fn is_model_input(input_name: &str) -> bool {
    matches!(
        input_name,
        "ckpt_name"
            | "unet_name"
            | "clip_name"
            | "clip_name1"
            | "clip_name2"
            | "vae_name"
            | "lora_name"
            | "model_name"
            | "upscale_model"
    )
}

/// List workflow JSON files this repo actually ships, not whatever a
/// ComfyUI instance's own userdata happens to have saved — those are two
/// unrelated sets (nothing ever syncs them), and this app's curated,
/// GPU-verified workflows (P-028/P-043) are the point.
pub fn list_committed_workflows() -> Result<Vec<WorkflowInfo>, ErrorEnvelope> {
    let mut workflows = Vec::new();
    for (path, raw) in BUNDLED_WORKFLOWS {
        let value: serde_json::Value = serde_json::from_str(raw)
            .map_err(|_| ErrorEnvelope::internal("Invalid bundled workflow JSON"))?;
        // Empty starter scaffolds are not runnable workflows.
        if !value.as_object().is_some_and(|nodes| {
            nodes
                .iter()
                .any(|(id, n)| id != "_meta" && n.get("class_type").is_some())
        }) {
            continue;
        }
        let name = Path::new(path)
            .file_stem()
            .unwrap()
            .to_string_lossy()
            .to_string();
        workflows.push(WorkflowInfo {
            category: categorize_workflow(&name),
            name,
            path: (*path).into(),
            description: value["_meta"]["description"].as_str().map(String::from),
        });
    }
    workflows.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(workflows)
}

/// Testable core: takes the workflow directories as a parameter instead of
/// the hardcoded, repo-root-relative `WORKFLOW_DIRS` constant, so tests can
/// point it at a temp directory instead of needing the real repo layout at
/// a predictable CWD (which `cargo test` does not reliably provide, and
/// which parallel test threads can't safely override process-wide via
/// `std::env::set_current_dir`).
#[cfg(test)]
fn list_workflows_in(dirs: &[&str]) -> Result<Vec<WorkflowInfo>, ErrorEnvelope> {
    let mut workflows = Vec::new();

    for dir in dirs {
        let dir_path = Path::new(dir);
        if !dir_path.is_dir() {
            continue; // a missing dir contributes no workflows, not an error
        }

        let entries = std::fs::read_dir(dir_path)
            .map_err(|e| ErrorEnvelope::internal(format!("reading {}: {}", dir, e)))?;

        for entry in entries {
            let entry = entry.map_err(|e| ErrorEnvelope::internal(e.to_string()))?;
            let file_path = entry.path();
            if file_path.extension().and_then(|e| e.to_str()) != Some("json") {
                continue;
            }
            let file_name = file_path
                .file_name()
                .and_then(|f| f.to_str())
                .unwrap_or_default()
                .to_string();
            let name = file_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string();
            let category = categorize_workflow(&name);

            workflows.push(WorkflowInfo {
                name,
                path: format!("{}/{}", dir, file_name),
                category,
                description: None,
            });
        }
    }

    workflows.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(workflows)
}

/// Load an exact bundled workflow ID. Never reads a user-supplied filesystem path.
pub fn load_workflow_json(workflow_path: &str) -> Result<String, ErrorEnvelope> {
    BUNDLED_WORKFLOWS
        .iter()
        .find(|(key, _)| *key == workflow_path)
        .map(|(_, raw)| (*raw).to_owned())
        .ok_or_else(|| ErrorEnvelope::path_escape("Unknown bundled workflow ID"))
}

/// Testable core — see `list_workflows_in`'s doc comment for why this
/// takes `dirs` as a parameter instead of using `WORKFLOW_DIRS` directly.
#[cfg(test)]
fn load_workflow_json_in(dirs: &[&str], workflow_path: &str) -> Result<String, ErrorEnvelope> {
    let requested = Path::new(workflow_path);

    let matched_base: Option<&Path> = dirs
        .iter()
        .map(Path::new)
        .find(|base| requested.starts_with(base));

    let Some(base) = matched_base else {
        return Err(ErrorEnvelope::path_escape(format!(
            "{} is not under a known workflow directory",
            workflow_path
        )));
    };

    let canonical_base: PathBuf = base
        .canonicalize()
        .map_err(|e| ErrorEnvelope::internal(format!("resolving {}: {}", base.display(), e)))?;

    let canonical_target: PathBuf = requested
        .canonicalize()
        .map_err(|_| ErrorEnvelope::not_found(format!("{} does not exist", workflow_path)))?;

    if !canonical_target.starts_with(&canonical_base) {
        return Err(ErrorEnvelope::path_escape(format!(
            "{} resolves outside its workflow directory",
            workflow_path
        )));
    }

    std::fs::read_to_string(&canonical_target)
        .map_err(|e| ErrorEnvelope::internal(format!("reading {}: {}", workflow_path, e)))
}

/// Strips this repo's own `_meta` documentation block (title/description/
/// required_models/required_nodes — added by P-028/P-043 to every committed
/// workflow file) before a graph reaches ComfyUI. Found via real hardware
/// evidence for this PR: ComfyUI's `/prompt` validates every top-level key
/// as a node needing a `class_type`, so sending `_meta` verbatim gets every
/// single committed workflow rejected with `missing_node_type` — not a
/// hypothetical, reproduced against the real installed ComfyUI on
/// `upscale-4x-v1.json`.
fn strip_workflow_meta(mut prompt: serde_json::Value) -> serde_json::Value {
    if let Some(obj) = prompt.as_object_mut() {
        obj.remove("_meta");
    }
    prompt
}

/// Queue a workflow prompt on ComfyUI. `workflow_json` is the file this
/// repo commits (real ComfyUI nodes plus a `_meta` doc block this repo adds
/// — see `strip_workflow_meta`) — this strips `_meta` and wraps the rest in
/// the `{"prompt": ..., "client_id": ...}` envelope ComfyUI's `/prompt`
/// endpoint expects.
pub async fn queue_prompt(comfyui_url: &str, workflow_json: &str) -> Result<String, ErrorEnvelope> {
    let client = reqwest::Client::new();
    let prompt: serde_json::Value = serde_json::from_str(workflow_json)
        .map_err(|e| ErrorEnvelope::invalid_request(format!("malformed workflow JSON: {}", e)))?;
    let prompt = strip_workflow_meta(prompt);

    let payload = serde_json::json!({
        "prompt": prompt,
        "client_id": "creator-extend",
    });

    let response = client
        .post(format!("{}/prompt", comfyui_url))
        .json(&payload)
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                ErrorEnvelope::timeout(format!("queueing prompt: {}", e))
            } else {
                ErrorEnvelope::dependency_unreachable(format!("queueing prompt: {}", e))
            }
        })?;

    if !response.status().is_success() {
        let error = response.text().await.unwrap_or_default();
        return Err(ErrorEnvelope::invalid_request(format!(
            "ComfyUI rejected prompt: {}",
            error
        )));
    }

    let body: serde_json::Value = response
        .json()
        .await
        .map_err(|e| ErrorEnvelope::internal(format!("parsing queue response: {}", e)))?;
    let prompt_id = body
        .get("prompt_id")
        .and_then(|p| p.as_str())
        .unwrap_or("unknown")
        .to_string();

    Ok(prompt_id)
}

/// Poll a previously-queued prompt's terminal state via ComfyUI's real
/// `GET /history/{prompt_id}` (confirmed against the actual server source,
/// modules/realtime-ai/comfyui/app/server.py / execution.py's
/// `ExecutionStatus`). An empty/missing entry means still queued or
/// running — not an error, `completed: false`.
pub async fn get_prompt_status(
    comfyui_url: &str,
    prompt_id: &str,
) -> Result<PromptStatus, ErrorEnvelope> {
    let client = reqwest::Client::new();

    let response = client
        .get(format!("{}/history/{}", comfyui_url, prompt_id))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                ErrorEnvelope::timeout(format!("checking status of {}: {}", prompt_id, e))
            } else {
                ErrorEnvelope::dependency_unreachable(format!(
                    "checking status of {}: {}",
                    prompt_id, e
                ))
            }
        })?;

    if !response.status().is_success() {
        return Err(ErrorEnvelope::dependency_unreachable(format!(
            "ComfyUI returned {} for /history/{}",
            response.status(),
            prompt_id
        )));
    }

    let body: serde_json::Value = response
        .json()
        .await
        .map_err(|e| ErrorEnvelope::internal(format!("parsing history response: {}", e)))?;

    let Some(entry) = body.get(prompt_id) else {
        // Not in history yet — ComfyUI moves a prompt into /history only
        // once it leaves the queue, so absence means still pending/running.
        return Ok(PromptStatus {
            completed: false,
            success: false,
            error: None,
            outputs: Vec::new(),
        });
    };

    let status = entry.get("status");
    let completed = status
        .and_then(|s| s.get("completed"))
        .and_then(|c| c.as_bool())
        .unwrap_or(false);
    let status_str = status
        .and_then(|s| s.get("status_str"))
        .and_then(|s| s.as_str())
        .unwrap_or("");
    let is_error = status_str == "error";

    let error = if is_error {
        status
            .and_then(|s| s.get("messages"))
            .map(|m| m.to_string())
    } else {
        None
    };

    Ok(PromptStatus {
        completed,
        success: completed && !is_error,
        error,
        outputs: prompt_outputs(entry),
    })
}

fn prompt_outputs(entry: &serde_json::Value) -> Vec<PromptOutputRef> {
    let mut result = Vec::new();
    let Some(nodes) = entry.get("outputs").and_then(|value| value.as_object()) else {
        return result;
    };
    for (node_id, node) in nodes {
        for bucket in ["images", "gifs"] {
            let Some(items) = node.get(bucket).and_then(|value| value.as_array()) else {
                continue;
            };
            for item in items {
                let Some(filename) = item.get("filename").and_then(|value| value.as_str()) else {
                    continue;
                };
                result.push(PromptOutputRef {
                    node_id: node_id.clone(),
                    filename: filename.into(),
                    subfolder: item
                        .get("subfolder")
                        .and_then(|value| value.as_str())
                        .unwrap_or("")
                        .into(),
                    folder_type: item
                        .get("type")
                        .and_then(|value| value.as_str())
                        .unwrap_or("output")
                        .into(),
                });
            }
        }
    }
    result.truncate(20);
    result
}

fn valid_output_ref(output: &PromptOutputRef) -> bool {
    !output.node_id.is_empty()
        && output.node_id.len() <= 100
        && output
            .node_id
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || ".-_".contains(character))
        && !output.filename.is_empty()
        && output.filename.len() <= 255
        && !output.filename.contains(['/', '\\', '\0'])
        && output.filename != "."
        && output.filename != ".."
        && output.subfolder.len() <= 512
        && !output.subfolder.contains(['\\', '\0'])
        && !output.subfolder.starts_with('/')
        && output
            .subfolder
            .split('/')
            .all(|part| !matches!(part, "." | ".."))
        && matches!(output.folder_type.as_str(), "output" | "temp")
}

fn preview_media(bytes: &[u8]) -> Option<&'static str> {
    if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        Some("image/png")
    } else if bytes.starts_with(b"\xff\xd8\xff") {
        Some("image/jpeg")
    } else if bytes.starts_with(b"RIFF") && bytes.get(8..12) == Some(b"WEBP") {
        Some("image/webp")
    } else if bytes.starts_with(b"GIF87a") || bytes.starts_with(b"GIF89a") {
        Some("image/gif")
    } else if bytes.get(4..8) == Some(b"ftyp") {
        Some("video/mp4")
    } else if bytes.starts_with(b"\x1a\x45\xdf\xa3") {
        Some("video/webm")
    } else {
        None
    }
}

/// Retrieve one output reference returned by `/history/{prompt_id}`. Query values are encoded by
/// reqwest, references are path-checked, and response bytes are bounded and sniffed before they
/// become a frontend data URL.
pub async fn get_output_preview(
    comfyui_url: &str,
    output: &PromptOutputRef,
) -> Result<OutputPreview, ErrorEnvelope> {
    if !valid_output_ref(output) {
        return Err(ErrorEnvelope::invalid_request(
            "Invalid ComfyUI output reference",
        ));
    }
    let mut response = reqwest::Client::new()
        .get(format!("{}/view", comfyui_url.trim_end_matches('/')))
        .query(&[
            ("filename", output.filename.as_str()),
            ("subfolder", output.subfolder.as_str()),
            ("type", output.folder_type.as_str()),
        ])
        .timeout(std::time::Duration::from_secs(15))
        .send()
        .await
        .map_err(|error| {
            if error.is_timeout() {
                ErrorEnvelope::timeout("ComfyUI output preview timed out")
            } else {
                ErrorEnvelope::dependency_unreachable("Could not reach the ComfyUI output server")
            }
        })?;
    if !response.status().is_success() {
        return Err(ErrorEnvelope::not_found(
            "ComfyUI output is no longer available",
        ));
    }
    if response
        .content_length()
        .is_some_and(|size| size > MAX_OUTPUT_BYTES)
    {
        return Err(ErrorEnvelope::invalid_request(
            "ComfyUI output exceeds 8 MiB",
        ));
    }
    let mut bytes = Vec::new();
    while let Some(chunk) = response
        .chunk()
        .await
        .map_err(|_| ErrorEnvelope::dependency_unreachable("Could not read ComfyUI output"))?
    {
        if bytes.len().saturating_add(chunk.len()) > MAX_OUTPUT_BYTES as usize {
            return Err(ErrorEnvelope::invalid_request(
                "ComfyUI output exceeds 8 MiB",
            ));
        }
        bytes.extend_from_slice(&chunk);
    }
    if bytes.is_empty() {
        return Err(ErrorEnvelope::invalid_request("ComfyUI output is empty"));
    }
    let media_type = preview_media(&bytes)
        .ok_or_else(|| ErrorEnvelope::invalid_request("Unsupported ComfyUI preview format"))?;
    Ok(OutputPreview {
        data_url: format!("data:{media_type};base64,{}", BASE64.encode(bytes)),
        media_type: media_type.into(),
    })
}

/// Categorize a workflow by name pattern.
fn categorize_workflow(name: &str) -> String {
    let lower = name.to_lowercase();
    if lower.contains("inpaint") || lower.contains("outpaint") {
        "inpaint".to_string()
    } else if lower.contains("upscale") {
        "upscale".to_string()
    } else if lower.contains("style") || lower.contains("ipadapter") {
        "stylize".to_string()
    } else if lower.contains("segment") || lower.contains("rmbg") || lower.contains("sam") {
        "segment".to_string()
    } else if lower.contains("video") || lower.contains("animate") {
        "video".to_string()
    } else if lower.contains("lcm") || lower.contains("realtime") {
        "realtime".to_string()
    } else {
        "general".to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use command_error::ErrorCode;
    use std::sync::atomic::{AtomicU32, Ordering};

    static COUNTER: AtomicU32 = AtomicU32::new(0);

    /// A fresh temp directory per test, so parallel test threads never
    /// collide — avoids both a new `tempfile` dependency and the hazard of
    /// mutating process-wide CWD across concurrently-running test threads.
    fn temp_dir() -> PathBuf {
        let n = COUNTER.fetch_add(1, Ordering::SeqCst);
        let dir = std::env::temp_dir().join(format!(
            "hcp-comfyui-test-{}-{}-{}",
            std::process::id(),
            n,
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn list_workflows_in_finds_json_files_and_skips_others() {
        let base = temp_dir();
        std::fs::write(base.join("real-workflow.json"), "{}").unwrap();
        std::fs::write(base.join("notes.txt"), "not a workflow").unwrap();

        let dir_str = base.to_str().unwrap().to_string();
        let workflows = list_workflows_in(&[&dir_str]).unwrap();

        assert_eq!(workflows.len(), 1);
        assert_eq!(workflows[0].name, "real-workflow");
        assert!(workflows[0].path.ends_with("real-workflow.json"));

        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn list_workflows_in_tolerates_a_missing_directory() {
        let missing = "/definitely/does/not/exist/anywhere";
        let workflows = list_workflows_in(&[missing]).unwrap();
        assert!(workflows.is_empty());
    }

    #[test]
    fn load_workflow_json_in_reads_a_real_file() {
        let base = temp_dir();
        std::fs::write(base.join("wf.json"), r#"{"1": {"class_type": "X"}}"#).unwrap();

        let dir_str = base.to_str().unwrap().to_string();
        let workflow_path = format!("{}/wf.json", dir_str);
        let json = load_workflow_json_in(&[&dir_str], &workflow_path).unwrap();

        assert_eq!(json, r#"{"1": {"class_type": "X"}}"#);
        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn load_workflow_json_in_rejects_a_path_outside_the_known_dirs() {
        let base = temp_dir();
        std::fs::write(base.join("wf.json"), "{}").unwrap();
        let dir_str = base.to_str().unwrap().to_string();

        // Not under any known dir at all.
        let err = load_workflow_json_in(&[&dir_str], "/etc/passwd").unwrap_err();
        assert_eq!(err.code, ErrorCode::PathEscape);

        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn load_workflow_json_in_rejects_traversal_that_escapes_via_dotdot() {
        // Regression for the real class of bug a naive string-prefix check
        // (without canonicalization) would miss: `starts_with` on path
        // *components* considers "base/../../../etc/passwd" to start with
        // "base", even though it resolves somewhere else entirely.
        let base = temp_dir();
        let sibling_secret = base
            .parent()
            .unwrap()
            .join(format!("hcp-comfyui-test-secret-{}", std::process::id()));
        std::fs::write(&sibling_secret, "top secret").unwrap();

        let dir_str = base.to_str().unwrap().to_string();
        let escaping_path = format!(
            "{}/../{}",
            dir_str,
            sibling_secret.file_name().unwrap().to_str().unwrap()
        );

        let err = load_workflow_json_in(&[&dir_str], &escaping_path).unwrap_err();
        assert_eq!(err.code, ErrorCode::PathEscape);

        std::fs::remove_dir_all(&base).ok();
        std::fs::remove_file(&sibling_secret).ok();
    }

    #[test]
    fn load_workflow_json_in_reports_not_found_for_a_missing_file() {
        let base = temp_dir();
        let dir_str = base.to_str().unwrap().to_string();
        let missing_path = format!("{}/nope.json", dir_str);

        let err = load_workflow_json_in(&[&dir_str], &missing_path).unwrap_err();
        assert_eq!(err.code, ErrorCode::NotFound);

        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn strip_workflow_meta_removes_meta_but_keeps_every_node() {
        let prompt = serde_json::json!({
            "_meta": {"title": "Test", "required_models": ["x"]},
            "1": {"class_type": "LoadImage", "inputs": {}},
            "2": {"class_type": "SaveImage", "inputs": {}},
        });
        let stripped = strip_workflow_meta(prompt);
        let obj = stripped.as_object().unwrap();
        assert!(!obj.contains_key("_meta"));
        assert_eq!(obj.len(), 2);
        assert!(obj.contains_key("1"));
        assert!(obj.contains_key("2"));
    }

    #[test]
    fn strip_workflow_meta_tolerates_a_workflow_with_no_meta_block() {
        let prompt = serde_json::json!({"1": {"class_type": "LoadImage", "inputs": {}}});
        let stripped = strip_workflow_meta(prompt.clone());
        assert_eq!(stripped, prompt);
    }

    #[test]
    fn categorize_workflow_matches_known_patterns() {
        assert_eq!(categorize_workflow("inpaint-fill-v1"), "inpaint");
        assert_eq!(categorize_workflow("upscale-4x-v1"), "upscale");
        assert_eq!(categorize_workflow("00-starter"), "general");
    }
}
