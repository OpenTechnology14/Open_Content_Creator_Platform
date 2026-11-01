"""Offline structural checks for audio-production's per-OS routing configs
(P-038).

No audio hardware, no PipeWire/VoiceMeeter/BlackHole install required.
The regression this file exists for: `pipewire.conf`'s own header comment
claims it "creates virtual null-sinks that map to the bus names used in
routing/README.md" — a completeness claim — but it only created 5 of the
6 canonical buses, silently missing MONITOR.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "modules" / "audio-production"
ROUTING_README = MODULE / "routing" / "README.md"
PIPEWIRE_CONF = MODULE / "routing" / "pipewire.conf"
BLACKHOLE_JSON = MODULE / "routing" / "blackhole-loopback.json"
VOICEMEETER_XML = MODULE / "voicemeeter" / "potato-config.xml"


def _canonical_bus_names() -> list[str]:
    """Parse the 'Bus mapping (canonical)' table's first column out of
    routing/README.md."""
    body = ROUTING_README.read_text(encoding="utf-8")
    section = body.split("## Bus mapping (canonical)", 1)[1].split("##", 1)[0]
    rows = [
        line for line in section.splitlines()
        if line.strip().startswith("|") and "---" not in line
    ]
    # First row is the header ("Bus | Source | Destination"); skip it.
    names = []
    for row in rows[1:]:
        cell = row.split("|")[1].strip()
        if cell:
            names.append(cell)
    return names


def test_canonical_bus_table_is_parseable() -> None:
    names = _canonical_bus_names()
    assert names, "found no rows in routing/README.md's canonical bus table"
    assert "MONITOR" in names, "sanity check: MONITOR should be one of the canonical buses"


def test_blackhole_json_parses() -> None:
    json.loads(BLACKHOLE_JSON.read_text(encoding="utf-8"))


def test_voicemeeter_xml_parses() -> None:
    ET.fromstring(VOICEMEETER_XML.read_text(encoding="utf-8"))


def _pipewire_bus_descriptions() -> set[str]:
    body = PIPEWIRE_CONF.read_text(encoding="utf-8")
    return set(re.findall(r'node\.description\s*=\s*"HCP-([A-Z-]+)"', body))


def test_pipewire_conf_creates_every_canonical_bus() -> None:
    """Regression: this file's own header comment claims to map every bus
    name in routing/README.md's canonical table, but only created 5 of 6
    — MONITOR was silently missing."""
    canonical = {name.replace(" ", "-") for name in _canonical_bus_names()}
    actual = _pipewire_bus_descriptions()
    missing = canonical - actual
    assert not missing, (
        f"pipewire.conf's header comment claims to map every bus in "
        f"routing/README.md's canonical table, but is missing: {missing}"
    )


def test_pipewire_conf_has_matching_capture_and_playback_per_bus() -> None:
    """Each loopback module needs both a capture (Sink, so apps can send
    audio into the bus) and playback (Source, so it's selectable as an
    input elsewhere) side — one without the other is a bus nothing can
    actually route through."""
    body = PIPEWIRE_CONF.read_text(encoding="utf-8")
    # Split into individual loopback module blocks by their node.description.
    blocks = re.split(r"(?=node\.description)", body)[1:]
    for block in blocks:
        name_match = re.search(r'node\.description\s*=\s*"([^"]+)"', block)
        name = name_match.group(1) if name_match else "<unknown>"
        assert 'media.class = "Audio/Sink"' in block, f"{name}: missing capture (Sink) side"
        assert 'media.class = "Audio/Source"' in block, f"{name}: missing playback (Source) side"


def test_mac_call_input_never_uses_an_output_only_device() -> None:
    """A call input must capture the host; Built-in Output cannot supply that input."""
    routing = json.loads(BLACKHOLE_JSON.read_text(encoding="utf-8"))["routing"]
    assert "built-in output" not in routing["discord_input"].lower()
    assert routing["discord_input"] != routing["discord_output"]


def test_recording_bus_map_matches_full_mix_and_isolated_tracks() -> None:
    """Prevent conflicting mic/desktop track instructions in the same guide."""
    body = ROUTING_README.read_text(encoding="utf-8")
    section = body.split("## Bus mapping (canonical)", 1)[1].split("##", 1)[0]
    isolated = {"MIC": 2, "GAME": 3, "MUSIC": 6, "AI-VOICE": 4, "CALL-IN": 5}
    destinations = {}
    for line in section.splitlines():
        if line.startswith("|") and "---" not in line:
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            destinations[cells[0]] = cells[2]
    for bus, track in isolated.items():
        tracks = {int(value) for value in re.findall(r"\d+", destinations[bus])}
        assert tracks == {1, track}, f"{bus} must reach full mix 1 and isolated track {track}"
    assert not re.search(r"\d", destinations["MONITOR"]), "Monitor must stay out of recording"
    track_section = body.split("OBS supports six tracks:", 1)[1].split("##", 1)[0]
    assert "| 6 | Music only |" in track_section
