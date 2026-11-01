"""Command-line entry point for Tier 0 grading (tone + geometry).

    python3 -m grading.cli --input photo.jpg --preset presets/night-neon-cool.yaml --output out.png
    python3 -m grading.cli --input photo.jpg --rotate 1.2 --vibrance 0.2 --output out.png

Run from `modules/cityscape-generation/` so `grading` imports resolve.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from . import geometry, tone
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
    p.add_argument("--barrel", type=float, default=None, help="lens distortion coefficient")
    p.add_argument("--perspective-vertical", type=float, default=None)
    p.add_argument("--perspective-horizontal", type=float, default=None)
    p.add_argument("--rotate", type=float, default=None, help="degrees")
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
        if args.barrel is not None:
            image = geometry.lens_distortion(image, args.barrel)
        if args.perspective_vertical is not None or args.perspective_horizontal is not None:
            image = geometry.perspective_correction(
                image,
                vertical=args.perspective_vertical or 0.0,
                horizontal=args.perspective_horizontal or 0.0,
            )
        if args.rotate is not None:
            image = geometry.rotate(image, args.rotate)
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
