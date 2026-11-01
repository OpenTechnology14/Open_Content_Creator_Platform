# local-llm

Config and reference notes for the agent. Setup steps live in
[`../setup/manual.md`](../setup/manual.md).

| File | Purpose |
|---|---|
| `agent.py` | The loop: read chat → retrieve memory → generate → act |
| `memory.py` | Embed, retrieve, and assemble context |
| `moderator.py` | Classify inbound and outbound messages |
| `migrations/0002_memory.sql` | `agent_memories` schema + vector index |

## Architecture

```
Chat / events
   │  (Twitch/YT chat → backend, OR backend events)
   ▼
Event bus (Redis pub/sub)
   │
   ▼
AI Agent service ──▶ Local LLM (Ollama / llama.cpp)
   │              ──▶ Memory store (Postgres + pgvector)
   │              ──▶ TTS (XTTS / Piper / ElevenLabs)
   ▼
Avatar (VTube Studio / PNGTuber / VRM)  +  audio output bus
   │
   ▼
OBS (avatar source + AI voice bus)
```

Redis and Postgres come from [`storage-data`](../../storage-data/setup/automated.md); the event
bus is [`backend-api`](../../backend-api/setup/manual.md). Everything in this folder is
agent-specific — it consumes that infrastructure rather than standing up its own.

## Tool selection

### LLM serving

| Option | When |
|---|---|
| **Ollama** | Easiest — one install, model pull, OpenAI-compatible API. **Start here.** |
| llama.cpp / llamafile | Lower-level, more control |
| vLLM / TGI | Production-grade, needs a real GPU |

### Models

| Model | VRAM | Note |
|---|---|---|
| Llama 3.1 8B Instruct | 8 GB (quantised) | Solid general-purpose |
| Qwen 2.5 7B Instruct | ~8 GB | Strong reasoning |
| Mistral Nemo 12B | 12 GB | Better persona stability |
| 3–4B models | low | For low-VRAM setups; noticeably less coherent persona |

### Avatar

| Option | Note |
|---|---|
| **VTube Studio** (paid, Steam) | Live2D; industry standard; WebSocket API for control |
| VSeeFace / Warudo | VRM (3D); free or freemium |
| PNGTuber Plus | Static PNG, audio-reactive swapping — bottom of the stack but fine |

See [`character-avatar`](../../character-avatar/setup/manual.md) — that module owns the puppet;
this one owns the decision.

### Agent framework

- **AITuberKit** — purpose-built for AI-driven streamers, with a well-considered persona system.
  Recommended. See [`../aituberkit/README.md`](../aituberkit/README.md).
- **Build-your-own** — a Python service orchestrating LLM + memory + TTS + avatar. Use when
  AITuberKit does not fit.

### TTS

| Option | Trade-off |
|---|---|
| **XTTS v2 (Coqui)** | Open, voice cloning, GPU, local |
| **Piper** | Fast, CPU-friendly, lower quality, local |
| **ElevenLabs** | Best quality, cloud, paid, and a latency cost |

Local TTS keeps the whole loop on your machine — the cloud option is the one place this pipeline
can silently stop being local-first.

## Moderation

The agent can moderate as well as speak:

1. Subscribe to chat messages.
2. Run a classifier prompt — "Is this message [spam | toxic | off-topic | normal]? Respond with
   one word."
3. On `spam` or `toxic`, emit `moderate.delete` or `moderate.timeout`.
4. A small service consumes those and calls the Twitch/YT moderation API.

**Never auto-ban on LLM output alone.** False positives are common, and a wrongly banned viewer
does not come back. The default action is *flag for human review*, not delete.

Run the classifier on **outbound** messages too — what the agent says is as much a liability as
what it hears.

## Latency budget

Voice-to-voice (user speaks → agent replies aloud):

| Stage | Target |
|---|---|
| STT (Whisper) | 200–500 ms |
| Memory retrieval | 50–100 ms |
| LLM generation (first tokens) | 200–500 ms |
| Full completion (50–100 tokens) | 500–1500 ms |
| TTS (XTTS) | 300–600 ms |
| Audio routing | <100 ms |
| **Total** | **1.5–3 s** |

Text chat → voice drops the STT stage: roughly 1–2 s. Acceptable on stream **as long as the agent
is not the only thing happening** — a 2-second gap in a conversation reads very differently from a
2-second gap in a monologue.

Quantised 8B models exist precisely to hold this budget. A larger model answering five seconds
late is worse on stream than a smaller one answering immediately.
