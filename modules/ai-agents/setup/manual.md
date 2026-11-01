# ai-agents — manual setup

For P-056's separate session-aware co-host, use [the Stream Autopilot host instructions](../stream_host/README.md).
The legacy single-persona loop below is unchanged. The new worker's speech/OBS/avatar integration
is not yet a completed creator journey.

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

A local LLM persona with memory that reads chat and drives the avatar — no per-message API bill.

## Prerequisites

Postgres running with pgvector enabled — see
[storage-data](../../storage-data/setup/manual.md). Redis and FastAPI from
[backend-api](../../backend-api/setup/manual.md) if the agent is to publish events.

## Memory store

```bash
docker compose up -d postgres
./scripts/setup/postgres_migrate.sh
```

Then, manually:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Apply `modules/ai-agents/local-llm/migrations/0002_memory.sql` —
`agent_memories (id, agent_id, content, embedding vector(768), created_at, importance, tags[])`
with an HNSW or IVFFlat index on `embedding`.

> Confirm that migration file exists before relying on it; it is referenced by the guide but not
> applied by `make migrate`.

**Alternative:** Chroma is a separate service and easier if you would rather not add a Postgres
extension.

## Install Ollama

```bash
# Linux / WSL
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

ollama pull llama3.1:8b-instruct-q4_K_M
ollama run llama3.1:8b-instruct-q4_K_M "Say hi"
```

Ollama serves on `localhost:11434` with an OpenAI-compatible API. A commented-out `ollama` service
exists in `docker-compose.yml` for container parity.

## Memory retrieval

`local-llm/memory.py`:

1. Embed the incoming message with a local embedding model (e.g. `nomic-embed-text` via Ollama).
2. Top-k similarity search against `agent_memories`, filtered by `agent_id`.
3. Combine with a recent-conversation buffer.
4. Inject into LLM context as `<memory>…</memory>` blocks.

A persona without memory is just a chatbot — this step is what makes it worth running.

## Agent service

`local-llm/agent.py` is the loop: read chat → retrieve memory → generate → act.

## Moderation

`local-llm/moderator.py` is a light filter. Run it on **both** directions — what reaches the agent
and what the agent says. An unmoderated agent on a live stream is a liability, not a feature.

## Avatar control

The agent decides; [character-avatar](../../character-avatar/setup/manual.md) applies.

## Latency budget

Chat message → embed → retrieve → generate → TTS → avatar. Each stage compounds. Quantised 8B
models exist precisely so this stays inside a conversational window; a larger model that answers
five seconds late is worse on stream than a smaller one that answers immediately.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] `ollama run` responds locally
- [ ] A message written now is retrieved as memory in a later, separate session
- [ ] The moderator blocks a deliberately bad input **and** a deliberately bad output
- [ ] Agent output visibly drives the avatar

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.
## Troubleshooting

- **Agent has no memory across restarts** — pgvector or `0002_memory.sql` was never applied.
- **Responses take many seconds** — the model is too large for available VRAM and is spilling to
  CPU; use a smaller quantisation.
- **`connection refused` on 11434** — Ollama is not running as a service.
