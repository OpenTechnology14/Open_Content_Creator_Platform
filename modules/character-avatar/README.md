# character-avatar

**Labels:** `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

Character / Avatar layer (Roadmap §4). PNGTubers, VTube Studio, VRM avatars, AI persona surfaces.

## Agent-driven avatars

The avatar becomes interesting when something else drives it. The seam: the AI agent decides an
expression or mouth state, and this module applies it.

- **VTube Studio** exposes a WebSocket API for exactly this — driven here by
  [`vtube/avatar_control.py`](vtube/avatar_control.py), which subscribes to the same
  `agent.reply` Redis channel `ai-agents/local-llm/agent.py` publishes every reply to, triggers a
  "talking" VTS hotkey for a duration estimated from the reply's length, then an "idle" hotkey.
  Which hotkey fires per persona is configured in
  [`vtube/avatar_mapping.yaml`](vtube/avatar_mapping.yaml), not hardcoded.
- **PNGTuber** state is driven by the audio level of the AI voice bus — see
  [`../audio-production/routing/README.md`](../audio-production/routing/README.md), and make sure
  AI-VOICE is *not* routed back into the agent's own input.

[`ai-agents`](../ai-agents/local-llm/README.md) owns the persona, memory, and moderation. This
module owns the puppet.

