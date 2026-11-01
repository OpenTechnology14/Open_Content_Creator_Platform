"""Golf shot tracer.

Pipeline:
  webcam/video → YOLO ball detection → Kalman smoothing → trajectory render
  → virtual cam (OBS source) + event emission to FastAPI /events.

This is a reference implementation. Real-world calibration, ball/club
disambiguation, and replay buffering live in sibling modules.

Run:
    python tracer.py --source 0
    python tracer.py --source path/to/swing.mp4 --emit-events
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass, field

import cv2
import numpy as np
from filterpy.kalman import KalmanFilter
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None  # type: ignore[assignment]


# ─── Trajectory state ───────────────────────────────────────────────────


@dataclass
class Trail:
    """Rolling history of (x, y) points for one detected ball."""
    points: list[tuple[int, int]] = field(default_factory=list)
    max_len: int = 120
    last_seen_ts: float = 0.0

    def add(self, x: int, y: int) -> None:
        self.points.append((x, y))
        if len(self.points) > self.max_len:
            self.points = self.points[-self.max_len:]
        self.last_seen_ts = time.time()


def make_kalman() -> KalmanFilter:
    """Constant-velocity Kalman filter for (x, y) pixel coords."""
    kf = KalmanFilter(dim_x=4, dim_z=2)
    kf.F = np.array([[1, 0, 1, 0],
                     [0, 1, 0, 1],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]], dtype=np.float32)
    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]], dtype=np.float32)
    kf.P *= 1000.0
    kf.R *= 5.0
    kf.Q *= 0.1
    return kf


# ─── Rendering ──────────────────────────────────────────────────────────


def draw_trail(frame: np.ndarray, trail: Trail, color=(0, 255, 255)) -> None:
    if len(trail.points) < 2:
        return
    pts = np.array(trail.points, dtype=np.int32)
    for i in range(1, len(pts)):
        thickness = max(1, int(8 * (i / len(pts))))
        cv2.line(frame, tuple(pts[i - 1]), tuple(pts[i]), color, thickness, cv2.LINE_AA)
    cv2.circle(frame, tuple(pts[-1]), 8, (255, 255, 255), -1, cv2.LINE_AA)


# ─── Detection ──────────────────────────────────────────────────────────


def detect_ball(model, frame: np.ndarray, conf: float = 0.35) -> tuple[int, int] | None:
    """Run YOLO and return the best 'sports ball' / golf-ball detection center."""
    results = model.predict(frame, conf=conf, verbose=False)
    best = None
    best_conf = 0.0
    for r in results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls = int(box.cls.item())
            label = model.names.get(cls, "")
            # COCO 'sports ball' is class 32 in default YOLOv8 weights.
            if "ball" not in label.lower():
                continue
            c = float(box.conf.item())
            if c > best_conf:
                best_conf = c
                xyxy = box.xyxy[0].cpu().numpy()
                cx = int((xyxy[0] + xyxy[2]) / 2)
                cy = int((xyxy[1] + xyxy[3]) / 2)
                best = (cx, cy)
    return best


# ─── Event emission ─────────────────────────────────────────────────────


def emit_shot_event(api_url: str, api_key: str, stream_id: str | None, trail: Trail) -> None:
    import httpx

    try:
        with httpx.Client(timeout=2.0) as client:
            client.post(
                f"{api_url}/events",
                headers={"x-api-key": api_key},
                json={
                    "source": "golf-tracer",
                    "kind": "shot_detected",
                    "stream_id": stream_id,
                    "data": {
                        "point_count": len(trail.points),
                        "first_point": trail.points[0] if trail.points else None,
                        "last_point": trail.points[-1] if trail.points else None,
                    },
                },
            )
    except Exception as e:
        logger.warning("event emit failed: {}", e)


# ─── Main loop ──────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="0", help="webcam index or video path")
    p.add_argument("--model", default="yolov8n.pt", help="ultralytics weights")
    p.add_argument("--conf", type=float, default=0.35)
    p.add_argument("--display", action="store_true", help="open a preview window")
    p.add_argument("--emit-events", action="store_true")
    p.add_argument("--stream-id", default=None)
    p.add_argument("--virtual-cam", action="store_true",
                   help="write annotated frames to a virtual camera (OBS source)")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if YOLO is None:
        logger.error("ultralytics not installed. pip install ultralytics")
        return 2

    source: int | str = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error("could not open source: {}", source)
        return 1

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    logger.info("capture: {}x{} @ {:.1f}fps", w, h, fps)

    model = YOLO(args.model)
    kf = make_kalman()
    kf_initialized = False
    trail = Trail()
    last_emit = 0.0

    api_url = os.environ.get("API_URL", "http://127.0.0.1:8000")
    api_key = os.environ.get("HCP_API_KEY", "")

    vcam = None
    if args.virtual_cam:
        try:
            import pyvirtualcam  # type: ignore
            vcam = pyvirtualcam.Camera(width=w, height=h, fps=int(fps))
            logger.info("virtual cam device: {}", vcam.device)
        except Exception as e:
            logger.error("virtual cam init failed: {}", e)
            vcam = None

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            detection = detect_ball(model, frame, conf=args.conf)
            if detection is not None:
                x, y = detection
                if not kf_initialized:
                    kf.x = np.array([x, y, 0, 0], dtype=np.float32)
                    kf_initialized = True
                else:
                    kf.predict()
                    kf.update(np.array([x, y], dtype=np.float32))
                px, py = int(kf.x[0]), int(kf.x[1])
                trail.add(px, py)
            elif kf_initialized:
                kf.predict()
                # Drop the trail if we haven't seen the ball for >1s.
                if time.time() - trail.last_seen_ts > 1.0 and trail.points:
                    if args.emit_events and time.time() - last_emit > 2.0:
                        emit_shot_event(api_url, api_key, args.stream_id, trail)
                        last_emit = time.time()
                    trail = Trail()
                    kf_initialized = False

            draw_trail(frame, trail)

            if vcam is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                vcam.send(rgb)
                vcam.sleep_until_next_frame()

            if args.display:
                cv2.imshow("golf-tracer", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        if vcam is not None:
            vcam.close()
        if args.display:
            cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
