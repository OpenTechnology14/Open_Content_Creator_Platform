"""Every observed value in tokens.yaml names its source and the exact text it was read from.

Sources inside this repository are re-read on every run. Sources in sibling repositories are re-read when
their checkout is supplied through the environment (the marketing crosswalk uses the same variables), at the
pinned revision, so a sibling change never fails this repository's build by surprise.
"""
from __future__ import annotations

import collections
import os
import re
import subprocess

import pytest

from helpers import REPO, load

T = load()
SIBLING_ENV = {
    "OpenTechnologyApp": "OPENTECHAPP_REPO_PATH",
    "OpenTechnologyBlog": "OTBLOG_REPO_PATH",
    "MyFeed": "MYFEED_REPO_PATH",
    "Job-Hunter": "JOB_HUNTER_REPO_PATH",
}


def _raws(node, source=None):
    """Yield (source_id, raw) for every `raw` string beneath a mapping that names a declared source."""
    if isinstance(node, dict):
        if isinstance(node.get("source"), str):
            source = node["source"]
        raw = node.get("raw")
        if source in T["sources"]:
            if isinstance(raw, str):
                yield source, raw
            elif isinstance(raw, list):
                for item in raw:
                    yield source, item
        for value in node.values():
            yield from _raws(value, source)
    elif isinstance(node, list):
        for value in node:
            yield from _raws(value, source)


OBSERVATIONS = collections.defaultdict(set)
for _source, _raw in _raws(T):
    OBSERVATIONS[_source].add(_raw)

IN_REPO = sorted(s for s, v in T["sources"].items() if v["repo"] == "hybrid-creator-platform")
EXTERNAL = sorted(s for s, v in T["sources"].items() if v["repo"] != "hybrid-creator-platform")


def test_every_declared_source_is_used_and_every_observation_names_a_declared_source():
    unused = sorted(set(T["sources"]) - set(OBSERVATIONS))
    assert not unused, f"declared but never observed (delete or use): {unused}"


def test_brand_marks_are_read_from_their_files():
    for name, mark in T["brand_marks"].items():
        text = (REPO / mark["file"]).read_text(encoding="utf-8")
        for raw in mark["raw"]:
            assert raw in text, f"{name}: {raw!r} is not in {mark['file']}"


@pytest.mark.parametrize("source_id", IN_REPO)
def test_in_repo_observations_still_exist(source_id):
    text = (REPO / T["sources"][source_id]["path"]).read_text(encoding="utf-8")
    missing = sorted(raw for raw in OBSERVATIONS[source_id] if raw not in text)
    assert not missing, f"{source_id}: no longer present in {T['sources'][source_id]['path']}: {missing}"


@pytest.mark.parametrize("source_id", EXTERNAL)
def test_sibling_observations_still_exist_at_the_pinned_revision(source_id):
    source = T["sources"][source_id]
    variable = SIBLING_ENV[source["repo"]]
    checkout = os.getenv(variable)
    if not checkout:
        pytest.skip(f"set ${variable} to a {source['repo']} checkout to re-read {source['path']}")
    sha = source["revision"].split("@", 1)[1]
    shown = subprocess.run(["git", "-C", checkout, "show", f"{sha}:{source['path']}"],
                           capture_output=True, text=True)
    if shown.returncode != 0:
        pytest.skip(f"{source['repo']} checkout has no revision {sha}: fetch it to verify")
    missing = sorted(raw for raw in OBSERVATIONS[source_id] if raw not in shown.stdout)
    assert not missing, f"{source_id}@{sha}: not found in {source['path']}: {missing}"


def _app_files():
    names = subprocess.run(["git", "ls-files", "apps"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    return [REPO / n for n in names if n.endswith((".svelte", ".css", ".html")) and "node_modules" not in n]


def _count(pattern: str) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for path in _app_files():
        for match in re.finditer(pattern, path.read_text(encoding="utf-8")):
            counts[match.group(1).strip()] += 1
    return counts


def test_recorded_desktop_radius_counts_match_the_apps():
    actual = _count(r"border-radius\s*:\s*([^;}]+)")
    for value, recorded in T["radius"]["observed_desktop"]["values"].items():
        assert actual[value] == recorded, f"border-radius: {value} recorded {recorded}, found {actual[value]}"


def test_recorded_off_grid_gaps_match_the_apps():
    actual = _count(r"\bgap\s*:\s*([^;}]+)")
    for value, recorded in T["space"]["observed_off_grid"]["values"].items():
        assert actual[value] == recorded, f"gap: {value} recorded {recorded}, found {actual[value]}"


def test_the_absence_claims_about_the_desktop_apps_hold():
    """The tokens file says the apps declare no shadow, no reduced-motion handling and define no custom properties."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in _app_files())
    assert "box-shadow" not in text
    assert "prefers-reduced-motion" not in text
    assert not re.search(r"(^|[\s{;])--[a-z0-9-]+\s*:", text), "a desktop app now defines a custom property: update tokens.yaml"
