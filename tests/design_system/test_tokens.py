"""tokens.yaml is evidence-first: its shape is fixed, nothing claims approval it does not have, every blocked
default points at a real owner decision, and every contrast number recomputes from the values."""
from __future__ import annotations

import re

import pytest

from helpers import THEMES, contrast, is_color, load

T = load()
REQUIRED_CATEGORIES = ("color", "type", "space", "radius", "shadow", "motion")
REQUIRED_COLORS = ("brand.primary", "brand.accent", "surface.base", "text.primary", "text.muted",
                   "surface.raised", "border.default", "border.input", "focus.ring", "status.danger")
DECISIONS = set(T["decisions"])


def _walk(node, path=()):
    """Yield (path, dict) for every mapping in the tree."""
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, path + (str(key),))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, path + (str(index),))


def test_the_file_is_drafted_and_approval_is_never_implied():
    assert T["schema_version"] == 1
    assert T["status"] == "drafted" and T["review"] == "awaiting owner review"
    for path, node in _walk(T):
        status = node.get("status") if isinstance(node.get("status"), str) else None
        if status == "approved":
            assert node.get("approved_by") and node.get("approved_on"), \
                f"{'.'.join(path)} is approved without approved_by and approved_on"
        if status:
            assert status in ("drafted", "approved", "deprecated"), f"{'.'.join(path)}: unknown status {status!r}"


def test_required_categories_and_semantic_tokens_exist():
    for category in REQUIRED_CATEGORIES:
        assert T[category], f"category {category} is empty"
    missing = [name for name in REQUIRED_COLORS if name not in T["color"]]
    assert not missing, f"missing semantic color tokens: {missing}"


def test_every_color_token_is_complete_and_valid():
    for name, token in T["color"].items():
        assert token.get("description"), f"{name}: no description"
        proposed = token["proposed"]
        if proposed is None:
            assert token.get("blocked_by") in DECISIONS, f"{name}: a null default needs blocked_by naming a decision"
        else:
            assert set(proposed) <= set(THEMES), f"{name}: proposed themes {sorted(proposed)}"
            assert proposed, f"{name}: empty proposed"
            for theme, value in proposed.items():
                assert is_color(value), f"{name}.{theme}: not a color: {value!r}"
        for consumer, entry in token["observed"].items():
            assert consumer in T["consumers"], f"{name}: observed consumer {consumer!r} is not declared"
            assert entry["source"] in T["sources"], f"{name}.{consumer}: unknown source {entry['source']!r}"
            themes = [t for t in THEMES if t in entry]
            assert themes, f"{name}.{consumer}: no light or dark observation"
            for theme in themes:
                assert is_color(entry[theme]["value"]), f"{name}.{consumer}.{theme}: {entry[theme]['value']!r}"
                assert entry[theme]["raw"], f"{name}.{consumer}.{theme}: no raw source text"


def test_blocked_by_always_names_a_real_decision_and_decisions_block_something():
    for path, node in _walk(T):
        if "blocked_by" in node:
            assert node["blocked_by"] in DECISIONS, f"{'.'.join(path)}: {node['blocked_by']!r}"
    for decision_id, decision in T["decisions"].items():
        assert decision["question"].endswith("?") and decision["blocks"], decision_id


def test_sources_are_declared_and_revision_pinned_when_external():
    for source_id, source in T["sources"].items():
        assert source["repo"] and source["path"], source_id
        if source["repo"] != "hybrid-creator-platform":
            assert re.fullmatch(r"main@[0-9a-f]{7}", source["revision"]), f"{source_id}: pin an external revision"


def test_the_scales_are_well_formed():
    space = T["space"]
    assert space["unit"]["proposed"] == "0.25rem"
    steps = space["scale"]["proposed"]
    assert steps == sorted(set(steps)) and all(isinstance(s, int) and s > 0 for s in steps)
    durations = T["motion"]["duration"]["proposed"]
    ms = {k: float(v[:-2]) for k, v in durations.items()}
    assert ms["fast"] < ms["base"] < ms["slow"]
    assert re.fullmatch(r"[0-9.]+rem", T["radius"]["base"]["proposed"])
    sizes = [float(v[:-3]) for v in T["type"]["size"]["proposed"].values()]
    assert sizes == sorted(sizes), "type sizes must ascend"


def _theme_value(token: str, theme: str):
    proposed = T["color"][token]["proposed"]
    return None if proposed is None else proposed.get(theme)


def _computed():
    for pair in T["contrast"]["pairs"]:
        for theme in THEMES:
            fg, bg = _theme_value(pair["fg"], theme), _theme_value(pair["bg"], theme)
            if fg and bg:
                yield pair, theme, round(contrast(fg, bg), 2)


def test_every_contrast_pair_passes_or_is_a_recorded_known_failure():
    failures = {(f["pair"], f["theme"]): f for f in T["contrast"]["known_failures"]}
    seen = set()
    for pair, theme, ratio in _computed():
        key = (pair["id"], theme)
        if ratio >= pair["min"]:
            assert key not in failures, f"{key} passes at {ratio} but is listed as a failure: remove it"
        else:
            assert key in failures, f"{key} fails AA ({ratio} < {pair['min']}) and is not a known failure"
            assert failures[key]["ratio"] == pytest.approx(ratio, abs=0.011), f"{key}: recorded ratio is stale"
            seen.add(key)
    assert seen == set(failures), f"known failures with no matching pair: {sorted(set(failures) - seen)}"
    for failure in failures.values():
        assert failure["decision"] in DECISIONS


def test_observed_pairs_recompute_and_only_failures_are_recorded():
    for pair in T["contrast"]["observed_pairs"]:
        ratio = round(contrast(pair["fg"], pair["bg"]), 2)
        assert ratio == pytest.approx(pair["ratio"], abs=0.011), f"{pair['id']}: recorded {pair['ratio']}, computed {ratio}"
        assert ratio < pair["min"], f"{pair['id']} passes: this list records failures"


def test_contrast_helper_matches_the_wcag_reference_values():
    assert contrast("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast("#777777", "#ffffff") == pytest.approx(4.48, abs=0.01)  # the well-known just-failing grey
    assert contrast("hsl(0 0% 100%)", "#ffffff") == pytest.approx(1.0)
