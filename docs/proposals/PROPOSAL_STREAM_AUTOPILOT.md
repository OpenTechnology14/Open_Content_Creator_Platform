# Proposal: Stream Autopilot — embodied AI host and game sessions

**Queue row:** `P-056`
**Agent model / effort:** `gpt-6-astra` / `xhigh` — Streaming, gameplay, speech/avatar guards and recovery
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — conversation, continuous speech, playback-timed avatar control, Twitch ingress, production supervision and stream direction built; live account/OBS/avatar/game acceptance open. State is authoritative in [the queue](../PROPOSALS.md).
**Owner:** OpenTechnology14 + agent
**Date:** 2026-09-08
**Roadmap layer(s):** Automation / Control, Character / Avatar, Realtime AI, Backend / API; existing AI Agents and Audio Production modules
**Evidence level:** Verified first-slice code/tests/rehearsal/speech export; Proposed full integration

## 1. Executive summary

Stream Autopilot coordinates an AI host that appears on stream, speaks, responds to viewers,
reacts to game events, and changes personality with the game. Optional game adapters eventually
let it play supported games and manage multiple independent sessions on one workstation.

This is a product capability spanning existing modules. The proposed coordinator lives at
`modules/automation-control/stream-autopilot/`. It must not duplicate avatar rendering, model
inference, speech synthesis, or chat reasoning. A new top-level module would duplicate the
current roadmap boundaries; that alternative needs an explicit layer/deviation decision before
implementation. The nested coordinator preserves the current layer map.

Recommended first release: one local AI co-host, one game/session, one avatar and voice, Twitch
chat, per-game persona configuration, OBS preview, and an immediate mute/pause control.
Autonomous gameplay and concurrent games have separate acceptance gates. No end-to-end runtime
is complete yet; the first working slice is recorded in §10 below.

## 2. Verified current state

Inspected locally on 2026-09-08:

- [Agent loop](../../modules/ai-agents/local-llm/agent.py): subscribes to global `chat.incoming`,
  calls Ollama, retrieves/stores memory, applies regex moderation, and publishes global
  `agent.reply`. The inspected loop does not synthesize or play speech.
- [Caddy persona](../../modules/ai-agents/local-llm/personas/caddy.yaml): one golf personality.
  The loop reads `name`, `system`, and `style`; its `guardrails` and `moderation` YAML fields
  are not a complete enforced per-persona policy.
- [Avatar bridge](../../modules/character-avatar/vtube/avatar_control.py): applies VTube Studio
  talking/idle hotkeys using estimated text duration. It has neither audio-timed lip sync nor
  a full-body animation runtime.
- [Agent setup](../../modules/ai-agents/setup/automated.md): datastore setup exists; agent
  service setup does not. Its suggestion that publishing a stop event is sufficient is not
  supported by the inspected agent loop, which subscribes only to `chat.incoming`. Correct
  that instruction when implementing the actual stop contract.
- [Roadmap](../architecture/roadmap.md): rendering, effects, and orchestration are separate
  layers. [Verification matrix](../agent/VERIFICATION-MATRIX.md) requires actual input and
  hardware evidence before calling their integration implemented.

These are code observations, not live OBS, voice, GPU, or game acceptance evidence.

## 3. Problem, goals, and non-goals

Actors: creator/operator, viewers providing untrusted chat, local host agent, game adapter,
and streaming platform. The creator controls session lifecycle and permitted capabilities.

Required product behaviors:

| Capability | Intended behavior |
|---|---|
| Human with effects | Creator drives camera/microphone; local face effects and optional body tracking/restyling feed OBS |
| Fully synthetic host | Original avatar idles, gestures, looks toward targets, emotes, and lip-syncs without requiring a person on camera |
| Per-game personality | Versioned profile selects identity, voice, tone, game vocabulary, reactions, and catchphrase rules |
| Conversation | Select relevant chat, produce bounded replies, moderate, speak, show captions, and animate |
| Game awareness | Prefer structured events; optionally use local screenshot interpretation when no game API exists |
| Gameplay | Game-specific adapter observes, acts, stops, and reports action results |
| Multiple games | Separate identities, memory, audio, captures, game clients, and control state per session |
| Stream direction | Start/stop within operator-configured authorization, scenes, breaks, fallback, and health handling |

Proposed first-release performance gates on the declared reference workstation: p95
accepted-chat-to-first-audio at most 4 seconds; captions and mouth state within 150 ms of
playback; local mute/pause acknowledged within 250 ms; a 60-minute recording with no cross-session
speech and no sustained OBS rendering/encoding lag above 1%. These are targets to measure,
not performance claims. Capture input/output timestamps and hardware configuration with results.

Exclusions from the first release: universal game-playing competence, ranked multiplayer bots,
anti-cheat bypass, unattended purchases, photorealistic full-body video generation guarantees,
cloud-dependent realtime processing, and distributed workers.

## 4. User paths and states

| Path | Expected behavior |
|---|---|
| First run | Choose co-host or autonomous mode, game, avatar, voice, capture source, audio device, and OBS scene; run readiness checks and local preview |
| Normal operation | `stopped → preflight → preview → running`; profile revision stays fixed for each in-flight utterance |
| Missing dependency | Identify the missing avatar/model/audio device/OBS/game adapter; block only the affected capability |
| Invalid configuration | Reject unknown profile IDs, unsupported schema versions, nonexistent devices, conflicting sessions, and unreasonable limits before execution |
| Chat flood | Bound queues, deduplicate message IDs, expire stale messages, limit per-viewer selection, expose drop counts |
| Internet loss | Platform chat disconnects; local preview/avatar remains available; no stale chat replay on reconnect |
| LLM/TTS loss | Cancel the failed utterance, display degraded status, use an optional configured local fallback clip with cooldown |
| GPU overload | Preserve game capture and OBS; lower optional effect quality, then pause AI inference; refuse additional sessions |
| Retry | Back off read/connect operations; reconcile OBS/game state before retrying actions; never blindly repeat start, purchase, or input commands |
| Pause/cancel | Cancel queued and active speech, release game input, idle avatar, keep or switch capture according to operator settings |
| Emergency stop | Independent local control silences playback and releases inputs even if the LLM is hung |
| Restart/recovery | Restore configuration and show last state; resume in preview, requiring a deliberate operator resume for autonomous actions |
| Upgrade | Validate versioned profiles, preserve previous revision, and reject unsupported schema versions with an actionable message |

## 5. Architecture and data flow

All game rendering, OBS composition, face/body processing, avatar rendering, language inference,
and default speech synthesis run locally. The platform chat connection necessarily uses the
internet. Optional remote management must use the existing authenticated backend/tailnet path.
Cloud voice is opt-in and is not required for the baseline.

```text
Twitch chat → backend chat adapter → session event routing
Game telemetry → backend event ingress → session event routing
                                         ↓
                   Stream Autopilot selects events and manages lifecycle
                                         ↓
                     AI Agents: persona + context + response
                                         ↓
               Audio Production: local speech + playback timeline
                                         ↓
              Character / Avatar: lips + expressions + body gestures
                                         ↓
             Creator Experience: OBS game capture + host + captions

Authorized gameplay mode → game adapter → observed result → event ingress
```

Modules communicate through versioned backend contracts; do not import each other's internal
Python modules. Standalone coordinator tests use recorded events and fake adapters. Production
adapters require explicit endpoints from configuration. Raw webcam frames stay local and are
not stored by default. Memory must use `(channel_id, session_id, game_id, persona_id)` isolation.

Body presentation has two distinct paths: tracking and filtering a real performer, and animating
a synthetic rig. An unattended host needs the latter. Start with an original VRM character,
animation clips and procedural gaze/blink, then add camera-driven pose retargeting. Photorealistic
face/body synthesis is a later benchmarked effects option, not a prerequisite for speaking.

## 6. Direct injection map

This is the target injection map, not a claim all paths exist. The actual first-slice paths
and deviations from delivery order are recorded in §10.

| Location | Symbol/surface | Before | Proposed change | Example | Verification |
|---|---|---|---|---|---|
| `modules/automation-control/stream-autopilot/` | `SessionSupervisor` | No coordinator | Lifecycle, bounded scheduling, readiness, adapter health, pause | `pause(session_id)` | Timeout/cancellation and state-machine tests |
| `configs/local/stream-autopilot.yaml` | Profile/session catalog | No game session config | Versioned profiles and workstation budgets | Contract below | Invalid config and isolation tests |
| `modules/ai-agents/local-llm/agent.py` | `run`, `load_persona` | Global channels and one persona | Session context, strict profiles, output schema, cancellation | `utterance_id` + profile revision | Concurrent-session and stale-output tests |
| `modules/character-avatar/vrm/` | `AvatarRenderer` | VTS hotkey path only | Locally bundled VRM renderer, expression and body commands | `gesture: celebrate` | Real OBS browser-source recording |
| `modules/audio-production/tts/` | `SpeechWorker` | No speech in inspected agent loop | Local synthesis, chosen audio device, captions/timing events, hard mute | `speech.started` | Actual audio loopback and cancellation |
| `modules/backend-api/fastapi/app/routers/autopilot.py` | Versioned session API | Absent | Authenticated lifecycle/status/profile operations | `POST /api/v1/autopilot/sessions` | Authorization and malformed-request tests |
| `modules/backend-api/fastapi/app/routers/` | Twitch ingress | No verified end-to-end chat path | EventSub adapter, authentication, deduplication, reconnect | `chat.message` | Real test-channel message → voice |
| `modules/automation-control/stream-autopilot/games/` | `GameAdapter` | Absent | Observe/act/cancel/capability interface | `action_id`, deadline | One real supported-game scenario |
| `apps/stream-extend/` | Autopilot controls | No verified complete host UI | Preview, profile/game selector, health, mute/pause | `Preview host` | Keyboard flow and live preview |

## 7. Contracts and examples

Proposed profile, stored under `configs/`:

```yaml
schema_version: 1
session_id: minecraft-builder
game_id: minecraft
mode: cohost
persona:
  id: nova-builder
  revision: 1
  display_name: Nova
  tone: curious, playful, concise
  voice_id: local-voice-1
  avatar_id: nova-vrm
  catchphrases:
    build_complete: ["Another block toward greatness."]
    player_death: ["That was a structural learning opportunity."]
  catchphrase_cooldown_seconds: 180
  max_reply_characters: 280
gameplay:
  enabled: false
  adapter_id: null
limits:
  chat_queue_capacity: 32
  chat_ttl_seconds: 15
  speech_queue_capacity: 2
```

Cooldowns and repetition suppression are enforced by code, keyed per session/persona/phrase;
prompt wording alone does not enforce them. Profile switches cancel old queued utterances and
increment a session generation counter so late LLM/TTS completions cannot speak in the new voice.

All events carry `schema_version`, `event_id`, `session_id`, `game_id`, `persona_id`,
`profile_revision`, `generation`, `occurred_at`, `expires_at`, `type`, and a typed payload.
Speech additionally carries `utterance_id`; game actions carry `action_id` and deadline.
Deduplication uses the platform's message/event ID and a bounded expiry cache.

Proposed local control responses: `202` for accepted transition with an operation ID, `400` for
invalid config, `401/403` for authentication/ownership failure, `409` for conflicting lifecycle
state or exhausted session budget, `503` for missing dependency. A read-only status endpoint
reports actual state plus capability-specific failures. Retry with an idempotency key; lifecycle
operations with the same key must not create a second session.

Keep legacy single-session event compatibility behind an explicit adapter; never broadcast a
new session-scoped reply onto the global legacy bus. A versioned memory migration must add
scope columns and indexes; do not silently assign old memories to every new session.

## 8. Security, privacy, accessibility, and observability

Chat is content, never an instruction source for machine control. The dialogue model has no
shell or arbitrary input-execution capability. Game actions are typed, allowlisted operations
authorized by the operator's session configuration and checked by the adapter.

Use authenticated backend routes and configured local binds. Keep platform tokens in the
existing secret configuration. Log identifiers, timings, decisions and errors rather than raw
chat, secrets, audio or frames by default. Memory retention is explicit and defaults off for new
autopilot sessions until configured. Visible captions, labeled controls, keyboard mute/pause,
and non-color-only health states are required.

Metrics: event drops by reason, queue age/depth, LLM and TTS duration, playback start latency,
avatar FPS, OBS lag, game action timeout, reconnects, and pause acknowledgements. Avoid viewer IDs
as metric labels. Alerts report failed components; no repeated chat announcements on failures.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| A1 | Flood 1,000 messages/minute for 10 minutes | Bounded memory/queues; TTL expiry; no unbounded speech backlog | Integration | Co-host |
| A2 | Game/profile switches while reply and TTS are in flight | Old generation cannot produce speech or gestures | Offline + live audio | Co-host |
| A3 | Malformed, repeated, oversized and prompt-injection chat | Validated/limited; no machine action | Offline | Co-host |
| A4 | Unplug audio, kill model server, stop avatar renderer | Named degraded state, capture remains stable, recovery works | Fault injection | Co-host |
| A5 | Mute while synthesis hangs and speech is playing | Local playback stops independently of network/model | Live audio | Co-host |
| A6 | Real chat on operator test channel | Correct persona speaks with caption and lip timing | Live | Co-host |
| A7 | Two games, distinct persona/memory/audio | Zero cross-session events or playback in 60 minutes | Live | Multi-session |
| A8 | Game adapter loses connection while holding input | Input released; state reconciled before resume | Adapter + live | Gameplay |
| A9 | Restart/crash during session creation | Idempotent recovery to preview; no duplicate stream or action | Integration | Co-host |
| A10 | GPU saturation and additional session request | Reject new workload or degrade AI; measure OBS lag | Real hardware | Multi-session |
| A11 | Unsupported game or automation capability | Explain unsupported mode; co-host still available | Offline | Gameplay |

Documentation verification on 2026-09-08: `make test` reached 100% and exited 0 (the configured
quiet output did not print a final pass count; skips/expected failure and a Pydantic deprecation
warning were present). Explicit checks confirmed all 7 relative links in this new proposal
resolve and P-056 has exactly one queue row linking here. `git diff --check` exited 0.
The explicit link check is needed because the existing link test scans tracked files only.
First-slice verification is recorded in §10. End-to-end live acceptance is still open: selected
character/voice bindings, a working game adapter, OBS capture, and a declared reference workstation
configuration are not supplied by this implementation.

## 10. Delivery plan

Owner expansion, 2026-09-08: at least one show daily, two flagship shows weekly, later two shows
daily. Add Roblox and Among Us to the original ten-game evaluation. Build one main personality
with game variations, a show catalog/calendar in Automation / Control, and a local Shorts
selection/rendering path in Content Creation for every recorded stream. Interaction-ranked
candidates and exact operator-selected sections both belong in that path. No automatic platform
posting or live broadcast launch is implied by a calendar or generated Short.

| Phase | Deliverable | Dependencies | Acceptance evidence |
|---|---|---|---|
| 0 | Queue, full design, choose first mode and hardware | Owner request | Documentation checks and explicit remaining decisions |
| 1 | Local preview co-host: profiles, chat, voice, original avatar, pause | Configured model/voice/avatar, test channel, OBS | A1–A6 and A9; saved local recording |
| 2 | Full-body expressions/gestures; optional performer tracking and filters | Phase 1 and licensed rig/assets | Pose/expression fixture plus real recording and timing measurements |
| 3 | One autonomous game adapter | Phase 1; supported environment and observed action API | Complete bounded in-game task, A8 and A11; demonstrate manual takeover |
| 4 | Multiple game sessions and stream direction | Phases 1–3 and measured resource budget | A7/A10 on declared hardware; separate captures/audio and session pause |

Owner chooses assets/hardware/game environment; implementation agent owns code, checks and
evidence. Do not call phase 4 complete based on a mocked scheduler or two background processes.
Actual game clients must render/capture: a headless game bot alone produces no stream video.

### First implementation slice — 2026-09-08

Owner explicitly requested starting the build in the follow-up, and asked about League, Dota,
World of Warcraft and paid cloud hosts. Implementation began with the AI Agents-owned worker
because persona/session handling is useful and verifiable independently of the future OBS/game
supervisor. No new top-level module or roadmap-layer split was needed.

- [Conversation worker](../../modules/ai-agents/stream_host/README.md): validated profiles,
  per-session bounded queues and ephemeral history, event expiry/deduplication, enforced phrase
  cooldown/rotation, cancellation/generation checks, Ollama text replies, and explicit scripted
  rehearsal. It can consume the existing authenticated backend WebSocket event envelope and
  publish results through `POST /events`; no direct module imports or new API routes.
- [Local configuration](../../configs/local/stream-autopilot.yaml): four game personas and two
  enabled example sessions. Voice/avatar IDs are unbound logical identifiers. `host_id` is
  metadata, not a remote launcher. No game automation is enabled or implemented.
- [Speech exporter](../../modules/audio-production/tts/README.md): validates a saved session
  reply and renders a real local WAV through macOS speech. No playback, audio-device routing,
  voice cloning or mouth/body synchronization yet.
- Existing legacy agent/Redis/VTS behavior remains separate; the new worker's conversational
  history is ephemeral. **Retention difference from the target design:** using existing backend
  `/events` stores chat and reply payloads in its events table; this is disclosed in the worker
  README. Per-session retention/deletion is still an integration requirement.

Verified: 21 focused behavioral/transport/audio tests pass on Python 3.12; Ruff 0.6.4 (CI pin)
passes `modules/ scripts/`; real CLI validation accepts four personas/two sessions; real CLI
rehearsal yields seven events, three replies, cooldown suppression and pause/resume; macOS speech
export produces a 1.829-second PCM WAV. Full offline suite and documentation verification are
recorded in the queue after completion. No live Ollama binary was found; model protocol and
backend envelope/auth handling are tested with fakes, not claimed as live inference or backend
acceptance. Module status remains scaffolded.

Still required: actual platform chat ingress, comprehensive moderation, playback with an
independent mute, avatar assets/rendering/lip sync/full-body animation, OBS/session supervision,
game adapters, backend reconnect/recovery, persistent scoped memory policy, and real hardware
soak tests. This is a working first slice, not completion of Phase 1 or a fully automated stream.

### Existing stream-module integrations — 2026-09-08

Owner explicitly requested reuse of the DJ Soundbox and other stream-based modules. DJ Soundbox
maps to the existing `soundboard` module. Added the local Automation / Control
[stream director](../../modules/automation-control/stream_director/README.md), configured in
[`configs/local/stream-director.yaml`](../../configs/local/stream-director.yaml):

- Soundboard's existing manifest slots map per game/reaction to exact operator-configured OBS
  hotkey names. Discover registration with OBS v5 `GetHotkeyList`, then invoke
  `TriggerHotkeyByName`. No copied audio assets or plugin-internal imports. Missing bindings
  are explicit; dock installation/loading remains manual. Reserve a global clip cooldown before
  dispatch so uncertain failures cannot immediately replay the sound.
- Broadcast Graphics receives host captions through the existing authenticated
  `PUT /overlays/lowerThird` contract and NodeCG bridge. Captions expire and clear on controls.
- Creator Experience uses configured OBS program scenes for pause/resume. Audio Production's
  selected AI voice OBS input can be muted on pause, and a configured soundboard stop hotkey
  can fire. Resume leaves audio muted until an operator verifies it: playback cancellation
  and safe automatic unmute are not yet implemented.
- Optional n8n controls use `/automation/trigger`, reporting **queued**, not completed. Director
  results use existing backend `/events` under `stream-director`; telemetry delivery errors
  retain stdout results and do not disable subsequent actions.

Only the configured on-air session can affect shared OBS/graphics. Scoped timestamps, event IDs
and generation checks suppress stale, duplicate, off-air or paused-session actions. The model
does not choose raw hotkeys, scenes or workflow names. No stream-start, stream-stop, game input,
cloud provisioning or arbitrary shell tools are exposed. File/live preview is the default;
`--apply` opts into configured effects. Backend authenticated events remain the runtime boundary
between modules; the manifest is a read-only asset/configuration reference, not a Python import.

This covers a director for reactions/controls, not the complete stream lifecycle supervisor.
Limitations: one director owns the global lower-third per OBS/backend instance; process-local
generations require restarting director with host; requests are bounded/serialized, not a hard
real-time emergency stop; no comprehensive playback/ducking/avatar synchronization or automatic
reconnect. Existing metrics can ingest action events, but no Prometheus dashboards are claimed.

### Personality audio policy boundary — P-066

[P-066](PROPOSAL_ASTRA_REACTION_AUDIO.md) scopes the next audio distinction without changing this
proposal's current claims. Gaming profiles may eventually dispatch an accepted Astra-authored
spoken phrase from Soundboard; when that happens, the matching live `stream_speech` reply must be
suppressed to prevent duplicate audio. OpenTech and general AI/technology profiles stay on the
scripted AI-VOICE path and do not use Soundboard. Their possible pause-to-answer flow is a later
safe-boundary script feature, not a gaming reaction or a clip-authoring shortcut.

Verification: 37 director + host + speech tests pass; actual host CLI output consumed by the
director preview yields four actions, one off-air ignore and one unbound sound report. Exact
API/wire contracts use fakes; Ruff 0.6.4 passes repository-wide; full `make test` exits 0.
Live OBS discovery was attempted at `127.0.0.1:4455` and returned
`ConnectionRefusedError`, exit 1. Live plugin audio, OBS scenes/mute, NodeCG and n8n execution are
not verified. No module status promotion.

## 11. Rollout and rollback

Feature disabled by default; preview first. Gameplay disabled independently. Operator must
configure stream destinations and when automatic start is allowed. Rollout starts on a local
recording/test channel. Pin dependency versions and retain prior persona/config revisions.

Rollback: mute and cancel all session work, release game controls, restore the configured OBS
fallback scene, disable the coordinator and keep the original manual stream path. Never stop
unrelated OBS processes or modify scenes not owned by this configuration. New memory data must
be exportable and remain isolated if code rolls back.

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation/decision owner | Due date |
|---|---|---|---|
| Co-host vs gameplay first | Changes first vertical slice | Owner wants manual Xbox play plus autonomous desktop streams; complete one host path, then one permitted gameplay adapter | Before gameplay implementation |
| Real performer vs synthetic host, realistic vs stylized | Different tracking/rendering/assets | Support separate modes; original VRM is proposed baseline | Before avatar integration |
| Workstation OS/GPU/VRAM and intended session count | Determines feasible concurrency and effects | Benchmark target machine; do not infer hardware from historical docs | Before performance acceptance |
| One broadcast switching games vs separate broadcasts | Different OBS, audio and platform layout | Owner targets three independent streams: Xbox/Mac plus two desktops purchased in stages; isolate runtime owners and configure destinations | Before multi-session phase |
| Streaming platform and language | Chat adapter/auth and persona requirements | Twitch ranking and first adapter are current assumptions | Before live chat integration |
| Gameplay permissions and adapter availability | Some popular games prohibit unauthorized automation | Verify publisher/server rules for each environment | Before enabling each adapter |
| New top-level module requested literally | Existing layers already own component responsibilities | Proposed nested coordinator; owner decides if a distinct layer is desired | Before creating a top-level module |

### Additional games and optional cloud execution — 2026-09-08

| Game | Practical automation target | Evidence and limit |
|---|---|---|
| Dota 2 | Scripted bots in supported bot/custom lobby environments | [Valve introduced a bot scripting API and lobby bot selection](https://www.dota2.com/700/other/). Use that route; no claim that this authorizes automated ordinary matchmaking. Current client/script compatibility still needs a live test |
| League of Legends | Co-host while a human plays | [Riot prohibits unauthorized bots/automation](https://www.riotgames.com/en/terms-of-service). No autoplay adapter planned for normal service play |
| World of Warcraft | Co-host while a human plays | [Blizzard prohibits unauthorized automated character control](https://www.blizzard.com/en-gb/legal/2c72a35c-bf1b-4ae6-99ec-80624e1b429c/blizzard-end-user-license-agreement). A second VM does not change that |
| StarCraft II | Research/local bot environments through its ML API | [PySC2](https://github.com/google-deepmind/pysc2) exposes observations/actions and scripted-agent examples; not authorization for ordinary ladder bots |
| Screeps | Autonomous programmable colonies | [The game is explicitly built for JavaScript automation](https://screeps.com/) |
| Minecraft | Bot API in an environment permitting automation | Mineflayer source linked below; no adapter built in this slice |

A paid GPU VM can host an additional rendered game. A basic CPU VPS can run server/bot logic
but is not an equivalent graphical gaming workstation. [AWS G6](https://aws.amazon.com/ec2/instance-types/g6/)
is a candidate because AWS explicitly lists game streaming/graphics workloads; its [gaming driver
documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-gaming-driver.html) covers
supported Windows/Linux configurations. This is a research candidate, not a tested game image or
recommendation to purchase before validating the exact game/OS/driver/encoder combination.

Proposed experiment: one GPU VM for one additional supported game, an independent game client,
capture and audio path, authenticated tailnet control, and a fixed runtime budget. Human camera
effects and the primary OBS path remain on the creator's workstation. Whole cloud-hosted game
broadcast sessions extend the roadmap's current local-only realtime rule: record an explicit
roadmap/deviation decision before implementing that deployment. No VM, account, subscription,
cloud spending or distributed worker system was created by this change.

Budget includes compute, OS/image costs where applicable, persistent disks and outgoing video
traffic ([AWS pricing dimensions](https://aws.amazon.com/ec2/pricing/on-demand/)). Illustrative
arithmetic only, **not a provider quote**: at $1/hour, 8 hours/day for 30 days is $240 compute,
and continuous 30-day operation is $720. A 6 Mbps video stream is about 2.7 GB/hour before
overhead, making outbound traffic material. Obtain region/OS-specific quotes and a stopping
policy before provisioning. Do not promise multiple game sessions per GPU without measurement.

### Game viewership evidence

The owner confirmed an Xbox Series S, no capture card and an initial hardware budget under $1,000.
All ten games below now have a [platform, GPU, cloud and capture evaluation](STREAM_AUTOPILOT_GAME_EVALUATION.md).
It records the inspected M1 Pro/16 GB workstation and the owner's staged plan: one inexpensive
desktop first, a second funded when realized revenue supports it, and optional on-demand GPU
capacity later. Target: two automated desktop game streams plus one manually played Xbox stream,
each with AI production. All game and concurrent-broadcast benchmarks remain pending.
Current WoW Midnight's published M2 minimum supersedes the older M1 advice given
in conversation. Evaluation entries do not enable additional runtime personas or autoplay.

Twitch only, all languages, trailing 30-day watch hours, retrieved 2026-09-08. The opened
[TwitchMetrics ranking](https://www.twitchmetrics.net/games/viewership) said updated September 8
at 12:18. Excludes Just Chatting, IRL and event categories. These figures are a snapshot, not a
cross-platform ranking or forecast of a new channel's audience.

| Game rank | Game/category label | Viewer hours |
|---|---|---:|
| 1 | League of Legends | 67,853,169 |
| 2 | Dota 2 | 65,266,159 |
| 3 | Counter-Strike | 60,378,106 |
| 4 | Grand Theft Auto V | 47,016,266 |
| 5 | VALORANT | 44,274,084 |
| 6 | Escape from Tarkov | 38,613,439 |
| 7 | Minecraft | 36,616,044 |
| 8 | World of Warcraft | 31,311,584 |
| 9 | Fortnite | 26,968,038 |
| 10 | Overwatch | 21,992,747 |

Technical source checks on 2026-09-08:

- [Twitch chat documentation](https://dev.twitch.tv/docs/chat/) informs the authenticated
  chat adapter design; connecting chat does not automatically implement moderation or voice.
- [three-vrm](https://github.com/pixiv/three-vrm) provides a Three.js VRM runtime. It is a
  candidate renderer, not evidence of an integrated host in this repository.
- [Mineflayer](https://github.com/PrismarineJS/mineflayer) provides a Minecraft bot API. This
  makes Minecraft a proposed first autonomy target in an operator-controlled environment that
  permits it; it does not guarantee general game competence or provide OBS game capture.
- [Riot terms](https://www.riotgames.com/en/terms-of-service) prohibit unauthorized bots and
  automation. League/VALORANT viewership is not evidence they are suitable autoplay targets.

## 13. Documentation updates

The first slice updates its worker/audio READMEs, owning module setup entries, configuration,
environment example, audit/acceptance evidence and module item matrix as well as this proposal.
Subsequent runtime implementation must update
the affected module READMEs and setup guides, `docs/agent/MODULE-ITEM-MATRIX.md`, the verification
matrix, acceptance checklist, API documentation, configuration/environment examples and
`docs/AUDIT.md` with measured results. Add an explicit coordinator README for local usage and
cloud differences. Compose changes require both local and DigitalOcean validation and smoke
tests. Module-wide status stays unchanged until the entire module has its required evidence.

If a new top-level module is chosen, update the roadmap, deviations, AGENTS/CLAUDE tables,
module index, both module matrices, and its manual/automated setup documents together.

### Daily programming, Shorts and interchangeable gameplay — 2026-09-08

Owner clarified: there must be no hardware references in show identities. A human or eligible
agent can play the same show, and operator takeover/return should preserve the running broadcast
and host. These are gameplay ownership transitions, separate from host conversation pause.

Built within existing roadmap layers:

- AI Agents: one Nova personality inherited by twelve game variations, fixed name/voice/avatar,
  core and per-game catchphrases. Legacy complete persona configs remain accepted.
- Automation / Control: 29 show concepts, two weekly flagships, daily planning with a stable
  optional second slot. [Show bible](STREAM_AUTOPILOT_SHOW_BIBLE.md) and
  [planner](../../modules/automation-control/show_planner/README.md) describe editable assumptions.
- Automation / Control: input ownership contract with epoch invalidation, release acknowledgement,
  fresh-state acknowledgement before agent return, timeout handling and stale-response rejection.
  No concrete game/device adapter, authenticated operator UI or live game inputs are included yet.
- Content Creation: game-agnostic recording/job contracts, ranked interaction windows, exact
  manual selections, local video review/export and real FFmpeg vertical MP4 production. Every
  calendar episode requests Shorts, but delivery of finished recordings/chat events is not wired.

Verification matrix rows: Python in a module and P-056 calendar / Shorts / input handoff.
`make test` reached 100%, exit 0 (`/tmp/hcp-show-shorts-test.log`; quiet configuration omits a final
pass count, with existing skips/expected failure and Pydantic deprecation warning). Combined
focused pytest run: **60 passed in 1.69 seconds** on Python 3.12. Ruff 0.6.4 passes `modules/
scripts/` and the new/updated focused tests. Main host CLI validates twelve variations/two
sessions; actual planner CLI exports 28 and 56 episodes, both covering all twelve games.

Real `stream_shorts produce` on a synthetic 90-second color-pattern/audio recording selected
one manual clip (3–10s) and two interaction clips (27–37s, 67–77s), then rendered three 720×1280
MP4s with measured durations 7/10/10 seconds and a complete manifest. Output frame visually
inspected: full source frame retained inside vertical padding. This proves media processing,
not suitability of the layout for a particular game's HUD or editorial quality.

Browser review verified recording load, manual 40–48s selection, deselection of the opening,
and export. The downloaded JSON was read and validated: exactly the two interaction clips plus
the manual selection. The reviewed plan was then rendered through the real CLI into three
MP4s (10/10/8 seconds), complete manifest. Browser download-event wait timed out, but the actual
file existed in Downloads and its contents were verified independently; no export failure remains.
Artifacts are ignored under `output/stream-autopilot/show-demo/`; recordings are synthetic and
were not committed or published. No cloud compute was used.

Still required for a real daily autonomous show: accounts and game environment, permitted game
adapter with actual input release and handoff controls, live chat/recording completion ingress,
durable episode/job recovery, model/voice/avatar bindings and local OBS/Soundbox/audio acceptance.
Existing director bindings remain the reuse path for DJ Soundbox and other stream modules.
Module statuses and Phase 1 remain unchanged; this is not a claim of unattended live readiness.

### Game-specific energy revision — 2026-09-08

Owner requested IShowSpeed as a performance reference, selectively by game. The twelve existing
persona systems now describe original high-expression, balanced or measured delivery, with short
payoffs, occasional audience participation and quieter intervals. Eight victory/defeat phrases
changed for Fortnite, Roblox, GTA V and Among Us. Core Nova identity, voice/avatar IDs, sessions,
reply limits and catchphrase cooldown are unchanged. See the
[show bible](STREAM_AUTOPILOT_SHOW_BIBLE.md#game-specific-performance-direction) for the full
mapping, examples, reference and evaluation criteria. No automatic audio gain, voice prosody,
pose or show-phase detector was added; audience fit remains an untested programming hypothesis.

Configuration/entrypoint verification: host CLI validation accepts twelve modes/two sessions;
24 focused host/planner tests pass in 0.66 seconds. Real CLI baseline rehearsal still emits seven
events/three replies, including cooldown and pause drops. An additional actual CLI replay of
persona changes and supplied game events emits 24 configured victory/defeat replies across all
twelve games, with fixed Nova identity. Compared parsed config against the pre-edit snapshot:
all non-persona fields, game IDs and persona keys are unchanged. No live model, expressive speech,
avatar or audience-retention test was run. Offline suite result is recorded in the queue row.

### Creator teaching and continuing work shows — 2026-09-08

Owner requested item/experience development as shows, with separate instruction and ongoing
work toward eligible product revenue. Added six show options (Roblox, Fortnite and GTA V/FiveM
pairs), shared project briefs, format/project fields in actual calendar exports and three active
idea-stage production briefs. GTA VI has a deferred research brief with reserved format names;
validation prevents scheduling deferred projects. Current catalog: 35 shows, twelve games.
The [show bible](STREAM_AUTOPILOT_SHOW_BIBLE.md#creator-shows-teach-it-then-keep-building-it)
records official creator-tool/monetization sources, platform limits and production-log proposals.

Project continuity is operator-maintained configuration; editor resume, file saving, live host
context injection and commercial publishing remain unimplemented. Tutorial/workshop delivery is
calmer when supplied to the existing persona prompt. This does not change Nova's identity or
human/agent takeover requirements. The Mac is eligible for a basic OBS test, not a completed
unattended AI broadcast. Roblox Studio is the first proposed Mac creator pilot.

Verification matrix row: Python in a module. Focused planner/host tests: 31 passed in 0.82s.
Tests cover paired-project continuity, metadata export, deferred/unknown/wrong-game/duplicate
project rejection and legacy catalog compatibility. Host CLI validates twelve personas/two
sessions. Full offline suite and real calendar entrypoint results are recorded in the queue.
No editor, game, marketplace account or recording was launched by this extension.


## Windows test readiness — 2026-09-08

Owner requested bringing the repository up to date for a Windows-device test. Added
`scripts/setup/stream_autopilot.py install|doctor|smoke`, a shared pinned dependency file,
Windows native speech export using System.Speech, and packaged IANA timezone data. The runner
uses argument lists, platform-specific virtualenv paths and UTF-8 subprocess output, and
records failing stages without replacing earlier results. It requires no Bash, Docker or GPU.
The new Windows/macOS CI workflow exercises native voices and actual FFmpeg output when run.

[Windows/Mac instructions](../../modules/ai-agents/stream_host/WINDOWS_TEST.md) cover setup,
report collection and a subsequent manual OBS recording. A source-only transfer kit is at
`output/stream-autopilot/windows-test-kit.zip`; it includes the current local module changes,
not credentials, a prebuilt environment or the entire platform.

Verification: installer completed using Python 3.12.13 on macOS arm64. Doctor passed with
`PYTHONTZPATH` empty, exercising packaged timezone data. All 72 focused host/speech/director/
planner/handoff/Shorts/setup tests passed in 1.94 seconds. The real smoke run at
`output/stream-autopilot/portable test café/report.json` passed all ten stages, including native
speech, 28 calendar entries, the review page and three 720×1280 MP4s. This checks spaces and
Unicode in output paths. `make test` reached 100% and exited 0
(`/tmp/hcp-windows-full-test.log`); Ruff 0.6.4 and `git diff --check` passed.

The Windows GitHub runner later passed the bootstrap plan, dependency/doctor path, System.Speech
export and real synthetic Shorts render in PR #41. This is native CI evidence, not acceptance on
the owner's Windows hardware. Real OBS/Soundbox, models, games, live chat and a Windows desktop
UI/hardware run remain separate work. P-056 stays In progress and no module status is promoted.

## Lifecycle supervisor and desktop rehearsal — 2026-09-08

Owner asked to continue Automated Streaming after remote control and Windows/capture readiness.
The next missing dependency was the lifecycle owner described in §6. Added the Automation /
Control [`stream_autopilot`](../../modules/automation-control/stream_autopilot/README.md)
coordinator with a versioned local policy at
[`configs/local/stream-supervisor.yaml`](../../configs/local/stream-supervisor.yaml).

The supervisor now owns `stopped → preflight → preview → running`, plus pause, resume, degraded
and emergency-stop handling. Required capability checks fail closed. Broadcast start needs both a
successful preview and `broadcast_start_authorized: true`; the committed sessions keep it false.
Autonomous mode is invalid without an explicitly enabled gameplay adapter. The configured
running-session budget is one until hardware measurement supports more.

Lifecycle operations use bounded persisted idempotency keys. A restarted coordinator never
assumes old workers, audio, inputs or OBS state are healthy: an active saved state recovers to
preview when its earlier preflight was ready, records the prior state and requires another
operator action. Pause and emergency stop time-bound the driver's acknowledgement and report a
degraded state instead of claiming stopped when input/audio release is uncertain.

Stream Extend now has an **Automated streaming** view. Its fixed native command bridge unpacks
only the bundled supervisor sources/policy, uses the Automation / Control module environment and
accepts only a configured session ID. The first UI action is deliberately a no-effects lifecycle
rehearsal; it does not accept a command/path, start a broadcast, contact a model or drive a game.

Verified in this slice: eight focused lifecycle tests; actual policy-validation and rehearsal
entry points; Stream Extend's seven Rust unit tests plus eight real OBS contract tests; Svelte
check/build with zero diagnostics; debug `.app` and DMG. On the MacBook display the bundled app
loaded the Dota co-host policy as live-start locked/gameplay disabled and completed
`preflight → preview → pause → preview → stop`, ending stopped and reporting no broadcast start.
The full offline suite reached 100% and exited 0. The expanded real Mac smoke report at
`output/stream-autopilot/lifecycle-integration-20260908202516/report.json` passed all eleven
stages, including the supervisor rehearsal, native speech and three rendered vertical clips.

This completes the deterministic lifecycle foundation, not its production driver. Live component
preflight, process ownership, local mute/playback, avatar/voice timing, OBS/Soundbox application,
platform chat, recording completion, a permitted game adapter and live restart acceptance remain
open. Phase 1 and module statuses do not advance.

## Advanced Shorts editing — 2026-09-08

Owner chose the first recommended editing increment. The existing Content Creation pipeline now
accepts optional validated edit data for brand colors/text, timestamped captions, event-linked
punch-ins with bounded zoom/focus values and audio loudness normalization. These fields remain in
the review/export plan, and each output manifest records the number of cues applied. Advanced
rendering is opt-in, so legacy version 1 jobs retain their plain layout and audio behavior. Text
reaches FFmpeg through temporary local UTF-8 files rather than filter-expression interpolation.

The portable demo now exercises three captions, two punch-ins and normalized audio across its
three selected clips. The MacBook smoke run at
`output/stream-autopilot/advanced-edit-optin-20260908/report.json` passed all eleven stages. A separate
real 8-second H.264/AAC render applied branding, one caption, one punch-in and normalization;
metadata verified 720×1280 and 8.0 seconds, and the rendered frame was visually inspected. A
silent-source render also completed with optional audio mapping. Twenty-one focused Shorts/setup
tests pass, `make test` reaches 100% with exit 0, Ruff 0.6.4 passes the required modules/scripts
scope plus changed tests, and `git diff --check` passes.

This slice consumes supplied edit cues. Speech transcription, semantic highlight scoring,
subject tracking, logo/font/music asset contracts, real-stream phone review, upload and publishing
remain open. No GPU or cloud service is required, and no module status is promoted.

## Continuous speech, avatar timing, Twitch ingress and production supervision — 2026-09-09

The Audio Production `stream_speech` worker now turns current on-air replies into continuous native
speech with a bounded queue, voice allowlist, TTL/deduplication and generation-safe cancellation.
It emits playback start/finish/cancel events and deletes temporary WAVs by default. The Character /
Avatar `stream_avatar` worker consumes those events to drive bound VTube Studio Talk/Idle hotkeys
from actual playback timing instead of a text-length estimate.

The production lifecycle driver composes the existing host, director, speech and optional avatar
and Twitch workers through fixed commands. Preview owns their process groups. Pause kills speech
first, then all viewer-facing workers, before a best-effort backend notice; resume starts a clean
worker set. Broadcast start is guarded by both supervisor authorization and a separate runtime
flag, and stop sends `StopStream` only if this driver started it. The committed runtime disables
applied OBS effects, avatar, Twitch and broadcast control until the operator accepts each binding.

Backend API now includes an optional Twitch EventSub WebSocket ingress worker. It requests the
`channel.chat.message` subscription, follows Twitch's reconnect URL, bounds messages, preserves
source timestamps/IDs and forwards text as a typed host `chat` event. Twitch documents that this
subscription requires a user access token with `user:read:chat`, sends notifications at least once,
and does not replay messages after an unexpected disconnect; downstream message-ID deduplication
and TTL handling cover those transport properties. See [subscription types](https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/)
and [WebSocket handling](https://dev.twitch.tv/docs/eventsub/handling-websocket-events/).

Focused tests cover speech cancellation, generation changes, actual-timing avatar events, repeated
controls, fixed production composition and Twitch envelope/subscription contracts. On the MacBook,
native `say`/`afplay` validation passed, an audible long utterance was canceled during playback in
0.0029 seconds, no false `finished` event was emitted and no WAV remained. All component configs
and CLIs validate. No backend containers, OBS, VTube Studio or Ollama processes were running, and
Twitch credentials are absent, so the live test-channel → voice/avatar/OBS recording remains gated.
Native Windows System.Speech playback and process-tree cancellation also remain gated. The full
offline suite, Python lint, diff checks and Stream Extend Rust bundle contract pass. Module statuses
stay scaffolded.

## Simulator and non-game stream profiles — 2026-09-10

The operator-owned program now distinguishes five explicit profile policies. Microsoft Flight
Simulator 2024, BeamNG.drive and Roblox private-experience labs are marked experimental for future
bounded controller adapters; scheduling them does not grant game input. The catalog adds two shows
for each lab and retains immediate human/agent handoff as an acceptance requirement.

Two top-level non-game profiles are also active in the draft catalog. `OpenTechMarketing` uses the
existing Nova identity with a product-educator variation and can accept only approved
`opentechblog` or `opentechapp` Marketing Crosswalk references. `VideoReview` uses a fair media
review variation for try-not-to-laugh and general edit reviews, accepts only operator-selected
local media and requires confirmation that the media may be used.

Both profiles bind to distinct YouTube channel environment-variable names and allow only private
or unlisted visibility. A local compiler validates the profile, source reference, existing media
file and rights confirmation, then emits an approval-state draft with upload disabled. There is no
URL downloader, OAuth client, YouTube API call or publisher. The expanded 45-show calendar reaches
fourteen games and both non-game subjects in the first 28 days. Live controller adapters, account
connection, upload implementation and platform acceptance remain open.

Verification for this slice: 37 focused host/planner tests pass. The real planner CLI exports 28
episodes covering sixteen distinct subjects and all five new profiles; a real OpenTechMarketing
plan resolves an existing local media file, remains `awaiting-approval`, uses private visibility
and reports `upload_enabled: false`. The full offline suite reaches 100% with exit 0; Ruff and
`git diff --check` pass.

## Production readiness inspection — 2026-10-12

Owner requested finishing the active build work. Explicit child assignment:
`gpt-6.1-sol` / `high` — bounded read-only production preflight and CLI safety checks using
existing worker contracts. Parent P-056 remains Astra/xhigh; the task has no independent
execution-model switch. The inspection may validate configs/dependencies and GET backend
readiness, but must never launch effect workers, trigger clip hotkeys, save a live state or
start a broadcast. Game adapter implementation/enablement still needs its permitted environment,
phase dependencies and reference workstation; these missing inputs were requested from the owner.

Actual `PYTHONPATH=modules/automation-control .venv-stream-autopilot/bin/python3 -m
stream_autopilot preflight` completed with session minecraft-main: host/director/speech
validators ready, backend-auth missing, overall ready false, no workers or broadcast started.
The three inspection tests prove missing checks remain false, failures still close the HTTP
client, unknown sessions never construct a driver, and effect shutdown is never called.
The existing shutdown can trigger OBS Stop All, so read-only inspection releases only HTTP.
Focused Automation / Control tests and Ruff passed. Game/environment and hardware inputs
remain pending; the gameplay adapter, native production controls, full-body/gesture scope and
real multi-session/performance acceptance are not completed by this inspection.

Final verification for this inspection: the required full offline suite reached 100%, exit 0;
35 focused final metadata/runner/inspection checks passed; the broader Automation / Control
suite and module/script Ruff passed. Stream Svelte check returned zero errors/warnings and
its debug `.app` bundle built. An initial parallel Rust/bundle run passed 15 unit and 13 OBS
contracts but its doctest failed to resolve tauri (E0463); rerunning `cargo test --locked
--manifest-path apps/stream-extend/src-tauri/Cargo.toml` sequentially passed the entire suite
including doctests (`/tmp/hcp-active-stream-rust-sequential.log`). No new native production
control UI or live effect acceptance is claimed by this CLI inspection. Remaining phase
dependencies above remain open; P-056 is not Done.

## Desktop production owner and remaining adapter build — 2026-10-12

Owner requested continuing P-056 until only real acceptance remains. The next build slice
adds persistent native production ownership and controls, followed by the bounded game/asset
integration code where its existing admission conditions permit it. Explicit child assignment:
`gpt-6.1-sol` / `xhigh` — local native ownership, cancellation and bundled worker contracts;
parent remains Astra/xhigh, and execution controls cannot independently switch this task's model.
No broadcast, account sign-in, gameplay permission or phase-order exception is inferred.
Rehearsal and production state must be separate. Defaults remain broadcast/gameplay disabled.
Move to Testing only after remaining implementation is actually built, retaining all real gates.

### Production build result and real-testing handoff

The bounded single-workstation production build is now in the queue's **Testing with remaining
features or delivery** section. Canonical state remains In progress. The persistent native
owner bundles fixed workers and required manifests, owns one output pipeline under OS/state
locks, keeps private operator copies, correlates requests and reserves stop capacity. Closing
or exiting cancels workers and reconciles only its owned OBS session. Native Run records before
streaming, fences delayed starts against stop, rejects profile conflicts and registers the
finalized recording in the shared Creator inbox. Unknown OBS ownership requires inactive
reconciliation; it never guesses that another output is safe to stop. Renderer input cannot
choose executable paths or arbitrary subprocess commands.

The first game adapter uses a pinned Mineflayer SDK on Node 22+, a dedicated bot identity and
a named permitted private/loopback test world. Its fixed forward/back/jump task lasts at most
one second and requires observed displacement. Pause, emergency stop, disconnect and EOF release
controls. Dependency preparation starts no client. No real world was connected, no game
permission was inferred and public/account/OS input remains unsupported. This is an action API
for an observed bot; local game rendering/capture and manual takeover need real acceptance.

Eight avatar cues are wired through authenticated backend events to exact operator-owned
VTube animation/expression IDs, with model, pause, stale/off-air and duplicate guards. They do
not replace speech generation/utterance guards. Stop uses existing authorization to restore
idle. A cue acknowledgement means queued, never visible movement. A compatible licensed rig
must supply the actual animations; `nova-vrm` is a logical identifier, not a VRM renderer.
Optional performer tracking/filters, other renderers/games and expanded multi-host sessions
remain dependent extensions after phase acceptance and measured budget; none is claimed built.

Real-model preflight now requires the configured model in Ollama's installed-model inventory.
Private `stream-runtime.yaml` can set `ollama_host`/`ollama_model`; existing shell settings are
fallbacks. Default host rehearsal, live/game locks and disabled body/avatar controls remain.

**Recorded checks:** full offline `make test` reached 100%, exit 0 before this documentation
handoff; Automation Control/Character Avatar focused suites pass; Ruff passes modules/scripts.
Stream Rust has 17 passing units (one opt-in packaged check separately run and passing),
13 OBS contracts and passing doctests. The native fake-OBS test covers recording-first,
idempotent replay, profile conflict, finalized inbox handoff and emergency stop superseding a
delayed start. The actual packaged Python owner test verifies host/director/speech validators,
correlation, default locked Run, emergency stop and shutdown without effects. Four Node game
contract cases pass; pinned SDK dependency import connected no client and npm audit reports
zero vulnerabilities. Svelte reports zero errors/warnings and the fresh debug Mac app bundles.
Empty preflight, stale restart readiness and missing installed-model regression cases failed
before the fixes and pass after; logs are under `/tmp/hcp-p056-*.log` in this workstation session.

**Native Mac evidence:** fresh bundle opened on the built-in display; production preflight
reports host/director/speech ready and backend-auth missing, Run stays disabled, emergency
stop returns `minecraft-main` to stopped and closing/reopening the owner preserves safe state.
This UI check caught the initially missing Soundboard manifest; the fixed bundle and packaged
validator test pass. No OBS stream, game input, VTube grant or external account action occurred.

**Next real testing:** provide ST-D06's named game permission/world, ST-D11's reference hardware
and the licensed compatible rig; bind backend/OBS/test-channel credentials manually. Run the
Phase 1 integrated recording and A1–A6/A9 recovery drills, Phase 2 visible gesture/timing check,
and Phase 3 bounded game task with release/disconnect/manual takeover (A8/A11). Record timestamps
for chat-to-first-audio, captions/mouth and mute/pause plus OBS rendering/encoding lag through
60 minutes. These are targets, not measured claims; a saved control acknowledgement cannot
prove audible silence or motion. A7/A10 multi-session expansion follows those results and
measured resources. Physical Windows acceptance, accounts/publishing and optional cloud remain
NOT RUN. No phase or module status is promoted by this Testing placement.

Final safety regression proof reverts only the empty-readiness/restart fixes in memory: both
new tests fail, while source files remain unchanged (`/tmp/hcp-p056-revert-proof.log`). The
normal focused suite then passes with the fixes. The final full offline rerun and generated
registry/queue/diff checks pass; Testing placement remains a work focus, not completion.
