"""Offline tests for nature-generation's Tier 0 preset loading (P-041).

Imports via tests/nature_generation/_load.py, not a bare `sys.path.insert
+ from grading import ...` — see that file's docstring for why: nature and
cityscape both have a submodule literally named `grading`, and the bare
pattern silently reuses whichever one's `sys.modules["grading"]` entry was
cached first if both modules' tests run in the same pytest session.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.nature_generation._load import presets, tone

apply_preset = presets.apply_preset
load_preset = presets.load_preset

# The exact example from grading/README.md's "Presets" section.
README_PRESET_YAML = """
preset: overcast-lift
pairs_with: nature-overcast-v1
vibrance: 0.25
exposure: 0.3
white_balance: {temp: -200, tint: 4}
curves:
  rgb: [[0, 8], [64, 72], [192, 200], [255, 250]]
"""


def test_load_preset_requires_preset_key(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("vibrance: 0.5\n")
    with pytest.raises(ValueError, match="preset"):
        load_preset(bad)


def test_load_and_apply_readme_example_preset(tmp_path):
    """The exact preset documented in grading/README.md should load and
    apply without error — the offline equivalent of confirming the doc's
    own example is actually valid input to the code it documents."""
    preset_file = tmp_path / "overcast-lift.yaml"
    preset_file.write_text(README_PRESET_YAML)

    preset = load_preset(preset_file)
    assert preset["preset"] == "overcast-lift"
    assert preset["pairs_with"] == "nature-overcast-v1"

    image = np.full((4, 4, 3), 0.5, dtype=np.float32)
    result = apply_preset(image, preset)
    assert result.shape == image.shape
    assert not np.array_equal(result, image)  # the preset should change something


def test_apply_preset_with_no_operations_is_identity():
    image = np.random.default_rng(0).random((3, 3, 3)).astype(np.float32)
    result = apply_preset(image, {"preset": "noop"})
    np.testing.assert_allclose(result, image)


def test_apply_preset_order_curves_applied_last():
    """Regression: curves are documented as "where a look actually lives"
    — applying them before other tonal ops would make their effect get
    partially undone by exposure/vibrance afterward. Verify curves is the
    final operation by checking a curve-only vs curve-plus-exposure preset
    against manually composing the same two operations in that order."""
    image = np.full((2, 2, 3), 0.4, dtype=np.float32)
    curve_points = [[0, 0], [102, 150], [255, 255]]  # brightens midtones
    preset = {"preset": "test", "exposure": 0.5, "curves": {"rgb": curve_points}}

    result = apply_preset(image, preset)
    expected = tone.apply_curves(tone.exposure(image, 0.5), curve_points)
    np.testing.assert_allclose(result, expected, atol=1e-5)
