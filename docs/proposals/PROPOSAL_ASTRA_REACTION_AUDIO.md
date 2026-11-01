# Proposal: Astra-authored gaming reaction audio and scripted personality routing

> **Queue row:** P-066
> **Agent model / effort:** `gpt-6-astra` / `xhigh` — Speech/clip exclusivity, native approval UI and stale-event guards
> Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
> **Status:** In progress — implementation built; production acceptance remains open
> **Owner:** OpenTechnology14 + agent
> **Date:** 2026-09-26
> **Last updated:** 2026-10-04
> **Roadmap layers:** `ai-agents`, `audio-production`, `soundboard`, `automation-control`
> **Evidence level:** Offline contracts, real local generation/render, native Mac interface; no OBS playback certification

## 1. Executive summary

The owner authorized the full P-066 build on 2026-09-30, including the previously deferred
Stream app interface and operator-controlled script pause/Q&A. The local implementation is
available in **Stream Extend → Automated streaming → Personalities → Prompt & Voice Preview**.

Gaming personalities can generate an editable authoring prompt, produce phrase/audio previews,
save immutable revisions, collect feedback, approve exact prompt/audio output, and select a
manually bound Soundboard library. OpenTech, AI and technical personalities instead get approved
script segments, safe-boundary pause, one reviewed source-grounded answer, and explicit resume.

The implementation uses an installed **Ollama** model for text and the existing **native OS speech
adapter** for audio. “Astra” identifies the requested creation/implementation workflow, not a
separate TTS engine or on-air persona. No cloud generation, model download or voice cloning was
added. Nothing has been approved for production or broadcast by this work.

Start with the [operator and runtime guide](../../modules/automation-control/voice_studio/README.md).
The [routing reference](../architecture/stream-personality-audio-routing.md) makes personality
differences discoverable without reading implementation code.

## 2. Implemented scope and ownership

| Surface | Owner | Built behavior |
|---|---|---|
| Resolved persona prompt and bounded candidate/answer generation | `ai-agents/stream_host/author.py` | Uses existing persona catalog; structured Ollama candidates; source-only answer instructions; no control tools |
| Render/play subprocess contract | `audio-production/stream_speech/render.py` | Fixed native speech adapter; render-only never plays; explicit script playback is cancellable |
| Revision library, jobs and script cursor | `automation-control/voice_studio` | One local owner, atomic JSON, PCM checksums, approval gates, feedback, parent comparisons, selection history and restart recovery |
| Native Stream UI | `apps/stream-extend` | Bundled stdio bridge, prompt/phrase editing, preview/cancel, audition, approve/reject, bind/select/disable/export, scripted Q&A controls |
| Clip playback | Existing OBS Soundbox/Soundboard plugin | Still manually installed, loaded and hotkey-bound; no supported automatic sound-list import added |
| Reaction routing | `automation-control/stream_director` | Accepted manifest, one clip-or-speech route, fresh/session/generation guards, cooldown, fallback/drop and stop controls |
| Routed live speech | `audio-production/stream_speech` | Optional `reply_source: stream-director`; host control events still cancel stale speech |
| Worker composition | `automation-control/stream_autopilot` | Reject mismatched director/speech routing; stop OBS-owned clips separately from worker termination |

No new module, public listener, Compose service, environment variable, cross-app contract or cloud
worker was added. Existing configs keep P-066 production routing off by default.

## 3. Personality policy and logic mapping

| Policy | Examples | Reactions / ordinary speech | Soundboard | Script question behavior |
|---|---|---|---|---|
| `gaming-reactive` | Nova game variations | Accepted clip for a mapped reaction; live voice fallback or explicit drop; ordinary chat stays live voice | Eligible after review and manual binding | Existing host pause; no script authoring in this view |
| `opentech-scripted` | OpenTech, Stream Extend, Content Extend, Chatbot Routing shows | Operator-approved script and reviewed answer on AI-VOICE | Disabled | Finish segment → hold cursor → draft one answer from episode sources → approve/speak → manual resume |
| `technical-scripted` | AI Learning, AI Control Layer, future technology hosts | Same source-reviewed script path | Disabled | Same bounded operator flow |
| `review-scripted` | VideoReview | Approved commentary and optional reviewed Q&A | Disabled | Same manual script controls |

Policy is a declared persona field, not inferred from words, a social account, or gameplay
ownership. The app displays persona IDs, game/module context and policy; it resolves the same
catalog as the host and shows the selected Autopilot session separately. Authoring another
persona does not switch the on-air identity.

## Prompt, audition, alignment and improvement

This heading retains the original scope reference; the workflow is now implemented:

1. Generate the selected gaming persona's full editable prompt from resolved Nova identity,
   game instructions and reaction vocabulary. This does not overwrite the live host system prompt.
2. Edit prompt, phrases, installed voice and model; save a new revision.
3. Render the saved phrases, or generate candidates and render audio in one preview job.
   “Immediate” means on-demand, not an on-air generation promise or latency SLA.
4. Read and audition every sample, compare the parent prompt/phrases, and record feedback.
   App audition requires isolated monitoring plus connected, off-air OBS. File rendering has no
   playback side effect and can run without OBS.
5. Approve the exact prompt/text/voice/audio checksums. Reject preserves history. Editing,
   rerendering or a changed persona context requires fresh review.
6. Separately import/test the accepted WAVs in Soundbox, enter exact play/Stop All hotkeys and
   confirm local audio/track acceptance before selecting the revision.
7. The export applies at the next stopped worker/session boundary. Keep an earlier approved
   revision for rollback; improvements never replace it automatically.

Generation failures are visible; a configured phrase is never presented as model-generated.
Cancellation and late completion stay scoped to the original job/revision. Cancel/failure retries
create new revisions. Feedback is human-directed iteration, not automatic learning or retraining.

### Starter prompt for alignment

The app generates a persona-specific version. A shortened example for Nova Builder:

```text
Create original short spoken reactions for Nova in Minecraft.
Keep Nova's warm, curious and lightly self-deprecating persona.
Use one natural sentence, no more than 18 words, aiming for 2–6 seconds.
Describe only the supplied reaction; do not invent gameplay observations.
Make the situation or Nova's prediction the joke, never the viewer.
No URLs, insults, purchases or spam. Keep the installed voice identity.
Use configured reaction names only. Return at most eight JSON phrases.
You have no tools, playback, OBS or publishing authority.
```

The persisted prompt is authoritative for that revision. Native voices do not promise emotional
prosody merely because a prompt requests it. Audio duration, silence, clipping and checksum are
checked after synthesis; human listening remains essential.

## 5. Local library and approval contract

`library.json` records schema version, immutable revision IDs, parent revisions, resolved persona
context/hash, prompt, phrases, selected model, installed voice binding, phrase origin, feedback,
job ID, elapsed time, audio path/duration/peak/SHA-256, and approval hash/time. Separate production
pointers and activation history select an approved revision without rewriting it.

States are `draft → generating → ready → approved`; failure/cancel/reject remain reviewable and
cannot activate. Disable removes the production pointer while retaining accepted history.
A superseded selection remains an approved rollback candidate rather than being relabelled as
unreviewed. The shipped CC0 SFX manifest is unchanged.

Limits: 64 revisions, eight phrases each, 18 words/phrase and 12 seconds by default, 5 MiB/audio,
20 feedback records/revision and 1,000 activation records. PCM is 16-bit mono/stereo WAV; silence,
empty files and clipped peaks fail review. These are bounded local creator artifacts, not committed
media or automatically published assets.

An OS lock prevents two owners. Saves are atomic. Restart cancels interrupted work and reconciles
the exported `production.json` from the library. Invalid active assets fail closed in the export.
Approval is invalid after changed prompt/phrases/audio/context. The operator guide documents the
local data path, backup and limits.

## 6. Runtime routing and no-duplicate rule

1. Opt in using `phrase_manifest` and `phrase_fallback: live_voice | drop` in the director config.
2. Configure the paired speech worker with `reply_source: stream-director`; do not also run a
   direct-host speech worker. The production loader rejects a mismatched pair or unapplied director.
3. For an on-air, fresh, nonduplicate gaming reaction, match persona/game/voice/policy, check the
   accepted WAV checksum and registered OBS hotkey, then dispatch the clip.
4. A clip dispatch never also forwards that utterance to speech—even after an ambiguous timeout.
   Normal chat and scripted replies use routed live speech. Missing/unbound assets follow the
   configured fallback; cooldown suppressions drop instead of doubling speech.
5. Reports distinguish acknowledged `clip_dispatched`, `clip_dispatch_uncertain`, live fallback,
   missing/changed asset, unbound hotkey, cooldown, duplicate/stale and paused outcomes.
6. Pause/persona changes stop selected clip hotkeys. The supervisor requests Stop All independently
   because an OBS-owned clip survives director process termination.

Selections are pinned for the worker lifetime. The plugin has no supported file-list API here:
the operator must verify that each hotkey actually points to the reviewed WAV. An acknowledgement
is not an audible-playback proof. OBS failure still needs its local Stop All/mute control.

This is **per-event exclusivity**, not an audio mixer or automatic ducking. Simultaneous unrelated
commentary/reactions, final bus levels and avatar timing require separate integration acceptance.
No invented clip-start timing is sent to the avatar.

## 7. Scripted pause/question contract

The originally “future” manual Q&A slice is now built. Load a reviewed script (paragraph segments)
and permitted episode sources. Only scripted policies can load it; only gaming policies can create
Soundboard drafts.

- Play renders/speaks segments through the native adapter on the operator-routed AI-VOICE output.
- Pause finishes the current segment and holds the next cursor. Stop cancels current synthesis/
  playback; a later resume can repeat an interrupted segment, never silently advance past it.
- Admit one bounded operator-entered question per pause. Model input includes only the question
  and supplied sources; sources/questions cannot become commands.
- Draft a bounded source-only answer. Model failure produces a deferral for review. The operator
  must check/edit and explicitly approve it before speech; generation is not a factuality guarantee.
- Speak the reviewed answer without changing the script cursor. Resume is always manual.
- Restart stays paused; leaving the panel stops script speech. Answers are not saved as clips.

Keep competing host/speech workers stopped while using this manual player. No live chat question
ingress, source retrieval, scheduled script runner, timed OBS captions, auto-resume or general
factuality validator is claimed. Those remain extensions, not hidden behavior of this build.

## P-066-UI — Stream Extend prompt and voice preview (backlog)

**State:** Implemented; native Windows and complete production audition/OBS acceptance remain open.
The backlog label/anchor is retained for existing links. This is a child of P-066, not a new module
or P-067 walkthrough feature.

Location: **Automated streaming → Personalities → Prompt & Voice Preview**. The native
`voice_studio_request` command uses a bounded strict JSON request over a fixed bundled stdio
worker, with no shell or arbitrary executable path. It requires the existing Automation / Control
Python environment. The local library persists between app launches.

The UI includes generated prompt editing, model/voice configuration, candidate editing, save-new,
render/generate/cancel, isolated audition/stop, feedback, parent comparison, approve/reject,
manual binding, select/disable/export and rollback by reselecting an older accepted revision.
Scripted personas show script/source review, cursor/state, pause/stop, question and answer approval
instead of Soundboard authoring.

## 9. Acceptance and verification

| Gate | Evidence / status |
|---|---|
| Persona prompt/context and bounded phrases | Focused studio tests; real local prompt/model/render smoke |
| Review/approval/activation separation and rollback | Focused immutable revision, checksum/context tamper, restart and rollback tests |
| Cancel, early cancel and retry | Focused tests; early-cancel race reproduced failing and fixed |
| Clip-or-speech exclusivity | Focused accepted/missing/tampered/unbound/uncertain/scripted/drop and duplicate tests |
| Session, generation, pause and stop | Existing director tests plus new phrase controls and supervisor Stop All contract |
| Script pause, reviewed answer and cursor resume | Focused blocked approval, one-question, boundary/cancel/restart tests |
| Actual local generation and WAVs | 2026-09-30: installed `qwen2.5-coder:7b` produced four phrases/WAVs in 20.329 seconds, 1.477–1.787 seconds each; PCM checks passed; not approved or played |
| Stream desktop | Svelte check/build, Rust contracts and native bundle; native Mac studio catalog/fields inspected |
| Required repository verification | Full offline suite reached 100% before interruption; final rerun recorded below |
| OBS import, correct hotkey/file mapping, audible one-path output, tracks, monitor isolation and local recording | **Open**; no live acceptance or broadcast performed |
| Native Windows speech/UI | **Open**; Mac builds/mocks do not certify Windows |
| Owner alignment on production prompt and sound | **Open by design**; implementation does not approve creative output on the owner's behalf |

The real generation smoke is `scripts/testing/voice_studio_smoke.py`; it reports its temporary
artifact library and never approves, plays or broadcasts. Run it with an already-installed model.
See the [verification matrix](../agent/VERIFICATION-MATRIX.md) and
[operator guide](../../modules/automation-control/voice_studio/README.md) for commands.

### Implementation verification — 2026-10-02

The 2026-10-02 pass was interrupted before its results were written down, and the implementation
stayed uncommitted until 2026-10-04. It was then moved onto a clean branch from `main`, merged with
the queue and docs changes that had landed meanwhile, and re-verified. The results below are from
that run; none is carried over from the interrupted pass.

| Check (2026-10-04, merged branch) | Result |
|---|---|
| `ruff check modules/ scripts/` (Ruff 0.6.4, the CI pin) | All checks passed |
| `pytest -q`, offline suite (pytest 8.3.2, the CI pin; Python 3.12 where CI uses 3.11) | **1295 passed, 12 skipped, 1 deselected, 1 xfailed; exit 0.** The 12 skips are missing optional dependencies (`fastapi`, `asyncpg`) and intentional ComfyUI workflow stubs, none in P-066 code |
| New P-066 test files | `test_voice_studio.py` 15 passed; `test_phrase_routing.py` 13 passed |
| `scripts/testing/voice_studio_smoke.py --model qwen2.5-coder:7b` | Real local Ollama generation and native render: status `ready`, four WAVs (mono, 22.05 kHz, 16-bit PCM), 4.16–5.62 s each, 23.5 s elapsed. **Not approved, not played.** Wording varies from run to run and this run's clips are longer than the 2026-09-30 run's, so these are candidates for owner review, not evidence of final quality |
| Rust bridge, static check only | All 18 `include_str!` sources exist, and `tokio` has the `full` feature set the bridge uses. **`cargo test`, the Svelte check and the native bundle were not re-run locally**; the `build-desktop-apps` CI job on the pull request is their evidence |
| Stream Extend frontend and Rust, Linux x86_64, 2026-10-05 (the P-066 voice studio including the bridge-bound tests) | `npm ci`, `npm run check` (252 files, 0 errors, 0 warnings) and `npm run build` pass. `cargo test --locked` in `apps/stream-extend/src-tauri`: **15 lib tests and 13 `obs_contract` tests pass**. Needed the GTK/WebKit dev packages (`libwebkit2gtk-4.1-dev` and friends) installed first |
| Voice studio bridge bounds, new in that run (7 tests in `voice_studio::worker_tests`, Unix only) | Drive the real bridge against fake `sh` workers: 64 KiB request cap (65 535 B accepted, 65 536 B refused before any worker starts), missing-environment message, ok/error mapping, one worker reused across calls, a refused request keeps the session, and an oversized reply, a worker exit or a non-JSON reply each discard the session so the next call starts a fresh worker. **Mutation-checked:** raising the request cap by one byte, widening the 16 MiB response cap to 64 MiB, and keeping the session after a failure each make a test fail. Fifteen repeat runs were stable. The 70 s timeout is **not** exercised (it is not injectable) |

Still not run locally: the native bundle, and any Mac or Windows build. A Linux `cargo test` does not
certify either platform; the `build-desktop-apps` and native-rehearsal CI jobs remain their evidence.

P-066 stays **In progress** until the open release gates above have evidence. No module is
promoted to production because tests or a bundle succeed.

## 10. Rollout, rollback and documentation

The generated library is opt-in and local-only. Rendering/review requires no broadcast. Activation
requires separate owner approval and manual OBS acceptance. Roll back by stopping playback,
selecting an earlier approved revision or disabling saved phrases, exporting, and restarting the
paired director/speech workers. Do not delete source WAVs as the first rollback action.

The routing reference, module READMEs, setup guides, agent matrices, API command ledger and audit
record are updated alongside implementation. The canonical roadmap layers remain unchanged.
