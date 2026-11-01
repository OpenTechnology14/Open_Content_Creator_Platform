"""Load and apply a Tier 0 preset YAML — the schema grading/README.md
documents:

    preset: night-neon-cool
    pairs_with: cityscape-neon-night-v1
    lens_distortion: {barrel: -0.02}
    perspective: {vertical: auto}
    white_balance:
      shadows: {temp: -400}
      highlights: {temp: 150}
    vibrance: 0.2
    curves:
      rgb: [[0, 4], [48, 40], [200, 210], [255, 252]]

Order is fixed, per grading/README.md: distortion -> perspective ->
rotation -> crop -> tone. `apply_preset()` delegates the geometry half to
`geometry.apply_geometry()` (already in that internal order) and then
applies tone last.

`white_balance` here differs from nature-generation's flat {temp, tint}
shape — cityscape's schema splits it into `shadows`/`highlights`, per-range
correction for mixed lighting sources (grading/README.md's "Colour —
cityscape only" section). `tone.white_balance()` only takes one flat
temp/tint pair; applying the shadows/highlights split for real needs a
luminance-dependent blend this Tier 0 scaffold doesn't build yet — see
apply_preset()'s own comment at that step for exactly what it does today.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from . import geometry, tone


def load_preset(path: Path | str) -> dict[str, Any]:
    with open(path) as f:
        doc = yaml.safe_load(f)
    if "preset" not in doc:
        raise ValueError(f"{path}: missing required 'preset' key")
    return doc


def apply_preset(image: np.ndarray, preset: dict[str, Any]) -> np.ndarray:
    geometry_params = {
        k: preset[k] for k in ("lens_distortion", "perspective", "rotation", "crop") if k in preset
    }
    out = geometry.apply_geometry(image, geometry_params) if geometry_params else image

    if "white_balance" in preset:
        wb = preset["white_balance"]
        if "shadows" in wb or "highlights" in wb:
            # Not yet implemented: a real per-range correction needs a
            # luminance mask blending two different temp/tint corrections,
            # which is more than a Tier 0 scaffold pass builds. Loudly
            # refuse rather than silently apply only one range (or neither)
            # and produce output that doesn't match what the preset asked for.
            raise NotImplementedError(
                "white_balance.shadows/highlights (mixed-source correction) is "
                "not implemented — only a flat {temp, tint} white_balance is "
                "supported today"
            )
        out = tone.white_balance(out, temp=wb.get("temp", 0.0), tint=wb.get("tint", 0.0))
    if "exposure" in preset:
        out = tone.exposure(out, float(preset["exposure"]))
    if "vibrance" in preset:
        out = tone.vibrance(out, float(preset["vibrance"]))
    if "saturation" in preset:
        out = tone.saturation(out, float(preset["saturation"]))
    if "contrast" in preset:
        out = tone.contrast(out, float(preset["contrast"]))
    if "curves" in preset and "rgb" in preset["curves"]:
        out = tone.apply_curves(out, preset["curves"]["rgb"])
    return out
