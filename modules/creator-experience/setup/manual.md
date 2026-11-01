# creator-experience — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

The foundation every other Stream module builds on. Do this first.

## Core software

| Tool | Purpose | Install |
|---|---|---|
| OBS Studio (≥ 30.x) | Streaming + recording | https://obsproject.com/ |
| obs-websocket (≥ 5.x) | Built into OBS 28+ — just enable | bundled |
| Advanced Scene Switcher | Conditional automation | plugin |
| Move Transition | Smooth source transitions | plugin |
| Source Clone | Reuse sources across scenes | plugin |
| StreamFX (optional) | Advanced filters/effects | plugin |

Pinned plugin versions: `modules/creator-experience/obs-config/plugins.md`.

## Capture card or camera

Run **Module setup → Capture hardware → Scan capture hardware** in either desktop app, or:

```bash
python3.12 scripts/setup/capture_devices.py
```

On Windows the scanner reports DirectShow video/audio names and present Camera, Image and Media
drivers. On macOS it reports AVFoundation devices. Select and save the intended video source and
optional capture-card audio source in the app. For an Xbox Series S, connect console HDMI output
to capture-card HDMI input and connect the card directly to a USB 3 port on the streaming computer.

In OBS, add **Video Capture Device**, choose the same video name, set 1920×1080 at 60 fps when
the card supports it, and select the card's audio input or add it as a separate Audio Input Capture.
Make a local recording before entering account or stream credentials.

## Video settings

Settings → Video.

- Base (canvas): 1920×1080
- Output (scaled): 1920×1080
- Downscale filter: Lanczos
- FPS: 60

## Output — streaming (Advanced mode)

- Encoder: NVENC HEVC (NVIDIA), AV1 on RTX 40+; otherwise NVENC H.264 / AMF / Apple VT / x264
- Rate control: CBR
- Bitrate: 6000 kbps for 1080p60 — tune per platform
- Keyframe interval: 2
- Preset (NVENC): P5 — Quality
- Profile: high
- Look-ahead: on (NVIDIA only)
- Psycho-visual tuning: on

## Output — recording

- Type: Standard
- Path: a fast local SSD, dedicated folder
- Format: **MKV** (crash-safe), with auto-remux to MP4 enabled in Advanced
- Encoder: same as streaming, or "Use stream encoder" for live recordings
- Quality: Indistinguishable Quality

## Audio

- Sample rate: 48 kHz, Stereo
- Mic and desktop audio as **separate sources**, never merged
- Mic filter chain, in this order:
  1. Noise Suppression (RNNoise)
  2. Noise Gate (−32 dB open / −36 dB close)
  3. Compressor (4:1, threshold −18 dB)
  4. Limiter (−1 dB)

For anything beyond this — multiple buses, mix-minus, TTS routing — see
[audio-production](../../audio-production/setup/manual.md).

## Scene collection

A reference collection is committed at `modules/creator-experience/scenes/default.json`.
Import via **Scene Collection → Import**.

## Multi-platform streaming

See `modules/creator-experience/obs-config/multi-platform.md`.

## OBS WebSocket

Enabling and securing it belongs to
[automation-control](../../automation-control/setup/manual.md) — that is where everything which
drives OBS programmatically lives.

## Managed Stream Extend recording handoff

Choose the active Stream profile in Stream Extend and the target Content profile in Creator Extend.
From Stream Extend's Dashboard, use **Go Live + Record**. The app starts recording first, then starts
the stream. Use **Stop + Send to Creator** to stop the stream, finalize only the recording the app
started, and register OBS's returned local file in Creator Extend → **Recordings**.

If OBS was already recording, Stream Extend may start the stream but deliberately leaves that
recording running and does not claim it. Add the completed file manually in Creator Extend. If the
app or workstation crashes, inspect OBS directly after restart; the app will not assume ownership
of a surviving recording.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] OBS streams to your platform at target bitrate with no dropped frames
- [ ] A test recording produces a playable MKV
- [ ] A Stream Extend-managed live session records before streaming, stops cleanly, and appears once
      in Creator Extend with the expected Stream and Content profiles
- [ ] A recording already active in OBS is not stopped or added automatically by Stream Extend
- [ ] Mic sounds clean with the filter chain engaged
- [ ] `make test-obs` connects (after configuring WebSocket)

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

- **Dropped frames on stream** — bitrate too high for upstream, or the encoder is saturated. Drop
  to 4500 kbps and re-test.
- **Encoder overloaded** — GPU is busy with a realtime AI effect; see
  [realtime-ai](../../realtime-ai/setup/manual.md) on latency budget.
- **Mic quiet or pumping** — the compressor threshold is below your speaking level; raise it.
