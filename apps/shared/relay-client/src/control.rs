//! Safe, persisted configuration and command validation for remote control.

use crate::{
    connection::{RelayConnection, RelayEvent},
    Product, RelayConfig, RelayMessage, RelayMode, SubscriptionTier,
};
use local_settings::{LocalSettings, OsCredentials, SettingsError};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, RwLock};
use url::Url;

const HOSTED_TOKEN: &str = "relay-hosted-token";
const SELF_HOSTED_TOKEN: &str = "relay-self-hosted-token";
pub const MAX_PENDING_COMMANDS: usize = 50;
pub const MAX_DISCOVERED_DEVICES: usize = 50;
const DEVICE_PRESENCE_LEASE: Duration = Duration::from_secs(75);

#[derive(Debug, Clone, Copy, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub enum RemoteMode {
    Local,
    Hosted,
    SelfHosted,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(default)]
pub struct RemotePublicSettings {
    pub mode: RemoteMode,
    pub enabled: bool,
    pub self_hosted_url: Option<String>,
    pub device_id: String,
    pub device_name: String,
}

impl Default for RemotePublicSettings {
    fn default() -> Self {
        Self {
            mode: RemoteMode::Local,
            enabled: false,
            self_hosted_url: None,
            device_id: uuid::Uuid::new_v4().to_string(),
            device_name: hostname::get()
                .map(|name| name.to_string_lossy().to_string())
                .unwrap_or_else(|_| "Creator workstation".into()),
        }
    }
}

#[derive(Debug, Clone)]
pub struct RemoteSettings {
    pub public: RemotePublicSettings,
    pub hosted_token: Option<String>,
    pub self_hosted_token: Option<String>,
}

impl RemoteSettings {
    pub fn relay_config(&self, product: Product) -> Result<RelayConfig, String> {
        let mode = match self.public.mode {
            RemoteMode::Local => RelayMode::Local,
            RemoteMode::Hosted => RelayMode::Hosted {
                jwt: self
                    .hosted_token
                    .clone()
                    .ok_or("Save a hosted relay token first")?,
            },
            RemoteMode::SelfHosted => RelayMode::SelfHosted {
                url: self
                    .public
                    .self_hosted_url
                    .clone()
                    .ok_or("Save a self-hosted relay URL first")?,
                api_key: Some(
                    self.self_hosted_token
                        .clone()
                        .ok_or("Save a self-hosted relay token first")?,
                ),
            },
        };
        Ok(RelayConfig {
            mode,
            product,
            device_id: self.public.device_id.clone(),
            device_name: self.public.device_name.clone(),
        })
    }

    pub fn view(&self) -> RemoteSettingsView {
        RemoteSettingsView {
            mode: self.public.mode,
            enabled: self.public.enabled,
            self_hosted_url: self.public.self_hosted_url.clone(),
            hosted_token_set: self.hosted_token.is_some(),
            self_hosted_token_set: self.self_hosted_token.is_some(),
            device_id: self.public.device_id.clone(),
            device_name: self.public.device_name.clone(),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct RemoteSettingsView {
    pub mode: RemoteMode,
    pub enabled: bool,
    pub self_hosted_url: Option<String>,
    pub hosted_token_set: bool,
    pub self_hosted_token_set: bool,
    pub device_id: String,
    pub device_name: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RemoteSettingsUpdate {
    pub mode: RemoteMode,
    pub enabled: bool,
    pub self_hosted_url: Option<String>,
    pub access_token: Option<String>,
    #[serde(default)]
    pub clear_access_token: bool,
    pub device_name: String,
}

#[derive(Clone)]
pub struct RemotePersistence {
    public: LocalSettings,
    credentials: OsCredentials,
}

impl RemotePersistence {
    pub fn new(root: &Path, product: &str) -> Result<Self, SettingsError> {
        Ok(Self {
            public: LocalSettings::new(root, &format!("{product}.remote"))?,
            credentials: OsCredentials::new("HybridCreatorPlatform", product)?,
        })
    }

    pub fn load(&self) -> Result<RemoteSettings, SettingsError> {
        Ok(RemoteSettings {
            public: self.public.load()?,
            hosted_token: self.credentials.get(HOSTED_TOKEN)?,
            self_hosted_token: self.credentials.get(SELF_HOSTED_TOKEN)?,
        })
    }

    pub fn save(
        &self,
        current: &RemoteSettings,
        update: RemoteSettingsUpdate,
    ) -> Result<RemoteSettings, String> {
        validate_update(current, &update)?;
        let mut next = current.clone();
        next.public.mode = update.mode;
        next.public.enabled = update.enabled && update.mode != RemoteMode::Local;
        next.public.device_name = update.device_name.trim().into();
        next.public.self_hosted_url = update
            .self_hosted_url
            .as_deref()
            .map(normalize_relay_url)
            .transpose()?;

        let target = match update.mode {
            RemoteMode::Hosted => Some((&mut next.hosted_token, HOSTED_TOKEN)),
            RemoteMode::SelfHosted => Some((&mut next.self_hosted_token, SELF_HOSTED_TOKEN)),
            RemoteMode::Local => None,
        };
        if let Some((value, key)) = target {
            if update.clear_access_token {
                self.credentials
                    .clear(key)
                    .map_err(|error| error.to_string())?;
                *value = None;
            } else if let Some(token) = update.access_token {
                self.credentials
                    .set(key, &token)
                    .map_err(|error| error.to_string())?;
                *value = Some(token);
            }
        }
        self.public
            .save(&next.public)
            .map_err(|error| error.to_string())?;
        Ok(next)
    }
}

fn validate_update(current: &RemoteSettings, update: &RemoteSettingsUpdate) -> Result<(), String> {
    let name = update.device_name.trim();
    if name.is_empty() || name.len() > 80 || name.chars().any(char::is_control) {
        return Err("Device name must be 1 to 80 printable characters".into());
    }
    if update.clear_access_token && update.access_token.is_some() {
        return Err("Choose either a new relay token or Clear saved token".into());
    }
    if let Some(token) = update.access_token.as_deref() {
        if token.is_empty() || token.len() > 8192 {
            return Err("Relay token must be 1 to 8192 characters".into());
        }
    }
    if update.mode == RemoteMode::SelfHosted {
        normalize_relay_url(
            update
                .self_hosted_url
                .as_deref()
                .ok_or("A self-hosted relay URL is required")?,
        )?;
    }
    if update.enabled {
        let has_token = update.access_token.is_some()
            || (!update.clear_access_token
                && match update.mode {
                    RemoteMode::Hosted => current.hosted_token.is_some(),
                    RemoteMode::SelfHosted => current.self_hosted_token.is_some(),
                    RemoteMode::Local => true,
                });
        if update.mode != RemoteMode::Local && !has_token {
            return Err("Save a relay token before enabling remote control".into());
        }
    }
    Ok(())
}

fn normalize_relay_url(value: &str) -> Result<String, String> {
    let parsed =
        Url::parse(value.trim()).map_err(|_| "Relay URL must be a valid HTTP or HTTPS URL")?;
    if !matches!(parsed.scheme(), "http" | "https") || parsed.host_str().is_none() {
        return Err("Relay URL must use HTTP or HTTPS and include a host".into());
    }
    if !parsed.username().is_empty()
        || parsed.password().is_some()
        || parsed.query().is_some()
        || parsed.fragment().is_some()
    {
        return Err("Relay URL cannot contain credentials, query values or fragments".into());
    }
    Ok(parsed.as_str().trim_end_matches('/').into())
}

#[derive(Debug, Clone, Serialize)]
pub struct PendingCommand {
    pub id: String,
    pub source_device_id: String,
    pub target: String,
    pub action: String,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RemoteRuntimeView {
    pub status: String,
    pub last_error: Option<String>,
    pub subscription_tier: Option<SubscriptionTier>,
    pub pending: Vec<PendingCommand>,
    pub outgoing: Vec<OutboundRequest>,
    pub devices: Vec<RemoteDevice>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RemoteDevice {
    pub device_id: String,
    pub device_name: String,
    pub product: Product,
}

#[derive(Debug, Clone, Serialize)]
pub struct OutboundRequest {
    pub id: String,
    pub target_device_id: String,
    pub action: String,
    pub status: String,
    pub message: String,
}

type PendingEntry = (PendingCommand, serde_json::Value);

struct DiscoveredDevice {
    device: RemoteDevice,
    last_seen: Instant,
}

/// One app's live relay session. Incoming commands are only queued; the app must
/// explicitly call `take_for_approval` before any local action can run.
pub struct RemoteRuntime {
    product: Product,
    device_id: Arc<RwLock<String>>,
    connection: Arc<Mutex<Option<RelayConnection>>>,
    status: Arc<RwLock<String>>,
    last_error: Arc<RwLock<Option<String>>>,
    subscription_tier: Arc<RwLock<Option<SubscriptionTier>>>,
    pending: Arc<RwLock<Vec<PendingEntry>>>,
    outgoing: Arc<RwLock<Vec<OutboundRequest>>>,
    devices: Arc<RwLock<Vec<DiscoveredDevice>>>,
    device_name: Arc<RwLock<String>>,
}

impl RemoteRuntime {
    pub fn new(product: Product) -> Self {
        Self {
            product,
            device_id: Arc::new(RwLock::new(String::new())),
            connection: Arc::new(Mutex::new(None)),
            status: Arc::new(RwLock::new("disconnected".into())),
            last_error: Arc::new(RwLock::new(None)),
            subscription_tier: Arc::new(RwLock::new(None)),
            pending: Arc::new(RwLock::new(Vec::new())),
            outgoing: Arc::new(RwLock::new(Vec::new())),
            devices: Arc::new(RwLock::new(Vec::new())),
            device_name: Arc::new(RwLock::new(String::new())),
        }
    }

    pub async fn connect(&self, settings: &RemoteSettings) -> Result<(), String> {
        self.disconnect().await;
        if !settings.public.enabled || settings.public.mode == RemoteMode::Local {
            *self.status.write().await = "disabled".into();
            return Ok(());
        }
        let config = settings.relay_config(self.product.clone())?;
        *self.device_id.write().await = settings.public.device_id.clone();
        *self.device_name.write().await = settings.public.device_name.clone();
        let (mut connection, mut events) = RelayConnection::new(config);
        connection
            .start()
            .await
            .map_err(|error| error.to_string())?;
        *self.status.write().await = "connecting".into();
        *self.last_error.write().await = None;
        *self.connection.lock().await = Some(connection);

        let product = self.product.clone();
        let status = self.status.clone();
        let last_error = self.last_error.clone();
        let tier = self.subscription_tier.clone();
        let pending = self.pending.clone();
        let outgoing = self.outgoing.clone();
        let connection = self.connection.clone();
        let device_id = self.device_id.clone();
        let device_name = self.device_name.clone();
        let devices = self.devices.clone();
        tokio::spawn(async move {
            while let Some(event) = events.recv().await {
                match event {
                    RelayEvent::Connected => *status.write().await = "connected".into(),
                    RelayEvent::Authenticated(subscription) => {
                        *tier.write().await = Some(subscription.tier);
                    }
                    RelayEvent::Disconnected(reason) => {
                        *status.write().await = "disconnected".into();
                        *last_error.write().await = Some(reason);
                    }
                    RelayEvent::Error(error) => {
                        *status.write().await = "reconnecting".into();
                        *last_error.write().await = Some(error);
                    }
                    RelayEvent::Message(message @ RelayMessage::Command { .. }) => {
                        let RelayMessage::Command {
                            id,
                            target_device_id,
                            ..
                        } = &message
                        else {
                            unreachable!()
                        };
                        if target_device_id != &*device_id.read().await {
                            continue;
                        }
                        let command_id = id.clone();
                        match validate_command(&product, message.clone()) {
                            Ok(entry) => {
                                let mut queue = pending.write().await;
                                if queue.iter().any(|(item, _)| item.id == entry.0.id) {
                                    send_result(
                                        &connection,
                                        command_id,
                                        false,
                                        serde_json::json!({"error": "Duplicate command ID"}),
                                    )
                                    .await;
                                } else if queue.len() >= MAX_PENDING_COMMANDS {
                                    send_result(
                                        &connection,
                                        command_id,
                                        false,
                                        serde_json::json!({"error": "Approval queue is full"}),
                                    )
                                    .await;
                                } else {
                                    queue.push(entry);
                                }
                            }
                            Err(error) => {
                                send_result(
                                    &connection,
                                    command_id,
                                    false,
                                    serde_json::json!({"error": error}),
                                )
                                .await;
                            }
                        }
                    }
                    RelayEvent::Message(RelayMessage::CommandResult { id, success, data }) => {
                        if let Some(request) = outgoing
                            .write()
                            .await
                            .iter_mut()
                            .find(|request| request.id == id)
                        {
                            request.status = if success { "completed" } else { "failed" }.into();
                            request.message = if success {
                                "Target device completed the approved action".into()
                            } else {
                                data.get("error")
                                    .and_then(serde_json::Value::as_str)
                                    .map(|value| value.chars().take(240).collect())
                                    .unwrap_or_else(|| "Target device rejected the action".into())
                            };
                        }
                    }
                    RelayEvent::Message(RelayMessage::DevicePresence {
                        device_id: peer_id,
                        device_name: peer_name,
                        product: peer_product,
                    }) => {
                        if peer_id == *device_id.read().await {
                            continue;
                        }
                        if peer_product != product {
                            continue;
                        }
                        let peer = match validate_presence(peer_id, peer_name, peer_product) {
                            Ok(peer) => peer,
                            Err(error) => {
                                *last_error.write().await = Some(error);
                                continue;
                            }
                        };
                        let mut known = devices.write().await;
                        let is_new = !known
                            .iter()
                            .any(|item| item.device.device_id == peer.device_id);
                        if let Some(existing) = known
                            .iter_mut()
                            .find(|item| item.device.device_id == peer.device_id)
                        {
                            existing.device = peer;
                            existing.last_seen = Instant::now();
                        } else {
                            if known.len() >= MAX_DISCOVERED_DEVICES {
                                known.remove(0);
                            }
                            known.push(DiscoveredDevice {
                                device: peer,
                                last_seen: Instant::now(),
                            });
                        }
                        drop(known);
                        if is_new {
                            let own_presence = RelayMessage::DevicePresence {
                                device_id: device_id.read().await.clone(),
                                device_name: device_name.read().await.clone(),
                                product,
                            };
                            if let Some(relay) = connection.lock().await.as_ref() {
                                let _ = relay.send(own_presence);
                            }
                        }
                    }
                    RelayEvent::Message(_) => {}
                }
            }
        });
        Ok(())
    }

    pub async fn disconnect(&self) {
        if let Some(connection) = self.connection.lock().await.take() {
            connection.shutdown();
        }
        *self.status.write().await = "disconnected".into();
        *self.subscription_tier.write().await = None;
        self.pending.write().await.clear();
        self.devices.write().await.clear();
    }

    pub async fn view(&self) -> RemoteRuntimeView {
        RemoteRuntimeView {
            status: self.status.read().await.clone(),
            last_error: self.last_error.read().await.clone(),
            subscription_tier: self.subscription_tier.read().await.clone(),
            pending: self
                .pending
                .read()
                .await
                .iter()
                .map(|entry| entry.0.clone())
                .collect(),
            outgoing: self.outgoing.read().await.clone(),
            devices: active_devices(&self.devices.read().await),
        }
    }

    pub async fn take_for_approval(&self, id: &str) -> Result<PendingEntry, String> {
        let mut pending = self.pending.write().await;
        let index = pending
            .iter()
            .position(|(command, _)| command.id == id)
            .ok_or("Remote command is no longer pending")?;
        Ok(pending.remove(index))
    }

    pub async fn deny(&self, id: &str) -> Result<(), String> {
        let (command, _) = self.take_for_approval(id).await?;
        self.complete(
            &command.id,
            false,
            serde_json::json!({"error": "Denied on the creator device"}),
        )
        .await
    }

    pub async fn complete(
        &self,
        id: &str,
        success: bool,
        data: serde_json::Value,
    ) -> Result<(), String> {
        let guard = self.connection.lock().await;
        let connection = guard.as_ref().ok_or("Relay is disconnected")?;
        connection
            .send(RelayMessage::CommandResult {
                id: id.into(),
                success,
                data,
            })
            .map_err(|error| error.to_string())
    }

    pub async fn request(
        &self,
        target_device_id: String,
        target: String,
        action: String,
        payload: serde_json::Value,
    ) -> Result<String, String> {
        validate_device_id(&target_device_id)?;
        let source_device_id = self.device_id.read().await.clone();
        validate_device_id(&source_device_id)?;
        if *self.status.read().await != "connected" {
            return Err("Connect to the relay before sending a request".into());
        }
        let id = uuid::Uuid::new_v4().to_string();
        let message = RelayMessage::Command {
            id: id.clone(),
            source_device_id,
            target_device_id: target_device_id.clone(),
            target: target.clone(),
            action: action.clone(),
            payload,
        };
        validate_command(&self.product, message.clone())?;
        {
            let mut outgoing = self.outgoing.write().await;
            if outgoing.len() >= MAX_PENDING_COMMANDS {
                outgoing.remove(0);
            }
            outgoing.push(OutboundRequest {
                id: id.clone(),
                target_device_id: target_device_id.clone(),
                action: format!("{target}/{action}"),
                status: "awaiting-approval".into(),
                message: "Waiting for approval on the target device".into(),
            });
        }
        let guard = self.connection.lock().await;
        if let Err(error) = guard
            .as_ref()
            .ok_or("Relay is disconnected")?
            .send(message)
            .map_err(|error| error.to_string())
        {
            self.outgoing
                .write()
                .await
                .retain(|request| request.id != id);
            return Err(error);
        }
        Ok(id)
    }
}

fn active_devices(devices: &[DiscoveredDevice]) -> Vec<RemoteDevice> {
    devices
        .iter()
        .filter(|entry| entry.last_seen.elapsed() <= DEVICE_PRESENCE_LEASE)
        .map(|entry| entry.device.clone())
        .collect()
}

fn validate_presence(
    device_id: String,
    device_name: String,
    product: Product,
) -> Result<RemoteDevice, String> {
    validate_device_id(&device_id)?;
    let name = device_name.trim();
    if name.is_empty() || name.len() > 80 || name.chars().any(char::is_control) {
        return Err("Relay sent an invalid device presence".into());
    }
    Ok(RemoteDevice {
        device_id,
        device_name: name.into(),
        product,
    })
}

async fn send_result(
    connection: &Arc<Mutex<Option<RelayConnection>>>,
    id: String,
    success: bool,
    data: serde_json::Value,
) {
    if let Some(connection) = connection.lock().await.as_ref() {
        let _ = connection.send(RelayMessage::CommandResult { id, success, data });
    }
}

pub fn validate_command(
    product: &Product,
    message: RelayMessage,
) -> Result<(PendingCommand, serde_json::Value), String> {
    let RelayMessage::Command {
        id,
        source_device_id,
        target_device_id,
        target,
        action,
        payload,
    } = message
    else {
        return Err("Message is not a remote command".into());
    };
    if id.is_empty() || id.len() > 128 || id.chars().any(char::is_control) {
        return Err("Command ID is invalid".into());
    }
    validate_device_id(&source_device_id)?;
    validate_device_id(&target_device_id)?;
    if serde_json::to_vec(&payload)
        .map_err(|_| "Command payload is invalid")?
        .len()
        > 16 * 1024
    {
        return Err("Command payload exceeds 16 KiB".into());
    }
    let summary = match (product, target.as_str(), action.as_str()) {
        (Product::StreamExtend, "obs", "switch_scene") => {
            let scene = required_string(&payload, "scene", 128)?;
            format!("Switch OBS to scene ‘{scene}’")
        }
        (Product::StreamExtend, "obs", "toggle_stream") => {
            "Start or stop the live OBS stream".into()
        }
        (Product::CreatorExtend, "comfyui", "queue_workflow") => {
            let path = required_string(&payload, "workflow_path", 512)?;
            format!("Queue approved ComfyUI workflow ‘{path}’")
        }
        _ => return Err(format!("Remote action {target}/{action} is not allowed")),
    };
    Ok((
        PendingCommand {
            id,
            source_device_id,
            target,
            action,
            summary,
        },
        payload,
    ))
}

fn validate_device_id(value: &str) -> Result<(), String> {
    if value.is_empty() || value.len() > 128 || value.chars().any(char::is_control) {
        return Err("Target and source device IDs must be 1 to 128 printable characters".into());
    }
    Ok(())
}

fn required_string<'a>(
    payload: &'a serde_json::Value,
    field: &str,
    max: usize,
) -> Result<&'a str, String> {
    let value = payload
        .get(field)
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| format!("Command requires a string {field}"))?;
    if value.is_empty() || value.len() > max || value.chars().any(char::is_control) {
        return Err(format!("Command field {field} is invalid"));
    }
    Ok(value)
}

#[cfg(test)]
mod tests {
    use super::*;
    use futures_util::{SinkExt, StreamExt};
    use tokio::net::TcpListener;
    use tokio_tungstenite::{accept_async, tungstenite::Message};

    #[test]
    fn view_redacts_both_tokens() {
        let settings = RemoteSettings {
            public: RemotePublicSettings::default(),
            hosted_token: Some("hosted-secret".into()),
            self_hosted_token: Some("private-secret".into()),
        };
        let serialized = serde_json::to_string(&settings.view()).unwrap();
        assert!(serialized.contains("hosted_token_set"));
        assert!(!serialized.contains("hosted-secret"));
        assert!(!serialized.contains("private-secret"));
    }

    #[test]
    fn command_allowlist_requires_ids_and_valid_parameters() {
        let allowed = RelayMessage::Command {
            id: "request-1".into(),
            source_device_id: "phone".into(),
            target_device_id: "studio".into(),
            target: "obs".into(),
            action: "switch_scene".into(),
            payload: serde_json::json!({"scene": "Gameplay"}),
        };
        assert!(validate_command(&Product::StreamExtend, allowed).is_ok());
        let denied = RelayMessage::Command {
            id: "request-2".into(),
            source_device_id: "phone".into(),
            target_device_id: "studio".into(),
            target: "system".into(),
            action: "shell".into(),
            payload: serde_json::json!({"command": "rm -rf /"}),
        };
        assert!(validate_command(&Product::StreamExtend, denied).is_err());
    }

    #[test]
    fn subscription_and_command_wire_format_match_the_server() {
        let auth: RelayMessage = serde_json::from_value(serde_json::json!({
            "AuthOk": {"subscription": {"tier": "connect", "active": true, "tenant_id": "t", "expires_at": null}}
        })).unwrap();
        assert!(matches!(auth, RelayMessage::AuthOk { .. }));
        let command: RelayMessage = serde_json::from_value(serde_json::json!({
            "Command": {"id": "42", "source_device_id": "phone", "target_device_id": "studio", "target": "obs", "action": "toggle_stream", "payload": {}}
        }))
        .unwrap();
        assert!(matches!(command, RelayMessage::Command { id, .. } if id == "42"));
        let presence: RelayMessage = serde_json::from_value(serde_json::json!({
            "DevicePresence": {"device_id": "studio", "device_name": "Studio PC", "product": "StreamExtend"}
        }))
        .unwrap();
        assert!(
            matches!(presence, RelayMessage::DevicePresence { device_id, .. } if device_id == "studio")
        );
    }

    #[test]
    fn device_presence_lease_hides_disconnected_peers() {
        let device = RemoteDevice {
            device_id: "peer".into(),
            device_name: "Peer".into(),
            product: Product::StreamExtend,
        };
        let devices = vec![
            DiscoveredDevice {
                device: device.clone(),
                last_seen: Instant::now(),
            },
            DiscoveredDevice {
                device: RemoteDevice {
                    device_id: "stale".into(),
                    ..device
                },
                last_seen: Instant::now() - DEVICE_PRESENCE_LEASE - Duration::from_secs(1),
            },
        ];
        assert_eq!(active_devices(&devices), vec![devices[0].device.clone()]);
    }

    #[tokio::test]
    async fn runtime_authenticates_queues_approval_and_returns_correlated_result() {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            let (stream, _) = listener.accept().await.unwrap();
            let mut socket = accept_async(stream).await.unwrap();
            let auth = socket.next().await.unwrap().unwrap().into_text().unwrap();
            assert_eq!(
                serde_json::from_str::<serde_json::Value>(&auth).unwrap()["Auth"]["jwt"],
                "test-token"
            );
            socket.send(Message::Text(serde_json::json!({
                "AuthOk": {"subscription": {"tier": "connect", "active": true, "tenant_id": "test", "expires_at": null}}
            }).to_string().into())).await.unwrap();
            socket.send(Message::Text(serde_json::json!({
                "DevicePresence": {"device_id": "control-room", "device_name": "Control Room", "product": "StreamExtend"}
            }).to_string().into())).await.unwrap();
            socket.send(Message::Text(serde_json::json!({
                "DevicePresence": {"device_id": "creator-only", "device_name": "Creator", "product": "CreatorExtend"}
            }).to_string().into())).await.unwrap();
            socket.send(Message::Text(serde_json::json!({
                "Command": {"id": "cmd-7", "source_device_id": "phone", "target_device_id": "studio", "target": "obs", "action": "switch_scene", "payload": {"scene": "Gameplay"}}
            }).to_string().into())).await.unwrap();
            loop {
                let text = socket.next().await.unwrap().unwrap().into_text().unwrap();
                let value: serde_json::Value = serde_json::from_str(&text).unwrap();
                if value.get("CommandResult").is_some() {
                    assert_eq!(value["CommandResult"]["id"], "cmd-7");
                    assert_eq!(value["CommandResult"]["success"], true);
                    break;
                }
            }
        });

        let runtime = RemoteRuntime::new(Product::StreamExtend);
        let settings = RemoteSettings {
            public: RemotePublicSettings {
                mode: RemoteMode::SelfHosted,
                enabled: true,
                self_hosted_url: Some(format!("http://{address}")),
                device_id: "studio".into(),
                ..RemotePublicSettings::default()
            },
            hosted_token: None,
            self_hosted_token: Some("test-token".into()),
        };
        runtime.connect(&settings).await.unwrap();
        tokio::time::timeout(std::time::Duration::from_secs(2), async {
            loop {
                let view = runtime.view().await;
                if !view.pending.is_empty()
                    && view.devices.iter().any(|device| {
                        device.device_id == "control-room" && device.device_name == "Control Room"
                    })
                    && !view
                        .devices
                        .iter()
                        .any(|device| device.device_id == "creator-only")
                {
                    break;
                }
                tokio::task::yield_now().await;
            }
        })
        .await
        .unwrap();
        let (command, _) = runtime.take_for_approval("cmd-7").await.unwrap();
        runtime
            .complete(
                &command.id,
                true,
                serde_json::json!({"current_scene": "Gameplay"}),
            )
            .await
            .unwrap();
        tokio::time::timeout(std::time::Duration::from_secs(2), server)
            .await
            .unwrap()
            .unwrap();
        runtime.disconnect().await;
    }
}
