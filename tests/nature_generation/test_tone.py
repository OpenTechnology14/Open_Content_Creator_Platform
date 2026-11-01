"""Offline tests for nature-generation's Tier 0 tone operations (P-041).

Pure numpy, no image files, no GPU, no ComfyUI — matching grading/README.md's
own framing: "the only tier whose correctness a test can assert rather
than an eye." Each test checks a documented mathematical property
(identity at the neutral parameter, the vibrance-vs-saturation weighting
difference, colour-space correctness) rather than "looks right" on a
sample photo, which nobody here can judge visually anyway.
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.nature_generation._load import tone


def _mid_grey(shape=(4, 4, 3)) -> np.ndarray:
    return np.full(shape, 0.5, dtype=np.float32)


def _random_image(shape=(8, 8, 3), seed=0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.random(shape).astype(np.float32)


# ── sRGB <-> linear round-trip ──────────────────────────────────────────

def test_srgb_linear_round_trip():
    img = _random_image()
    round_tripped = tone.linear_to_srgb(tone.srgb_to_linear(img))
    np.testing.assert_allclose(round_tripped, img, atol=1e-5)


def test_srgb_to_linear_black_and_white_are_fixed_points():
    black = np.zeros((2, 2, 3), dtype=np.float32)
    white = np.ones((2, 2, 3), dtype=np.float32)
    np.testing.assert_allclose(tone.srgb_to_linear(black), black, atol=1e-6)
    np.testing.assert_allclose(tone.srgb_to_linear(white), white, atol=1e-6)


# ── LAB round-trip ───────────────────────────────────────────────────────

def test_lab_round_trip():
    img = _random_image(seed=1)
    linear = tone.srgb_to_linear(img)
    round_tripped = tone.lab_to_linear_rgb(tone.linear_rgb_to_lab(linear))
    np.testing.assert_allclose(round_tripped, linear, atol=1e-4)


def test_grey_has_zero_chroma_in_lab():
    """A neutral grey pixel should have a=b=0 in LAB by definition."""
    grey = np.full((1, 1, 3), 0.5, dtype=np.float32)
    lab = tone.linear_rgb_to_lab(tone.srgb_to_linear(grey))
    np.testing.assert_allclose(lab[..., 1], 0.0, atol=1e-4)
    np.testing.assert_allclose(lab[..., 2], 0.0, atol=1e-4)


# ── exposure ─────────────────────────────────────────────────────────────

def test_exposure_zero_stops_is_identity():
    img = _random_image(seed=2)
    np.testing.assert_allclose(tone.exposure(img, 0.0), img, atol=1e-5)


def test_exposure_one_stop_doubles_linear_light():
    img = _mid_grey()
    linear_before = tone.srgb_to_linear(img)
    result = tone.exposure(img, 1.0)
    linear_after = tone.srgb_to_linear(result)
    np.testing.assert_allclose(linear_after, linear_before * 2.0, atol=1e-4)


def test_exposure_negative_stops_darkens():
    img = _mid_grey()
    result = tone.exposure(img, -1.0)
    assert np.all(result < img)


# ── white balance ────────────────────────────────────────────────────────

def test_white_balance_zero_is_identity():
    img = _random_image(seed=3)
    result = tone.white_balance(img, temp=0.0, tint=0.0)
    np.testing.assert_allclose(result, img, atol=1e-5)


def test_white_balance_positive_temp_warms():
    """Positive temp = warmer = more red, less blue."""
    grey = _mid_grey()
    result = tone.white_balance(grey, temp=500.0, tint=0.0)
    assert np.all(result[..., 0] > grey[..., 0])  # red increased
    assert np.all(result[..., 2] < grey[..., 2])  # blue decreased


# ── saturation vs vibrance ───────────────────────────────────────────────

def test_saturation_scale_one_is_identity():
    img = _random_image(seed=4)
    result = tone.saturation(img, 1.0)
    np.testing.assert_allclose(result, img, atol=1e-4)


def test_saturation_zero_desaturates_to_grey():
    img = _random_image(seed=5)
    result = tone.saturation(img, 0.0)
    lab = tone.linear_rgb_to_lab(tone.srgb_to_linear(result))
    np.testing.assert_allclose(lab[..., 1], 0.0, atol=1e-3)
    np.testing.assert_allclose(lab[..., 2], 0.0, atol=1e-3)


def test_saturation_scales_saturated_and_muted_pixels_equally():
    """Regression against the exact bug grading/README.md warns about:
    plain saturation should push an already-saturated pixel and a muted
    pixel by the *same relative amount* — that's what makes a saturated
    sky go neon while muted foliage barely moves in absolute terms, even
    though the relative boost is identical.

    Both test pixels are moderate (not near a gamut-primary vivid colour)
    so scale=1.3 doesn't clip either one at the sRGB boundary — a strongly
    saturated pixel clipping is a real optical effect, not a bug, but
    would contaminate this assertion by capping its chroma growth for a
    reason unrelated to the property being checked here.
    """
    moderately_saturated = np.array([[[0.65, 0.35, 0.4]]], dtype=np.float32)
    muted = np.array([[[0.55, 0.45, 0.45]]], dtype=np.float32)
    scale = 1.3

    def chroma(px):
        lab = tone.linear_rgb_to_lab(tone.srgb_to_linear(px))
        return float(np.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)[0, 0])

    c_sat_before, c_muted_before = chroma(moderately_saturated), chroma(muted)
    c_sat_after = chroma(tone.saturation(moderately_saturated, scale))
    c_muted_after = chroma(tone.saturation(muted, scale))

    ratio_sat = c_sat_after / c_sat_before
    ratio_muted = c_muted_after / c_muted_before
    np.testing.assert_allclose(ratio_sat, scale, atol=1e-2)
    np.testing.assert_allclose(ratio_muted, scale, atol=1e-2)
    np.testing.assert_allclose(ratio_sat, ratio_muted, atol=1e-3)


def test_vibrance_boosts_muted_pixels_more_than_saturated_ones():
    """The documented opposite of saturation()'s behaviour: vibrance's
    relative boost should be larger for a muted pixel than a saturated one.

    Uses gentle pixel values and a small `amount` — verified empirically
    (not just assumed) to stay clear of sRGB gamut clipping under a
    mutation that deletes vibrance's weighting entirely: two earlier,
    more aggressive versions of this test (a near-primary vivid pixel at
    amount=0.5, then a "moderate" pixel still at amount=0.5) both let the
    saturated-pixel's growth clip at the gamut boundary regardless of the
    weighting bug, which silently passed even with the weighting removed
    — the exact bug this test exists to catch. Confirmed by hand that the
    unweighted mutation produces identical ratios (0.2/0.2) here, and the
    real weighted code produces distinguishably different ones."""
    saturated = np.array([[[0.58, 0.42, 0.45]]], dtype=np.float32)
    muted = np.array([[[0.52, 0.48, 0.49]]], dtype=np.float32)
    amount = 0.2

    def chroma(px):
        lab = tone.linear_rgb_to_lab(tone.srgb_to_linear(px))
        return float(np.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)[0, 0])

    c_sat_before, c_muted_before = chroma(saturated), chroma(muted)
    c_sat_after = chroma(tone.vibrance(saturated, amount))
    c_muted_after = chroma(tone.vibrance(muted, amount))

    ratio_sat = (c_sat_after - c_sat_before) / c_sat_before
    ratio_muted = (c_muted_after - c_muted_before) / c_muted_before
    assert ratio_muted > ratio_sat, (
        f"vibrance should boost the muted pixel proportionally more than the "
        f"saturated one (muted ratio {ratio_muted}, saturated ratio {ratio_sat})"
    )


def test_vibrance_zero_amount_is_identity():
    img = _random_image(seed=6)
    result = tone.vibrance(img, 0.0)
    np.testing.assert_allclose(result, img, atol=1e-4)


# ── contrast ──────────────────────────────────────────────────────────────

def test_contrast_zero_is_identity():
    img = _random_image(seed=7)
    np.testing.assert_allclose(tone.contrast(img, 0.0), img, atol=1e-5)


def test_contrast_pivot_at_mid_grey_is_fixed():
    grey = np.full((2, 2, 3), 0.5, dtype=np.float32)
    result = tone.contrast(grey, 0.5)
    np.testing.assert_allclose(result, grey, atol=1e-5)


def test_contrast_positive_amount_darkens_shadows_and_lifts_highlights():
    dark = np.full((1, 1, 3), 0.25, dtype=np.float32)
    light = np.full((1, 1, 3), 0.75, dtype=np.float32)
    dark_result = tone.contrast(dark, 0.5)
    light_result = tone.contrast(light, 0.5)
    assert np.all(dark_result < dark)
    assert np.all(light_result > light)


def test_contrast_endpoints_are_fixed_for_any_amount():
    black = np.zeros((1, 1, 3), dtype=np.float32)
    white = np.ones((1, 1, 3), dtype=np.float32)
    for amount in (-1.0, -0.3, 0.3, 1.0):
        np.testing.assert_allclose(tone.contrast(black, amount), black, atol=1e-6)
        np.testing.assert_allclose(tone.contrast(white, amount), white, atol=1e-6)


# ── curves ────────────────────────────────────────────────────────────────

def test_identity_curve_is_identity():
    img = _random_image(seed=8)
    identity_points = [[0, 0], [128, 128], [255, 255]]
    result = tone.apply_curves(img, identity_points)
    np.testing.assert_allclose(result, img, atol=1e-2)


def test_curve_control_point_is_exact():
    """A pixel exactly at a control point's input should map to exactly
    that control point's output."""
    points = [[0, 8], [64, 72], [192, 200], [255, 250]]
    img = np.full((1, 1, 3), 64.0 / 255.0, dtype=np.float32)
    result = tone.apply_curves(img, points)
    np.testing.assert_allclose(result, 72.0 / 255.0, atol=1e-3)


def test_curve_applies_identically_to_all_channels():
    points = [[0, 0], [128, 200], [255, 255]]
    img = np.array([[[0.1, 0.5, 0.9]]], dtype=np.float32)
    result = tone.apply_curves(img, points)
    expected_r = float(np.interp(0.1, [0, 128 / 255, 1.0], [0, 200 / 255, 1.0]))
    assert abs(float(result[0, 0, 0]) - expected_r) < 1e-3


# ── determinism ───────────────────────────────────────────────────────────

def test_tier0_operations_are_deterministic():
    """grading/README.md's own claim: Tier 0 is "the only tier that is an
    exact function rather than a sample" — applying the same operation
    twice to the same input must give byte-identical output. Checked
    across every operation, not just one, since determinism is a property
    each function has to hold independently (no hidden RNG, no
    time-dependent state)."""
    img = _random_image(seed=42)
    ops = [
        lambda x: tone.vibrance(x, 0.3),
        lambda x: tone.saturation(x, 1.2),
        lambda x: tone.exposure(x, 0.5),
        lambda x: tone.white_balance(x, temp=100, tint=-20),
        lambda x: tone.contrast(x, 0.4),
        lambda x: tone.apply_curves(x, [[0, 10], [128, 140], [255, 245]]),
    ]
    for op in ops:
        first = op(img)
        second = op(img)
        np.testing.assert_array_equal(first, second)
