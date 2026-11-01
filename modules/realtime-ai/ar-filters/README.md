# ar-filters

Realtime AR lens-style overlays — the Snapchat-filter genre. A sprite
(PNG with alpha) tracked to face-mesh landmarks and composited onto the
webcam feed in real time, output to a virtual camera for OBS.

**This is not `deepfacelive` / `deep-live-cam` / `liveportrait`.** Those
do face-swap and portrait animation — they replace or reshape the face
and carry [`realtime-ai`](../setup/manual.md)'s consent requirements. This module overlays a graphic
*on top of* your own face (glasses, ears, masks) and never touches the
face itself, so those consent requirements don't apply here.

## How it works

```
Webcam -> MediaPipe Face Mesh (landmarks)
       -> affine-transform sprite to anchor points (rotate/scale/translate)
       -> alpha composite onto frame
       -> virtual camera
       -> OBS reads it as a normal video source
```

No ComfyUI round-trip — everything runs local and in-process, so added
latency is camera-capture-bound rather than network-bound: typically
under 20ms, well below the face-swap tools' 60-150ms in [`realtime-ai`](../setup/manual.md).

## Usage

```bash
pip install opencv-python mediapipe pyvirtualcam numpy
python3 face_mesh_filter.py --filter filters/glasses.json
```

Then in OBS: add a Video Capture Device source and select the virtual
camera device named in the script's startup log line.

## Filter manifests

Each filter is a JSON file in `filters/` describing which landmarks to
anchor to and where its sprite art lives:

```json
{
  "name": "glasses",
  "sprite": "../assets/glasses.png",
  "anchor_landmarks": { "left": 33, "right": 263, "center": 168 },
  "scale_multiplier": 1.6,
  "vertical_offset_frac": 0.0
}
```

- `anchor_landmarks.left` / `.right` — landmark indices used to compute
  rotation and scale (eye-to-eye by default).
- `anchor_landmarks.center` — landmark the sprite is centered on
  (defaults to the left/right midpoint if omitted).
- `scale_multiplier` — tune per sprite; the base scale is derived from
  eye distance so filters stay face-size-relative across users and
  camera distances.
- `vertical_offset_frac` — nudge the anchor up/down, as a fraction of
  frame height.

Common anchor landmark indices (MediaPipe Face Mesh, 468-point model):

| Feature | Index |
|---|---|
| Left eye outer corner | 33 |
| Right eye outer corner | 263 |
| Nose bridge | 168 |
| Nose tip | 1 |
| Forehead center | 10 |
| Chin | 152 |

## Sprite art

**Not shipped in-repo** — same convention as the face-swap model weights
in `../deepfacelive/`. Add your own RGBA PNGs under `assets/` (gitignored)
and point `sprite` in your manifest at the relative path.

## Status

Scaffolded — the pipeline and one example manifest (`filters/glasses.json`)
exist and are runnable; no sprite art is bundled. Validate by supplying
your own PNG at `assets/glasses.png`, running the script, and confirming
OBS shows the composited output with acceptable tracking stability.

## Deliverables (commit these)

- Additional `filters/*.json` manifests as you add sprite art
- Latency/stability notes here once validated on your hardware
