use std::{
    collections::BTreeSet,
    env, fs,
    hash::{DefaultHasher, Hash, Hasher},
    path::{Path, PathBuf},
};

fn add_tree(root: &Path, relative: &str, paths: &mut BTreeSet<String>) {
    let directory = root.join(relative);
    for entry in fs::read_dir(&directory).unwrap() {
        let path = entry.unwrap().path();
        if path.is_dir() {
            if path.file_name().is_some_and(|name| name == "__pycache__") {
                continue;
            }
            let child = path
                .strip_prefix(root)
                .unwrap()
                .to_string_lossy()
                .replace('\\', "/");
            add_tree(root, &child, paths);
        } else if path.extension().is_none_or(|extension| extension != "pyc") {
            paths.insert(
                path.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/"),
            );
        }
    }
}
fn main() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("../../..");
    let catalog = "configs/local/module-install-catalog.json";
    let value: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(root.join(catalog)).unwrap()).unwrap();
    let mut paths: BTreeSet<String> = [
        catalog,
        "configs/local/audio-setup.json",
        "modules/audio-production/routing/blackhole-loopback.json",
        "modules/audio-production/routing/pipewire.conf",
        "modules/audio-production/voicemeeter/potato-config.xml",
        "scripts/setup/capture_devices.py",
        "scripts/setup/capture_test.py",
        "scripts/setup/modules.py",
        "scripts/setup/module_readiness.py",
        "scripts/setup/postgres_container_migrate.sh",
        "modules/creator-experience/scenes/default.json",
        "docker-compose.yml",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();
    for directory in [
        "modules/backend-api/fastapi",
        "modules/observability",
        "modules/broadcast-graphics/nodecg/bundles",
        "modules/automation-control/n8n/workflows",
        "modules/storage-data/postgres/migrations",
        "modules/storage-data/minio",
        "modules/ai-agents/local-llm/migrations",
    ] {
        add_tree(&root, directory, &mut paths);
    }
    for item in value["modules"].as_object().unwrap().values() {
        for key in ["manual", "automated"] {
            paths.insert(item[key].as_str().unwrap().into());
        }
        for path in item["requirements"].as_array().unwrap() {
            paths.insert(path.as_str().unwrap().into());
        }
    }
    let mut source = String::from("const ASSETS: &[(&str,&str)] = &[\n");
    let mut hash = DefaultHasher::new();
    for path in paths {
        let absolute = root.join(&path).canonicalize().unwrap();
        assert!(absolute.starts_with(root.canonicalize().unwrap()));
        println!("cargo:rerun-if-changed={}", absolute.display());
        path.hash(&mut hash);
        fs::read(&absolute).unwrap().hash(&mut hash);
        source.push_str(&format!(
            "({:?},include_str!({:?})),\n",
            path,
            absolute.to_str().unwrap()
        ));
    }
    source.push_str(&format!(
        "];\nconst ASSET_VERSION: &str = \"{:016x}\";\n",
        hash.finish()
    ));
    fs::write(
        PathBuf::from(env::var("OUT_DIR").unwrap()).join("assets.rs"),
        source,
    )
    .unwrap();
    tauri_plugin::Builder::new(&[
        "snapshot",
        "audio_setup_status",
        "python_status",
        "start_python_bootstrap",
        "ffmpeg_status",
        "start_ffmpeg_bootstrap",
        "obs_status",
        "start_obs_bootstrap",
        "launch_obs",
        "obs_scene_plan",
        "docker_status",
        "docker_plan",
        "start_docker_bootstrap",
        "launch_docker_desktop",
        "start_docker_services",
        "start_local_service_bootstrap",
        "copy_local_credential",
        "save_selection",
        "manual",
        "check",
        "capture_scan",
        "capture_test",
        "save_capture_selection",
        "start_install",
        "job_status",
    ])
    .build();
}
