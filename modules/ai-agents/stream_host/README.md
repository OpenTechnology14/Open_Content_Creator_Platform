# Stream Autopilot conversational host

**P-056: first working slice; not a complete autonomous streamer.** This native Python worker
runs isolated co-host conversations for configured game sessions. It implements persona loading,
short ephemeral conversation history, bounded queues, event expiry/deduplication, catchphrase
rotation/cooldowns, basic text filtering, and cancellation on pause or persona changes. Real
chat replies use the configured Ollama instance. Scripted rehearsal needs no model or services.

The AI Agents layer owns this conversation logic. The eventual stream supervisor belongs in
Automation / Control; it will own OBS/game lifecycle, not model prompts. This worker has no game
input, OBS, filesystem tool, or shell-execution capability. Other modules receive its versioned
events through the existing authenticated backend, not direct imports of its internals.

## Run locally

From the repository root, use Python 3.11+ in a virtual environment:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r modules/ai-agents/stream_host/requirements.txt
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host --help
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host --validate
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host \
  --rehearsal --input configs/local/stream-autopilot-demo.jsonl
```

Use an existing suitable virtual environment instead of recreating it if one is already in use.
The demo produces three replies, one cooldown drop, one paused-message drop, and two control
events. Rehearsal replies identify themselves as scripted; game reactions are configured phrases.
The file reader drains after each record so demonstrations are deterministic. Concurrent queue
behavior is exercised by backend mode and tests.

Edit [the workstation configuration](../../../configs/local/stream-autopilot.yaml) to select
personas and sessions. One main personality, Nova, supplies a fixed name, voice/avatar binding
and core catchphrases to fourteen game variations, six Marketing Crosswalk module modes and
VideoReview. The module modes are `task-management` (OpenTechApp), `stream-extend`,
`content-extend`, `ai-learning`, `ai-control-layer` and `chatbot-routing`; the last three are
OpenTechnologyBlog modules. Two sessions are enabled in the example. Per-profile systems and
phrases extend the core personality; switching input ownership must not switch the host identity.
These are co-host profiles, **not game adapters**. Voice/avatar IDs are logical bindings; no avatar
or downloaded voice is included.
`host_id` is inventory metadata only; changing it does not contact or provision a VM.

The personality-to-audio distinction is summarized in
[streaming personality audio routing](../../../docs/architecture/stream-personality-audio-routing.md):
gaming profiles may use reviewed, pre-created reaction clips through Soundboard, while OpenTech
and general AI/technology profiles stay on scripted AI-VOICE delivery. The current host emits
replies; it does not author, save, or select raw Soundboard assets. Each persona declares
`audio_policy` (`gaming-reactive` by default; `opentech-scripted`, `technical-scripted` or
`review-scripted` for the non-game modes) and every reply carries it so the director can refuse
Soundboard dispatch for scripted personalities. [P-066](../../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md)
scopes Astra as the first off-air phrase creator.

For real model replies, set `OLLAMA_HOST` and `OLLAMA_MODEL` to your installed local runtime,
then omit `--rehearsal`. The worker reads exported environment variables, not `.env` automatically:

```bash
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host \
  --input configs/local/stream-autopilot-demo.jsonl
```

Missing configuration fails with exit 1; a failed reply emits an error event and file replay also
exits 1. Model/dependency failures do not kill other active sessions in backend mode. No automatic
model downloads or cloud inference fallback occur. Keep the model on the creator workstation.

## Backend mode and event contract

Start the existing local backend stack separately. Export `AUTOPILOT_BACKEND_URL` and the matching
`HCP_API_KEY` (Compose maps this to the backend's internal `API_KEY`), plus Ollama configuration,
then run:

```bash
PYTHONPATH=modules/ai-agents .venv/bin/python -m stream_host --backend
```

The worker connects to `/ws?topics=events.stream-autopilot.input` with `X-API-Key` and sends
replies/control/drop/error events through `POST /events` with the same header. No new routes,
public service, Compose container, or database migration are added. Disconnects stop the worker
and discard pending work; reconnect/recovery automation is not implemented yet.

Publish input to the existing authenticated `POST /events` with this body (replace `occurred_at`
with the current timezone-aware timestamp):

```json
{
  "source": "stream-autopilot",
  "kind": "input",
  "data": {
    "schema_version": 1,
    "event_id": "unique-message-id",
    "session_id": "minecraft-main",
    "kind": "chat",
    "occurred_at": "2026-09-08T13:00:00Z",
    "user": "viewer-name",
    "text": "What should we build next?"
  }
}
```

Supported input kinds: `chat` with text; `game` with a configured `reaction`; `pause`; `resume`;
`persona` with a known `persona_id`. A trusted platform adapter must always wrap viewer messages
as `chat`. Viewers must never receive the API key or construct operator control events. The
current input producers are a local fixture or an authenticated operator/backend client; a
Twitch/YouTube chat adapter is not implemented in this slice.

Network events require `occurred_at`. Local rehearsal files may omit it and get the current
time. Content expires before inference and again before output. Input length is capped at 500
characters. One active model request plus a bounded queue exists per session; no global
cross-session history. Deduplication retains up to 1,024 IDs per session within the TTL window;
under a larger flood the oldest IDs can be evicted. Persistent memory is not enabled.

Output uses backend source `stream-host` and kinds `reply`, `control`, `dropped`, or `error`.
Reply data includes `session_id`, `generation`, `utterance_id`, `persona_id`, `game_id`, logical
`voice_id`/`avatar_id`, and `text`. Pause/resume/persona controls increment generation and clear
queued content. Consumers must reject replies from older generations. A control acknowledges
the conversation worker only; it does **not** prove a downstream speaker or avatar is muted.

Backend events are persisted by the existing `/events` route. Thus backend mode stores supplied
chat/reply content in the events table; configure platform retention before a public deployment.
Application logs contain session/error identifiers rather than message text. Basic literal-term
and link/spam filtering is not comprehensive moderation; live broadcast approval/moderation is
still an integration requirement.

## Speech export and limitations

[The stream director](../../automation-control/stream_director/README.md) consumes this worker's
backend replies/controls and coordinates existing soundboard, graphics, OBS/audio and n8n
interfaces. It only acts for the configured on-air session. Control outputs now include
`created_at`; restart the director when restarting this host because generations are process-local.

The [local speech exporter](../../audio-production/tts/README.md) turns one saved reply into a
WAV using an installed macOS or Windows voice. This proves local speech synthesis only. Continuous playback,
voice assignment, timed visemes, full-body animation, camera face/body effects, full OBS lifecycle,
autonomous gameplay, remote VM management, and unattended broadcasting remain unimplemented.

The [P-066 voice studio](../../automation-control/voice_studio/README.md) is separate from this live
reply path. `stream_host.author` exposes resolved persona prompts and bounded Ollama phrase/answer
generation over JSON stdin. Reviewed gaming WAVs route through the director's exclusive clip-or-
speech path. OpenTech/technical scripts instead use the studio's operator-controlled native speech
player with boundary pause, source-reviewed Q&A and manual resume; no Soundboard clip is created.

## Verification

```bash
make test
python3 -m ruff check modules/ scripts/
python3 -m pytest tests/ai_agents/test_stream_host.py tests/audio_production/test_host_speech.py
```

Initial slice verified on 2026-09-08 using a separate Python 3.12 environment: 21 focused tests passed, configuration
validation accepted the original four personas/two sessions, the real CLI rehearsal produces seven events
including three replies, and macOS speech export creates a 1.829-second PCM WAV. Ruff 0.6.4 (the
CI pin) passes repository-wide. Full offline suite results are recorded in P-056.

Not live-verified: Ollama generation (no Ollama executable found here), backend/Redis/Postgres
round-trip, actual Twitch chat, OBS capture, avatar rendering, audio routing/playback, any game
client, or any cloud VM. HTTP/WebSocket contracts use fakes in the focused suite. Module status
remains scaffolded until live acceptance is complete.

## DigitalOcean and other cloud hosts

No remote provisioner or cloud execution adapter is shipped. The local co-host path does not
depend on the cloud. A GPU VM for an additional game is an optional future deployment with
separate session/OS/audio/capture isolation; a CPU-only VPS can host a game server or bot logic
without necessarily being able to render a broadcast. A Linux/Windows VM also needs a different
speech adapter from the initial macOS exporter. See P-056 for research and unresolved deployment
decisions, including the roadmap's current local-only realtime rule.

Programming extension: CLI validation now accepts twelve game variations under Nova and two
configured sessions. All 60 combined P-056 focused tests pass, including main-personality
inheritance, daily planning, gameplay handoff and Shorts selection. No live acceptance promotion.

Game delivery is configured in each persona's `system`: four expressive, four balanced and four
measured variants. The main Nova identity stays fixed. See the [show bible's performance
direction](../../../docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md#game-specific-performance-direction)
for intended rhythms and examples. Prompt instructions do not change TTS loudness, avatar
animation or OBS mixing; live expressive delivery remains unverified.

Profile expansion, 2026-09-10: configuration validation now accepts sixteen variations under
Nova. Microsoft Flight Simulator 2024 and BeamNG.drive add simulator-lab delivery;
OpenTechMarketing uses approved product sources and VideoReview uses operator-selected local
media. These prompts do not grant gameplay control, access marketing files or load videos by
themselves. The show planner owns the source and destination policy checks.

For native Windows setup and the shared Mac rehearsal, use [Windows/Mac test instructions](WINDOWS_TEST.md). The test runner does not require Bash or Docker.
