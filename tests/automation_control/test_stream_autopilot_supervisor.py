"""Behavioral contracts for the durable Stream Autopilot lifecycle supervisor."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from stream_autopilot.models import CapabilityCheck, SupervisorConfig, load_config  # noqa: E402
from stream_autopilot.supervisor import SessionSupervisor  # noqa: E402


def configuration(**updates):
    data = load_config(ROOT / "configs/local/stream-supervisor.yaml").model_dump()
    data.update(updates)
    return SupervisorConfig.model_validate(data)


class Driver:
    def __init__(self, checks=None, fail=None, delay=0):
        self.checks = checks or [
            CapabilityCheck(id="test-runtime", status="ready", detail="test adapter ready")
        ]
        self.fail = fail
        self.delay = delay
        self.actions = []

    async def _do(self, action):
        self.actions.append(action)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail == action:
            raise RuntimeError("injected failure")

    async def preflight(self, session_id, policy):
        await self._do("preflight")
        return self.checks

    async def preview(self, session_id, policy):
        await self._do("preview")

    async def run(self, session_id, policy):
        await self._do("run")

    async def pause(self, session_id, policy):
        await self._do("pause")

    async def stop(self, session_id, policy):
        await self._do("stop")


def enabled_live_config(maximum=1):
    data = configuration().model_dump()
    data["max_concurrent_running"] = maximum
    for session in data["sessions"].values():
        session["broadcast_start_authorized"] = True
    return SupervisorConfig.model_validate(data)


async def ready_preview(supervisor, session="minecraft-main"):
    await supervisor.apply(session, "preflight", f"preflight-{session}")
    return await supervisor.apply(session, "preview", f"preview-{session}")


def test_policy_rejects_implicit_autonomy_and_impossible_budget():
    data = configuration().model_dump()
    data["sessions"]["minecraft-main"]["mode"] = "autonomous"
    with pytest.raises(ValidationError):
        SupervisorConfig.model_validate(data)
    data = configuration().model_dump()
    data["max_concurrent_running"] = 3
    with pytest.raises(ValidationError):
        SupervisorConfig.model_validate(data)


def test_full_operator_lifecycle_and_persisted_permissions(tmp_path):
    async def scenario():
        driver = Driver()
        state = tmp_path / "private" / "state.json"
        supervisor = SessionSupervisor(enabled_live_config(), driver, state)
        assert (await ready_preview(supervisor))["lifecycle"] == "preview"
        assert (await supervisor.apply("minecraft-main", "run", "run-1"))["lifecycle"] == "running"
        assert (await supervisor.apply("minecraft-main", "pause", "pause-1"))[
            "lifecycle"
        ] == "paused"
        assert (await supervisor.apply("minecraft-main", "resume", "resume-1"))[
            "lifecycle"
        ] == "preview"
        assert (await supervisor.apply("minecraft-main", "stop", "stop-1"))[
            "lifecycle"
        ] == "stopped"
        assert driver.actions == ["preflight", "preview", "run", "pause", "preview", "stop"]
        assert state.is_file()
        if sys.platform != "win32":
            assert state.stat().st_mode & 0o777 == 0o600

    asyncio.run(scenario())


def test_missing_required_capability_fails_closed(tmp_path):
    async def scenario():
        checks = [CapabilityCheck(id="avatar", status="missing", detail="renderer unavailable")]
        supervisor = SessionSupervisor(configuration(), Driver(checks), tmp_path / "state.json")
        result = await supervisor.apply("minecraft-main", "preflight", "one")
        assert result["lifecycle"] == "degraded"
        assert result["ready"] is False
        with pytest.raises(ValueError):
            await supervisor.apply("minecraft-main", "preview", "two")
        assert supervisor.status("minecraft-main")["lifecycle"] == "degraded"

    asyncio.run(scenario())


def test_operation_replay_is_idempotent_and_cross_action_reuse_is_rejected(tmp_path):
    async def scenario():
        driver = Driver()
        supervisor = SessionSupervisor(configuration(), driver, tmp_path / "state.json")
        first = await supervisor.apply("minecraft-main", "preflight", "same-operation")
        await supervisor.apply("minecraft-main", "preview", "advance-state")
        second = await supervisor.apply("minecraft-main", "preflight", "same-operation")
        assert first == second
        assert second["lifecycle"] == "preflight"
        assert driver.actions == ["preflight", "preview"]
        with pytest.raises(ValueError):
            await supervisor.apply("minecraft-main", "preview", "same-operation")

    asyncio.run(scenario())


def test_running_budget_is_enforced(tmp_path):
    async def scenario():
        supervisor = SessionSupervisor(enabled_live_config(), Driver(), tmp_path / "state.json")
        await ready_preview(supervisor, "minecraft-main")
        await ready_preview(supervisor, "dota-lobby")
        assert (await supervisor.apply("minecraft-main", "run", "run-minecraft"))[
            "lifecycle"
        ] == "running"
        with pytest.raises(ValueError):
            await supervisor.apply("dota-lobby", "run", "run-dota")
        assert supervisor.status("dota-lobby")["lifecycle"] == "preview"
        assert supervisor.status("minecraft-main")["lifecycle"] == "running"

    asyncio.run(scenario())


def test_restart_recovers_active_state_to_preview_and_requires_operator(tmp_path):
    async def scenario():
        state = tmp_path / "state.json"
        config = enabled_live_config()
        first = SessionSupervisor(config, Driver(), state)
        await ready_preview(first)
        await first.apply("minecraft-main", "run", "run-before-crash")
        recovered = SessionSupervisor(config, Driver(), state)
        status = recovered.status("minecraft-main")
        assert status["lifecycle"] == "preview"
        assert status["previous_lifecycle"] == "running"
        assert status["resume_required"] is True
        with pytest.raises(ValueError):
            await recovered.apply("minecraft-main", "run", "run-after-crash")
        assert recovered.status("minecraft-main")["lifecycle"] == "preview"

    asyncio.run(scenario())


def test_emergency_stop_timeout_is_visible_and_never_reports_stopped(tmp_path):
    async def scenario():
        data = configuration().model_dump()
        data["emergency_timeout_seconds"] = 0.01
        supervisor = SessionSupervisor(
            SupervisorConfig.model_validate(data), Driver(delay=0.1), tmp_path / "state.json"
        )
        result = await supervisor.apply("minecraft-main", "emergency_stop", "panic")
        assert result["lifecycle"] == "degraded"
        assert result["last_error"] == "emergency_stop failed: TimeoutError"

    asyncio.run(scenario())


def test_broadcast_requires_explicit_operator_policy(tmp_path):
    async def scenario():
        supervisor = SessionSupervisor(configuration(), Driver(), tmp_path / "state.json")
        await ready_preview(supervisor)
        with pytest.raises(ValueError):
            await supervisor.apply("minecraft-main", "run", "run-disabled")
        assert supervisor.status("minecraft-main")["lifecycle"] == "preview"

    asyncio.run(scenario())


def test_empty_preflight_can_never_authorize_preview(tmp_path):
    class Empty(Driver):
        async def preflight(self, session_id, policy):
            return []

    async def scenario():
        supervisor = SessionSupervisor(enabled_live_config(), Empty(), tmp_path / "state.json")
        result = await supervisor.apply("minecraft-main", "preflight", "empty-proof")
        assert result["ready"] is False
        with pytest.raises(ValueError):
            await supervisor.apply("minecraft-main", "preview", "empty-preview")

    asyncio.run(scenario())


def test_restart_requires_fresh_readiness_before_starting_workers(tmp_path):
    async def scenario():
        config = enabled_live_config()
        path = tmp_path / "state.json"
        first = SessionSupervisor(config, Driver(), path)
        await ready_preview(first)
        await first.apply("minecraft-main", "run", "old-run")
        recovered = SessionSupervisor(config, Driver(), path)
        with pytest.raises(ValueError):
            await recovered.apply("minecraft-main", "preview", "stale-preview")
        assert recovered.status("minecraft-main")["ready"] is False
        await recovered.apply("minecraft-main", "preflight", "fresh-proof")
        assert (await recovered.apply("minecraft-main", "preview", "fresh-preview"))[
            "lifecycle"
        ] == "preview"

    asyncio.run(scenario())
