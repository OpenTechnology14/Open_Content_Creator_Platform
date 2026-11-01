//! Persistent local production owner; correlated replies, no renderer commands or secrets.
use crate::autopilot::AutopilotBridge;
use fs2::FileExt;
use local_settings::OsCredentials;
use recording_library::{RecordingLibrary, RecordingOrigin};
use serde_json::{json, Value};
use std::{
    collections::HashMap,
    fs::{self, File, OpenOptions},
    path::PathBuf,
    process::Stdio,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    time::{SystemTime, UNIX_EPOCH},
};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    process::{Child, ChildStdin, Command},
    sync::{oneshot, Mutex},
    time::{timeout, Duration},
};

type Replies = Arc<Mutex<HashMap<String, oneshot::Sender<Result<Value, String>>>>>;
struct LiveContext {
    config: crate::AppConfig,
    operation_id: String,
    source: Option<String>,
    content: Option<String>,
}
struct Session {
    child: Arc<Mutex<Child>>,
    input: Arc<Mutex<Option<ChildStdin>>>,
    replies: Replies,
    _lock: File,
    bindings: crate::AppConfig,
}
pub struct ProductionBridge {
    root: PathBuf,
    setup: PathBuf,
    config: Arc<std::sync::Mutex<crate::AppConfig>>,
    session: Mutex<Option<Session>>,
    live: Mutex<Option<LiveContext>>,
    obs_owner: crate::obs::ObsSessionState,
    obs_cache: crate::obs::ObsClientCache,
    generation: AtomicU64,
}
fn identifier() -> String {
    static NEXT: AtomicU64 = AtomicU64::new(0);
    format!(
        "{}-{}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    )
}
fn allowed(action: &str) -> bool {
    matches!(
        action,
        "status" | "preflight" | "preview" | "run" | "pause" | "resume" | "stop" | "emergency_stop"
    )
}
fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}
impl ProductionBridge {
    pub fn new(
        root: PathBuf,
        setup: PathBuf,
        config: Arc<std::sync::Mutex<crate::AppConfig>>,
    ) -> Self {
        Self {
            root,
            setup,
            config,
            session: Mutex::new(None),
            live: Mutex::new(None),
            obs_owner: crate::obs::ObsSessionState::new(),
            obs_cache: crate::obs::ObsClientCache::new(),
            generation: AtomicU64::new(0),
        }
    }
    async fn connect(&self) -> Result<(Arc<Mutex<Option<ChildStdin>>>, Replies), String> {
        let mut guard = self.session.lock().await;
        if let Some(session) = guard.as_ref() {
            if session
                .child
                .lock()
                .await
                .try_wait()
                .map_err(|_| "Cannot inspect production owner")?
                .is_none()
            {
                return Ok((session.input.clone(), session.replies.clone()));
            }
        }
        *guard = None;
        fs::create_dir_all(&self.root).map_err(|_| "Cannot prepare production storage")?;
        let lock = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(self.root.join("production.lock"))
            .map_err(|_| "Cannot open production ownership lock")?;
        lock.try_lock_exclusive()
            .map_err(|_| "Another app instance owns this production runtime")?;
        let bundle = AutopilotBridge::new(self.root.join("bundle"), self.setup.clone());
        let runtime = bundle.unpack()?;
        let operator = self.root.join("operator");
        fs::create_dir_all(&operator).map_err(|_| "Cannot prepare operator configuration")?;
        for name in [
            "stream-supervisor.yaml",
            "stream-runtime.yaml",
            "stream-autopilot.yaml",
            "stream-director.yaml",
            "stream-speech.yaml",
            "stream-avatar.yaml",
            "twitch-chat.yaml",
            "minecraft-gameplay.json",
        ] {
            let target = operator.join(name);
            if !target.exists() {
                let mut contents = fs::read_to_string(runtime.join("configs/local").join(name))
                    .map_err(|_| "Cannot read bundled production policy")?;
                if name == "stream-runtime.yaml" {
                    for file in [
                        "stream-autopilot",
                        "stream-director",
                        "stream-speech",
                        "stream-avatar",
                        "twitch-chat",
                    ] {
                        contents = contents.replace(
                            &format!("configs/local/{file}.yaml"),
                            &format!("{file}.yaml"),
                        );
                    }
                }
                if name == "stream-runtime.yaml" {
                    contents = contents.replace(
                        "configs/local/minecraft-gameplay.json",
                        "minecraft-gameplay.json",
                    );
                }
                fs::write(&target, contents).map_err(|_| "Cannot prepare production policy")?;
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    fs::set_permissions(&target, fs::Permissions::from_mode(0o600))
                        .map_err(|_| "Cannot protect production policy")?;
                }
            }
        }
        let mut command = Command::new(bundle.interpreter()?);
        command
            .args(["-m", "stream_autopilot", "--config"])
            .arg(operator.join("stream-supervisor.yaml"))
            .arg("serve")
            .arg("--runtime-config")
            .arg(operator.join("stream-runtime.yaml"))
            .arg("--state")
            .arg(self.root.join("production-state.json"))
            .env("PYTHONPATH", runtime.join("modules/automation-control"))
            .env("PYTHONUTF8", "1")
            .env("AUTOPILOT_NATIVE_BROADCAST_OWNER", "1")
            .current_dir(runtime)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        let settings = self
            .config
            .lock()
            .map_err(|_| "Cannot read saved connection settings")?
            .clone();
        command
            .env("AUTOPILOT_BACKEND_URL", settings.api_url.clone())
            .env("OBS_WEBSOCKET_HOST", settings.obs_host.clone())
            .env("OBS_WEBSOCKET_PORT", settings.obs_port.to_string());
        if let Some(password) = settings.obs_password.as_deref() {
            command.env("OBS_WEBSOCKET_PASSWORD", password);
        }
        // Generated local-service and OBS credentials remain outside the webview and logs.
        if !cfg!(test) {
            if let Ok(store) = OsCredentials::new("HybridCreatorPlatform", "local-services") {
                if let Ok(Some(key)) = store.get("hcp-api-key") {
                    command.env("HCP_API_KEY", key);
                }
            }
        } else {
            command
                .env_remove("HCP_API_KEY")
                .env_remove("OBS_WEBSOCKET_PASSWORD");
        }
        let mut child = command
            .spawn()
            .map_err(|_| "Could not start production owner; check module dependencies")?;
        let input = Arc::new(Mutex::new(child.stdin.take()));
        let stdout = child
            .stdout
            .take()
            .ok_or("Production owner has no response stream")?;
        let replies: Replies = Arc::new(Mutex::new(HashMap::new()));
        let reader_replies = replies.clone();
        tokio::spawn(async move {
            let mut lines = BufReader::new(stdout).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                if line.len() > 131_072 {
                    break;
                }
                let Ok(value) = serde_json::from_str::<Value>(&line) else {
                    break;
                };
                let Some(id) = value["operation_id"].as_str() else {
                    break;
                };
                if let Some(sender) = reader_replies.lock().await.remove(id) {
                    let _ = sender.send(Ok(value));
                }
            }
            for (_, sender) in reader_replies.lock().await.drain() {
                let _ = sender.send(Err(
                    "Production response stream closed; recheck state before retrying".into(),
                ));
            }
        });
        *guard = Some(Session {
            child: Arc::new(Mutex::new(child)),
            input: input.clone(),
            replies: replies.clone(),
            _lock: lock,
            bindings: settings,
        });
        Ok((input, replies))
    }
    pub async fn request(&self, action: &str, operation_id: &str) -> Result<Value, String> {
        if !allowed(action) || !valid_id(operation_id) {
            return Err("Invalid production action or operation identifier".into());
        }
        let (input, replies) = self.connect().await?;
        let (sender, receiver) = oneshot::channel();
        {
            let mut pending = replies.lock().await;
            let priority = matches!(action, "stop" | "emergency_stop");
            if pending.len() >= (if priority { 8 } else { 6 }) || pending.contains_key(operation_id)
            {
                return Err("Production request is already pending or queue is full".into());
            }
            pending.insert(operation_id.into(), sender);
        }
        let mut frame =
            json!({"session_id":null,"action":action,"operation_id":operation_id}).to_string();
        frame.push('\n');
        let result = async {
            let mut stdin = input.lock().await;
            let writer = stdin.as_mut().ok_or("Production owner is closing")?;
            writer
                .write_all(frame.as_bytes())
                .await
                .map_err(|_| "Could not deliver production action")?;
            writer
                .flush()
                .await
                .map_err(|_| "Could not flush production action")?;
            Ok::<(), String>(())
        }
        .await;
        if let Err(error) = result {
            replies.lock().await.remove(operation_id);
            return Err(error);
        }
        let seconds = if action == "preflight" { 70 } else { 15 };
        let answer = timeout(Duration::from_secs(seconds), receiver).await;
        replies.lock().await.remove(operation_id);
        match answer {
            Ok(Ok(value)) => value,
            _ => Err("Production action is unobserved; recheck state and use Emergency stop before retrying".into()),
        }
    }
    async fn stop_live(&self) -> Result<Value, String> {
        let mut context = self.live.lock().await;
        let Some(live) = context.as_ref() else {
            return Ok(json!({"broadcast_stopped":true}));
        };
        let config = &live.config;
        if !self.obs_owner.is_owned().await {
            return Err(
                "OBS start was not confirmed; reconcile OBS manually before retrying".into(),
            );
        }
        let result = crate::obs::stop_live_session(
            &self.obs_cache,
            &self.obs_owner,
            &config.obs_host,
            config.obs_port,
            config.obs_password.as_deref(),
        )
        .await
        .map_err(|_| "OBS stop/finalized recording is not confirmed; check OBS before retrying")?;
        let mut report = json!({"broadcast_stopped":!result.stream_active});
        if let Some(path) = result.recording_path.as_deref() {
            let library = RecordingLibrary::new(
                self.root
                    .parent()
                    .ok_or("Missing library root")?
                    .join("recording-library"),
            )?;
            match library.register(
                path,
                RecordingOrigin::StreamSession,
                result.source_profile_id.as_deref(),
                result.content_profile_id.as_deref(),
            ) {
                Ok(recording) => {
                    report["handoff"] =
                        json!({"id":recording.record.id,"file_name":recording.record.file_name});
                }
                Err(_) => {
                    report["handoff_error"] =
                        json!("OBS finalized the file; import it manually in Creator Extend");
                }
            }
        }
        *context = None;
        Ok(report)
    }
    pub async fn control(
        &self,
        action: &str,
        operation_id: &str,
        source: Option<String>,
        content: Option<String>,
    ) -> Result<Value, String> {
        if (action != "reconcile" && !allowed(action)) || !valid_id(operation_id) {
            return Err("Invalid production control request".into());
        }
        if action == "reconcile" {
            let mut live = self.live.lock().await;
            if let Some(current) = live.as_ref() {
                let cfg = &current.config;
                if self.obs_owner.is_owned().await
                    || !crate::obs::outputs_inactive(
                        &self.obs_cache,
                        &cfg.obs_host,
                        cfg.obs_port,
                        cfg.obs_password.as_deref(),
                    )
                    .await
                    .map_err(|_| "Cannot confirm OBS is inactive")?
                {
                    return Err("OBS still has active or owned outputs; stop/reconcile them before clearing uncertainty".into());
                }
                *live = None;
            }
            drop(live);
            return self.request("status", operation_id).await;
        }
        if matches!(action, "stop" | "emergency_stop") {
            self.generation.fetch_add(1, Ordering::SeqCst);
        }
        for profile in [source.as_deref(), content.as_deref()]
            .into_iter()
            .flatten()
        {
            if !valid_id(profile) {
                return Err("Invalid recording profile".into());
            }
        }
        if action == "run" {
            let live = self.live.lock().await;
            if let Some(current) = live.as_ref() {
                if current.operation_id == operation_id
                    && current.source == source
                    && current.content == content
                    && self.obs_owner.is_owned().await
                {
                    let mut replay = self.request(action, operation_id).await?;
                    replay["broadcast_started"] = json!(true);
                    replay["replayed"] = json!(true);
                    return Ok(replay);
                }
                return Err(
                    "Reconcile or stop the previous OBS operation before another Run".into(),
                );
            }
        }
        let epoch = self.generation.load(Ordering::SeqCst);
        let mut reply = self.request(action, operation_id).await?;
        if action == "run"
            && reply["ok"] == true
            && reply["status"]["lifecycle"] == "running"
            && reply["broadcast_control_enabled"] == true
        {
            let mut live = self.live.lock().await;
            if self.generation.load(Ordering::SeqCst) != epoch {
                return Err("Run was superseded by stop".into());
            }
            let config = self
                .session
                .lock()
                .await
                .as_ref()
                .ok_or("Production owner disappeared")?
                .bindings
                .clone();
            *live = Some(LiveContext {
                config: config.clone(),
                operation_id: operation_id.into(),
                source: source.clone(),
                content: content.clone(),
            });
            let started = crate::obs::start_live_session(
                &self.obs_cache,
                &self.obs_owner,
                &config.obs_host,
                config.obs_port,
                config.obs_password.as_deref(),
                source,
                content,
            )
            .await;
            if started.is_err() {
                drop(live);
                let _ = self.request("emergency_stop", &identifier()).await;
                return Err(
                    "OBS start/recording was not confirmed; reconcile OBS before retrying".into(),
                );
            }
            reply["broadcast_started"] = json!(true);
            drop(live);
            if self.generation.load(Ordering::SeqCst) != epoch {
                let _ = self.stop_live().await?;
                return Err("Run was superseded; owned OBS session was stopped".into());
            }
        }
        if matches!(action, "stop" | "emergency_stop") {
            reply["obs"] = self.stop_live().await?;
        }
        Ok(reply)
    }
    pub async fn prepare_game(&self) -> Result<Value, String> {
        let status = self.request("status", &identifier()).await?;
        if matches!(
            status["status"]["lifecycle"].as_str(),
            Some("preview" | "running" | "paused" | "preflight")
        ) {
            return Err("Stop the runtime before changing its optional game dependencies".into());
        }
        let bundle = AutopilotBridge::new(self.root.join("bundle"), self.setup.clone());
        let runtime = bundle.unpack()?;
        let output = timeout(
            Duration::from_secs(190),
            Command::new(bundle.interpreter()?)
                .args(["-m", "stream_autopilot.gameplay", "--config"])
                .arg(runtime.join("configs/local/minecraft-gameplay.json"))
                .arg("--install-dependencies")
                .env("PYTHONPATH", runtime.join("modules/automation-control"))
                .env("PYTHONUTF8", "1")
                .current_dir(runtime)
                .stdin(Stdio::null())
                .stderr(Stdio::null())
                .kill_on_drop(true)
                .output(),
        )
        .await
        .map_err(|_| "Optional game dependency preparation timed out")?
        .map_err(|_| "Could not prepare the pinned game package")?;
        if !output.status.success() {
            return Err(
                "Game package preparation failed; install Node.js 22+ and recheck the local setup"
                    .into(),
            );
        }
        serde_json::from_slice(&output.stdout).map_err(|_| "Invalid game dependency report".into())
    }
    pub async fn shutdown(&self) -> Result<(), String> {
        self.generation.fetch_add(1, Ordering::SeqCst);
        let mut guard = self.session.lock().await;
        let mut child_result = Ok(());
        if let Some(session) = guard.as_ref() {
            session.input.lock().await.take();
            child_result =
                match timeout(Duration::from_secs(20), session.child.lock().await.wait()).await {
                    Ok(Ok(status)) if status.success() => Ok(()),
                    _ => Err("Production shutdown is unconfirmed; check local effects".to_string()),
                };
        }
        *guard = None;
        drop(guard);
        let obs_result = self.stop_live().await;
        child_result?;
        obs_result?;
        Ok(())
    }
}
#[tauri::command]
pub async fn autopilot_production_status(
    bridge: tauri::State<'_, ProductionBridge>,
) -> Result<Value, String> {
    bridge.request("status", &identifier()).await
}
#[tauri::command]
pub async fn autopilot_production_action(
    bridge: tauri::State<'_, ProductionBridge>,
    action: String,
    operation_id: String,
    source_profile_id: Option<String>,
    content_profile_id: Option<String>,
) -> Result<Value, String> {
    bridge
        .control(
            &action,
            &operation_id,
            source_profile_id,
            content_profile_id,
        )
        .await
}
#[tauri::command]
pub async fn autopilot_production_disconnect(
    bridge: tauri::State<'_, ProductionBridge>,
) -> Result<(), String> {
    bridge.shutdown().await
}
#[tauri::command]
pub async fn autopilot_prepare_game(
    bridge: tauri::State<'_, ProductionBridge>,
) -> Result<Value, String> {
    bridge.prepare_game().await
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn only_fixed_actions_and_bounded_ascii_ids() {
        assert!(allowed("emergency_stop"));
        assert!(!allowed("serve --shell"));
        assert!(valid_id("op-1"));
        assert!(!valid_id("../path"));
        assert!(!valid_id("é"));
    }
    #[tokio::test]
    #[ignore = "requires HCP_AUTOPILOT_TEST_PYTHON pointing at a prepared local interpreter"]
    async fn real_packaged_owner_correlates_cancel_and_shutdown_without_effects() {
        let python = PathBuf::from(std::env::var("HCP_AUTOPILOT_TEST_PYTHON").unwrap());
        let root = std::env::temp_dir().join(format!("hcp-owner-{}", identifier()));
        let setup = root.join("setup");
        #[cfg(windows)]
        let interpreter = setup
            .join(".venv-modules/automation-control")
            .join(if cfg!(windows) {
                "Scripts/python.exe"
            } else {
                "bin/python"
            });
        fs::create_dir_all(setup.join(".venv-modules")).unwrap();
        #[cfg(unix)]
        std::os::unix::fs::symlink(
            python.parent().unwrap().parent().unwrap(),
            setup.join(".venv-modules/automation-control"),
        )
        .unwrap();
        #[cfg(windows)]
        {
            fs::create_dir_all(interpreter.parent().unwrap()).unwrap();
            fs::copy(&python, &interpreter).unwrap();
        }
        let bridge = ProductionBridge::new(
            root.join("production"),
            setup,
            Arc::new(std::sync::Mutex::new(crate::AppConfig::default())),
        );
        assert!(bridge
            .control("bad-command", "x", None, None)
            .await
            .is_err());
        assert!(!root.join("production").exists());
        let status = bridge.request("status", "status-first").await.unwrap();
        assert_eq!(status["status"]["lifecycle"], "stopped");
        assert_eq!(status["policy"]["broadcast_start_authorized"], false);
        let checked = bridge.request("preflight", "bundled-validators").await.unwrap();
        for name in ["host", "director", "speech"] {
            assert!(checked["status"]["checks"].as_array().unwrap().iter().any(
                |check| check["id"] == name && check["status"] == "ready"
            ), "bundled {name} validator was not ready: {checked}");
        }
        let (preflight, stopped) = tokio::join!(
            bridge.request("preflight", "preflight-pending"),
            bridge.control("emergency_stop", "priority-stop", None, None)
        );
        assert!(preflight.is_ok());
        let stopped = stopped.unwrap();
        assert_eq!(stopped["status"]["lifecycle"], "stopped");
        assert_eq!(stopped["worker_states"], json!({}));
        assert!(
            bridge
                .control("run", "locked-run", None, None)
                .await
                .unwrap()["ok"]
                == false
        );
        bridge.shutdown().await.unwrap();
        assert!(bridge.session.lock().await.is_none());
        fs::remove_dir_all(root).unwrap();
    }
    #[cfg(unix)]
    #[tokio::test]
    async fn native_run_records_first_replays_once_and_registers_only_owned_output() {
        use futures_util::{SinkExt, StreamExt};
        use std::os::unix::fs::PermissionsExt;
        use tokio_tungstenite::{accept_async, tungstenite::Message};
        let root = std::env::temp_dir().join(format!("hcp-native-owner-contract-{}", identifier()));
        let setup = root.join("setup");
        let executable = setup.join(".venv-modules/automation-control/bin/python");
        fs::create_dir_all(executable.parent().unwrap()).unwrap();
        fs::write(&executable, r#"#!/usr/bin/env python3
import sys,json
revision=0
for line in sys.stdin:
 request=json.loads(line);revision+=1
 lifecycle='running' if request['action']=='run' else 'stopped'
 print(json.dumps({'ok':True,'operation_id':request['operation_id'],'broadcast_control_enabled':True,'session_id':'fixture','worker_states':{},'policy':{'broadcast_start_authorized':True},'status':{'lifecycle':lifecycle,'revision':revision,'ready':True}}),flush=True)
"#).unwrap();
        fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
        let output = root.join("owned.mkv");
        fs::write(&output, vec![1u8; 1024]).unwrap();
        let log = Arc::new(Mutex::new(Vec::<String>::new()));
        let stream_on = Arc::new(std::sync::atomic::AtomicBool::new(false));
        let record_on = Arc::new(std::sync::atomic::AtomicBool::new(false));
        let delay_next = Arc::new(std::sync::atomic::AtomicBool::new(false));
        let start_observed = Arc::new(tokio::sync::Notify::new());
        let delayed = delay_next.clone();
        let observed = start_observed.clone();
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let port = listener.local_addr().unwrap().port();
        let calls = log.clone();
        let streaming = stream_on.clone();
        let recording = record_on.clone();
        let path = output.clone();
        let server = tokio::spawn(async move {
            loop {
                let (socket, _) = listener.accept().await.unwrap();
                let mut ws = accept_async(socket).await.unwrap();
                ws.send(Message::Text(json!({"op":0,"d":{"obsWebSocketVersion":"5.5.5","rpcVersion":1,"authentication":null}}).to_string())).await.unwrap();
                let _ = ws.next().await;
                ws.send(Message::Text(
                    json!({"op":2,"d":{"negotiatedRpcVersion":1}}).to_string(),
                ))
                .await
                .unwrap();
                while let Some(Ok(message)) = ws.next().await {
                    let Ok(text) = message.to_text() else { break };
                    let request: Value = serde_json::from_str(text).unwrap();
                    let name = request["d"]["requestType"].as_str().unwrap().to_string();
                    calls.lock().await.push(name.clone());
                    let response = match name.as_str() {
                        "GetVersion" => {
                            json!({"obsStudioVersion":"30.2.0","obsWebSocketVersion":"5.5.5","rpcVersion":1,"availableRequests":[],"supportedImageFormats":[],"platform":"macos","platformDescription":"fixture"})
                        }
                        "GetStreamStatus" => {
                            json!({"outputActive":streaming.load(Ordering::SeqCst),"outputReconnecting":false,"outputTimecode":"00:00:00.000","outputDuration":0,"outputCongestion":0.0,"outputBytes":0,"outputSkippedFrames":0,"outputTotalFrames":0})
                        }
                        "GetRecordStatus" => {
                            json!({"outputActive":recording.load(Ordering::SeqCst),"outputPaused":false,"outputTimecode":"00:00:00.000","outputDuration":0,"outputBytes":0})
                        }
                        "StartRecord" => {
                            recording.store(true, Ordering::SeqCst);
                            json!({})
                        }
                        "StartStream" => {
                            if delayed.swap(false, Ordering::SeqCst) {
                                observed.notify_one();
                                tokio::time::sleep(Duration::from_millis(50)).await;
                            }
                            streaming.store(true, Ordering::SeqCst);
                            json!({})
                        }
                        "StopStream" => {
                            streaming.store(false, Ordering::SeqCst);
                            json!({})
                        }
                        "StopRecord" => {
                            recording.store(false, Ordering::SeqCst);
                            json!({"outputPath":path.to_string_lossy()})
                        }
                        _ => panic!("unexpected fixture request"),
                    };
                    let reply = json!({"op":7,"d":{"requestId":request["d"]["requestId"],"requestType":name,"requestStatus":{"result":true,"code":100,"comment":null},"responseData":response}});
                    let mut reply = reply;
                    if matches!(name.as_str(), "StartRecord" | "StartStream" | "StopStream") {
                        reply["d"].as_object_mut().unwrap().remove("responseData");
                    }
                    if ws.send(Message::Text(reply.to_string())).await.is_err() {
                        break;
                    }
                }
            }
        });
        let mut config = crate::AppConfig::default();
        config.obs_host = "127.0.0.1".into();
        config.obs_port = port;
        let bridge = ProductionBridge::new(
            root.join("production"),
            setup,
            Arc::new(std::sync::Mutex::new(config)),
        );
        let first = bridge
            .control(
                "run",
                "owned-run",
                Some("stream-main".into()),
                Some("content-main".into()),
            )
            .await
            .unwrap();
        assert_eq!(first["broadcast_started"], true);
        assert_eq!(
            bridge
                .control(
                    "run",
                    "owned-run",
                    Some("stream-main".into()),
                    Some("content-main".into())
                )
                .await
                .unwrap()["replayed"],
            true
        );
        assert!(bridge
            .control("run", "owned-run", Some("wrong-profile".into()), None)
            .await
            .is_err());
        let stopped = bridge
            .control("emergency_stop", "owned-stop", None, None)
            .await
            .unwrap();
        assert!(stopped["obs"]["handoff"]["id"].is_string());
        let calls = log.lock().await;
        let first_record = calls.iter().position(|x| x == "StartRecord").unwrap();
        let first_stream = calls.iter().position(|x| x == "StartStream").unwrap();
        assert!(first_record < first_stream);
        assert_eq!(calls.iter().filter(|x| *x == "StartStream").count(), 1);
        assert!(
            calls.iter().position(|x| x == "StopStream").unwrap()
                < calls.iter().position(|x| x == "StopRecord").unwrap()
        );
        drop(calls);
        delay_next.store(true, Ordering::SeqCst);
        let (late, stop) = tokio::join!(bridge.control("run", "late-start", None, None), async {
            start_observed.notified().await;
            bridge
                .control("emergency_stop", "late-stop", None, None)
                .await
        });
        assert!(late.is_err());
        assert_eq!(stop.unwrap()["obs"]["broadcast_stopped"], true);
        assert!(!stream_on.load(Ordering::SeqCst));
        assert!(!record_on.load(Ordering::SeqCst));
        bridge.shutdown().await.unwrap();
        server.abort();
        fs::remove_dir_all(root).unwrap();
    }
}
