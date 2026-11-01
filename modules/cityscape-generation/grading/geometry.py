"""Tier 0 — geometry corrections unique to cityscape (see grading/README.md's
"Geometry — cityscape only" table). No AI, no GPU, no OpenCV — a single
shared inverse-warp/bilinear-sample core underlies lens distortion,
perspective (keystone) correction, and rotation, each supplying its own
coordinate map.

Order, per grading/README.md, is always: distortion -> perspective ->
rotation -> crop -> tone. Correcting distortion first matters because
every later operation inherits it; perspective before crop because
correction loses edge pixels crop would otherwise have already discarded.
`apply_geometry()` below applies exactly this order.

Images are float32 numpy arrays, shape (H, W, 3), values in [0, 1] — same
convention as tone.py.
"""

from __future__ import annotations

import numpy as np


def _bilinear_sample(image: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Sample `image` at floating-point coordinates (xs, ys) — same shape
    as the output — using bilinear interpolation. Out-of-bounds samples
    return 0 (black), not a wraparound or an error; a correction that
    needs to pull in pixels from outside the original frame is exactly
    the "perspective correction loses edge pixels" case grading/README.md
    already names as a reason to crop after, not before."""
    h, w = image.shape[:2]
    x0 = np.floor(xs).astype(np.int64)
    y0 = np.floor(ys).astype(np.int64)
    x1, y1 = x0 + 1, y0 + 1

    fx, fy = xs - x0, ys - y0

    def gather(yi: np.ndarray, xi: np.ndarray) -> np.ndarray:
        valid = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        xi_c = np.clip(xi, 0, w - 1)
        yi_c = np.clip(yi, 0, h - 1)
        out = image[yi_c, xi_c]
        return np.where(valid[..., None], out, 0.0)

    top = gather(y0, x0) * (1 - fx)[..., None] + gather(y0, x1) * fx[..., None]
    bottom = gather(y1, x0) * (1 - fx)[..., None] + gather(y1, x1) * fx[..., None]
    return (top * (1 - fy)[..., None] + bottom * fy[..., None]).astype(np.float32)


def _output_grid(height: int, width: int) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float64)
    return xs, ys


def lens_distortion(image: np.ndarray, barrel: float) -> np.ndarray:
    """Correct radial lens distortion. `barrel` is the coefficient from
    grading/README.md's preset schema — negative corrects barrel
    distortion (the common case for wide lenses), positive corrects
    pincushion. `barrel=0` is exact identity.

    Model: for each output pixel at normalized radius r from centre, the
    corresponding SOURCE pixel is at r * (1 + barrel * r^2) — the standard
    single-term radial distortion model. This corrects distortion (maps a
    distorted image to a corrected one); it is not the forward model a
    lens itself applies.
    """
    if barrel == 0.0:
        return image.copy()

    h, w = image.shape[:2]
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    scale = max(cx, cy)

    xs, ys = _output_grid(h, w)
    nx, ny = (xs - cx) / scale, (ys - cy) / scale
    r = np.sqrt(nx**2 + ny**2)
    factor = 1.0 + barrel * r**2

    src_x = cx + nx * factor * scale
    src_y = cy + ny * factor * scale
    return _bilinear_sample(image, src_x, src_y)


def perspective_correction(
    image: np.ndarray, vertical: float = 0.0, horizontal: float = 0.0
) -> np.ndarray:
    """Correct converging verticals/horizontals ("keystone"). `vertical`
    and `horizontal` are skew fractions in roughly [-0.5, 0.5] — how far
    the top (for vertical) or one side (for horizontal) has additionally
    converged toward the centre, as a fraction of half the frame
    dimension. Both 0 is exact identity.

    This is a real, if simplified, homography: the four output corners
    map to a keystone-shaped quadrilateral in the source, solved for a
    single projective transform via a linear system — not the "pretend
    it's a simple vertical shear" approximation, which corrects tilt but
    not true perspective."""
    for name, value in (("vertical", vertical), ("horizontal", horizontal)):
        if isinstance(value, str):
            # grading/README.md's preset example uses `perspective: {vertical: auto}`
            # — automatic keystone detection from vanishing lines in the image.
            # That's a real computer-vision feature (line/vanishing-point
            # detection), not a Tier 0 "no AI, no GPU" operation, and isn't
            # built here. Fail loudly rather than silently no-op or crash on
            # a string-vs-float multiply further down.
            raise NotImplementedError(
                f"perspective_correction({name}={value!r}): automatic keystone "
                f"detection is not implemented — pass an explicit numeric value"
            )

    if vertical == 0.0 and horizontal == 0.0:
        return image.copy()

    h, w = image.shape[:2]
    dst_corners = np.array(
        [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float64
    )
    # Source quadrilateral: top edge pulled in by `vertical`, one side
    # pulled in by `horizontal` — the keystone shape a corrected image's
    # four corners actually came from in the original (distorted) frame.
    top_in = vertical * (w / 2.0)
    side_in = horizontal * (h / 2.0)
    src_corners = np.array(
        [
            [0 + top_in, 0 + side_in],
            [w - 1 - top_in, 0 + side_in],
            [w - 1, h - 1],
            [0, h - 1],
        ],
        dtype=np.float64,
    )

    homography = _solve_homography(dst_corners, src_corners)
    xs, ys = _output_grid(h, w)
    ones = np.ones_like(xs)
    dst_pts = np.stack([xs, ys, ones], axis=-1)
    src_pts = dst_pts @ homography.T
    src_x = src_pts[..., 0] / src_pts[..., 2]
    src_y = src_pts[..., 1] / src_pts[..., 2]
    return _bilinear_sample(image, src_x, src_y)


def _solve_homography(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    """Solve for H such that src ~= H @ dst (homogeneous), given 4 point
    correspondences — the standard DLT (direct linear transform) setup."""
    A = []
    for (dx, dy), (sx, sy) in zip(dst, src):
        A.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy, -sx])
        A.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy, -sy])
    A = np.array(A, dtype=np.float64)
    _, _, vt = np.linalg.svd(A)
    h = vt[-1].reshape(3, 3)
    return h / h[2, 2]


def rotate(image: np.ndarray, degrees: float) -> np.ndarray:
    """Rotate about the image centre. `degrees=0` is exact identity.
    Positive `degrees` rotates the image content **clockwise** — e.g.
    `rotate(img, 90)` moves content that was at the top-right corner to
    the bottom-right. Verified empirically, not just asserted: array row
    index increases downward, which flips the usual "positive angle is
    counter-clockwise" math convention relative to what it would mean for
    y-up coordinates."""
    if degrees == 0.0:
        return image.copy()

    h, w = image.shape[:2]
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    theta = np.radians(-degrees)  # negated: makes positive `degrees` clockwise, see docstring
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    xs, ys = _output_grid(h, w)
    dx, dy = xs - cx, ys - cy
    src_x = cx + dx * cos_t - dy * sin_t
    src_y = cy + dx * sin_t + dy * cos_t
    return _bilinear_sample(image, src_x, src_y)


def crop(image: np.ndarray, top: int, left: int, height: int, width: int) -> np.ndarray:
    """Exact pixel extraction — no interpolation, no approximation."""
    return image[top : top + height, left : left + width].copy()


def apply_geometry(image: np.ndarray, params: dict) -> np.ndarray:
    """Apply every geometry op present in `params`, in the fixed order
    grading/README.md specifies: distortion -> perspective -> rotation ->
    crop. Any step missing from `params` is skipped, not defaulted to a
    no-op call — cheaper, and avoids a redundant identity resample."""
    out = image
    if "lens_distortion" in params:
        out = lens_distortion(out, params["lens_distortion"].get("barrel", 0.0))
    if "perspective" in params:
        p = params["perspective"]
        out = perspective_correction(
            out, vertical=p.get("vertical", 0.0), horizontal=p.get("horizontal", 0.0)
        )
    if "rotation" in params:
        out = rotate(out, params["rotation"])
    if "crop" in params:
        c = params["crop"]
        out = crop(out, c["top"], c["left"], c["height"], c["width"])
    return out
