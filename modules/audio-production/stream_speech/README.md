# Stream Autopilot speech worker

This Audio Production worker turns current `stream-host` replies into local speech. It validates
the on-air session, generation, age, voice binding and queue limits before synthesis. macOS uses
`say` plus `afplay`; Windows uses installed System.Speech plus SoundPlayer. Both paths pass reply
text as stdin data to fixed commands.

Playback emits `started`, `finished`, `canceled` or `failed` events through the existing backend
event contract. The start/finish events give an avatar worker actual playback timing instead of
estimating duration from text. Pause, persona change and shutdown cancel synthesis/playback,
clear the bounded queue and prevent an old generation from speaking. WAV files are deleted after
playback unless operator configuration explicitly retains them.

Validate the native dependencies:

```bash
PYTHONPATH=modules/audio-production python3 -m stream_speech --validate
```

Run a local JSONL reply/control rehearsal, which produces audible speech:

```bash
PYTHONPATH=modules/audio-production python3 -m stream_speech --input /path/to/host-output.jsonl
```

For the live authenticated event bus, set `AUTOPILOT_BACKEND_URL` and `HCP_API_KEY`, then use
`--backend`. Configure the on-air session and logical voice IDs in
[`configs/local/stream-speech.yaml`](../../../configs/local/stream-speech.yaml). The default
logical `nova-local` binding uses the operating system default voice. Selecting and routing the
actual OBS audio device remains an operator setup step.

This worker does not start a broadcast, ingest platform chat, render an avatar or control a game.
Native Windows playback acceptance remains pending.

## Local voices (P-068, slice 1)

A `voices:` entry can also be a structured `provider: local` voice, rendered by a local TTS engine
instead of the operating system ([P-068](../../../docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md)).
Slice 1 builds the seam only: the schema, the router, a render cache and a readiness report.
**No engine adapter ships, no model is installed and no voice has been recorded or measured**, so
a local voice reports `ready: false` until a later slice adds an engine. The shipped config has
none, and operating-system voices behave exactly as before.

```yaml
render_cache_directory: output/stream-autopilot/speech-cache
voices:
  nova-local: null                 # operating-system voice, unchanged
  nova-opentech:
    provider: local
    engine: chatterbox             # chatterbox | f5-tts | xtts-v2 | kokoro
    model_path: models/tts/chatterbox
    speaker_ref: models/tts/refs/owner-measured.wav   # cloning engines only; kokoro has none
    sample_rate: 48000             # the WAV rate the engine must deliver
    revision: ""                   # change when the weights or engine settings change
```

- **Pre-recorded narration only.** A local engine takes tens of seconds per line, far past
  `event_ttl_seconds`. A line that is not cached yet is rendered while its event ages; if that
  outlives the event the worker reports `canceled` (`stale_before_playback`) instead of speaking,
  but the render still lands in the cache, so the next submission of the same line plays at once.
  Render ahead of the run, then play.
- **The cache is keyed on the text and the whole voice spec**, including the *content* of
  `speaker_ref`, so re-recording the sample or changing any setting stops old renders being
  reused. The weights are not hashed; bump `revision` when they change. Entries are never evicted.
  Without `render_cache_directory` every line is rendered.
- **Paths are repository-relative** (no absolute path, drive letter, backslash or `..`).
  `models/tts/` is gitignored: weights and the owner's reference recording must never be committed.
- **Nothing downstream of the WAV changes.** Playback, cancellation and the `started`, `finished`
  and `canceled` events stay with the native player, so the avatar's mouth-sync is unaffected. A
  failure is a `failed` event with reason `local_engine_unavailable` (no adapter, model or
  reference missing) or `local_speech_failure`, and the worker carries on with the next reply.
  There is no silent fallback to the operating-system voice.
- **Check readiness** with `PYTHONPATH=modules/audio-production python3 -m stream_speech --validate`.
  The report gains `voice_providers`, one entry per voice. Readiness is reported, not enforced:
  `valid` stays true so an engine that is not installed yet cannot fail a live-stream preflight.
- **Not covered yet:** the voice studio's `stream_speech.render` and the Autopilot production
  driver still use native voices only; give them a `provider: local` voice and they fail.
  `providers.py` and `cache.py` are deliberately outside the file list Stream Extend bundles, and a
  test fails if a bundled file ever imports them.

## Pre-rendering a script (P-068 slice 4)

Local voices are for pre-recorded narration ([P-067](../../../docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md)
section 7.4: pre-render, never stream). Render a script's lines ahead of the run and the cache fills; at run
time every line is a cache hit and plays at once. `--prerender` also reports each line's real duration and,
per voice, the p50 and p95 render time that [P-068 section 6.2](../../../docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md)
asks for instead of a mean, which hides the outlier that stalls a batch.

```json
{"voice_id": "nova-local", "text": "Today we walk through the weekly review."}
{"voice_id": "nova-opentech", "text": "First, open the draft and check the three numbers."}
```

```bash
PYTHONPATH=modules/audio-production python3 -m stream_speech --prerender lines.jsonl
```

One JSON record per line on stdout (`status` is `rendered`, `cached` or `failed`, with `render_seconds` and
`audio_seconds`), then a `prerender_summary`. A record carries the line's index, length and a short hash of
its text, never the text. The exit status is 1 if any line failed, after the whole script has run.

- **The file is validated first** (voice ids against the speech config, text length, file size), so a typo on
  line 40 costs nothing. Local voices need `render_cache_directory`, or the renders would be thrown away.
- **Cache hits are not renders**, so only rendered lines are timed. Section 6.2's pass condition for batch use
  is **p95 under 60 s**; `p95_under_limit.met` is `null` until there are twenty rendered lines, because the p95
  of five lines is not a p95.
- **Native voices are timed too** (no cache, no pass condition), as the baseline a local voice has to beat.
  Measured on an Apple M1 Pro with 16 GiB: 20 paragraphs of 254-473 characters through the default operating
  system voice took p50 4.53 s, p95 5.46 s, max 5.50 s, about 0.21 s of rendering per second of audio. That is
  the incumbent. No local engine has been measured, because none is installed.

## Boundary with saved reaction clips

This worker owns live AI-VOICE speech. [P-066](../../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md)
adds `stream_speech.render` as a fixed JSON-stdin render/play adapter used by the
[voice studio](../../automation-control/voice_studio/README.md). Rendering saved gaming candidates
never plays them; accepted clips are manually loaded into OBS Soundboard.

With a director `phrase_manifest`, set this worker's `reply_source: stream-director` and do not run
a second direct-host speech worker. It receives only director-selected fallback/ordinary replies
plus the original host controls, preventing duplicate voice for a clip-dispatched event. Defaults
retain `stream-host` for the legacy configuration. Scripted personas use the studio's separate
manual script/Q&A player and the same native adapter on AI-VOICE, never the Soundboard. Keep this
continuous worker stopped while using that manual player to avoid competing audio.
