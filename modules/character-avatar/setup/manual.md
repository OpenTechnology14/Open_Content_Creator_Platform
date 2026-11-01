# character-avatar — manual setup

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

PNGTuber and VTube Studio avatars, driven by the same agent and scene switcher as the rest of
the stream.

## PNGTubers (start here)

The lightweight path — no rigging, no tracking, works on any hardware.

1. Prepare at minimum two states: mouth-closed and mouth-open. Four (adding blink variants) reads
   noticeably better.
2. Export as PNGs with transparency, same canvas size and registration so they swap without shifting.
3. Add to OBS as an Image Source, driven by an audio-level trigger so the mouth opens when you speak.

This is often all a stream needs. Do not jump to a rigged model until the PNGTuber is limiting you.

## VTube Studio (rigged 2D)

Desktop app, Windows-first. Install it, load or purchase a Live2D model, and calibrate face
tracking against your webcam. Capture into OBS via Spout/NDI or a window capture with a colour key.

## VRM avatars (3D)

For 3D, VRM models plug into VTube Studio's 3D mode or a dedicated VRM host.

## Agent-driven avatars

The avatar becomes interesting when something else drives it. `vtube/avatar_control.py` in this
module is the seam: it subscribes to the `agent.reply` Redis channel `ai-agents`' agent loop
publishes every reply to, triggers a "talking" VTube Studio hotkey for a duration estimated from
the reply's length, then an "idle" hotkey. See [ai-agents](../../ai-agents/setup/manual.md) —
that module owns the persona, memory, and moderation; this one owns the puppet.

To wire it up:

1. In VTube Studio, go to Settings -> Hotkeys and create at least a "Talking" and an "Idle"
   hotkey (or reuse an existing pair) for expression/mouth changes on your model.
2. Edit `vtube/avatar_mapping.yaml` if your hotkey names differ from the defaults, or to give a
   specific persona its own hotkeys instead of the shared default.
3. Run `python vtube/avatar_control.py` alongside `ai-agents`' `agent.py`. It needs `PYYAML`,
   `loguru`, `redis`, and `websockets` installed, and `REDIS_URL` pointed at the same Redis the
   agent publishes to (defaults to `redis://127.0.0.1:6379/0`, matching `agent.py`'s own default).

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] The avatar renders in OBS with a clean transparent background
- [ ] Mouth state responds to your voice with no perceptible lag
- [ ] If agent-driven, an agent event visibly changes the avatar

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

- **Avatar background is not transparent** — window capture instead of Spout/NDI; switch, or key
  a solid colour.
- **Mouth flaps constantly** — the audio trigger threshold is below your room noise floor; raise
  it, or gate the mic first (see [audio-production](../../audio-production/setup/manual.md)).
- **Model shifts between states** — the PNG states were exported on different canvas sizes.
