//! In-memory, application-owned OBS task controller. No page owns a session.
use crate::{obs, preferences::Preferences};
use recording_library::{RecordingLibrary, RecordingOrigin};
use serde::{Deserialize, Serialize};

fn new_generation() -> String {
    static NEXT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(1);
    format!(
        "{}-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos(),
        NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
    )
}

pub const MANAGED_RECORDING_BLOCKED: &str = "Managed recording is unavailable: OBS StopRecord cannot check the recording generation atomically. Start and finish recordings in OBS, then use validated manual import. No output will be adopted.";
pub fn admit_managed_recording() -> Result<(), String> {
    Err(MANAGED_RECORDING_BLOCKED.into())
}

const OBS_ERROR: &str =
    "OBS could not confirm the request. Refresh status; use manual inactive recovery if continuity is lost.";

// Never serialized or logged. Active commands use this pinned connection even
// if the selected profiles or presentation change in another part of the app.
#[derive(Clone)]
pub struct Connection {
    pub host: String,
    pub port: u16,
    pub password: Option<String>,
}
struct Pinned {
    id: String,
    connection: Connection,
    source: String,
    content: String,
}

pub struct Controller {
    session: obs::LocalRecordingState,
    pinned: Option<Pinned>,
    pending: Option<obs::LiveSessionResult>,
    revision: u64,
    context_epoch: String,
}

impl Default for Controller {
    fn default() -> Self {
        Self {
            session: obs::LocalRecordingState::default(),
            pinned: None,
            pending: None,
            revision: 0,
            context_epoch: new_generation(),
        }
    }
}
// Context is a native state identity, not a credential. Never infer it from
// session_id=null: each controller lifetime and idle connection revision differ.
#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MutationContext {
    pub expected_context_id: String,
    pub session_id: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Status {
    pub session_id: Option<String>,
    pub context_id: String,
    pub managed_recording_available: bool,
    pub connected: bool,
    pub stream_active: Option<bool>,
    pub recording_active: Option<bool>,
    pub owned: bool,
    pub recovery_required: bool,
    pub handoff_pending: bool,
    pub source_profile_id: Option<String>,
    pub content_profile_id: Option<String>,
}

impl Controller {
    pub fn require_generation(&self, expected: Option<&str>) -> Result<(), String> {
        if self.pinned.as_ref().map(|p| p.id.as_str()) != expected {
            return Err("Session changed; refresh OBS controls before retrying".into());
        }
        Ok(())
    }
    pub fn busy(&self) -> bool {
        self.pinned.is_some()
    }
    pub fn allow_preferences(
        &self,
        current: &Preferences,
        next: &Preferences,
    ) -> Result<(), String> {
        if self.busy()
            && (next.require_pack("stream").is_err()
                || current.obs_host != next.obs_host
                || current.obs_port != next.obs_port)
        {
            return Err("Finish or recover the OBS session before disabling Stream or changing its connection".into());
        }
        Ok(())
    }
    pub fn allow_password_change(&self) -> Result<(), String> {
        if self.busy() {
            return Err("Finish or recover the OBS session before changing its password".into());
        }
        Ok(())
    }
    #[cfg(test)]
    pub fn connection<'a>(&'a self, fallback: &'a Connection) -> &'a Connection {
        self.pinned
            .as_ref()
            .map(|p| &p.connection)
            .unwrap_or(fallback)
    }
    pub fn resolve_connection(
        &self,
        load: impl FnOnce() -> Result<Connection, String>,
    ) -> Result<Connection, String> {
        if let Some(pinned) = &self.pinned {
            return Ok(pinned.connection.clone());
        }
        load()
    }
    #[cfg(test)]
    pub fn test_reservation(connection: Connection) -> Self {
        Self {
            pinned: Some(Pinned {
                id: "test-reservation".into(),
                connection,
                source: "stream-main".into(),
                content: "content-main".into(),
            }),
            ..Default::default()
        }
    }
    pub fn context_id(&self) -> String {
        format!(
            "{}:{}:{}",
            self.context_epoch,
            self.revision,
            self.pinned
                .as_ref()
                .map(|p| p.id.as_str())
                .unwrap_or("idle")
        )
    }
    pub fn invalidate_idle_observations(&mut self) {
        if !self.busy() {
            self.invalidate_observations();
        }
    }
    pub fn admit_observed_mutation(&self, expected: &MutationContext) -> Result<(), String> {
        self.require_context(&expected.expected_context_id)?;
        self.require_generation(expected.session_id.as_deref())
    }
    pub fn invalidate_observations(&mut self) {
        self.revision = self.revision.wrapping_add(1);
    }
    async fn snapshot(
        &self,
        load: impl FnOnce() -> Result<Connection, String>,
    ) -> Result<(Connection, Status), String> {
        let connection = self.resolve_connection(load)?;
        let owned = self.session.is_owned().await;
        Ok((
            connection,
            Status {
                session_id: self.pinned.as_ref().map(|p| p.id.clone()),
                context_id: self.context_id(),
                managed_recording_available: false,
                connected: false,
                stream_active: None,
                recording_active: None,
                owned,
                recovery_required: self.pinned.is_some() && !owned && self.pending.is_none(),
                handoff_pending: self.pending.is_some(),
                source_profile_id: self.pinned.as_ref().map(|p| p.source.clone()),
                content_profile_id: self.pinned.as_ref().map(|p| p.content.clone()),
            },
        ))
    }
    // Compatibility for protocol tests; native commands use observe_status
    // below, which releases the root controller lock before any network read.
    #[cfg(test)]
    pub async fn status(&self, _cache: &obs::ObsClientCache, fallback: &Connection) -> Status {
        let (connection, status) = self
            .snapshot(|| Ok(fallback.clone()))
            .await
            .expect("provided fallback");
        observe_connection(connection, status).await
    }
    pub async fn start(
        &mut self,
        _cache: &obs::ObsClientCache,
        _connection: Connection,
        _source: String,
        _content: String,
    ) -> Result<StartReceipt, String> {
        // No managed output may be started without a safe completion contract.
        admit_managed_recording()?;
        unreachable!("managed recording admission is fenced")
    }
    // Protocol candidate only. Never called by the application/native handler.
    // Its continuous witness is useful evidence, but cannot make Stop atomic.
    #[cfg(test)]
    pub async fn candidate_start(
        &mut self,
        cache: &obs::ObsClientCache,
        connection: Connection,
        source: String,
        content: String,
    ) -> Result<StartReceipt, String> {
        if self.busy() {
            return Err("Finish or recover the current OBS session first".into());
        }
        // Reject external outputs before reserving an attempted session. No
        // pre-existing recording/stream is ever adopted, stopped or registered.
        if !obs::outputs_inactive(
            cache,
            &connection.host,
            connection.port,
            connection.password.as_deref(),
        )
        .await
        .map_err(|_| OBS_ERROR)?
        {
            return Err("OBS has external active outputs. Stop them in OBS before starting a local recording".into());
        }
        self.pinned = Some(Pinned {
            id: new_generation(),
            connection,
            source,
            content,
        });
        let pinned = self.pinned.as_ref().expect("reserved");
        let confirmed = obs::start_owned_recording(
            cache,
            &self.session,
            &pinned.connection.host,
            pinned.connection.port,
            pinned.connection.password.as_deref(),
            pinned.source.clone(),
            pinned.content.clone(),
        )
        .await
        .is_ok();
        // Return reservation identity even for an unknown start outcome. This
        // enables recovery when the next observation itself fails.
        Ok(StartReceipt {
            session_id: pinned.id.clone(),
            context_id: self.context_id(),
            confirmed,
            source_profile_id: pinned.source.clone(),
            content_profile_id: pinned.content.clone(),
        })
    }

    pub async fn stop(
        &mut self,
        _cache: &obs::ObsClientCache,
        library: &RecordingLibrary,
        expected: &str,
    ) -> Result<String, String> {
        self.require_generation(Some(expected))?;
        // Only retry a previously finalized inbox handoff. Never dispatch an
        // unconditional StopRecord, including for continuously observed output.
        if self.pending.is_none() {
            return Err(MANAGED_RECORDING_BLOCKED.into());
        }
        self.complete_handoff(library)
    }
    #[cfg(test)]
    pub async fn candidate_stop(
        &mut self,
        cache: &obs::ObsClientCache,
        library: &RecordingLibrary,
        expected: &str,
    ) -> Result<String, String> {
        self.require_generation(Some(expected))?;
        let pinned = self
            .pinned
            .as_ref()
            .ok_or("No owned recording; external outputs must be controlled in OBS")?;
        if self.pending.is_none() {
            if !self.session.is_owned().await {
                return Err("Recording continuity is unproven. Inspect/stop output in OBS, then recover when inactive; no external file will be attributed".into());
            }
            self.pending = Some(
                obs::stop_owned_recording(
                    cache,
                    &self.session,
                    &pinned.connection.host,
                    pinned.connection.port,
                    pinned.connection.password.as_deref(),
                )
                .await
                .map_err(|_| OBS_ERROR)?,
            );
        }
        self.complete_handoff(library)
    }
    fn complete_handoff(&mut self, library: &RecordingLibrary) -> Result<String, String> {
        let result = self.pending.as_ref().expect("finalized");
        let detail = if let Some(path) = &result.recording_path {
            // Keep finalized path and attribution on registration failure. Retry
            // registers the same file, never sends a second StopRecord request.
            library
                .register(
                    path,
                    RecordingOrigin::StreamSession,
                    result.source_profile_id.as_deref(),
                    result.content_profile_id.as_deref(),
                )
                .map_err(|_| {
                    "Recording finalized; inbox registration needs retry. The file remains local."
                })?;
            "Recording is ready in the shared media library"
        } else {
            "OBS is no longer recording. No file was claimed; import the finalized file manually"
        };
        self.pending = None;
        self.pinned = None;
        self.invalidate_observations();
        Ok(detail.into())
    }
    pub async fn recover(
        &mut self,
        cache: &obs::ObsClientCache,
        expected: &str,
    ) -> Result<(), String> {
        self.require_generation(Some(expected))?;
        let pinned = self.pinned.as_ref().ok_or("No session needs recovery")?;
        if self.session.is_owned().await || self.pending.is_some() {
            return Err("Use Stop or retry inbox registration for this owned session".into());
        }
        if !obs::outputs_inactive(
            cache,
            &pinned.connection.host,
            pinned.connection.port,
            pinned.connection.password.as_deref(),
        )
        .await
        .map_err(|_| OBS_ERROR)?
        {
            return Err("Inspect and stop the unconfirmed output in OBS before recovery".into());
        }
        self.session.clear().await;
        self.pinned = None;
        self.invalidate_observations();
        Ok(())
    }
    pub async fn abandon_handoff(
        &mut self,
        cache: &obs::ObsClientCache,
        expected: &str,
    ) -> Result<String, String> {
        self.require_generation(Some(expected))?;
        if self.pending.is_none() || self.session.is_owned().await {
            return Err("Only a finalized handoff can be left for manual import".into());
        }
        let pinned = self.pinned.as_ref().ok_or("No finalized handoff")?;
        if !obs::outputs_inactive(
            cache,
            &pinned.connection.host,
            pinned.connection.port,
            pinned.connection.password.as_deref(),
        )
        .await
        .map_err(|_| OBS_ERROR)?
        {
            return Err(
                "Verify OBS outputs are inactive before leaving this handoff for manual import"
                    .into(),
            );
        }
        let detail = format!("Inbox handoff abandoned. No file was registered, deleted or changed. Import the existing file manually; original source profile: {}, Content profile: {}.", pinned.source, pinned.content);
        self.session.clear().await;
        self.pending = None;
        self.pinned = None;
        self.invalidate_observations();
        Ok(detail)
    }
}

/// Defense in depth beyond the app ACL: only the named local main WebView
/// may use operational commands. No wildcard origins or arbitrary dev ports.
pub fn admit(label: &str, url: &url::Url) -> Result<(), String> {
    let packaged = matches!(
        (url.scheme(), url.host_str(), url.port()),
        ("tauri", Some("localhost"), None) | ("http" | "https", Some("tauri.localhost"), None)
    );
    let development =
        cfg!(debug_assertions) && url.origin().ascii_serialization() == "http://localhost:5175";
    if label != "main"
        || !url.username().is_empty()
        || url.password().is_some()
        || !(packaged || development)
    {
        return Err("OBS control requires the trusted local main window".into());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn foreign_origins_and_windows_cannot_invoke_operational_commands() {
        assert!(admit("main", &url::Url::parse("tauri://localhost/").unwrap()).is_ok());
        for (label, url) in [
            ("other", "tauri://localhost/"),
            ("main", "https://example.invalid/"),
            ("main", "http://localhost:5176/"),
            ("main", "tauri://localhost.evil/"),
            ("main", "tauri://secret@localhost/"),
        ] {
            assert!(admit(label, &url::Url::parse(url).unwrap()).is_err());
        }
    }
    #[test]
    fn repair_pinned_connection_never_reads_corrupt_preferences_or_locked_vault() {
        let controller = Controller {
            pinned: Some(Pinned {
                id: "owned".into(),
                connection: Connection {
                    host: "pinned.test".into(),
                    port: 4455,
                    password: Some("synthetic-private".into()),
                },
                source: "stream-main".into(),
                content: "content-main".into(),
            }),
            ..Default::default()
        };
        let resolved = controller
            .resolve_connection(|| Err("corrupt preferences or locked vault".into()))
            .unwrap();
        assert_eq!(resolved.host, "pinned.test");
        assert!(Controller::default()
            .resolve_connection(|| Err("idle pack denied".into()))
            .is_err());
    }
    #[test]
    fn session_blocks_unsafe_preferences_but_allows_navigation_and_content() {
        let before = Preferences::initial();
        let mut controller = Controller::default();
        controller.pinned = Some(Pinned {
            id: "session-1".into(),
            connection: Connection {
                host: before.obs_host.clone(),
                port: before.obs_port,
                password: Some("synthetic".into()),
            },
            source: "stream-main".into(),
            content: "content-main".into(),
        });
        let mut next = before.clone();
        next.active_page = "create".into();
        next.comfyui_url = "http://127.0.0.1:1".into();
        assert!(controller.allow_preferences(&before, &next).is_ok());
        next.enabled_packs = vec!["content".into()];
        assert!(controller.allow_preferences(&before, &next).is_err());
        next = before.clone();
        next.obs_port += 1;
        assert!(controller.allow_preferences(&before, &next).is_err());
        next = before.clone();
        next.obs_host = "other.invalid".into();
        assert!(controller.allow_preferences(&before, &next).is_err());
        assert!(controller.allow_password_change().is_err());
        assert!(Controller::default().allow_password_change().is_ok());
    }
}

#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct StartReceipt {
    pub session_id: String,
    pub context_id: String,
    pub confirmed: bool,
    pub source_profile_id: String,
    pub content_profile_id: String,
}
impl std::ops::Deref for StartReceipt {
    type Target = str;
    fn deref(&self) -> &str {
        &self.session_id
    }
}
#[derive(Serialize)]
pub struct Observation<T> {
    pub session_id: Option<String>,
    pub context_id: String,
    pub value: T,
}
async fn observe_connection(connection: Connection, mut status: Status) -> Status {
    let cache = obs::ObsClientCache::new();
    let observed = tokio::time::timeout(std::time::Duration::from_secs(3), async {
        let stream = obs::get_stream_status(
            &cache,
            &connection.host,
            connection.port,
            connection.password.as_deref(),
        )
        .await
        .ok();
        let recording = obs::recording_active(
            &cache,
            &connection.host,
            connection.port,
            connection.password.as_deref(),
        )
        .await
        .ok();
        (stream, recording)
    })
    .await
    .unwrap_or((None, None));
    status.connected = observed.0.is_some() && observed.1.is_some();
    status.stream_active = observed.0.map(|s| s.active);
    status.recording_active = observed.1;
    status
}
pub async fn observe_status(
    controller: &tokio::sync::Mutex<Controller>,
    load: impl FnOnce() -> Result<Connection, String>,
) -> Result<Status, String> {
    let (connection, status) = controller.lock().await.snapshot(load).await?;
    let mut status = observe_connection(connection, status).await;
    let controller = controller.lock().await;
    controller.require_context(&status.context_id)?;
    // A lost subscription revokes Stop even if an observation socket reconnects.
    status.owned = controller.session.is_owned().await;
    status.recovery_required = controller.busy() && !status.owned && controller.pending.is_none();
    Ok(status)
}
impl Controller {
    pub fn require_context(&self, context: &str) -> Result<(), String> {
        if self.context_id() != context {
            return Err("OBS context changed; discard old observation".into());
        }
        Ok(())
    }
}
pub async fn inspect_audio(
    controller: &tokio::sync::Mutex<Controller>,
    load: impl FnOnce() -> Result<Connection, String>,
) -> Result<Observation<Vec<obs::AudioInput>>, String> {
    let (connection, status) = controller.lock().await.snapshot(load).await?;
    let value = obs::audio_inputs(
        &obs::ObsClientCache::new(),
        &connection.host,
        connection.port,
        connection.password.as_deref(),
    )
    .await
    .map_err(|_| "Could not read OBS audio inputs")?;
    controller
        .lock()
        .await
        .require_context(&status.context_id)?;
    Ok(Observation {
        session_id: status.session_id,
        context_id: status.context_id,
        value,
    })
}
pub async fn inspect_scenes(
    controller: &tokio::sync::Mutex<Controller>,
    load: impl FnOnce() -> Result<Connection, String>,
) -> Result<Observation<Vec<obs::SceneInfo>>, String> {
    let (connection, status) = controller.lock().await.snapshot(load).await?;
    let value = obs::get_scenes(
        &obs::ObsClientCache::new(),
        &connection.host,
        connection.port,
        connection.password.as_deref(),
    )
    .await
    .map_err(|_| "Could not read OBS scenes")?;
    controller
        .lock()
        .await
        .require_context(&status.context_id)?;
    Ok(Observation {
        session_id: status.session_id,
        context_id: status.context_id,
        value,
    })
}

// Native commands and protocol tests share these exact admission paths. The
// context/generation checks run under the mutation lock BEFORE the idle loader
// can read settings/vault, or a socket/cache can be created. Pinned resolution
// remains lazy and independent of preferences. No mutation is replayed here.
pub async fn set_observed_mute(
    controller: &tokio::sync::Mutex<Controller>,
    load: impl FnOnce() -> Result<Connection, String>,
    expected: MutationContext,
    input_name: &str,
    muted: bool,
) -> Result<Vec<obs::AudioInput>, String> {
    let controller = controller.lock().await;
    controller.admit_observed_mutation(&expected)?;
    let c = controller.resolve_connection(load)?;
    obs::set_input_muted(
        &obs::ObsClientCache::new(),
        &c.host,
        c.port,
        c.password.as_deref(),
        input_name,
        muted,
    )
    .await
    .map_err(|_| "OBS did not confirm the audio change".into())
}
pub async fn switch_observed_scene(
    controller: &tokio::sync::Mutex<Controller>,
    load: impl FnOnce() -> Result<Connection, String>,
    expected: MutationContext,
    scene_name: &str,
) -> Result<Vec<obs::SceneInfo>, String> {
    let controller = controller.lock().await;
    controller.admit_observed_mutation(&expected)?;
    let c = controller.resolve_connection(load)?;
    obs::switch_observed_scene(
        &obs::ObsClientCache::new(),
        &c.host,
        c.port,
        c.password.as_deref(),
        scene_name,
    )
    .await
    .map_err(|_| "OBS did not confirm the scene change".into())
}
