"""Print a JSON draft lineup; never start an OBS stream or create a scheduled job."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError

from .planner import calendar, load_program

ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/local/stream-programming.yaml"
    )
    parser.add_argument("--start", type=date.fromisoformat, default=None)
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--daily-slots", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    try:
        program = load_program(args.config)
        output = {
            "schema_version": program.schema_version,
            "launch_enabled": False,
            "timezone": program.timezone,
            "episodes": calendar(
                program,
                args.start or datetime.now(ZoneInfo(program.timezone)).date(),
                args.days,
                args.daily_slots,
            ),
        }
        sys.stdout.write(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
        return 0
    except (OSError, ValueError, ValidationError, ZoneInfoNotFoundError) as exc:
        sys.stderr.write(f"Show plan failed: {type(exc).__name__}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
