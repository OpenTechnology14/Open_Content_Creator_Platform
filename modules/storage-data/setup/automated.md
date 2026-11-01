# storage-data — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

Fully automated. This is one of the six modules with a real automated path — everything
here runs from Compose plus two committed scripts.

After selecting this module, either Extend app can also start the bundled local `postgres`,
`redis` and `minio` services from **Module setup**. It generates a private local environment once,
retains the service job and health states, and does not require a source checkout. Once those
services are healthy, **Initialize data & workflows** applies both migration trees, creates and
verifies all expected buckets and the recordings lifecycle, and records each step durably. The
helper containers and resources are bundled with the apps; no host `psql` or `mc` is required.

## One command

MinIO server/client images are built from checksum-pinned upstream source because the old
published images no longer pull. The first build downloads Go dependencies and may take
several minutes; subsequent starts use the cache. The same recipe is bundled in both apps.
See [source-build provenance and verification](../minio/README.md).

```bash
make up
```

Brings up `postgres`, `redis`, and `minio` (all in the default Compose profile, no flag needed),
alongside the rest of the core stack.

## Then initialise

```bash
make migrate
```

Runs `scripts/setup/postgres_migrate.sh`, which applies
`modules/storage-data/postgres/migrations/0001_init.sql` — tables `creators`, `streams`,
`events`, `assets`.

```bash
./scripts/setup/minio_init.sh
```

Creates buckets: `comfyui-outputs`, `recordings`, `models`, `project-assets`, `backups`,
`nature-corpus`, `cityscape-corpus`.

## Verify

```bash
make ps          # postgres, redis, minio all Up
make healthcheck # smoke-tests running services
```

MinIO console at http://localhost:9001, S3 endpoint at http://localhost:9000 (credentials
from `.env`).

`make migrate` applies migrations from **both** module directories — `storage-data`'s and
`ai-agents`' — in filename order, and `0001_init.sql` creates the `pgcrypto` and `vector`
extensions itself. There is no manual SQL step.

## Not automated

- **DigitalOcean.** The cloud overlay swaps local Postgres/Redis for managed services and
  MinIO for DO Spaces — endpoint and credential changes in `.env`, not a script.
