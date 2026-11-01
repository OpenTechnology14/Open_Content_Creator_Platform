#!/usr/bin/env python3
"""Generate a deterministic placeholder icon source PNG for a desktop app.

Not real branding — a flat-color square with the product's first letter,
meant to unblock `tauri icon` (which needs a 1024x1024 source image to
generate the full icon set) until real brand assets exist. See each app's
README/docs for the disclosure that this is a placeholder.

Usage:
    python3 generate_placeholder_icons.py --name "Stream Extend" --color "#ff6b35" --out apps/stream-extend/icon-source.png
    python3 generate_placeholder_icons.py --name "Creator Extend" --color "#7c4dff" --out apps/creator-extend/icon-source.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024


def generate(name: str, color: str, out_path: Path) -> None:
    img = Image.new("RGB", (SIZE, SIZE), color)
    draw = ImageDraw.Draw(img)

    letter = name.strip()[0].upper()
    font_size = int(SIZE * 0.55)
    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", font_size
        )
    except OSError:
        font = ImageFont.load_default(size=font_size)

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    position = ((SIZE - text_w) / 2 - bbox[0], (SIZE - text_h) / 2 - bbox[1])
    draw.text(position, letter, fill="white", font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"wrote {out_path} ({SIZE}x{SIZE}, placeholder — not real branding)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name", required=True, help="Product name, e.g. 'Stream Extend'")
    p.add_argument("--color", required=True, help="Hex background color, e.g. '#ff6b35'")
    p.add_argument("--out", required=True, type=Path, help="Output PNG path")
    args = p.parse_args()
    generate(args.name, args.color, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
