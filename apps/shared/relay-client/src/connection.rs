//! WebSocket connection management with auto-reconnect.
//!
//! Handles the lifecycle: connect → authenticate → maintain → reconnect.

use crate::{
    ConnectionStatus, RelayClient, RelayConfig, RelayError, RelayMessage, RelayMode,
    SubscriptionStatus, CONNECT_TIMEOUT, PING_INTERVAL, RECONNECT_BASE_DELAY, RECONNECT_MAX_DELAY,
};
use futures_util::{SinkExt, StreamExt};
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use tokio_tungstenite::tungstenite::Message;

/// Event emitted by the relay connection for the app to handle.
#[derive(Debug, Clone)]
pub enum RelayEvent {
    Connected,
    Authenticated(SubscriptionStatus),
    Disconnected(String),
    Message(RelayMessage),
    Error(String),
}

/// Manages the WebSocket connection to the relay.
pub struct RelayConnection {
    config: Arc<RwLock<RelayConfig>>,
    status: Arc<RwLock<ConnectionStatus>>,
    event_tx: mpsc::UnboundedSender<RelayEvent>,
    message_tx: mpsc::UnboundedSender<RelayMessage>,
    message_rx: Option<mpsc::UnboundedReceiver<RelayMessage>>,
    shutdown: tokio::sync::watch::Sender<bool>,
}

impl RelayConnection {
    /// Create a new relay connection. Returns (connection, event_receiver).
    pub fn new(config: RelayConfig) -> (Self, mpsc::UnboundedReceiver<RelayEvent>) {
        let (event_tx, event_rx) = mpsc::unbounded_channel();
        let (shutdown_tx, _) = tokio::sync::watch::channel(false);
        let (message_tx, message_rx) = mpsc::unbounded_channel();

        let conn = Self {
            config: Arc::new(RwLock::new(config)),
            status: Arc::new(RwLock::new(ConnectionStatus::Disconnected)),
            event_tx,
            message_tx,
            message_rx: Some(message_rx),
            shutdown: shutdown_tx,
        };

        (conn, event_rx)
    }

    /// Start the connection loop in the background.
    pub async fn start(&mut self) -> Result<(), RelayError> {
        let config = self.config.read().await;

        // Local mode — no connection needed
        if matches!(config.mode, RelayMode::Local) {
            tracing::info!("Relay mode is Local — skipping connection");
            return Ok(());
        }

        let ws_url = RelayClient::new(config.clone())
            .ws_url()
            .ok_or_else(|| RelayError::Connection("No relay URL configured".into()))?;

        drop(config); // Release read lock

        tracing::info!("Connecting to relay at {}", ws_url);
        *self.status.write().await = ConnectionStatus::Connecting;

        let message_rx = self
            .message_rx
            .take()
            .ok_or_else(|| RelayError::Connection("Relay connection is already running".into()))?;
        let config = self.config.clone();
        let status = self.status.clone();
        let event_tx = self.event_tx.clone();
        let mut shutdown_rx = self.shutdown.subscribe();
        tokio::spawn(async move {
            run_connection_loop(
                config,
                status,
                event_tx,
                message_rx,
                &mut shutdown_rx,
                ws_url,
            )
            .await;
        });
        Ok(())
    }

    /// Single connection attempt.
    async fn connect_once(
        &self,
        ws_url: &str,
        msg_rx: &mut mpsc::UnboundedReceiver<RelayMessage>,
    ) -> Result<(), RelayError> {
        let connect_future = tokio_tungstenite::connect_async(ws_url);
        let (ws_stream, _) = tokio::time::timeout(CONNECT_TIMEOUT, connect_future)
            .await
            .map_err(|_| RelayError::Timeout(CONNECT_TIMEOUT))?
            .map_err(|e| RelayError::Connection(e.to_string()))?;

        let (mut write, mut read) = ws_stream.split();

        // Authenticate
        let config = self.config.read().await;
        let jwt = match &config.mode {
            RelayMode::Hosted { jwt } => jwt.clone(),
            RelayMode::SelfHosted { api_key, .. } => api_key.clone().unwrap_or_default(),
            RelayMode::Local => unreachable!(),
        };
        let auth_msg = RelayMessage::Auth {
            jwt,
            device_id: config.device_id.clone(),
            device_name: config.device_name.clone(),
            product: config.product,
        };
        let presence = RelayMessage::DevicePresence {
            device_id: config.device_id.clone(),
            device_name: config.device_name.clone(),
            product: config.product,
        };
        drop(config);

        let auth_json = serde_json::to_string(&auth_msg)?;
        write
            .send(Message::Text(auth_json.into()))
            .await
            .map_err(|e| RelayError::Connection(e.to_string()))?;

        // Wait for auth response
        let auth_response = tokio::time::timeout(CONNECT_TIMEOUT, read.next())
            .await
            .map_err(|_| RelayError::Timeout(CONNECT_TIMEOUT))?
            .ok_or_else(|| RelayError::Connection("Connection closed during auth".into()))?
            .map_err(|e| RelayError::Connection(e.to_string()))?;

        if let Message::Text(text) = auth_response {
            let msg: RelayMessage = serde_json::from_str(&text)?;
            match msg {
                RelayMessage::AuthOk { subscription } => {
                    *self.status.write().await = ConnectionStatus::Connected;
                    let _ = self.event_tx.send(RelayEvent::Connected);
                    let _ = self.event_tx.send(RelayEvent::Authenticated(subscription));
                    let presence = serde_json::to_string(&presence)?;
                    write
                        .send(Message::Text(presence.into()))
                        .await
                        .map_err(|e| RelayError::Connection(e.to_string()))?;
                    tracing::info!("Relay authenticated successfully");
                }
                RelayMessage::AuthError { reason } => {
                    return Err(RelayError::AuthFailed(reason));
                }
                _ => {
                    return Err(RelayError::Connection("Unexpected auth response".into()));
                }
            }
        }

        // Main message loop
        let mut ping_interval = tokio::time::interval(PING_INTERVAL);
        let mut shutdown_rx = self.shutdown.subscribe();

        loop {
            tokio::select! {
                // Incoming from relay
                msg = read.next() => {
                    match msg {
                        Some(Ok(Message::Text(text))) => {
                            match serde_json::from_str::<RelayMessage>(&text) {
                                Ok(relay_msg) => {
                                    if matches!(relay_msg, RelayMessage::Pong) {
                                        continue; // Heartbeat — don't propagate
                                    }
                                    let _ = self.event_tx.send(RelayEvent::Message(relay_msg));
                                }
                                Err(e) => {
                                    tracing::warn!("Failed to parse relay message: {}", e);
                                }
                            }
                        }
                        Some(Ok(Message::Close(_))) => {
                            tracing::info!("Relay sent close frame");
                            return Ok(());
                        }
                        Some(Err(e)) => {
                            return Err(RelayError::Connection(e.to_string()));
                        }
                        None => {
                            return Err(RelayError::Connection("Stream ended".into()));
                        }
                        _ => {} // Binary, Ping, Pong — ignore
                    }
                }

                // Outbound from app
                Some(msg) = msg_rx.recv() => {
                    let json = serde_json::to_string(&msg)?;
                    write.send(Message::Text(json.into())).await
                        .map_err(|e| RelayError::Connection(e.to_string()))?;
                }

                // Heartbeat
                _ = ping_interval.tick() => {
                    let ping = serde_json::to_string(&RelayMessage::Ping)?;
                    write.send(Message::Text(ping.into())).await
                        .map_err(|e| RelayError::Connection(e.to_string()))?;
                    let presence = serde_json::to_string(&presence)?;
                    write.send(Message::Text(presence.into())).await
                        .map_err(|e| RelayError::Connection(e.to_string()))?;
                }

                // Shutdown
                _ = shutdown_rx.changed() => {
                    let _ = write.send(Message::Close(None)).await;
                    return Ok(());
                }
            }
        }
    }

    /// Send a message to the relay.
    pub fn send(&self, msg: RelayMessage) -> Result<(), RelayError> {
        self.message_tx
            .send(msg)
            .map_err(|_| RelayError::NotConnected)
    }

    /// Shut down the connection.
    pub fn shutdown(&self) {
        let _ = self.shutdown.send(true);
    }

    /// Update the relay config (e.g. switch from Local to Hosted after login).
    pub async fn update_config(&self, config: RelayConfig) {
        *self.config.write().await = config;
    }
}

async fn run_connection_loop(
    config: Arc<RwLock<RelayConfig>>,
    status: Arc<RwLock<ConnectionStatus>>,
    event_tx: mpsc::UnboundedSender<RelayEvent>,
    mut message_rx: mpsc::UnboundedReceiver<RelayMessage>,
    shutdown_rx: &mut tokio::sync::watch::Receiver<bool>,
    ws_url: String,
) {
    let mut attempt: u32 = 0;
    loop {
        let proxy = RelayConnection {
            config: config.clone(),
            status: status.clone(),
            event_tx: event_tx.clone(),
            message_tx: mpsc::unbounded_channel().0,
            message_rx: None,
            shutdown: tokio::sync::watch::channel(false).0,
        };
        tokio::select! {
            _ = shutdown_rx.changed() => {
                *status.write().await = ConnectionStatus::Disconnected;
                let _ = event_tx.send(RelayEvent::Disconnected("Disconnected by this device".into()));
                break;
            }
            result = proxy.connect_once(&ws_url, &mut message_rx) => {
                match result {
                    Ok(()) => {
                        *status.write().await = ConnectionStatus::Disconnected;
                        let _ = event_tx.send(RelayEvent::Disconnected("Relay closed the connection".into()));
                    }
                    Err(error) => {
                        let _ = event_tx.send(RelayEvent::Error(error.to_string()));
                    }
                }
                attempt = attempt.saturating_add(1);
                *status.write().await = ConnectionStatus::Reconnecting { attempt };
                let delay = std::cmp::min(
                    RECONNECT_BASE_DELAY * 2u32.saturating_pow(attempt.min(16)),
                    RECONNECT_MAX_DELAY,
                );
                tokio::select! {
                    _ = shutdown_rx.changed() => {
                        *status.write().await = ConnectionStatus::Disconnected;
                        let _ = event_tx.send(RelayEvent::Disconnected("Disconnected by this device".into()));
                        break;
                    }
                    _ = tokio::time::sleep(delay) => {}
                }
            }
        }
    }
}
