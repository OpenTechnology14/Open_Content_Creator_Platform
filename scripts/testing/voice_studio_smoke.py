"""Render an off-air P-066 sample with real installed dependencies; never approve or play it."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/automation-control"))

from voice_studio.studio import Request, Studio  # noqa: E402


async def run(model: str) -> dict:
    library = Path(tempfile.mkdtemp(prefix="hcp-p066-smoke-"))
    studio = Studio(ROOT, library, ROOT / "configs/local/voice-studio.yaml")
    await studio.start()
    try:
        result = await studio.handle(
            Request(
                action="create",
                persona_id="nova-builder",
                model=model,
                phrases=[{"reaction": "victory", "text": "A good block day."}],
            )
        )
        ident = result["revision_id"]
        await studio.handle(Request(action="preview", revision_id=ident, generate=bool(model)))
        await studio.task
        revision = studio.revision(ident)
        report = {
            "library": str(library),
            "revision": ident,
            "status": revision["status"],
            "origin": revision["phrase_origin"],
            "elapsed_seconds": revision["elapsed_seconds"],
            "assets": len(revision["assets"]),
            "durations": [a["duration_seconds"] for a in revision["assets"]],
            "error": revision["error"],
            "approved": False,
            "played": False,
        }
        if revision["status"] != "ready":
            raise RuntimeError(json.dumps(report))
        return report
    finally:
        await studio.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", default="", help="Optional installed Ollama model; blank renders a fixed phrase"
    )
    args = parser.parse_args()
    sys.stdout.write(json.dumps(asyncio.run(run(args.model)), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
