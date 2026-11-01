//! Persistent, redacted Stream Extend connection settings.

use crate::AppConfig;
use local_settings::{LocalSettings, OsCredentials, SettingsError};
use relay_client::{Product, RelayConfig, RelayMode};
use serde::{Deserialize, Serialize};
use std::path::Path;
use url::Url;

const OBS_PASSWORD: &str = "obs-password";

#[derive(Clone)]
pub struct ConnectionPersistence {
    public: LocalSettings,
    credentials: OsCredentials,
}

impl ConnectionPersistence {
    pub fn new(root: &Path, product: &str) -> Result<Self, SettingsError> {
        Ok(Self {
            public: LocalSettings::new(root, product)?,
            credentials: OsCredentials::new("HybridCreatorPlatform", product)?,
        })
    }

    pub fn load_public(&self) -> Result<AppConfig, SettingsError> {
        let public = self.public.load::<PublicSettings>()?;
        Ok(public.into_config(None))
    }

    pub fn load_password(&self) -> Result<Option<String>, SettingsError> {
        self.credentials.get(OBS_PASSWORD)
    }

    pub fn save(
        &self,
        current: &AppConfig,
        update: ConnectionSettingsUpdate,
    ) -> Result<AppConfig, String> {
        update.validate()?;
        let mut next = current.clone();
        next.obs_host = update.obs_host.trim().into();
        next.obs_port = update.obs_port;
        next.comfyui_url = normalize_url(&update.comfyui_url)?;
        next.grafana_url = normalize_url(&update.grafana_url)?;
        next.api_url = normalize_url(&update.api_url)?;

        let previous_password = next.obs_password.clone();
        let password_changed = update.clear_obs_password || update.obs_password.is_some();
        if update.clear_obs_password {
            next.obs_password = None;
        } else if let Some(password) = update.obs_password {
            next.obs_password = Some(password);
        }
        if password_changed {
            write_secret(
                &self.credentials,
                OBS_PASSWORD,
                next.obs_password.as_deref(),
            )?;
        }
        if let Err(error) = self.public.save(&PublicSettings::from(&next)) {
            if password_changed {
                let _ = write_secret(
                    &self.credentials,
                    OBS_PASSWORD,
                    previous_password.as_deref(),
                );
            }
            return Err(error.to_string());
        }
        Ok(next)
    }
}

fn write_secret(
    credentials: &OsCredentials,
    name: &str,
    value: Option<&str>,
) -> Result<(), String> {
    match value {
        Some(secret) => credentials.set(name, secret),
        None => credentials.clear(name),
    }
    .map_err(|error| error.to_string())
}

#[derive(Debug, Clone, Deserialize)]
pub struct ConnectionSettingsUpdate {
    pub obs_host: String,
    pub obs_port: u16,
    pub obs_password: Option<String>,
    #[serde(default)]
    pub clear_obs_password: bool,
    pub comfyui_url: String,
    pub grafana_url: String,
    pub api_url: String,
}

impl ConnectionSettingsUpdate {
    fn validate(&self) -> Result<(), String> {
        let host = self.obs_host.trim();
        if host.is_empty()
            || host.contains('/')
            || host.contains(':')
            || host.chars().any(char::is_whitespace)
        {
            return Err("OBS host must be a hostname or IP address without a URL scheme".into());
        }
        if self.obs_port == 0 {
            return Err("OBS port must be between 1 and 65535".into());
        }
        if self.clear_obs_password && self.obs_password.is_some() {
            return Err("Choose either a new OBS password or Clear saved password".into());
        }
        if self.obs_password.as_deref() == Some("") {
            return Err("A new OBS password cannot be empty".into());
        }
        normalize_url(&self.comfyui_url)?;
        normalize_url(&self.grafana_url)?;
        normalize_url(&self.api_url)?;
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct ConnectionSettingsView {
    pub obs_host: String,
    pub obs_port: u16,
    pub obs_password_set: bool,
    pub comfyui_url: String,
    pub grafana_url: String,
    pub api_url: String,
}

impl From<&AppConfig> for ConnectionSettingsView {
    fn from(config: &AppConfig) -> Self {
        Self {
            obs_host: config.obs_host.clone(),
            obs_port: config.obs_port,
            obs_password_set: config.obs_password.is_some(),
            comfyui_url: config.comfyui_url.clone(),
            grafana_url: config.grafana_url.clone(),
            api_url: config.api_url.clone(),
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
struct PublicSettings {
    obs_host: String,
    obs_port: u16,
    comfyui_url: String,
    grafana_url: String,
    api_url: String,
}

impl Default for PublicSettings {
    fn default() -> Self {
        Self {
            obs_host: "localhost".into(),
            obs_port: 4455,
            comfyui_url: "http://localhost:8188".into(),
            grafana_url: "http://localhost:3000".into(),
            api_url: "http://localhost:8000".into(),
        }
    }
}

impl From<&AppConfig> for PublicSettings {
    fn from(config: &AppConfig) -> Self {
        Self {
            obs_host: config.obs_host.clone(),
            obs_port: config.obs_port,
            comfyui_url: config.comfyui_url.clone(),
            grafana_url: config.grafana_url.clone(),
            api_url: config.api_url.clone(),
        }
    }
}

impl PublicSettings {
    fn into_config(self, obs_password: Option<String>) -> AppConfig {
        AppConfig {
            obs_host: self.obs_host,
            obs_port: self.obs_port,
            obs_password,
            comfyui_url: self.comfyui_url,
            grafana_url: self.grafana_url,
            api_url: self.api_url,
            relay: RelayConfig {
                mode: RelayMode::Local,
                product: Product::StreamExtend,
                ..RelayConfig::default()
            },
        }
    }
}

fn normalize_url(value: &str) -> Result<String, String> {
    let parsed =
        Url::parse(value.trim()).map_err(|_| "Service URLs must be valid HTTP or HTTPS URLs")?;
    if !matches!(parsed.scheme(), "http" | "https") || parsed.host_str().is_none() {
        return Err("Service URLs must use HTTP or HTTPS and include a host".into());
    }
    if !parsed.username().is_empty()
        || parsed.password().is_some()
        || parsed.query().is_some()
        || parsed.fragment().is_some()
    {
        return Err("Service URLs cannot contain credentials, query values or fragments".into());
    }
    Ok(parsed.as_str().trim_end_matches('/').into())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn base_update() -> ConnectionSettingsUpdate {
        ConnectionSettingsUpdate {
            obs_host: "localhost".into(),
            obs_port: 4455,
            obs_password: None,
            clear_obs_password: false,
            comfyui_url: "http://localhost:8188".into(),
            grafana_url: "http://localhost:3000".into(),
            api_url: "http://localhost:8000".into(),
        }
    }

    #[test]
    fn frontend_view_never_contains_the_obs_password() {
        let mut config = AppConfig::default();
        config.obs_password = Some("do-not-return-this".into());
        let value = serde_json::to_value(ConnectionSettingsView::from(&config)).unwrap();
        assert_eq!(value["obs_password_set"], true);
        assert!(!value.to_string().contains("do-not-return-this"));
    }

    #[test]
    fn update_rejects_hosts_urls_and_ambiguous_password_changes() {
        assert!(base_update().validate().is_ok());
        assert_eq!(
            normalize_url("http://localhost:8188/ ").unwrap(),
            "http://localhost:8188"
        );
        assert!(normalize_url("http://user:secret@localhost:8188").is_err());
        assert!(normalize_url("http://localhost:8188?token=secret").is_err());
        let mut invalid_host = base_update();
        invalid_host.obs_host = "http://localhost".into();
        assert!(invalid_host.validate().is_err());
        let mut ambiguous = base_update();
        ambiguous.obs_password = Some("new".into());
        ambiguous.clear_obs_password = true;
        assert!(ambiguous.validate().is_err());
    }
}
