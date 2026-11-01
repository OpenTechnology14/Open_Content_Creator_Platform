# pose-estimation

Config and reference notes. Setup steps live in [`../setup/manual.md`](../setup/manual.md).

## Model choice

| Model | Runs on | Keypoints | Use when |
|---|---|---|---|
| **MediaPipe Pose** (`mediapipe_swing.py`) | CPU | 33 | Amateur swing analysis — fast, sufficient, no GPU contention with the tracer |
| **YOLOv8-Pose / YOLO11-Pose** (`yolo_pose.py`) | GPU | 17 (COCO) | Higher accuracy, when the GPU is free |

MediaPipe's CPU path matters more than it looks: the golf tracer already wants the GPU, so
putting pose on CPU keeps both running at once.

## Swing metrics

All derivable from keypoints over time:

- Shoulder rotation angle
- Hip rotation
- Hand path
- Takeaway tempo
- Downswing tempo

## posture_screen.py — same directory, different pipeline

`posture_screen.py` is a **still-image** body-alignment analyser: a front/side/back photo in,
shoulder tilt, hip tilt, and forward-head-posture measurements out. It shares the MediaPipe Pose
model with the swing scripts and nothing else — single photo, not video, and unrelated to golf.

It is wired into the Creator Extend desktop app's "Posture Screen" panel via
`apps/creator-extend/src-tauri/src/posture.rs`.

Do not assume changes to the swing pipeline affect it, or vice versa.
