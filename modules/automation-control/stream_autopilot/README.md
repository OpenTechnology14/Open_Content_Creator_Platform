# Stream Autopilot supervisor

This Automation / Control component owns the durable lifecycle around the Stream Autopilot host,
director, speech, avatar, Twitch ingress and future game adapters. Each implementation remains in
its roadmap module and communicates through the authenticated backend event boundary.

The state machine is `stopped → preflight → preview → running`, with `paused` and `degraded`
states. A session can enter `running` only after a successful preflight and preview, with
`broadcast_start_authorized: true` in operator-owned configuration. The committed configuration
keeps that setting false.

Pause and emergency stop require the injected driver to silence AI output and release game input
before acknowledging. Restart recovery never resumes an old live state: it restores a ready
session to preview, records the prior state, and requires another deliberate operator action.
Operation IDs make retried lifecycle requests idempotent and cannot be reused for a different
action.

Validate the policy or run the no-effects lifecycle rehearsal:

```bash
PYTHONPATH=modules/automation-control python3 -m stream_autopilot status
PYTHONPATH=modules/automation-control python3 -m stream_autopilot rehearse
```

`rehearse` does not contact OBS, a model, audio, an avatar, chat, or a game and never starts a
broadcast.

The production driver uses the fixed component list in `production.py`; configuration cannot add
shell commands. It starts workers in preview, kills local speech first and then all viewer-facing
workers on pause, restarts them for resume, and stops OBS only when it started that broadcast.
`configs/local/stream-runtime.yaml` keeps Twitch, avatar effects, applied OBS actions and broadcast
control disabled until their manual bindings are accepted. Start its bounded local JSONL control
service with:

```bash
PYTHONPATH=modules/automation-control python3 -m stream_autopilot serve
```

Each input line must contain exactly `session_id`, `action`, and `operation_id`. Stream Extend still
exposes the safe rehearsal while secure backend/account settings and the production-service UI are
open integration work.

The local policy is [`configs/local/stream-supervisor.yaml`](../../../configs/local/stream-supervisor.yaml).
Cloud execution is not implemented; realtime components remain local under the project roadmap.

## Production readiness inspection

```bash
PYTHONPATH=modules/automation-control python3 -m stream_autopilot preflight
```

This reads the existing runtime bindings, runs each enabled component's fixed `--validate`
command and checks backend readiness when a non-placeholder `HCP_API_KEY` is supplied in the
environment. It starts no effect workers, touches no supervisor state and never triggers clip
hotkeys or game/broadcast controls. Missing checks appear explicitly with `ready: false`; a
successful diagnostic command does not prove a usable on-air pipeline. Use `--session` to check
an enabled configured session and `--runtime-config` for operator-owned local configuration.
Cloud/live acceptance still requires the owning module's evidence.

## Desktop production ownership

Stream Extend now exposes a persistent production owner in Automated streaming. Readiness,
preview, authorized local/broadcast run, pause/resume, stop and emergency stop use correlated
local JSONL requests. The owner accepts no renderer-selected executable, path or shell command.
Rehearsal and production state are separate. One OS lock protects each production state file;
restart invalidates old readiness and requires a fresh check. Emergency/stop interrupt an
in-flight validation/action. An unconfirmed release or shutdown reports degraded/error.

Public connection endpoints come from the app's saved Connections settings; the generated
backend key and OBS password stay in the native/OS-credential boundary. Operator YAML/JSON
copies live under `HybridCreatorPlatform/stream-autopilot-production/operator`. Config/connection
changes apply after closing the production owner. Worker validators share only the selected
host session, preventing duplicate off-air personas from the same process. Workers remain local.

`local_run_authorized` permits a bounded local running session without broadcasting when
`control_broadcast` is false. Broadcast needs both policy authorization and runtime broadcast
control. Both stay false by default. Native broadcast runs use a distinct recording-first OBS
owner and register its finalized path in the shared Creator inbox; they cannot claim a preexisting
recording. Stop supersedes pending native starts; duplicate Run IDs cannot start twice. A failed
OBS acknowledgement must be reconciled manually, and the read-only inactive check does not stop
someone else's output. App quit waits for owner shutdown and pauses quitting if it is unconfirmed.

The [private-world Minecraft adapter](minecraft/README.md) remains opt-in. The optional package
preparation action installs its pinned SDK only and cannot start a game. The configured avatar
worker exposes owned model gesture/look/emote cues; a queued request is not visible-motion proof.
Full-body cue mode needs a compatible original VTS model and all configured body-only cue IDs.
No avatar asset, game/server, platform login or broadcast permission ships with these controls.

For real model mode in the desktop owner, set `host_rehearsal: false` and the private runtime
copy's `ollama_host`/`ollama_model` to an installed local model. Preflight checks `/api/tags`;
it does not download a model or prove its latency. Close/reopen the owner after policy edits.
