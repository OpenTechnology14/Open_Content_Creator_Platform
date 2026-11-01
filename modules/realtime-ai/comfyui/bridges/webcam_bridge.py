#!/usr/bin/env python3
"""Webcam → ComfyUI → Virtual Camera bridge.

A standalone Python process that:
1. Captures frames from a webcam via OpenCV
2. Sends each frame to a running ComfyUI instance via the API
3. Receives the processed frame
4. Writes it to a virtual camera for OBS to consume

This is the "external bridge" approach — simpler than in-process ComfyUI
webcam nodes, but adds ~20-50 ms of transfer overhead.

Usage:
    python webcam_bridge.py
    python webcam_bridge.py --camera 0 --workflow realtime-lcm-stylize-v1.json
    python webcam_bridge.py --width 512 --height 512 --fps-cap 15

Requirements:
    pip install opencv-python requests pyvirtualcam numpy
    ComfyUI running at http://127.0.0.1:8188
    pyvirtualcam requires: OBS Virtual Camera (Windows) or v4l2loopback (Linux)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
import requests

log = logging.getLogger("webcam_bridge")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

COMFYUI_URL = "http://127.0.0.1:8188"


def upload_frame(frame: np.ndarray) -> str:
    """Encode a frame as PNG and upload to ComfyUI. Returns remote filename."""
    _, buf = cv2.imencode(".png", frame)
    resp = requests.post(
        f"{COMFYUI_URL}/upload/image",
        files={"image": ("webcam_frame.png", buf.tobytes(), "image/png")},
    )
    resp.raise_for_status()
    return resp.json()["name"]


def queue_workflow(workflow: dict, image_name: str) -> str:
    """Inject the image name into the workflow and queue it. Returns prompt_id."""
    # Replace the LoadImage node's image field with our uploaded frame
    for node in workflow.values():
        if node.get("class_type") == "LoadImage":
            node["inputs"]["image"] = image_name
            break

    client_id = str(uuid.uuid4())
    resp = requests.post(
        f"{COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def wait_for_output(prompt_id: str, timeout: float = 10.0) -> bytes | None:
    """Poll ComfyUI history until the prompt completes. Returns image bytes."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
        data = resp.json()
        if prompt_id in data:
            outputs = data[prompt_id].get("outputs", {})
            for node_out in outputs.values():
                for img in node_out.get("images", []):
                    dl = requests.get(
                        f"{COMFYUI_URL}/view",
                        params={"filename": img["filename"], "type": "output"},
                    )
                    return dl.content
            return None
        time.sleep(0.05)  # 50ms poll — tight for realtime
    return None


def decode_image(data: bytes) -> np.ndarray:
    """Decode raw image bytes into an OpenCV BGR frame."""
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def run_bridge(
    camera_index: int = 0,
    workflow_path: str | None = None,
    width: int = 512,
    height: int = 512,
    fps_cap: int = 15,
) -> None:
    """Main bridge loop."""
    # Verify ComfyUI is reachable
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
    except requests.ConnectionError:
        log.error("Cannot reach ComfyUI at %s. Start it first.", COMFYUI_URL)
        sys.exit(1)

    # Load workflow
    if workflow_path:
        wf_path = Path(workflow_path)
    else:
        wf_path = Path(__file__).parent.parent / "workflows" / "realtime-lcm-stylize-v1.json"

    if not wf_path.exists():
        log.error("Workflow not found: %s", wf_path)
        log.info("Create a realtime workflow JSON first (see modules/realtime-ai/setup/manual.md).")
        sys.exit(1)

    workflow_template = json.loads(wf_path.read_text())

    # Open webcam
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        log.error("Cannot open camera %d", camera_index)
        sys.exit(1)

    # Open virtual camera
    try:
        import pyvirtualcam
        vcam = pyvirtualcam.Camera(width=width, height=height, fps=fps_cap)
        log.info("Virtual camera opened: %s (%dx%d @ %d fps)", vcam.device, width, height, fps_cap)
    except ImportError:
        log.error("pyvirtualcam not installed. pip install pyvirtualcam")
        sys.exit(1)
    except Exception as e:
        log.error("Cannot open virtual camera: %s", e)
        log.info("Windows: install OBS Virtual Camera. Linux: install v4l2loopback.")
        sys.exit(1)

    frame_interval = 1.0 / fps_cap
    frames_processed = 0
    start_time = time.time()

    log.info("Bridge running. Press Ctrl+C to stop.")

    try:
        while True:
            loop_start = time.time()

            ret, frame = cap.read()
            if not ret:
                log.warning("Camera read failed, retrying...")
                continue

            # Resize if needed
            frame = cv2.resize(frame, (width, height))

            # Upload → process → download
            try:
                remote_name = upload_frame(frame)
                workflow = json.loads(json.dumps(workflow_template))  # deep copy
                prompt_id = queue_workflow(workflow, remote_name)
                result = wait_for_output(prompt_id, timeout=5.0)

                if result:
                    output_frame = decode_image(result)
                    output_frame = cv2.resize(output_frame, (width, height))
                    # pyvirtualcam expects RGB, OpenCV gives BGR
                    vcam.send(cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB))
                else:
                    # If processing failed, pass through the original frame
                    vcam.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            except Exception as e:
                log.warning("Frame processing error: %s — passing through", e)
                vcam.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            frames_processed += 1
            if frames_processed % 30 == 0:
                elapsed = time.time() - start_time
                actual_fps = frames_processed / elapsed
                log.info("Processed %d frames — %.1f fps", frames_processed, actual_fps)

            # Rate limiting
            elapsed_frame = time.time() - loop_start
            sleep_time = frame_interval - elapsed_frame
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("Stopping bridge...")
    finally:
        cap.release()
        vcam.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Webcam → ComfyUI → Virtual Camera bridge")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--workflow", type=str, default=None, help="Path to ComfyUI workflow JSON")
    parser.add_argument("--width", type=int, default=512, help="Frame width (default: 512)")
    parser.add_argument("--height", type=int, default=512, help="Frame height (default: 512)")
    parser.add_argument("--fps-cap", type=int, default=15, help="Max FPS (default: 15)")
    args = parser.parse_args()

    run_bridge(
        camera_index=args.camera,
        workflow_path=args.workflow,
        width=args.width,
        height=args.height,
        fps_cap=args.fps_cap,
    )
