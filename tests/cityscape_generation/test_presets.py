"""Offline tests for cityscape-generation's Tier 0 preset loading (P-041).

See tests/nature_generation/_load.py for why imports go through _load
rather than a bare `sys.path.insert + from grading import ...`.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.cityscape_generation._load import presets

apply_preset = presets.apply_preset
load_preset = presets.load_preset

# The exact example from grading/README.md's "Presets" section.
README_PRESET_YAML = """
preset: night-neon-cool
pairs_with: cityscape-neon-night-v1
lens_distortion: {barrel: -0.02}
vibrance: 0.2
curves:
  rgb: [[0, 4], [48, 40], [200, 210], [255, 252]]
"""


def test_load_preset_requires_preset_key(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("vibrance: 0.5\n")
    with pytest.raises(ValueError, match="preset"):
        load_preset(bad)


def test_load_and_apply_readme_example_preset_minus_auto_perspective(tmp_path):
    """The README's own example uses `perspective: {vertical: auto}`,
    which apply_preset()/geometry.perspective_correction() deliberately
    reject (auto keystone detection is real computer vision, not built
    here — see geometry.py's NotImplementedError). This test uses the
    same example with that one field removed, since it's the only part
    not yet implemented; everything else in the documented preset should
    load and apply cleanly."""
    preset_file = tmp_path / "night-neon-cool.yaml"
    preset_file.write_text(README_PRESET_YAML)

    preset = load_preset(preset_file)
    assert preset["preset"] == "night-neon-cool"

    image = np.full((8, 8, 3), 0.5, dtype=np.float32)
    result = apply_preset(image, preset)
    assert result.shape == image.shape
    assert not np.array_equal(result, image)


def test_apply_preset_auto_perspective_raises_not_implemented(tmp_path):
    """The regression test for the gap above: a preset using the
    documented `perspective: {vertical: auto}` shape should fail loudly,
    not silently ignore the field or crash on a string/float multiply."""
    preset = {
        "preset": "test",
        "perspective": {"vertical": "auto"},
    }
    image = np.full((4, 4, 3), 0.5, dtype=np.float32)
    with pytest.raises(NotImplementedError):
        apply_preset(image, preset)


def test_apply_preset_shadows_highlights_white_balance_raises_not_implemented():
    """Same shape of regression: the documented shadows/highlights split
    white balance isn't implemented — must fail loudly, not silently
    apply a partial or wrong correction."""
    preset = {
        "preset": "test",
        "white_balance": {"shadows": {"temp": -400}, "highlights": {"temp": 150}},
    }
    image = np.full((4, 4, 3), 0.5, dtype=np.float32)
    with pytest.raises(NotImplementedError):
        apply_preset(image, preset)


def test_apply_preset_with_no_operations_is_identity():
    image = np.random.default_rng(0).random((5, 5, 3)).astype(np.float32)
    result = apply_preset(image, {"preset": "noop"})
    np.testing.assert_allclose(result, image)


def test_apply_preset_geometry_runs_before_tone():
    """Regression for the documented order: distortion -> perspective ->
    rotation -> crop -> tone. Compose the same rotate-then-vibrance
    manually and compare."""
    from tests.cityscape_generation._load import geometry, tone

    image = np.random.default_rng(1).random((6, 6, 3)).astype(np.float32)
    preset = {"preset": "test", "rotation": 5.0, "vibrance": 0.2}

    result = apply_preset(image, preset)
    expected = tone.vibrance(geometry.rotate(image, 5.0), 0.2)
    np.testing.assert_allclose(result, expected, atol=1e-5)
