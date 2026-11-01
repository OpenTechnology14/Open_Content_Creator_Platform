//! Persistent, redacted Creator Extend connection settings.

use crate::AppConfig;
use local_settings::{LocalSettings, OsCredentials, SettingsError};
use relay_client::{Product, RelayConfig, RelayMode};
use serde::{Deserialize, Serialize};
use std::path::Path;
use url::Url;

const MINIO_ACCESS_KEY: &str = "minio-access-key";
const MINIO_SECRET_KEY: &str = "minio-secret-key";

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
        Ok(self.public.load::<PublicSettings>()?.into_config())
    }

    pub fn load_credentials(&self) -> Result<(Option<String>, Option<String>), SettingsError> {
        Ok((
            self.credentials.get(MINIO_ACCESS_KEY)?,
            self.credentials.get(MINIO_SECRET_KEY)?,
        ))
    }

    pub fn save(
        &self,
        current: &AppConfig,
        update: ConnectionSettingsUpdate,
    ) -> Result<AppConfig, String> {
        update.validate()?;
        let mut next = current.clone();
        next.comfyui_url = normalize_url(&update.comfyui_url)?;
        next.minio_endpoint = normalize_url(&update.minio_endpoint)?;
        next.api_url = normalize_url(&update.api_url)?;
        next.blender_path = normalize_optional_path(update.blender_path);
        next.krita_path = normalize_optional_path(update.krita_path);

        let previous_access_key = next.minio_access_key.clone();
        let previous_secret_key = next.minio_secret_key.clone();
        let access_changed = update.clear_minio_access_key || update.minio_access_key.is_some();
        let secret_changed = update.clear_minio_secret_key || update.minio_secret_key.is_some();
        next.minio_access_key = desired_secret(
            next.minio_access_key,
            update.minio_access_key,
            update.clear_minio_access_key,
        );
        next.minio_secret_key = desired_secret(
            next.minio_secret_key,
            update.minio_secret_key,
            update.clear_minio_secret_key,
        );

        if access_changed {
            write_secret(
                &self.credentials,
                MINIO_ACCESS_KEY,
                next.minio_access_key.as_deref(),
            )?;
        }
        if secret_changed {
            if let Err(error) = write_secret(
                &self.credentials,
                MINIO_SECRET_KEY,
                next.minio_secret_key.as_deref(),
            ) {
                if access_changed {
                    let _ = write_secret(
                        &self.credentials,
                        MINIO_ACCESS_KEY,
                        previous_access_key.as_deref(),
                    );
                }
                return Err(error);
            }
        }
        if let Err(error) = self.public.save(&PublicSettings::from(&next)) {
            if access_changed {
                let _ = write_secret(
                    &self.credentials,
                    MINIO_ACCESS_KEY,
                    previous_access_key.as_deref(),
                );
            }
            if secret_changed {
                let _ = write_secret(
                    &self.credentials,
                    MINIO_SECRET_KEY,
                    previous_secret_key.as_deref(),
                );
            }
            return Err(error.to_string());
        }
        Ok(next)
    }
}

fn desired_secret(
    current: Option<String>,
    replacement: Option<String>,
    clear: bool,
) -> Option<String> {
    if clear {
        None
    } else if let Some(secret) = replacement {
        Some(secret)
    } else {
        current
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
    pub comfyui_url: String,
    pub minio_endpoint: String,
    pub minio_access_key: Option<String>,
    pub minio_secret_key: Option<String>,
    #[serde(default)]
    pub clear_minio_access_key: bool,
    #[serde(default)]
    pub clear_minio_secret_key: bool,
    pub blender_path: Option<String>,
    pub krita_path: Option<String>,
    pub api_url: String,
}

impl ConnectionSettingsUpdate {
    fn validate(&self) -> Result<(), String> {
        normalize_url(&self.comfyui_url)?;
        normalize_url(&self.minio_endpoint)?;
        normalize_url(&self.api_url)?;
        validate_secret_change(
            self.minio_access_key.as_deref(),
            self.clear_minio_access_key,
            "MinIO access key",
        )?;
        validate_secret_change(
            self.minio_secret_key.as_deref(),
            self.clear_minio_secret_key,
            "MinIO secret key",
        )
    }
}

fn validate_secret_change(value: Option<&str>, clear: bool, label: &str) -> Result<(), String> {
    if clear && value.is_some() {
        return Err(format!(
            "Choose either a new {label} or Clear saved {label}"
        ));
    }
    if value == Some("") {
        return Err(format!("A new {label} cannot be empty"));
    }
    Ok(())
}

#[derive(Debug, Clone, Serialize)]
pub struct ConnectionSettingsView {
    pub comfyui_url: String,
    pub minio_endpoint: String,
    pub minio_access_key_set: bool,
    pub minio_secret_key_set: bool,
    pub blender_path: Option<String>,
    pub krita_path: Option<String>,
    pub api_url: String,
}

impl From<&AppConfig> for ConnectionSettingsView {
    fn from(config: &AppConfig) -> Self {
        Self {
            comfyui_url: config.comfyui_url.clone(),
            minio_endpoint: config.minio_endpoint.clone(),
            minio_access_key_set: config.minio_access_key.is_some(),
            minio_secret_key_set: config.minio_secret_key.is_some(),
            blender_path: config.blender_path.clone(),
            krita_path: config.krita_path.clone(),
            api_url: config.api_url.clone(),
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
struct PublicSettings {
    comfyui_url: String,
    minio_endpoint: String,
    blender_path: Option<String>,
    krita_path: Option<String>,
    api_url: String,
}

impl Default for PublicSettings {
    fn default() -> Self {
        Self {
            comfyui_url: "http://localhost:8188".into(),
            minio_endpoint: "http://localhost:9000".into(),
            blender_path: None,
            krita_path: None,
            api_url: "http://localhost:8000".into(),
        }
    }
}

impl From<&AppConfig> for PublicSettings {
    fn from(config: &AppConfig) -> Self {
        Self {
            comfyui_url: config.comfyui_url.clone(),
            minio_endpoint: config.minio_endpoint.clone(),
            blender_path: config.blender_path.clone(),
            krita_path: config.krita_path.clone(),
            api_url: config.api_url.clone(),
        }
    }
}

impl PublicSettings {
    fn into_config(self) -> AppConfig {
        AppConfig {
            comfyui_url: self.comfyui_url,
            minio_endpoint: self.minio_endpoint,
            minio_access_key: None,
            minio_secret_key: None,
            blender_path: self.blender_path,
            krita_path: self.krita_path,
            api_url: self.api_url,
            relay: RelayConfig {
                mode: RelayMode::Local,
                product: Product::CreatorExtend,
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

fn normalize_optional_path(value: Option<String>) -> Option<String> {
    value.and_then(|path| {
        let trimmed = path.trim();
        (!trimmed.is_empty()).then(|| trimmed.into())
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frontend_view_redacts_both_minio_credentials() {
        let mut config = AppConfig::default();
        config.minio_access_key = Some("access-secret".into());
        config.minio_secret_key = Some("super-secret".into());
        let value = serde_json::to_value(ConnectionSettingsView::from(&config)).unwrap();
        assert_eq!(value["minio_access_key_set"], true);
        assert_eq!(value["minio_secret_key_set"], true);
        assert!(!value.to_string().contains("access-secret"));
        assert!(!value.to_string().contains("super-secret"));
    }

    #[test]
    fn validation_rejects_unsafe_urls_and_ambiguous_secret_changes() {
        assert!(normalize_url("file:///tmp/service").is_err());
        assert!(normalize_url("http://user:secret@localhost:8188").is_err());
        assert!(normalize_url("http://localhost:8188?token=secret").is_err());
        assert_eq!(
            normalize_url("http://localhost:8188/").unwrap(),
            "http://localhost:8188"
        );
        assert!(validate_secret_change(Some("new"), true, "key").is_err());
        assert!(validate_secret_change(None, false, "key").is_ok());
    }
}
