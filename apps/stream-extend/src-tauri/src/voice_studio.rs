//! Fixed, bundled stdio API; no shell, listener, or caller-selected executable.
use serde_json::{json, Value};
use std::{fs, path::PathBuf, process::Stdio};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    process::{Child, ChildStdin, ChildStdout, Command},
    sync::Mutex,
    time::{timeout, Duration},
};

const FILES: &[(&str, &str)] = &[
    (
        "configs/local/voice-studio.yaml",
        include_str!("../../../../configs/local/voice-studio.yaml"),
    ),
    (
        "configs/local/stream-autopilot.yaml",
        include_str!("../../../../configs/local/stream-autopilot.yaml"),
    ),
    (
        "configs/local/stream-speech.yaml",
        include_str!("../../../../configs/local/stream-speech.yaml"),
    ),
    (
        "modules/automation-control/voice_studio/__init__.py",
        include_str!("../../../../modules/automation-control/voice_studio/__init__.py"),
    ),
    (
        "modules/automation-control/voice_studio/__main__.py",
        include_str!("../../../../modules/automation-control/voice_studio/__main__.py"),
    ),
    (
        "modules/automation-control/voice_studio/studio.py",
        include_str!("../../../../modules/automation-control/voice_studio/studio.py"),
    ),
    (
        "modules/automation-control/voice_studio/script.py",
        include_str!("../../../../modules/automation-control/voice_studio/script.py"),
    ),
    (
        "modules/automation-control/voice_studio/process.py",
        include_str!("../../../../modules/automation-control/voice_studio/process.py"),
    ),
    (
        "modules/ai-agents/stream_host/__init__.py",
        include_str!("../../../../modules/ai-agents/stream_host/__init__.py"),
    ),
    (
        "modules/ai-agents/stream_host/models.py",
        include_str!("../../../../modules/ai-agents/stream_host/models.py"),
    ),
    (
        "modules/ai-agents/stream_host/author.py",
        include_str!("../../../../modules/ai-agents/stream_host/author.py"),
    ),
    (
        "modules/audio-production/stream_speech/__init__.py",
        include_str!("../../../../modules/audio-production/stream_speech/__init__.py"),
    ),
    (
        "modules/audio-production/stream_speech/models.py",
        include_str!("../../../../modules/audio-production/stream_speech/models.py"),
    ),
    (
        "modules/audio-production/stream_speech/runtime.py",
        include_str!("../../../../modules/audio-production/stream_speech/runtime.py"),
    ),
    (
        "modules/audio-production/stream_speech/native.py",
        include_str!("../../../../modules/audio-production/stream_speech/native.py"),
    ),
    (
        "modules/audio-production/stream_speech/render.py",
        include_str!("../../../../modules/audio-production/stream_speech/render.py"),
    ),
    (
        "modules/audio-production/stream_speech/windows_playback.ps1",
        include_str!("../../../../modules/audio-production/stream_speech/windows_playback.ps1"),
    ),
    (
        "modules/audio-production/tts/windows_speech.ps1",
        include_str!("../../../../modules/audio-production/tts/windows_speech.ps1"),
    ),
];

struct Session {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
}

pub struct VoiceStudio {
    root: PathBuf,
    setup: PathBuf,
    session: Mutex<Option<Session>>,
}
impl VoiceStudio {
    pub fn new(root: PathBuf, setup: PathBuf) -> Self {
        Self {
            root,
            setup,
            session: Mutex::new(None),
        }
    }
    fn spawn(&self) -> Result<Session, String> {
        let runtime = self.root.join("runtime-v1");
        for (path, contents) in FILES {
            let target = runtime.join(path);
            fs::create_dir_all(target.parent().unwrap())
                .map_err(|_| "Cannot prepare voice studio")?;
            fs::write(target, contents).map_err(|_| "Cannot prepare voice studio")?;
        }
        let python = self
            .setup
            .join(".venv-modules/automation-control")
            .join(if cfg!(windows) {
                "Scripts/python.exe"
            } else {
                "bin/python"
            });
        if !python.is_file() {
            return Err(
                "Install Automation / Control in Module setup before opening Personalities".into(),
            );
        }
        let mut child = Command::new(python)
            .args(["-m", "voice_studio", "--library"])
            .arg(self.root.join("library"))
            .env("PYTHONPATH", runtime.join("modules/automation-control"))
            .env("PYTHONUTF8", "1")
            .current_dir(runtime)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| "Cannot start voice studio")?;
        Ok(Session {
            input: child.stdin.take().unwrap(),
            output: BufReader::new(child.stdout.take().unwrap()),
            child,
        })
    }
    pub async fn call(&self, request: Value) -> Result<Value, String> {
        let mut line = serde_json::to_vec(&request).map_err(|_| "Invalid studio request")?;
        if line.len() > 65535 {
            return Err("Studio request exceeds 64 KiB".into());
        }
        line.push(b'\n');
        let mut guard = self.session.lock().await;
        if guard.is_none() {
            *guard = Some(self.spawn()?);
        }
        let session = guard.as_mut().unwrap();
        let exchange = async {
            session
                .input
                .write_all(&line)
                .await
                .map_err(|_| "Studio stopped")?;
            session.input.flush().await.map_err(|_| "Studio stopped")?;
            // read_until can allocate an unbounded line; consume bounded chunks instead.
            let mut bytes = Vec::new();
            loop {
                let chunk = session
                    .output
                    .fill_buf()
                    .await
                    .map_err(|_| "Studio stopped")?;
                if chunk.is_empty() {
                    return Err("Studio stopped; check setup or another library owner");
                }
                let end = chunk.iter().position(|b| *b == b'\n');
                let count = end.map_or(chunk.len(), |i| i + 1);
                if bytes.len() + count > 16 * 1024 * 1024 {
                    return Err("Studio response exceeds limit");
                }
                bytes.extend_from_slice(&chunk[..count]);
                session.output.consume(count);
                if end.is_some() {
                    break;
                }
            }
            serde_json::from_slice::<Value>(&bytes).map_err(|_| "Invalid studio response")
        };
        match timeout(Duration::from_secs(70), exchange).await {
            Ok(Ok(reply)) => {
                if reply["ok"] == json!(true) {
                    Ok(reply["data"].clone())
                } else {
                    Err(reply["error"]
                        .as_str()
                        .unwrap_or("Studio request failed")
                        .to_owned())
                }
            }
            failure => {
                // Closing stdin tells the owner to cancel all render/playback children, then exit.
                let session = guard.take().unwrap();
                drop(session.input);
                let mut child = session.child;
                tokio::spawn(async move {
                    let _ = child.wait().await;
                });
                Err(match failure {
                    Err(_) => "Studio timed out; inspect status before retrying",
                    _ => "Studio unavailable; check Module setup or library ownership",
                }
                .into())
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn sources_are_fixed_and_complete() {
        assert_eq!(FILES.len(), 18);
        assert!(FILES
            .iter()
            .all(|(path, contents)| !path.contains("..") && !contents.is_empty()));
    }
}

/// The bridge's bounds and failure handling, driven against fake workers that stand in for the
/// Automation / Control Python process. Unix only: the fake is a `#!/bin/sh` script installed at
/// the path `spawn` expects. The 70 s timeout is not exercised, because it is not injectable.
#[cfg(all(test, unix))]
mod worker_tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;

    /// Fake workers are exec'd right after being written; serializing the tests keeps a sibling
    /// test's fork from holding the script open and failing the exec with ETXTBSY.
    static SERIAL: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

    struct Fixture {
        dir: PathBuf,
    }

    impl Fixture {
        fn new(tag: &str) -> Self {
            let nanos = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let dir = std::env::temp_dir()
                .join(format!("voice-studio-{tag}-{}-{nanos}", std::process::id()));
            fs::create_dir_all(&dir).unwrap();
            Self { dir }
        }

        fn studio(&self) -> VoiceStudio {
            VoiceStudio::new(self.dir.join("root"), self.dir.join("setup"))
        }

        fn counts(&self) -> PathBuf {
            self.dir.join("spawn-count")
        }

        /// Installs a worker. Every start appends one line to the spawn log first.
        fn worker(&self, body: &str) {
            let python = self
                .dir
                .join("setup/.venv-modules/automation-control/bin/python");
            fs::create_dir_all(python.parent().unwrap()).unwrap();
            let script = format!(
                "#!/bin/sh\necho x >> '{}'\n{body}\n",
                self.counts().display()
            );
            fs::write(&python, script).unwrap();
            fs::set_permissions(&python, fs::Permissions::from_mode(0o755)).unwrap();
        }

        fn spawns(&self) -> usize {
            fs::read_to_string(self.counts()).map_or(0, |log| log.lines().count())
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.dir);
        }
    }

    const ECHO_OK: &str = r#"while read -r line; do printf '{"ok":true,"data":{"n":1}}\n'; done"#;

    fn request_of_len(bytes: usize) -> Value {
        // {"a":""} is 8 bytes; the filler makes up the rest.
        json!({ "a": "x".repeat(bytes - 8) })
    }

    #[tokio::test]
    async fn oversized_request_is_rejected_before_any_worker_starts() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("oversize-request");
        fixture.worker(ECHO_OK);
        let err = fixture
            .studio()
            .call(request_of_len(65536))
            .await
            .unwrap_err();
        assert_eq!(err, "Studio request exceeds 64 KiB");
        assert_eq!(fixture.spawns(), 0);
    }

    #[tokio::test]
    async fn request_at_the_limit_reaches_the_worker() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("limit-request");
        fixture.worker(ECHO_OK);
        let reply = fixture.studio().call(request_of_len(65535)).await.unwrap();
        assert_eq!(reply, json!({ "n": 1 }));
        assert_eq!(fixture.spawns(), 1);
    }

    #[tokio::test]
    async fn missing_automation_environment_names_the_setup_step() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("no-python");
        let err = fixture
            .studio()
            .call(json!({ "action": "status" }))
            .await
            .unwrap_err();
        assert!(err.starts_with("Install Automation / Control"), "{err}");
    }

    #[tokio::test]
    async fn successful_replies_return_data_and_share_one_worker() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("reuse");
        fixture.worker(ECHO_OK);
        let studio = fixture.studio();
        for _ in 0..3 {
            let reply = studio.call(json!({ "action": "status" })).await.unwrap();
            assert_eq!(reply, json!({ "n": 1 }));
        }
        assert_eq!(fixture.spawns(), 1);
    }

    #[tokio::test]
    async fn worker_errors_are_surfaced_without_dropping_the_session() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("worker-error");
        fixture.worker(
            r#"while read -r line; do
  case "$line" in
    *named*) printf '{"ok":false,"error":"Revision is not approved"}\n' ;;
    *) printf '{"ok":false}\n' ;;
  esac
done"#,
        );
        let studio = fixture.studio();
        let err = studio.call(json!({ "action": "named" })).await.unwrap_err();
        assert_eq!(err, "Revision is not approved");
        let err = studio.call(json!({ "action": "bare" })).await.unwrap_err();
        assert_eq!(err, "Studio request failed");
        assert_eq!(
            fixture.spawns(),
            1,
            "a refused request must not restart the worker"
        );
    }

    #[tokio::test]
    async fn oversized_response_is_cut_off_and_the_next_call_gets_a_fresh_worker() {
        let _serial = SERIAL.lock().await;
        let fixture = Fixture::new("oversize-response");
        // First start answers with 17 MB and no newline, then keeps its pipe open, so only the
        // 16 MiB cap can end the read (an exit would end it on EOF and prove nothing). Later
        // starts behave.
        fixture.worker(&format!(
            r#"if [ "$(wc -l < '{log}' | tr -d ' ')" = 1 ]; then
  read -r line
  head -c 17000000 /dev/zero | tr '\0' a
  sleep 8
  exit 0
fi
{ECHO_OK}"#,
            log = fixture.counts().display()
        ));
        let studio = fixture.studio();
        let started = std::time::Instant::now();
        assert!(studio.call(json!({ "action": "status" })).await.is_err());
        assert!(
            started.elapsed() < Duration::from_secs(5),
            "the response cap must end the read, not the worker exiting or the 70 s timeout"
        );
        let reply = studio.call(json!({ "action": "status" })).await.unwrap();
        assert_eq!(reply, json!({ "n": 1 }));
        assert_eq!(fixture.spawns(), 2);
    }

    #[tokio::test]
    async fn worker_exit_or_garbage_reply_drops_the_session() {
        let _serial = SERIAL.lock().await;
        for (tag, body) in [
            ("exits", "read -r line\nexit 0"),
            ("garbage", "read -r line\necho not-json\nsleep 5"),
        ] {
            let fixture = Fixture::new(tag);
            fixture.worker(body);
            let studio = fixture.studio();
            assert!(
                studio.call(json!({ "action": "status" })).await.is_err(),
                "{tag}"
            );
            assert!(
                studio.call(json!({ "action": "status" })).await.is_err(),
                "{tag}"
            );
            assert_eq!(
                fixture.spawns(),
                2,
                "{tag}: each failure must discard the session"
            );
        }
    }
}
