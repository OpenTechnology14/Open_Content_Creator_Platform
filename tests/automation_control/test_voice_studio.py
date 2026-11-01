"""P-066: durable review gates, render ownership and source-reviewed script controls."""

import asyncio
import copy
import json
import struct
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
sys.path.insert(0, str(ROOT / "modules/ai-agents"))

from stream_host.author import catalog, prompt_for  # noqa: E402
from voice_studio import studio as module  # noqa: E402
from voice_studio.studio import Request, Studio  # noqa: E402


def wav(path):
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        out.writeframes(struct.pack("<h", 1200) * 2205)


async def make_studio(tmp_path, monkeypatch):
    async def fake_call(root, owning_module, entry, args, data, timeout=60):
        if data.get("action") == "catalog":
            return catalog(ROOT / "configs/local/stream-autopilot.yaml")
        if data.get("action") == "prompt":
            p = catalog(ROOT / "configs/local/stream-autopilot.yaml")[data["persona_id"]]
            return {"prompt": prompt_for(p)}
        if data.get("action") == "generate":
            return {"phrases": [{"reaction": "victory", "text": "A good block day."}]}
        if data.get("action") == "answer":
            return {"answer": "The brief describes local rendering."}
        wav(Path(data["output"]))
        return {"duration_seconds": 0.1}

    monkeypatch.setattr(module, "call", fake_call)
    studio = Studio(ROOT, tmp_path, ROOT / "configs/local/voice-studio.yaml")
    await studio.start()
    return studio


async def create_ready(studio):
    result = await studio.handle(Request(action="create", persona_id="nova-builder", model="test"))
    ident = result["revision_id"]
    await studio.handle(Request(action="preview", revision_id=ident, generate=True))
    await studio.task
    assert studio.revision(ident)["status"] == "ready"
    return ident


async def approve(studio, ident):
    return await studio.handle(
        Request(action="approve", revision_id=ident, acceptance_confirmed=True)
    )


async def activate(studio, ident):
    return await studio.handle(
        Request(
            action="activate",
            revision_id=ident,
            bindings={"0": "play-0"},
            stop_hotkey="stop-all",
            acceptance_confirmed=True,
        )
    )


def test_generated_prompt_resolves_identity_and_policy(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        result = await studio.handle(Request(action="create", persona_id="nova-builder"))
        revision = studio.revision(result["revision_id"])
        assert "minecraft" in revision["prompt"] and "Nova" in revision["prompt"]
        assert revision["status"] == "draft" and not revision["assets"]
        with pytest.raises(ValueError, match="gaming"):
            await studio.handle(Request(action="create", persona_id="nova-opentech"))
        await studio.close()

    asyncio.run(scenario())


def test_review_activation_revision_and_rollback_are_separate(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        ident = await create_ready(studio)
        with pytest.raises(ValueError, match="Approve"):
            await activate(studio, ident)
        with pytest.raises(ValueError, match="Confirm"):
            await studio.handle(Request(action="approve", revision_id=ident))
        await approve(studio, ident)
        await activate(studio, ident)
        saved = copy.deepcopy(studio.revision(ident))
        draft = await studio.handle(
            Request(action="revise", revision_id=ident, feedback="Less exuberant")
        )
        assert studio.revision(ident) == saved
        assert studio.data["production"]["nova-builder"]["revision_id"] == ident
        assert "Less exuberant" in studio.revision(draft["revision_id"])["prompt"]
        with pytest.raises(ValueError):
            await activate(studio, draft["revision_id"])
        await studio.handle(Request(action="disable", revision_id=ident))
        assert json.loads((tmp_path / "production.json").read_text())["profiles"] == {}
        assert studio.asset_path(saved["assets"][0]).exists()
        await activate(studio, ident)
        await studio.close()
        restarted = await make_studio(tmp_path, monkeypatch)
        assert restarted.data["production"]["nova-builder"]["revision_id"] == ident
        await restarted.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("change", ["text", "audio", "context"])
def test_changed_review_material_cannot_activate(tmp_path, monkeypatch, change):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        ident = await create_ready(studio)
        await approve(studio, ident)
        revision = studio.revision(ident)
        if change == "text":
            revision["prompt"] += " changed"
        elif change == "context":
            studio.personas["nova-builder"] = {**studio.personas["nova-builder"], "system": "new"}
        else:
            (tmp_path / revision["assets"][0]["file"]).write_bytes(b"bad")
        with pytest.raises((ValueError, EOFError, wave.Error)):
            await activate(studio, ident)
        assert studio.data["production"] == {}
        await studio.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "text", ["", "word " * 19, "https://spam.test", "free vbucks", "bad\0value"]
)
def test_phrase_limits_before_native_synthesis(tmp_path, monkeypatch, text):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        with pytest.raises(ValueError, match="constraints"):
            await studio.handle(
                Request(
                    action="create",
                    persona_id="nova-builder",
                    phrases=[{"reaction": "victory", "text": text}],
                )
            )
        await studio.close()

    asyncio.run(scenario())


def test_cancel_never_promotes_and_retry_is_new_revision(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        created = await studio.handle(Request(action="create", persona_id="nova-builder"))
        ident = created["revision_id"]
        entered = asyncio.Event()

        async def slow(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(module, "call", slow)
        await studio.handle(Request(action="preview", revision_id=ident))
        await entered.wait()
        await studio.handle(Request(action="cancel", revision_id=ident))
        assert studio.revision(ident)["status"] == "canceled"
        assert studio.job_revision is None and not studio.data["production"]
        with pytest.raises(ValueError, match="new revision"):
            await studio.handle(Request(action="preview", revision_id=ident))
        await studio.close()

    asyncio.run(scenario())


def test_audition_and_unknown_inputs_fail_closed(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        ident = await create_ready(studio)
        with pytest.raises(ValueError, match="isolated"):
            await studio.handle(Request(action="audio", revision_id=ident))
        result = await studio.handle(
            Request(action="audio", revision_id=ident, monitor_confirmed=True)
        )
        assert result["mime"] == "audio/wav" and result["audio"].startswith("UklGR")
        with pytest.raises(ValueError):
            Request(action="audio", output_path="/arbitrary")
        await studio.close()

    asyncio.run(scenario())


def test_cancel_before_render_task_starts_is_durable(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        created = await studio.handle(Request(action="create", persona_id="nova-builder"))
        ident = created["revision_id"]
        await studio.handle(Request(action="preview", revision_id=ident))
        await studio.handle(Request(action="cancel", revision_id=ident))
        assert studio.revision(ident)["status"] == "canceled"
        assert studio.job_revision is None
        await studio.close()

    asyncio.run(scenario())


def test_script_boundary_pause_reviewed_answer_and_resume(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        await studio.handle(
            Request(
                action="script_load",
                persona_id="nova-opentech",
                segments=["First segment", "Second segment"],
                sources="Local rendering",
                acceptance_confirmed=True,
                model="test",
            )
        )
        started, finish = asyncio.Event(), asyncio.Event()
        spoken = []

        async def speak(text):
            spoken.append(text)
            started.set()
            await finish.wait()

        monkeypatch.setattr(studio.script, "speak", speak)
        await studio.handle(Request(action="script_play", monitor_confirmed=True))
        await started.wait()
        await studio.handle(Request(action="script_pause"))
        assert studio.script.state["cursor"] == 0
        finish.set()
        await studio.script.task
        assert studio.script.state["state"] == "paused_for_question"
        assert studio.script.state["cursor"] == 1
        await studio.handle(Request(action="script_question", question="Where is rendering?"))
        await studio.script.task
        with pytest.raises(ValueError):
            await studio.handle(Request(action="script_question", question="Duplicate"))
        with pytest.raises(ValueError, match="Approve"):
            await studio.handle(Request(action="script_answer", answer="Locally"))
        await studio.handle(
            Request(
                action="script_answer",
                answer="Locally",
                acceptance_confirmed=True,
                monitor_confirmed=True,
            )
        )
        await studio.script.task
        assert studio.script.state["state"] == "paused" and studio.script.state["cursor"] == 1
        await studio.handle(Request(action="script_resume", monitor_confirmed=True))
        await studio.script.task
        assert spoken == ["First segment", "Locally", "Second segment"]
        assert studio.script.state["state"] == "finished"
        assert not studio.data["revisions"] and not studio.data["production"]
        await studio.close()

    asyncio.run(scenario())


def test_script_stop_cancels_and_restart_does_not_autoplay(tmp_path, monkeypatch):
    async def scenario():
        studio = await make_studio(tmp_path, monkeypatch)
        await studio.handle(
            Request(
                action="script_load",
                persona_id="nova-ai-learning",
                segments=["Segment"],
                sources="Evidence",
                acceptance_confirmed=True,
            )
        )
        entered = asyncio.Event()

        async def speak(text):
            entered.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(studio.script, "speak", speak)
        await studio.handle(Request(action="script_play", monitor_confirmed=True))
        await entered.wait()
        await studio.handle(Request(action="script_stop"))
        assert studio.script.task.done() and studio.script.state["cursor"] == 0
        await studio.close()
        restarted = await make_studio(tmp_path, monkeypatch)
        assert restarted.script.state["state"] == "paused" and restarted.script.task is None
        await restarted.close()

    asyncio.run(scenario())
