//! Contract tests for `obs.rs`'s obs-websocket-v5 client against a fake OBS
//! server (P-001 WP-5 OBS half, HCP-005). No live OBS needed — this is the
//! "fakes pass in CI" half of the proposal's own WP-5 exit bar; hardware
//! evidence against the real, installed OBS Studio is separate and
//! recorded in docs/PROPOSALS.md, not here.
//!
//! The fake server is hand-rolled against `tokio-tungstenite`'s server-side
//! API (`accept_async`) speaking the real obs-websocket v5 wire protocol.
//! Every op-code and field name below was read directly out of the `obws`
//! 0.15.0 crate's own (de)serialization source
//! (`~/.cargo/registry/.../obws-0.15.0/src/{responses,requests}/*.rs`), not
//! assumed or copied from this repo's old stub comments. No authentication
//! challenge is modeled (`Hello.authentication: null`) — none of the tests
//! below need a wrong-password path, and obws sends no auth response when
//! the server doesn't ask for one, confirmed against
//! `obws::client::connection::handshake`.

use std::net::SocketAddr;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;

use command_error::ErrorCode;
use futures_util::{SinkExt, StreamExt};
use serde_json::{json, Value};
use stream_extend_lib::obs::{self, ObsClientCache};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::Mutex as AsyncMutex;
use tokio_tungstenite::{
    accept_async,
    tungstenite::{
        protocol::{frame::coding::CloseCode, CloseFrame},
        Message,
    },
    WebSocketStream,
};

// Candidate recording transport tests use test-only controller methods. They do
// not claim runtime Start/Stop availability; native admission remains fenced.
// Exercise the actual combined root controller with this existing protocol
// harness; no new test dependencies or copy of the OBS fake is introduced.
#[allow(dead_code)]
#[path = "../../../extend/src-tauri/src/preferences.rs"]
mod preferences;
#[path = "../../../extend/src-tauri/src/production.rs"]
mod production;

const NO_PASSWORD: Option<&str> = None;
const FIXED_SCENE_UUID_MAIN: &str = "11111111-1111-1111-1111-111111111111";
const FIXED_SCENE_UUID_ALT: &str = "22222222-2222-2222-2222-222222222222";

#[derive(Default)]
struct FakeState {
    current_scene: AsyncMutex<String>,
    recording_active: AtomicBool,
    stream_active: AtomicBool,
    recording_path: String,
    request_log: AsyncMutex<Vec<String>>,
    fail_request: AsyncMutex<Option<String>>,
    fail_after_apply: AtomicBool,
    error_code: AtomicUsize,
    omit_lifecycle: AtomicBool,
    subscriptions: AsyncMutex<Vec<u32>>,
    muted: AtomicBool,
    replace_on_stop: AtomicBool,
    hold_stop: AtomicBool,
    stop_entered: tokio::sync::Notify,
    stop_release: tokio::sync::Notify,
    hold_mute: AtomicBool,
    mute_entered: tokio::sync::Notify,
    mute_release: tokio::sync::Notify,
    hold_audio: AtomicBool,
    audio_entered: tokio::sync::Notify,
    audio_release: tokio::sync::Notify,
    events: Option<tokio::sync::broadcast::Sender<Value>>,
    disconnect_request: AsyncMutex<Option<String>>,
    replacement_path: AsyncMutex<Option<String>>,

    /// Count of `ToggleStream` requests specifically — NOT a count of all
    /// requests. `obws::Client::connect()` issues its own internal
    /// `GetVersion` request as part of `verify_versions()` before it ever
    /// returns (confirmed by reading `obws-0.15.0/src/client/mod.rs`
    /// directly) — every connection carries at least one request nothing
    /// in `obs.rs` asked for, so a generic per-connection request count
    /// would conflate "obws's own connect-time overhead" with "did
    /// `toggle_stream` send a redundant extra request."
    toggle_stream_request_count: AtomicUsize,
}

#[derive(Clone, Copy)]
enum Behavior {
    /// Answer every request with a canned, real-shaped response.
    Normal,
    /// Respond normally to the connect-time `GetVersion` check (request
    /// #1 on any fresh connection — obws issues it internally regardless
    /// of what the caller asked for), then read the next request and hang
    /// forever without responding or closing the connection — exercises
    /// `obs.rs`'s own per-request `REQUEST_TIMEOUT` (hardcoded at 8s;
    /// this test genuinely takes ~8 real seconds rather than a shortened
    /// one — parameterizing the timeout just for this one test would
    /// touch every OBS command's signature in `lib.rs`/`relay.rs`, judged
    /// not worth it for a few seconds of test runtime).
    HangAfterConnect,
    /// On the FIRST connection only: respond normally to the connect-time
    /// `GetVersion` check and exactly one real request after it (so a
    /// first call succeeds and its client gets cached), then close the
    /// socket without responding to the next request that arrives on that
    /// SAME connection — simulating the connection dying *between* two
    /// separate calls, not during the first one (`with_client` already
    /// retries once within a single call, so a drop during the very first
    /// request would be invisible to the caller and prove nothing). Every
    /// later connection serves normally, so a caller that reconnects
    /// after the drop succeeds.
    DropAfterFirstRealRequest,
    AuthenticationRejected,
}

async fn start_fake_obs(behavior: Behavior) -> (SocketAddr, Arc<FakeState>) {
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let state = Arc::new(FakeState {
        current_scene: AsyncMutex::new("Main Scene".into()),
        recording_active: AtomicBool::new(false),
        recording_path: std::env::temp_dir()
            .join(format!("hcp-obs-recording-{}.mkv", unique_fixture_id()))
            .to_string_lossy()
            .into_owned(),
        events: Some(tokio::sync::broadcast::channel(1024).0),
        error_code: AtomicUsize::new(207),
        ..Default::default()
    });
    std::fs::write(&state.recording_path, vec![1u8; 1024]).unwrap();
    let state_task = state.clone();

    tokio::spawn(async move {
        let mut first_connection = true;
        loop {
            let Ok((stream, _)) = listener.accept().await else {
                return;
            };
            let mut ws = match accept_async(stream).await {
                Ok(ws) => ws,
                Err(_) => continue,
            };
            if matches!(behavior, Behavior::AuthenticationRejected) {
                reject_authentication(&mut ws).await;
                continue;
            }
            if !handshake(&mut ws, &state_task).await {
                continue;
            }

            let is_first = first_connection;
            first_connection = false;
            let state_task = state_task.clone();
            tokio::spawn(async move {
                match behavior {
                    Behavior::Normal => serve_normally(&mut ws, &state_task, usize::MAX).await,
                    Behavior::HangAfterConnect if is_first => {
                        serve_normally(&mut ws, &state_task, 1).await; // the connect-time GetVersion
                        let _ = ws.next().await; // read the real request, then hang without responding
                        std::future::pending::<()>().await;
                    }
                    Behavior::HangAfterConnect => {
                        serve_normally(&mut ws, &state_task, usize::MAX).await
                    }
                    Behavior::DropAfterFirstRealRequest if is_first => {
                        serve_normally(&mut ws, &state_task, 2).await; // connect-time GetVersion + first real request
                        let _ = ws.next().await; // read the next request, then drop without responding
                    }
                    Behavior::DropAfterFirstRealRequest => {
                        serve_normally(&mut ws, &state_task, usize::MAX).await
                    }
                    Behavior::AuthenticationRejected => unreachable!(),
                }
            });
        }
    });

    (addr, state)
}

async fn reject_authentication(ws: &mut WebSocketStream<TcpStream>) {
    let hello = json!({
        "op": 0,
        "d": {
            "obsWebSocketVersion": "5.5.5",
            "rpcVersion": 1,
            "authentication": { "challenge": "Y2hhbGxlbmdl", "salt": "c2FsdA==" }
        }
    });
    if ws.send(Message::Text(hello.to_string())).await.is_err() {
        return;
    }
    let _ = ws.next().await;
    let _ = ws
        .send(Message::Close(Some(CloseFrame {
            code: CloseCode::Library(4009),
            reason: "Authentication Failed".into(),
        })))
        .await;
}

async fn handshake(ws: &mut WebSocketStream<TcpStream>, state: &FakeState) -> bool {
    let hello = json!({
        "op": 0,
        "d": { "obsWebSocketVersion": "5.5.5", "rpcVersion": 1, "authentication": null }
    });
    if ws.send(Message::Text(hello.to_string())).await.is_err() {
        return false;
    }

    let Some(Ok(msg)) = ws.next().await else {
        return false;
    };
    let Ok(text) = msg.to_text() else {
        return false;
    };
    let Ok(parsed) = serde_json::from_str::<Value>(text) else {
        return false;
    };
    if parsed.get("op").and_then(Value::as_u64) != Some(1) {
        return false;
    }

    state
        .subscriptions
        .lock()
        .await
        .push(parsed["d"]["eventSubscriptions"].as_u64().unwrap_or(0) as u32);
    let identified = json!({ "op": 2, "d": { "negotiatedRpcVersion": 1 } });
    ws.send(Message::Text(identified.to_string())).await.is_ok()
}

async fn serve_normally(
    ws: &mut WebSocketStream<TcpStream>,
    state: &FakeState,
    max_requests: usize,
) {
    let mut served = 0usize;
    let mut events = state.events.as_ref().unwrap().subscribe();
    loop {
        if served >= max_requests {
            return;
        }
        let msg = tokio::select! {
            biased;
            event = events.recv() => {
                match event { Ok(event) => { if event["op"] == 999 { let _ = ws.close(None).await; return; } if ws.send(Message::Text(event.to_string())).await.is_err() { return; } }, Err(_) => return }
                continue;
            }
            msg = ws.next() => msg,
        };
        let Some(Ok(msg)) = msg else {
            return;
        };
        let Ok(text) = msg.to_text() else { return };
        let Ok(parsed) = serde_json::from_str::<Value>(text) else {
            return;
        };
        if parsed.get("op").and_then(Value::as_u64) != Some(6) {
            continue;
        }
        let d = &parsed["d"];
        let request_id = d["requestId"].as_str().unwrap_or_default().to_string();
        let request_type = d["requestType"].as_str().unwrap_or_default().to_string();

        if request_type == "ToggleStream" {
            state
                .toggle_stream_request_count
                .fetch_add(1, Ordering::SeqCst);
        }

        state.request_log.lock().await.push(request_type.clone());

        if request_type == "StopRecord" && state.replace_on_stop.load(Ordering::SeqCst) {
            // A different controller replaces the output after client admission.
            external_replacement(state).await;
        }
        if request_type == "StopRecord" && state.hold_stop.load(Ordering::SeqCst) {
            state.stop_entered.notify_one();
            state.stop_release.notified().await;
        }
        if request_type == "GetInputList" && state.hold_audio.load(Ordering::SeqCst) {
            state.audio_entered.notify_one();
            state.audio_release.notified().await;
        }
        if matches!(request_type.as_str(), "GetInputMute" | "SetInputMute")
            && d["requestData"]["inputName"] != "Mic"
        {
            let response = json!({"op":7,"d":{"requestType":request_type,"requestId":request_id,"requestStatus":{"result":false,"code":600,"comment":"unknown input"}}});
            let _ = ws.send(Message::Text(response.to_string())).await;
            continue;
        }
        if state.disconnect_request.lock().await.as_deref() == Some(request_type.as_str()) {
            if request_type == "StopRecord" {
                state.recording_active.store(false, Ordering::SeqCst);
            }
            let _ = ws.close(None).await;
            return;
        }
        let fail = state.fail_request.lock().await.as_deref() == Some(request_type.as_str());
        if fail && state.fail_after_apply.load(Ordering::SeqCst) {
            // Simulate an acknowledged request whose response was lost.
            if request_type == "StartRecord" {
                state.recording_active.store(true, Ordering::SeqCst);
            }
            if request_type == "StopRecord" {
                state.recording_active.store(false, Ordering::SeqCst);
            }
        }
        if fail {
            let response = json!({"op":7,"d":{"requestType":request_type,"requestId":request_id,
                "requestStatus":{"result":false,"code":state.error_code.load(Ordering::SeqCst),"comment":"synthetic private error must not reach UI"}}});
            let _ = ws.send(Message::Text(response.to_string())).await;
            continue;
        }
        if request_type == "SetInputMute" && state.hold_mute.load(Ordering::SeqCst) {
            state.mute_entered.notify_one();
            state.mute_release.notified().await;
        }
        if request_type == "SetInputMute" {
            state.muted.store(
                d["requestData"]["inputMuted"].as_bool().unwrap(),
                Ordering::SeqCst,
            );
        }
        if request_type == "SetCurrentProgramScene" {
            if let Some(name) = d
                .get("requestData")
                .and_then(|rd| rd.get("sceneName"))
                .and_then(Value::as_str)
            {
                *state.current_scene.lock().await = name.to_string();
            }
        }

        if request_type == "StartRecord" {
            state.recording_active.store(true, Ordering::SeqCst);
        } else if request_type == "StopRecord" {
            state.recording_active.store(false, Ordering::SeqCst);
        }
        if request_type == "StartStream" {
            state.stream_active.store(true, Ordering::SeqCst);
        } else if request_type == "StopStream" {
            state.stream_active.store(false, Ordering::SeqCst);
        } else if request_type == "ToggleStream" {
            let active = state.stream_active.load(Ordering::SeqCst);
            state.stream_active.store(!active, Ordering::SeqCst);
        }
        if (request_type == "StartRecord" || request_type == "StopRecord")
            && !state.omit_lifecycle.load(Ordering::SeqCst)
        {
            let active = request_type == "StartRecord";
            for output_state in if active {
                ["STARTING", "STARTED"]
            } else {
                ["STOPPING", "STOPPED"]
            } {
                let event = record_event(
                    active,
                    output_state,
                    if active {
                        None
                    } else {
                        Some(state.recording_path.as_str())
                    },
                );
                if ws.send(Message::Text(event.to_string())).await.is_err() {
                    return;
                }
            }
        }
        let response_data = canned_response(&request_type, state).await;
        let mut resp_d = json!({
            "requestType": request_type,
            "requestId": request_id,
            "requestStatus": { "result": true, "code": 100, "comment": null },
        });
        if let Some(data) = response_data {
            resp_d["responseData"] = data;
        }
        let resp = json!({ "op": 7, "d": resp_d });
        if ws.send(Message::Text(resp.to_string())).await.is_err() {
            return;
        }
        served += 1;
    }
}

async fn canned_response(request_type: &str, state: &FakeState) -> Option<Value> {
    match request_type {
        "GetVersion" => Some(json!({
            "obsStudioVersion": "30.2.0",
            "obsWebSocketVersion": "5.5.5",
            "rpcVersion": 1,
            "availableRequests": [],
            "supportedImageFormats": [],
            "platform": "macos",
            "platformDescription": "macOS 15.0",
        })),
        "GetSceneList" => {
            let current_scene = state.current_scene.lock().await;
            let (uuid, alt_uuid, alt_name) =
                (FIXED_SCENE_UUID_MAIN, FIXED_SCENE_UUID_ALT, "Starting Soon");
            let current = current_scene.as_str();
            Some(json!({
                "currentProgramSceneName": current,
                "currentProgramSceneUuid": if current == "Main Scene" { uuid } else { alt_uuid },
                "scenes": [
                    { "sceneName": "Main Scene", "sceneUuid": uuid, "sceneIndex": 0 },
                    { "sceneName": alt_name, "sceneUuid": alt_uuid, "sceneIndex": 1 },
                ],
            }))
        }
        // Zero response fields — confirmed against obws's own SetCurrentProgramScene
        // handling (no responses::scenes type for it at all).
        "SetCurrentProgramScene" => None,
        "GetStreamStatus" => Some(json!({
            "outputActive": state.stream_active.load(Ordering::SeqCst),
            "outputReconnecting": false,
            "outputTimecode": "00:02:03.000",
            "outputDuration": 123_000,
            "outputCongestion": 0.0,
            "outputBytes": 125_000,
            "outputSkippedFrames": 3,
            "outputTotalFrames": 1000,
        })),
        "ToggleStream" => {
            Some(json!({ "outputActive": state.stream_active.load(Ordering::SeqCst) }))
        }
        "StartStream" => None,
        "StopStream" => None,
        "GetInputList" => Some(
            json!({"inputs":[{"inputName":"Mic","inputUuid":FIXED_SCENE_UUID_MAIN,"inputKind":"coreaudio_input_capture","unversionedInputKind":"coreaudio_input_capture"}]}),
        ),
        "GetInputMute" => Some(json!({"inputMuted":state.muted.load(Ordering::SeqCst)})),
        "SetInputMute" => None,
        "GetRecordStatus" => Some(json!({
            "outputActive": state.recording_active.load(Ordering::SeqCst),
            "outputPaused": false,
            "outputTimecode": "00:00:00.000",
            "outputDuration": 0,
            "outputBytes": 0,
        })),
        "StartRecord" => None,
        "StopRecord" => Some(
            json!({ "outputPath": state.replacement_path.lock().await.as_deref().unwrap_or(&state.recording_path) }),
        ),
        _ => None,
    }
}

async fn unreachable_addr() -> SocketAddr {
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    drop(listener); // nothing is listening on this port anymore
    addr
}

// ── get_status ───────────────────────────────────────────────────────

#[tokio::test]
async fn full_handshake_then_get_status_reports_connected_with_real_version_fields() {
    let (addr, _state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();

    let status = obs::get_status(&cache, "127.0.0.1", addr.port(), NO_PASSWORD).await;
    assert!(status.connected);
    assert_eq!(status.obs_version.as_deref(), Some("30.2.0"));
    assert_eq!(status.ws_version.as_deref(), Some("5.5.5"));
    assert_eq!(status.platform.as_deref(), Some("macos"));
}

#[tokio::test]
async fn get_status_reports_disconnected_when_obs_is_unreachable() {
    let addr = unreachable_addr().await;
    let cache = ObsClientCache::new();

    let status = obs::get_status(&cache, "127.0.0.1", addr.port(), NO_PASSWORD).await;
    assert!(!status.connected);
}

#[tokio::test]
async fn diagnostic_distinguishes_reachable_and_unreachable_websocket() {
    let (addr, _state) = start_fake_obs(Behavior::Normal).await;
    let connected = obs::diagnose_connection("127.0.0.1", addr.port(), NO_PASSWORD).await;
    assert_eq!(connected.state, "connected");
    assert_eq!(connected.obs_version.as_deref(), Some("30.2.0"));

    let unavailable = unreachable_addr().await;
    let disconnected = obs::diagnose_connection("127.0.0.1", unavailable.port(), NO_PASSWORD).await;
    assert_eq!(disconnected.state, "websocket_unreachable");
}

#[tokio::test]
async fn diagnostic_identifies_a_rejected_obs_password() {
    let (addr, _state) = start_fake_obs(Behavior::AuthenticationRejected).await;
    let diagnostic =
        obs::diagnose_connection("127.0.0.1", addr.port(), Some("wrong-password")).await;
    assert_eq!(diagnostic.state, "authentication_failed");
    assert!(diagnostic.detail.contains("rejected"));
}

#[tokio::test]
async fn recording_test_creates_evidence_without_interrupting_an_active_recording() {
    let (addr, state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let report = obs::run_recording_test(
        &cache,
        "127.0.0.1",
        addr.port(),
        NO_PASSWORD,
        std::time::Duration::from_millis(1),
    )
    .await
    .unwrap();
    assert!(report.accepted);
    assert_eq!(report.bytes, 1024);

    state.recording_active.store(true, Ordering::SeqCst);
    let error = obs::run_recording_test(
        &cache,
        "127.0.0.1",
        addr.port(),
        NO_PASSWORD,
        std::time::Duration::from_millis(1),
    )
    .await
    .unwrap_err();
    assert_eq!(error.code, ErrorCode::InvalidRequest);
}

// ── get_scenes / switch_scene ───────────────────────────────────────

#[tokio::test]
async fn get_scenes_returns_real_scene_list_with_current_flag_set() {
    let (addr, _state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();

    let scenes = obs::get_scenes(&cache, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap();
    assert_eq!(scenes.len(), 2);
    let main = scenes.iter().find(|s| s.name == "Main Scene").unwrap();
    assert!(main.is_current);
    let alt = scenes.iter().find(|s| s.name == "Starting Soon").unwrap();
    assert!(!alt.is_current);
}

#[tokio::test]
async fn switch_scene_returns_the_freshly_observed_scene_list() {
    let (addr, _state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();

    let scenes = obs::switch_scene(
        &cache,
        "127.0.0.1",
        addr.port(),
        NO_PASSWORD,
        "Starting Soon",
    )
    .await
    .unwrap();

    // Proves a real observed result came back (the fake server only marks a
    // scene current after it actually receives SetCurrentProgramScene) —
    // not `Ok(())` or a stale/static list.
    let alt = scenes.iter().find(|s| s.name == "Starting Soon").unwrap();
    assert!(
        alt.is_current,
        "expected the switched-to scene to be marked current in the re-fetched list"
    );
    let main = scenes.iter().find(|s| s.name == "Main Scene").unwrap();
    assert!(!main.is_current);
}

// ── get_stream_status ────────────────────────────────────────────────

#[tokio::test]
async fn get_stream_status_maps_real_fields_including_derived_kbps() {
    let (addr, _state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();

    let status = obs::get_stream_status(&cache, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap();
    assert_eq!(status.bytes, 125_000);
    assert_eq!(status.skipped_frames, 3);
    assert_eq!(status.total_frames, 1000);
    assert_eq!(status.timecode.as_deref(), Some("00:02:03"));
    // outputDuration = 123_000ms = 123s; kbps = 125_000*8/1000 / 123 ≈ 8.13
    assert!(
        (status.kbits_per_sec - 8.130).abs() < 0.01,
        "got {}",
        status.kbits_per_sec
    );
}

// ── toggle_stream ────────────────────────────────────────────────────

#[tokio::test]
async fn toggle_stream_returns_the_authoritative_new_state_with_no_extra_request() {
    let (addr, state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();

    let active = obs::toggle_stream(&cache, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap();
    assert!(active);
    assert_eq!(
        state.toggle_stream_request_count.load(Ordering::SeqCst),
        1,
        "toggle_stream should send exactly one ToggleStream request, no redundant re-read"
    );
}

#[tokio::test]
async fn managed_live_session_records_before_streaming_and_returns_finalized_path() {
    let (addr, state) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let session = obs::ObsSessionState::new();
    let started = obs::start_live_session(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        NO_PASSWORD,
        Some("stream-main".into()),
        Some("content-main".into()),
    )
    .await
    .unwrap();
    assert!(started.stream_active);
    assert!(started.recording_owned);

    let stopped = obs::stop_live_session(&cache, &session, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap();
    assert_eq!(
        stopped.recording_path.as_deref(),
        Some(state.recording_path.as_str())
    );
    assert_eq!(stopped.source_profile_id.as_deref(), Some("stream-main"));
    assert_eq!(stopped.content_profile_id.as_deref(), Some("content-main"));
    let log = state.request_log.lock().await;
    let record_start = log.iter().position(|item| item == "StartRecord").unwrap();
    let stream_start = log.iter().position(|item| item == "StartStream").unwrap();
    let stream_stop = log.iter().position(|item| item == "StopStream").unwrap();
    let record_stop = log.iter().position(|item| item == "StopRecord").unwrap();
    assert!(record_start < stream_start);
    assert!(stream_stop < record_stop);
}

#[tokio::test]
async fn managed_live_session_never_stops_or_claims_a_preexisting_recording() {
    let (addr, state) = start_fake_obs(Behavior::Normal).await;
    state.recording_active.store(true, Ordering::SeqCst);
    let cache = ObsClientCache::new();
    let session = obs::ObsSessionState::new();
    let started = obs::start_live_session(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        NO_PASSWORD,
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!started.recording_owned);
    let stopped = obs::stop_live_session(&cache, &session, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap();
    assert!(stopped.recording_path.is_none());
    assert!(state.recording_active.load(Ordering::SeqCst));
    assert!(!state
        .request_log
        .lock()
        .await
        .iter()
        .any(|item| item == "StopRecord"));
}

// ── timeout / reconnect ─────────────────────────────────────────────

#[tokio::test]
async fn a_request_that_never_responds_surfaces_request_timeout_not_a_guessed_value() {
    let (addr, _state) = start_fake_obs(Behavior::HangAfterConnect).await;
    let cache = ObsClientCache::new();

    let err = obs::get_scenes(&cache, "127.0.0.1", addr.port(), NO_PASSWORD)
        .await
        .unwrap_err();
    assert_eq!(err.code, ErrorCode::RequestTimeout);
}

#[tokio::test]
async fn a_dropped_mid_session_connection_causes_the_next_call_to_reconnect_successfully() {
    let (addr, _state) = start_fake_obs(Behavior::DropAfterFirstRealRequest).await;
    let cache = ObsClientCache::new();

    // First call: connects fresh, gets a real response, its client is now
    // cached. The fake server then silently kills that same connection.
    let first = obs::get_scenes(&cache, "127.0.0.1", addr.port(), NO_PASSWORD).await;
    assert!(
        first.is_ok(),
        "first call should succeed against a fresh connection: {first:?}"
    );

    // Second call against the SAME cache: its first attempt hits the now-dead
    // connection and fails, but `with_client`'s drop-and-retry-once logic
    // should reconnect against a fresh connection and succeed anyway —
    // without this, the second call would surface the stale-connection
    // error instead.
    let second = obs::get_scenes(&cache, "127.0.0.1", addr.port(), NO_PASSWORD).await;
    assert!(
        second.is_ok(),
        "expected the cache to reconnect and succeed on the next call: {second:?}"
    );
}

fn unique_fixture_id() -> String {
    static NEXT: AtomicUsize = AtomicUsize::new(1);
    format!(
        "{}-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    )
}

fn combined_connection(addr: SocketAddr) -> production::Connection {
    production::Connection {
        host: "127.0.0.1".into(),
        port: addr.port(),
        password: None,
    }
}
fn combined_library() -> (std::path::PathBuf, recording_library::RecordingLibrary) {
    let root = std::env::temp_dir().join(format!("hcp-combined-{}", unique_fixture_id()));
    let library = recording_library::RecordingLibrary::new(&root).unwrap();
    (root, library)
}

#[tokio::test]
async fn combined_recording_pins_profiles_connection_and_hands_off_exactly_once() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let (root, library) = combined_library();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    // UI/profile changes cannot replace the captured attribution/endpoint.
    let wrong = production::Connection {
        host: "127.0.0.1".into(),
        port: 1,
        password: Some("private-synthetic".into()),
    };
    cache.clear().await; // force reconnect: cached clients must not mask an endpoint redirection
    let status = controller.status(&cache, &wrong).await;
    assert!(status.connected && status.owned);
    assert!(
        fake.subscriptions.lock().await.contains(&64),
        "ownership requires an Outputs subscription"
    );
    assert_eq!(status.source_profile_id.as_deref(), Some("stream-main"));
    assert_eq!(status.content_profile_id.as_deref(), Some("content-main"));
    assert!(serde_json::to_string(&status)
        .unwrap()
        .find("private-synthetic")
        .is_none());
    let scenes =
        obs::switch_observed_scene(&cache, "127.0.0.1", addr.port(), None, "Starting Soon")
            .await
            .unwrap();
    assert!(scenes
        .iter()
        .any(|s| s.name == "Starting Soon" && s.is_current));
    assert!(
        obs::switch_observed_scene(&cache, "127.0.0.1", addr.port(), None, "unknown")
            .await
            .is_err()
    );
    let inputs = obs::set_input_muted(&cache, "127.0.0.1", addr.port(), None, "Mic", true)
        .await
        .unwrap();
    assert!(inputs[0].muted);
    assert!(
        obs::set_input_muted(&cache, "127.0.0.1", addr.port(), None, "unknown", false)
            .await
            .is_err()
    );
    assert!(controller
        .candidate_stop(&cache, &library, "stale-session")
        .await
        .is_err());
    assert!(controller.recover(&cache, &id).await.is_err());
    controller
        .candidate_stop(&cache, &library, &id)
        .await
        .unwrap();
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    let records = library.list().unwrap();
    assert_eq!(records.len(), 1);
    assert_eq!(
        records[0].record.source_profile_id.as_deref(),
        Some("stream-main")
    );
    assert_eq!(
        records[0].record.content_profile_id.as_deref(),
        Some("content-main")
    );
    let requests = fake.request_log.lock().await;
    assert_eq!(requests.iter().filter(|r| *r == "StartRecord").count(), 1);
    assert_eq!(requests.iter().filter(|r| *r == "StopRecord").count(), 1);
    assert!(!requests
        .iter()
        .any(|r| r == "StartStream" || r == "StopStream"));
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_external_recording_and_stream_are_never_adopted_or_stopped() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let (root, library) = combined_library();
    fake.recording_active.store(true, Ordering::SeqCst);
    assert!(controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into()
        )
        .await
        .is_err());
    assert!(!controller.busy());
    assert!(controller
        .candidate_stop(&cache, &library, "external")
        .await
        .is_err());
    fake.recording_active.store(false, Ordering::SeqCst);
    fake.stream_active.store(true, Ordering::SeqCst);
    assert!(controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into()
        )
        .await
        .is_err());
    assert!(!controller.busy());
    let requests = fake.request_log.lock().await;
    assert!(!requests
        .iter()
        .any(|r| r == "StartRecord" || r == "StopRecord" || r == "StopStream"));
    assert!(library.list().unwrap().is_empty());
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_failed_start_keeps_recovery_reservation_without_adopting_output() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    *fake.fail_request.lock().await = Some("StartRecord".into());
    fake.fail_after_apply.store(true, Ordering::SeqCst);
    let receipt = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    assert!(!receipt.confirmed);
    assert!(!serde_json::to_string(&receipt)
        .unwrap()
        .contains("private error"));
    let status = controller.status(&cache, &combined_connection(addr)).await;
    assert!(status.recovery_required && !status.owned);
    let id = status.session_id.unwrap();
    let (root, library) = combined_library();
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert!(controller.recover(&cache, &id).await.is_err());
    assert!(controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "other".into(),
            "other".into()
        )
        .await
        .is_err());
    assert!(fake.recording_active.load(Ordering::SeqCst));
    fake.recording_active.store(false, Ordering::SeqCst); // operator stops in OBS
    controller.recover(&cache, &id).await.unwrap();
    assert!(!controller.busy());
    let requests = fake.request_log.lock().await;
    assert_eq!(requests.iter().filter(|r| *r == "StartRecord").count(), 1);
    assert!(!requests.iter().any(|r| r == "StopRecord"));
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_stop_failure_retries_owned_recording_and_preserves_pinned_destination() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "opentech-marketing".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    *fake.fail_request.lock().await = Some("StopRecord".into());
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert!(
        controller
            .status(&cache, &combined_connection(addr))
            .await
            .owned
    );
    assert!(library.list().unwrap().is_empty());
    *fake.fail_request.lock().await = None;
    controller
        .candidate_stop(&cache, &library, &id)
        .await
        .unwrap();
    assert_eq!(
        library.list().unwrap()[0]
            .record
            .content_profile_id
            .as_deref(),
        Some("opentech-marketing")
    );
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        2
    );
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_lost_stop_response_requires_manual_import_without_duplicate_stop() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    *fake.fail_request.lock().await = Some("StopRecord".into());
    fake.fail_after_apply.store(true, Ordering::SeqCst);
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    *fake.fail_request.lock().await = None;
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    controller.recover(&cache, &id).await.unwrap();
    assert!(library.list().unwrap().is_empty());
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_inbox_retry_does_not_send_another_stop_or_lose_attribution() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "agent-labs".into(),
            "opentech-marketing".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    std::fs::remove_file(&fake.recording_path).unwrap();
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert!(
        controller
            .status(&cache, &combined_connection(addr))
            .await
            .handoff_pending
    );
    assert!(controller.recover(&cache, &id).await.is_err());
    std::fs::write(&fake.recording_path, vec![1u8; 1024]).unwrap();
    controller
        .candidate_stop(&cache, &library, &id)
        .await
        .unwrap();
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    assert_eq!(
        library.list().unwrap()[0]
            .record
            .source_profile_id
            .as_deref(),
        Some("agent-labs")
    );
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_duplicate_concurrent_start_stop_and_stale_generation_are_rejected() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let controller = AsyncMutex::new(production::Controller::default());
    let start = || async {
        controller
            .lock()
            .await
            .candidate_start(
                &cache,
                combined_connection(addr),
                "stream-main".into(),
                "content-main".into(),
            )
            .await
    };
    let (a, b) = tokio::join!(start(), start());
    assert_ne!(a.is_ok(), b.is_ok());
    let id = a.or(b).unwrap();
    let (root, library) = combined_library();
    let stop = || async {
        controller
            .lock()
            .await
            .candidate_stop(&cache, &library, &id)
            .await
    };
    let (a, b) = tokio::join!(stop(), stop());
    assert_ne!(a.is_ok(), b.is_ok());
    let next = controller
        .lock()
        .await
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    assert_ne!(id, next);
    assert!(controller
        .lock()
        .await
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert!(controller
        .lock()
        .await
        .require_generation(Some(&id))
        .is_err());
    controller
        .lock()
        .await
        .candidate_stop(&cache, &library, &next)
        .await
        .unwrap();
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_restart_never_restores_ownership_of_an_existing_recording() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut old = production::Controller::default();
    old.candidate_start(
        &cache,
        combined_connection(addr),
        "stream-main".into(),
        "content-main".into(),
    )
    .await
    .unwrap();
    drop(old);
    let mut restarted = production::Controller::default();
    let status = restarted.status(&cache, &combined_connection(addr)).await;
    assert!(!status.owned && status.recording_active == Some(true));
    assert!(restarted
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into()
        )
        .await
        .is_err());
    let (root, library) = combined_library();
    assert!(restarted
        .candidate_stop(&cache, &library, "persisted-id")
        .await
        .is_err());
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    if root.exists() {
        std::fs::remove_dir_all(root).unwrap();
    }
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_adapter_independently_rejects_external_unowned_and_duplicate_calls() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let session = obs::LocalRecordingState::new();
    fake.recording_active.store(true, Ordering::SeqCst);
    assert!(obs::start_owned_recording(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        None,
        "stream-main".into(),
        "content-main".into()
    )
    .await
    .is_err());
    assert!(
        obs::stop_owned_recording(&cache, &session, "127.0.0.1", addr.port(), None)
            .await
            .is_err()
    );
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StartRecord" || r == "StopRecord"));
    fake.recording_active.store(false, Ordering::SeqCst);
    obs::start_owned_recording(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        None,
        "stream-main".into(),
        "content-main".into(),
    )
    .await
    .unwrap();
    assert!(obs::start_owned_recording(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        None,
        "other".into(),
        "other".into()
    )
    .await
    .is_err());
    obs::stop_owned_recording(&cache, &session, "127.0.0.1", addr.port(), None)
        .await
        .unwrap();
    let requests = fake.request_log.lock().await;
    assert_eq!(requests.iter().filter(|r| *r == "StartRecord").count(), 1);
    assert_eq!(requests.iter().filter(|r| *r == "StopRecord").count(), 1);
    std::fs::remove_file(&fake.recording_path).unwrap();
}

#[tokio::test]
async fn combined_recording_stop_cannot_claim_an_external_recording_in_a_legacy_live_session() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let session = obs::ObsSessionState::new();
    fake.recording_active.store(true, Ordering::SeqCst);
    obs::start_live_session(
        &cache,
        &session,
        "127.0.0.1",
        addr.port(),
        None,
        Some("stream-main".into()),
        Some("content-main".into()),
    )
    .await
    .unwrap();
    assert!(obs::stop_owned_recording(
        &cache,
        &obs::LocalRecordingState::new(),
        "127.0.0.1",
        addr.port(),
        None
    )
    .await
    .is_err());
    assert!(fake.recording_active.load(Ordering::SeqCst));
    obs::stop_live_session(&cache, &session, "127.0.0.1", addr.port(), None)
        .await
        .unwrap();
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    std::fs::remove_file(&fake.recording_path).unwrap();
}

fn record_event(active: bool, state: &str, path: Option<&str>) -> Value {
    json!({"op":5,"d":{"eventType":"RecordStateChanged","eventIntent":64,
        "eventData":{"outputActive":active,"outputState":format!("OBS_WEBSOCKET_OUTPUT_{state}"),"outputPath":path}}})
}
async fn external_replacement(fake: &FakeState) {
    fake.recording_active.store(false, Ordering::SeqCst);
    let _ = fake.events.as_ref().unwrap().send(record_event(
        false,
        "STOPPED",
        Some(&fake.recording_path),
    ));
    *fake.replacement_path.lock().await = Some("external-replacement.mkv".into());
    fake.recording_active.store(true, Ordering::SeqCst);
    let _ = fake
        .events
        .as_ref()
        .unwrap()
        .send(record_event(true, "STARTED", None));
}
#[tokio::test]
async fn repair_external_replacement_cannot_be_stopped_or_attributed() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    external_replacement(&fake).await;
    let (root, library) = combined_library();
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert!(fake.recording_active.load(Ordering::SeqCst));
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        0
    );
    assert!(library.list().unwrap().is_empty());
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_uncertain_stop_never_retries_against_replacement() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    *fake.disconnect_request.lock().await = Some("StopRecord".into());
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    *fake.disconnect_request.lock().await = None;
    external_replacement(&fake).await;
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    assert!(fake.recording_active.load(Ordering::SeqCst));
    assert!(library.list().unwrap().is_empty());
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_pending_handoff_can_be_explicitly_left_for_manual_import() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    std::fs::remove_file(&fake.recording_path).unwrap();
    assert!(controller
        .candidate_stop(&cache, &library, &id)
        .await
        .is_err());
    // Runtime retry is registration only; missing file never dispatches another Stop.
    assert!(controller.stop(&cache, &library, &id).await.is_err());
    assert!(controller.abandon_handoff(&cache, &id).await.is_ok());
    assert!(!controller.busy());
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    let _ = std::fs::remove_dir_all(root);
}

#[tokio::test]
async fn repair_slow_inspection_does_not_hold_the_safety_controller() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let controller = Arc::new(AsyncMutex::new(production::Controller::default()));
    fake.hold_audio.store(true, Ordering::SeqCst);
    let handle = {
        let controller = controller.clone();
        tokio::spawn(async move {
            production::inspect_audio(&controller, || Ok(combined_connection(addr))).await
        })
    };
    fake.audio_entered.notified().await;
    let admitted = controller.try_lock().is_ok();
    fake.audio_release.notify_one();
    handle.await.unwrap().unwrap();
    assert!(
        admitted,
        "hung inspection held the controller mutex used by safety commands"
    );
    let _ = std::fs::remove_file(&fake.recording_path);
}

#[tokio::test]
async fn repair_safety_commands_dispatch_while_audio_inspection_is_held_and_stale_read_is_rejected()
{
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let controller = Arc::new(AsyncMutex::new(production::Controller::default()));
    let id = controller
        .lock()
        .await
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    fake.hold_audio.store(true, Ordering::SeqCst);
    let inspection = {
        let controller = controller.clone();
        tokio::spawn(async move {
            production::inspect_audio(&controller, || {
                Err("corrupt preferences must not be consulted".into())
            })
            .await
        })
    };
    fake.audio_entered.notified().await;
    let (root, library) = combined_library();
    // Timeout is solely a deadlock escape: the read remains explicitly held
    // until both actual protocol mutations have completed on other sockets.
    tokio::time::timeout(std::time::Duration::from_secs(2), async {
        let guard = controller.lock().await;
        guard.require_generation(Some(&id)).unwrap();
        let c = guard
            .resolve_connection(|| Err("locked vault must not be consulted".into()))
            .unwrap();
        let audio = obs::set_input_muted(
            &ObsClientCache::new(),
            &c.host,
            c.port,
            c.password.as_deref(),
            "Mic",
            true,
        )
        .await
        .unwrap();
        assert!(audio[0].muted);
        drop(guard);
        controller
            .lock()
            .await
            .candidate_stop(&cache, &library, &id)
            .await
            .unwrap();
    })
    .await
    .expect("inspection blocked safety dispatch");
    assert!(fake.muted.load(Ordering::SeqCst));
    fake.audio_release.notify_one();
    assert!(
        inspection.await.unwrap().is_err(),
        "stale generation read was accepted after Stop"
    );
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_lost_control_subscription_revokes_ownership_even_when_observation_reconnects() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    fake.events
        .as_ref()
        .unwrap()
        .send(json!({"op":999}))
        .unwrap();
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    let status = c.status(&cache, &combined_connection(addr)).await;
    assert!(status.connected && !status.owned && status.recovery_required);
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    fake.recording_active.store(false, Ordering::SeqCst);
    c.recover(&cache, &id).await.unwrap();
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_unknown_api_outcome_revokes_stop_retry_without_a_replacement() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    *fake.fail_request.lock().await = Some("StopRecord".into());
    fake.error_code.store(205, Ordering::SeqCst);
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    *fake.fail_request.lock().await = None;
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    assert!(library.list().unwrap().is_empty());
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_missing_start_event_never_confers_ownership() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    fake.omit_lifecycle.store(true, Ordering::SeqCst);
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let receipt = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    assert!(!receipt.confirmed);
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &receipt).await.is_err());
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_finalized_abandon_checks_generation_inactivity_and_preserves_manual_attribution() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "agent-labs".into(),
            "opentech-marketing".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    assert!(c.abandon_handoff(&cache, &id).await.is_err());
    std::fs::remove_file(&fake.recording_path).unwrap();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    assert!(c.abandon_handoff(&cache, "stale").await.is_err());
    fake.stream_active.store(true, Ordering::SeqCst);
    assert!(c.abandon_handoff(&cache, &id).await.is_err());
    fake.stream_active.store(false, Ordering::SeqCst);
    let note = c.abandon_handoff(&cache, &id).await.unwrap();
    assert!(
        note.contains("agent-labs")
            && note.contains("opentech-marketing")
            && note.contains("No file was registered")
    );
    let before = preferences::Preferences::initial();
    let mut next = before.clone();
    next.obs_port += 1;
    assert!(c.allow_preferences(&before, &next).is_ok());
    let next = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    assert_ne!(id, next);
    assert!(c.abandon_handoff(&cache, &id).await.is_err());
    assert!(c.abandon_handoff(&cache, &next).await.is_err());
    assert_eq!(
        fake.request_log
            .lock()
            .await
            .iter()
            .filter(|r| *r == "StopRecord")
            .count(),
        1
    );
    assert!(library
        .register(
            &fake.recording_path,
            recording_library::RecordingOrigin::ManualImport,
            None,
            None
        )
        .is_err());
    let _ = std::fs::remove_dir_all(root);
}

#[tokio::test]
async fn repair_lagged_subscription_cannot_authorize_stop() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    for _ in 0..300 {
        fake.events
            .as_ref()
            .unwrap()
            .send(record_event(true, "PAUSED", None))
            .unwrap();
    }
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    assert!(!c.status(&cache, &combined_connection(addr)).await.owned);
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_finalized_path_must_match_the_observed_stop_lifecycle() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let alternate =
        std::env::temp_dir().join(format!("different-finalized-{}.mkv", unique_fixture_id()));
    std::fs::write(&alternate, [1u8; 32]).unwrap();
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    *fake.replacement_path.lock().await = Some(alternate.to_string_lossy().into());
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    let status = c.status(&cache, &combined_connection(addr)).await;
    assert!(status.recovery_required && !status.handoff_pending);
    assert!(library.list().unwrap().is_empty());
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
    let _ = std::fs::remove_file(alternate);
}
#[tokio::test]
async fn repair_abandon_cannot_discard_an_unconfirmed_nonfinalized_reservation() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    *fake.fail_request.lock().await = Some("StartRecord".into());
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    assert!(!id.confirmed);
    assert!(c.abandon_handoff(&cache, &id).await.is_err());
    assert!(c.busy());
    c.recover(&cache, &id).await.unwrap();
    let _ = std::fs::remove_file(&fake.recording_path);
}

#[tokio::test]
async fn repair_missing_stop_lifecycle_never_registers_an_acknowledged_path() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut c = production::Controller::default();
    let id = c
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    fake.omit_lifecycle.store(true, Ordering::SeqCst);
    let (root, library) = combined_library();
    assert!(c.candidate_stop(&cache, &library, &id).await.is_err());
    assert!(library.list().unwrap().is_empty());
    let status = c.status(&cache, &combined_connection(addr)).await;
    assert!(status.recovery_required && !status.handoff_pending);
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}

#[tokio::test]
async fn repair_replacement_after_stop_admission_must_not_be_destroyed() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let cache = ObsClientCache::new();
    let mut controller = production::Controller::default();
    // Reserve with the test-only candidate; the actual runtime cannot Start.
    let id = controller
        .candidate_start(
            &cache,
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into(),
        )
        .await
        .unwrap();
    let (root, library) = combined_library();
    fake.replace_on_stop.store(true, Ordering::SeqCst);
    assert!(controller.stop(&cache, &library, &id).await.is_err());
    assert!(
        fake.recording_active.load(Ordering::SeqCst),
        "parameterless StopRecord destroyed the replacement after its admission barrier"
    );
    assert!(!fake
        .request_log
        .lock()
        .await
        .iter()
        .any(|r| r == "StopRecord"));
    assert!(library.list().unwrap().is_empty());
    let _ = std::fs::remove_dir_all(root);
    let _ = std::fs::remove_file(&fake.recording_path);
}
#[tokio::test]
async fn repair_runtime_managed_start_is_fenced_before_any_obs_request() {
    let (addr, fake) = start_fake_obs(Behavior::Normal).await;
    let mut controller = production::Controller::default();
    assert!(controller
        .start(
            &ObsClientCache::new(),
            combined_connection(addr),
            "stream-main".into(),
            "content-main".into()
        )
        .await
        .is_err());
    assert!(fake.request_log.lock().await.is_empty());
    assert!(!controller.busy());
    assert!(production::admit_managed_recording().is_err());
    let _ = std::fs::remove_file(&fake.recording_path);
}

fn r2_key(context: &str, session_id: Option<&str>) -> production::MutationContext {
    production::MutationContext {
        expected_context_id: context.into(),
        session_id: session_id.map(str::to_owned),
    }
}
#[tokio::test]
async fn r2_old_audio_and_scene_cannot_retarget_a_new_idle_endpoint() {
    let (a, fa) = start_fake_obs(Behavior::Normal).await;
    let (b, fb) = start_fake_obs(Behavior::Normal).await;
    let controller = AsyncMutex::new(production::Controller::default());
    let audio = production::inspect_audio(&controller, || Ok(combined_connection(a)))
        .await
        .unwrap();
    let scenes = production::inspect_scenes(&controller, || Ok(combined_connection(a)))
        .await
        .unwrap();
    controller.lock().await.invalidate_idle_observations();
    let loads = AtomicUsize::new(0);
    assert!(production::set_observed_mute(
        &controller,
        || {
            loads.fetch_add(1, Ordering::SeqCst);
            Ok(combined_connection(b))
        },
        r2_key(&audio.context_id, None),
        "Mic",
        true
    )
    .await
    .is_err());
    assert!(production::switch_observed_scene(
        &controller,
        || {
            loads.fetch_add(1, Ordering::SeqCst);
            Ok(combined_connection(b))
        },
        r2_key(&scenes.context_id, None),
        "Starting Soon"
    )
    .await
    .is_err());
    assert_eq!(
        loads.load(Ordering::SeqCst),
        0,
        "stale command consulted settings/vault"
    );
    assert!(
        fb.request_log.lock().await.is_empty(),
        "stale command contacted B"
    );
    assert!(!fa.muted.load(Ordering::SeqCst));
    assert!(!fb.muted.load(Ordering::SeqCst));
    let fresh_audio = production::inspect_audio(&controller, || Ok(combined_connection(b)))
        .await
        .unwrap();
    let fresh_scenes = production::inspect_scenes(&controller, || Ok(combined_connection(b)))
        .await
        .unwrap();
    production::set_observed_mute(
        &controller,
        || Ok(combined_connection(b)),
        r2_key(&fresh_audio.context_id, None),
        "Mic",
        true,
    )
    .await
    .unwrap();
    production::switch_observed_scene(
        &controller,
        || Ok(combined_connection(b)),
        r2_key(&fresh_scenes.context_id, None),
        "Starting Soon",
    )
    .await
    .unwrap();
    assert!(fb.muted.load(Ordering::SeqCst));
    assert_eq!(*fb.current_scene.lock().await, "Starting Soon");
    assert!(!fa.muted.load(Ordering::SeqCst));
    let _ = std::fs::remove_file(&fa.recording_path);
    let _ = std::fs::remove_file(&fb.recording_path);
}
#[tokio::test]
async fn r2_missing_malformed_reconstructed_and_prior_controller_contexts_fail_before_resolution() {
    for json in [
        serde_json::json!({"session_id":null}),
        serde_json::json!({"expected_context_id":null}),
        serde_json::json!({"expected_context_id":4}),
    ] {
        assert!(serde_json::from_value::<production::MutationContext>(json).is_err());
    }
    let controller = AsyncMutex::new(production::Controller::default());
    let old = production::Controller::default().context_id();
    for context in ["", "0:idle", old.as_str()] {
        assert!(production::set_observed_mute(
            &controller,
            || panic!("invalid context read vault"),
            r2_key(context, None),
            "Mic",
            true
        )
        .await
        .is_err());
        assert!(production::switch_observed_scene(
            &controller,
            || panic!("invalid context opened endpoint"),
            r2_key(context, None),
            "Main Scene"
        )
        .await
        .is_err());
    }
    for _change in ["host/port", "same-host credential rotation", "pack change"] {
        let previous = controller.lock().await.context_id();
        controller.lock().await.invalidate_idle_observations();
        assert!(production::set_observed_mute(
            &controller,
            || panic!("changed context read credentials"),
            r2_key(&previous, None),
            "Mic",
            true
        )
        .await
        .is_err());
    }
}
#[tokio::test]
async fn r2_delayed_idle_mutation_is_checked_after_it_acquires_the_lock() {
    let controller = Arc::new(AsyncMutex::new(production::Controller::default()));
    let mut held = controller.lock().await;
    let observed = held.context_id();
    let ready = Arc::new(tokio::sync::Notify::new());
    let task = {
        let c = controller.clone();
        let ready = ready.clone();
        tokio::spawn(async move {
            ready.notify_one();
            production::set_observed_mute(
                &c,
                || panic!("queued old command read new endpoint"),
                r2_key(&observed, None),
                "Mic",
                true,
            )
            .await
        })
    };
    ready.notified().await;
    held.invalidate_idle_observations();
    drop(held);
    assert!(task.await.unwrap().is_err());
}
#[tokio::test]
async fn r2_old_held_inspection_cannot_complete_into_a_new_connection_context() {
    let (a, fa) = start_fake_obs(Behavior::Normal).await;
    let controller = Arc::new(AsyncMutex::new(production::Controller::default()));
    fa.hold_audio.store(true, Ordering::SeqCst);
    let task = {
        let c = controller.clone();
        tokio::spawn(
            async move { production::inspect_audio(&c, || Ok(combined_connection(a))).await },
        )
    };
    fa.audio_entered.notified().await;
    controller.lock().await.invalidate_idle_observations();
    fa.audio_release.notify_one();
    assert!(task.await.unwrap().is_err());
    let _ = std::fs::remove_file(&fa.recording_path);
}
#[tokio::test]
async fn r2_pinned_mutations_keep_their_observation_and_skip_corrupt_idle_settings() {
    let (a, fa) = start_fake_obs(Behavior::Normal).await;
    let controller = AsyncMutex::new(production::Controller::default());
    let receipt = controller
        .lock()
        .await
        .candidate_start(
            &ObsClientCache::new(),
            combined_connection(a),
            "agent-labs".into(),
            "opentech-marketing".into(),
        )
        .await
        .unwrap();
    let observed = production::inspect_audio(&controller, || {
        Err("corrupt preferences/locked vault".into())
    })
    .await
    .unwrap();
    controller.lock().await.invalidate_idle_observations(); // safe Content-pack change must keep pin context
    assert_eq!(observed.context_id, controller.lock().await.context_id());
    production::set_observed_mute(
        &controller,
        || panic!("pinned mutation read corrupt idle settings"),
        r2_key(&observed.context_id, Some(&receipt.session_id)),
        "Mic",
        true,
    )
    .await
    .unwrap();
    production::switch_observed_scene(
        &controller,
        || panic!("pinned scene read vault"),
        r2_key(&observed.context_id, Some(&receipt.session_id)),
        "Starting Soon",
    )
    .await
    .unwrap();
    assert!(production::set_observed_mute(
        &controller,
        || panic!("wrong generation read vault"),
        r2_key(&observed.context_id, None),
        "Mic",
        false
    )
    .await
    .is_err());
    assert!(fa.muted.load(Ordering::SeqCst));
    let _ = std::fs::remove_file(&fa.recording_path);
}

#[tokio::test]
async fn r2_mutation_admitted_before_settings_change_finishes_on_a_then_revokes_the_old_key() {
    let (a, fa) = start_fake_obs(Behavior::Normal).await;
    let (b, fb) = start_fake_obs(Behavior::Normal).await;
    let controller = Arc::new(AsyncMutex::new(production::Controller::default()));
    let audio = production::inspect_audio(&controller, || Ok(combined_connection(a)))
        .await
        .unwrap();
    let context = audio.context_id.clone();
    fa.hold_mute.store(true, Ordering::SeqCst);
    let task = {
        let c = controller.clone();
        tokio::spawn(async move {
            production::set_observed_mute(
                &c,
                || Ok(combined_connection(a)),
                r2_key(&context, None),
                "Mic",
                true,
            )
            .await
        })
    };
    fa.mute_entered.notified().await;
    assert!(
        controller.try_lock().is_err(),
        "mutation released connection lock before completion"
    );
    fa.mute_release.notify_one();
    task.await.unwrap().unwrap();
    controller.lock().await.invalidate_idle_observations();
    assert!(production::set_observed_mute(
        &controller,
        || Ok(combined_connection(b)),
        r2_key(&audio.context_id, None),
        "Mic",
        false
    )
    .await
    .is_err());
    assert!(fa.muted.load(Ordering::SeqCst));
    assert!(fb.request_log.lock().await.is_empty());
    let _ = std::fs::remove_file(&fa.recording_path);
    let _ = std::fs::remove_file(&fb.recording_path);
}

#[tokio::test]
async fn r2_stale_scene_alone_cannot_contact_or_mutate_the_new_target() {
    let (a, fa) = start_fake_obs(Behavior::Normal).await;
    let (b, fb) = start_fake_obs(Behavior::Normal).await;
    let controller = AsyncMutex::new(production::Controller::default());
    let observed = production::inspect_scenes(&controller, || Ok(combined_connection(a)))
        .await
        .unwrap();
    controller.lock().await.invalidate_idle_observations();
    let loads = AtomicUsize::new(0);
    assert!(production::switch_observed_scene(
        &controller,
        || {
            loads.fetch_add(1, Ordering::SeqCst);
            Ok(combined_connection(b))
        },
        r2_key(&observed.context_id, None),
        "Starting Soon"
    )
    .await
    .is_err());
    assert_eq!(loads.load(Ordering::SeqCst), 0);
    assert!(fb.request_log.lock().await.is_empty());
    assert_eq!(*fb.current_scene.lock().await, "Main Scene");
    let _ = std::fs::remove_file(&fa.recording_path);
    let _ = std::fs::remove_file(&fb.recording_path);
}
