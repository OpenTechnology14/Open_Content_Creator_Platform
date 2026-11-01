//! OBS WebSocket client for Stream Extend.
//!
//! Wraps obs-websocket v5 via the `obws` crate. `obws` pulls in
//! `tokio-websockets`, not `tokio-tungstenite` (the stack `relay-client`
//! already uses) — a second, disclosed WS stack in this binary, not a
//! silently-absorbed one.

use std::{path::Path, time::Duration};

use command_error::ErrorEnvelope;
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex as AsyncMutex;

const CONNECT_TIMEOUT: Duration = Duration::from_secs(5);
const REQUEST_TIMEOUT: Duration = Duration::from_secs(8);

/// Lazily-established, shared OBS connection. `obws::Client` is Send+Sync
/// but not `Clone`, so this cache — not the client itself — is what gets
/// `Arc`'d around to the Tauri commands and (later) `StreamRelayManager`.
pub struct ObsClientCache(AsyncMutex<Option<obws::Client>>);

impl ObsClientCache {
    pub fn new() -> Self {
        Self(AsyncMutex::new(None))
    }

    /// Drops the cached connection — called by `set_config` when
    /// host/port/password actually change, so the next request reconnects
    /// with the new credentials instead of reusing a stale client.
    pub async fn clear(&self) {
        *self.0.lock().await = None;
    }
}

impl Default for ObsClientCache {
    fn default() -> Self {
        Self::new()
    }
}

/// In-memory ownership marker for one live session started by this app.
/// It intentionally does not survive a crash: after restart Stream Extend
/// must not claim or stop recording work it can no longer prove it owns.
pub struct ObsSessionState(AsyncMutex<Option<OwnedSession>>);

#[derive(Debug, Clone)]
struct OwnedSession {
    recording_owned: bool,
    source_profile_id: Option<String>,
    content_profile_id: Option<String>,
}

impl ObsSessionState {
    pub fn new() -> Self {
        Self(AsyncMutex::new(None))
    }
}

impl ObsSessionState {
    pub async fn is_owned(&self) -> bool {
        self.0.lock().await.is_some()
    }
}

impl Default for ObsSessionState {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObsStatus {
    pub connected: bool,
    pub obs_version: Option<String>,
    pub ws_version: Option<String>,
    pub platform: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObsConnectionDiagnostic {
    pub state: String,
    pub detail: String,
    pub host: String,
    pub port: u16,
    pub obs_version: Option<String>,
    pub websocket_version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObsRecordingReport {
    pub accepted: bool,
    pub duration_seconds: u64,
    pub bytes: u64,
    pub file_name: Option<String>,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamStatus {
    pub active: bool,
    pub reconnecting: bool,
    pub timecode: Option<String>,
    pub bytes: u64,
    pub kbits_per_sec: f64,
    pub total_frames: u32,
    pub skipped_frames: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveSessionResult {
    pub stream_active: bool,
    pub recording_active: bool,
    pub recording_owned: bool,
    pub recording_path: Option<String>,
    pub source_profile_id: Option<String>,
    pub content_profile_id: Option<String>,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SceneInfo {
    pub name: String,
    pub index: usize,
    pub is_current: bool,
}

async fn connect(
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<obws::Client, ErrorEnvelope> {
    tokio::time::timeout(CONNECT_TIMEOUT, obws::Client::connect(host, port, password))
        .await
        .map_err(|_| ErrorEnvelope::timeout(format!("connecting to OBS at {host}:{port}")))?
        .map_err(|e| map_obs_err(e, "connecting to OBS"))
}

pub async fn diagnose_connection(
    host: &str,
    port: u16,
    password: Option<&str>,
) -> ObsConnectionDiagnostic {
    let base = |state: &str, detail: String| ObsConnectionDiagnostic {
        state: state.into(),
        detail,
        host: host.into(),
        port,
        obs_version: None,
        websocket_version: None,
    };
    let client = match tokio::time::timeout(
        CONNECT_TIMEOUT,
        obws::Client::connect(host, port, password),
    )
    .await
    {
        Err(_) => {
            return base(
                "websocket_unreachable",
                format!("Timed out connecting to OBS WebSocket at {host}:{port}."),
            )
        }
        Ok(Err(obws::error::Error::Handshake(
            obws::client::HandshakeError::ConnectionClosed(Some(details)),
        ))) if u16::from(details.code)
            == u16::from(obws::responses::WebSocketCloseCode::AuthenticationFailed) =>
        {
            return base(
                "authentication_failed",
                "OBS rejected the saved WebSocket password. Update it in Connections and retry."
                    .into(),
            )
        }
        Ok(Err(
            obws::error::Error::ObsStudioVersion(_, _)
            | obws::error::Error::ObsWebsocketVersion(_, _)
            | obws::error::Error::RpcVersion { .. },
        )) => {
            return base(
                "incompatible",
                "OBS or obs-websocket is incompatible with this app. Update OBS Studio and retry."
                    .into(),
            )
        }
        Ok(Err(obws::error::Error::Handshake(_))) => {
            return base(
                "handshake_failed",
                "OBS answered but the WebSocket handshake failed. Check authentication and WebSocket settings."
                    .into(),
            )
        }
        Ok(Err(_)) => {
            return base(
                "websocket_unreachable",
                format!("OBS WebSocket did not answer at {host}:{port}. Enable it in OBS Tools → WebSocket Server Settings."),
            )
        }
        Ok(Ok(client)) => client,
    };
    match client.general().version().await {
        Ok(version) => ObsConnectionDiagnostic {
            state: "connected".into(),
            detail: "Authenticated to OBS WebSocket and read its version.".into(),
            host: host.into(),
            port,
            obs_version: Some(version.obs_studio_version.to_string()),
            websocket_version: Some(version.obs_web_socket_version.to_string()),
        },
        Err(_) => base(
            "handshake_failed",
            "OBS connected but its version check failed. Recheck WebSocket settings.".into(),
        ),
    }
}

pub async fn run_recording_test(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
    duration: Duration,
) -> Result<ObsRecordingReport, ErrorEnvelope> {
    let status = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.recording().status().await })
    })
    .await?;
    if status.active {
        return Err(ErrorEnvelope::invalid_request(
            "OBS is already recording. Stop it before running the bounded setup test.",
        ));
    }
    with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.recording().start().await })
    })
    .await?;
    tokio::time::sleep(duration).await;
    let path = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.recording().stop().await })
    })
    .await
    .map_err(|_| {
        ErrorEnvelope::internal(
            "OBS did not confirm that the test recording stopped. Stop recording in OBS before retrying.",
        )
    })?;
    let bytes = std::fs::metadata(&path)
        .map(|value| value.len())
        .unwrap_or(0);
    let file_name = Path::new(&path)
        .file_name()
        .and_then(|value| value.to_str())
        .map(str::to_string);
    let accepted = !path.is_empty() && bytes > 0;
    Ok(ObsRecordingReport {
        accepted,
        duration_seconds: duration.as_secs(),
        bytes,
        file_name,
        detail: if accepted {
            "OBS finalized a non-empty local recording. Review picture and audio before streaming."
                .into()
        } else {
            "OBS stopped the test, but the returned recording file was missing or empty.".into()
        },
    })
}

/// Maps a real `obws::error::Error` to our stable envelope. `Handshake`
/// covers both a wrong password and an RPC-version mismatch —
/// `command-error`'s `ErrorCode` has no dedicated `Unauthorized` variant
/// despite `PROPOSAL_RELEASE_GAP_CLOSURE.md` §7.1 listing one as allowed (a
/// pre-existing gap in the shared crate); using `InvalidRequest` here rather
/// than expanding shared infrastructure in this PR.
fn map_obs_err(e: obws::error::Error, context: &str) -> ErrorEnvelope {
    match e {
        obws::error::Error::Connect(_) => {
            ErrorEnvelope::dependency_unreachable(format!("{context}: {e}"))
        }
        obws::error::Error::Timeout => ErrorEnvelope::timeout(format!("{context}: {e}")),
        obws::error::Error::Handshake(_) => ErrorEnvelope::invalid_request(format!(
            "{context}: {e} (check the OBS WebSocket password)"
        )),
        obws::error::Error::Api { code, message } => ErrorEnvelope::invalid_request(format!(
            "{context}: OBS rejected the request (code {code:?}): {message:?}"
        )),
        _ => ErrorEnvelope::dependency_unreachable(format!("{context}: {e}")),
    }
}

/// Ensures `cache` holds a live client, connecting if it doesn't. Does not
/// retry a request failure on its own — `with_client` below owns the
/// drop-and-retry-once behavior for an already-connected-but-now-stale
/// client.
async fn get_or_connect<'a>(
    cache: &'a ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<tokio::sync::MutexGuard<'a, Option<obws::Client>>, ErrorEnvelope> {
    let mut guard = cache.0.lock().await;
    if guard.is_none() {
        *guard = Some(connect(host, port, password).await?);
    }
    Ok(guard)
}

/// Runs `f` against a live client, retrying once (dropping the stale client
/// and reconnecting) if the first attempt fails with anything other than
/// our own request timeout. This is the load-bearing piece that turns a
/// dropped mid-session connection into a self-healing next call instead of
/// a permanent failure.
async fn with_client<T, F>(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
    f: F,
) -> Result<T, ErrorEnvelope>
where
    F: for<'c> Fn(
        &'c obws::Client,
    ) -> std::pin::Pin<
        Box<dyn std::future::Future<Output = Result<T, obws::error::Error>> + Send + 'c>,
    >,
{
    {
        let guard = get_or_connect(cache, host, port, password).await?;
        let client = guard.as_ref().expect("just connected");
        match tokio::time::timeout(REQUEST_TIMEOUT, f(client)).await {
            Ok(Ok(value)) => return Ok(value),
            Ok(Err(_)) => {} // fall through to drop + retry below
            Err(_) => return Err(ErrorEnvelope::timeout("waiting for OBS to respond")),
        }
    }

    // The cached client errored on a real request (not our timeout) — treat
    // it as stale, drop it, and retry once against a fresh connection.
    cache.clear().await;
    let guard = get_or_connect(cache, host, port, password).await?;
    let client = guard.as_ref().expect("just connected");
    tokio::time::timeout(REQUEST_TIMEOUT, f(client))
        .await
        .map_err(|_| ErrorEnvelope::timeout("waiting for OBS to respond"))?
        .map_err(|e| map_obs_err(e, "sending request to OBS"))
}

/// Get OBS connection status. Polled every ~2s by the frontend — must never
/// surface an error UI on the routine "OBS isn't open yet," so every
/// failure degrades to `connected: false` instead of propagating.
pub async fn get_status(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> ObsStatus {
    let result = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.general().version().await })
    })
    .await;

    match result {
        Ok(version) => ObsStatus {
            connected: true,
            obs_version: Some(version.obs_studio_version.to_string()),
            ws_version: Some(version.obs_web_socket_version.to_string()),
            platform: Some(version.platform),
        },
        Err(_) => ObsStatus {
            connected: false,
            obs_version: None,
            ws_version: None,
            platform: None,
        },
    }
}

fn to_scene_infos(scenes: obws::responses::scenes::Scenes) -> Vec<SceneInfo> {
    let current_name = scenes
        .current_program_scene
        .as_ref()
        .map(|s| s.name.clone());
    scenes
        .scenes
        .into_iter()
        .map(|s| {
            let is_current = current_name.as_deref() == Some(s.id.name.as_str());
            SceneInfo {
                name: s.id.name,
                index: s.index,
                is_current,
            }
        })
        .collect()
}

pub async fn get_scenes(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<Vec<SceneInfo>, ErrorEnvelope> {
    let scenes = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.scenes().list().await })
    })
    .await?;
    Ok(to_scene_infos(scenes))
}

/// Switches the current program scene and returns the freshly-observed
/// scene list. `SetCurrentProgramScene` has zero response fields (confirmed
/// against the real obs-websocket v5 protocol spec) — the only real
/// "observed result" is a follow-up scene list, not `Ok(())`.
pub async fn switch_scene(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
    scene_name: &str,
) -> Result<Vec<SceneInfo>, ErrorEnvelope> {
    let name = scene_name.to_string();
    with_client(cache, host, port, password, move |client| {
        let name = name.clone();
        Box::pin(async move {
            client
                .scenes()
                .set_current_program_scene(name.as_str())
                .await
        })
    })
    .await?;

    get_scenes(cache, host, port, password).await
}

// obws reports `timecode`/`duration` as `time::Duration` (a signed
// duration), not `std::time::Duration` — matching its real response type
// here rather than converting at every call site.
fn derive_kbits_per_sec(bytes: u64, duration: time::Duration) -> f64 {
    let secs = duration.as_seconds_f64();
    if secs <= 0.0 {
        return 0.0;
    }
    (bytes as f64 * 8.0 / 1000.0) / secs
}

fn format_timecode(d: time::Duration) -> String {
    let total_secs = d.whole_seconds().max(0);
    let h = total_secs / 3600;
    let m = (total_secs % 3600) / 60;
    let s = total_secs % 60;
    format!("{h:02}:{m:02}:{s:02}")
}

pub async fn get_stream_status(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<StreamStatus, ErrorEnvelope> {
    let status = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().status().await })
    })
    .await?;

    Ok(StreamStatus {
        active: status.active,
        reconnecting: status.reconnecting,
        timecode: Some(format_timecode(status.timecode)),
        bytes: status.bytes,
        // Average since stream start, not a live sliding-window rate — a
        // real delta would need state carried between polls, deliberately
        // out of scope here.
        kbits_per_sec: derive_kbits_per_sec(status.bytes, status.duration),
        total_frames: status.total_frames,
        skipped_frames: status.skipped_frames,
    })
}

/// Toggles streaming. `obws`'s `.toggle()` already returns the new
/// authoritative active-state bool directly from OBS's own response — no
/// extra re-read needed, unlike `switch_scene`.
pub async fn toggle_stream(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<bool, ErrorEnvelope> {
    with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().toggle().await })
    })
    .await
}

pub async fn outputs_inactive(
    cache: &ObsClientCache,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<bool, ErrorEnvelope> {
    let streaming = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().status().await })
    })
    .await?;
    let recording = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.recording().status().await })
    })
    .await?;
    Ok(!streaming.active && !recording.active)
}

pub async fn start_live_session(
    cache: &ObsClientCache,
    session: &ObsSessionState,
    host: &str,
    port: u16,
    password: Option<&str>,
    source_profile_id: Option<String>,
    content_profile_id: Option<String>,
) -> Result<LiveSessionResult, ErrorEnvelope> {
    let mut owned = session.0.lock().await;
    if owned.is_some() {
        return Err(ErrorEnvelope::invalid_request(
            "Stream Extend already owns a live session.",
        ));
    }
    let stream_status = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().status().await })
    })
    .await?;
    if stream_status.active {
        return Err(ErrorEnvelope::invalid_request(
            "OBS is already streaming. Stop it before starting a managed Stream Extend session.",
        ));
    }
    let record_status = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.recording().status().await })
    })
    .await?;
    let recording_owned = !record_status.active;
    if recording_owned {
        with_client(cache, host, port, password, |client| {
            Box::pin(async move { client.recording().start().await })
        })
        .await?;
    }
    let stream_start = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().start().await })
    })
    .await;
    if let Err(error) = stream_start {
        if recording_owned {
            let _ = with_client(cache, host, port, password, |client| {
                Box::pin(async move { client.recording().stop().await })
            })
            .await;
        }
        return Err(error);
    }
    *owned = Some(OwnedSession {
        recording_owned,
        source_profile_id: source_profile_id.clone(),
        content_profile_id: content_profile_id.clone(),
    });
    Ok(LiveSessionResult {
        stream_active: true,
        recording_active: true,
        recording_owned,
        recording_path: None,
        source_profile_id,
        content_profile_id,
        detail: if recording_owned {
            "Live session started. Stream Extend is recording locally for Creator Extend.".into()
        } else {
            "Live session started. OBS was already recording, so Stream Extend will not stop or claim that recording.".into()
        },
    })
}

pub async fn stop_live_session(
    cache: &ObsClientCache,
    session: &ObsSessionState,
    host: &str,
    port: u16,
    password: Option<&str>,
) -> Result<LiveSessionResult, ErrorEnvelope> {
    let mut owned = session.0.lock().await;
    let session_record = owned.clone();
    let stream_status = with_client(cache, host, port, password, |client| {
        Box::pin(async move { client.streaming().status().await })
    })
    .await?;
    if stream_status.active {
        with_client(cache, host, port, password, |client| {
            Box::pin(async move { client.streaming().stop().await })
        })
        .await?;
    }

    let recording_path = if session_record
        .as_ref()
        .is_some_and(|value| value.recording_owned)
    {
        Some(
            with_client(cache, host, port, password, |client| {
                Box::pin(async move { client.recording().stop().await })
            })
            .await
            .map_err(|_| {
                ErrorEnvelope::internal(
                    "The stream stopped, but OBS did not confirm recording finalization. Stop recording in OBS and import the file in Creator Extend.",
                )
            })?,
        )
    } else {
        None
    };
    *owned = None;
    let recording_owned = session_record
        .as_ref()
        .is_some_and(|value| value.recording_owned);
    Ok(LiveSessionResult {
        stream_active: false,
        recording_active: session_record.is_none() || !recording_owned,
        recording_owned,
        recording_path,
        source_profile_id: session_record
            .as_ref()
            .and_then(|value| value.source_profile_id.clone()),
        content_profile_id: session_record
            .as_ref()
            .and_then(|value| value.content_profile_id.clone()),
        detail: if recording_owned {
            "Stream and owned recording stopped; OBS returned the finalized local file.".into()
        } else if session_record.is_some() {
            "Stream stopped. The pre-existing OBS recording was left running and was not claimed."
                .into()
        } else {
            "Stream stopped. This app did not own a recording for the session.".into()
        },
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use command_error::ErrorCode;

    #[test]
    fn derive_kbits_per_sec_computes_the_average_rate() {
        // 1,000,000 bytes over 8 seconds = 1,000,000*8/1000 / 8 = 1000 kbit/s
        let kbps = derive_kbits_per_sec(1_000_000, time::Duration::seconds(8));
        assert!((kbps - 1000.0).abs() < 0.001);
    }

    #[test]
    fn derive_kbits_per_sec_is_zero_for_a_zero_duration() {
        assert_eq!(derive_kbits_per_sec(1_000_000, time::Duration::ZERO), 0.0);
    }

    #[test]
    fn format_timecode_pads_to_two_digits() {
        assert_eq!(format_timecode(time::Duration::seconds(5)), "00:00:05");
        assert_eq!(format_timecode(time::Duration::seconds(3661)), "01:01:01");
    }

    #[test]
    fn map_obs_err_maps_api_rejection_to_invalid_request() {
        let err = map_obs_err(
            obws::error::Error::Api {
                code: obws::responses::StatusCode::ResourceNotFound,
                message: Some("no such scene".into()),
            },
            "test",
        );
        assert_eq!(err.code, ErrorCode::InvalidRequest);
    }
}
