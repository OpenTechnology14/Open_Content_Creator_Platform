use std::{env, fs, path::PathBuf};

fn bundled_tool_files(root: &PathBuf) -> String {
    let files = [
        "modules/image-editing/krita/scripts/apply_style.py",
        "modules/image-editing/krita/scripts/batch_upscale.py",
        "modules/image-editing/krita/scripts/export_to_minio.py",
        "modules/sports-analytics/pose-estimation/posture_screen.py",
        "modules/asset-pipeline/asset_pipeline/__init__.py",
        "modules/asset-pipeline/asset_pipeline/client.py",
        "modules/content-creation/blender/scripts/batch_render.py",
        "plugins/blender-addon/__init__.py",
        "plugins/blender-addon/preferences.py",
        "plugins/blender-addon/panels.py",
        "plugins/blender-addon/operators/__init__.py",
    ];
    let mut code = String::from("const BUNDLED_TOOL_FILES: &[(&str, &str)] = &[\n");
    for relative in files {
        let source = root
            .join(relative)
            .canonicalize()
            .expect("tool source missing");
        assert!(source.starts_with(root), "tool source escapes repository");
        println!("cargo:rerun-if-changed={}", source.display());
        code.push_str(&format!(
            "({relative:?}, include_str!({:?})),\n",
            source.to_str().unwrap()
        ));
    }
    code.push_str("];\n");
    code
}

fn main() {
    // Bundle curated JSON as compiled resources so launch directory and OS paths do not matter.
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .join("../../..")
        .canonicalize()
        .expect("repository root missing");
    let mut sources = Vec::new();
    for directory in [
        "modules/image-editing/workflows",
        "modules/realtime-ai/comfyui/workflows",
    ] {
        let base = root
            .join(directory)
            .canonicalize()
            .expect("workflow directory missing");
        println!("cargo:rerun-if-changed={}", base.display());
        for entry in fs::read_dir(&base).unwrap() {
            let path = entry.unwrap().path();
            if path.extension().and_then(|x| x.to_str()) != Some("json") {
                continue;
            }
            let canonical = path.canonicalize().unwrap();
            assert!(
                canonical.starts_with(&base),
                "workflow symlink escapes curated directory"
            );
            let key = format!(
                "{}/{}",
                directory,
                path.file_name().unwrap().to_str().unwrap()
            );
            sources.push((key, canonical));
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
    fs::write(
        PathBuf::from(env::var("OUT_DIR").unwrap()).join("tool_catalog.rs"),
        bundled_tool_files(&root),
    )
    .unwrap();
    tauri_build::build()
}
