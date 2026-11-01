"""Load and apply a Tier 0 preset YAML — the schema grading/README.md
documents:

    preset: overcast-lift
    pairs_with: nature-overcast-v1     # adapter in ../adapters/
    vibrance: 0.25
    exposure: +0.3
    white_balance: {temp: -200, tint: +4}
    curves:
      rgb: [[0, 8], [64, 72], [192, 200], [255, 250]]

`pairs_with` names a Tier 4 adapter this preset's tone is designed to
complement — informational only here; nothing in this module trains or
applies adapters (see ../adapters/README.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml

from . import tone


def load_preset(path: Path | str) -> dict[str, Any]:
    with open(path) as f:
        doc = yaml.safe_load(f)
    if "preset" not in doc:
        raise ValueError(f"{path}: missing required 'preset' key")
    return doc


def apply_preset(image: np.ndarray, preset: dict[str, Any]) -> np.ndarray:
    """Apply a preset's operations in a fixed order: white balance,
    exposure, vibrance/saturation, contrast, then curves last — curves are
    "where a look actually lives" per grading/README.md, so they get the
    final say over the tonal operations that precede them."""
    out = image
    if "white_balance" in preset:
        wb = preset["white_balance"]
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
