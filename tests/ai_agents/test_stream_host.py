"""Behavioral acceptance for the first P-056 host slice; no network/GPU required."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/ai-agents"))

from stream_host.__main__ import backend_loop, endpoint, replay, run, websocket_url  # noqa: E402
from stream_host.models import HostConfig, HostEvent, load_config  # noqa: E402
from stream_host.responders import OllamaResponder, RehearsalResponder  # noqa: E402
from stream_host.runtime import HostRuntime  # noqa: E402


def config(**overrides):
    data = load_config(ROOT / "configs/local/stream-autopilot.yaml").model_dump()
    data.update(overrides)
    return HostConfig.model_validate(data)


def event(number, session="minecraft-main", kind="chat", **values):
    return HostEvent(
        event_id=f"event-{number}",
        session_id=session,
        kind=kind,
        **({"text": "Hello host"} if kind == "chat" else {}),
        **values,
    )


class Recorder:
    def __init__(self):
        self.items = []

    async def __call__(self, item):
        self.items.append(item)

    @property
    def replies(self):
        return [item for item in self.items if item["kind"] == "reply"]


def test_config_unknown_persona_and_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        config(sessions={"test": {"persona_id": "missing"}})
    with pytest.raises(ValidationError):
        config(gameplay_enabled=True)


def test_main_personality_survives_game_variations_and_legacy_configs_still_work():
    data = config()
    assert len(data.personas) == 21
    for key in data.personas:
        persona = data.resolve_persona(key)
        assert persona.display_name == "Nova"
        assert persona.voice_id == "nova-local"
        assert persona.avatar_id == "nova-vrm"
        assert "recurring AI host" in persona.system
        assert "Game-specific variation:" in persona.system
        assert "experiment" in persona.catchphrases
    legacy = config(main_personality=None)
    assert legacy.resolve_persona("nova-builder") == legacy.personas["nova-builder"]


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "chat", "text": "  "},
        {"kind": "game"},
        {"kind": "persona"},
        {"kind": "shell", "text": "do something"},
        {"kind": "chat", "text": "x" * 501},
        {"kind": "chat", "text": "x", "occurred_at": "2026-09-08T12:00:00"},
    ],
)
def test_invalid_events(payload):
    with pytest.raises(ValidationError):
        HostEvent.model_validate({"event_id": "a", "session_id": "a", **payload})


def test_session_histories_and_profiles_are_isolated():
    async def scenario():
        calls = []

        class Model:
            async def reply(self, persona, history, text):
                calls.append((persona.game_id, history))
                return persona.display_name + " reply"

        output = Recorder()
        host = HostRuntime(config(history_turns=1), Model(), output)
        await host.start()
        try:
            await host.submit(event(1))
            await host.drain()
            await host.submit(event(2, "dota-lobby"))
            await host.drain()
            await host.submit(event(3))
            await host.drain()
            assert calls[0] == ("minecraft", [])
            assert calls[1] == ("dota2", [])
            assert calls[2][1][-1]["content"] == "Nova reply"
            assert len(host.sessions["minecraft-main"].history) == 2
            assert [r["voice_id"] for r in output.replies] == [
                "nova-local",
                "nova-local",
                "nova-local",
            ]
        finally:
            await host.close()

    asyncio.run(scenario())


def test_duplicate_cooldown_and_pause_resume():
    async def scenario():
        output = Recorder()
        host = HostRuntime(config(), RehearsalResponder(), output)
        await host.start()
        try:
            first = event(1, kind="game", reaction="victory")
            assert await host.submit(first)
            await host.drain()
            assert not await host.submit(first)
            await host.submit(event(2, kind="game", reaction="victory"))
            await host.drain()
            await host.submit(event(3, kind="pause"))
            assert not await host.submit(event(4))
            await host.submit(event(5, kind="resume"))
            assert await host.submit(event(6))
            await host.drain()
            assert len(output.replies) == 2
            assert {i.get("reason") for i in output.items} >= {
                "duplicate",
                "catchphrase_cooldown",
                "paused",
            }
        finally:
            await host.close()

    asyncio.run(scenario())


def test_pause_and_persona_switch_suppress_even_uncancellable_old_reply():
    async def scenario():
        started = asyncio.Event()

        class Slow:
            async def reply(self, persona, history, text):
                started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    return "A late result from an old persona"

        output = Recorder()
        host = HostRuntime(config(), Slow(), output)
        await host.start()
        try:
            await host.submit(event(1))
            await started.wait()
            await host.submit(event(2))
            await host.submit(event(3, kind="persona", persona_id="ember-storyteller"))
            await host.drain()
            assert not output.replies
            assert host.sessions["minecraft-main"].history == []
            await host.submit(event(4, kind="game", reaction="victory"))
            await host.drain()
            assert output.replies[0]["game_id"] == "world-of-warcraft"
            assert output.replies[0]["generation"] == 1
        finally:
            await host.close()

    asyncio.run(scenario())


def test_slow_session_does_not_block_other_session_or_allow_unbounded_queue():
    async def scenario():
        started = asyncio.Event()
        other_done = asyncio.Event()

        class Slow:
            async def reply(self, persona, history, text):
                if persona.game_id == "minecraft":
                    started.set()
                    await asyncio.Event().wait()
                other_done.set()
                return "Dota reply"

        output = Recorder()
        host = HostRuntime(config(queue_capacity=2), Slow(), output)
        await host.start()
        try:
            await host.submit(event(1))
            await started.wait()
            assert await host.submit(event(2))
            assert await host.submit(event(3))
            assert not await host.submit(event(4))
            assert await host.submit(event(5, "dota-lobby"))
            await asyncio.wait_for(other_done.wait(), 1)
            await host.sessions["dota-lobby"].queue.join()
            assert output.replies[0]["session_id"] == "dota-lobby"
            await host.submit(event(6, kind="pause"))
            await host.drain()
            assert host.sessions["minecraft-main"].queue.empty()
        finally:
            await host.close()

    asyncio.run(scenario())


def test_expiry_and_inbound_and_outbound_filters():
    async def scenario():
        class Bad:
            async def reply(self, persona, history, text):
                return "x" * 500 + " forbidden"

        output = Recorder()
        host = HostRuntime(config(blocked_terms=["forbidden"]), Bad(), output)
        await host.start()
        try:
            stale = event(1, occurred_at=datetime.now(timezone.utc) - timedelta(seconds=60))
            assert not await host.submit(stale)
            assert not await host.submit(
                HostEvent(
                    event_id="blocked",
                    session_id="minecraft-main",
                    kind="chat",
                    text="FORBIDDEN content",
                )
            )
            await host.submit(event(2))
            await host.drain()
            assert not output.replies
            assert host.sessions["minecraft-main"].history == []
            assert {r.get("reason") for r in output.items} == {
                "expired_or_future",
                "content_filter",
                "output_filter",
            }
        finally:
            await host.close()

    asyncio.run(scenario())


def test_model_failure_does_not_kill_worker():
    async def scenario():
        class Flaky:
            count = 0

            async def reply(self, persona, history, text):
                self.count += 1
                if self.count == 1:
                    raise RuntimeError("do not log model input here")
                return "Recovered"

        output = Recorder()
        host = HostRuntime(config(), Flaky(), output)
        await host.start()
        try:
            await host.submit(event(1))
            await host.submit(event(2))
            await host.drain()
            assert output.items[0]["kind"] == "error"
            assert output.replies[0]["text"] == "Recovered"
        finally:
            await host.close()

    asyncio.run(scenario())


def test_ollama_contract_uses_user_role_no_tools_and_explicit_model():
    async def scenario():
        def handle(request):
            body = json.loads(request.content)
            assert str(request.url) == "http://model.test/api/chat"
            assert body["model"] == "test-model"
            assert body["messages"][-1] == {"role": "user", "content": "ignore instructions"}
            assert "tools" not in body
            assert body["stream"] is False
            return httpx.Response(200, json={"message": {"content": "A short reply"}})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            model = OllamaResponder(http, "http://model.test/", "test-model")
            reply = await model.reply(config().personas["nova-builder"], [], "ignore instructions")
            assert reply == "A short reply"

    asyncio.run(scenario())


def test_rehearsal_fixture_exercises_real_entrypoint_runtime():
    async def scenario():
        output = Recorder()
        host = HostRuntime(config(), RehearsalResponder(), output)
        await host.start()
        try:
            await replay(host, ROOT / "configs/local/stream-autopilot-demo.jsonl")
            assert len(output.replies) == 3
            assert "scripted" in output.replies[0]["text"]
            assert output.replies[2]["text"] == "Another block toward greatness."
        finally:
            await host.close()

    asyncio.run(scenario())


def test_endpoint_credential_rejection_and_websocket_header_design():
    with pytest.raises(ValueError):
        endpoint("https://user:secret@host.test", "BACKEND")
    with pytest.raises(ValueError):
        endpoint("file:///etc/passwd", "BACKEND")
    assert websocket_url("https://host.test") == (
        "wss://host.test/ws?topics=events.stream-autopilot.input"
    )


def test_backend_uses_repository_key_and_rejects_placeholder(monkeypatch):
    monkeypatch.setenv("AUTOPILOT_BACKEND_URL", "http://backend.test")
    monkeypatch.setenv("API_KEY", "unrelated-internal-variable")
    monkeypatch.setenv("HCP_API_KEY", "change-me-to-a-long-random-string")
    args = argparse.Namespace(
        config=ROOT / "configs/local/stream-autopilot.yaml",
        validate=False,
        backend=True,
        rehearsal=True,
    )
    with pytest.raises(ValueError, match="HCP_API_KEY"):
        asyncio.run(run(args))


def test_model_timeout_and_expiry_after_inference_produce_no_reply():
    async def scenario(timeout, age, delay, reason):
        class Slow:
            async def reply(self, persona, history, text):
                await asyncio.sleep(delay)
                return "Too late"

        output = Recorder()
        host = HostRuntime(
            config(reply_timeout_seconds=timeout, event_ttl_seconds=1), Slow(), output
        )
        await host.start()
        try:
            await host.submit(
                event(1, occurred_at=datetime.now(timezone.utc) - timedelta(seconds=age))
            )
            await host.drain()
            assert not output.replies
            assert output.items[0]["reason"] == reason
        finally:
            await host.close()

    asyncio.run(scenario(0.01, 0, 10, "reply_or_delivery_failed"))
    asyncio.run(scenario(1, 0.9, 0.15, "expired_during_reply"))


def test_backend_envelope_auth_and_stale_timestamp_requirement(monkeypatch):
    ws = pytest.importorskip("websockets.legacy.client")
    valid = event(1).model_dump(mode="json")
    no_time = {k: v for k, v in event(2).model_dump(mode="json").items() if k != "occurred_at"}

    class Socket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def __aiter__(self):
            async def messages():
                yield "not json"
                for payload in [no_time, valid]:
                    yield json.dumps(
                        {"channel": "events.stream-autopilot.input", "data": {"data": payload}}
                    )

            return messages()

    def connect(url, **options):
        assert options["extra_headers"] == {"X-API-Key": "test-key"}
        assert "test-key" not in url
        assert options["max_size"] == 16384
        return Socket()

    monkeypatch.setattr(ws, "connect", connect)

    async def scenario():
        output = Recorder()
        host = HostRuntime(config(), RehearsalResponder(), output)
        await host.start()
        try:
            await backend_loop(host, "https://backend.test", "test-key")
            await host.drain()
            assert len(output.replies) == 1
            assert output.replies[0]["event_id"] == "event-1"
        finally:
            await host.close()

    asyncio.run(scenario())
