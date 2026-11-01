//! Shared, versioned readiness contract for both Extend desktop apps.
//!
//! Local probes stay in each native app because they own their authenticated
//! OBS/ComfyUI clients. This crate owns the common state model, persistence,
//! capability calculation and outbound OpenTechnology event contract.

use local_settings::{LocalSettings, OsCredentials, SettingsError};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::{
    collections::HashMap,
    path::Path,
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use time::{format_description::well_known::Rfc3339, OffsetDateTime};
use url::Url;

pub const SCHEMA_VERSION: u8 = 1;
pub const MANIFEST_VERSION: &str = "2026.09.1";
const API_KEY: &str = "opentechnology-api-key";
const DEFAULT_TTL: Duration = Duration::from_secs(5 * 60);

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReadinessStatus {
    NotChecked,
    Ready,
    Blocked,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CheckObservation {
    pub event_id: String,
    pub check_id: String,
    pub status: ReadinessStatus,
    pub observed_at: String,
    pub expires_at: Option<String>,
    pub summary: String,
    pub evidence: Map<String, Value>,
}

impl CheckObservation {
    pub fn ready(check_id: &str, summary: &str, evidence: Map<String, Value>) -> Self {
        Self::new(ReadinessStatus::Ready, check_id, summary, evidence)
    }

    pub fn blocked(check_id: &str, summary: &str) -> Self {
        Self::new(ReadinessStatus::Blocked, check_id, summary, Map::new())
    }

    pub fn failed(check_id: &str, summary: &str) -> Self {
        Self::new(ReadinessStatus::Failed, check_id, summary, Map::new())
    }

    fn new(
        status: ReadinessStatus,
        check_id: &str,
        summary: &str,
        evidence: Map<String, Value>,
    ) -> Self {
        let now = SystemTime::now();
        Self {
            event_id: unique_id("event"),
            check_id: check_id.into(),
            status,
            observed_at: timestamp(now),
            expires_at: Some(timestamp(now + DEFAULT_TTL)),
            summary: summary.chars().take(500).collect(),
            evidence: sanitize_evidence(evidence),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct CapabilityReadiness {
    pub capability_id: String,
    pub label: String,
    pub status: ReadinessStatus,
    pub summary: String,
    pub required_checks: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReadinessManifest {
    pub schema_version: u8,
    pub manifest_version: String,
    pub product: String,
    pub checks: Vec<CheckDefinition>,
    pub capabilities: Vec<CapabilityDefinition>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CheckDefinition {
    pub id: String,
    pub label: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityDefinition {
    pub id: String,
    pub label: String,
    pub requires: Vec<String>,
}

impl ReadinessManifest {
    pub fn parse(source: &str) -> Result<Self, String> {
        let manifest: Self =
            serde_json::from_str(source).map_err(|_| "Readiness manifest is invalid JSON")?;
        if manifest.schema_version != SCHEMA_VERSION
            || manifest.manifest_version != MANIFEST_VERSION
            || manifest.product.trim().is_empty()
        {
            return Err("Readiness manifest version or product is unsupported".into());
        }
        let check_ids: std::collections::HashSet<_> = manifest
            .checks
            .iter()
            .map(|item| item.id.as_str())
            .collect();
        if check_ids.len() != manifest.checks.len()
            || manifest.capabilities.iter().any(|capability| {
                capability.requires.is_empty()
                    || capability
                        .requires
                        .iter()
                        .any(|check_id| !check_ids.contains(check_id.as_str()))
            })
        {
            return Err("Readiness manifest has duplicate or unresolved check IDs".into());
        }
        Ok(manifest)
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ReadinessSnapshot {
    pub schema_version: u8,
    pub manifest_version: String,
    pub product: String,
    pub machine_id: String,
    pub setup_run_id: String,
    pub generated_at: String,
    pub checks: Vec<CheckObservation>,
    pub capabilities: Vec<CapabilityReadiness>,
}

impl ReadinessSnapshot {
    pub fn new(
        product: &str,
        machine_id: &str,
        checks: Vec<CheckObservation>,
        capabilities: &[(&str, &str, &[&str])],
    ) -> Self {
        let capabilities = capabilities
            .iter()
            .map(|(id, label, required)| capability(id, label, required, &checks))
            .collect();
        Self {
            schema_version: SCHEMA_VERSION,
            manifest_version: MANIFEST_VERSION.into(),
            product: product.into(),
            machine_id: machine_id.into(),
            setup_run_id: unique_id("run"),
            generated_at: timestamp(SystemTime::now()),
            checks,
            capabilities,
        }
    }

    pub fn capability_ready(&self, id: &str) -> bool {
        self.capabilities
            .iter()
            .any(|item| item.capability_id == id && item.status == ReadinessStatus::Ready)
    }

    pub fn from_manifest(
        machine_id: &str,
        checks: Vec<CheckObservation>,
        manifest: &ReadinessManifest,
    ) -> Self {
        let specs: Vec<_> = manifest
            .capabilities
            .iter()
            .map(|item| (item.id.clone(), item.label.clone(), item.requires.clone()))
            .collect();
        let refs: Vec<_> = specs
            .iter()
            .map(|(id, label, required)| {
                (
                    id.as_str(),
                    label.as_str(),
                    required.iter().map(String::as_str).collect::<Vec<_>>(),
                )
            })
            .collect();
        let capabilities: Vec<_> = refs
            .iter()
            .map(|(id, label, required)| capability(id, label, required, &checks))
            .collect();
        Self {
            schema_version: manifest.schema_version,
            manifest_version: manifest.manifest_version.clone(),
            product: manifest.product.clone(),
            machine_id: machine_id.into(),
            setup_run_id: unique_id("run"),
            generated_at: timestamp(SystemTime::now()),
            checks,
            capabilities,
        }
    }
}

fn capability(
    id: &str,
    label: &str,
    required: &[&str],
    checks: &[CheckObservation],
) -> CapabilityReadiness {
    let by_id: HashMap<_, _> = checks
        .iter()
        .map(|observation| (observation.check_id.as_str(), observation))
        .collect();
    let present: Vec<_> = required
        .iter()
        .filter_map(|check_id| by_id.get(check_id).copied())
        .collect();
    let (status, summary) = if present.len() != required.len() {
        (
            ReadinessStatus::NotChecked,
            "Required checks have not run on this device".into(),
        )
    } else if let Some(failed) = present
        .iter()
        .find(|item| item.status == ReadinessStatus::Failed)
    {
        (ReadinessStatus::Failed, failed.summary.clone())
    } else if let Some(blocked) = present
        .iter()
        .find(|item| item.status != ReadinessStatus::Ready)
    {
        (ReadinessStatus::Blocked, blocked.summary.clone())
    } else {
        (
            ReadinessStatus::Ready,
            format!("All {} required checks passed", required.len()),
        )
    };
    CapabilityReadiness {
        capability_id: id.into(),
        label: label.into(),
        status,
        summary,
        required_checks: required.iter().map(|value| (*value).into()).collect(),
    }
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
struct PublicState {
    machine_id: String,
    sync: PublicSyncSettings,
    snapshot: Option<ReadinessSnapshot>,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
struct PublicSyncSettings {
    enabled: bool,
    base_url: String,
    project_id: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct SyncSettingsView {
    pub enabled: bool,
    pub base_url: String,
    pub project_id: String,
    pub machine_id: String,
    pub api_key_set: bool,
}

#[derive(Clone, Debug, Deserialize)]
pub struct SyncSettingsUpdate {
    pub enabled: bool,
    pub base_url: String,
    pub project_id: String,
    pub machine_id: String,
    pub api_key: Option<String>,
    #[serde(default)]
    pub clear_api_key: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct SyncReport {
    pub attempted: usize,
    pub accepted: usize,
    pub duplicates: usize,
    pub failures: Vec<String>,
}

#[derive(Clone)]
pub struct SetupEngine {
    state: LocalSettings,
    credentials: OsCredentials,
}

impl SetupEngine {
    pub fn new(root: &Path, product: &str) -> Result<Self, SettingsError> {
        let state = LocalSettings::new(root.join("readiness"), product)?;
        let credentials = OsCredentials::new("HybridCreatorPlatform", product)?;
        let engine = Self { state, credentials };
        let mut current = engine.load()?;
        if current.machine_id.is_empty() {
            current.machine_id = default_machine_id();
            engine.state.save(&current)?;
        }
        Ok(engine)
    }

    pub fn settings(&self) -> Result<SyncSettingsView, String> {
        let state = self.load().map_err(|error| error.to_string())?;
        Ok(SyncSettingsView {
            enabled: state.sync.enabled,
            base_url: state.sync.base_url,
            project_id: state.sync.project_id,
            machine_id: state.machine_id,
            api_key_set: self
                .credentials
                .get(API_KEY)
                .map_err(|error| error.to_string())?
                .is_some(),
        })
    }

    pub fn save_settings(&self, update: SyncSettingsUpdate) -> Result<SyncSettingsView, String> {
        validate_settings(&update)?;
        let mut state = self.load().map_err(|error| error.to_string())?;
        let previous_key = self
            .credentials
            .get(API_KEY)
            .map_err(|error| error.to_string())?;
        let effective_key = if update.clear_api_key {
            None
        } else {
            update.api_key.as_ref().or(previous_key.as_ref())
        };
        if update.enabled && effective_key.is_none() {
            return Err("Save an OpenTechnology API key before enabling synchronization".into());
        }
        let key_changed = update.clear_api_key || update.api_key.is_some();
        if update.clear_api_key {
            self.credentials
                .clear(API_KEY)
                .map_err(|error| error.to_string())?;
        } else if let Some(ref key) = update.api_key {
            self.credentials
                .set(API_KEY, key)
                .map_err(|error| error.to_string())?;
        }
        state.machine_id = update.machine_id.trim().into();
        state.sync = PublicSyncSettings {
            enabled: update.enabled,
            base_url: update.base_url.trim().trim_end_matches('/').into(),
            project_id: update.project_id.trim().into(),
        };
        if let Err(error) = self.state.save(&state) {
            if key_changed {
                match previous_key.as_deref() {
                    Some(value) => {
                        let _ = self.credentials.set(API_KEY, value);
                    }
                    None => {
                        let _ = self.credentials.clear(API_KEY);
                    }
                }
            }
            return Err(error.to_string());
        }
        self.settings()
    }

    pub fn save_snapshot(
        &self,
        mut snapshot: ReadinessSnapshot,
    ) -> Result<ReadinessSnapshot, String> {
        let mut state = self.load().map_err(|error| error.to_string())?;
        snapshot.machine_id = state.machine_id.clone();
        state.snapshot = Some(snapshot.clone());
        self.state.save(&state).map_err(|error| error.to_string())?;
        Ok(snapshot)
    }

    pub fn latest(&self) -> Result<Option<ReadinessSnapshot>, String> {
        let mut state = self.load().map_err(|error| error.to_string())?;
        if let Some(ref mut value) = state.snapshot {
            if expire_snapshot(value) {
                self.state.save(&state).map_err(|error| error.to_string())?;
            }
        }
        Ok(state.snapshot)
    }

    pub async fn publish_latest(&self) -> Result<SyncReport, String> {
        let mut state = self.load().map_err(|error| error.to_string())?;
        if !state.sync.enabled {
            return Err("Enable OpenTechnology synchronization first".into());
        }
        let key = self
            .credentials
            .get(API_KEY)
            .map_err(|error| error.to_string())?
            .ok_or("Save an OpenTechnology API key first")?;
        if let Some(ref mut value) = state.snapshot {
            if expire_snapshot(value) {
                self.state.save(&state).map_err(|error| error.to_string())?;
            }
        }
        let snapshot = state
            .snapshot
            .ok_or("Run readiness checks before synchronizing")?;
        let endpoint = format!(
            "{}/api/projects/{}/setup/events",
            state.sync.base_url, state.sync.project_id
        );
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .build()
            .map_err(|_| "Could not prepare the synchronization client")?;
        Ok(publish_snapshot(&client, &endpoint, &key, &snapshot).await)
    }

    fn load(&self) -> Result<PublicState, SettingsError> {
        self.state.load()
    }
}

async fn publish_snapshot(
    client: &reqwest::Client,
    endpoint: &str,
    key: &str,
    snapshot: &ReadinessSnapshot,
) -> SyncReport {
    let mut report = SyncReport {
        attempted: 0,
        accepted: 0,
        duplicates: 0,
        failures: Vec::new(),
    };
    for check in &snapshot.checks {
        if check.status == ReadinessStatus::NotChecked {
            continue;
        }
        report.attempted += 1;
        let event = setup_event(snapshot, check);
        match client
            .post(endpoint)
            .bearer_auth(key)
            .json(&event)
            .send()
            .await
        {
            Ok(response) if response.status().is_success() => {
                let body = response.json::<Value>().await.unwrap_or_default();
                report.accepted += 1;
                if body["duplicate"] == true {
                    report.duplicates += 1;
                }
            }
            Ok(response) => report.failures.push(format!(
                "{}: server returned HTTP {}",
                check.check_id,
                response.status().as_u16()
            )),
            Err(error) => report.failures.push(format!(
                "{}: {}",
                check.check_id,
                if error.is_timeout() {
                    "request timed out"
                } else {
                    "server could not be reached"
                }
            )),
        }
    }
    report
}

fn setup_event(snapshot: &ReadinessSnapshot, check: &CheckObservation) -> Value {
    let mut payload = serde_json::json!({
        "checkId": check.check_id,
        "status": check.status,
        "observedAt": check.observed_at,
        "summary": check.summary,
        "evidence": check.evidence,
    });
    if let Some(ref expires_at) = check.expires_at {
        payload["expiresAt"] = Value::String(expires_at.clone());
    }
    serde_json::json!({
        "eventId": check.event_id,
        "eventType": "setup.check.observed",
        "schemaVersion": SCHEMA_VERSION,
        "manifestVersion": snapshot.manifest_version,
        "machineId": snapshot.machine_id,
        "setupRunId": snapshot.setup_run_id,
        "occurredAt": snapshot.generated_at,
        "payload": payload
    })
}

fn validate_settings(update: &SyncSettingsUpdate) -> Result<(), String> {
    validate_identifier(&update.machine_id, "Machine ID")?;
    if update.enabled || !update.project_id.trim().is_empty() {
        validate_identifier(&update.project_id, "Project ID")?;
    }
    if update.clear_api_key && update.api_key.is_some() {
        return Err("Choose either a new API key or Clear saved API key".into());
    }
    if update.api_key.as_deref() == Some("") {
        return Err("A new API key cannot be empty".into());
    }
    if update.enabled || !update.base_url.trim().is_empty() {
        let parsed = Url::parse(update.base_url.trim())
            .map_err(|_| "OpenTechnology URL must be a valid HTTP or HTTPS URL")?;
        if !matches!(parsed.scheme(), "http" | "https")
            || parsed.host_str().is_none()
            || !parsed.username().is_empty()
            || parsed.password().is_some()
            || parsed.query().is_some()
            || parsed.fragment().is_some()
        {
            return Err(
                "OpenTechnology URL cannot contain credentials, query values or fragments".into(),
            );
        }
    }
    Ok(())
}

fn validate_identifier(value: &str, label: &str) -> Result<(), String> {
    let value = value.trim();
    if value.is_empty()
        || value.len() > 100
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-' | b'_'))
    {
        return Err(format!(
            "{label} must use only letters, numbers, dots, underscores and hyphens"
        ));
    }
    Ok(())
}

fn expire_snapshot(snapshot: &mut ReadinessSnapshot) -> bool {
    let now = OffsetDateTime::now_utc();
    let mut changed = false;
    for check in &mut snapshot.checks {
        let expired = check
            .expires_at
            .as_deref()
            .and_then(|value| OffsetDateTime::parse(value, &Rfc3339).ok())
            .is_some_and(|expires| expires <= now);
        if expired {
            changed = true;
            check.status = ReadinessStatus::Blocked;
            check.summary = "Evidence expired; run readiness checks again".into();
            check.event_id = unique_id("event");
            check.observed_at = now
                .format(&Rfc3339)
                .unwrap_or_else(|_| timestamp(SystemTime::now()));
            check.expires_at = None;
        }
    }
    let specs: Vec<_> = snapshot
        .capabilities
        .iter()
        .map(|item| {
            (
                item.capability_id.clone(),
                item.label.clone(),
                item.required_checks.clone(),
            )
        })
        .collect();
    snapshot.capabilities = specs
        .iter()
        .map(|(id, label, required)| {
            let refs: Vec<_> = required.iter().map(String::as_str).collect();
            capability(id, label, &refs, &snapshot.checks)
        })
        .collect();
    changed
}

fn sanitize_evidence(evidence: Map<String, Value>) -> Map<String, Value> {
    evidence
        .into_iter()
        .filter(|(key, value)| {
            let lower = key.to_ascii_lowercase();
            ![
                "password",
                "secret",
                "token",
                "credential",
                "streamkey",
                "stream_key",
                "apikey",
                "api_key",
            ]
            .iter()
            .any(|word| lower.contains(word))
                && matches!(
                    value,
                    Value::String(_) | Value::Number(_) | Value::Bool(_) | Value::Array(_)
                )
        })
        .take(32)
        .collect()
}

fn default_machine_id() -> String {
    format!("{}-{}", std::env::consts::OS, unique_number())
}

fn unique_id(prefix: &str) -> String {
    format!("{prefix}_{}-{}", unique_number(), std::process::id())
}

fn unique_number() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}

fn timestamp(value: SystemTime) -> String {
    let duration = value.duration_since(UNIX_EPOCH).unwrap_or_default();
    OffsetDateTime::from_unix_timestamp_nanos(duration.as_nanos() as i128)
        .ok()
        .and_then(|value| value.format(&Rfc3339).ok())
        .unwrap_or_else(|| "1970-01-01T00:00:00Z".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use wiremock::{
        matchers::{body_json, header, method, path},
        Mock, MockServer, ResponseTemplate,
    };

    #[test]
    fn one_contract_gates_capabilities_from_required_checks() {
        let checks = vec![
            CheckObservation::ready("stream.obs.websocket", "OBS answered", Map::new()),
            CheckObservation::blocked("stream.obs.scenes", "No scenes were found"),
        ];
        let snapshot = ReadinessSnapshot::new(
            "stream-extend",
            "studio-mac",
            checks,
            &[(
                "obs-control",
                "OBS control",
                &["stream.obs.websocket", "stream.obs.scenes"],
            )],
        );
        assert!(!snapshot.capability_ready("obs-control"));
        assert_eq!(snapshot.capabilities[0].status, ReadinessStatus::Blocked);
    }

    #[test]
    fn event_contract_is_versioned_and_redacts_sensitive_evidence_keys() {
        let mut evidence = Map::new();
        evidence.insert("detectedVersion".into(), Value::String("31.0".into()));
        evidence.insert("apiToken".into(), Value::String("do-not-send".into()));
        let check = CheckObservation::ready("stream.obs.websocket", "OBS answered", evidence);
        assert!(check.evidence.contains_key("detectedVersion"));
        assert!(!check.evidence.contains_key("apiToken"));
        let snapshot = ReadinessSnapshot::new(
            "stream-extend",
            "studio-mac",
            vec![check.clone()],
            &[("obs-control", "OBS control", &["stream.obs.websocket"])],
        );
        let event = setup_event(&snapshot, &check);
        assert_eq!(event["schemaVersion"], SCHEMA_VERSION);
        assert_eq!(event["eventType"], "setup.check.observed");
        assert!(!event.to_string().contains("do-not-send"));
    }

    #[test]
    fn local_state_round_trip_never_serializes_api_key() {
        let root = std::env::temp_dir().join(unique_id("hcp-readiness"));
        let engine = SetupEngine::new(&root, "test-product").unwrap();
        let state = engine.load().unwrap();
        let serialized = serde_json::to_string(&state).unwrap();
        assert!(!serialized.contains("api_key"));
        assert!(!state.machine_id.is_empty());
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn identifiers_and_urls_are_restricted() {
        let valid = SyncSettingsUpdate {
            enabled: true,
            base_url: "https://tasks.example.com".into(),
            project_id: "project-123".into(),
            machine_id: "studio-mac".into(),
            api_key: None,
            clear_api_key: false,
        };
        assert!(validate_settings(&valid).is_ok());
        assert!(validate_settings(&SyncSettingsUpdate {
            base_url: "https://user:secret@example.com?q=1".into(),
            ..valid.clone()
        })
        .is_err());
        assert!(validate_settings(&SyncSettingsUpdate {
            machine_id: "../escape".into(),
            ..valid
        })
        .is_err());
    }

    #[test]
    fn manifest_rejects_unresolved_capability_checks() {
        let valid = r#"{
          "schema_version": 1,
          "manifest_version": "2026.09.1",
          "product": "stream-extend",
          "checks": [{"id":"stream.obs.websocket","label":"OBS WebSocket"}],
          "capabilities": [{"id":"obs-control","label":"OBS control","requires":["stream.obs.websocket"]}]
        }"#;
        let manifest = ReadinessManifest::parse(valid).unwrap();
        assert_eq!(manifest.product, "stream-extend");
        assert!(
            ReadinessManifest::parse(&valid.replace("stream.obs.websocket\"]", "missing\"]"))
                .is_err()
        );
    }

    #[test]
    fn expired_evidence_is_replaced_with_a_new_blocking_observation() {
        let check = CheckObservation::ready("stream.obs.websocket", "OBS answered", Map::new());
        let original_event_id = check.event_id.clone();
        let mut snapshot = ReadinessSnapshot::new(
            "stream-extend",
            "studio-mac",
            vec![check],
            &[("obs-control", "OBS control", &["stream.obs.websocket"])],
        );
        snapshot.checks[0].expires_at = Some("1970-01-01T00:00:00Z".into());

        assert!(expire_snapshot(&mut snapshot));
        assert_eq!(snapshot.checks[0].status, ReadinessStatus::Blocked);
        assert_ne!(snapshot.checks[0].event_id, original_event_id);
        assert!(snapshot.checks[0].expires_at.is_none());
        assert!(!snapshot.capability_ready("obs-control"));
    }

    #[tokio::test]
    async fn publisher_sends_the_exact_authenticated_ingestion_contract() {
        let server = MockServer::start().await;
        let check = CheckObservation::ready("creator.comfyui.api", "ComfyUI answered", Map::new());
        let snapshot = ReadinessSnapshot::new(
            "creator-extend",
            "studio-mac",
            vec![check.clone()],
            &[("comfy-workflows", "ComfyUI", &["creator.comfyui.api"])],
        );
        let event = setup_event(&snapshot, &check);
        Mock::given(method("POST"))
            .and(path("/api/projects/project-1/setup/events"))
            .and(header("authorization", "Bearer test-key"))
            .and(body_json(event))
            .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
                "accepted": true,
                "duplicate": false
            })))
            .expect(1)
            .mount(&server)
            .await;
        let report = publish_snapshot(
            &reqwest::Client::new(),
            &format!("{}/api/projects/project-1/setup/events", server.uri()),
            "test-key",
            &snapshot,
        )
        .await;
        assert_eq!(report.attempted, 1);
        assert_eq!(report.accepted, 1);
        assert!(report.failures.is_empty());
    }
}
