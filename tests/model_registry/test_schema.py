"""Offline tests for the model-registry schema/validation (P-018)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "modules" / "model-registry"))

from model_registry.schema import ModelEntry, is_distributable, validate_entry  # noqa: E402


def _entry(**overrides) -> ModelEntry:
    base = dict(
        name="sdxl-base-1.0",
        kind="checkpoint",
        version="1.0",
        sha256="a" * 64,
        size_bytes=1024,
        source_url="https://example.com/model.safetensors",
        license="OpenRAIL-M",
    )
    base.update(overrides)
    return ModelEntry(**base)


# ── validate_entry ─────────────────────────────────────────────────────

def test_well_formed_entry_has_no_problems():
    assert validate_entry(_entry()) == []


def test_missing_required_field_is_flagged():
    e = _entry(license="")
    problems = validate_entry(e)
    assert any("license" in p for p in problems)


def test_invalid_kind_is_flagged():
    e = _entry(kind="not-a-real-kind")
    problems = validate_entry(e)
    assert any("kind" in p for p in problems)


def test_short_sha256_is_flagged():
    e = _entry(sha256="deadbeef")
    problems = validate_entry(e)
    assert any("sha256" in p for p in problems)


def test_non_hex_sha256_is_flagged():
    e = _entry(sha256="z" * 64)
    problems = validate_entry(e)
    assert any("sha256" in p for p in problems)


def test_zero_size_is_flagged():
    e = _entry(size_bytes=0)
    problems = validate_entry(e)
    assert any("size_bytes" in p for p in problems)


def test_negative_size_is_flagged():
    e = _entry(size_bytes=-5)
    problems = validate_entry(e)
    assert any("size_bytes" in p for p in problems)


def test_malformed_corpus_manifest_hash_is_flagged():
    e = _entry(kind="adapter", corpus_manifest_sha256="too-short")
    problems = validate_entry(e)
    assert any("corpus_manifest_sha256" in p for p in problems)


def test_well_formed_corpus_manifest_hash_is_not_flagged():
    e = _entry(kind="adapter", corpus_manifest_sha256="b" * 64)
    problems = validate_entry(e)
    assert not any("corpus_manifest_sha256" in p for p in problems)


# ── is_distributable ──────────────────────────────────────────────────

def test_open_license_checkpoint_is_distributable():
    assert is_distributable(_entry(license="MIT")) is True


def test_empty_license_is_not_distributable():
    assert is_distributable(_entry(license="")) is False


def test_proprietary_license_is_not_distributable():
    assert is_distributable(_entry(license="Proprietary — internal use only")) is False


def test_non_commercial_license_is_not_distributable():
    assert is_distributable(_entry(license="CC-BY-NC-4.0 (non-commercial)")) is False


def test_adapter_without_corpus_manifest_is_not_distributable():
    """The exact gap P-018 was written to close: nature-generation/
    cityscape-generation's adapter configs required this field but nothing
    enforced its presence."""
    e = _entry(kind="adapter", license="CC-BY-4.0", corpus_manifest_sha256=None)
    assert is_distributable(e) is False


def test_adapter_with_corpus_manifest_and_open_license_is_distributable():
    e = _entry(kind="adapter", license="CC-BY-4.0", corpus_manifest_sha256="c" * 64)
    assert is_distributable(e) is True


def test_checkpoint_does_not_need_corpus_manifest():
    """Only adapters carry the corpus-manifest requirement — a base
    checkpoint trained by a third party has no corpus manifest to pin."""
    e = _entry(kind="checkpoint", license="MIT", corpus_manifest_sha256=None)
    assert is_distributable(e) is True


# ── round-trip ────────────────────────────────────────────────────────

def test_to_dict_from_dict_round_trip():
    original = _entry(kind="adapter", corpus_manifest_sha256="e" * 64, requires_controlnet=["lineart"])
    restored = ModelEntry.from_dict(original.to_dict())
    assert restored == original


def test_from_dict_ignores_unknown_keys():
    """Registry files evolve; an unrecognized key (a typo, or a field from
    a newer schema version) should not crash the loader."""
    data = _entry().to_dict()
    data["some_future_field"] = "ignored"
    ModelEntry.from_dict(data)  # does not raise
