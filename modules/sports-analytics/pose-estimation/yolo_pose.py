#!/usr/bin/env python3
"""YOLO-Pose swing analysis — GPU-accelerated pose estimation.

Uses Ultralytics YOLOv8-Pose (or YOLO11-Pose) for 17-keypoint detection,
then computes golf swing metrics from keypoint trajectories.

Higher accuracy than MediaPipe for rapid motion, but requires a GPU.

Usage:
    python yolo_pose.py --video swing.mp4
    python yolo_pose.py --video swing.mp4 --model yolov8m-pose.pt --show
    python yolo_pose.py --camera 0  # live webcam

Requirements:
    pip install ultralytics opencv-python numpy
"""

from __future__ import annotations

import argparse
import logging
import math
import sys

import cv2
import numpy as np

log = logging.getLogger("yolo_pose")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# COCO pose keypoint indices
NOSE, L_EYE, R_EYE = 0, 1, 2
L_EAR, R_EAR = 3, 4
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16


def angle_between(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Compute the angle at point b between segments ba and bc, in degrees."""
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1, 1))))


def compute_swing_metrics(keypoints_over_time: list[np.ndarray]) -> dict:
    """Compute golf swing metrics from a sequence of 17-keypoint arrays.

    Each entry in keypoints_over_time is shape (17, 2) — x,y per keypoint.

    Returns dict of metric name → list of per-frame values.
    """
    metrics = {
        "shoulder_rotation_deg": [],
        "hip_rotation_deg": [],
        "left_elbow_angle_deg": [],
        "right_elbow_angle_deg": [],
        "spine_angle_deg": [],
    }

    for kps in keypoints_over_time:
        if kps is None or len(kps) < 17:
            for k in metrics:
                metrics[k].append(None)
            continue

        # Shoulder rotation: angle of shoulder line relative to horizontal
        shoulder_vec = kps[R_SHOULDER] - kps[L_SHOULDER]
        shoulder_angle = math.degrees(math.atan2(shoulder_vec[1], shoulder_vec[0]))
        metrics["shoulder_rotation_deg"].append(round(shoulder_angle, 1))

        # Hip rotation
        hip_vec = kps[R_HIP] - kps[L_HIP]
        hip_angle = math.degrees(math.atan2(hip_vec[1], hip_vec[0]))
        metrics["hip_rotation_deg"].append(round(hip_angle, 1))

        # Left elbow angle
        left_elbow = angle_between(kps[L_SHOULDER], kps[L_ELBOW], kps[L_WRIST])
        metrics["left_elbow_angle_deg"].append(round(left_elbow, 1))

        # Right elbow angle
        right_elbow = angle_between(kps[R_SHOULDER], kps[R_ELBOW], kps[R_WRIST])
        metrics["right_elbow_angle_deg"].append(round(right_elbow, 1))

        # Spine angle (midpoint of shoulders to midpoint of hips, vs vertical)
        mid_shoulder = (kps[L_SHOULDER] + kps[R_SHOULDER]) / 2
        mid_hip = (kps[L_HIP] + kps[R_HIP]) / 2
        spine_vec = mid_shoulder - mid_hip
        spine_angle = math.degrees(math.atan2(spine_vec[0], -spine_vec[1]))  # 0 = upright
        metrics["spine_angle_deg"].append(round(spine_angle, 1))

    return metrics


def run_analysis(
    source: str | int,
    model_name: str = "yolov8n-pose.pt",
    show: bool = False,
    output_path: str | None = None,
) -> dict:
    """Run YOLO-Pose on a video/camera source and compute swing metrics."""
    try:
        from ultralytics import YOLO  # type: ignore[import-untyped]
    except ImportError:
        log.error("ultralytics not installed. pip install ultralytics")
        sys.exit(1)

    model = YOLO(model_name)
    log.info("Loaded model: %s", model_name)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        log.error("Cannot open source: %s", source)
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    all_keypoints = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)

        kps = None
        if results and results[0].keypoints is not None:
            keypoints_data = results[0].keypoints.xy
            if len(keypoints_data) > 0:
                kps = keypoints_data[0].cpu().numpy()  # First person only

                # Draw skeleton on frame
                annotated = results[0].plot()
                if show:
                    cv2.imshow("YOLO Pose", annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                if writer:
                    writer.write(annotated)

        all_keypoints.append(kps)
        frame_count += 1

    cap.release()
    if writer:
        writer.release()
    if show:
        cv2.destroyAllWindows()

    metrics = compute_swing_metrics(all_keypoints)

    # Summary
    log.info("Processed %d frames at %.1f fps", frame_count, fps)
    for name, values in metrics.items():
        valid = [v for v in values if v is not None]
        if valid:
            log.info("  %s: min=%.1f, max=%.1f, range=%.1f",
                     name, min(valid), max(valid), max(valid) - min(valid))

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO-Pose golf swing analysis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--video", type=str, help="Path to video file")
    group.add_argument("--camera", type=int, help="Camera index for live analysis")
    parser.add_argument("--model", default="yolov8n-pose.pt", help="YOLO pose model")
    parser.add_argument("--show", action="store_true", help="Display annotated video")
    parser.add_argument("--output", type=str, help="Save annotated video to file")
    args = parser.parse_args()

    source = args.video if args.video else args.camera
    run_analysis(source, model_name=args.model, show=args.show, output_path=args.output)
