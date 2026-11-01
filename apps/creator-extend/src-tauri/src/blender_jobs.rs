//! Owned, bounded Blender still jobs. Persisted metadata never authorizes killing a PID.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    io::Read,
    path::{Path, PathBuf},
    process::Stdio,
    sync::Arc,
    time::Duration,
};
use tokio::{
    process::{Child, Command},
    sync::Mutex,
};
use uuid::Uuid;

#[derive(Clone)]
pub struct BlenderJobs {
    root: PathBuf,
    owned: Arc<Mutex<BTreeMap<String, Arc<Mutex<Child>>>>>,
    submission: Arc<Mutex<()>>,
}

fn identifier(value: &str) -> bool {
    value.len() == 32
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn write_json(path: &Path, value: &Value) -> Result<(), String> {
    let temporary = path.with_extension(format!("json-native-{}", Uuid::new_v4().simple()));
    fs::write(
        &temporary,
        serde_json::to_vec_pretty(value).map_err(|_| "Invalid job metadata")?,
    )
    .map_err(|_| "Cannot save job metadata")?;
    fs::rename(&temporary, path).map_err(|_| "Cannot commit job metadata".into())
}

fn hash_file(path: &Path) -> Result<String, String> {
    let mut file = fs::File::open(path).map_err(|_| "Cannot read selected project")?;
    let mut hash = Sha256::new();
    let mut buffer = [0; 65536];
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|_| "Cannot hash selected project")?;
        if count == 0 {
            break;
        }
        hash.update(&buffer[..count]);
    }
    Ok(format!("{:x}", hash.finalize()))
}

fn validate_scenes(scenes: &[String]) -> Result<(), String> {
    if scenes.is_empty() || scenes.len() > 16 {
        return Err("Select 1–16 scenes".into());
    }
    let distinct: std::collections::BTreeSet<_> = scenes.iter().collect();
    if distinct.len() != scenes.len()
        || scenes.iter().any(|name| {
            name.is_empty() || name.chars().count() > 120 || name.chars().any(char::is_control)
        })
    {
        return Err("Choose distinct, bounded scene names".into());
    }
    Ok(())
}

impl BlenderJobs {
    pub fn new(root: PathBuf) -> Self {
        Self {
            root,
            owned: Arc::new(Mutex::new(BTreeMap::new())),
            submission: Arc::new(Mutex::new(())),
        }
    }

    fn folder(&self, id: &str) -> Result<PathBuf, String> {
        if !identifier(id) {
            return Err("Invalid Blender job ID".into());
        }
        let root = self
            .root
            .canonicalize()
            .map_err(|_| "Job library is unavailable")?;
        let path = root.join(id).canonicalize().map_err(|_| "Job not found")?;
        if !path.starts_with(root) {
            return Err("Job path escapes its library".into());
        }
        Ok(path)
    }

    pub async fn status(&self, id: &str) -> Result<Value, String> {
        let folder = self.folder(id)?;
        let path = folder.join("job.json");
        if fs::metadata(&path)
            .map_err(|_| "Job metadata is unavailable")?
            .len()
            > 131072
        {
            return Err("Job metadata exceeds limits".into());
        }
        let mut value: Value =
            serde_json::from_slice(&fs::read(path).map_err(|_| "Cannot read job metadata")?)
                .map_err(|_| "Invalid job metadata")?;
        if value["job_id"] != id {
            return Err("Job identity mismatch".into());
        }
        let owned = self.owned.lock().await.contains_key(id);
        if !owned
            && matches!(
                value["status"].as_str(),
                Some("starting" | "queued" | "running" | "cancelling")
            )
        {
            value["status"] = json!("interrupted");
        }
        value["process_owned"] = json!(owned);
        if let Some(items) = value["scenes"].as_array() {
            for item in items {
                if item["status"] != "complete" {
                    continue;
                }
                let output =
                    PathBuf::from(value["output"].as_str().ok_or("Missing output folder")?);
                let name = item["artifact"]["file"]
                    .as_str()
                    .ok_or("Missing artifact")?;
                if name.contains(['/', '\\']) || !name.ends_with(".png") {
                    return Err("Invalid artifact name".into());
                }
                let artifact = output
                    .join(name)
                    .canonicalize()
                    .map_err(|_| "Rendered artifact is missing")?;
                if !artifact.starts_with(
                    output
                        .canonicalize()
                        .map_err(|_| "Output folder is missing")?,
                ) {
                    return Err("Artifact escaped output folder".into());
                }
                if hash_file(&artifact)?
                    != item["artifact"]["sha256"]
                        .as_str()
                        .ok_or("Missing artifact checksum")?
                {
                    return Err("Rendered artifact checksum changed".into());
                }
            }
        }
        Ok(value)
    }

    pub async fn list(&self) -> Result<Vec<Value>, String> {
        fs::create_dir_all(&self.root).map_err(|_| "Cannot prepare job library")?;
        let mut results = Vec::new();
        for entry in fs::read_dir(&self.root).map_err(|_| "Cannot inspect job library")? {
            let id = entry
                .map_err(|_| "Cannot inspect job library")?
                .file_name()
                .to_string_lossy()
                .into_owned();
            if identifier(&id) {
                match self.status(&id).await {
                    Ok(value) => results.push(value),
                    Err(error) => {
                        results.push(json!({"job_id":id,"status":"unavailable","error":error}))
                    }
                }
            }
            if results.len() >= 64 {
                break;
            }
        }
        Ok(results)
    }

    pub async fn start(
        &self,
        executable: &str,
        script: &Path,
        project: &str,
        output: &str,
        scenes: Vec<String>,
        parent: Option<String>,
    ) -> Result<String, String> {
        let _submission = self.submission.lock().await;
        validate_scenes(&scenes)?;
        let project = Path::new(project)
            .canonicalize()
            .map_err(|_| "Selected project is missing")?;
        if project
            .extension()
            .and_then(|s| s.to_str())
            .map(|s| s.eq_ignore_ascii_case("blend"))
            != Some(true)
            || !project.is_file()
        {
            return Err("Choose a .blend project".into());
        }
        let size = fs::metadata(&project)
            .map_err(|_| "Cannot inspect project")?
            .len();
        if !(12..=2_147_483_648).contains(&size) {
            return Err("Project size exceeds supported limits".into());
        }
        let mut header = [0; 7];
        fs::File::open(&project)
            .and_then(|mut f| f.read_exact(&mut header))
            .map_err(|_| "Cannot inspect project header")?;
        if &header != b"BLENDER"
            && header[..2] != [0x1f, 0x8b]
            && header[..4] != [0x28, 0xb5, 0x2f, 0xfd]
        {
            return Err("Selected file has no supported Blender project signature".into());
        }
        let output = Path::new(output)
            .canonicalize()
            .map_err(|_| "Choose an existing output directory")?;
        if !output.is_dir() || !script.is_file() {
            return Err("Output folder or packaged job script is unavailable".into());
        }
        if let Some(parent) = &parent {
            if !identifier(parent) {
                return Err("Invalid parent job".into());
            }
        }
        if self.owned.lock().await.len() >= 1 {
            return Err("Wait for or cancel the current Blender job".into());
        }
        fs::create_dir_all(&self.root).map_err(|_| "Cannot prepare job library")?;
        if fs::read_dir(&self.root)
            .map_err(|_| "Cannot inspect job library")?
            .count()
            >= 64
        {
            return Err(
                "Job library limit reached; preserve/archive old jobs before continuing".into(),
            );
        }
        let id = Uuid::new_v4().simple().to_string();
        let folder = self.root.join(&id);
        fs::create_dir(&folder).map_err(|_| "Cannot prepare new job attempt")?;
        let metadata = folder.join("job.json");
        let source_hash = hash_file(&project)?;
        let initial = json!({"schema_version":1,"job_id":id,"attempt_id":id,"parent_job_id":parent,"status":"starting","project":project,"project_sha256":source_hash,"output_root":output,"selected_scenes":scenes,"scenes":[]});
        write_json(&metadata, &initial)?;
        let log_path = folder.join("process.log");
        let log = fs::OpenOptions::new()
            .create_new(true)
            .append(true)
            .open(&log_path)
            .map_err(|_| "Cannot create job log")?;
        let mut command = Command::new(executable);
        command
            .args(["--factory-startup", "--disable-autoexec", "--background"])
            .arg(&project)
            .arg("--python")
            .arg(script)
            .arg("--")
            .arg("--output")
            .arg(&output)
            .arg("--job-id")
            .arg(&id)
            .arg("--metadata")
            .arg(&metadata)
            .arg("--source-sha256")
            .arg(&source_hash);
        for name in &scenes {
            command.arg(format!("--scene={name}"));
        }
        command
            .stdin(Stdio::null())
            .stdout(Stdio::from(
                log.try_clone().map_err(|_| "Cannot open job log")?,
            ))
            .stderr(Stdio::from(log))
            .kill_on_drop(true);
        #[cfg(target_os = "windows")]
        command.creation_flags(0x08000000);
        let child = match command.spawn() {
            Ok(child) => child,
            Err(_) => {
                let mut failed = initial;
                failed["status"] = json!("failed");
                failed["error"] = json!("Blender process could not start");
                write_json(&metadata, &failed)?;
                return Err("Blender process could not start".into());
            }
        };
        let child = Arc::new(Mutex::new(child));
        self.owned.lock().await.insert(id.clone(), child.clone());
        let owned = self.owned.clone();
        let tracked_id = id.clone();
        tokio::spawn(async move {
            let started = std::time::Instant::now();
            loop {
                let mut process = child.lock().await;
                let state = process.try_wait();
                if fs::metadata(&log_path).is_ok_and(|m| m.len() > 1_048_576) {
                    let _ = fs::OpenOptions::new()
                        .write(true)
                        .open(&log_path)
                        .and_then(|f| f.set_len(0));
                }
                match state {
                    Ok(Some(exit)) => {
                        if let Ok(bytes) = fs::read(&metadata) {
                            if let Ok(mut value) = serde_json::from_slice::<Value>(&bytes) {
                                if value["status"] != "cancelled"
                                    && (!exit.success() || value["status"] != "complete")
                                {
                                    value["status"] = json!("failed");
                                }
                                value["process_exit_success"] = json!(exit.success());
                                let _ = write_json(&metadata, &value);
                            }
                        }
                        break;
                    }
                    Err(_) => break,
                    Ok(None) => {}
                }
                if started.elapsed() > Duration::from_secs(1800) {
                    let _ = process.kill().await;
                    if let Ok(bytes) = fs::read(&metadata) {
                        if let Ok(mut value) = serde_json::from_slice::<Value>(&bytes) {
                            value["status"] = json!("failed");
                            value["error"] = json!("job_timeout");
                            let _ = write_json(&metadata, &value);
                        }
                    }
                    break;
                }
                drop(process);
                tokio::time::sleep(Duration::from_millis(250)).await;
            }
            owned.lock().await.remove(&tracked_id);
        });
        Ok(id)
    }

    pub async fn cancel(&self, id: &str) -> Result<(), String> {
        let child = self
            .owned
            .lock()
            .await
            .get(id)
            .cloned()
            .ok_or("This app session does not own that Blender process")?;
        let mut process = child.lock().await;
        process
            .kill()
            .await
            .map_err(|_| "Could not stop owned Blender job")?;
        let path = self.folder(id)?.join("job.json");
        let mut value: Value =
            serde_json::from_slice(&fs::read(&path).map_err(|_| "Cannot read cancelled job")?)
                .map_err(|_| "Invalid job metadata")?;
        value["status"] = json!("cancelled");
        write_json(&path, &value)
    }

    pub async fn retry(
        &self,
        executable: &str,
        script: &Path,
        id: &str,
        interrupted_confirmed: bool,
    ) -> Result<String, String> {
        let value = self.status(id).await?;
        if !matches!(
            value["status"].as_str(),
            Some("failed" | "cancelled" | "interrupted")
        ) || value["process_owned"] == true
        {
            return Err("Only stopped failed/interrupted jobs can be retried".into());
        }
        if value["status"] == "interrupted" && !interrupted_confirmed {
            return Err(
                "Confirm the previous worker has stopped; this session cannot claim its PID".into(),
            );
        }
        let completed: std::collections::BTreeSet<_> = value["scenes"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|item| item["status"] == "complete")
            .filter_map(|item| item["name"].as_str())
            .collect();
        let scenes = value["selected_scenes"]
            .as_array()
            .ok_or("Missing selected scenes")?
            .iter()
            .filter_map(Value::as_str)
            .filter(|name| !completed.contains(name))
            .map(String::from)
            .collect();
        let project = value["project"].as_str().ok_or("Missing project")?;
        if hash_file(Path::new(project))?
            != value["project_sha256"]
                .as_str()
                .ok_or("Missing source checksum")?
        {
            return Err("Project changed; inspect it before starting a new job".into());
        }
        let output = value["output_root"]
            .as_str()
            .map(String::from)
            .or_else(|| {
                value["output"]
                    .as_str()
                    .and_then(|p| Path::new(p).parent())
                    .map(|p| p.to_string_lossy().into_owned())
            })
            .ok_or("Missing output root")?;
        self.start(
            executable,
            script,
            project,
            &output,
            scenes,
            Some(id.into()),
        )
        .await
    }
}
