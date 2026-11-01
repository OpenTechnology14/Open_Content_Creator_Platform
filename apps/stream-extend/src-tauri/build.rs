use std::{env, fs, path::PathBuf};
fn main() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .join("../../..")
        .canonicalize()
        .unwrap();
    let mut paths = Vec::new();
    for directory in [
        "modules/automation-control/stream_autopilot",
        "modules/automation-control/stream_director",
        "modules/ai-agents/stream_host",
        "modules/audio-production/stream_speech",
        "modules/character-avatar/stream_avatar",
        "modules/character-avatar/vtube",
        "modules/backend-api/twitch_chat",
    ] {
        let mut directories = vec![root.join(directory)];
        while let Some(dir) = directories.pop() {
            for entry in fs::read_dir(dir).unwrap() {
                let path = entry.unwrap().path();
                if path.is_dir()
                    && !matches!(
                        path.file_name().unwrap().to_str(),
                        Some("__pycache__" | "node_modules" | ".git")
                    )
                {
                    directories.push(path);
                } else if path
                    .extension()
                    .is_some_and(|ext| ext == "py" || ext == "ps1" || ext == "mjs" || ext == "json")
                {
                    paths.push(path);
                }
            }
        }
    }
    for name in [
        "stream-supervisor",
        "stream-runtime",
        "stream-autopilot",
        "stream-director",
        "stream-speech",
        "stream-avatar",
        "twitch-chat",
    ] {
        paths.push(root.join(format!("configs/local/{name}.yaml")));
    }
    paths.push(root.join("configs/local/minecraft-gameplay.json"));
    paths.push(root.join("modules/soundboard/sounds/manifest.yaml"));
    paths.push(root.join("modules/audio-production/tts/windows_speech.ps1"));
    paths.sort();
    paths.dedup();
    let mut source = String::from("const FILES: &[(&str,&str)] = &[\n");
    for path in paths {
        let path = path.canonicalize().unwrap();
        assert!(path.starts_with(&root));
        let relative = path
            .strip_prefix(&root)
            .unwrap()
            .to_string_lossy()
            .replace('\\', "/");
        println!("cargo:rerun-if-changed={}", path.display());
        source.push_str(&format!(
            "({relative:?},include_str!({:?})),\n",
            path.to_str().unwrap()
        ));
    }
    source.push_str("];\n");
    fs::write(
        PathBuf::from(env::var("OUT_DIR").unwrap()).join("autopilot-assets.rs"),
        source,
    )
    .unwrap();
    tauri_build::build()
}
