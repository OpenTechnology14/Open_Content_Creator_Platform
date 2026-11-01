# ai-agents — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

**Partially automated.** The datastore is; the model runtime is not.

## What is automated

```bash
make up        # postgres (the memory store)
make migrate   # applies 0001_init.sql
```

## What is not

- **Ollama.** Installed with a vendor script per OS, not by this repo. A commented-out `ollama`
  service exists in `docker-compose.yml` — uncomment it if you want container parity.
- **Model pull.** `ollama pull` is manual and downloads several GB.
- ~~pgvector~~ — **corrected 2026-08-31.** `make migrate` *does* apply
  `local-llm/migrations/0002_memory.sql`: `scripts/setup/postgres_migrate.sh` lists this module's
  migration directory, and `storage-data`'s `0001_init.sql` creates the `vector` and `pgcrypto`
  extensions. No manual SQL step is required.
- **The agent itself.** `local-llm/agent.py`, `moderator.py`, and `memory.py` are run directly
  with `python`; there is no service definition or Make target.

## What exists

Three real Python files (~395 lines): agent, moderator, memory.

P-056 also adds [the Stream Autopilot host](../stream_host/README.md), a separate native worker
with a real validation/rehearsal CLI and optional backend event transport. It does not require
the legacy pgvector agent loop. Its dependencies and startup are manual; no service definition
or automatic model installation is supplied. See that README for the commands and verification.

## Remote management (the app path)

Stream Extend is specified to let you watch and steer the agent from a phone — review what it
said, adjust persona settings, and mute it mid-stream.

**Specified, not shipped** — `CLAUDE.md` §11 has this module at `scaffolded`.

The mute path matters more than the rest: an agent that says something wrong on a live stream
needs an off switch that is not "alt-tab and find the terminal". Until the app exists, wire that
kill switch yourself — the agent subscribes to Redis, so publishing a stop event is enough.

Config and tuning reference: [`../local-llm/README.md`](../local-llm/README.md).
