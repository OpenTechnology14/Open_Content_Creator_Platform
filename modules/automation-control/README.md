# automation-control

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (automated)

Automation / Control layer (Roadmap §5). Advanced Scene Switcher, OBS WebSocket, n8n, StreamDeck.

Stream Autopilot is being built under [P-056](../../docs/proposals/PROPOSAL_STREAM_AUTOPILOT.md).
Its first [conversation worker](../ai-agents/stream_host/README.md) belongs to AI Agents.
The [stream director](stream_director/README.md) now connects its events to existing soundboard
hotkeys, OBS scenes/voice mute, NodeCG lower thirds and optional n8n triggers. It previews by
default and requires explicit local bindings to apply actions. The
[Stream Autopilot supervisor](stream_autopilot/README.md) adds durable preflight, preview,
run, pause, recovery and stop state with explicit broadcast authorization and session budgets.
Its production service driver, automated OBS stream start and gameplay remain unimplemented.

Desktop remote control is now wired through the shared relay client in both Extend apps. Requests
are targeted by device ID and require local approval before the allowlisted OBS or ComfyUI action
runs. Authenticated, same-product devices announce themselves and appear in a target selector, so
operators no longer need to copy IDs between workstations. The relay binds announcements and
command sources to the authenticated device and rejects malformed or oversized messages before
fan-out. Presence refreshes periodically and expires from the selector when a peer disappears.
Hosted production, OpenTechnology companion and native Windows acceptance remain open.
