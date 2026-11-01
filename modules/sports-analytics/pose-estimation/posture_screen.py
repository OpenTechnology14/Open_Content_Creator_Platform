"""Still-image posture screening analyzer.

Takes a single uploaded photo (front, side, or back view) and emits body
landmarks plus derived posture metrics — the PostureScreen-style workflow,
built on the same MediaPipe Pose model as mediapipe_swing.py, but for one
static frame instead of a video stream.

Usage:
    python3 posture_screen.py --image photo.jpg --view side
    python3 posture_screen.py --image photo.jpg --view front --out result.json

With no --out, the JSON result is printed to stdout (this is what the Tauri
posture_analyze command reads).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Optional

import cv2

try:
    import mediapipe as mp
except ImportError:
    mp = None  # type: ignore[assignment]

# MediaPipe Pose landmark indices used below.
NOSE = 0
LEFT_EAR, RIGHT_EAR = 7, 8
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_HIP, RIGHT_HIP = 23, 24

# Thresholds (degrees / normalized fraction of image width) — tune per
# clinical guidance, not derived from any single source. Kept as named
# constants rather than inline magic numbers so they're one place to adjust.
SHOULDER_TILT_WARN_DEG = 3.0
SHOULDER_TILT_FLAG_DEG = 6.0
HIP_TILT_WARN_DEG = 3.0
HIP_TILT_FLAG_DEG = 6.0
LATERAL_SHIFT_WARN_FRAC = 0.02
LATERAL_SHIFT_FLAG_FRAC = 0.04
FORWARD_HEAD_WARN_DEG = 10.0
FORWARD_HEAD_FLAG_DEG = 15.0
TRUNK_LEAN_WARN_DEG = 4.0
TRUNK_LEAN_FLAG_DEG = 8.0
MIN_VISIBILITY = 0.5


def _lm_point(landmarks, idx: int) -> dict:
    lm = landmarks[idx]
    return {"x": lm.x, "y": lm.y, "z": lm.z, "v": lm.visibility}


def _angle_from_horizontal_deg(p1: dict, p2: dict) -> float:
    dx = p2["x"] - p1["x"]
    dy = p2["y"] - p1["y"]
    return math.degrees(math.atan2(dy, dx))


def _angle_from_vertical_deg(top: dict, bottom: dict) -> float:
    dx = bottom["x"] - top["x"]
    dy = bottom["y"] - top["y"]
    return math.degrees(math.atan2(dx, dy))


def _flag(value: float, warn: float, bad: float, label: str) -> Optional[dict]:
    magnitude = abs(value)
    if magnitude >= bad:
        return {"severity": "flag", "label": label, "value": round(value, 2)}
    if magnitude >= warn:
        return {"severity": "warning", "label": label, "value": round(value, 2)}
    return None


def compute_posture_metrics(landmarks, view: str) -> dict:
    """Derive posture metrics from a single frame's landmarks.

    view: "front", "back", or "side" — side view uses whichever half of the
    body (left/right) has higher-visibility landmarks, since only one side
    faces the camera.
    """
    metrics: dict = {}
    flags: list[dict] = []

    if view in ("front", "back"):
        l_sh, r_sh = _lm_point(landmarks, LEFT_SHOULDER), _lm_point(landmarks, RIGHT_SHOULDER)
        l_hip, r_hip = _lm_point(landmarks, LEFT_HIP), _lm_point(landmarks, RIGHT_HIP)

        shoulder_tilt = _angle_from_horizontal_deg(l_sh, r_sh)
        hip_tilt = _angle_from_horizontal_deg(l_hip, r_hip)
        shoulder_mid_x = (l_sh["x"] + r_sh["x"]) / 2
        hip_mid_x = (l_hip["x"] + r_hip["x"]) / 2
        lateral_shift = shoulder_mid_x - hip_mid_x

        metrics["shoulder_tilt_deg"] = round(shoulder_tilt, 2)
        metrics["hip_tilt_deg"] = round(hip_tilt, 2)
        metrics["lateral_shift_frac"] = round(lateral_shift, 4)

        f = _flag(shoulder_tilt, SHOULDER_TILT_WARN_DEG, SHOULDER_TILT_FLAG_DEG, "shoulders uneven")
        if f:
            flags.append(f)
        f = _flag(hip_tilt, HIP_TILT_WARN_DEG, HIP_TILT_FLAG_DEG, "hips uneven")
        if f:
            flags.append(f)
        f = _flag(lateral_shift, LATERAL_SHIFT_WARN_FRAC, LATERAL_SHIFT_FLAG_FRAC, "trunk shifted laterally")
        if f:
            flags.append(f)

    elif view == "side":
        left_visible = landmarks[LEFT_SHOULDER].visibility + landmarks[LEFT_HIP].visibility
        right_visible = landmarks[RIGHT_SHOULDER].visibility + landmarks[RIGHT_HIP].visibility
        if left_visible >= right_visible:
            ear, shoulder, hip = LEFT_EAR, LEFT_SHOULDER, LEFT_HIP
        else:
            ear, shoulder, hip = RIGHT_EAR, RIGHT_SHOULDER, RIGHT_HIP

        ear_pt = _lm_point(landmarks, ear)
        shoulder_pt = _lm_point(landmarks, shoulder)
        hip_pt = _lm_point(landmarks, hip)

        forward_head = _angle_from_vertical_deg(shoulder_pt, ear_pt)
        trunk_lean = _angle_from_vertical_deg(hip_pt, shoulder_pt)

        metrics["forward_head_deg"] = round(forward_head, 2)
        metrics["trunk_lean_deg"] = round(trunk_lean, 2)
        metrics["side_used"] = "left" if left_visible >= right_visible else "right"

        f = _flag(forward_head, FORWARD_HEAD_WARN_DEG, FORWARD_HEAD_FLAG_DEG, "forward head posture")
        if f:
            flags.append(f)
        f = _flag(trunk_lean, TRUNK_LEAN_WARN_DEG, TRUNK_LEAN_FLAG_DEG, "trunk leaning off vertical")
        if f:
            flags.append(f)
    else:
        raise ValueError(f"Unknown view: {view!r} (expected front, side, or back)")

    return {"metrics": metrics, "flags": flags}


def analyze_image(image_path: str, view: str, out_path: str | None = None) -> dict:
    if mp is None:
        raise RuntimeError("mediapipe not installed")

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    height, width = image.shape[:2]

    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    )
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
    finally:
        pose.close()

    if not results.pose_landmarks:
        result = {
            "ok": False,
            "error": "No person detected in image.",
            "image_width": width,
            "image_height": height,
        }
        if out_path:
            Path(out_path).write_text(json.dumps(result))
        return result

    landmarks = results.pose_landmarks.landmark
    keypoints = [
        {"x": lm.x, "y": lm.y, "z": lm.z, "v": lm.visibility} for lm in landmarks
    ]

    low_visibility = [
        idx
        for idx in (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP)
        if landmarks[idx].visibility < MIN_VISIBILITY
    ]

    analysis = compute_posture_metrics(landmarks, view)

    result = {
        "ok": True,
        "view": view,
        "image_width": width,
        "image_height": height,
        "keypoints": keypoints,
        "metrics": analysis["metrics"],
        "flags": analysis["flags"],
        "low_visibility_landmarks": low_visibility,
    }

    if out_path:
        Path(out_path).write_text(json.dumps(result))
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--view", required=True, choices=["front", "side", "back"])
    p.add_argument("--out", default=None, help="Write JSON here instead of stdout")
    args = p.parse_args()

    try:
        result = analyze_image(args.image, args.view, args.out)
    except Exception as exc:  # surfaced to the caller, not swallowed
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    if not args.out:
        print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
