# golf-tracer

Config and reference notes for the shot tracer. Setup steps live in
[`../setup/manual.md`](../setup/manual.md).

| File | Purpose |
|---|---|
| `tracer.py` | Detect → track → fit → render |
| `ndi_output.py` | NDI sender, consumed by the OBS NDI plugin |
| `replay.py` | Replay buffer — last N frames, instant slow-motion on a hotkey |
| `calibration.json` | Pixel-to-metre mapping for this physical camera setup — **template only, not read by any code yet** (verified 2026-09-01, `P-040`); see below |

## Camera placement and calibration

**`calibration.json` is not consumed by `tracer.py`, `replay.py`, or `ndi_output.py` today** —
none of the three reads it. `tracer.py`'s Kalman filter and polynomial fit both operate entirely
in pixel space; nothing converts a trajectory to real-world units. Recording your setup's
`camera_matrix`/`ground_plane` here is preparation for a not-yet-built conversion step (a
homography from `ground_plane`'s point correspondences via `cv2.findHomography`, undistortion via
`camera_matrix`/`dist_coeffs`), not something that changes the tracer's behavior yet. The rest of
this section describes the intended calibration procedure for when that step exists.

For a 2D tracer:

- Camera **perpendicular to the ball's flight plane** — down-the-line for swings, behind the tee
  for trajectory.
- Camera **fixed for the whole session**. Any movement invalidates the pixel-to-metre mapping,
  and nothing downstream can detect that it happened.
- Calibrate scale once by placing an object of known size in frame (a tee marker, a club length)
  and recording the conversion in `calibration.json`.

Re-calibrate whenever the camera is bumped or moved. A stale `calibration.json` produces a tracer
that looks right and measures wrong — the worst failure mode here.

## Trajectory math

Per-frame detections give `(x, y, t)` points. Turning those into a trajectory:

1. **Kalman filter** over `(x, y, vx, vy)` state. Handles occlusion — a briefly invisible ball —
   gracefully, which is why it comes before the fit.
2. **Polynomial fit** on the smoothed points; quadratic in `y(x)` for a single-camera 2D tracer.
3. Draw the polynomial as a Bézier or a simple polyline overlay.

A 3D tracer (Trackman-style) needs stereo cameras, intrinsic and extrinsic calibration, and
triangulation. Out of scope — the single-camera 2D path is what this module implements.

## Frame-skip and realtime trade-offs

Rough throughput on a single RTX 3060:

| Model | fps |
|---|---|
| YOLOv8n | ~120 |
| YOLOv8m | ~40 |
| YOLOv8x | ~15 |

For realtime OBS output:

- Prefer YOLOv8n or YOLO11n with your fine-tuned weights — see [`../models/README.md`](../models/README.md).
- Set `CAP_PROP_BUFFERSIZE = 1` on `cv2.VideoCapture` to stop latency building up.
- **If you fall behind, drop frames rather than queue.** The Kalman filter recovers from a gap;
  it cannot recover from output that is three seconds stale.

## Output to OBS

| Path | Trade-off |
|---|---|
| **Virtual camera** (`pyvirtualcam`) | Easiest. Write rendered frames, add as an OBS source. |
| **NDI** (`ndi_output.py`) | Best quality and lower latency — no codec re-encode. Needs the OBS NDI plugin. |
