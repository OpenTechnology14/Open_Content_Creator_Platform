"""Offline tests for cityscape-generation's Tier 0 geometry ops (P-041).

No OpenCV, no real photos — geometry.py is hand-rolled numpy (inverse
warp + bilinear sampling), specifically to avoid a heavy new CI
dependency for a single module's Tier 0. That trade-off makes these tests
carry more weight than usual: correctness here rests entirely on the
math and these checks, not on "does it look right", which nobody can
judge in this environment anyway. Every test checks either an exact
mathematical identity (zero-parameter cases, known transforms) or a
property provable without a reference image (shape preservation, a
homography solved from 4 points reproducing exactly those 4 points).
"""

from __future__ import annotations

import numpy as np
import pytest

from tests.cityscape_generation._load import geometry


def _checkerboard(size=16) -> np.ndarray:
    """A simple pattern with real structure (not flat colour), so a warp
    that scrambles pixels is visibly different from identity, not just
    numerically different by float noise."""
    img = np.zeros((size, size, 3), dtype=np.float32)
    for y in range(size):
        for x in range(size):
            if (x // 2 + y // 2) % 2 == 0:
                img[y, x] = 1.0
    return img


# ── lens distortion ──────────────────────────────────────────────────────

def test_lens_distortion_zero_barrel_is_identity():
    img = _checkerboard()
    result = geometry.lens_distortion(img, 0.0)
    np.testing.assert_allclose(result, img)


def test_lens_distortion_preserves_shape():
    img = _checkerboard()
    result = geometry.lens_distortion(img, -0.1)
    assert result.shape == img.shape


def test_lens_distortion_centre_pixel_is_unmoved():
    """The distortion model is r * (1 + barrel * r^2) — at r=0 (image
    centre) the correction is always identity regardless of `barrel`,
    since scaling zero by anything is still zero."""
    img = _checkerboard(size=17)  # odd size gives an exact centre pixel
    cy, cx = 8, 8
    for barrel in (-0.3, -0.1, 0.1, 0.3):
        result = geometry.lens_distortion(img, barrel)
        np.testing.assert_allclose(result[cy, cx], img[cy, cx], atol=1e-5)


# ── perspective correction ───────────────────────────────────────────────

def test_perspective_zero_skew_is_identity():
    img = _checkerboard()
    result = geometry.perspective_correction(img, vertical=0.0, horizontal=0.0)
    np.testing.assert_allclose(result, img)


def test_perspective_preserves_shape():
    img = _checkerboard()
    result = geometry.perspective_correction(img, vertical=0.1)
    assert result.shape == img.shape


def test_perspective_auto_raises_not_implemented():
    img = _checkerboard()
    with pytest.raises(NotImplementedError):
        geometry.perspective_correction(img, vertical="auto")


def test_solve_homography_reproduces_exact_correspondences():
    """The DLT solver underlying perspective correction: given 4 point
    correspondences, the solved homography should map each source point
    to (very close to) its exact destination — this is the actual
    mathematical guarantee a homography from 4 points gives, checked
    directly rather than through the visual result of a full image warp."""
    dst = np.array([[0, 0], [99, 0], [99, 99], [0, 99]], dtype=np.float64)
    src = np.array([[10, 5], [95, 8], [99, 99], [0, 99]], dtype=np.float64)

    h = geometry._solve_homography(dst, src)

    for (dx, dy), (sx, sy) in zip(dst, src):
        pt = h @ np.array([dx, dy, 1.0])
        mapped = pt[:2] / pt[2]
        np.testing.assert_allclose(mapped, [sx, sy], atol=1e-6)


# ── rotation ──────────────────────────────────────────────────────────────

def test_rotate_zero_degrees_is_identity():
    img = _checkerboard()
    result = geometry.rotate(img, 0.0)
    np.testing.assert_allclose(result, img)


def test_rotate_preserves_shape():
    img = _checkerboard()
    result = geometry.rotate(img, 15.0)
    assert result.shape == img.shape


def test_rotate_centre_pixel_is_unmoved():
    img = _checkerboard(size=17)
    cy, cx = 8, 8
    for degrees in (-90.0, 45.0, 180.0):
        result = geometry.rotate(img, degrees)
        np.testing.assert_allclose(result[cy, cx], img[cy, cx], atol=1e-4)


def test_rotate_90_degrees_moves_content_clockwise():
    """Pins down rotate()'s documented direction convention (clockwise
    for positive degrees) against a known case, rather than trusting the
    docstring's claim. This is also the only test in this file that
    actually catches a sign error in the rotation formula — several
    others (centre-pixel-unmoved, 180-twice-round-trip) hold regardless
    of direction and don't."""
    size = 5
    img = np.zeros((size, size, 3), dtype=np.float32)
    img[0, size - 1] = 1.0  # top-right corner

    result = geometry.rotate(img, 90.0)
    brightest = np.unravel_index(np.argmax(result[..., 0]), result[..., 0].shape)
    assert brightest == (size - 1, size - 1), (
        f"expected the top-right corner to move to bottom-right (clockwise) "
        f"under rotate(+90), got {brightest}"
    )


def test_rotate_180_twice_approximately_restores_original():
    """Not an exact round-trip (bilinear resampling loses a little detail
    each pass), but rotating 180 degrees twice should land very close to
    the original — the one rotation angle where every source pixel maps
    to an exact integer destination pixel (no interpolation blur), so this
    is the strongest round-trip check available without a reference image."""
    img = _checkerboard(size=16)
    round_tripped = geometry.rotate(geometry.rotate(img, 180.0), 180.0)
    np.testing.assert_allclose(round_tripped, img, atol=1e-4)


# ── crop ──────────────────────────────────────────────────────────────────

def test_crop_extracts_exact_region():
    img = _checkerboard()
    cropped = geometry.crop(img, top=2, left=3, height=4, width=5)
    assert cropped.shape == (4, 5, 3)
    np.testing.assert_array_equal(cropped, img[2:6, 3:8])


def test_crop_full_image_is_identity():
    img = _checkerboard()
    h, w = img.shape[:2]
    result = geometry.crop(img, top=0, left=0, height=h, width=w)
    np.testing.assert_array_equal(result, img)


# ── apply_geometry ordering ────────────────────────────────────────────────

def test_apply_geometry_runs_distortion_before_perspective_before_rotation_before_crop():
    """Regression for the documented fixed order. Compose the same four
    operations by hand in that order and compare against apply_geometry's
    output for a params dict containing all four."""
    img = _checkerboard(size=20)
    params = {
        "lens_distortion": {"barrel": -0.05},
        "perspective": {"vertical": 0.05},
        "rotation": 3.0,
        "crop": {"top": 1, "left": 1, "height": 16, "width": 16},
    }

    result = geometry.apply_geometry(img, params)

    manual = geometry.lens_distortion(img, -0.05)
    manual = geometry.perspective_correction(manual, vertical=0.05)
    manual = geometry.rotate(manual, 3.0)
    manual = geometry.crop(manual, top=1, left=1, height=16, width=16)

    np.testing.assert_allclose(result, manual, atol=1e-6)


def test_apply_geometry_skips_absent_steps():
    img = _checkerboard()
    result = geometry.apply_geometry(img, {"rotation": 10.0})
    expected = geometry.rotate(img, 10.0)
    np.testing.assert_allclose(result, expected)


def test_apply_geometry_empty_params_is_identity():
    img = _checkerboard()
    result = geometry.apply_geometry(img, {})
    np.testing.assert_allclose(result, img)


def test_geometry_operations_are_deterministic():
    """Same claim as nature-generation's tone ops: Tier 0 is "the only
    tier that is an exact function rather than a sample" — every geometry
    op must give byte-identical output across repeated calls."""
    img = _checkerboard()
    ops = [
        lambda x: geometry.lens_distortion(x, -0.05),
        lambda x: geometry.perspective_correction(x, vertical=0.05),
        lambda x: geometry.rotate(x, 12.0),
        lambda x: geometry.crop(x, top=1, left=1, height=10, width=10),
    ]
    for op in ops:
        first = op(img)
        second = op(img)
        np.testing.assert_array_equal(first, second)
