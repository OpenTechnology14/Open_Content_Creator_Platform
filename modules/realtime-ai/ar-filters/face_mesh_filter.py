#!/usr/bin/env python3
"""Realtime AR face filter — Snapchat-lens-style sprite overlay.

Webcam -> MediaPipe Face Mesh -> anchor a sprite (RGBA PNG) to face
landmarks (eye corners / nose bridge) via an affine transform ->
alpha-composite -> virtual camera, for OBS to consume as a normal video
source.

This is a different genre from deepfacelive/deep-live-cam/liveportrait,
which do face-swap and portrait animation. This module overlays a
graphic tracked to the face — glasses, ears, masks — it never replaces
or reshapes the face itself, so none of realtime-ai/README.md's face-swap consent
requirements apply to it.

Usage:
    python3 face_mesh_filter.py --filter filters/glasses.json
    python3 face_mesh_filter.py --camera 0 --filter filters/glasses.json --fps-cap 30

Requirements:
    pip install opencv-python mediapipe pyvirtualcam numpy
    Virtual camera: OBS Virtual Camera (Windows/Mac) or v4l2loopback (Linux)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import cv2
import numpy as np

try:
    import mediapipe as mp
except ImportError:
    mp = None  # type: ignore[assignment]

log = logging.getLogger("face_mesh_filter")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


def load_filter(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    sprite_path = manifest_path.parent / manifest["sprite"]
    sprite = cv2.imread(str(sprite_path), cv2.IMREAD_UNCHANGED)
    if sprite is None:
        raise FileNotFoundError(
            f"Sprite not found: {sprite_path}. Filter art isn't shipped in-repo "
            "(see assets/ in this module's README) — add your own RGBA PNG there."
        )
    if sprite.ndim != 3 or sprite.shape[2] != 4:
        raise ValueError(f"Sprite must have an alpha channel (RGBA): {sprite_path}")
    manifest["_sprite"] = sprite
    return manifest


def _landmark_px(landmarks, idx: int, width: int, height: int) -> np.ndarray:
    lm = landmarks[idx]
    return np.array([lm.x * width, lm.y * height], dtype=np.float32)


def composite_sprite(
    frame: np.ndarray, sprite: np.ndarray, center: np.ndarray, angle_deg: float, scale: float
) -> np.ndarray:
    """Rotate/scale/translate an RGBA sprite onto frame at center, alpha-blended."""
    sh, sw = sprite.shape[:2]
    out_w, out_h = max(int(sw * scale), 1), max(int(sh * scale), 1)

    resized = cv2.resize(sprite, (out_w, out_h), interpolation=cv2.INTER_AREA)
    rot_mat = cv2.getRotationMatrix2D((out_w / 2, out_h / 2), -angle_deg, 1.0)
    rotated = cv2.warpAffine(
        resized,
        rot_mat,
        (out_w, out_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    fh, fw = frame.shape[:2]
    x0 = int(center[0] - out_w / 2)
    y0 = int(center[1] - out_h / 2)

    src_x0, src_y0 = max(0, -x0), max(0, -y0)
    dst_x0, dst_y0 = max(0, x0), max(0, y0)
    dst_x1, dst_y1 = min(fw, x0 + out_w), min(fh, y0 + out_h)
    if dst_x1 <= dst_x0 or dst_y1 <= dst_y0:
        return frame
    src_x1 = src_x0 + (dst_x1 - dst_x0)
    src_y1 = src_y0 + (dst_y1 - dst_y0)

    region = rotated[src_y0:src_y1, src_x0:src_x1]
    alpha = region[:, :, 3:4].astype(np.float32) / 255.0
    frame_region = frame[dst_y0:dst_y1, dst_x0:dst_x1].astype(np.float32)
    blended = frame_region * (1 - alpha) + region[:, :, :3].astype(np.float32) * alpha
    frame[dst_y0:dst_y1, dst_x0:dst_x1] = blended.astype(np.uint8)
    return frame


def run_filter(camera_index: int, manifest_path: Path, width: int, height: int, fps_cap: int) -> None:
    if mp is None:
        log.error("mediapipe not installed. pip install mediapipe")
        sys.exit(1)

    filt = load_filter(manifest_path)
    anchors = filt["anchor_landmarks"]
    scale_mult = filt.get("scale_multiplier", 1.0)
    v_offset = filt.get("vertical_offset_frac", 0.0)

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not cap.isOpened():
        log.error("Cannot open camera %d", camera_index)
        sys.exit(1)

    try:
        import pyvirtualcam

        vcam = pyvirtualcam.Camera(width=width, height=height, fps=fps_cap)
        log.info("Virtual camera opened: %s (%dx%d @ %d fps)", vcam.device, width, height, fps_cap)
    except ImportError:
        log.error("pyvirtualcam not installed. pip install pyvirtualcam")
        sys.exit(1)
    except Exception as e:
        log.error("Cannot open virtual camera: %s", e)
        log.info("Windows/Mac: install OBS Virtual Camera. Linux: install v4l2loopback.")
        sys.exit(1)

    frame_interval = 1.0 / fps_cap
    log.info("Filter '%s' running. Press Ctrl+C to stop.", filt.get("name", manifest_path.stem))

    try:
        while True:
            loop_start = time.time()
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.resize(frame, (width, height))

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                left = _landmark_px(landmarks, anchors["left"], width, height)
                right = _landmark_px(landmarks, anchors["right"], width, height)
                center_idx = anchors.get("center")
                center = (
                    _landmark_px(landmarks, center_idx, width, height)
                    if center_idx is not None
                    else (left + right) / 2
                )
                center[1] += v_offset * height

                eye_dist = float(np.linalg.norm(right - left))
                angle = float(np.degrees(np.arctan2(right[1] - left[1], right[0] - left[0])))
                sprite = filt["_sprite"]
                base_scale = eye_dist / max(sprite.shape[1] * 0.5, 1.0)
                frame = composite_sprite(frame, sprite, center, angle, base_scale * scale_mult)

            vcam.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            elapsed = time.time() - loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        log.info("Stopping filter...")
    finally:
        cap.release()
        vcam.close()
        face_mesh.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Realtime AR face filter (Snapchat-lens-style)")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--filter", type=Path, required=True, help="Path to a filter manifest JSON")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps-cap", type=int, default=30)
    args = parser.parse_args()

    run_filter(args.camera, args.filter, args.width, args.height, args.fps_cap)
