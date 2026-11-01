#!/usr/bin/env python3
"""Masked-region repaint for your live OBS background.

Regenerates just the masked part of your current background image — not
the whole thing — then writes the result back to the same file your OBS
"Static Image Background" source is pointed at (see
recipes/static-bg.md). Built on
modules/image-editing/workflows/inpaint-fill-v1.json, the same
generative-fill workflow the Krita integration uses.

This is the missing piece between recipe #1 (Static Image Background)
and recipe #4 (AI-Generated Environment, see recipes/ai-environment.md):
generate a background once with the full-replace workflow, then use this
script for touch-ups without a full re-render (different seed/lighting
every time you regenerate the whole image).

Usage:
    python3 repaint_region.py --background studio_bg.png --mask corner_mask.png \\
        --prompt "a warm reading lamp on a side table"

    # Preview to a new file instead of overwriting the live background
    python3 repaint_region.py --background studio_bg.png --mask corner_mask.png \\
        --prompt "..." --output studio_bg_preview.png

Mask convention: white = repaint this region, black = keep unchanged
(same convention as ComfyUI's MaskEditor).

After running, if OBS doesn't pick up the change: right-click the Image
source -> Properties -> reselect the file (or toggle it) to force a
cache refresh. OBS does not watch the file for changes automatically.

Requirements:
    pip install requests
    ComfyUI running at http://127.0.0.1:8188 with SDXL Inpainting
    (see modules/image-editing/workflows/README.md for model download)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import requests

log = logging.getLogger("repaint_region")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2] / "image-editing" / "workflows" / "inpaint-fill-v1.json"
)
DEFAULT_NEGATIVE = "lowres, bad quality, blurry, watermark, seam, discontinuity"
POLL_INTERVAL = 2

# ---------------------------------------------------------------------------
# ComfyUI helpers (same pattern as image-editing/krita/scripts/apply_style.py)
# ---------------------------------------------------------------------------


def _upload_image(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (filepath.name, f, "image/png")},
        )
    resp.raise_for_status()
    return resp.json()["name"]


def _build_workflow(image_name: str, mask_name: str, prompt: str, negative: str, seed: int) -> dict:
    raw = json.loads(WORKFLOW_PATH.read_text())
    raw.pop("_meta", None)  # not a node — must not be sent to ComfyUI's /prompt
    raw["2"]["inputs"]["image"] = image_name
    raw["3"]["inputs"]["image"] = mask_name
    raw["6"]["inputs"]["text"] = prompt
    raw["7"]["inputs"]["text"] = negative
    raw["8"]["inputs"]["seed"] = seed
    return raw


def _queue_prompt(workflow: dict) -> str:
    client_id = str(uuid.uuid4())
    resp = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def _wait_for_result(prompt_id: str, timeout: int = 300) -> list[str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
        resp.raise_for_status()
        data = resp.json()
        if prompt_id in data:
            filenames = []
            for node_out in data[prompt_id].get("outputs", {}).values():
                for img in node_out.get("images", []):
                    filenames.append(img["filename"])
            return filenames
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"ComfyUI did not finish prompt {prompt_id} in {timeout}s")


def _download_output(filename: str) -> bytes:
    resp = requests.get(
        f"{COMFYUI_URL}/view",
        params={"filename": filename, "type": "output"},
    )
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def repaint_region(
    background_path: Path,
    mask_path: Path,
    prompt: str,
    output_path: Path | None = None,
    negative: str = DEFAULT_NEGATIVE,
    seed: int = 0,
) -> Path:
    if not WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"Missing workflow: {WORKFLOW_PATH}")

    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
    except requests.ConnectionError:
        log.error("Cannot reach ComfyUI at %s. Start ComfyUI first (see modules/realtime-ai/setup/manual.md).", COMFYUI_URL)
        sys.exit(1)

    log.info("Uploading background: %s", background_path.name)
    image_name = _upload_image(background_path)
    log.info("Uploading mask: %s", mask_path.name)
    mask_name = _upload_image(mask_path)

    workflow = _build_workflow(image_name, mask_name, prompt, negative, seed)
    prompt_id = _queue_prompt(workflow)
    log.info("Queued prompt %s — waiting ...", prompt_id[:8])

    out_files = _wait_for_result(prompt_id)
    if not out_files:
        raise RuntimeError("No output received from ComfyUI")

    data = _download_output(out_files[0])
    # Default: overwrite the same file OBS is already watching, so no
    # source-path change is needed in OBS — just a cache refresh.
    dest = output_path or background_path
    dest.write_bytes(data)
    log.info("Saved -> %s (%d KB)", dest.name, len(data) // 1024)
    return dest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repaint a masked region of your OBS background image")
    parser.add_argument("--background", type=Path, required=True, help="Current background image (OBS source file)")
    parser.add_argument("--mask", type=Path, required=True, help="Mask PNG — white=repaint, black=keep")
    parser.add_argument("--prompt", type=str, required=True, help="What to generate in the masked region")
    parser.add_argument("--negative", type=str, default=DEFAULT_NEGATIVE)
    parser.add_argument("--output", type=Path, default=None, help="Write here instead of overwriting --background")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    repaint_region(
        background_path=args.background,
        mask_path=args.mask,
        prompt=args.prompt,
        output_path=args.output,
        negative=args.negative,
        seed=args.seed,
    )
