# storage-data — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

Prefer the automated path — it covers everything below except pgvector. Use this when you are
running services outside Compose, or on DigitalOcean managed services.

## Postgres

Persistent state: creator profiles, session metadata, event log, asset pointers.

```bash
docker compose up -d postgres
```

Schema lives at `modules/storage-data/postgres/migrations/0001_init.sql` and owns:

- `creators` — per-creator profile + settings
- `streams` — session metadata
- `events` — generic event log (scene changes, AI actions)
- `assets` — pointers into MinIO

Apply it:

```bash
./scripts/setup/postgres_migrate.sh
```

### pgvector and the agent memory schema

Both are handled by the same command. `postgres_migrate.sh` applies migrations from **both**
module directories in filename order:

| Order | File | Creates |
|---|---|---|
| 1 | `storage-data/postgres/migrations/0001_init.sql` | `pgcrypto` + `vector` extensions, then `creators`, `streams`, `events`, `assets` |
| 2 | `ai-agents/local-llm/migrations/0002_memory.sql` | `agent_memories` with a `vector(768)` embedding column |

> **Corrected 2026-08-31.** An earlier version of this doc said pgvector was a manual
> `CREATE EXTENSION` step and that `0002_memory.sql` was not applied. Both were wrong — the
> script has always listed the `ai-agents` directory, and `0001_init.sql` creates both extensions.
>
> Two real bugs were found and fixed in the same pass: the script used `mapfile` (bash 4+, absent
> from macOS's `/bin/bash` 3.2), and it sorted **full paths**, which applied `ai-agents/0002`
> before `storage-data/0001` — the opposite of the "lexical order" it promises.

## Redis

The event bus. Pub/sub between FastAPI ↔ NodeCG ↔ OBS automation, WebSocket fanout (one
publisher, many overlay subscribers), rate limiting and caching.

```bash
docker compose up -d redis
```

## MinIO

S3-compatible asset store for AI outputs, recordings, project files, and model weights.

Compose now builds MinIO from pinned source; allow several minutes for its first build.
See [build/provenance details](../minio/README.md). The S3 API and bucket contract remain the same.

```bash
docker compose up -d minio
./scripts/setup/minio_init.sh
```

Buckets created: `comfyui-outputs`, `recordings`, `models`, `project-assets`, `backups`,
`nature-corpus`, `cityscape-corpus`.

Console http://localhost:9001 · S3 endpoint http://localhost:9000 (credentials from `.env`).

### Feeding MinIO from ComfyUI

Two patterns; start with the first:

1. **Filesystem hand-off** — ComfyUI writes to a local output folder and a watcher uploads.
   Ships as `modules/realtime-ai/comfyui/scripts/output_to_minio.py`.
2. **S3 SaveImage custom node** — community nodes (e.g. `comfyui-s3`) write directly. More setup.

## DigitalOcean

Swap MinIO for **DO Spaces** and local Postgres/Redis for managed services. The same S3 client
code works against either by changing endpoint and credentials in `.env`.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — script portability, migration ordering, bucket declarations
- `make ps` — postgres, redis, minio all Up
- `make migrate` — migrations apply in filename order

**Manual — nothing automates these:**

- [ ] `psql` lists the four tables `0001_init.sql` creates, plus `agent_memories` from `0002`
- [ ] MinIO console shows all **seven** buckets, including `nature-corpus` and `cityscape-corpus`
- [ ] `redis-cli ping` returns `PONG`
- [ ] `SELECT extname FROM pg_extension;` includes `vector` and `pgcrypto`

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
