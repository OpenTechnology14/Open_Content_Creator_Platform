"""P-056 production worker composition and local safety contracts."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
import httpx
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from stream_autopilot.models import load_config  # noqa: E402
from stream_autopilot.production import (  # noqa: E402
    ProductionDriver,
    RuntimeSettings,
    load_runtime_settings,
)


def test_runtime_config_resolves_fixed_module_configs_and_rejects_unknown_fields():
    settings = load_runtime_settings(ROOT / "configs/local/stream-runtime.yaml")
    assert settings.host_config.is_absolute()
    assert settings.host_config.name == "stream-autopilot.yaml"
    assert settings.checked_backend_url() == "http://127.0.0.1:8000"
    assert settings.on_air_session == "minecraft-main"
    with pytest.raises(ValidationError):
        RuntimeSettings.model_validate({**settings.model_dump(), "command": "viewer supplied"})


class FakeDriver(ProductionDriver):
    def __init__(self, settings):
        super().__init__(settings)
        self.calls = []

    def _commands(self, *, validate=False):
        return {
            "host": (["host"], "ai-agents"),
            "speech": (["speech"], "audio-production"),
        }

    async def _spawn(self, name, command, module):
        self.calls.append(("spawn", name))

    async def _terminate(self, name):
        self.calls.append(("terminate", name))

    async def _hard_terminate(self, name):
        self.calls.append(("hard-terminate", name))

    async def _control(self, session_id, action, paused):
        self.calls.append(("control", session_id, action, paused))

    async def _notify_control(self, session_id, action, paused):
        await self._control(session_id, action, paused)


def test_real_model_preflight_requires_installed_model(monkeypatch):
    async def scenario():
        settings = load_runtime_settings(ROOT / "configs/local/stream-runtime.yaml")
        settings = settings.model_copy(update={"host_rehearsal": False})
        policy = load_config(ROOT / "configs/local/stream-supervisor.yaml").sessions["minecraft-main"]
        driver = FakeDriver(settings)
        driver._commands = lambda **kwargs: {}
        monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        monkeypatch.setenv("OLLAMA_MODEL", "required-model:latest")
        await driver.http.aclose()
        driver.http = httpx.AsyncClient(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"models": [{"name": "other:latest"}]})
        ))
        checks = await driver.preflight("minecraft-main", policy)
        assert any(check.id == "local-model" and check.status == "missing" for check in checks)
        await driver.http.aclose()
    asyncio.run(scenario())


def test_preview_pause_resume_and_stop_put_hard_audio_stop_first():
    async def scenario():
        settings = load_runtime_settings(ROOT / "configs/local/stream-runtime.yaml")
        policy = load_config(ROOT / "configs/local/stream-supervisor.yaml").sessions[
            "minecraft-main"
        ]
        driver = FakeDriver(settings)
        await driver.preview("minecraft-main", policy)
        await driver.pause("minecraft-main", policy)
        await driver.preview("minecraft-main", policy)
        await driver.stop("minecraft-main", policy)
        await driver.close()
        assert driver.calls[:3] == [
            ("spawn", "host"),
            ("spawn", "speech"),
            ("control", "minecraft-main", "resume", False),
        ]
        pause = driver.calls.index(("control", "minecraft-main", "pause", True))
        assert driver.calls[3] == ("hard-terminate", "speech")
        assert {call[1] for call in driver.calls[3:pause]} == {
            "speech",
            "gameplay",
            "director",
            "avatar",
            "twitch",
            "host",
        }

    asyncio.run(scenario())


def test_control_event_matches_host_contract_and_off_air_preview_is_rejected(monkeypatch):
    async def scenario():
        captured = {}

        async def handler(request):
            captured.update(__import__("json").loads(request.content))
            return httpx.Response(201, json={})

        settings = load_runtime_settings(ROOT / "configs/local/stream-runtime.yaml")
        driver = FakeDriver(settings)
        await driver.http.aclose()
        driver.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        monkeypatch.setenv("HCP_API_KEY", "local-test-key")
        await ProductionDriver._control(driver, "minecraft-main", "pause", True)
        assert captured["data"]["kind"] == "pause"
        assert set(captured["data"]) == {
            "schema_version",
            "kind",
            "event_id",
            "session_id",
            "occurred_at",
        }
        policy = load_config(ROOT / "configs/local/stream-supervisor.yaml").sessions["dota-lobby"]
        with pytest.raises(ValueError):
            await driver.preview("dota-lobby", policy)
        await driver.close()

    asyncio.run(scenario())
