"""Gameplay ownership never changes show identity or claims an unacknowledged release."""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
from stream_director.handoff import GameplayHandoff, Receipt  # noqa: E402


class Adapter:
    def __init__(self):
        self.calls = []

    async def stop_and_release(self, epoch):
        self.calls.append(("release", epoch))
        return Receipt(epoch=epoch, action="released")

    async def synchronize_and_start(self, epoch):
        self.calls.append(("fresh-state", epoch))
        return Receipt(epoch=epoch, action="started")


def test_switching_fences_old_inputs_and_keeps_session_identity():
    async def scenario():
        adapter = Adapter()
        handoff = GameplayHandoff("show-session", adapter)
        assert not handoff.permits_agent_input(0)
        agent = await handoff.switch("agent")
        assert agent["input_owner"] == "agent"
        assert adapter.calls == [("release", 1), ("fresh-state", 1)]
        assert handoff.permits_agent_input(1)
        manual = await handoff.switch("manual")
        assert manual["input_owner"] == "manual"
        assert manual["session_id"] == agent["session_id"]
        assert not handoff.permits_agent_input(1)
        resumed = await handoff.switch("agent")
        assert handoff.permits_agent_input(resumed["epoch"])
        assert not handoff.permits_agent_input(1)
        paused = await handoff.switch("paused")
        assert paused["input_owner"] == "paused"

    asyncio.run(scenario())


def test_missing_or_wrong_ack_cannot_claim_manual_control():
    async def scenario():
        missing = GameplayHandoff("show", None)
        assert (await missing.switch("manual"))["input_owner"] == "blocked"

        class Wrong(Adapter):
            async def stop_and_release(self, epoch):
                return Receipt(epoch=epoch + 1, action="released")

        wrong = GameplayHandoff("show", Wrong())
        assert (await wrong.switch("manual"))["input_owner"] == "blocked"

    asyncio.run(scenario())


def test_late_start_after_timeout_cannot_restore_agent_ownership():
    async def scenario():
        finish = asyncio.Event()

        class Slow(Adapter):
            async def synchronize_and_start(self, epoch):
                try:
                    await finish.wait()
                except asyncio.CancelledError:
                    await finish.wait()
                return Receipt(epoch=epoch, action="started")

        handoff = GameplayHandoff("show", Slow(), timeout_seconds=0.01)
        result = await handoff.switch("agent")
        assert result["input_owner"] == "blocked"
        assert not handoff.permits_agent_input(result["epoch"])
        pending = await handoff.switch("manual")
        assert pending["reason"] == "prior_adapter_operation_still_running"
        finish.set()
        await asyncio.sleep(0.01)
        assert not handoff.permits_agent_input(result["epoch"])
        assert (await handoff.switch("manual"))["input_owner"] == "manual"

    asyncio.run(scenario())


def test_takeover_supersedes_an_inflight_agent_start():
    async def scenario():
        started, finish = asyncio.Event(), asyncio.Event()

        class Slow(Adapter):
            async def synchronize_and_start(self, epoch):
                started.set()
                await finish.wait()
                return Receipt(epoch=epoch, action="started")

        handoff = GameplayHandoff("same-show", Slow(), timeout_seconds=0.1)
        launch = asyncio.create_task(handoff.switch("agent"))
        await started.wait()
        takeover = asyncio.create_task(handoff.switch("manual"))
        await asyncio.sleep(0)
        assert not handoff.permits_agent_input(1)
        finish.set()
        await launch
        result = await takeover
        assert result["input_owner"] == "manual"
        assert result["epoch"] == 2

    asyncio.run(scenario())
