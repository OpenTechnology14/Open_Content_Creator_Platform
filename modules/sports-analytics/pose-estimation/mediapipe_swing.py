"""MediaPipe-based golf swing analyzer.

Inputs a video (or webcam) and emits per-frame keypoint records. Designed
to feed downstream analytics (tempo, plane angle, hip-shoulder separation).

This module focuses on data extraction. Visualization belongs in tracer.py
or your overlay pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

try:
    import mediapipe as mp
except ImportError:
    mp = None  # type: ignore[assignment]


def analyze(source: str | int, out_path: str | None = None) -> list[dict]:
    if mp is None:
        raise RuntimeError("mediapipe not installed")

    pose = mp.solutions.pose.Pose(
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    )
    cap = cv2.VideoCapture(source)
    records: list[dict] = []
    frame_idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            if results.pose_landmarks:
                kps = [
                    {"x": lm.x, "y": lm.y, "z": lm.z, "v": lm.visibility}
                    for lm in results.pose_landmarks.landmark
                ]
                records.append({"frame": frame_idx, "keypoints": kps})
            frame_idx += 1
    finally:
        cap.release()
        pose.close()

    if out_path:
        Path(out_path).write_text(json.dumps(records))
    return records


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    src: int | str = int(args.source) if args.source.isdigit() else args.source
    records = analyze(src, args.out)
    print(f"frames processed: {len(records)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
