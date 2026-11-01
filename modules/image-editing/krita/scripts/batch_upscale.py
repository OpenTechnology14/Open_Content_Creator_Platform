#!/usr/bin/env python3
"""Batch upscale images via ComfyUI's UltimateSDUpscale node.

Reads every .png / .jpg / .webp from an input folder, sends each to a
running ComfyUI instance using the upscale workflow, and writes the
results to an output folder.

Usage (standalone — outside Krita):
    python batch_upscale.py --input ./raw --output ./upscaled
    python batch_upscale.py --input ./raw --output ./upscaled --scale 4
    python batch_upscale.py --input ./raw --output ./upscaled --dry-run

Usage (inside Krita — as a Krita script action):
    The script also exposes `upscale_current_layer()` which can be bound
    to a Krita shortcut. It sends the active layer to ComfyUI and places
    the upscaled result on a new layer.

Requirements:
    pip install websocket-client requests Pillow
    ComfyUI running at http://127.0.0.1:8188 with UltimateSDUpscale node
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import time
import uuid
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COMFYUI_URL = "http://127.0.0.1:8188"
SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_SCALE = 2
POLL_INTERVAL = 2  # seconds

log = logging.getLogger("batch_upscale")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ---------------------------------------------------------------------------
# ComfyUI helpers
# ---------------------------------------------------------------------------


def _upload_image(filepath: Path) -> str:
    """Upload an image to ComfyUI's /upload/image endpoint. Returns filename."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (filepath.name, f, "image/png")},
        )
    resp.raise_for_status()
    return resp.json()["name"]


def _build_upscale_workflow(image_name: str, scale: int) -> dict:
    """Return a minimal ComfyUI API prompt for tiled upscale."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        "2": {
            "class_type": "UltimateSDUpscale",
            "inputs": {
                "image": ["1", 0],
                "upscale_by": scale,
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 0.3,
                "tile_width": 512,
                "tile_height": 512,
                "tile_padding": 32,
                "seam_fix_mode": "Half Tile",
                "seam_fix_denoise": 0.25,
                "seam_fix_width": 64,
                "seam_fix_mask_blur": 8,
                "seam_fix_padding": 16,
                "upscale_model": "RealESRGAN_x4plus.pth",
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["2", 0],
                "filename_prefix": "upscaled",
            },
        },
    }


def _queue_prompt(workflow: dict) -> str:
    """Queue a workflow and return the prompt_id."""
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow, "client_id": client_id}
    resp = requests.post(f"{COMFYUI_URL}/prompt", json=payload)
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def _wait_for_result(prompt_id: str, timeout: int = 300) -> list[str]:
    """Poll /history until the prompt completes. Return output filenames."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
        resp.raise_for_status()
        data = resp.json()
        if prompt_id in data:
            outputs = data[prompt_id].get("outputs", {})
            filenames = []
            for node_output in outputs.values():
                for img in node_output.get("images", []):
                    filenames.append(img["filename"])
            return filenames
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"ComfyUI did not finish prompt {prompt_id} in {timeout}s")


def _download_output(filename: str) -> bytes:
    """Download a finished image from ComfyUI's output directory."""
    resp = requests.get(
        f"{COMFYUI_URL}/view",
        params={"filename": filename, "type": "output"},
    )
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def process_folder(
    input_dir: Path,
    output_dir: Path,
    scale: int = DEFAULT_SCALE,
    dry_run: bool = False,
) -> None:
    """Process every supported image in input_dir."""
    files = sorted(
        f for f in input_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTS
    )
    if not files:
        log.warning("No images found in %s", input_dir)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    log.info("Found %d image(s) — scale %dx", len(files), scale)

    if dry_run:
        for f in files:
            log.info("[dry-run] Would upscale: %s", f.name)
        return

    # ── Manual step: verify ComfyUI is reachable ──────────────────────
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
    except requests.ConnectionError:
        log.error(
            "Cannot reach ComfyUI at %s. "
            "Start ComfyUI first (see modules/realtime-ai/setup/manual.md).",
            COMFYUI_URL,
        )
        sys.exit(1)

    for idx, filepath in enumerate(files, 1):
        log.info("[%d/%d] Uploading %s ...", idx, len(files), filepath.name)
        remote_name = _upload_image(filepath)

        workflow = _build_upscale_workflow(remote_name, scale)
        prompt_id = _queue_prompt(workflow)
        log.info("  Queued prompt %s — waiting ...", prompt_id[:8])

        out_files = _wait_for_result(prompt_id)
        for out_name in out_files:
            data = _download_output(out_name)
            dest = output_dir / f"{filepath.stem}_{scale}x.png"
            dest.write_bytes(data)
            log.info("  Saved → %s (%d KB)", dest.name, len(data) // 1024)


# ---------------------------------------------------------------------------
# Krita integration (optional — only runs inside Krita)
# ---------------------------------------------------------------------------

try:
    from krita import Krita  # type: ignore[import-untyped]

    def upscale_current_layer(scale: int = DEFAULT_SCALE) -> None:
        """Send the active layer to ComfyUI for upscaling, add result as new layer."""
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            raise RuntimeError("No active document in Krita")

        layer = doc.activeNode()
        # Export active layer to temp PNG
        pixel_data = layer.pixelData(0, 0, doc.width(), doc.height())

        from PIL import Image  # type: ignore[import-untyped]

        img = Image.frombytes("RGBA", (doc.width(), doc.height()), pixel_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # Upload
        resp = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": ("krita_layer.png", buf, "image/png")},
        )
        resp.raise_for_status()
        remote_name = resp.json()["name"]

        # Queue and wait
        workflow = _build_upscale_workflow(remote_name, scale)
        prompt_id = _queue_prompt(workflow)
        out_files = _wait_for_result(prompt_id)

        if out_files:
            data = _download_output(out_files[0])
            result_img = Image.open(io.BytesIO(data))
            new_layer = doc.createNode(f"Upscaled {scale}x", "paintlayer")
            new_layer.setPixelData(
                result_img.tobytes(), 0, 0, result_img.width, result_img.height
            )
            doc.rootNode().addChildNode(new_layer, None)
            doc.refreshProjection()

except ImportError:
    pass  # Not running inside Krita — CLI-only mode


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch upscale images via ComfyUI"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Folder of images to upscale"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Destination folder"
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=DEFAULT_SCALE,
        choices=[2, 4],
        help="Upscale factor (default: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without processing",
    )
    args = parser.parse_args()
    process_folder(args.input, args.output, scale=args.scale, dry_run=args.dry_run)
