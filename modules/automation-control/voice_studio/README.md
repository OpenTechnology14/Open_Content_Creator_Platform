# Personality voice studio (P-066)

**Labels:** `Stream` · **Status:** Built locally; OBS/track and native Windows acceptance remain open.

Stream Extend → **Automated streaming → Personalities → Prompt & Voice Preview** is the operator
surface. It uses the existing resolved persona catalog, including the selected Autopilot session;
choosing an authoring persona does not switch the on-air session.

## Two delivery paths

| Persona policy | Author/review | Output |
|---|---|---|
| `gaming-reactive` | Editable prompt → Ollama phrase candidates → local voice render → audition → exact-revision approval | Manually loaded OBS Soundbox clips for reactions; configured live voice fallback for missing clips; normal chat remains live voice |
| `opentech-scripted`, `technical-scripted`, `review-scripted` | Operator-approved script and episode brief → safe-boundary pause → one source-grounded answer draft → explicit answer approval → manual resume | Native speech on the operator-routed AI-VOICE bus; never Soundboard |

“Astra” in the proposal names the requested implementation/authoring workflow, not a new speech
engine or on-air identity. The implemented text provider is an installed Ollama model. The speech
renderer is the existing macOS/Windows native adapter. Delivery instructions do not implement
emotion controls, voice cloning, or a different installed voice.

## Setup and local CLI

In Stream Extend, install **Automation / Control** through Module setup. Its existing requirements
provide Pydantic, YAML and HTTP dependencies. Install a local Ollama model separately for generated
phrases and Q&A; the app neither downloads a model nor spends API credits. Rendering edited phrases
does not require Ollama. An installed system voice is required. OBS is not required for rendering;
the app requires connected, off-air OBS and an isolated output confirmation before auditioning.

The standalone service uses one JSON request per stdin line, one `{ok,data}` or `{ok,error}` reply
per stdout line. EOF cancels active render/playback children. Use Python 3.11+ with
`stream_director/requirements.txt` installed:

```bash
PYTHONPATH=modules/automation-control python -m voice_studio --library /absolute/local/phrase-library
```

Then send, for example:

```json
{"action":"create","persona_id":"nova-builder","model":"your-installed-model"}
```

Use the returned `revision_id` with `preview` (`generate:true` combines phrase generation and
audio rendering), `status`, `cancel`, `feedback`, `revise`, `reject`, `approve`, `activate`,
`disable`, `audio`, or `export`. CLI `audio` returns WAV bytes as base64; it never plays them.
`Request` in [studio.py](studio.py) is the strict, bounded request schema. Only an operator-owned
local process should call this API; there is no HTTP listener or remote-control endpoint.

Configuration: [voice-studio.yaml](../../../configs/local/voice-studio.yaml). `OLLAMA_HOST` and
`OLLAMA_MODEL`, when set, override the configured endpoint/model. No new environment variable is
required. The app bundles a config snapshot with its runtime; repository config changes require
rebuilding the app. Per-revision model/installed-voice selection remains editable in the UI.

App storage is the OS local application-data directory under
`HybridCreatorPlatform/voice-studio/library`; the CLI uses the explicit directory above.
Do not commit generated WAVs. Back up the **entire** stopped library together; there is no automatic
cloud backup or DigitalOcean worker. Soundbox and speech playback must remain on the workstation.

## Review, revision, and production gates

1. Generate the persona prompt. Review/edit the prompt, reaction texts, installed voice and model.
2. Save edits as a **new revision**. Choose **Render saved phrases**, or **Generate AI phrases +
   audio**. Rendering does not play audio, approve anything, or touch OBS.
3. Audition every sample off air, leave feedback, compare with the parent revision, and approve
   the exact prompt/phrases/voice/WAV checksums. Reject retains history. Cancel/failure requires a
   new revision before retry. Preview results remain attached to their original revision.
4. Manually import each accepted WAV into OBS Soundbox and test the exact play and Stop All
   hotkeys, levels, and recording track. Enter those hotkey names and explicitly select the
   approved revision for production. The app cannot install/configure Soundbox or prove a hotkey
   points at the intended file; the operator's recording test is essential.
5. Export `production.json`. Configure the director/speech pair below and restart them at a stopped
   session boundary. A running director pins its manifest; selection changes do not hot-swap it.
6. Improvements never replace the active revision automatically. Roll back by selecting an older
   approved revision and reconfirming its bindings. Disable removes a persona from the next
   manifest without deleting the recordings or review history.

The library stores resolved persona context/hash, parent revision, prompt, model, voice binding,
phrase origin, feedback, job ID, elapsed time, PCM duration/peak/checksum and approval hash/time.
Native output must be nonempty, nonsilent, unclipped 16-bit mono/stereo PCM WAV, under 5 MiB and
the configured duration. Text checks bound words/reactions and known blocked content; they are not
a substitute for editorial review. Limits: 64 revisions, eight samples/revision, 20 feedback entries
per revision, 1,000 activation records. Archive the whole stopped library before those limits.

An OS file lock prevents concurrent app/CLI owners; JSON saves are atomic. Interrupted jobs reopen
as failed/paused, never approved or playing. Startup reconciles the export from the authoritative
library and clears invalid exported selections. No approval can survive changed audio/context.

## Runtime hookup: exactly one spoken reaction route

In an operator-owned copy of `configs/local/stream-director.yaml`:

```yaml
phrase_manifest: /absolute/local/phrase-library/production.json
phrase_fallback: live_voice # or drop
```

In the matching speech config:

```yaml
reply_source: stream-director
```

Point `director_config` and `speech_config` in the local `stream-runtime.yaml` copy at those files
and set `director_apply: true` only after OBS acceptance. The production loader rejects a mismatched
pair or preview-only director. For independently launched workers, use that same speech source;
do **not** also launch a default direct-host speech worker. Keep their `on_air_session` values equal.
Existing repository defaults preserve the legacy SFX route and direct-host speech until opted in.

The director checks persona/game/voice/policy, timestamp, session, generation, duplicate ID,
asset checksum and registered hotkey before dispatch. It forwards only fallback or conversational
replies to `events.stream-director.reply`; the routed speech worker still receives host controls.
Scripted policies cannot select a clip. Cooldown suppression drops a reaction instead of voicing
it twice. An uncertain play request is never retried or followed by live speech. Audit records
distinguish acknowledged dispatch, uncertain dispatch, fallback and drop; OBS acknowledgement is
not proof of audible playback. Pause/persona controls stop configured clips. The supervisor also
requests Stop All directly because terminating the director cannot stop an OBS-owned clip.
If OBS is unreachable, use its local Stop All/mute; remote acknowledgement cannot guarantee silence.

This is per-event exclusivity, not an audio mixer. Avoid overlapping unrelated live commentary and
reaction events; final bus levels, ducking, output devices and clip playback timing remain OBS/audio
acceptance. No synthetic Soundbox playback event is claimed as real avatar lip-sync timing.

## Script pause and source-reviewed answers

Select a scripted persona, paste approved script paragraphs (1–500 characters each, at most 100)
and the permitted episode sources. Review/load, confirm the OS output route and that competing
host/speech workers are stopped, then Play. **Pause at next boundary** finishes the current paragraph
and holds the next cursor. **Stop voice now** cancels synthesis/playback immediately; resuming may
repeat the interrupted segment rather than silently skip it. Navigating away stops script speech.

At a pause, the operator enters one bounded question. The configured model drafts from the supplied
sources only; model failure produces a deferral for review. The operator must check/edit and approve
the answer before it is spoken. No automatic source retrieval, chat ingress, factuality guarantee,
or automatic resume is claimed. Resume is explicit and keeps the script cursor. Restart stays paused.
The answer is temporary native speech, never a saved Soundboard phrase. UI state labels expose
playing/pausing/paused-for-question/answer-review/answering/finished; OBS captions are not added by
this manual script player. Schedule/chat integration remains a later extension.

## Verification

```bash
python -m pytest tests/automation_control/test_voice_studio.py tests/automation_control/test_phrase_routing.py -q
python scripts/testing/voice_studio_smoke.py --model your-installed-model
make test
```

The smoke creates a temporary local library, renders real audio and reports artifact paths, counts,
durations and elapsed time; it never approves, plays, imports into OBS, or broadcasts. Verification
evidence and remaining release gates are recorded in [P-066](../../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md).
