"""The default stack must build verifiable MinIO artifacts without retired image tags."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_acceptance_teardown_is_namespaced(monkeypatch):
    """A live acceptance run must never delete the user's default storage volumes."""
    import importlib.util
    import subprocess

    spec = importlib.util.spec_from_file_location("acceptance_fixture_helpers", ROOT / "tests/acceptance/conftest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._compose("down", "--volumes")
    args = calls[0]
    assert args[2:4] == ["--project-name", module.ACCEPTANCE_PROJECT]
    assert module.ACCEPTANCE_PROJECT.startswith("hcp-acceptance-")
    assert module.ACCEPTANCE_PROJECT != "hybrid-creator-platform"


def test_minio_services_build_from_narrow_bundled_context():
    services = yaml.safe_load((ROOT / "docker-compose.yml").read_text())["services"]
    for name, target in [("minio", "server"), ("minio-bootstrap", "client")]:
        service = services[name]
        assert service.get("build") == {
            "context": "./modules/storage-data/minio",
            "dockerfile": "Dockerfile",
            "target": target,
        }
        assert service["pull_policy"] == "build"
        assert "quay.io" not in service["image"]
    assert services["minio"]["volumes"] == ["minio-data:/data"]
    assert all(port.startswith("127.0.0.1:") for port in services["minio"]["ports"])


def test_minio_sources_and_base_images_are_checksum_pinned():
    import json
    import re

    folder = ROOT / "modules/storage-data/minio"
    provenance = json.loads((folder / "provenance.json").read_text())
    recipe = (folder / "Dockerfile").read_text()
    for component in ["server", "client"]:
        item = provenance[component]
        assert re.fullmatch(r"[a-f0-9]{40}", item["commit"])
        assert re.fullmatch(r"[a-f0-9]{64}", item["archive_sha256"])
        assert item["archive_url"] in recipe
        assert f"--checksum=sha256:{item['archive_sha256']}" in recipe
    for base in provenance["base_images"].values():
        assert re.search(r"@sha256:[a-f0-9]{64}$", base)
        assert base in recipe
    assert "-mod=readonly" in recipe


def test_acceptance_ci_builds_server_and_client_before_live_harness():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["lint-and-test"]["steps"]
    build = next(i for i, step in enumerate(steps) if step.get("run") == "docker compose build minio minio-bootstrap")
    acceptance = next(i for i, step in enumerate(steps) if step.get("run") == "make test-acceptance")
    assert build < acceptance
