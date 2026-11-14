"""Regenerate only the checked schema; roundtrip examples are reviewed fixed fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from .models import schema_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).with_name("wire") / "schema.json"
    expected = json.dumps(schema_bundle(), indent=2, sort_keys=True) + "\n"
    if args.write:
        path.write_text(expected)
    elif path.read_text() != expected:
        raise SystemExit("production schema drift")


if __name__ == "__main__":
    main()
