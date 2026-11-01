use base64::{engine::general_purpose::STANDARD, Engine};
use std::{
    env, fs,
    hash::{DefaultHasher, Hash, Hasher},
    path::{Path, PathBuf},
};

fn data_url(path: &Path) -> String {
    let mime = match path.extension().and_then(|value| value.to_str()) {
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        value => panic!("unsupported bundled logo type: {value:?}"),
    };
    format!(
        "data:{mime};base64,{}",
        STANDARD.encode(fs::read(path).unwrap())
    )
}

fn main() {
    let repository = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("../../..");
    let module = repository.join("modules/social-management");
    let mut paths = vec![module.join("catalog.yaml"), module.join("requirements.txt")];
    for entry in fs::read_dir(module.join("social_management")).unwrap() {
        let path = entry.unwrap().path();
        if path.extension().and_then(|value| value.to_str()) == Some("py") {
            paths.push(path);
        }
    }
    for entry in fs::read_dir(module.join("assets/brands")).unwrap() {
        let path = entry.unwrap().path();
        if path.is_file() {
            paths.push(path);
        }
    }
    paths.sort();

    let canonical_repository = repository.canonicalize().unwrap();
    let mut source = String::from("const ASSETS: &[(&str, &[u8])] = &[\n");
    let mut hasher = DefaultHasher::new();
    for path in &paths {
        let canonical = path.canonicalize().unwrap();
        assert!(canonical.starts_with(&canonical_repository));
        let relative = canonical.strip_prefix(&canonical_repository).unwrap();
        println!("cargo:rerun-if-changed={}", canonical.display());
        relative.hash(&mut hasher);
        fs::read(&canonical).unwrap().hash(&mut hasher);
        source.push_str(&format!(
            "({:?}, include_bytes!({:?})),\n",
            relative.to_string_lossy(),
            canonical.to_str().unwrap()
        ));
    }
    source.push_str("];\n");

    let catalog_yaml = fs::read_to_string(module.join("catalog.yaml")).unwrap();
    let catalog: serde_yaml::Value = serde_yaml::from_str(&catalog_yaml).unwrap();
    let catalog_json = serde_json::to_string(&catalog).unwrap();
    source.push_str(&format!("const CATALOG_JSON: &str = {:?};\n", catalog_json));
    source.push_str("const LOGOS: &[(&str, &str)] = &[\n");
    for entry in fs::read_dir(module.join("assets/brands")).unwrap() {
        let path = entry.unwrap().path();
        if path.is_file() {
            let relative = path.strip_prefix(&module).unwrap().to_string_lossy();
            source.push_str(&format!("({:?}, {:?}),\n", relative, data_url(&path)));
        }
    }
    source.push_str(&format!(
        "];\nconst ASSET_VERSION: &str = \"{:016x}\";\n",
        hasher.finish()
    ));
    fs::write(
        PathBuf::from(env::var("OUT_DIR").unwrap()).join("assets.rs"),
        source,
    )
    .unwrap();
    tauri_plugin::Builder::new(&[
        "snapshot",
        "selection",
        "activate_profile",
        "save_selection",
        "start",
        "status",
        "authorize",
        "connections",
        "disconnect",
    ])
    .build();
}
