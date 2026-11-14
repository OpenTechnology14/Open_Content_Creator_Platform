//! Local recording ownership is a continuous Outputs subscription on one
//! non-reconnecting control socket. Observations never confer ownership.
use super::{ErrorEnvelope, LiveSessionResult, ObsClientCache, CONNECT_TIMEOUT, REQUEST_TIMEOUT};
use futures_util::{FutureExt, StreamExt};
use obws::events::{Event, EventStream, OutputState};
use tokio::sync::Mutex;

#[derive(Default)]
pub struct LocalRecordingState(Mutex<Option<Witness>>);
#[derive(Clone, Copy, PartialEq)]
enum Phase {
    Starting,
    Recording,
    Stopping,
    Finished,
    Lost,
}
struct Witness {
    client: obws::Client,
    events: EventStream,
    phase: Phase,
    finalized: Option<String>,
    source: String,
    content: String,
}
async fn request<T>(
    future: impl std::future::Future<Output = Result<T, obws::error::Error>>,
) -> Result<T, obws::error::Error> {
    tokio::time::timeout(REQUEST_TIMEOUT, future)
        .await
        .map_err(|_| obws::error::Error::Timeout)?
}
fn lost() -> ErrorEnvelope {
    ErrorEnvelope::invalid_request("Recording continuity is unproven. Control output in OBS; recover only when inactive. No file was attributed.")
}
impl Witness {
    fn event(&mut self, event: Event) {
        if self.phase == Phase::Lost {
            return;
        }
        match event {
            Event::RecordStateChanged {
                active,
                state,
                path,
            } => match (self.phase, state) {
                (Phase::Starting, OutputState::Starting) => (),
                (Phase::Starting, OutputState::Started) if active => self.phase = Phase::Recording,
                (Phase::Recording, OutputState::Paused | OutputState::Resumed) if active => (),
                (Phase::Stopping, OutputState::Stopping) => (),
                (Phase::Stopping, OutputState::Stopped) if !active => {
                    self.finalized = path;
                    self.phase = Phase::Finished;
                }
                _ => self.phase = Phase::Lost,
            },
            Event::ServerStopping | Event::ServerStopped | Event::RecordFileChanged { .. } => {
                self.phase = Phase::Lost
            }
            _ => (),
        }
    }
    fn drain(&mut self) {
        loop {
            match self.events.next().now_or_never() {
                Some(Some(event)) => self.event(event),
                // obws terminates this stream on receiver lag as well as closure.
                Some(None) => {
                    self.phase = Phase::Lost;
                    return;
                }
                None => return,
            }
        }
    }
    async fn wait_for(&mut self, target: Phase) -> Result<(), ErrorEnvelope> {
        let outcome = tokio::time::timeout(REQUEST_TIMEOUT, async {
            loop {
                self.drain();
                if self.phase == target {
                    return true;
                }
                if self.phase == Phase::Lost {
                    return false;
                }
                match self.events.next().await {
                    Some(event) => self.event(event),
                    None => return false,
                }
            }
        })
        .await;
        if outcome != Ok(true) {
            self.phase = Phase::Lost;
            return Err(lost());
        }
        Ok(())
    }
    async fn barrier(&mut self) -> Result<bool, ErrorEnvelope> {
        // Same-socket response orders preceding lifecycle frames before the
        // destructive admission check. Never reconnect this witness socket.
        let status = request(self.client.recording().status()).await;
        self.drain();
        match status {
            Ok(status) => Ok(status.active),
            Err(_) => {
                self.phase = Phase::Lost;
                Err(lost())
            }
        }
    }
}
impl LocalRecordingState {
    pub fn new() -> Self {
        Self::default()
    }
    pub async fn is_owned(&self) -> bool {
        let mut value = self.0.lock().await;
        value.as_mut().is_some_and(|w| {
            w.drain();
            w.phase == Phase::Recording
        })
    }
    pub async fn clear(&self) {
        *self.0.lock().await = None;
    }
}

pub async fn start_owned_recording(
    _cache: &ObsClientCache,
    session: &LocalRecordingState,
    host: &str,
    port: u16,
    password: Option<&str>,
    source_profile_id: String,
    content_profile_id: String,
) -> Result<(), ErrorEnvelope> {
    let mut slot = session.0.lock().await;
    if slot.is_some() {
        return Err(ErrorEnvelope::invalid_request(
            "Recording session needs completion or recovery",
        ));
    }
    let client = obws::Client::connect_with_config(obws::client::ConnectConfig {
        host,
        port,
        password,
        dangerous: None,
        event_subscriptions: Some(obws::requests::EventSubscription::OUTPUTS),
        broadcast_capacity: 128,
        connect_timeout: CONNECT_TIMEOUT,
    })
    .await
    .map_err(|_| lost())?;
    let events = client.events().map_err(|_| lost())?;
    let stream = request(client.streaming().status())
        .await
        .map_err(|_| lost())?;
    let recording = request(client.recording().status())
        .await
        .map_err(|_| lost())?;
    if stream.active || recording.active {
        return Err(ErrorEnvelope::invalid_request(
            "External OBS output is active",
        ));
    }
    let mut witness = Witness {
        client,
        events,
        phase: Phase::Starting,
        finalized: None,
        source: source_profile_id,
        content: content_profile_id,
    };
    witness.drain();
    if witness.phase != Phase::Starting {
        return Err(lost());
    }
    *slot = Some(witness);
    let witness = slot.as_mut().expect("reserved");
    if request(witness.client.recording().start()).await.is_err() {
        witness.phase = Phase::Lost;
        return Err(lost());
    }
    witness.wait_for(Phase::Recording).await?;
    if !witness.barrier().await? || witness.phase != Phase::Recording {
        witness.phase = Phase::Lost;
        return Err(lost());
    }
    Ok(())
}

pub async fn stop_owned_recording(
    _cache: &ObsClientCache,
    session: &LocalRecordingState,
    _host: &str,
    _port: u16,
    _password: Option<&str>,
) -> Result<LiveSessionResult, ErrorEnvelope> {
    let mut slot = session.0.lock().await;
    let witness = slot.as_mut().ok_or_else(lost)?;
    witness.drain();
    if witness.phase != Phase::Recording {
        return Err(lost());
    }
    if !witness.barrier().await? || witness.phase != Phase::Recording {
        witness.phase = Phase::Lost;
        return Err(lost());
    }
    witness.phase = Phase::Stopping;
    match request(witness.client.recording().stop()).await {
        Ok(path) => {
            witness.wait_for(Phase::Finished).await?;
            let active = witness.barrier().await?;
            if active
                || witness.phase != Phase::Finished
                || witness.finalized.as_deref() != Some(path.as_str())
            {
                witness.phase = Phase::Lost;
                return Err(lost());
            }
            let result = LiveSessionResult {
                stream_active: false,
                recording_active: false,
                recording_owned: true,
                recording_path: Some(path),
                source_profile_id: Some(witness.source.clone()),
                content_profile_id: Some(witness.content.clone()),
                detail: "Owned recording finalized with matching OBS lifecycle evidence".into(),
            };
            *slot = None;
            Ok(result)
        }
        Err(obws::error::Error::Api {
            code: obws::responses::StatusCode::NotReady,
            ..
        }) => {
            // OBS documents NotReady as an unexecuted, retryable rejection.
            // Only retain ownership if the same socket still witnesses the
            // uninterrupted output. All unknown/transport outcomes revoke it.
            witness.phase = Phase::Recording;
            if !witness.barrier().await? || witness.phase != Phase::Recording {
                witness.phase = Phase::Lost;
            }
            Err(ErrorEnvelope::invalid_request(
                "OBS rejected Stop before execution; refresh and retry only if still owned",
            ))
        }
        Err(_) => {
            witness.phase = Phase::Lost;
            Err(lost())
        }
    }
}
