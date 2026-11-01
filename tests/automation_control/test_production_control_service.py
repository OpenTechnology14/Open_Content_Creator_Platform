"""Production RPC cancellation fences old effects and never stops unowned playback."""

import asyncio
import io
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
from stream_autopilot import __main__ as cli  # noqa: E402
from stream_autopilot.models import CapabilityCheck  # noqa: E402
from stream_autopilot.production import ProductionDriver, load_runtime_settings  # noqa: E402

CONFIG = ROOT / "configs/local/stream-supervisor.yaml"
RUNTIME = ROOT / "configs/local/stream-runtime.yaml"


def test_close_without_effects_never_triggers_hotkeys(monkeypatch):
    async def scenario():
        driver = ProductionDriver(load_runtime_settings(RUNTIME))

        async def forbidden():
            pytest.fail("unowned clip shutdown")

        monkeypatch.setattr(driver, "_stop_phrases", forbidden)
        await driver.close()

    asyncio.run(scenario())


def test_service_status_is_correlated_and_live_start_rejected(monkeypatch, tmp_path):
    class Driver:
        processes = {}

        def __init__(self, settings):
            pass

        async def preflight(self, session, policy):
            return [CapabilityCheck(id="fixture", status="ready", detail="owned test")]

        async def preview(self, session, policy):
            pass

        async def run(self, session, policy):
            pytest.fail("live start was allowed")

        async def stop(self, session, policy):
            pass

        async def close(self):
            pass

    frames = [
        {"session_id": None, "action": "status", "operation_id": "status-1"},
        {"session_id": "different-owner", "action": "stop", "operation_id": "wrong-1"},
        {"session_id": None, "action": "run", "operation_id": "run-1"},
    ]
    monkeypatch.setattr(cli, "ProductionDriver", Driver)
    monkeypatch.setattr(
        cli.sys, "stdin", io.StringIO("\n".join(json.dumps(x) for x in frames) + "\n")
    )
    output = io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", output)
    asyncio.run(cli.serve(CONFIG, RUNTIME, tmp_path / "production.json"))
    replies = {
        item["operation_id"]: item for item in map(json.loads, output.getvalue().splitlines())
    }
    assert replies["status-1"]["ok"]
    assert replies["status-1"]["policy"]["broadcast_start_authorized"] is False
    assert replies["wrong-1"]["error"] == "invalid_request"
    assert not replies["run-1"]["ok"]


def test_emergency_interrupts_pending_preflight(monkeypatch, tmp_path):
    started = False
    calls = []

    class Driver:
        processes = {}

        def __init__(self, settings):
            pass

        async def preflight(self, session, policy):
            nonlocal started
            started = True
            try:
                await asyncio.sleep(60)
            finally:
                calls.append("validation-interrupted")

        async def stop(self, session, policy):
            calls.append("stop")

        async def close(self):
            calls.append("close")

    class Input:
        index = 0

        def readline(self, bound):
            self.index += 1
            if self.index == 1:
                return (
                    json.dumps(
                        {"session_id": None, "action": "preflight", "operation_id": "slow-1"}
                    )
                    + "\n"
                )
            if self.index == 2:
                import time

                for _ in range(100):
                    if started:
                        break
                    time.sleep(0.001)
                return (
                    json.dumps(
                        {"session_id": None, "action": "emergency_stop", "operation_id": "stop-1"}
                    )
                    + "\n"
                )
            import time

            time.sleep(0.02)
            return ""

    monkeypatch.setattr(cli, "ProductionDriver", Driver)
    monkeypatch.setattr(cli.sys, "stdin", Input())
    output = io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", output)
    asyncio.run(cli.serve(CONFIG, RUNTIME, tmp_path / "production.json"))
    replies = {
        item["operation_id"]: item for item in map(json.loads, output.getvalue().splitlines())
    }
    assert replies["slow-1"]["error"] == "interrupted"
    assert replies["stop-1"]["status"]["lifecycle"] == "stopped"
    assert calls == ["validation-interrupted", "stop", "close"]


def test_oversized_frame_cannot_execute_its_tail(monkeypatch, tmp_path):
    class Driver:
        processes = {}

        def __init__(self, settings):
            pass

        async def close(self):
            pass

    monkeypatch.setattr(cli, "ProductionDriver", Driver)
    monkeypatch.setattr(
        cli.sys,
        "stdin",
        io.StringIO("x" * 4097 + '\n{"session_id":null,"action":"run","operation_id":"bad"}\n'),
    )
    output = io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", output)
    asyncio.run(cli.serve(CONFIG, RUNTIME, tmp_path / "production.json"))
    assert len(output.getvalue().splitlines()) == 1
    assert json.loads(output.getvalue())["error"] == "frame_too_large"


def test_only_one_service_can_own_the_same_state_file(tmp_path):
    with cli.production_lock(tmp_path / "state.json"):
        with pytest.raises(OSError):
            with cli.production_lock(tmp_path / "state.json"):
                pytest.fail("two owners")
    with cli.production_lock(tmp_path / "state.json"):
        pass
