# character-avatar — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

Python dependency setup is automated. VTube Studio installation, avatar assets, its one-time plugin
authorization and hotkey acceptance remain manual desktop steps.

## What exists

Two Python files in `vtube/`: `vts_client.py` (~115 lines, a minimal VTube Studio WebSocket API
client) and `avatar_control.py` (the agent -> avatar bridge, `P-042`, 2026-09-01) — it subscribes
to Redis's `agent.reply` channel and drives `vts_client.py`'s hotkey triggers, configured by
`avatar_mapping.yaml`. Run `avatar_control.py` directly; there is no service or Make target, and
it does not appear in `docker-compose.yml` — VTube Studio itself is a desktop app this bridge
only talks to over a local WebSocket.

## What automation would take

Avatar assets and VTube Studio model files are per-creator and licensed individually, so an
in-repo script could at most wire the control path once the avatar exists — which is exactly what
`avatar_control.py` now does. What's still not automatable: VTube Studio's own installation, model
loading, and hotkey configuration (Settings -> Hotkeys) are all inside a desktop app's GUI, and the
one-time auth-token popup VTube Studio shows a new plugin can't be clicked through by a script. The
dependency this module shares with automation is the AI agent driving it — see
[ai-agents](../../ai-agents/setup/automated.md).

P-056 also adds [`stream_avatar`](../stream_avatar/README.md), which consumes actual native speech
start/finish/cancel events and activates configured Talk/Idle hotkeys. This removes the older
text-length timing estimate from the new path. A live avatar model and full-body animation remain
separate acceptance work.
