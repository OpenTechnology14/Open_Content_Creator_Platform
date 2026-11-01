# sports-analytics — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

Golf shot tracing, pose estimation, and swing analysis from an ordinary camera — no launch monitor.

## Prerequisites

- A camera that can deliver a high, stable frame rate. Ball tracking is frame-rate bound: 120 fps
  gives you roughly twice the trajectory samples of 60 fps.
- NVIDIA GPU for YOLO inference at usable speed.
- Good, even lighting. Motion blur destroys small-object detection more than resolution does.

```bash
pip install -r modules/sports-analytics/requirements.txt
```

Core stack: OpenCV, YOLO (Ultralytics), MediaPipe.

## Camera placement and calibration

Fixed position, fixed focal length, locked exposure. Anything that moves between calibration and
capture invalidates the trajectory math. Calibrate once per physical setup and re-calibrate if the
camera is bumped.

## Pipeline

Capture → detect ball → associate detections across frames into a track → fit a trajectory →
render the tracer → output to OBS.

`golf-tracer/tracer.py` is the entry point. `golf-tracer/ndi_output.py` sends the composited
result to OBS over NDI. `golf-tracer/replay.py` handles replay.

### Frame-skip and realtime tradeoffs

Realtime tracing and accurate tracing pull against each other. Skipping frames raises throughput
and costs trajectory fidelity. Decide which you are optimising for before tuning — a tracer that
is smooth but wrong is worse than one that lags.

## Pose estimation and swing analysis

- `pose-estimation/yolo_pose.py` — YOLO-based pose
- `pose-estimation/mediapipe_swing.py` — MediaPipe swing analysis
- `pose-estimation/posture_screen.py` — posture screening

## Models

Weights go outside the repo. Never commit them (`CLAUDE.md` §10).

## Output to OBS

NDI is the path of least resistance — `ndi_output.py` publishes a stream that OBS picks up as an
NDI source.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] The tracer draws a plausible arc on recorded footage before you try it live
- [ ] Pose landmarks track through a full swing without dropping
- [ ] OBS shows the NDI source at the expected frame rate

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.
## Troubleshooting

- **Ball not detected** — motion blur. Raise shutter speed and add light before touching the model.
- **Tracer arc jitters** — too few trajectory samples; raise capture fps or reduce frame-skip.
- **NDI source missing in OBS** — the NDI runtime is not installed, or a firewall is blocking
  discovery on the local network.
