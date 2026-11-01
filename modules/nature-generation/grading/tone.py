"""Tier 0 — deterministic tone and colour operations. No AI, no GPU, no
ComfyUI, no corpus. Pure functions over a numpy array; every operation is
an exact, reversible-in-principle transform, matching this module's own
grading/README.md.

Images are float32 numpy arrays, shape (H, W, 3), RGB order, values in
[0, 1] — the calling code converts to/from 8-bit at the edges (see
`load_image`/`save_image`). Colour-space handling follows the table in
grading/README.md exactly:

    Vibrance              LAB
    Saturation            LAB or HSV, never gamma-encoded sRGB — LAB used
                          here for consistency with vibrance
    Exposure              linear light
    White balance         linear light
    Contrast              gamma-encoded (sRGB) is fine
    Per-channel curves    RGB (gamma-encoded)

Only numpy — no OpenCV. Full geometric correction (cityscape's domain)
needs it; this module's Tier 0 is intentionally scoped to what plain
array math does exactly and testably.
"""

from __future__ import annotations

import numpy as np

# ── sRGB <-> linear light ─────────────────────────────────────────────
# Standard sRGB EOTF (IEC 61966-2-1), not a flat gamma-2.2 approximation —
# the piecewise form matters near black, which is exactly where "protect
# the black point" caution in both grading READMEs applies.


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    srgb = np.clip(srgb, 0.0, 1.0)
    return np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )


def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    linear = np.clip(linear, 0.0, 1.0)
    return np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * (linear ** (1.0 / 2.4)) - 0.055,
    )


# ── sRGB(linear) <-> CIE LAB, via XYZ (D65) ───────────────────────────
# Standard matrices/formulas — see any colorimetry reference (e.g. Bruce
# Lindbloom's site). Kept in linear-light space going in, matching how
# every real colour pipeline does this conversion.

_RGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
])
_XYZ_TO_RGB = np.linalg.inv(_RGB_TO_XYZ)
_D65_WHITE = np.array([0.95047, 1.00000, 1.08883])


def _f_lab(t: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    return np.where(t > delta**3, np.cbrt(t), t / (3 * delta**2) + 4.0 / 29.0)


def _f_lab_inv(t: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    return np.where(t > delta, t**3, 3 * delta**2 * (t - 4.0 / 29.0))


def linear_rgb_to_lab(linear_rgb: np.ndarray) -> np.ndarray:
    xyz = linear_rgb @ _RGB_TO_XYZ.T
    xyz_n = xyz / _D65_WHITE
    fx, fy, fz = _f_lab(xyz_n[..., 0]), _f_lab(xyz_n[..., 1]), _f_lab(xyz_n[..., 2])
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def lab_to_linear_rgb(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    xyz_n = np.stack([_f_lab_inv(fx), _f_lab_inv(fy), _f_lab_inv(fz)], axis=-1)
    xyz = xyz_n * _D65_WHITE
    linear_rgb = xyz @ _XYZ_TO_RGB.T
    return np.clip(linear_rgb, 0.0, None)


# ── Operations ─────────────────────────────────────────────────────────


def exposure(srgb: np.ndarray, stops: float) -> np.ndarray:
    """Linear-light multiply. `stops` in [-3, +3] per grading/README.md."""
    linear = srgb_to_linear(srgb)
    linear = linear * (2.0**stops)
    return linear_to_srgb(linear)


def white_balance(srgb: np.ndarray, temp: float = 0.0, tint: float = 0.0) -> np.ndarray:
    """Linear-light channel gain. `temp` shifts blue<->orange (positive =
    warmer, more red/less blue); `tint` shifts green<->magenta. Both are
    small approximate offsets (roughly Kelvin/100 and a green-magenta
    fraction), not a physically exact colour-temperature model — exact
    enough for a grading preset, not a colorimeter."""
    linear = srgb_to_linear(srgb)
    r_gain = 1.0 + temp * 0.001
    b_gain = 1.0 - temp * 0.001
    g_gain = 1.0 - tint * 0.001
    gains = np.array([r_gain, g_gain, b_gain])
    linear = linear * gains
    return linear_to_srgb(linear)


def saturation(srgb: np.ndarray, scale: float) -> np.ndarray:
    """Uniform LAB chroma scale, `scale` in [0, 2]. `scale=1` is identity,
    `scale=0` is greyscale. Unlike vibrance, every pixel is scaled equally
    regardless of how saturated it already is — this is the "already-
    saturated sky goes neon" behaviour grading/README.md warns about."""
    linear = srgb_to_linear(srgb)
    lab = linear_rgb_to_lab(linear)
    lab[..., 1] *= scale
    lab[..., 2] *= scale
    linear = lab_to_linear_rgb(lab)
    return linear_to_srgb(linear)


def vibrance(srgb: np.ndarray, amount: float) -> np.ndarray:
    """LAB chroma boost weighted *away* from already-saturated pixels —
    the opposite weighting from `saturation()`. A pixel near max chroma
    for its lightness gets almost no additional boost; a muted pixel gets
    close to the full `amount`. This is "usually what someone means" per
    grading/README.md."""
    linear = srgb_to_linear(srgb)
    lab = linear_rgb_to_lab(linear)
    chroma = np.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    # Weight falls off as chroma rises. 100 is an approximate practical
    # max chroma for sRGB gamut in CIELAB; this is a soft, not hard, cap.
    weight = np.clip(1.0 - chroma / 100.0, 0.0, 1.0)
    boost = 1.0 + amount * weight
    lab[..., 1] *= boost
    lab[..., 2] *= boost
    linear = lab_to_linear_rgb(lab)
    return linear_to_srgb(linear)


def contrast(srgb: np.ndarray, amount: float) -> np.ndarray:
    """S-curve contrast in gamma-encoded space (per grading/README.md,
    unlike exposure/white-balance which are linear-light). `amount` in
    [-1, 1]; 0 is identity. Pivots at 0.5 (mid-grey)."""
    amount = np.clip(amount, -1.0, 1.0)
    # Power-based pivot at mid-grey: monotonic for any `amount`, exact
    # identity at amount=0, and exact at both endpoints (0 and 1) for
    # every amount — a simple sin()-based S-curve overshoots near the
    # extremes and doesn't have that last property. The exponent is kept
    # strictly positive (floor 0.01, not 0) so amount=-1 doesn't hit the
    # x**0 == 1 singularity at x=0, which would otherwise send black to
    # 0.5 instead of leaving it fixed.
    exponent = max(1.0 + amount, 0.01)
    x = srgb
    lo = x < 0.5
    out = np.where(
        lo,
        0.5 * (2 * x) ** exponent,
        1.0 - 0.5 * (2 * (1.0 - x)) ** exponent,
    )
    return np.clip(out, 0.0, 1.0)


def apply_curves(srgb: np.ndarray, control_points: list[list[float]]) -> np.ndarray:
    """Per-channel RGB curve via piecewise-linear interpolation over
    `control_points` — [[in_0, out_0], [in_1, out_1], ...] in 0-255 scale
    (matching the preset YAML examples in grading/README.md), applied
    identically to R, G, and B. Gamma-encoded space, per the README table."""
    xs = np.array([p[0] for p in control_points], dtype=np.float64) / 255.0
    ys = np.array([p[1] for p in control_points], dtype=np.float64) / 255.0
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    flat = srgb.reshape(-1)
    curved = np.interp(flat, xs, ys)
    return curved.reshape(srgb.shape).astype(np.float32)
