"""Exercise live-fixture commands with a fake Docker process; no real services."""
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]


def test_relay_fixture_tears_down_only_its_owned_container(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("relay_owned_fixture", ROOT / "tests/cloud_relay/conftest.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    commands = []

    def run(args, **kwargs):
        commands.append(args)
        return SimpleNamespace(returncode=0, stdout="127.0.0.1:55432\n", stderr="")

    async def ready(_):
        return True

    monkeypatch.setattr(fixture.shutil, "which", lambda tool: "docker" if tool == "docker" else None)
    monkeypatch.setattr(fixture.subprocess, "run", run)
    monkeypatch.setattr(fixture, "_ready", ready, raising=False)
    if hasattr(fixture, "_wait_for_postgres"):
        monkeypatch.setattr(fixture, "_wait_for_postgres", lambda: None)
    factory = SimpleNamespace(mktemp=lambda _: tmp_path)
    wrapped = fixture.relay_postgres.__wrapped__
    generator = wrapped(factory) if inspect.signature(wrapped).parameters else wrapped()
    next(generator)
    generator.close()
    assert not any("--volumes" in args or "--remove-orphans" in args for args in commands)
    start = next(args for args in commands if args[:2] == ["docker", "run"])
    owner = start[start.index("--name") + 1]
    assert owner.startswith("hcp-relay-acceptance-")
    assert "127.0.0.1::5432" in start
    assert ["docker", "rm", "--force", owner] in commands
