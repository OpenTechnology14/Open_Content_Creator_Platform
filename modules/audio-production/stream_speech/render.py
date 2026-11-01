"""Bounded JSON speech-file rendering and playback entry point for local orchestrators."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .native import NativeSpeechAdapter


async def run(action: str, request: dict) -> dict:
    """Render without playback, or play a workstation-owned file explicitly."""
    adapter = NativeSpeechAdapter()
    try:
        if action == "render":
            duration = await adapter.synthesize(
                request["text"], request.get("voice"), Path(request["output"])
            )
            return {"duration_seconds": duration}
        await adapter.play(Path(request["path"]))
        return {"finished": True}
    finally:
        await adapter.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["render", "play"])
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384:
            raise ValueError("audio request exceeds limit")
        sys.stdout.write(json.dumps(asyncio.run(run(args.action, json.loads(raw)))) + "\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"Native speech failed ({type(exc).__name__}); check installed voice\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
