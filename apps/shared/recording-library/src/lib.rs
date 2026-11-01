//! Private local recording inbox shared by both Extend desktop apps.

use fs2::FileExt;
use local_settings::LocalSettings;
use serde::{Deserialize, Serialize};
use std::{
    fs::{self, OpenOptions},
    path::{Path, PathBuf},
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
};
use uuid::Uuid;

const MAX_RECORDINGS: usize = 500;
const VIDEO_EXTENSIONS: &[&str] = &["mkv", "mp4", "mov", "webm", "m4v", "avi", "ts"];

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum RecordingOrigin {
    StreamSession,
    ManualImport,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum RecordingStatus {
    Ready,
    Editing,
    Published,
    Archived,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct RecordingRecord {
    pub id: String,
    pub file_path: String,
    pub file_name: String,
    pub bytes: u64,
    pub created_at_unix: u64,
    pub source_profile_id: Option<String>,
    pub content_profile_id: Option<String>,
    pub origin: RecordingOrigin,
    pub status: RecordingStatus,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
pub struct RecordingView {
    #[serde(flatten)]
    pub record: RecordingRecord,
    pub available: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct LibraryState {
    #[serde(default = "schema_version")]
    schema_version: u8,
    #[serde(default)]
    recordings: Vec<RecordingRecord>,
}

impl Default for LibraryState {
    fn default() -> Self {
        Self {
            schema_version: 1,
            recordings: Vec::new(),
        }
    }
}

fn schema_version() -> u8 {
    1
}

#[derive(Clone, Debug)]
pub struct RecordingLibrary {
    root: PathBuf,
    settings: LocalSettings,
}

impl RecordingLibrary {
    pub fn new(root: impl Into<PathBuf>) -> Result<Self, String> {
        let root = root.into();
        let settings =
            LocalSettings::new(&root, "recordings").map_err(|error| error.to_string())?;
        Ok(Self { root, settings })
    }

    pub fn list(&self) -> Result<Vec<RecordingView>, String> {
        self.with_lock(|state| {
            let mut values = state.recordings.clone();
            values.sort_by_key(|item| std::cmp::Reverse(item.created_at_unix));
            Ok(values
                .into_iter()
                .map(|record| RecordingView {
                    available: Path::new(&record.file_path).is_file(),
                    record,
                })
                .collect())
        })
    }

    pub fn register(
        &self,
        path: impl AsRef<Path>,
        origin: RecordingOrigin,
        source_profile_id: Option<&str>,
        content_profile_id: Option<&str>,
    ) -> Result<RecordingView, String> {
        validate_optional_id(source_profile_id)?;
        validate_optional_id(content_profile_id)?;
        let canonical = path
            .as_ref()
            .canonicalize()
            .map_err(|_| "Recording file does not exist".to_string())?;
        let metadata = canonical
            .metadata()
            .map_err(|_| "Recording metadata is unavailable".to_string())?;
        if !metadata.is_file() || metadata.len() == 0 {
            return Err("Recording must be a non-empty local file".into());
        }
        let extension = canonical
            .extension()
            .and_then(|value| value.to_str())
            .map(str::to_ascii_lowercase)
            .ok_or_else(|| "Recording needs a supported video extension".to_string())?;
        if !VIDEO_EXTENSIONS.contains(&extension.as_str()) {
            return Err("Recording needs a supported video extension".into());
        }
        let file_name = canonical
            .file_name()
            .and_then(|value| value.to_str())
            .ok_or_else(|| "Recording filename is invalid".to_string())?
            .to_string();
        let file_path = canonical.to_string_lossy().into_owned();
        let bytes = metadata.len();
        let timestamp = now_unix();

        self.with_lock(|state| {
            if let Some(existing) = state
                .recordings
                .iter_mut()
                .find(|item| item.file_path == file_path)
            {
                existing.bytes = bytes;
                existing.file_name = file_name.clone();
                if source_profile_id.is_some() {
                    existing.source_profile_id = source_profile_id.map(str::to_string);
                }
                if content_profile_id.is_some() {
                    existing.content_profile_id = content_profile_id.map(str::to_string);
                }
                let value = existing.clone();
                self.save(state)?;
                return Ok(RecordingView {
                    record: value,
                    available: true,
                });
            }
            if state.recordings.len() >= MAX_RECORDINGS {
                if let Some(index) = state
                    .recordings
                    .iter()
                    .enumerate()
                    .filter(|(_, item)| item.status == RecordingStatus::Archived)
                    .min_by_key(|(_, item)| item.created_at_unix)
                    .map(|(index, _)| index)
                {
                    state.recordings.remove(index);
                } else {
                    return Err(
                        "Recording inbox is full; archive an item before adding another".into(),
                    );
                }
            }
            let record = RecordingRecord {
                id: format!("rec-{}", Uuid::new_v4().simple()),
                file_path,
                file_name,
                bytes,
                created_at_unix: timestamp,
                source_profile_id: source_profile_id.map(str::to_string),
                content_profile_id: content_profile_id.map(str::to_string),
                origin,
                status: RecordingStatus::Ready,
            };
            state.recordings.push(record.clone());
            self.save(state)?;
            Ok(RecordingView {
                record,
                available: true,
            })
        })
    }

    pub fn update(
        &self,
        id: &str,
        status: RecordingStatus,
        content_profile_id: Option<&str>,
    ) -> Result<RecordingView, String> {
        validate_id(id)?;
        validate_optional_id(content_profile_id)?;
        self.with_lock(|state| {
            let record = state
                .recordings
                .iter_mut()
                .find(|item| item.id == id)
                .ok_or_else(|| "Unknown recording".to_string())?;
            record.status = status;
            record.content_profile_id = content_profile_id.map(str::to_string);
            let value = record.clone();
            self.save(state)?;
            Ok(RecordingView {
                available: Path::new(&value.file_path).is_file(),
                record: value,
            })
        })
    }

    pub fn reveal(&self, id: &str) -> Result<(), String> {
        validate_id(id)?;
        let record = self
            .list()?
            .into_iter()
            .find(|item| item.record.id == id)
            .ok_or_else(|| "Unknown recording".to_string())?;
        if !record.available {
            return Err("Recording file is no longer available at its saved location".into());
        }
        reveal_path(Path::new(&record.record.file_path))
    }

    fn save(&self, state: &LibraryState) -> Result<(), String> {
        self.settings.save(state).map_err(|error| error.to_string())
    }

    fn with_lock<T>(
        &self,
        operation: impl FnOnce(&mut LibraryState) -> Result<T, String>,
    ) -> Result<T, String> {
        fs::create_dir_all(&self.root).map_err(|_| "Recording storage is unavailable")?;
        let lock_path = self.root.join("recordings.lock");
        let lock = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(lock_path)
            .map_err(|_| "Recording storage is unavailable")?;
        lock.lock_exclusive()
            .map_err(|_| "Recording storage is busy")?;
        let mut state = self
            .settings
            .load::<LibraryState>()
            .map_err(|error| error.to_string())?;
        let result = if state.schema_version == 1 {
            operation(&mut state)
        } else {
            Err("Recording library schema is unsupported".into())
        };
        let _ = FileExt::unlock(&lock);
        result
    }
}

fn validate_optional_id(value: Option<&str>) -> Result<(), String> {
    if let Some(value) = value {
        validate_id(value)?;
    }
    Ok(())
}

fn validate_id(value: &str) -> Result<(), String> {
    if value.is_empty()
        || value.len() > 80
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    {
        return Err("Invalid recording or profile identifier".into());
    }
    Ok(())
}

fn now_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[cfg(target_os = "macos")]
fn reveal_path(path: &Path) -> Result<(), String> {
    run_reveal(Command::new("/usr/bin/open").arg("-R").arg(path))
}

#[cfg(target_os = "windows")]
fn reveal_path(path: &Path) -> Result<(), String> {
    run_reveal(Command::new("explorer.exe").arg(format!("/select,{}", path.display())))
}

#[cfg(all(unix, not(target_os = "macos")))]
fn reveal_path(path: &Path) -> Result<(), String> {
    let parent = path
        .parent()
        .ok_or_else(|| "Recording folder is invalid".to_string())?;
    run_reveal(Command::new("xdg-open").arg(parent))
}

fn run_reveal(command: &mut Command) -> Result<(), String> {
    command
        .spawn()
        .map(|_| ())
        .map_err(|_| "Could not reveal the recording in the system file manager".into())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> (PathBuf, RecordingLibrary, PathBuf) {
        let root = std::env::temp_dir().join(format!("hcp-recordings-{}", Uuid::new_v4()));
        fs::create_dir_all(&root).unwrap();
        let video = root.join("session.mkv");
        fs::write(&video, vec![9u8; 1024]).unwrap();
        let library = RecordingLibrary::new(root.join("state")).unwrap();
        (root, library, video)
    }

    #[test]
    fn register_deduplicates_canonical_paths_and_round_trips_profiles() {
        let (root, library, video) = fixture();
        let first = library
            .register(
                &video,
                RecordingOrigin::StreamSession,
                Some("stream-main"),
                Some("content-main"),
            )
            .unwrap();
        let second = library
            .register(
                &video,
                RecordingOrigin::ManualImport,
                Some("agent-labs"),
                None,
            )
            .unwrap();
        assert_eq!(first.record.id, second.record.id);
        let values = library.list().unwrap();
        assert_eq!(values.len(), 1);
        assert_eq!(
            values[0].record.source_profile_id.as_deref(),
            Some("agent-labs")
        );
        assert_eq!(
            values[0].record.content_profile_id.as_deref(),
            Some("content-main")
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn update_changes_workflow_state_and_reports_a_missing_source_file() {
        let (root, library, video) = fixture();
        let value = library
            .register(&video, RecordingOrigin::ManualImport, None, None)
            .unwrap();
        let updated = library
            .update(
                &value.record.id,
                RecordingStatus::Editing,
                Some("video-review"),
            )
            .unwrap();
        assert_eq!(updated.record.status, RecordingStatus::Editing);
        assert_eq!(
            updated.record.content_profile_id.as_deref(),
            Some("video-review")
        );
        fs::remove_file(video).unwrap();
        assert!(!library.list().unwrap()[0].available);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_empty_unsupported_and_invalid_profile_inputs() {
        let (root, library, video) = fixture();
        let text = root.join("notes.txt");
        fs::write(&text, b"not video").unwrap();
        assert!(library
            .register(&text, RecordingOrigin::ManualImport, None, None)
            .is_err());
        assert!(library
            .register(
                &video,
                RecordingOrigin::ManualImport,
                Some("../escape"),
                None
            )
            .is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
