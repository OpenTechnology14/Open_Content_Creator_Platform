# Test Suites

Cross-module unit, contract, integration, and scenario tests.

Run with `make test` (or `python3 -m pytest`). `pyproject.toml` scopes collection to this
directory — without that, pytest also matches `scripts/setup/test_obs_websocket.py`, a manual
connectivity utility that `sys.exit()`s at import and crashes collection.

## What exists

| Suite | Covers | Needs a service? |
|---|---|---|
| `storage_data/test_setup_scripts.py` | Shell-script portability and strict mode, migration ordering and coverage, MinIO bucket declarations, migration transactionality | **No** — fully offline |
| `tests/docs/test_docs_integrity.py` | Links, doc index coverage, proposal queue coverage, module labels, matrix coverage, use-case coverage | **No** — fully offline |
| `backend_api/test_routes.py` | FastAPI route table — catches double-prefix and similar routing bugs by inspecting `app.routes`, no server needed. Python 3.11+ only (skipped below that) | **No** — fully offline |
| `acceptance/test_creator_journey.py` | **P-016.** The one end-to-end journey: create a stream, publish an event, read it back, round-trip an object through MinIO, stop the stream, confirm the metric moved | **Yes** — marked `live`, excluded from the default run |

## The offline / live split

Everything here is **offline**: no Postgres, no MinIO, no network, no GPU. That is deliberate, and
it is not a limitation — both bugs this suite was written for were caught without a database:

- `postgres_migrate.sh` used `mapfile` (bash 4+), so `make migrate` died on macOS's `/bin/bash` 3.2.
- It sorted full paths, applying `ai-agents/0002` before `storage-data/0001`.

Live checks against real services live in `tests/acceptance/`, marked `pytest.mark.live` and
excluded from the default run by `pyproject.toml`'s `addopts`. Run them with
`make test-acceptance`. `docker_stack` in `tests/acceptance/conftest.py` skips the whole directory
— not fails — when no Docker daemon is available, so a contributor without Docker still gets a
green default suite.

Acceptance runs use a unique `hcp-acceptance-*` Compose project so teardown targets only
that run's volumes, never the default creator stack. Existing fixed service ports/container
names can still conflict with a running stack; use a dedicated test host rather than stopping
an unrelated creator session. CI builds the pinned MinIO server and client before the live
journey and verifies the real bucket/lifecycle bootstrap too.

## Adding a test

New behaviour needs deterministic success, failure, timeout, and recovery coverage where those
paths exist. A bug fix needs a test that fails before the fix and passes after — `CLAUDE.md` §9.
Prove it: revert the fix and watch it fail.

Release gates: [`../docs/proposals/PROPOSAL_RELEASE_GAP_CLOSURE.md`](../docs/proposals/PROPOSAL_RELEASE_GAP_CLOSURE.md).
