use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct Preferences {
    pub schema_version: u8,
    pub enabled_packs: Vec<String>,
    pub active_page: String,
    pub layout: String,
    pub obs_host: String,
    pub obs_port: u16,
    pub comfyui_url: String,
}

impl Preferences {
    pub fn initial() -> Self {
        serde_json::from_str(include_str!(
            "../../../../configs/ui/extend-preview-defaults.json"
        ))
        .expect("valid bundled preview defaults")
    }

    pub fn require_pack(&self, pack: &str) -> Result<(), String> {
        if self.enabled_packs.iter().any(|item| item == pack) {
            Ok(())
        } else {
            Err("Enable this workspace in Settings first".into())
        }
    }

    pub fn validate(&self) -> Result<(), String> {
        if self.schema_version != 1 {
            return Err("Unsupported preview settings version".into());
        }
        if self.enabled_packs.is_empty()
            || self.enabled_packs.len() > 2
            || self
                .enabled_packs
                .iter()
                .any(|item| !matches!(item.as_str(), "stream" | "content"))
            || (self.enabled_packs.len() == 2 && self.enabled_packs[0] == self.enabled_packs[1])
        {
            return Err("Choose Stream, Create or both".into());
        }
        match self.active_page.as_str() {
            "home" | "settings" => (),
            "stream" => self.require_pack("stream")?,
            "create" | "library" => self.require_pack("content")?,
            _ => return Err("Unknown page".into()),
        }
        if !matches!(self.layout.as_str(), "guided" | "compact") {
            return Err("Unknown navigation layout".into());
        }
        if self.obs_host.is_empty()
            || self.obs_host.len() > 253
            || self
                .obs_host
                .chars()
                .any(|c| !(c.is_ascii_alphanumeric() || matches!(c, '.' | '-' | ':' | '[' | ']')))
            || self.obs_port == 0
        {
            return Err("Enter an OBS hostname and valid port".into());
        }
        let url = url::Url::parse(&self.comfyui_url).map_err(|_| "Enter a valid ComfyUI URL")?;
        if !matches!(url.scheme(), "http" | "https") || url.host_str().is_none() {
            return Err("ComfyUI requires an HTTP or HTTPS address".into());
        }
        if !url.username().is_empty()
            || url.password().is_some()
            || url.query().is_some()
            || url.fragment().is_some()
        {
            return Err("ComfyUI URL cannot contain credentials or query parameters".into());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn pack_admission_and_active_page_are_native_constraints() {
        let mut prefs = Preferences::initial();
        prefs.enabled_packs = vec!["stream".into()];
        assert!(prefs.require_pack("content").is_err());
        prefs.active_page = "library".into();
        assert!(prefs.validate().is_err());
        prefs.active_page = "stream".into();
        assert!(prefs.validate().is_ok());
    }
    #[test]
    fn credentials_never_enter_public_preferences() {
        let mut value = serde_json::to_value(Preferences::initial()).unwrap();
        value["obs_password"] = "synthetic-secret".into();
        assert!(serde_json::from_value::<Preferences>(value).is_err());
    }
    #[test]
    fn invalid_schemas_packs_and_secret_urls_are_rejected() {
        let mut prefs = Preferences::initial();
        prefs.schema_version = 2;
        assert!(prefs.validate().is_err());
        prefs = Preferences::initial();
        prefs.enabled_packs = vec!["stream".into(), "stream".into()];
        assert!(prefs.validate().is_err());
        prefs = Preferences::initial();
        prefs.comfyui_url = "http://user:secret@example.invalid".into();
        assert!(prefs.validate().is_err());
    }
    #[test]
    fn defaults_and_both_presentations_share_the_same_packs() {
        let mut prefs = Preferences::initial();
        assert!(prefs.validate().is_ok());
        prefs.layout = "compact".into();
        assert!(prefs.validate().is_ok());
        assert_eq!(prefs.enabled_packs, Preferences::initial().enabled_packs);
    }
}
