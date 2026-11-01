"""Command-line entry point for the model registry.

    python3 -m model_registry.cli validate
    python3 -m model_registry.cli checksum /path/to/weight.safetensors
    python3 -m model_registry.cli verify sdxl-base-1.0 /path/to/weight.safetensors
    python3 -m model_registry.cli status

Run from `modules/model-registry/` (or with that directory on `PYTHONPATH`)
so `model_registry` and its sibling `asset_pipeline` import resolve —
`registry.py` handles the second one.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from model_registry.checksum import compute_sha256, verify_local_file
from model_registry.registry import DEFAULT_REGISTRY_PATH, load_registry
from model_registry.schema import is_distributable, validate_entry


def cmd_validate(args: argparse.Namespace) -> int:
    entries = load_registry(args.registry)
    if not entries:
        print(f"{args.registry}: no entries (an empty registry is valid, not an error)")
        return 0

    problems: list[str] = []
    for entry in entries:
        problems.extend(validate_entry(entry))

    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        return 1

    print(f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} — all well-formed")
    return 0


def cmd_checksum(args: argparse.Namespace) -> int:
    print(compute_sha256(args.path))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    entries = load_registry(args.registry)
    match = next((e for e in entries if e.name == args.name), None)
    if match is None:
        print(f"no registry entry named {args.name!r}")
        return 1

    ok = verify_local_file(match, args.path)
    print(f"{'OK' if ok else 'MISMATCH'}: {args.path} against {args.name}")
    return 0 if ok else 1


def cmd_status(args: argparse.Namespace) -> int:
    entries = load_registry(args.registry)
    if not entries:
        print(f"{args.registry}: no entries")
        return 0

    for entry in entries:
        dist = "distributable" if is_distributable(entry) else "NOT distributable"
        problems = validate_entry(entry)
        shape = "well-formed" if not problems else f"{len(problems)} problem(s)"
        print(f"{entry.name} ({entry.kind}, v{entry.version}) — {dist}, {shape}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="model_registry", description=__doc__)
    p.add_argument(
        "--registry", type=Path, default=DEFAULT_REGISTRY_PATH,
        help=f"path to registry.yml (default: {DEFAULT_REGISTRY_PATH})",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="check every entry is well-formed").set_defaults(func=cmd_validate)

    p_checksum = sub.add_parser("checksum", help="compute a local file's SHA-256")
    p_checksum.add_argument("path", type=Path)
    p_checksum.set_defaults(func=cmd_checksum)

    p_verify = sub.add_parser("verify", help="check a local file matches a registry entry's checksum")
    p_verify.add_argument("name", help="registry entry name")
    p_verify.add_argument("path", type=Path)
    p_verify.set_defaults(func=cmd_verify)

    sub.add_parser("status", help="list every entry with its distributability").set_defaults(func=cmd_status)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
