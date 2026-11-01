use command_error::ErrorCode;
use creator_extend_lib::{
    comfyui,
    workflow_inputs::{self, InputEdit},
};
use serde_json::{json, Value};
use wiremock::matchers::{method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn template() -> String {
    json!({
        "_meta": {"description":"preserve this"},
        "1": {"class_type":"LoadImage", "inputs":{"image":"PLACEHOLDER_IMAGE"}},
        "2": {"class_type":"CLIPTextEncode", "inputs":{"text":"original", "clip":["5",0]}},
        "3": {"class_type":"KSampler", "inputs":{"seed":42, "steps":20, "positive":["2",0]}},
        "4": {"class_type":"Other", "inputs":{"seed":["3",0], "text":["2",0]}},
        "5": {"class_type":"CheckpointLoaderSimple", "inputs":{"ckpt_name":"model.safetensors"}}
    })
    .to_string()
}
fn edit(id: &str, input: &str, value: Value) -> InputEdit {
    serde_json::from_value(json!({"node_id":id,"input":input,"value":value})).unwrap()
}

#[test]
fn exposes_literals_and_preserves_graph_links_models_and_template() {
    let raw = template();
    let fields = workflow_inputs::fields(&raw).unwrap();
    assert_eq!(fields.len(), 3);
    let result = workflow_inputs::prepare(
        &raw,
        &[
            edit("1", "image", json!("input/café.png")),
            edit("2", "text", json!("a blue cottage")),
            edit("3", "seed", json!(9007199254740991u64)),
        ],
    )
    .unwrap();
    let expected: Value = serde_json::from_str(&raw).unwrap();
    let actual: Value = serde_json::from_str(&result).unwrap();
    assert_eq!(
        actual["2"]["inputs"]["clip"],
        expected["2"]["inputs"]["clip"]
    );
    assert_eq!(actual["4"], expected["4"]);
    assert_eq!(actual["5"], expected["5"]);
    assert_eq!(actual["_meta"], expected["_meta"]);
    assert_eq!(actual["3"]["inputs"]["seed"], json!(9007199254740991u64));
    assert_eq!(expected["1"]["inputs"]["image"], "PLACEHOLDER_IMAGE");
}

#[test]
fn rejects_placeholder_unknown_duplicate_link_and_invalid_values() {
    assert!(workflow_inputs::prepare(&template(), &[]).is_err());
    for bad in [
        edit("5", "ckpt_name", json!("other")),
        edit("4", "seed", json!(2)),
        edit("3", "seed", json!(-1)),
        edit("3", "seed", json!(1.5)),
        edit("3", "seed", json!(9007199254740992u64)),
        edit("3", "seed", json!("4")),
        edit("1", "image", json!("../secret.png")),
        edit("1", "image", json!("C:\\secret.png")),
        edit("1", "image", json!("/secret.png")),
        edit("1", "image", json!("file.png [output]")),
        edit("2", "text", json!("a".repeat(16385))),
        edit("2", "text", json!("\0")),
    ] {
        let edits = if bad.node_id == "1" {
            vec![bad]
        } else {
            vec![edit("1", "image", json!("valid.png")), bad]
        };
        let err = workflow_inputs::prepare(&template(), &edits).unwrap_err();
        assert_eq!(err.code, ErrorCode::InvalidRequest);
    }
    assert!(workflow_inputs::prepare(
        &template(),
        &[
            edit("1", "image", json!("valid.png")),
            edit("2", "text", json!("a")),
            edit("2", "text", json!("b"))
        ]
    )
    .is_err());
    assert!(workflow_inputs::fields("{}").is_err());
    assert!(workflow_inputs::fields("not json").is_err());
}

#[test]
fn actual_upscale_template_accepts_image_and_keeps_nodes() {
    let raw = include_str!("../../../../modules/image-editing/workflows/upscale-4x-v1.json");
    let fields = workflow_inputs::fields(raw).unwrap();
    assert!(fields.iter().any(|f| f.kind == "text"));
    assert!(fields.iter().any(|f| f.kind == "seed"));
    assert!(fields
        .iter()
        .any(|f| f.label.starts_with("Positive prompt")));
    assert!(fields
        .iter()
        .any(|f| f.label.starts_with("Negative prompt")));
    let edits: Vec<_> = fields
        .iter()
        .filter(|f| f.kind == "image")
        .map(|f| edit(&f.node_id, &f.input, json!("uploaded.png")))
        .collect();
    let result = workflow_inputs::prepare(raw, &edits).unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&result)
            .unwrap()
            .as_object()
            .unwrap()
            .len(),
        serde_json::from_str::<Value>(raw)
            .unwrap()
            .as_object()
            .unwrap()
            .len()
    );
}

// Signature is sufficient for client contract tests; real image decoding belongs to ComfyUI.
fn png() -> Vec<u8> {
    b"\x89PNG\r\n\x1a\nfixture".to_vec()
}

#[tokio::test]
async fn uploads_without_overwrite_then_queues_the_returned_reference() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/upload/image"))
        .and(|request: &wiremock::Request| {
            let body = String::from_utf8_lossy(&request.body);
            body.contains("creator-input.png")
                && body.contains("name=\"overwrite\"\r\n\r\nfalse")
                && body.contains("name=\"type\"\r\n\r\ninput")
        })
        .respond_with(
            ResponseTemplate::new(200).set_body_json(
                json!({"name":"creator-input (1).png","subfolder":"","type":"input"}),
            ),
        )
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("POST"))
        .and(path("/prompt"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({"prompt_id":"run-1"})))
        .expect(1)
        .mount(&server)
        .await;
    let image = workflow_inputs::upload_image(&server.uri(), png())
        .await
        .unwrap();
    let prepared = workflow_inputs::prepare(
        &template(),
        &[
            edit("1", "image", json!(image)),
            edit("2", "text", json!("new prompt")),
            edit("3", "seed", json!(7)),
        ],
    )
    .unwrap();
    assert_eq!(
        comfyui::queue_prompt(&server.uri(), &prepared)
            .await
            .unwrap(),
        "run-1"
    );
    let requests = server.received_requests().await.unwrap();
    let payload: Value = requests[1].body_json().unwrap();
    assert_eq!(
        payload["prompt"]["1"]["inputs"]["image"],
        "creator-input (1).png"
    );
    assert_eq!(payload["prompt"]["2"]["inputs"]["text"], "new prompt");
    assert!(payload["prompt"].get("_meta").is_none());
}

#[tokio::test]
async fn invalid_upload_bytes_never_reach_server() {
    let server = MockServer::start().await;
    for data in [
        Vec::new(),
        vec![0; 10 * 1024 * 1024 + 1],
        b"<svg>bad</svg>".to_vec(),
    ] {
        assert!(workflow_inputs::upload_image(&server.uri(), data)
            .await
            .is_err());
    }
    assert!(server.received_requests().await.unwrap().is_empty());
}

#[tokio::test]
async fn rejected_or_malformed_response_does_not_create_an_input_reference() {
    for response in [
        ResponseTemplate::new(400),
        ResponseTemplate::new(200).set_body_string("not-json"),
        ResponseTemplate::new(200)
            .set_body_json(json!({"name":"../bad.png","subfolder":"","type":"input"})),
        ResponseTemplate::new(200)
            .set_body_json(json!({"name":"good.png","subfolder":"../../outside","type":"input"})),
        ResponseTemplate::new(200)
            .set_body_json(json!({"name":"good.png","subfolder":"","type":"output"})),
    ] {
        let server = MockServer::start().await;
        Mock::given(path("/upload/image"))
            .respond_with(response)
            .mount(&server)
            .await;
        assert!(workflow_inputs::upload_image(&server.uri(), png())
            .await
            .is_err());
    }
}

/// Explicit local acceptance; starts a synthetic image-copy job, requires no model weights.
#[tokio::test]
#[ignore = "requires an operator-selected local ComfyUI; see workflow-inputs guide"]
async fn live_upload_prepare_queue_and_read_output() {
    let url = std::env::var("HCP_COMFYUI_ACCEPTANCE_URL").expect("set the local acceptance URL");
    let reference =
        workflow_inputs::upload_image(&url, include_bytes!("input-fixture.png").to_vec())
            .await
            .unwrap();
    let raw = json!({
        "1":{"class_type":"LoadImage","inputs":{"image":"PLACEHOLDER_IMAGE"}},
        "2":{"class_type":"SaveImage","inputs":{"images":["1",0],"filename_prefix":"creator-input-acceptance"}}
    }).to_string();
    let prepared = workflow_inputs::prepare(&raw, &[edit("1", "image", json!(reference))]).unwrap();
    let id = comfyui::queue_prompt(&url, &prepared).await.unwrap();
    let mut success = false;
    let mut completed_outputs = Vec::new();
    for _ in 0..30 {
        let state = comfyui::get_prompt_status(&url, &id).await.unwrap();
        if state.completed {
            assert!(state.success, "{:?}", state.error);
            completed_outputs = state.outputs;
            success = true;
            break;
        }
        tokio::time::sleep(std::time::Duration::from_secs(1)).await;
    }
    assert!(success, "Synthetic job did not complete within 30 seconds");
    assert_eq!(completed_outputs.len(), 1);
    let preview = comfyui::get_output_preview(&url, &completed_outputs[0])
        .await
        .unwrap();
    assert_eq!(preview.media_type, "image/png");
    assert!(preview.data_url.starts_with("data:image/png;base64,"));
}

#[test]
fn bundled_workflows_load_without_repository_working_directory() {
    // Cargo runs this from the crate directory, not the repo root.
    let workflows = comfyui::list_committed_workflows().unwrap();
    assert!(workflows.iter().any(|w| w.name == "upscale-4x-v1"));
    assert!(!workflows.iter().any(|w| w.name == "00-starter"));
    for workflow in workflows {
        let raw = comfyui::load_workflow_json(&workflow.path).unwrap();
        workflow_inputs::fields(&raw).unwrap();
    }
    for invalid in [
        "/etc/passwd",
        "modules/image-editing/workflows/../../secret.json",
        "modules/image-editing/workflows/unknown.json",
    ] {
        assert!(comfyui::load_workflow_json(invalid).is_err());
    }
}

#[test]
fn upload_destination_excludes_credentials_and_query() {
    assert_eq!(
        workflow_inputs::upload_target("https://user:secret@example.test:8443/comfy?key=private")
            .unwrap(),
        "https://example.test:8443"
    );
    assert!(workflow_inputs::upload_target("file:///tmp/secret").is_err());
}
