"""Offline structural checks for sports-analytics (P-040).

No OpenCV/MediaPipe/YOLO/camera required. Two things checked:

1. `calibration.json` — `golf-tracer/README.md` used to describe it as an
   actively-consumed pixel-to-metre mapping ("Re-calibrate whenever the
   camera is bumped... produces a tracer that... measures wrong"), but no
   `.py` file in this module reads it at all; `tracer.py`'s Kalman filter
   and polynomial fit operate entirely in pixel space. This is the
   tripwire: if calibration.json is ever wired in for real, this test
   should start failing and prompt updating the doc's disclosure note
   (and itself) rather than the two silently drifting apart again.

2. The Rust <-> Python contract between `apps/creator-extend/src-tauri/
   src/posture.rs` (Tauri command) and `pose-estimation/posture_screen.py`
   (the script it shells out to) — the CLI flags posture.rs passes must
   be flags posture_screen.py's argparse actually defines, cross-checked
   without needing a Rust toolchain or a real Tauri build.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "modules" / "sports-analytics"
CALIBRATION_JSON = MODULE / "golf-tracer" / "calibration.json"
GOLF_TRACER_README = MODULE / "golf-tracer" / "README.md"
POSTURE_RS = REPO / "apps" / "creator-extend" / "src-tauri" / "src" / "posture.rs"
POSTURE_PY = MODULE / "pose-estimation" / "posture_screen.py"


def _module_py_files() -> list[Path]:
    return sorted(MODULE.rglob("*.py"))


def test_calibration_json_parses() -> None:
    doc = json.loads(CALIBRATION_JSON.read_text(encoding="utf-8"))
    assert "camera_matrix" in doc
    assert "ground_plane" in doc


def test_calibration_json_is_not_yet_read_by_any_module_code() -> None:
    """Tripwire, not a requirement: this documents the current true state.
    If someone wires calibration.json into tracer.py/replay.py, this test
    starts failing — that's the point. Update golf-tracer/README.md's
    disclosure note (it currently says 'template only, not read by any
    code yet') and this test together, not just one of them."""
    # Checked by literal filename, not the word "calibration" — tracer.py's
    # own docstring mentions calibration in prose ("Real-world calibration
    # ... live in sibling modules") without reading the file, and a
    # substring match on the word alone would false-positive on that.
    referencing = [
        f for f in _module_py_files()
        if "calibration.json" in f.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not referencing, (
        f"calibration.json is now referenced by {[f.name for f in referencing]} — "
        f"update golf-tracer/README.md's 'template only, not read by any code yet' "
        f"disclosure (and this test, which exists specifically to catch this)"
    )


def test_readme_disclosure_note_is_present() -> None:
    body = GOLF_TRACER_README.read_text(encoding="utf-8")
    assert "not read by any code yet" in body or "not consumed by" in body, (
        "golf-tracer/README.md's disclosure that calibration.json isn't wired in "
        "yet seems to have been removed — was it actually wired in? If so this "
        "test and test_calibration_json_is_not_yet_read_by_any_module_code should "
        "both be updated together, not just this one"
    )


# ── posture.rs <-> posture_screen.py contract ─────────────────────────

def _rust_cli_flags() -> set[str]:
    body = POSTURE_RS.read_text(encoding="utf-8")
    return set(re.findall(r'\.arg\("(--[a-z-]+)"\)', body))


def _python_argparse_flags() -> set[str]:
    body = POSTURE_PY.read_text(encoding="utf-8")
    return set(re.findall(r'add_argument\("(--[a-z-]+)"', body))


def test_posture_rs_only_passes_flags_posture_screen_py_actually_defines() -> None:
    """A flag posture.rs passes that argparse doesn't recognize would make
    every posture-screen call in the desktop app fail with a usage error —
    this is the offline equivalent of actually running the Tauri command."""
    rust_flags = _rust_cli_flags()
    python_flags = _python_argparse_flags()
    assert rust_flags, "found no .arg(\"--x\") calls in posture.rs — check the regex/path"
    assert python_flags, "found no add_argument(\"--x\" calls in posture_screen.py — check the regex/path"

    unknown = rust_flags - python_flags
    assert not unknown, (
        f"posture.rs passes flag(s) posture_screen.py's argparse doesn't define: {unknown}"
    )


def test_posture_rs_view_values_match_posture_screen_py_choices() -> None:
    """posture.rs validates `view` against a hardcoded front/side/back list
    before ever shelling out — if posture_screen.py's argparse `choices`
    ever changes, the two independently-maintained lists could silently
    diverge and one side would reject a value the other accepts."""
    rust_body = POSTURE_RS.read_text(encoding="utf-8")
    rust_views = set(re.findall(r'"(front|side|back)"', rust_body))

    python_body = POSTURE_PY.read_text(encoding="utf-8")
    choices_match = re.search(r'--view.*?choices=\[([^\]]+)\]', python_body, re.DOTALL)
    assert choices_match, "could not find --view's choices=[...] in posture_screen.py"
    python_views = set(re.findall(r'"(\w+)"', choices_match.group(1)))

    assert rust_views == python_views, (
        f"posture.rs validates against {rust_views} but posture_screen.py accepts "
        f"{python_views} — a view value valid on one side could be rejected on the other"
    )
