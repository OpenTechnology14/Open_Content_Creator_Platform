//! Shared relay client for Stream Extend + Creator Extend.
//!
//! Supports two connection modes:
//! 1. **Hosted** — auto-connects to streamextend.com / creatorextend.com relay
//!    for paying subscribers (subscription verified via JWT).
//! 2. **Self-hosted** — connects to a user-provided relay URL for users
//!    running their own DigitalOcean (or any) relay instance.
//!
//! The relay provides 5 cloud-only features:
//! - Remote access (control your setup from outside local network)
//! - Push notifications (stream alerts, job completion, errors)
//! - Metric persistence (Grafana dashboards from any device)
//! - Multi-device sync (settings, presets, workflows)
//! - Multi-user access (team members on the same platform)

use serde::{Deserialize, Serialize};
use std::time::Duration;
use thiserror::Error;

pub mod auth;
pub mod connection;
pub mod control;
pub mod sync;

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/// Hosted relay endpoints (the hosted service infrastructure).
pub const HOSTED_RELAY_STREAM: &str = "wss://relay.streamextend.com/ws";
pub const HOSTED_RELAY_CREATOR: &str = "wss://relay.creatorextend.com/ws";
pub const HOSTED_API_STREAM: &str = "https://relay.streamextend.com/api/v1";
pub const HOSTED_API_CREATOR: &str = "https://relay.creatorextend.com/api/v1";

/// Connection timeouts.
pub const CONNECT_TIMEOUT: Duration = Duration::from_secs(10);
pub const PING_INTERVAL: Duration = Duration::from_secs(30);
pub const RECONNECT_BASE_DELAY: Duration = Duration::from_secs(1);
pub const RECONNECT_MAX_DELAY: Duration = Duration::from_secs(60);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RelayMode {
    /// No cloud connection — all features local-only.
    Local,
    /// Connect to the hosted relay (subscription required).
    Hosted { jwt: String },
    /// Connect to a self-hosted relay instance.
    SelfHosted {
        url: String,
        api_key: Option<String>,
    },
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Product {
    StreamExtend,
    CreatorExtend,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RelayConfig {
    pub mode: RelayMode,
    pub product: Product,
    pub device_id: String,
    pub device_name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum SubscriptionTier {
    Free,
    Connect, // $5/mo
    Pro,     // $12/mo
    Team,    // $25/mo
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscriptionStatus {
    pub tier: SubscriptionTier,
    pub active: bool,
    pub tenant_id: Option<String>,
    pub expires_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RelayMessage {
    // Authentication
    Auth {
        jwt: String,
        device_id: String,
        device_name: String,
        product: Product,
    },
    AuthOk {
        subscription: SubscriptionStatus,
    },
    AuthError {
        reason: String,
    },

    // Remote control
    Command {
        id: String,
        source_device_id: String,
        target_device_id: String,
        target: String,
        action: String,
        payload: serde_json::Value,
    },
    CommandResult {
        id: String,
        success: bool,
        data: serde_json::Value,
    },
    DevicePresence {
        device_id: String,
        device_name: String,
        product: Product,
    },

    // Sync
    SyncPush {
        key: String,
        value: serde_json::Value,
        version: u64,
    },
    SyncPull {
        key: String,
    },
    SyncData {
        key: String,
        value: serde_json::Value,
        version: u64,
    },

    // Notifications
    Notification {
        title: String,
        body: String,
        channel: String,
    },

    // Metrics
    MetricsBatch {
        metrics: Vec<MetricPoint>,
    },

    // Heartbeat
    Ping,
    Pong,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricPoint {
    pub name: String,
    pub value: f64,
    pub timestamp: u64,
    pub labels: std::collections::HashMap<String, String>,
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

#[derive(Error, Debug)]
pub enum RelayError {
    #[error("Not connected to relay")]
    NotConnected,

    #[error("Authentication failed: {0}")]
    AuthFailed(String),

    #[error("Subscription required for this feature (tier: {required:?})")]
    SubscriptionRequired { required: SubscriptionTier },

    #[error("Connection error: {0}")]
    Connection(String),

    #[error("Timeout after {0:?}")]
    Timeout(Duration),

    #[error("Relay returned error: {0}")]
    RelayError(String),

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

pub struct RelayClient {
    config: RelayConfig,
    status: ConnectionStatus,
    subscription: Option<SubscriptionStatus>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ConnectionStatus {
    Disconnected,
    Connecting,
    Connected,
    Reconnecting { attempt: u32 },
}

impl RelayClient {
    pub fn new(config: RelayConfig) -> Self {
        Self {
            config,
            status: ConnectionStatus::Disconnected,
            subscription: None,
        }
    }

    /// Resolve the WebSocket URL based on relay mode + product.
    pub fn ws_url(&self) -> Option<String> {
        match &self.config.mode {
            RelayMode::Local => None,
            RelayMode::Hosted { .. } => Some(match self.config.product {
                Product::StreamExtend => HOSTED_RELAY_STREAM.to_string(),
                Product::CreatorExtend => HOSTED_RELAY_CREATOR.to_string(),
            }),
            RelayMode::SelfHosted { url, .. } => {
                // Normalize: ensure ws:// or wss:// prefix
                let ws_url = if url.starts_with("ws://") || url.starts_with("wss://") {
                    url.clone()
                } else if url.starts_with("https://") {
                    url.replace("https://", "wss://")
                } else if url.starts_with("http://") {
                    url.replace("http://", "ws://")
                } else {
                    format!("wss://{}", url)
                };
                // Append /ws if not already present
                if ws_url.ends_with("/ws") {
                    Some(ws_url)
                } else {
                    Some(format!("{}/ws", ws_url.trim_end_matches('/')))
                }
            }
        }
    }

    /// Resolve the REST API URL based on relay mode + product.
    pub fn api_url(&self) -> Option<String> {
        match &self.config.mode {
            RelayMode::Local => None,
            RelayMode::Hosted { .. } => Some(match self.config.product {
                Product::StreamExtend => HOSTED_API_STREAM.to_string(),
                Product::CreatorExtend => HOSTED_API_CREATOR.to_string(),
            }),
            RelayMode::SelfHosted { url, .. } => {
                let base = url.trim_end_matches('/');
                Some(format!("{}/api/v1", base))
            }
        }
    }

    pub fn status(&self) -> &ConnectionStatus {
        &self.status
    }

    pub fn subscription(&self) -> Option<&SubscriptionStatus> {
        self.subscription.as_ref()
    }

    /// Check if the current subscription tier allows a feature.
    pub fn can_use(&self, required: &SubscriptionTier) -> bool {
        match &self.subscription {
            None => matches!(required, SubscriptionTier::Free),
            Some(sub) => {
                if !sub.active {
                    return matches!(required, SubscriptionTier::Free);
                }
                match (&sub.tier, required) {
                    (_, SubscriptionTier::Free) => true,
                    (SubscriptionTier::Connect, SubscriptionTier::Connect) => true,
                    (SubscriptionTier::Pro, SubscriptionTier::Connect | SubscriptionTier::Pro) => {
                        true
                    }
                    (SubscriptionTier::Team, _) => true,
                    _ => false,
                }
            }
        }
    }
}

impl Default for RelayConfig {
    fn default() -> Self {
        Self {
            mode: RelayMode::Local,
            product: Product::StreamExtend,
            device_id: uuid::Uuid::new_v4().to_string(),
            device_name: hostname::get()
                .map(|h| h.to_string_lossy().to_string())
                .unwrap_or_else(|_| "Unknown Device".to_string()),
        }
    }
}
