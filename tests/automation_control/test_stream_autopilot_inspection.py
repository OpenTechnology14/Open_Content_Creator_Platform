"""A production readiness inspection must never acquire or shut down effect ownership."""
import asyncio
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
from stream_autopilot import __main__ as cli  # noqa: E402
from stream_autopilot.models import CapabilityCheck  # noqa: E402

CONFIG = ROOT / "configs/local/stream-supervisor.yaml"
RUNTIME = ROOT / "configs/local/stream-runtime.yaml"


def test_inspection_only_preflights_and_closes_http(monkeypatch):
    calls = []
    class Http:
        async def aclose(self):
            calls.append("http-close")
    class Driver:
        def __init__(self, settings):
            self.http = Http()
        async def preflight(self, session, policy):
            calls.append("preflight")
            return [CapabilityCheck(id="dependency", status="missing", detail="not installed")]
        async def close(self):
            pytest.fail("effect shutdown must not run")
    monkeypatch.setattr(cli, "ProductionDriver", Driver)
    result = asyncio.run(cli.inspect_production(CONFIG, RUNTIME))
    assert calls == ["preflight", "http-close"]
    assert result["ready"] is False
    assert result["workers_started"] is False
    assert result["broadcast_started"] is False


def test_inspection_failure_still_closes_only_http(monkeypatch):
    calls = []
    class Http:
        async def aclose(self):
            calls.append("http-close")
    class Driver:
        def __init__(self, settings):
            self.http = Http()
        async def preflight(self, session, policy):
            raise RuntimeError("validation failed")
    monkeypatch.setattr(cli, "ProductionDriver", Driver)
    with pytest.raises(RuntimeError):
        asyncio.run(cli.inspect_production(CONFIG, RUNTIME))
    assert calls == ["http-close"]


def test_unknown_session_never_constructs_effect_driver(monkeypatch):
    monkeypatch.setattr(cli, "ProductionDriver", lambda _: pytest.fail("driver constructed"))
    with pytest.raises(ValueError, match="enabled configured"):
        asyncio.run(cli.inspect_production(CONFIG, RUNTIME, "unknown-session"))
