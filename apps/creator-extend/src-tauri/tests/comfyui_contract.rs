//! Contract tests for `comfyui.rs`'s HTTP client against a fake ComfyUI
//! server (P-053, WP-5 ComfyUI half). No live ComfyUI needed — this is the
//! "fakes pass in CI" half of the proposal's own WP-5 exit bar; hardware
//! evidence against the real, already-installed ComfyUI is separate and
//! recorded in docs/PROPOSALS.md, not here.
//!
//! `wiremock`, a `[dev-dependencies]`-only crate — first Rust test file in
//! either app (zero existing precedent to extend), matched to what
//! `comfyui.rs` actually sends by reading `modules/realtime-ai/comfyui/
//! app/server.py`'s and `execution.py`'s real endpoint/response shapes
//! directly, not assumed.

use command_error::ErrorCode;
use creator_extend_lib::comfyui;
use wiremock::matchers::{method, path, query_param};
use wiremock::{Mock, MockServer, ResponseTemplate};

// ── get_status ────────────────────────────────────────────────────────

#[tokio::test]
async fn get_status_bounds_an_unresponsive_queue() {
    let server = MockServer::start().await;
    Mock::given(method("GET")).and(path("/system_stats"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({"devices": []})))
        .mount(&server).await;
    Mock::given(method("GET")).and(path("/queue"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({"queue_pending": []}))
            .set_delay(std::time::Duration::from_secs(10)))
        .mount(&server).await;
    let outcome = tokio::time::timeout(std::time::Duration::from_secs(5), comfyui::get_status(&server.uri())).await;
    assert!(outcome.is_ok(), "ComfyUI queue status exceeded its request deadline");
    assert!(outcome.unwrap().is_err());
}

#[tokio::test]
async fn get_status_reports_connected_with_real_gpu_fields() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/system_stats"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "system": {},
            "devices": [{
                "name": "Apple M1 Pro",
                "vram_total": 17_179_869_184u64,
                "vram_free": 8_589_934_592u64,
            }],
        })))
        .mount(&server)
        .await;

    Mock::given(method("GET"))
        .and(path("/queue"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "queue_running": [],
            "queue_pending": [["id1"], ["id2"]],
        })))
        .mount(&server)
        .await;

    let status = comfyui::get_status(&server.uri()).await.unwrap();
    assert!(status.connected);
    assert_eq!(status.gpu_name.as_deref(), Some("Apple M1 Pro"));
    assert_eq!(status.vram_total_mb, Some(16384));
    assert_eq!(status.vram_free_mb, Some(8192));
    assert_eq!(status.queue_remaining, 2);
}

#[tokio::test]
async fn get_status_reports_disconnected_when_comfyui_is_unreachable() {
    // No mock server at all — connection refused, not a 4xx/5xx.
    let status = comfyui::get_status("http://127.0.0.1:1").await.unwrap();
    assert!(!status.connected);
}

// ── preflight_workflow ───────────────────────────────────────────────

async fn mock_preflight_status(server: &MockServer) {
    Mock::given(method("GET"))
        .and(path("/system_stats"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "devices": [{
                "name": "Test GPU",
                "vram_total": 8_589_934_592u64,
                "vram_free": 4_294_967_296u64,
            }],
        })))
        .mount(server)
        .await;
    Mock::given(method("GET"))
        .and(path("/queue"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "queue_pending": [],
        })))
        .mount(server)
        .await;
}

#[tokio::test]
async fn preflight_accepts_available_nodes_and_fixed_model_choices() {
    let server = MockServer::start().await;
    mock_preflight_status(&server).await;
    Mock::given(method("GET"))
        .and(path("/object_info"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "CheckpointLoaderSimple": {
                "input": {"required": {"ckpt_name": [["base.safetensors"]]}}
            },
            "CLIPTextEncode": {
                "input": {"required": {"text": ["STRING", {"multiline": true}]}}
            },
        })))
        .mount(&server)
        .await;

    let result = comfyui::preflight_workflow(
        &server.uri(),
        r#"{
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "base.safetensors"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "a prompt"}}
    }"#,
    )
    .await
    .unwrap();

    assert!(result.connected);
    assert!(result.compatible);
    assert_eq!(result.checked_models, vec!["base.safetensors"]);
    assert!(result.missing_nodes.is_empty());
    assert!(result.missing_models.is_empty());
    assert_eq!(result.vram_free_mb, Some(4096));
}

#[tokio::test]
async fn preflight_reports_missing_node_and_model_without_queueing() {
    let server = MockServer::start().await;
    mock_preflight_status(&server).await;
    Mock::given(method("GET"))
        .and(path("/object_info"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "CheckpointLoaderSimple": {
                "input": {"required": {"ckpt_name": [["other.safetensors"]]}}
            }
        })))
        .mount(&server)
        .await;

    let result = comfyui::preflight_workflow(
        &server.uri(),
        r#"{
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "base.safetensors"}},
        "2": {"class_type": "MissingCustomNode", "inputs": {}}
    }"#,
    )
    .await
    .unwrap();

    assert!(!result.compatible);
    assert_eq!(result.missing_nodes, vec!["MissingCustomNode"]);
    assert_eq!(result.missing_models, vec!["base.safetensors"]);
    assert!(result.summary.contains("Missing node classes"));
}

#[tokio::test]
async fn preflight_keeps_a_disconnected_endpoint_out_of_the_queue_path() {
    let result = comfyui::preflight_workflow(
        "http://127.0.0.1:1",
        r#"{"1": {"class_type": "LoadImage", "inputs": {}}}"#,
    )
    .await
    .unwrap();

    assert!(!result.connected);
    assert!(!result.compatible);
    assert!(result.summary.contains("Start ComfyUI"));
}

#[tokio::test]
async fn queue_guard_rejects_a_workflow_when_preflight_finds_a_missing_node() {
    let server = MockServer::start().await;
    mock_preflight_status(&server).await;
    Mock::given(method("GET"))
        .and(path("/object_info"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({})))
        .mount(&server)
        .await;

    let error = comfyui::require_compatible_workflow(
        &server.uri(),
        r#"{"1": {"class_type": "MissingCustomNode", "inputs": {}}}"#,
    )
    .await
    .unwrap_err();

    assert_eq!(error.code, ErrorCode::InvalidRequest);
    assert!(error.message.contains("preflight blocked"));
}

// ── queue_prompt ─────────────────────────────────────────────────────

#[tokio::test]
async fn queue_prompt_returns_the_real_prompt_id_on_success() {
    let server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/prompt"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "prompt_id": "abc-123",
            "number": 1,
            "node_errors": {},
        })))
        .mount(&server)
        .await;

    let prompt_id = comfyui::queue_prompt(&server.uri(), r#"{"1": {"class_type": "X"}}"#)
        .await
        .unwrap();
    assert_eq!(prompt_id, "abc-123");
}

#[tokio::test]
async fn queue_prompt_rejects_malformed_workflow_json_before_any_request() {
    let server = MockServer::start().await;
    // Deliberately no mock registered — if this reaches the network at all,
    // wiremock's own unmatched-request behavior would surface it.

    let err = comfyui::queue_prompt(&server.uri(), "not json")
        .await
        .unwrap_err();
    assert_eq!(err.code, ErrorCode::InvalidRequest);
}

#[tokio::test]
async fn queue_prompt_surfaces_a_comfyui_rejection_as_invalid_request() {
    let server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/prompt"))
        .respond_with(ResponseTemplate::new(400).set_body_string("node_errors: bad graph"))
        .mount(&server)
        .await;

    let err = comfyui::queue_prompt(&server.uri(), r#"{"1": {}}"#)
        .await
        .unwrap_err();
    assert_eq!(err.code, ErrorCode::InvalidRequest);
    assert!(err.message.contains("bad graph"));
}

// ── get_prompt_status ────────────────────────────────────────────────

#[tokio::test]
async fn get_prompt_status_reports_pending_when_absent_from_history() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/history/still-running"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({})))
        .mount(&server)
        .await;

    let status = comfyui::get_prompt_status(&server.uri(), "still-running")
        .await
        .unwrap();
    assert!(!status.completed);
    assert!(!status.success);
}

#[tokio::test]
async fn get_prompt_status_reports_success_on_a_completed_entry() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/history/done-ok"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "done-ok": {
                "status": { "status_str": "success", "completed": true, "messages": [] },
                "outputs": {
                    "9": {"images": [{
                        "filename": "finished image.png",
                        "subfolder": "creator/jobs",
                        "type": "output"
                    }]}
                },
            },
        })))
        .mount(&server)
        .await;

    let status = comfyui::get_prompt_status(&server.uri(), "done-ok")
        .await
        .unwrap();
    assert!(status.completed);
    assert!(status.success);
    assert!(status.error.is_none());
    assert_eq!(status.outputs.len(), 1);
    assert_eq!(status.outputs[0].filename, "finished image.png");
    assert_eq!(status.outputs[0].subfolder, "creator/jobs");
}

#[tokio::test]
async fn get_prompt_status_reports_failure_on_an_errored_entry() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/history/done-error"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "done-error": {
                "status": {
                    "status_str": "error",
                    "completed": true,
                    "messages": [["execution_error", {"exception_message": "boom"}]],
                },
            },
        })))
        .mount(&server)
        .await;

    let status = comfyui::get_prompt_status(&server.uri(), "done-error")
        .await
        .unwrap();
    assert!(status.completed);
    assert!(!status.success);
    assert!(status.error.is_some());
}

#[tokio::test]
async fn get_prompt_status_surfaces_unreachable_comfyui() {
    let err = comfyui::get_prompt_status("http://127.0.0.1:1", "x")
        .await
        .unwrap_err();
    assert_eq!(err.code, ErrorCode::DependencyUnreachable);
}

#[tokio::test]
async fn output_preview_fetches_an_encoded_bounded_history_reference() {
    let server = MockServer::start().await;
    let png = b"\x89PNG\r\n\x1a\nsmall-preview";
    Mock::given(method("GET"))
        .and(path("/view"))
        .and(query_param("filename", "finished image.png"))
        .and(query_param("subfolder", "creator/jobs"))
        .and(query_param("type", "output"))
        .respond_with(ResponseTemplate::new(200).set_body_bytes(png))
        .expect(1)
        .mount(&server)
        .await;

    let preview = comfyui::get_output_preview(
        &server.uri(),
        &comfyui::PromptOutputRef {
            node_id: "9".into(),
            filename: "finished image.png".into(),
            subfolder: "creator/jobs".into(),
            folder_type: "output".into(),
        },
    )
    .await
    .unwrap();
    assert_eq!(preview.media_type, "image/png");
    assert!(preview.data_url.starts_with("data:image/png;base64,"));
}

#[tokio::test]
async fn output_preview_rejects_path_escape_before_requesting_comfyui() {
    let server = MockServer::start().await;
    let err = comfyui::get_output_preview(
        &server.uri(),
        &comfyui::PromptOutputRef {
            node_id: "9".into(),
            filename: "../secret.png".into(),
            subfolder: "".into(),
            folder_type: "output".into(),
        },
    )
    .await
    .unwrap_err();
    assert_eq!(err.code, ErrorCode::InvalidRequest);
    assert!(server.received_requests().await.unwrap().is_empty());
}

#[tokio::test]
async fn output_preview_rejects_an_oversized_response() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/view"))
        .respond_with(ResponseTemplate::new(200).set_body_bytes(vec![0; 8 * 1024 * 1024 + 1]))
        .mount(&server)
        .await;

    let err = comfyui::get_output_preview(
        &server.uri(),
        &comfyui::PromptOutputRef {
            node_id: "9".into(),
            filename: "too-large.png".into(),
            subfolder: "".into(),
            folder_type: "output".into(),
        },
    )
    .await
    .unwrap_err();
    assert_eq!(err.code, ErrorCode::InvalidRequest);
}
