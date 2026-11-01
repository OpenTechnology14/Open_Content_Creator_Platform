"""A clean runner must generate embedded frontend assets before native tests."""

from pathlib import Path

import yaml


def test_installer_workflow_builds_frontend_before_native_tests() -> None:
    repo = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load(
        (repo / ".github/workflows/desktop-installers.yml").read_text()
    )
    steps = workflow["jobs"]["windows"]["steps"]
    frontend_built = False
    for step in steps:
        command = step.get("run", "")
        if "cargo test" in command:
            assert frontend_built, "Tauri generate_context! needs frontendDist on a clean host"
        if "npm run build" in command or "npm run tauri build" in command:
            frontend_built = True
