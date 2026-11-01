"""Serve local JSON-line commands over stdio; no listener, account or cloud dependency."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .studio import Request, Studio

ROOT = Path(__file__).resolve().parents[3]


async def serve(args: argparse.Namespace) -> None:
    args.library.mkdir(parents=True, exist_ok=True)
    # One owner across app/CLI instances. OS releases the lock after a crash.
    with (args.library / "studio.lock").open("a+b") as lock:
        if sys.platform == "win32":
            import msvcrt

            lock.seek(0)
            lock.write(b"0")
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        studio = Studio(ROOT, args.library, args.config)
        await studio.start()
        try:
            while True:
                raw = await asyncio.to_thread(sys.stdin.buffer.readline, 65537)
                if not raw:
                    break
                try:
                    if len(raw) > 65536:
                        raise ValueError("Studio request exceeds 64 KiB")
                    result = await studio.handle(Request.model_validate_json(raw))
                    reply = {"ok": True, "data": result}
                except Exception as exc:
                    reply = {"ok": False, "error": str(exc)[:500]}
                sys.stdout.write(json.dumps(reply) + "\n")
                sys.stdout.flush()
        finally:
            await studio.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/local/voice-studio.yaml")
    parser.add_argument("--library", type=Path, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(serve(args))
        return 0
    except Exception as exc:
        sys.stderr.write(
            f"Voice studio unavailable ({type(exc).__name__}); check setup/library owner\n"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
