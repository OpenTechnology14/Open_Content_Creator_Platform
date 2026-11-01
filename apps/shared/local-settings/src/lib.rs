//! Local configuration persistence for both Extend desktop apps.
//!
//! Public endpoint settings are JSON in the app's local-data directory. Passwords and keys
//! are stored by the operating system credential manager and never serialized with the JSON.

use keyring::v1::{Entry, Error as KeyringError};
use serde::{de::DeserializeOwned, Serialize};
use std::{
    fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SettingsError {
    #[error("Local settings storage is unavailable")]
    Storage,
    #[error("Saved settings could not be read")]
    Invalid,
    #[error("The operating system credential manager is unavailable")]
    Credential,
}

#[derive(Clone, Debug)]
pub struct LocalSettings {
    path: PathBuf,
}

impl LocalSettings {
    pub fn new(directory: impl Into<PathBuf>, product: &str) -> Result<Self, SettingsError> {
        if product.is_empty()
            || !product
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_'))
        {
            return Err(SettingsError::Storage);
        }
        Ok(Self {
            path: directory.into().join(format!("{product}.json")),
        })
    }

    pub fn load<T: DeserializeOwned + Default>(&self) -> Result<T, SettingsError> {
        match fs::read(&self.path) {
            Ok(bytes) => serde_json::from_slice(&bytes).map_err(|_| SettingsError::Invalid),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(T::default()),
            Err(_) => Err(SettingsError::Storage),
        }
    }

    pub fn save<T: Serialize>(&self, value: &T) -> Result<(), SettingsError> {
        let directory = self.path.parent().ok_or(SettingsError::Storage)?;
        fs::create_dir_all(directory).map_err(|_| SettingsError::Storage)?;
        set_private_directory_permissions(directory)?;
        let temporary = self.path.with_extension(format!("{}.tmp", unique_id()));
        let bytes = serde_json::to_vec_pretty(value).map_err(|_| SettingsError::Invalid)?;
        fs::write(&temporary, bytes).map_err(|_| SettingsError::Storage)?;
        set_private_file_permissions(&temporary)?;
        fs::rename(&temporary, &self.path).map_err(|_| SettingsError::Storage)
    }

    pub fn path(&self) -> &Path {
        &self.path
    }
}

#[derive(Clone, Debug)]
pub struct OsCredentials {
    service: String,
    product: String,
}

impl OsCredentials {
    pub fn new(service: &str, product: &str) -> Result<Self, SettingsError> {
        if service.trim().is_empty() || product.trim().is_empty() {
            return Err(SettingsError::Credential);
        }
        Ok(Self {
            service: service.into(),
            product: product.into(),
        })
    }

    fn entry(&self, name: &str) -> Result<Entry, SettingsError> {
        if name.is_empty()
            || !name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_'))
        {
            return Err(SettingsError::Credential);
        }
        Entry::new(&self.service, &format!("{}.{}", self.product, name))
            .map_err(|_| SettingsError::Credential)
    }

    pub fn get(&self, name: &str) -> Result<Option<String>, SettingsError> {
        match self.entry(name)?.get_password() {
            Ok(secret) => Ok(Some(secret)),
            Err(KeyringError::NoEntry) => Ok(None),
            Err(_) => Err(SettingsError::Credential),
        }
    }

    pub fn set(&self, name: &str, secret: &str) -> Result<(), SettingsError> {
        if secret.is_empty() {
            return Err(SettingsError::Credential);
        }
        self.entry(name)?
            .set_password(secret)
            .map_err(|_| SettingsError::Credential)
    }

    pub fn clear(&self, name: &str) -> Result<(), SettingsError> {
        match self.entry(name)?.delete_credential() {
            Ok(()) | Err(KeyringError::NoEntry) => Ok(()),
            Err(_) => Err(SettingsError::Credential),
        }
    }
}

fn unique_id() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}

#[cfg(unix)]
fn set_private_directory_permissions(path: &Path) -> Result<(), SettingsError> {
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700)).map_err(|_| SettingsError::Storage)
}

#[cfg(not(unix))]
fn set_private_directory_permissions(_path: &Path) -> Result<(), SettingsError> {
    Ok(())
}

#[cfg(unix)]
fn set_private_file_permissions(path: &Path) -> Result<(), SettingsError> {
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(path, fs::Permissions::from_mode(0o600)).map_err(|_| SettingsError::Storage)
}

#[cfg(not(unix))]
fn set_private_file_permissions(_path: &Path) -> Result<(), SettingsError> {
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};

    #[derive(Default, Debug, Deserialize, PartialEq, Serialize)]
    struct Example {
        endpoint: String,
    }

    #[test]
    fn public_settings_round_trip_atomically_without_secret_fields() {
        let root = std::env::temp_dir().join(format!("hcp-settings-{}", unique_id()));
        let store = LocalSettings::new(&root, "com.example.app").unwrap();
        let value = Example {
            endpoint: "http://127.0.0.1:8188".into(),
        };
        store.save(&value).unwrap();
        assert_eq!(store.load::<Example>().unwrap(), value);
        let serialized = fs::read_to_string(store.path()).unwrap();
        assert!(!serialized.contains("password"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_names_that_could_escape_the_settings_directory() {
        assert!(LocalSettings::new(std::env::temp_dir(), "../escape").is_err());
        assert!(OsCredentials::new("", "app").is_err());
    }
}
