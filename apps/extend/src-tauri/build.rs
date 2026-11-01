use std::{env, fs, path::PathBuf};
fn main() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .join("../../..")
        .canonicalize()
        .unwrap();
    let mut sources = Vec::new();
    for directory in [
        "modules/image-editing/workflows",
        "modules/realtime-ai/comfyui/workflows",
    ] {
        let base = root.join(directory).canonicalize().unwrap();
        println!("cargo:rerun-if-changed={}", base.display());
        for entry in fs::read_dir(&base).unwrap() {
            let path = entry.unwrap().path();
            if path.extension().and_then(|value| value.to_str()) != Some("json") {
                continue;
            }
            let canonical = path.canonicalize().unwrap();
            assert!(
                canonical.starts_with(&base),
                "workflow escaped its curated directory"
            );
            sources.push((
                format!(
                    "{}/{}",
                    directory,
                    path.file_name().unwrap().to_str().unwrap()
                ),
                canonical,
            ));
        }
    }
    sources.sort_by(|a, b| a.0.cmp(&b.0));
    let mut code = String::from("const BUNDLED_WORKFLOWS: &[(&str, &str)] = &[\n");
    for (key, path) in sources {
        code.push_str(&format!(
            "({:?}, include_str!({:?})),\n",
            key,
            path.to_str().unwrap()
        ));
    }
    code.push_str("];\n");
    fs::write(
        PathBuf::from(env::var("OUT_DIR").unwrap()).join("workflow_catalog.rs"),
        code,
    )
    .unwrap();
    tauri_build::build();
}
