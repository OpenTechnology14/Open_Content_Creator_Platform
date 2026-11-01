//! Validated per-run workflow inputs. Never edits the committed workflow file.
use command_error::ErrorEnvelope;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashSet;

const MAX_SEED: u64 = 9_007_199_254_740_991;
const MAX_IMAGE_BYTES: usize = 10 * 1024 * 1024;

#[derive(Debug, Clone, Serialize)]
pub struct InputField {
    pub node_id: String,
    pub input: String,
    pub label: String,
    pub kind: String,
    pub value: Value,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InputEdit {
    pub node_id: String,
    pub input: String,
    pub value: Value,
}

fn parse(raw: &str) -> Result<Value, ErrorEnvelope> {
    if raw.len() > 2 * 1024 * 1024 {
        return Err(ErrorEnvelope::invalid_request("Workflow exceeds 2 MiB"));
    }
    let graph: Value = serde_json::from_str(raw)
        .map_err(|_| ErrorEnvelope::invalid_request("Invalid workflow JSON"))?;
    if !graph.as_object().is_some_and(|nodes| {
        nodes
            .iter()
            .any(|(id, n)| id != "_meta" && n.get("class_type").is_some())
    }) {
        return Err(ErrorEnvelope::invalid_request(
            "Workflow contains no executable nodes",
        ));
    }
    Ok(graph)
}

/// Only expose supported literal fields. Connections and model/node definitions are immutable.
pub fn fields(raw: &str) -> Result<Vec<InputField>, ErrorEnvelope> {
    let graph = parse(raw)?;
    let mut fields = Vec::new();
    for (id, node) in graph.as_object().unwrap() {
        let class = node["class_type"].as_str().unwrap_or("");
        let Some(inputs) = node["inputs"].as_object() else {
            continue;
        };
        for (input, value) in inputs {
            let kind = if matches!(class, "LoadImage" | "LoadImageMask")
                && input == "image"
                && value.is_string()
            {
                "image"
            } else if matches!(class, "CLIPTextEncode" | "CLIPTextEncodeSDXL")
                && matches!(input.as_str(), "text" | "text_g" | "text_l")
                && value.is_string()
            {
                "text"
            } else if matches!(input.as_str(), "seed" | "noise_seed") && value.is_u64() {
                "seed"
            } else {
                continue;
            };
            let used_as = |name: &str| {
                graph.as_object().unwrap().values().any(|consumer| {
                    consumer["inputs"][name]
                        .as_array()
                        .is_some_and(|link| link.first().and_then(Value::as_str) == Some(id))
                })
            };
            let title = match kind {
                "text" if used_as("positive") && !used_as("negative") => "Positive prompt",
                "text" if used_as("negative") && !used_as("positive") => "Negative prompt",
                "text" => "Prompt",
                "image" if class == "LoadImageMask" => "Mask image",
                "image" => "Image",
                _ => "Seed",
            };
            fields.push(InputField {
                node_id: id.clone(),
                input: input.clone(),
                label: format!("{} ({})", title, id),
                kind: kind.into(),
                value: value.clone(),
            });
        }
    }
    Ok(fields)
}

fn valid_image_name(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 512
        && !value.starts_with("PLACEHOLDER")
        && !value.contains(['\\', ':', '\0', '[', ']'])
        && !value.chars().any(char::is_control)
        && value
            .split('/')
            .all(|part| !part.is_empty() && part != "." && part != "..")
}

/// Validate all edits against the original graph before applying any of them.
pub fn prepare(raw: &str, edits: &[InputEdit]) -> Result<String, ErrorEnvelope> {
    let available = fields(raw)?;
    let mut graph = parse(raw)?;
    let mut changed = HashSet::new();
    for edit in edits {
        if !changed.insert((&edit.node_id, &edit.input)) {
            return Err(ErrorEnvelope::invalid_request("Duplicate workflow input"));
        }
        let field = available
            .iter()
            .find(|f| f.node_id == edit.node_id && f.input == edit.input)
            .ok_or_else(|| ErrorEnvelope::invalid_request("Unsupported workflow input"))?;
        let valid = match field.kind.as_str() {
            "text" => edit
                .value
                .as_str()
                .is_some_and(|v| v.len() <= 16_384 && !v.contains('\0')),
            "seed" => edit.value.as_u64().is_some_and(|v| v <= MAX_SEED),
            "image" => edit.value.as_str().is_some_and(valid_image_name),
            _ => false,
        };
        if !valid {
            return Err(ErrorEnvelope::invalid_request(format!(
                "Invalid {}",
                field.label
            )));
        }
        graph[&edit.node_id]["inputs"][&edit.input] = edit.value.clone();
    }
    for field in &available {
        if field.kind == "image"
            && !graph[&field.node_id]["inputs"][&field.input]
                .as_str()
                .is_some_and(valid_image_name)
        {
            return Err(ErrorEnvelope::invalid_request(format!(
                "Choose an image for {}",
                field.label
            )));
        }
    }
    serde_json::to_string(&graph).map_err(|_| ErrorEnvelope::internal("Cannot serialize workflow"))
}

/// Show only the destination origin; never send unrelated app credentials to the editor.
pub fn upload_target(url: &str) -> Result<String, ErrorEnvelope> {
    let parsed = reqwest::Url::parse(url)
        .map_err(|_| ErrorEnvelope::invalid_request("Invalid ComfyUI URL"))?;
    if !matches!(parsed.scheme(), "http" | "https") || parsed.host_str().is_none() {
        return Err(ErrorEnvelope::invalid_request(
            "ComfyUI requires an HTTP(S) URL",
        ));
    }
    Ok(parsed.origin().ascii_serialization())
}

/// Upload only operator-selected raster bytes to the configured ComfyUI input directory.
/// Fixed filenames + overwrite=false let ComfyUI choose a collision-free name.
pub async fn upload_image(url: &str, bytes: Vec<u8>) -> Result<String, ErrorEnvelope> {
    if bytes.is_empty() || bytes.len() > MAX_IMAGE_BYTES {
        return Err(ErrorEnvelope::invalid_request(
            "Choose an image up to 10 MiB",
        ));
    }
    let (extension, mime) = if bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        ("png", "image/png")
    } else if bytes.starts_with(b"\xff\xd8\xff") {
        ("jpg", "image/jpeg")
    } else if bytes.starts_with(b"RIFF") && bytes.get(8..12) == Some(b"WEBP") {
        ("webp", "image/webp")
    } else {
        return Err(ErrorEnvelope::invalid_request(
            "Choose a PNG, JPEG or WebP image",
        ));
    };
    let part = reqwest::multipart::Part::bytes(bytes)
        .file_name(format!("creator-input.{}", extension))
        .mime_str(mime)
        .map_err(|_| ErrorEnvelope::internal("Cannot prepare image upload"))?;
    let form = reqwest::multipart::Form::new()
        .part("image", part)
        .text("type", "input")
        .text("overwrite", "false");
    let response = reqwest::Client::new()
        .post(format!("{}/upload/image", url.trim_end_matches('/')))
        .multipart(form)
        .timeout(std::time::Duration::from_secs(30))
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                ErrorEnvelope::timeout("Image upload timed out")
            } else {
                ErrorEnvelope::dependency_unreachable("Image upload could not reach ComfyUI")
            }
        })?;
    if !response.status().is_success() {
        return Err(ErrorEnvelope::invalid_request(
            "ComfyUI rejected the image upload",
        ));
    }
    let value: Value = response
        .json()
        .await
        .map_err(|_| ErrorEnvelope::invalid_request("Invalid image upload response"))?;
    let name = value["name"].as_str().unwrap_or("");
    let folder = value["subfolder"].as_str().unwrap_or("");
    if value["type"] != "input"
        || name.contains('/')
        || !valid_image_name(name)
        || (!folder.is_empty() && !valid_image_name(folder))
    {
        return Err(ErrorEnvelope::invalid_request(
            "Invalid ComfyUI input image reference",
        ));
    }
    Ok(if folder.is_empty() {
        name.into()
    } else {
        format!("{}/{}", folder, name)
    })
}
