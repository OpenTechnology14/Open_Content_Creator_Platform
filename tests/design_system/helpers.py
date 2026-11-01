"""Shared helpers for the design-system tests: token loading and WCAG 2.x contrast."""
from __future__ import annotations

import colorsys
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
HUB = REPO / "design-system"
TOKENS = HUB / "tokens.yaml"
THEMES = ("light", "dark")

_HSL = re.compile(r"hsl\(\s*([0-9.]+)\s+([0-9.]+)%\s+([0-9.]+)%\s*\)")
_HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")


def load() -> dict:
    return yaml.safe_load(TOKENS.read_text(encoding="utf-8"))


def is_color(text: str) -> bool:
    return bool(_HSL.fullmatch(text.strip()) or _HEX.fullmatch(text.strip()) or text.strip() == "white")


def rgb(text: str) -> tuple[float, float, float]:
    text = text.strip()
    if text == "white":
        return (1.0, 1.0, 1.0)
    if (m := _HSL.fullmatch(text)):
        hue, saturation, lightness = float(m[1]) / 360, float(m[2]) / 100, float(m[3]) / 100
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        return (r, g, b)
    if (m := _HEX.fullmatch(text)):
        digits = m[1]
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return tuple(int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4))
    raise ValueError(f"not a color: {text!r}")


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(text: str) -> float:
    r, g, b = (_linear(c) for c in rgb(text))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
