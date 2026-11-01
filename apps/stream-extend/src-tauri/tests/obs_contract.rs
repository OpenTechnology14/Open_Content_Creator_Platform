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
            .join(format!("hcp-obs-recording-{}.mkv", std::process::id()))
            .to_string_lossy()
            .into_owned(),
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
            if !handshake(&mut ws).await {
                continue;
            }

            match behavior {
                Behavior::Normal => serve_normally(&mut ws, &state_task, usize::MAX).await,
                Behavior::HangAfterConnect if first_connection => {
                    first_connection = false;
                    serve_normally(&mut ws, &state_task, 1).await; // the connect-time GetVersion
                    let _ = ws.next().await; // read the real request, then hang without responding
                    std::future::pending::<()>().await;
                }
                Behavior::HangAfterConnect => {
                    serve_normally(&mut ws, &state_task, usize::MAX).await
                }
                Behavior::DropAfterFirstRealRequest if first_connection => {
                    first_connection = false;
                    serve_normally(&mut ws, &state_task, 2).await; // connect-time GetVersion + first real request
                    let _ = ws.next().await; // read the next request, then drop without responding
                }
                Behavior::DropAfterFirstRealRequest => {
                    serve_normally(&mut ws, &state_task, usize::MAX).await
                }
                Behavior::AuthenticationRejected => unreachable!(),
            }
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

async fn handshake(ws: &mut WebSocketStream<TcpStream>) -> bool {
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

    let identified = json!({ "op": 2, "d": { "negotiatedRpcVersion": 1 } });
    ws.send(Message::Text(identified.to_string())).await.is_ok()
}

async fn serve_normally(
    ws: &mut WebSocketStream<TcpStream>,
    state: &FakeState,
    max_requests: usize,
) {
    let mut served = 0usize;
    loop {
        if served >= max_requests {
            return;
        }
        let Some(Ok(msg)) = ws.next().await else {
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
        "GetRecordStatus" => Some(json!({
            "outputActive": state.recording_active.load(Ordering::SeqCst),
            "outputPaused": false,
            "outputTimecode": "00:00:00.000",
            "outputDuration": 0,
            "outputBytes": 0,
        })),
        "StartRecord" => None,
        "StopRecord" => Some(json!({ "outputPath": state.recording_path })),
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
