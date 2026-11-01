//! Multi-device sync module.
//!
//! Handles bidirectional sync of settings, presets, and workflows
//! between devices via the relay. Uses a last-write-wins strategy
//! with version vectors for conflict resolution.

use crate::{RelayError, RelayMessage, SubscriptionTier};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Syncable data categories.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum SyncCategory {
    /// App preferences (theme, layout, notification settings).
    Settings,
    /// OBS scene presets, ComfyUI workflow presets.
    Presets,
    /// ComfyUI workflow JSON files.
    Workflows,
    /// Role profiles and search configs (if sharing across devices).
    Profiles,
}

impl SyncCategory {
    /// Minimum subscription tier required to sync this category.
    pub fn required_tier(&self) -> SubscriptionTier {
        match self {
            // Settings sync requires Pro
            SyncCategory::Settings => SubscriptionTier::Pro,
            SyncCategory::Presets => SubscriptionTier::Pro,
            SyncCategory::Workflows => SubscriptionTier::Pro,
            SyncCategory::Profiles => SubscriptionTier::Pro,
        }
    }

    /// Key prefix used in relay sync messages.
    pub fn prefix(&self) -> &str {
        match self {
            SyncCategory::Settings => "settings",
            SyncCategory::Presets => "presets",
            SyncCategory::Workflows => "workflows",
            SyncCategory::Profiles => "profiles",
        }
    }
}

/// A single sync entry with version tracking.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncEntry {
    pub key: String,
    pub value: serde_json::Value,
    pub version: u64,
    pub updated_at: u64,
    pub device_id: String,
}

/// Local sync state — persisted to app data directory.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SyncState {
    pub entries: HashMap<String, SyncEntry>,
    pub last_sync_at: Option<u64>,
}

impl SyncState {
    pub fn load(app_data_dir: &std::path::Path) -> Self {
        let path = app_data_dir.join("sync_state.json");
        match std::fs::read_to_string(&path) {
            Ok(json) => serde_json::from_str(&json).unwrap_or_default(),
            Err(_) => Self::default(),
        }
    }

    pub fn save(&self, app_data_dir: &std::path::Path) -> Result<(), RelayError> {
        let path = app_data_dir.join("sync_state.json");
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(&path, json)
            .map_err(|e| RelayError::Connection(format!("Failed to save sync state: {}", e)))
    }

    /// Update a local entry and return the relay message to push.
    pub fn update(
        &mut self,
        category: &SyncCategory,
        key: &str,
        value: serde_json::Value,
        device_id: &str,
    ) -> RelayMessage {
        let full_key = format!("{}/{}", category.prefix(), key);
        let version = self
            .entries
            .get(&full_key)
            .map(|e| e.version + 1)
            .unwrap_or(1);

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let entry = SyncEntry {
            key: full_key.clone(),
            value: value.clone(),
            version,
            updated_at: now,
            device_id: device_id.to_string(),
        };

        self.entries.insert(full_key.clone(), entry);
        self.last_sync_at = Some(now);

        RelayMessage::SyncPush {
            key: full_key,
            value,
            version,
        }
    }

    /// Apply an incoming sync entry (from another device via relay).
    /// Returns true if the entry was applied (newer version).
    pub fn apply_remote(
        &mut self,
        key: String,
        value: serde_json::Value,
        version: u64,
        device_id: &str,
    ) -> bool {
        let dominated = self
            .entries
            .get(&key)
            .map(|e| version > e.version)
            .unwrap_or(true);

        if dominated {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs();

            self.entries.insert(
                key.clone(),
                SyncEntry {
                    key,
                    value,
                    version,
                    updated_at: now,
                    device_id: device_id.to_string(),
                },
            );
            true
        } else {
            false
        }
    }
}
