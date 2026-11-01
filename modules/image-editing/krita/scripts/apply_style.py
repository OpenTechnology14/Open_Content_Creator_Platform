#!/usr/bin/env python3
"""Apply a style preset to an image via ComfyUI's IPAdapter node.

Takes a content image and a style reference image, sends both to ComfyUI
with an IPAdapter + ControlNet workflow, and returns the stylized result.

Usage (standalone):
    python apply_style.py --content photo.png --style monet.png --output styled.png
    python apply_style.py --content photo.png --style monet.png --strength 0.8
    python apply_style.py --content photo.png --style monet.png --dry-run

Usage (inside Krita):
    Select a region, then call `apply_style_to_selection("style_name")`
    from Krita's scripting console or bind it to a shortcut.

Named presets (STYLE_PRESETS below — NOT files in ../presets/, which is a
different, unrelated, currently-empty folder for Krita workspace layouts;
see krita/README.md):
    anime      — clean anime / cel-shading style
    watercolor — soft watercolor / illustration
    oil        — oil painting texture and brushwork
    pixel      — pixel art reduction
    cinematic  — film color grading + grain

Known limitation: each preset is only a (weight, denoise) tuning pair —
there is no bundled reference image showing what "anime" or "watercolor"
actually looks like. In CLI mode you supply your own --style reference,
so this doesn't matter. In Krita preset mode (apply_style_to_selection),
there is no separate reference to supply, so the content image is used as
its own style reference (see that function) — the preset's weight/denoise
numbers shape the result, but two different presets will look more alike
than their names suggest until real per-preset reference images exist.

Requirements:
    pip install websocket-client requests Pillow
    ComfyUI running at http://127.0.0.1:8188 with:
      - ComfyUI_IPAdapter_plus
      - comfyui_controlnet_aux
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

log = logging.getLogger("apply_style")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COMFYUI_URL = "http://127.0.0.1:8188"
POLL_INTERVAL = 2
DEFAULT_STRENGTH = 0.7
DEFAULT_DENOISE = 0.5

# Built-in style presets — each maps to specific IPAdapter settings
STYLE_PRESETS: dict[str, dict] = {
    "anime": {
        "weight": 0.85,
        "denoise": 0.55,
        "description": "Clean anime / cel-shading",
    },
    "watercolor": {
        "weight": 0.75,
        "denoise": 0.60,
        "description": "Soft watercolor illustration",
    },
    "oil": {
        "weight": 0.80,
        "denoise": 0.50,
        "description": "Oil painting texture",
    },
    "pixel": {
        "weight": 0.90,
        "denoise": 0.70,
        "description": "Pixel art reduction",
    },
    "cinematic": {
        "weight": 0.65,
        "denoise": 0.40,
        "description": "Film color grading + grain",
    },
}

# ---------------------------------------------------------------------------
# ComfyUI helpers
# ---------------------------------------------------------------------------


def _upload_image(filepath: Path) -> str:
    """Upload an image to ComfyUI. Returns the filename on the server."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{COMFYUI_URL}/upload/image",
            files={"image": (filepath.name, f, "image/png")},
        )
    resp.raise_for_status()
    return resp.json()["name"]


def _upload_image_bytes(data: bytes, name: str = "krita_input.png") -> str:
    """Upload raw bytes as an image. Returns the filename on the server."""
    resp = requests.post(
        f"{COMFYUI_URL}/upload/image",
        files={"image": (name, io.BytesIO(data), "image/png")},
    )
    resp.raise_for_status()
    return resp.json()["name"]


def _build_style_workflow(
    content_name: str,
    style_name: str,
    strength: float,
    denoise: float,
) -> dict:
    """Build a ComfyUI API workflow for IPAdapter style transfer."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": content_name},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": style_name},
        },
        "3": {
            "class_type": "CLIPVisionLoader",
            "inputs": {
                "clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
            },
        },
        "4": {
            "class_type": "IPAdapterModelLoader",
            "inputs": {
                "ipadapter_file": "ip-adapter-plus_sd15.safetensors",
            },
        },
        "5": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors",
            },
        },
        "6": {
            "class_type": "IPAdapterApply",
            "inputs": {
                "ipadapter": ["4", 0],
                "clip_vision": ["3", 0],
                "image": ["2", 0],
                "model": ["5", 0],
                "weight": strength,
            },
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["6", 0],
                "positive": ["8", 0],
                "negative": ["9", 0],
                "latent_image": ["10", 0],
                "seed": 42,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": denoise,
            },
        },
        "8": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "masterpiece, best quality",
                "clip": ["5", 1],
            },
        },
        "9": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "lowres, bad quality, blurry, watermark",
                "clip": ["5", 1],
            },
        },
        "10": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["1", 0],
                "vae": ["5", 2],
            },
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["5", 2],
            },
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["11", 0],
                "filename_prefix": "styled",
            },
        },
    }


def _queue_prompt(workflow: dict) -> str:
    """Queue a ComfyUI workflow and return the prompt_id."""
    client_id = str(uuid.uuid4())
    resp = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def _wait_for_result(prompt_id: str, timeout: int = 300) -> list[str]:
    """Poll /history until the prompt finishes. Return output filenames."""
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
    """Download a result image from ComfyUI's output directory."""
    resp = requests.get(
        f"{COMFYUI_URL}/view",
        params={"filename": filename, "type": "output"},
    )
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def apply_style(
    content_path: Path,
    style_path: Path,
    output_path: Path | None = None,
    strength: float = DEFAULT_STRENGTH,
    denoise: float = DEFAULT_DENOISE,
    dry_run: bool = False,
) -> Path | None:
    """Apply style transfer to a single image. Return the output path."""
    if dry_run:
        log.info(
            "[dry-run] Would stylize %s with %s (strength=%.2f, denoise=%.2f)",
            content_path.name,
            style_path.name,
            strength,
            denoise,
        )
        return None

    # ── Manual step: verify ComfyUI is reachable ──────────────────────
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
    except requests.ConnectionError:
        log.error(
            "Cannot reach ComfyUI at %s. Start ComfyUI first (see modules/realtime-ai/setup/manual.md).",
            COMFYUI_URL,
        )
        sys.exit(1)

    log.info("Uploading content: %s", content_path.name)
    content_name = _upload_image(content_path)

    log.info("Uploading style: %s", style_path.name)
    style_name = _upload_image(style_path)

    workflow = _build_style_workflow(content_name, style_name, strength, denoise)
    prompt_id = _queue_prompt(workflow)
    log.info("Queued prompt %s — waiting ...", prompt_id[:8])

    out_files = _wait_for_result(prompt_id)
    if not out_files:
        log.error("No output received from ComfyUI")
        return None

    data = _download_output(out_files[0])
    dest = output_path or content_path.with_stem(f"{content_path.stem}_styled")
    dest.write_bytes(data)
    log.info("Saved → %s (%d KB)", dest.name, len(data) // 1024)
    return dest


# ---------------------------------------------------------------------------
# Krita integration (optional)
# ---------------------------------------------------------------------------

try:
    from krita import Krita  # type: ignore[import-untyped]

    def apply_style_to_selection(
        preset: str = "anime",
        strength: float | None = None,
    ) -> None:
        """Apply a style preset to the current selection in Krita.

        The styled region is placed on a new layer.
        """
        from PIL import Image  # type: ignore[import-untyped]

        if preset not in STYLE_PRESETS:
            raise ValueError(
                f"Unknown preset '{preset}'. "
                f"Available: {', '.join(STYLE_PRESETS)}"
            )

        cfg = STYLE_PRESETS[preset]
        weight = strength or cfg["weight"]
        denoise = cfg["denoise"]

        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            raise RuntimeError("No active document")

        w, h = doc.width(), doc.height()
        layer = doc.activeNode()
        pixel_data = layer.pixelData(0, 0, w, h)

        img = Image.frombytes("RGBA", (w, h), pixel_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        content_name = _upload_image_bytes(buf.getvalue(), "krita_content.png")

        # For preset mode, use the content image as its own light style ref
        # (the IPAdapter weight + denoise do the actual stylization)
        style_name = content_name

        workflow = _build_style_workflow(content_name, style_name, weight, denoise)
        prompt_id = _queue_prompt(workflow)
        out_files = _wait_for_result(prompt_id)

        if out_files:
            result_data = _download_output(out_files[0])
            result_img = Image.open(io.BytesIO(result_data))
            new_layer = doc.createNode(f"Style: {preset}", "paintlayer")
            new_layer.setPixelData(
                result_img.tobytes(), 0, 0, result_img.width, result_img.height
            )
            doc.rootNode().addChildNode(new_layer, None)
            doc.refreshProjection()
            log.info("Style '%s' applied on new layer", preset)

except ImportError:
    pass  # Not inside Krita


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply style transfer via ComfyUI IPAdapter"
    )
    parser.add_argument(
        "--content", type=Path, required=True, help="Content image to stylize"
    )
    parser.add_argument(
        "--style", type=Path, required=True, help="Style reference image"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output path (default: auto)"
    )
    parser.add_argument(
        "--strength",
        type=float,
        default=DEFAULT_STRENGTH,
        help=f"Style strength 0.0-1.0 (default: {DEFAULT_STRENGTH})",
    )
    parser.add_argument(
        "--denoise",
        type=float,
        default=DEFAULT_DENOISE,
        help=f"Denoise level 0.0-1.0 (default: {DEFAULT_DENOISE})",
    )
    parser.add_argument(
        "--preset",
        choices=list(STYLE_PRESETS.keys()),
        help="Use a built-in style preset (overrides --strength/--denoise)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would happen"
    )
    parser.add_argument(
        "--list-presets", action="store_true", help="List available style presets"
    )

    args = parser.parse_args()

    if args.list_presets:
        print("\nAvailable style presets:")
        for name, cfg in STYLE_PRESETS.items():
            print(f"  {name:12s} — {cfg['description']} (weight={cfg['weight']}, denoise={cfg['denoise']})")
        sys.exit(0)

    if args.preset:
        preset_cfg = STYLE_PRESETS[args.preset]
        args.strength = preset_cfg["weight"]
        args.denoise = preset_cfg["denoise"]

    apply_style(
        content_path=args.content,
        style_path=args.style,
        output_path=args.output,
        strength=args.strength,
        denoise=args.denoise,
        dry_run=args.dry_run,
    )
