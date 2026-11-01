"""Offline checks for the soundboard starter pack (P-044).

No OBS install needed. `manifest.yaml` is the single source of truth for
what's bundled vs. a placeholder — these tests keep it honest: every
`bundled` entry must have a real, small, license-tagged file on disk, and
every `placeholder` entry must NOT ship a file (that's the whole point of
the copyright line drawn in modules/soundboard/README.md).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SOUNDBOARD = REPO / "modules" / "soundboard"
MANIFEST_PATH = SOUNDBOARD / "sounds" / "manifest.yaml"
MAX_BUNDLED_BYTES = 5 * 1024 * 1024  # CLAUDE.md §10: never commit binaries over 5 MB
ALLOWED_CATEGORIES = {"stinger", "ui", "reaction", "meme"}
ALLOWED_STATUSES = {"bundled", "placeholder"}


def _manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def _sounds() -> list[dict]:
    return _manifest()["sounds"]


def test_manifest_parses_and_has_sounds():
    sounds = _sounds()
    assert isinstance(sounds, list)
    assert len(sounds) > 0


@pytest.mark.parametrize("sound", _sounds(), ids=lambda s: s["slot"])
def test_every_sound_has_required_fields(sound: dict):
    for key in ("name", "slot", "category", "status"):
        assert key in sound, f"{sound.get('slot', sound)} missing required field {key!r}"
    assert sound["category"] in ALLOWED_CATEGORIES, (
        f"{sound['slot']}: unknown category {sound['category']!r}"
    )
    assert sound["status"] in ALLOWED_STATUSES, (
        f"{sound['slot']}: unknown status {sound['status']!r}"
    )


def test_slot_names_are_unique():
    slots = [s["slot"] for s in _sounds()]
    assert len(slots) == len(set(slots)), "duplicate slot name in manifest.yaml"


@pytest.mark.parametrize(
    "sound", [s for s in _sounds() if s["status"] == "bundled"], ids=lambda s: s["slot"]
)
def test_bundled_sound_has_a_real_small_licensed_file(sound: dict):
    assert "file" in sound, f"{sound['slot']}: bundled entry must name a file"
    path = SOUNDBOARD / "sounds" / sound["file"]
    assert path.is_file(), f"{sound['slot']}: {path} does not exist"
    size = path.stat().st_size
    assert 0 < size <= MAX_BUNDLED_BYTES, (
        f"{sound['slot']}: {path} is {size} bytes — expected 0 < size <= {MAX_BUNDLED_BYTES}"
    )
    for key in ("source", "source_url", "license"):
        assert sound.get(key), f"{sound['slot']}: bundled entry missing {key!r}"


@pytest.mark.parametrize(
    "sound", [s for s in _sounds() if s["status"] == "placeholder"], ids=lambda s: s["slot"]
)
def test_placeholder_sound_ships_no_file_and_explains_why(sound: dict):
    """The copyright line this module draws only holds if placeholders never
    silently grow a `file` key — that would be exactly the "ship a copyrighted
    meme clip" mistake README.md says this repo doesn't make."""
    assert "file" not in sound, (
        f"{sound['slot']}: placeholder entries must not ship a file — "
        f"see modules/soundboard/README.md's copyright note"
    )
    assert sound.get("note"), f"{sound['slot']}: placeholder entry missing a note explaining why"


def test_no_stray_audio_files_outside_the_manifest():
    """Every real audio file on disk must be claimed by exactly one bundled
    entry — an unclaimed file is either dead weight or a license nobody
    recorded."""
    on_disk = {
        str(p.relative_to(SOUNDBOARD / "sounds"))
        for p in (SOUNDBOARD / "sounds").rglob("*")
        if p.is_file() and p.suffix in (".ogg", ".wav", ".mp3")
    }
    claimed = {s["file"] for s in _sounds() if s["status"] == "bundled"}
    assert on_disk == claimed, f"on disk but not in manifest: {on_disk - claimed}; " \
        f"in manifest but missing: {claimed - on_disk}"


def test_readme_bundled_count_matches_manifest():
    """README.md states an exact bundled count in prose — regression test so
    the two can't silently drift apart."""
    bundled = sum(1 for s in _sounds() if s["status"] == "bundled")
    readme = (SOUNDBOARD / "README.md").read_text(encoding="utf-8")
    assert f"{bundled} bundled clips" in readme, (
        f"README.md doesn't say '{bundled} bundled clips' — manifest has {bundled} "
        f"bundled entries, update the prose or the manifest"
    )
