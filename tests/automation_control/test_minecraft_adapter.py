"""Only a declared private-world task can acquire game input; SDK checks never connect."""

from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))
from stream_autopilot.gameplay import load_game, MinecraftPeer  # noqa:E402


def fixture(tmp_path, **updates):
    value = json.loads((ROOT / "configs/local/minecraft-gameplay.json").read_text())
    value.update(updates)
    path = tmp_path / "game.json"
    path.write_text(json.dumps(value))
    return path


def test_permissions_public_targets_and_commands_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_game(fixture(tmp_path, enabled=True))
    with pytest.raises(ValueError):
        load_game(fixture(tmp_path, host="8.8.8.8"))
    with pytest.raises(ValueError):
        load_game(fixture(tmp_path, task={"action": "attack", "duration_ms": 500}))
    with pytest.raises(ValueError):
        load_game(fixture(tmp_path, username="administrator"))


def test_disabled_default_can_never_spawn_a_client(tmp_path, monkeypatch):
    import asyncio

    peer = MinecraftPeer(fixture(tmp_path))

    async def forbidden(*args, **kwargs):
        pytest.fail("game client spawned")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    with pytest.raises(ValueError):
        asyncio.run(peer.open())
