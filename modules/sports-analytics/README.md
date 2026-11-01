# sports-analytics

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

Sports / Analytics layer (Roadmap §3). OpenCV + YOLO + MediaPipe pipelines for golf tracing, swing analysis, replay systems.

## Core technologies

| Tool | Version | Purpose |
|---|---|---|
| OpenCV | 4.9+ | Frame capture, filtering, drawing |
| Ultralytics YOLO | YOLOv8 or YOLO11 | Ball / club / person detection |
| MediaPipe | 0.10+ | Pose estimation (swing analysis) |
| NumPy | latest | Trajectory math |
| FilterPy | latest | Kalman filter for smoothing |

```bash
pip install -r requirements.txt
```

## Config docs

- [`golf-tracer/README.md`](golf-tracer/README.md) — trajectory math, camera calibration, `calibration.json`
- [`models/README.md`](models/README.md) — model selection, fine-tuning, where weights live
- [`pose-estimation/README.md`](pose-estimation/README.md) — swing and posture analysis

