# Stream Autopilot director

P-056's native, local integration worker coordinates the existing DJ Soundbox (`soundboard`)
and stream modules. It consumes the conversational host's events through the authenticated
backend. It does not import another module's Python internals, synthesize its own audio clips,
or replace the soundboard plugin.

| Existing module | Implemented integration |
|---|---|
| `soundboard` | Game reaction → registered manifest slot → explicitly mapped OBS hotkey; global clip cooldown; optional stop hotkey on pause |
| `creator-experience` | Pause/resume → configured existing OBS program scene |
| `audio-production` | Pause → mute the configured AI voice input inside OBS |
| `broadcast-graphics` | Host reply → existing NodeCG `lowerThird` through backend `PUT /overlays/lowerThird`; timed hide |
| `automation-control` / n8n | Optional pause/resume/persona → existing authenticated `/automation/trigger`; reports queued, not workflow complete |
| `backend-api` | Authenticated host-event subscription, graphics API, and persisted director action results |
| `ai-agents` | Session/generation/timestamp-aware replies and controls from `stream_host` |

The existing table describes the current SFX/reaction integration. [P-066](../../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md)
adds a second, explicitly reviewed asset type for short spoken gaming reactions. The director
must resolve the profile's audio policy before dispatch: an accepted phrase clip suppresses the
matching live speech event; an unavailable clip follows the declared live-voice fallback or drops
with a named reason. OpenTech and general AI/technology scripted profiles are Soundboard-disabled.
That last rule is already enforced: host replies carry the persona's `audio_policy`, and any
policy other than `gaming-reactive` skips a mapped slot with the reason `scripted_audio_policy`.
The field can only withhold a clip, never select one; replies without it keep the legacy path.
The model never supplies a raw hotkey, filename, scene, or destination.

Opt into P-066 with `phrase_manifest` and `phrase_fallback: live_voice` (or `drop`). Pair it with
speech `reply_source: stream-director`; the applied director becomes the single reply router.
Accepted WAV checksums/persona/game/voice and exact hotkey availability are checked before dispatch.
Uncertain dispatch never retries or falls through to speech. Revisions are pinned until restart.
See the [voice studio runtime hookup](../voice_studio/README.md#runtime-hookup-exactly-one-spoken-reaction-route)
for full configuration, manual plugin loading and OBS acceptance. An OBS hotkey acknowledgement
does not certify that the intended WAV was audible on the correct track.

Avatar rendering, full-body effects, continuous voice playback, automatic music ducking and
Prometheus dashboards are not added here. In particular, a text reply is not a speech-start
event: ducking and lip sync need actual playback timing. Director results are available to
future monitoring through `events.stream-director.action_result` and structured stdout now.

## Local setup and preview

From the repository root, using Python 3.11+:

```bash
.venv/bin/pip install -r modules/automation-control/stream_director/requirements.txt
PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director --help
PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director --validate
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host \
  --rehearsal --input configs/local/stream-autopilot-demo.jsonl > /tmp/host-director-input.jsonl
PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director \
  --input /tmp/host-director-input.jsonl
```

Create a virtual environment first if needed, following [the conversation worker's setup](../../ai-agents/stream_host/README.md).
The default is a **preview**: no OBS requests, overlay writes or workflow triggers. Run the
last two commands together: records older than the configured TTL are discarded, including
old fixture outputs. Control events now carry `created_at` as an additive host-output field.

Configuration lives in [stream-director.yaml](../../../configs/local/stream-director.yaml).
It uses the actual [soundboard registry](../../soundboard/sounds/manifest.yaml), including
Victory Fanfare, Record Scratch, Dramatic Impact and Wrong Answer. Unknown slots fail validation.
Placeholder slots still need user-supplied files loaded into the dock; validation of a registry
name does not prove the corresponding clip is installed. Default routes use bundled clips.

The committed config enables lower-third previews and reaction mappings, but leaves OBS
hotkeys, scenes and the voice input **unbound**. Unbound sound routes report
`unbound_sound_slot`. Nothing guesses hotkey names or synthesizes keyboard shortcuts.

## Bind to the existing soundboard and OBS

1. Complete [soundboard setup](../../soundboard/setup/manual.md): install the plugin and load
   the named clips in its dock. Clip loading/installation are still manual.
2. Enable authenticated OBS WebSocket and export `OBS_WEBSOCKET_HOST`, `OBS_WEBSOCKET_PORT`
   and `OBS_WEBSOCKET_PASSWORD`. These are existing repo environment variables.
3. Discover the running OBS instance's names (read-only):

   ```bash
   PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director --discover-obs
   ```

4. Put exact registered hotkey names into `sound_hotkeys`, keyed by manifest slot. The list
   contains **all OBS hotkeys**: verify each selected name belongs to the intended Soundboard
   clip, not a streaming/recording operation. Test the clip in OBS itself once. `stop_sound_hotkey`
   is the plugin's stop action, if exposed by the installed version.
5. Optionally bind `pause_scene`, `resume_scene` and `ai_voice_input` from the discovered scene
   and input names. A logical bus label such as AI-VOICE is not automatically an OBS input name.
6. Select `on_air_session`. Only that session can change this broadcast; other simultaneous
   game conversations cannot play clips or overwrite its caption.

The adapter uses OBS v5 `GetHotkeyList`, `TriggerHotkeyByName`, `SetCurrentProgramScene` and
`SetInputMute`. It checks hotkey registration before each invocation and handles OBS authentication.
It never retries an uncertain action. The [OBS protocol](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md)
describes generic hotkey support as best-effort: an acknowledgement does not prove a plugin
played audible sound. Verify the installed plugin/OBS combination and mixer track assignments.

## Connect the existing backend and graphics

Export `AUTOPILOT_BACKEND_URL` and `HCP_API_KEY` as for the host worker. Start the existing backend
and NodeCG stack separately and add the existing lower-third graphic as an OBS Browser Source.
No new API route, public listener, service, or Compose container is added by this worker.

```bash
# Observe configured actions against fresh live host events:
PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director --backend
# Apply configured bindings after setup:
PYTHONPATH=modules/automation-control .venv/bin/python -m stream_director --backend --apply
```

`--apply` is also available for fresh file input. Configuration validation and OBS discovery
are read-only modes and reject `--apply`. The worker reads exported environment variables; it
does not automatically load `.env`. No networking is needed for file preview.

Backend subscriptions are only `events.stream-host.reply` and `events.stream-host.control`.
Source payload kind must match the topic. Chat/model output never specifies a raw OBS command,
workflow name or sound filename: those come only from the operator config. The lower-third
bundle renders title/subtitle using `textContent`.

The existing `lowerThird` replicant is global. Reserve it for this director while running;
do not run two directors against the same overlay/OBS instance. Independent broadcasts need
separate graphics/backend state, not just different session IDs. This worker has no dynamic
on-air session switch or remote provisioning interface.

## Pause, failures and recovery

Pause mutes the configured AI voice OBS input, triggers the configured sound stop, hides the
caption and switches to the configured pause scene. Each action is independent; a missing
sound plugin cannot prevent the following graphics/scene action. Optional configured automation
triggers queue through the existing backend API with session/event/generation metadata.

Resume can switch the scene and hides old captions. **It leaves AI voice muted**: the initial
speech adapter has no playback cancellation/flush handshake, so unmuting could reveal stale
audio. The operator verifies the voice bus and unmutes it manually. This does not mute the
system speakers or cancel a TTS process; retain an independent physical/local mute control.

Captions hide after the configured duration. A newer reply replaces the timer; generation
changes/pauses cancel it. Duplicate events, expired events, off-air events and older generations
are ignored. Deduplication is bounded to 1,024 records within the event TTL window. Clip cooldown
is global to this broadcast and is reserved before dispatch, including failed/uncertain requests.

No blind retries. Backend disconnect stops the worker and cancels pending caption timers.
Shutdown attempts to hide a lower third only if this worker successfully wrote it. It does not
start/stop streaming or alter unrelated inputs. Backend audit failures leave results on stdout
and do not disable subsequent module actions. File-apply exits nonzero when an action fails;
continuous backend mode reports failures and keeps processing future input.

Requests are bounded but serialized; this is not a hard-real-time emergency-stop implementation.
After restarting the host worker, restart this director too: generation counters are currently
process-local, and durable run IDs/reconnect reconciliation are not implemented.

## Verification and current limits

Run `make test`, the focused `tests/automation_control/test_stream_director.py` suite, and
`ruff check modules/ scripts/` with the repo's CI version. Tests cover scoping, stale events,
duplicates, cooldowns, unbound slots, caption expiry, pause behavior, independent failures,
preview isolation, exact backend/OBS requests, n8n queue semantics and OBS wire authentication.

Verified on 2026-09-08: 37 combined director/host/speech tests pass on Python 3.12; `make test`
exits 0; Ruff 0.6.4 passes repository-wide. Real host CLI output → director file preview produces
four preview actions, ignores one off-air event and reports one unbound sound slot. Configuration
validation and all four relative README links pass. Attempted live `--discover-obs` at the test endpoint
`127.0.0.1:4455`: connection refused, exit 1. Live plugin playback, OBS scene/mute changes,
NodeCG visual output, backend delivery and n8n execution are therefore not claimed as verified.
P-056 and the owning modules remain in progress/scaffolded.

All execution is local. There is no DigitalOcean/cloud director deployment; the creator's
camera, OBS and soundboard do not gain a cloud dependency.

## Human / agent gameplay handoff

`handoff.py` implements a separate input-ownership state machine. It never stops OBS or changes
Nova's session, persona, voice, sound bindings or graphics. The intended operator controls are
**Take control**, **Let agent play**, and **Pause gameplay agent**. Pausing gameplay differs from
pausing the conversational host. The AI can continue commentary while the human plays.

`GameplayHandoff.switch("manual")` invalidates the old input epoch immediately, then requires
an adapter acknowledgement that the agent stopped and released held inputs. Switching to
`"agent"` first releases prior inputs, then requires a fresh game-state synchronization receipt.
Every actual agent input must call `permits_agent_input(epoch)` immediately before injection.
Timeout, missing adapter, stale acknowledgement or failure leaves ownership blocked; it never
reports a successful human takeover without the release receipt. Late responses cannot restore
agent ownership. An unresolved adapter operation blocks further starts until resolved.

This is a tested adapter contract, **not a live game controller or installed UI buttons**.
A concrete adapter, authenticated operator endpoint/hotkey binding and device-level input release
still need implementation and live acceptance. A controller that ignores epoch checks cannot
be stopped by this Python contract alone. Console and PC input devices need separate adapters;
interchangeability is a show-level requirement, not evidence that all devices permit automation.
Do not enable agent gameplay in a game/mode without a supported, permitted adapter.
