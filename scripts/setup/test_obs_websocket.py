#!/usr/bin/env python3
"""Verify OBS WebSocket connectivity from this machine.

Usage, from the repo root, inside a virtual environment (Homebrew and many
Linux Pythons refuse a bare `pip install`):
    python3 -m venv .venv
    .venv/bin/python -m pip install -r scripts/setup/requirements-obs.txt
    .venv/bin/python scripts/setup/test_obs_websocket.py

With that venv activated, `make test-obs` runs the same script. On Windows the
interpreter is `.venv\\Scripts\\python.exe`.

Connection settings come from OBS_WEBSOCKET_HOST, OBS_WEBSOCKET_PORT and
OBS_WEBSOCKET_PASSWORD (see .env.example): the environment first, then the
repo-root .env for anything the environment does not set.

Prints OBS version, current scene, and the scene list. Exits non-zero on
failure so it can drop into healthcheck.sh later.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

try:
    import obsws_python as obs
except ImportError:
    print(
        "ERROR: install OBS dependencies first  "
        f"({sys.executable} -m pip install -r scripts/setup/requirements-obs.txt)",
        file=sys.stderr,
    )
    sys.exit(2)

# obsws-python logs a full traceback for a refused connection or a failed
# request; this script reports those as a single line instead.
logging.getLogger("obsws_python").setLevel(logging.CRITICAL)

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_env_file(path: Path) -> None:
    """Export KEY=VALUE lines from `path`; variables already in the environment win."""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def main() -> int:
    if ENV_FILE.exists():
        load_env_file(ENV_FILE)

    host = os.environ.get("OBS_WEBSOCKET_HOST", "127.0.0.1")
    port = int(os.environ.get("OBS_WEBSOCKET_PORT", "4455"))
    password = os.environ.get("OBS_WEBSOCKET_PASSWORD", "")

    print(f"connecting to ws://{host}:{port} ...")
    try:
        client = obs.ReqClient(host=host, port=port, password=password, timeout=5)
    except Exception as e:
        print(f"FAILED to connect: {e}", file=sys.stderr)
        return 1

    try:
        version = client.get_version()
        scene = client.get_current_program_scene()
        scenes = client.get_scene_list()

        print(f"  OBS version    : {version.obs_version}")
        print(f"  WS version     : {version.obs_web_socket_version}")
        print(f"  current scene  : {scene.current_program_scene_name}")
        print(f"  total scenes   : {len(scenes.scenes)}")
        for item in scenes.scenes:
            print(f"    - {item['sceneName']}")
        return 0
    except Exception as e:
        print(f"FAILED to query OBS: {e}", file=sys.stderr)
        return 1
    finally:
        client.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
