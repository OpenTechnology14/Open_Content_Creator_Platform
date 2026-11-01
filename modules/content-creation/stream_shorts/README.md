# Stream recording → Shorts

**Labels:** Content · P-056 · Local selection, review and real MP4 rendering.

This Content Creation pipeline accepts one completed recording and normalized interaction
metadata for any game/session. It selects nonoverlapping moments, retains exact manual sections,
and renders 720×1280 H.264/AAC MP4s with the entire game frame fitted inside a vertical canvas.
Optional editing data adds timed captions, event-driven punch-ins, brand colors/text and EBU-style
loudness normalization. It uses the imageio-ffmpeg bundled executable; no GPU or cloud account is
required.

## Run locally

From the repository root, in a Python 3.11+ virtual environment:

```bash
.venv/bin/pip install -r modules/content-creation/stream_shorts/requirements.txt
PYTHONPATH=modules/content-creation .venv/bin/python -m stream_shorts --help
PYTHONPATH=modules/content-creation .venv/bin/python -m stream_shorts select --job configs/local/stream-shorts-demo.json > plan.json
PYTHONPATH=modules/content-creation .venv/bin/python -m stream_shorts review --plan plan.json --output review.html
```

Open `review.html` in a browser. Choose the matching local recording; it stays on your machine.
Preview suggestions, uncheck unwanted clips, scrub the video and mark start/end or enter seconds,
then add a labeled section. Download the selected clip plan. Render that plan with:

```bash
PYTHONPATH=modules/content-creation .venv/bin/python -m stream_shorts render --plan reviewed-plan.json --source recording.mp4 --output shorts-reviewed
```

For unattended selection and rendering of one completed recording:

```bash
PYTHONPATH=modules/content-creation .venv/bin/python -m stream_shorts produce --job job.json --source recording.mp4 --output shorts-new
```

Outputs must use a new directory; existing work is never overwritten. Each run writes a manifest
with recording/session/game/show IDs, selected intervals, source path, plan hash and completion
or failure status. Each rendered output also records the applied caption/punch-in counts and audio
normalization setting. Duration must match the declared recording within 0.25 seconds; verify that
it is the correct recording, since equal durations alone cannot establish identity. Output size
and duration are checked after each clip. Partial failures are recorded, not marked complete.

## Advanced editing contract

The optional `edit` object is copied from the job into the reviewable plan. Advanced rendering is
opt-in through `"enabled": true`; existing version 1 jobs without it retain the original plain
full-frame layout and audio behavior. The demo job shows the full structure:

```json
{
  "edit": {
    "enabled": true,
    "style": {
      "background_color": "#101827",
      "accent_color": "#B7F7DA",
      "brand_title": "NOVA BUILDS",
      "watermark": "@nova",
      "captions_enabled": true,
      "normalize_audio": true,
      "target_lufs": -16
    },
    "captions": [
      {"start_seconds": 29, "end_seconds": 33, "text": "Chat found the breakthrough!"}
    ],
    "punch_ins": [
      {"start_seconds": 30, "end_seconds": 32, "scale": 1.2,
       "focus_x": 0.5, "focus_y": 0.5, "event_id": "chat-2"}
    ]
  }
}
```

All times remain relative to the complete recording. The renderer clips overlapping cues to each
selected output. Captions are limited to 20 seconds and punch-ins to 8 seconds; zoom and focus
values and hexadecimal colors are validated before reaching FFmpeg. Text is passed through local
UTF-8 files instead of being interpolated into the filter graph. Brand text is intentionally
plain text in this slice; image logos, fonts and music require an explicit asset contract and
rights metadata.

## Input contract and selection

[Demo job](../../../configs/local/stream-shorts-demo.json) is synthetic metadata for a 90-second
recording, not a captured livestream. `offset_seconds` is relative to the beginning of that
recording, not wall-clock time. Use a stable pseudonymous `user_key` for each viewer. No raw
chat message content is needed. The ingress adapter must identify bots and ineligible events;
this selector does not detect undeclared bots or prove that accounts belong to different people.

Scores combine distinct viewers and per-viewer capped participation in each window. Events
from other sessions, duplicate IDs, bots, ineligible events and out-of-recording timestamps are
ignored. Manual sections win over automatic selections and may exceed the preferred clip count.
Excluded sections block automatic selection; conflicting manual sections are rejected. Each
manual/excluded interval is at most 60 seconds; use adjoining intervals for a longer exclusion.
If there are no eligible interactions, an explicitly labeled fallback can still produce a draft
clip. A recording shorter than five seconds or entirely excluded produces no automatic clip.

Scores rank participation, not whether a scene is entertaining or appropriate. The pipeline does
not transcribe speech, track subjects, classify game events, moderate video/audio, upload, or
publish. Caption timestamps/text and punch-in focus points must be supplied by an operator or an
upstream adapter. Creator Extend's **Recordings** inbox supplies the local recording from a managed
Stream Extend session or a manual import. The review page displays the edit summary and exports a
plan; it does not itself launch FFmpeg. Local CLI processing is working; automatic ingestion of
platform chat and OBS recording-finished events outside Stream Extend's managed live control,
durable interaction jobs, and automatic delivery from the inbox into a Shorts job remain integration
work. An episode's
`shorts_requested` flag expresses intent and does not prove that a clip was produced.

## Module boundary and cloud

Automation / Control owns episode timing and the completion event. Content Creation owns this
recording/job artifact contract and rendering, without importing the host or director. A future
backend adapter can supply these artifacts for every session. DigitalOcean batch execution is
optional and untested; live capture stays local. No new Compose service or environment variable.
