use creator_extend_lib::blender_jobs::BlenderJobs;
use serde_json::json;
use std::{fs, path::PathBuf};
use uuid::Uuid;

fn workspace() -> PathBuf {
    let root =
        std::env::temp_dir().join(format!("hcp-blender-contract-{}", Uuid::new_v4().simple()));
    fs::create_dir(&root).unwrap();
    root
}

#[tokio::test]
#[ignore = "requires an explicitly supplied real Blender executable and owned fixture"]
async fn real_blender_owned_job_smoke() {
    let executable = std::env::var("HCP_BLENDER_EXECUTABLE").unwrap();
    let root = PathBuf::from(std::env::var("HCP_BLENDER_FIXTURE_ROOT").unwrap());
    let project = root.join("fixture.blend");
    let script = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../modules/content-creation/blender/scripts/batch_render.py")
        .canonicalize()
        .unwrap();
    let jobs = BlenderJobs::new(root.join(format!("native-jobs-{}", Uuid::new_v4().simple())));
    let id = jobs
        .start(
            &executable,
            &script,
            project.to_str().unwrap(),
            root.to_str().unwrap(),
            vec!["One".into(), "Two".into()],
            None,
        )
        .await
        .unwrap();
    let mut result = json!({});
    for _ in 0..240 {
        result = jobs.status(&id).await.unwrap();
        if result["process_owned"] == false {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(250)).await;
    }
    assert_eq!(result["status"], "complete");
    assert_eq!(result["scenes"].as_array().unwrap().len(), 2);
    assert!(result["scenes"]
        .as_array()
        .unwrap()
        .iter()
        .all(|item| item["status"] == "complete"));
    let partial_id = jobs
        .start(
            &executable,
            &script,
            project.to_str().unwrap(),
            root.to_str().unwrap(),
            vec!["NoCamera".into(), "One".into()],
            None,
        )
        .await
        .unwrap();
    for _ in 0..240 {
        if jobs.status(&partial_id).await.unwrap()["process_owned"] == false {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(250)).await;
    }
    let partial = jobs.status(&partial_id).await.unwrap();
    assert_eq!(partial["status"], "failed");
    assert_eq!(partial["scenes"][1]["status"], "complete");
    let retained = PathBuf::from(partial["output"].as_str().unwrap()).join("01.png");
    let retained_bytes = fs::read(&retained).unwrap();
    let retry_id = jobs
        .retry(&executable, &script, &partial_id, false)
        .await
        .unwrap();
    for _ in 0..240 {
        if jobs.status(&retry_id).await.unwrap()["process_owned"] == false {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(250)).await;
    }
    let retried = jobs.status(&retry_id).await.unwrap();
    assert_eq!(retried["status"], "failed"); // Missing camera remains an honest failure.
    assert_eq!(retried["parent_job_id"], partial_id);
    assert_eq!(retried["selected_scenes"], json!(["NoCamera"]));
    assert_ne!(retried["output"], partial["output"]);
    assert_eq!(fs::read(retained).unwrap(), retained_bytes);
    println!(
        "Real owned job {id} passed with verified artifacts in {}",
        result["output"]
    );
}

#[cfg(unix)]
#[tokio::test]
async fn retry_skips_verified_outputs_and_rejects_changed_project() {
    use sha2::{Digest, Sha256};
    use std::os::unix::fs::PermissionsExt;
    let root = workspace();
    let id = "c".repeat(32);
    let library = root.join("jobs");
    let folder = library.join(&id);
    let output = root.join("previous-output");
    fs::create_dir_all(&folder).unwrap();
    fs::create_dir(&output).unwrap();
    let original = b"BLENDER-v450fixture";
    let project = root.join("project.blend");
    fs::write(&project, original).unwrap();
    let artifact = b"retained output";
    fs::write(output.join("00.png"), artifact).unwrap();
    let metadata = json!({"job_id":id,"status":"failed","project":project,
        "project_sha256":format!("{:x}",Sha256::digest(original)),"output_root":root,
        "output":output,"selected_scenes":["One","Two"],"scenes":[
            {"name":"One","status":"complete","artifact":{"file":"00.png","sha256":format!("{:x}",Sha256::digest(artifact))}},
            {"name":"Two","status":"failed"}]});
    let metadata_path = folder.join("job.json");
    let metadata_bytes = serde_json::to_vec(&metadata).unwrap();
    fs::write(&metadata_path, &metadata_bytes).unwrap();
    let script = root.join("fixed.py");
    fs::write(&script, "# fixture").unwrap();
    let executable = root.join("fake-blender");
    fs::write(&executable,"#!/usr/bin/env python3\nimport sys,time,json,pathlib\np=pathlib.Path(sys.argv[sys.argv.index('--metadata')+1]);p.with_name('argv.json').write_text(json.dumps(sys.argv[1:]));time.sleep(30)\n").unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    let manager = BlenderJobs::new(library.clone());
    fs::write(&project, b"BLENDER-v450changed").unwrap();
    assert!(manager
        .retry(executable.to_str().unwrap(), &script, &id, false)
        .await
        .unwrap_err()
        .contains("Project changed"));
    assert_eq!(fs::read_dir(&library).unwrap().count(), 1);
    fs::write(&project, original).unwrap();
    let retry_id = manager
        .retry(executable.to_str().unwrap(), &script, &id, false)
        .await
        .unwrap();
    assert_ne!(retry_id, id);
    let argv = library.join(&retry_id).join("argv.json");
    for _ in 0..40 {
        if argv.is_file() {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
    }
    let args: Vec<String> = serde_json::from_slice(&fs::read(argv).unwrap()).unwrap();
    assert!(args.contains(&"--scene=Two".into()));
    assert!(!args.contains(&"--scene=One".into()));
    let attempt = manager.status(&retry_id).await.unwrap();
    assert_eq!(attempt["parent_job_id"], id);
    assert_eq!(attempt["selected_scenes"], json!(["Two"]));
    manager.cancel(&retry_id).await.unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(350)).await;
    assert_eq!(fs::read(metadata_path).unwrap(), metadata_bytes);
    assert_eq!(fs::read(output.join("00.png")).unwrap(), artifact);
    fs::remove_dir_all(root).unwrap();
}

#[cfg(unix)]
#[tokio::test]
async fn owned_process_is_cancellable_and_arguments_cannot_enable_scripts() {
    use std::os::unix::fs::PermissionsExt;
    let root = workspace();
    let executable = root.join("fake-blender");
    fs::write(&executable,"#!/usr/bin/env python3\nimport sys,time,json,pathlib\np=pathlib.Path(sys.argv[sys.argv.index('--metadata')+1]);p.with_name('argv.json').write_text(json.dumps(sys.argv[1:]));time.sleep(30)\n").unwrap();
    fs::set_permissions(&executable, fs::Permissions::from_mode(0o700)).unwrap();
    let project = root.join("project.blend");
    fs::write(&project, b"BLENDER-v450fixture").unwrap();
    let script = root.join("fixed.py");
    fs::write(&script, "# fixture").unwrap();
    let manager = BlenderJobs::new(root.join("jobs"));
    let id = manager
        .start(
            executable.to_str().unwrap(),
            &script,
            project.to_str().unwrap(),
            root.to_str().unwrap(),
            vec!["--python=untrusted-label".into()],
            None,
        )
        .await
        .unwrap();
    let argv = root.join("jobs").join(&id).join("argv.json");
    for _ in 0..40 {
        if argv.is_file() {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
    }
    let args: Vec<String> = serde_json::from_slice(&fs::read(argv).unwrap()).unwrap();
    assert!(
        args.iter().position(|s| s == "--disable-autoexec").unwrap()
            < args
                .iter()
                .position(|s| s == project.canonicalize().unwrap().to_str().unwrap())
                .unwrap()
    );
    assert!(args.contains(&"--scene=--python=untrusted-label".into()));
    assert!(manager
        .start(
            executable.to_str().unwrap(),
            &script,
            project.to_str().unwrap(),
            root.to_str().unwrap(),
            vec!["other".into()],
            None
        )
        .await
        .is_err());
    manager.cancel(&id).await.unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(350)).await;
    assert_eq!(manager.status(&id).await.unwrap()["status"], "cancelled");
    assert_eq!(manager.status(&id).await.unwrap()["process_owned"], false);
    fs::remove_dir_all(root).unwrap();
}

#[tokio::test]
async fn missing_dependency_fails_without_process_or_rendered_output() {
    let root = workspace();
    let project = root.join("input.blend");
    fs::write(&project, b"BLENDER-v450fixture").unwrap();
    let script = root.join("fixed.py");
    fs::write(&script, "# fixture").unwrap();
    let manager = BlenderJobs::new(root.join("jobs"));
    assert!(manager
        .start(
            "/no-such-blender-executable",
            &script,
            project.to_str().unwrap(),
            root.to_str().unwrap(),
            vec!["one".into()],
            None
        )
        .await
        .is_err());
    let jobs = manager.list().await.unwrap();
    assert_eq!(jobs.len(), 1);
    assert_eq!(jobs[0]["status"], "failed");
    assert_eq!(jobs[0]["selected_scenes"][0], "one");
    assert!(manager
        .cancel(jobs[0]["job_id"].as_str().unwrap())
        .await
        .is_err());
    fs::remove_dir_all(root).unwrap();
}

#[tokio::test]
async fn invalid_paths_and_selections_are_rejected_before_library_creation() {
    let root = workspace();
    let manager = BlenderJobs::new(root.join("jobs"));
    assert!(manager
        .start(
            "unused",
            &root,
            "bad.blend",
            root.to_str().unwrap(),
            vec![],
            None
        )
        .await
        .is_err());
    assert!(manager.status("../../outside").await.is_err());
    assert!(!root.join("jobs").exists());
    fs::remove_dir_all(root).unwrap();
}

#[tokio::test]
async fn restarted_session_reports_interrupted_and_cannot_kill_persisted_pid() {
    let root = workspace();
    let id = "a".repeat(32);
    fs::create_dir(root.join(&id)).unwrap();
    fs::write(
        root.join(&id).join("job.json"),
        serde_json::to_vec(
            &json!({"job_id":id,"status":"running","pid":std::process::id(),"scenes":[]}),
        )
        .unwrap(),
    )
    .unwrap();
    let restarted = BlenderJobs::new(root.clone());
    let status = restarted.status(&id).await.unwrap();
    assert_eq!(status["status"], "interrupted");
    assert_eq!(status["process_owned"], false);
    assert!(restarted.cancel(&id).await.is_err());
    assert!(restarted
        .retry("unused", &root, &id, false)
        .await
        .unwrap_err()
        .contains("previous worker"));
    fs::remove_dir_all(root).unwrap();
}

#[tokio::test]
async fn changed_artifacts_and_path_escape_cannot_be_reported_complete() {
    let root = workspace();
    let id = "b".repeat(32);
    fs::create_dir(root.join(&id)).unwrap();
    fs::write(root.join("00.png"), b"changed artifact").unwrap();
    let path = root.join(&id).join("job.json");
    let mut value = json!({"job_id":id,"status":"complete","output":root,"scenes":[{"name":"one","status":"complete","artifact":{"file":"00.png","sha256":"0".repeat(64)}}]});
    fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
    let manager = BlenderJobs::new(root.clone());
    assert!(manager.status(&id).await.unwrap_err().contains("checksum"));
    value["scenes"][0]["artifact"]["file"] = json!("../outside.png");
    fs::write(&path, serde_json::to_vec(&value).unwrap()).unwrap();
    assert!(manager
        .status(&id)
        .await
        .unwrap_err()
        .contains("artifact name"));
    fs::remove_dir_all(root).unwrap();
}
