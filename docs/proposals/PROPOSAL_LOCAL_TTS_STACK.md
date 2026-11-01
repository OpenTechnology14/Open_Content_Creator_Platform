# Proposal: Local TTS stack for Nova

**Queue row:** `P-068`
**Agent model / effort:** `gpt-6.1-sol` / `high` — Local TTS providers, GPU benchmarking and playback events
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Pending` — slices 1–4 (provider seam and render cache; blind audition rig; recording checker; pre-render and timing) built at the owner's request 2026-10-05; D1–D3 and all engine, model and recording work still await the owner — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md)
**Owner:** OpenTechnology14 + agent
**Date:** 2026-09-22
**Roadmap layers:** Audio Production, Content Creation, Character / Avatar
**Evidence level:** Slices 1–4 — offline contract tests with fake engines, and real runs on the Mac: `--validate`, the audition rig on installed operating-system voices, the recording checker on real speech and AAC round trips, and a latency baseline for the operating-system voice (§10). **No local engine has been installed, no model downloaded, no voice recorded or cloned, and no local engine benchmarked**; the only measurement is of the incumbent operating-system voice, and everything else here is still a specification.
**Depends on:** [`PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md`](PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) (`P-067`) — the three-account voice model this either complements or replaces

---

## Owner decision points — read these first

Three decisions gate everything below. The rest of the document exists to inform them.

| # | Decision | Recommendation | What it changes |
|---|---|---|---|
| **D1** | **Confirm the hybrid strategy** — OpenTechnology local, Games and Reactions staying on ElevenLabs — or override to fully local, which means voice-acting three distinct vibes yourself **Question:** Go hybrid — your own cloned voice locally for OpenTechnology, ElevenLabs for Games and Reactions — rather than fully local? | **Hybrid** (§3). Fully local requires you to perform a young energetic register and a Latin-accented register convincingly, which is a voice-acting problem, not a software one | Everything |
| **D2** | **Willing to record 3–10 minutes of clean voice sample** as the clone source? **Question:** Will you record 3–10 minutes of clean voice sample to clone from? | Yes if D1 is hybrid or fully local. A clone is the only path to a distinctive *and* legally clean voice | Blocks the OpenTechnology voice entirely |
| **D3** | **Target: prototype (~half a day) or production-ready (~a day plus fine-tuning)?** **Question:** Build a prototype first, about half a day, rather than going straight to production-ready? | **Prototype first.** Decide on production only after an A/B against ElevenLabs on real narration | Scope of §5 |

---

## Non-goals

1. **Live-stream real-time narration.** Local inference on an M1 Pro is too slow for a live host — use the ElevenLabs streaming API if that is ever needed. This proposal covers **pre-recorded** content only: walkthroughs, VOD narration, recorded reactions.
2. **Non-English voice generation** beyond what the recommended models natively support.
3. **Fine-tuning the Games and Reactions voices.** Under the recommended hybrid they stay on ElevenLabs — see §3.
4. **Replacing ElevenLabs entirely.** The recommendation is to reduce the bill, not eliminate the dependency.
5. **Cloning any real person other than the owner.** `P-067` §7.3 sets this boundary and it is unchanged here: cloning a named style reference without written consent violates provider terms and creates right-of-publicity exposure.

---

## 1. Cost and motivation

### 1.1 The arithmetic

| | ElevenLabs Pro | Local |
|---|---|---|
| Recurring | **$99/mo** | **$0** after setup |
| Setup cost | Minutes | Half a day to a day (§5) |
| Per-paragraph latency | Sub-second, streaming | **~5–30 s on an M1 Pro** (estimate, §2.4) |
| Live use | Yes | **No** |
| Quality ceiling | Very high | High, model-dependent |
| Voice variety | Large pre-built library | What you can clone or find pre-built |

> **Pricing figures are owner-supplied as of 2026-09-22** — ElevenLabs Pro at $99/mo, Creator at $22/mo. Provider pricing changes without notice. **Re-verify both tiers on ElevenLabs' own pricing page before acting on the saving in §3.3**, because the entire financial case rests on those two numbers and this document did not check them.

### 1.2 Why latency is acceptable here

`P-067` §7.4 already commits to **pre-rendering every narration line to WAV before a run starts**, for three reasons that have nothing to do with cost: determinism across takes, no network stall during capture, and real durations so pacing is arithmetic rather than a guess.

That decision is what makes local TTS viable. If narration were synthesized live, a 20-second inference would be fatal. Pre-rendered, it is a background job that finishes before recording begins — and the hash-keyed cache in `P-067` §7.4 means changing one line re-synthesizes one line.

**The local-first argument does not apply, and saying so matters.** [`CLAUDE.md`](../../CLAUDE.md) §2 keeps latency-sensitive work on the local GPU. TTS for pre-recorded content is not latency-sensitive; it is a batch render. So local here is a **cost** decision, not an architecture one, and it should be judged on cost and quality rather than on principle.

---

## 2. Local model options

**Everything in this section is desk research.** No model below has been installed or benchmarked on the target machine. Performance figures are estimates for an M1 Pro / 16 GB with MPS, offered to size the decision — not measurements. §6 is how they become real.

| Model | Params / size | Cloning | Est. latency (M1 Pro, one paragraph) | Best for |
|---|---|---|---|---|
| **Kokoro TTS** | ~82 M | **No** — pre-built voices only | Fast; near-real-time on CPU | High-volume pre-built narration where you do not need a specific identity |
| **Coqui XTTS v2** | ~1.8 GB class | **Yes**, from ~6 s of reference audio | ~10–30 s | Multilingual cloning; the most documented option |
| **F5-TTS** | Mid | Yes | Similar to XTTS v2 | Sharper output than XTTS v2 on clean references |
| **Chatterbox** (Resemble, open-sourced mid-2025) | Mid | Yes | Similar class | **Cleanest local quality currently available** |
| **OpenVoice v2** | Small-mid | Style transfer + cloning | Fast-ish | Style transfer onto an existing voice |

### 2.1 Recommendation by purpose

| Purpose | Model | Why |
|---|---|---|
| **Pre-built, pre-recorded narration** — where identity does not matter | **Kokoro** | ~82 M parameters, real-time on CPU, no GPU contention. The only option here that could run alongside a render without competing for memory |
| **Cloned Nova narration — the owner's voice, OpenTechnology account** | **Chatterbox**, with **F5-TTS** as the A/B alternate | Chatterbox is reported as the cleanest current local quality; F5-TTS is the closest competitor. Pick between them by ear on your own sample (§6.1), not by reading this table |
| **Multilingual, or if the above disappoint** | **XTTS v2** | Most documented, most tutorials, widest community. The safe fallback, not the quality leader |
| Style transfer | OpenVoice v2 | Narrow use. Skip unless a specific need appears |

### 2.2 Why not simply the highest quality everywhere

Because the M1 Pro's 16 GB is shared between applications and graphics, and the constraint recurs throughout this repo's docs. A 2 GB TTS model resident while ComfyUI holds SDXL (~7 GB) and a recorder runs is how you reach the memory pressure that the Stream Extend guide names as the most common OBS crash cause on this hardware.

Kokoro's ~82 M parameters are the reason it earns a row at all: it is small enough not to participate in that competition.

### 2.3 Storage

Voice models run roughly **200 MB to 2 GB each**. Cloned-voice artifacts add to that. Budget **~5 GB** for the stack plus a few cloned variants, on top of the ~100 GB the Creator Extend guide already asks you to keep free.

Every downloaded weight gets a row in [`model-registry`](../../modules/model-registry/README.md)'s `registry.yml` — checksum, licence, distributability. That module is `implemented` and its CLI is one of the few fully automated things in this repo:

```bash
python3.12 -m model_registry.cli status
```

**This is not bureaucracy for a TTS model.** Licences differ sharply across these projects, and a cloned voice built on a weight you cannot redistribute is a voice you cannot ship in a product. Record it at download time, when the licence is in front of you.

### 2.4 The latency claim, stated honestly

"~5–30 s per paragraph" is a **range from published reports and community benchmarks, not a measurement on this machine.** It could be materially better on an M1 Pro with MPS, or materially worse for a model whose MPS path is incomplete — several of these projects were built CUDA-first and their Apple Silicon support varies.

§6.2 exists specifically to replace this estimate with a p50/p95 you measured.

---

## 3. Fit with the three-account model

`P-067` §7.2 selects **Option B**: three Nova variants sharing core identity, one voice per account.

| Account | Vibe | ElevenLabs binding (P-067 §7.3) |
|---|---|---|
| games | Young, energetic, expressive | Adam (alts: Josh, Sam) |
| reactions | Young, energetic, Latin-accented | Diego (alt: Mateo) |
| opentechnology | Deep, warm, measured, narrative | Dave (alt: Antoni) |

### 3.1 Local cannot replicate three vibes from one sample

This is the central constraint and it is worth being blunt about. A cloned voice sounds like **the person who recorded the sample**. One owner recording produces one voice. Getting a young, Latin-accented, energetic register out of it requires either:

- the owner performing that register convincingly — a **voice-acting** problem, not a software one; or
- licensed samples from someone who has it, which the owner does not have and which carries its own consent requirements.

Neither is a software decision, and no amount of model selection changes it.

### 3.2 Recommendation: hybrid

| Account | Provider | Voice | Why |
|---|---|---|---|
| **opentechnology** | **Local** (Chatterbox or F5-TTS) | **Owner's cloned voice** | Highest-volume long-form narration, so the biggest cost saving. Legally cleanest — your own voice. And if you record in a measured register, it plausibly *is* the "wise narrator" vibe, rather than approximating it |
| **games** | ElevenLabs | Adam | A young energetic register is one you would have to perform. Pre-built is better and cheap at this volume |
| **reactions** | ElevenLabs | Diego | A native Latin accent is not something a clone of your voice will produce. `P-067` §7.3 already prefers a natively-accented voice over an overlay |

The OpenTechnology account is the right one to move local for a reason beyond volume: it is the account where a **distinctive** voice is worth most. Games and Reactions are entertainment registers where a good pre-built voice is indistinguishable from a good clone. A professional channel narrated by the actual person behind the product is a different and better claim — and it sidesteps the Morgan-Freeman-vibe problem entirely, because you are no longer approximating anyone.

### 3.3 The saving

| | Before | After |
|---|---|---|
| ElevenLabs tier | Pro — **$99/mo** | Creator — **$22/mo** |
| Local | — | $0 |
| **Monthly** | **$99** | **$22** |

Moving the highest-volume long-form narration off the metered provider is what allows the tier drop. **Verify the character allowance on the Creator tier covers your remaining Games and Reactions volume before switching** — the saving is real only if the lower tier actually fits, and this document has not checked that.

### 3.4 If the owner overrides to fully local

Viable, with eyes open. It means recording **three** sample sets in three registers and cloning each. The energetic and accented ones are the hard part, and the honest failure mode is that Nova's Games voice sounds like the owner doing an impression — which is worse than a well-chosen pre-built voice, not better.

Recommend attempting it **only after** the OpenTechnology clone has passed §6.1, so there is a known-good baseline to compare against.

---

## 4. Integration

> **Slice 1 of this section is built** — see §10 for what exists and where it deviates.

### 4.1 Config

Extend [`configs/local/stream-speech.yaml`](../../configs/local/stream-speech.yaml) rather than inventing a parallel file. It currently declares `voices: {nova-local: null}`, where null means the OS default voice.

```yaml
voices:
  nova-local: null                  # OS default — retained as the offline fallback

  nova-opentech:
    provider: local
    engine: chatterbox              # chatterbox | f5-tts | xtts-v2 | kokoro
    model_path: models/tts/chatterbox
    speaker_ref: models/tts/refs/owner-measured.wav
    sample_rate: 48000

  nova-games:
    provider: elevenlabs
    voice_id: adam
    api_key_env: ELEVENLABS_API_KEY

  nova-reactions:
    provider: elevenlabs
    voice_id: diego
    api_key_env: ELEVENLABS_API_KEY
```

The `provider` field is the seam. It already has to exist for `P-067` §7.3, so local becomes a third provider value rather than a new mechanism — which is the main reason to land `P-067`'s config shape first.

### 4.2 Playback events are unchanged

The local synthesizer writes a WAV and hands it to the existing speech worker, which emits the same **playback start, finish and cancellation** events that [`modules/character-avatar/stream_avatar/`](../../modules/character-avatar/stream_avatar/) already consumes for mouth-sync.

**Nothing downstream of the WAV changes.** Not the avatar adapter, not the pet overlay, not the recorder, not the recording inbox. That is the point of pre-rendering: local TTS is a swap at one seam.

### 4.3 Cache

The hash-keyed cache from `P-067` §7.4 — keyed on `(text, voice_id, settings)` — matters *more* locally than it did with a paid API. With ElevenLabs the cache saves money; locally it saves 20 seconds per line on every re-run. A three-minute walkthrough with 30 lines is the difference between a 10-minute re-render and a 20-second one.

---

## 5. Setup

Atomic steps. **None of these have been run** — this is the plan, and §6 is what turns it into evidence.

### 5.1 Prerequisites

```bash
brew install python@3.11 ffmpeg
```

```bash
python3.11 --version && ffmpeg -version | head -1
```

Python 3.11 rather than this repo's usual 3.12: several of these projects pin older torch or transformers builds, and 3.11 has the widest wheel coverage. Keep it in its own venv; do not mix it with the module environments.

### 5.2 Environment

```bash
python3.11 -m venv ~/.venvs/nova-tts
source ~/.venvs/nova-tts/bin/activate
pip install --upgrade pip
```

### 5.3 Install per engine

Pick one to start — Chatterbox if following the recommendation.

**Chatterbox:**

```bash
pip install chatterbox-tts
```

**F5-TTS:**

```bash
pip install f5-tts
```

**Coqui XTTS v2:**

```bash
pip install TTS
```

**Kokoro:**

```bash
pip install kokoro-onnx
```

**Verify** — each must import and report a version, and torch must see MPS:

```bash
python -c "import torch; print('mps', torch.backends.mps.is_available())"
```

Pass condition: `mps True`. If it prints `False`, every figure in §2 is wrong for your install, because you are on CPU.

> Package names are as published at time of writing and **have not been installed here**. If one does not resolve, the project's own README is the authority — do not substitute a similarly-named package, which is a supply-chain risk, not a convenience.

### 5.4 Voice sample recording protocol

This is the step that determines quality, and it is the one most likely to be rushed.

| Requirement | Value | Why |
|---|---|---|
| Room | Quiet, soft furnishings, no HVAC | Room reflections clone as part of "your voice" |
| Mic | Your best; consistent distance throughout | Distance changes become timbre changes |
| Format | **48 kHz WAV, no compression** | Cloning from an MP3 clones the artifacts |
| Length | **3–10 minutes** | 6 s is the documented XTTS v2 *minimum*; more is better for consistency |
| Content | **Varied** — statements, questions, lists, numbers, technical terms | A sample of only flat statements produces a voice that cannot ask a question |
| Register | **The register you want Nova to have** | For OpenTechnology: measured, warm, unhurried. Perform the target, do not read flatly and hope |
| Consistency | One sitting, no throat-clearing, no edits | Splices become audible discontinuities |

Read something real and varied — your own blog posts are ideal, because the vocabulary matches what Nova will actually say.

```bash
ffprobe -v error -show_entries stream=sample_rate,channels,codec_name \
  -of default=noprint_wrappers=1 ~/nova-voice/owner-measured.wav
```

Pass condition: `48000`, mono or stereo, PCM codec. Anything lossy — re-record.

> **Slice 3:** [`tts/check_voice_sample.py`](../../modules/audio-production/tts/check_voice_sample.py) runs this check and the measurable rest of the table. It also looks for what this pass condition cannot see: an MP3 or AAC converted to 48 kHz PCM reports `48000`, PCM, and then clones its artifacts, but it leaves a low-pass cutoff behind.

### 5.5 Clone

Each engine's own CLI or Python API takes the reference WAV plus text. Follow the engine's README; the invocation differs per project and inventing one here would be guessing.

**Verify:** synthesize one paragraph of real script text — not "hello world", which tells you nothing about prosody. Listen on **headphones and laptop speakers**, because they fail differently.

### 5.6 Fine-tuning (optional, D3-dependent)

Only if §6.1 says the clone is close but inconsistent across runs. Fine-tuning costs hours and a larger corpus; it is a production step, not a prototype one. Skip it entirely if the zero-shot clone passes.

### 5.7 Wire into the pipeline

1. Add the `nova-opentech` block to `stream-speech.yaml` (§4.1).
2. Implement the `provider: local` branch in the speech worker's synthesis path.
3. Confirm the worker still emits playback start/finish/cancel unchanged (§4.2).
4. Register every downloaded weight in `model-registry` (§2.3).

---

## 6. Test plan

The whole point of this section: **replace the estimates in §2 with measurements.**

### 6.1 Voice quality A/B — blind

Same paragraph of real script text, three renders:

| A | Local clone (owner's voice) |
| B | `nova-local` — the current OS default |
| C | ElevenLabs pre-built (Dave) |

Randomize order, listen without labels, rank. **Include B.** It is the current state and the thing you are actually replacing, and if the local clone does not clearly beat the OS default the project stops there.

Judge on: naturalness, consistency across sentences, handling of technical terms and numbers, and whether it sounds like **you**.

**Pass condition:** local clone ranks first or ties ElevenLabs. If it ranks below the OS default, abandon local for this account.

### 6.2 Latency

```bash
for i in $(seq 1 20); do /usr/bin/time -p <synth-command> 2>&1 | grep real; done
```

Twenty paragraphs of realistic length. Record **p50 and p95**, not the mean — the mean hides the outlier that stalls a batch.

**Pass condition for batch use: p95 under 60 s per paragraph.** A 30-line walkthrough at p95 is then under 30 minutes of background render, which is tolerable overnight and annoying same-day. Above that, use Kokoro for drafts and reserve the clone for finals.

> **Slice 4:** `python -m stream_speech --prerender lines.jsonl` measures this: p50, p95 and max render time per voice, with this pass condition applied once there are twenty renders. See §10.

### 6.3 Consistency across sessions

Synthesize the same line on three separate days, with a process restart between each. Compare by ear and by waveform.

**Pass condition:** no audible drift. Some models are non-deterministic across runs; if yours is, pin the seed if it exposes one, and if it does not, know that re-rendering one line in an otherwise-finished video may not match its neighbours.

### 6.4 Pipeline integration

The test that matters most, because it is the one that fails silently:

1. Synthesize narration for a real walkthrough script via the local provider.
2. Run a `walkthrough` recording (`P-067` §9, Run 1).
3. Confirm the pet mouth-syncs correctly — proves playback events still fire (§4.2).
4. Confirm the finished recording registers in the inbox with the right `content_profile_id`.
5. Confirm Creator Extend's account router sends it to the **OpenTechnology** account.

**Pass condition: all five.** Step 3 is the one to watch — if the local path writes a WAV without going through the speech worker's event emission, the pet goes still and nothing errors.

---

## 7. Boundaries

- Pre-recorded content only. No live narration (Non-goals).
- The OS default `nova-local` stays as the offline fallback; local TTS is an addition, not a removal.
- Only the owner's voice is cloned. `P-067` §7.3's prohibition on cloning named references is unchanged.
- Every downloaded weight gets a `model-registry` row before use (§2.3).
- Nothing downstream of the WAV changes (§4.2). If a local-TTS change requires touching the avatar adapter or the recorder, that is a signal the seam is in the wrong place.

---

## 8. Cross-links

- [`PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md`](PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) — `P-067`; the three-account voice model, pre-render decision and cache this builds on
- [`configs/local/stream-speech.yaml`](../../configs/local/stream-speech.yaml) — the config this extends
- [`modules/audio-production/`](../../modules/audio-production/) — the owning module
- [`modules/character-avatar/stream_avatar/`](../../modules/character-avatar/stream_avatar/) — consumes the playback events (§4.2)
- [`modules/model-registry/`](../../modules/model-registry/) — weight provenance (§2.3)
- [`CREATOR_EXTEND_PRODUCTION_SETUP.md`](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) — downstream pipeline and disk budget
- [`STREAM_EXTEND_PRODUCTION_SETUP.md`](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) — the three-account model and the M1 Pro memory constraint

---

## 9. Acceptance limits

> **Updated 2026-10-05:** §10 records what has since been built and the one measurement made (the incumbent operating-system voice). The statements below describe the specification as written; anything §10 does not list is still unverified.

This is a specification and proves nothing. **No model has been installed, no voice recorded or cloned, no latency measured, no A/B run, and no pricing page checked.**

Specifically not verified:

- The **$99 and $22 ElevenLabs figures** are owner-supplied as of 2026-09-22 and were not confirmed against the provider. The financial case rests entirely on them.
- The **~5–30 s latency range** is desk research, not a measurement on an M1 Pro. §6.2 exists to replace it.
- **Package names** in §5.3 are as published at time of writing and were not installed.
- **Relative model quality** in §2 is from published reports, not from listening on this machine. §6.1 is the real comparison.

Everything in §6 is designed to convert one of those into evidence. Until it runs, this document is a plan.

---

## 10. Implementation record

### Slice 1 — the provider seam and render cache (2026-10-05)

**Authorization.** Built at the owner's direct instruction in chat on 2026-10-05, as the smallest first
slice that holds under any answer to D1–D3. That is not acceptance of the proposal: it stays `Pending`,
D1–D3 are unanswered, and nothing here pre-empts them — no engine, model download, voice recording or
ElevenLabs change was made.

**Executed by:** Claude Sonnet 5.5, not the assigned `gpt-6.1-sol` / `high`. The
[model policy](../PROPOSALS.md#agent-model-selection) asks for the actual execution model to be recorded
when it differs; the assignment is unchanged for later slices.

**What exists now**, under `modules/audio-production/stream_speech/` unless noted:

| Piece | Where | What it does |
|---|---|---|
| `provider: local` voice schema | `models.py` (`LocalVoice`, `Voice`) | The §4.1 shape, validated at load: engine is one of chatterbox, f5-tts, xtts-v2 or kokoro; repository-relative paths only; a reference recording for the cloning engines and none for Kokoro; `sample_rate`; and a `revision` that busts the cache when weights change. Operating-system voices (`null` or a name) are unchanged |
| Provider router | `providers.py` (`RoutedSpeechAdapter`, `LocalSynthesizer`, `Engine` protocol) | Local voices go to a registered engine adapter; everything else, and all playback and cancellation, stays with the native adapter, so §4.2's events cannot change. `default_engines()` is empty |
| Render cache | `cache.py` (`RenderCache`, `cache_key`) | §4.3: keyed on the text and the whole voice spec, including the *content* of the reference recording. Entries are published atomically and a damaged entry is a miss |
| Readiness report | `__main__.py` (`--validate` gains `voice_providers`) | Per voice: its provider and, for local voices, whether the engine, model and reference are present. Reported, not enforced, so an engine that is not installed cannot fail a live preflight |
| Tests | `tests/audio_production/test_local_voice_provider.py` | 39 tests with a fake engine, including the §6.4 silent-failure case (a local voice emits the same events as a native one) and a guard that the files Stream Extend bundles import only bundled siblings |
| Ignore rule | `.gitignore` | `models/tts/`: weights and the owner's reference recording never enter git |

**Deviations from the spec, and why.**

1. The cache key omits the logical voice id that §4.3 lists. The runtime hands the adapter the voice spec,
   not its id, and the spec already captures the voice's identity; leaving the id out also means renaming a
   binding does not re-render a library.
2. `revision` is new. §4.1 has no way to say "the weights changed", and hashing gigabytes per line is not
   workable, so the operator bumps a label instead.
3. `sample_rate` is a delivered-rate contract: an engine that returns another rate is an error, so the
   recorder and OBS always receive the configured format.
4. `provider: elevenlabs` is not added. It belongs to `P-067` §7.3's config shape, and nothing in the
   repository calls ElevenLabs yet.
5. Failures carry their own `failed` reasons, `local_engine_unavailable` and `local_speech_failure`, through
   an optional `failure_reason` on the exception; the native path still reports `native_speech_failure`.
   There is deliberately no fallback to the operating-system voice.

**Verification (2026-10-05).** Offline: the 39 new tests pass; 22 mutations of the new code were each caught
by a named test, and a separate mutation proved the bundle guard; Ruff is clean; the full offline suite is
1354 passed, 12 skipped, 1 xfailed. Real, on the Mac: `python -m stream_speech --validate` with the shipped
config (`valid: true`, the existing keys unchanged plus `voice_providers`) and with a local voice configured
but no engine (`valid: true`, `ready: false`, "no adapter for engine"); a local voice with `../` in a path
fails at load; native `stream_speech.render` still writes a 22050 Hz WAV.

**Not verified and not built.** Any engine adapter, installation or model (§5.3); a `model-registry` row
(§2.3); the A/B, latency, consistency and pipeline tests of §6, so every figure in §2 is still an estimate;
the voice studio's `stream_speech.render` and the Autopilot production driver, which still take native voices
only; audible playback and active-playback cancellation timing, which this slice did not re-run because the
playback path is unchanged (the router delegates to the native adapter); and D1–D3.

### Slice 2 — the blind audition rig (2026-10-05)

A separate pull request stacked on slice 1 and independent of it in code; same authorization and executor.

**What exists now:** `modules/audio-production/tts/audition.py` (standard library only) and
`tests/audio_production/test_voice_audition.py`.

- `build` renders the incumbent operating-system voice from a script (`--native LABEL[=VOICE]`, through the
  existing `render_reply` renderer) and/or takes WAVs rendered elsewhere (`--candidate LABEL=file.wav`). It
  copies each to a neutral `take-N.wav` in a seeded, recorded, shuffled order, attenuates the louder ones to
  the quietest's level (attenuation only, so nothing clips) and writes `key.reveal-after-ranking.json`. It
  prints only take paths; nothing it prints, or names a file after, identifies a voice.
- `reveal` takes the ranking (`--rank 2 3 1`, with `1=3` for a tie), unmasks it and records it once in
  `result.json`. With `--subject` it applies §6.1: ranked first (a tie counts), and not below the incumbent;
  below it, the rig says local voice is abandoned for the account.

**Why these controls.** Order, loudness and labels are the three biases a listening test like this is most
exposed to, and the rig removes all three. Format differences (sample rate, channels) can still reveal a voice
to someone who inspects the files; the rig warns rather than resampling, because a crude resampler would
colour the comparison.

**Limits.** Candidates must be 16-bit PCM WAV (`ffmpeg -i in.mp3 -c:a pcm_s16le out.wav` converts an
ElevenLabs download). `--native` takes at most 500 characters and needs macOS `say` or Windows System.Speech.
The `P-067` §7.5 mid-clip switch is not covered, and ElevenLabs is not called: the owner exports its renders
by hand. The rig makes the listening fair; it does not do the listening, so §6.1's pass condition is still
unmeasured.

**Verification (2026-10-05).** 30 tests. 24 mutations of the tool were run; 4 initially survived, each exposing
a missing test, and all 24 are now caught by a named test. Ruff is clean. A real run on the Mac with two
installed operating-system voices and a synthetic tone: a 20.5 dB loudness spread matched to -26.18 dBFS on all
three takes, neutral names only, a reveal recorded once and a second reveal refused. Not run: any listening,
any candidate other than OS voices, and Windows.

### Slice 3 — the clone-source recording checker (2026-10-05)

A third pull request, stacked on slice 2; same authorization and executor.

**What exists now:** `modules/audio-production/tts/check_voice_sample.py` (standard library only) and
`tests/audio_production/test_voice_sample_check.py`. It reads 16, 24 and 32-bit PCM and float WAV in 30 s blocks
(a 10-minute stereo 24-bit file takes about five seconds) and reports nine checks, each pass, warn, fail or skip,
with every measured number: format, length, clipping, level, noise, silence, dc, drift and bandwidth. Exit status
is 0 ready (warnings allowed; `--strict` counts them), 1 not ready, 2 unreadable. Measuring and grading are
separate, so every threshold boundary is tested directly.

**What it adds to §5.4's own pass condition.** `ffprobe` reports `48000`, mono or stereo, PCM, and an MP3 or AAC
converted to 48 kHz PCM reports exactly that and then clones its artifacts. The bandwidth check looks for the
low-pass those codecs leave behind.

**Validated against real signals, not only synthetic ones.**

- A real codec: Apple AAC through `afconvert`, over operating-system speech plus full-band room noise. The clean
  file is not flagged. At 24, 32, 48 and 64 kbps the cutoff is flagged at 7.2, 9.5, 14.2 and 16.1 kHz. At 96, 128
  and 192 kbps it is not flagged, because those cutoffs sit above the 17 kHz scan (a documented limit).
- Real speech (macOS voice written at 48 kHz): no cliff is flagged. Its own roll-off is gradual, about 28 dB over
  14-16 kHz, which is why the detector demands a 30 dB drop within 900 Hz rather than any steep slope.
- Synthetic brick-walls at 8, 11 and 15.9 kHz are located within 0.3 kHz, and a full-band signal is not flagged.
- The FFT agrees with a naive DFT to 1.7e-14.

**Not validated.** MP3 (no encoder here); any microphone recording; mains hum, which is not measured; and the
starting thresholds themselves, which are guesses at what a good recording measures until the first real one
exists. The report prints every number so the owner can judge them.

**Limits.** Not covered: room reflections and reverb, mains hum, register, varied content, splices that leave no
digital silence, and consistency between takes. A pass means the recording is not obviously broken, not that it
will clone well. The noise-floor estimate needs pauses, so a few seconds of room tone should open the recording.
Level, noise and spectrum use the first channel; clipping is checked on every channel.

**Verification (2026-10-05).** 68 tests. 28 mutations of the tool were run; 2 initially survived, each exposing a
missing test (a clipped stretch straddling a block boundary where neither side reaches three samples, and
negative-only clipping), and all 28 are now caught by a named test. Ruff is clean, the full offline suite is
1454 passed (12 skipped, 1 xfailed) on the Mac, and two of the 68 tests (real OS speech and the AAC round trip)
run only on macOS. Not run: any microphone recording, and Windows.

### Slice 4 — pre-render and timing (2026-10-05)

A fourth pull request, stacked on slice 3; same authorization and executor.

**What exists now:** `python -m stream_speech --prerender lines.jsonl` (`stream_speech/prerender.py`, wired into the
worker CLI) and `tests/audio_production/test_prerender.py`. It validates the whole script first, renders each line
through the same router the live worker uses, and streams one record per line (status `rendered`, `cached` or
`failed`, with render and audio seconds, a short text hash and never the text), then a summary with, per voice,
the renders, cache hits and failures and the p50, p95 and max render time. Only renders are timed, because a cache
hit is not a render. For local voices the summary applies §6.2's pass condition (p95 under 60 s) and reports
`met: null` until there are twenty rendered lines. This is `P-067` §7.4's "pre-render, never stream" step: it fills
slice 1's cache so every line plays at once, and it reports each line's real duration before pacing is chosen.

**The first measurement in this proposal, and it is of the incumbent, not of a local engine.** Twenty paragraphs of
254-473 characters through the default operating-system voice on an Apple M1 Pro with 16 GiB took p50 4.53 s,
p95 5.46 s and max 5.50 s, about 0.21 s of rendering per second of audio. That is the latency baseline for §6.1's
incumbent; every local figure in §2 is still an estimate.

**One change to the worker's error output.** In `--prerender` mode an error prints its message ("line 2 is invalid",
"voice 'x' is not configured") instead of only the exception type. Live modes still name only the type, because
viewer text can reach their errors; a pre-render script is operator-written and its errors never echo a line.

**Limits.** No local engine exists, so the local path is proven only with fake engines and a scripted clock, and the
pass condition has never been evaluated on a real engine. Native timings include process start-up. One run reports
one machine at one moment, so §6.3's consistency across sessions is not covered.

**Verification (2026-10-05).** 30 tests. 24 mutations of the new logic were run; 2 initially survived (scratch audio
piling up until the end of a long script, and an error message that could echo a line's text), each led to a
stronger test, and all are now caught. Ruff is clean and the full offline suite is 1485 passed (12 skipped,
1 xfailed). Real runs on the Mac: the 20-paragraph baseline above; a script with a local voice and no engine (the
local lines `failed` with `local_engine_unavailable`, the native line rendered, exit 1); and an unknown voice id and a
missing cache directory (both refused before anything rendered).

**Candidate next slices, none started.** The first real engine (Kokoro first: it needs no clone, but it needs
permission to download weights), with a `model-registry` row for every downloaded weight (§2.3); `provider: local` in
the voice studio's `stream_speech.render`; and Windows runs of slices 2-4.
