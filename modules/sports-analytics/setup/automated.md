# sports-analytics — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

**There is no automated setup script for this module.** The closest thing is a Python dependency
install:

```bash
pip install -r modules/sports-analytics/requirements.txt
```

That is the only committed automation. Camera calibration, model weights, and OBS wiring are all
manual.

## What exists

Six real Python files (~895 lines total):

| File | Purpose |
|---|---|
| `golf-tracer/tracer.py` | Shot tracing |
| `golf-tracer/ndi_output.py` | NDI output to OBS |
| `golf-tracer/replay.py` | Replay |
| `pose-estimation/yolo_pose.py` | YOLO pose |
| `pose-estimation/posture_screen.py` | Posture screening |
| `pose-estimation/mediapipe_swing.py` | Swing analysis |

Each is run directly with `python`. There is no launcher, service, or Make target.

## What automation would take

A `make sports-setup` target could create a venv and install requirements. Model weights cannot be
committed (`CLAUDE.md` §10), and camera calibration is physical — inherently manual.

## Mobile replay (the app path)

Creator Extend is specified to add mobile replay control: trigger instant slow-motion replays
from a phone, scrub shot traces, and share annotated swing breakdowns. The tracer keeps running
locally on the GPU — the app is a remote control, not a processing path.

**Specified, not shipped.** `CLAUDE.md` §11 has this module at `scaffolded` and `docs/AUDIT.md`
records both desktop apps as lacking a complete build scaffold. The local replay buffer in
`golf-tracer/replay.py` is real and works today without any app.

