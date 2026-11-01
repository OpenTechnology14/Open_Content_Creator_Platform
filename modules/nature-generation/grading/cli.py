"""Command-line entry point for Tier 0 grading.

    python3 -m grading.cli --input photo.jpg --preset presets/overcast-lift.yaml --output out.png
    python3 -m grading.cli --input photo.jpg --vibrance 0.25 --exposure 0.3 --output out.png

Run from `modules/nature-generation/` so `grading` imports resolve.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from . import tone
from .presets import apply_preset, load_preset


def load_image(path: Path | str) -> np.ndarray:
    from PIL import Image  # noqa: PLC0415

    img = Image.open(path).convert("RGB")
    return np.asarray(img, dtype=np.float32) / 255.0


def save_image(array: np.ndarray, path: Path | str) -> None:
    from PIL import Image  # noqa: PLC0415

    clipped = np.clip(array, 0.0, 1.0)
    img = Image.fromarray((clipped * 255.0).round().astype(np.uint8))
    img.save(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--preset", type=Path, help="preset YAML — see grading/README.md's schema")
    p.add_argument("--vibrance", type=float, default=None)
    p.add_argument("--saturation", type=float, default=None)
    p.add_argument("--exposure", type=float, default=None)
    p.add_argument("--contrast", type=float, default=None)
    args = p.parse_args(argv)

    image = load_image(args.input)

    if args.preset:
        preset = load_preset(args.preset)
        image = apply_preset(image, preset)
    else:
        if args.vibrance is not None:
            image = tone.vibrance(image, args.vibrance)
        if args.saturation is not None:
            image = tone.saturation(image, args.saturation)
        if args.exposure is not None:
            image = tone.exposure(image, args.exposure)
        if args.contrast is not None:
            image = tone.contrast(image, args.contrast)

    save_image(image, args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
