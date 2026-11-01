# Proposal: Acceptance harness — one executable creator journey

**Queue row:** `P-016`
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — Real cross-service journey, failure recovery and promotion evidence
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Done` (all 4 phases, 2026-09-01) — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md); this document is frozen at proposal time (2026-08-31) except where `§10`'s table and this line record what actually happened
**Owner:** Agent
**Date:** 2026-08-31
**Roadmap layer(s):** Cross-cutting. Ships in neither app, like `marketing-crosswalk`
**Evidence level (2026-08-31, at proposal time):** §2 Verified against the working tree. The journey itself was **Proposed** — it had never been run, and the authoring environment could not run it (§2.4).
**Outcome (2026-09-01, added during a `docs/` sweep, `P-048`):** the journey **did run**, repeatedly, in CI — first full green run 33452956159 (private development evidence; not distributed), after six PR pushes that each found a real bug (§2.4's "expect the first CI run to fail on something this proposal did not anticipate" held true five more times over). §2.4's "cannot run it here" was about the *authoring* environment specifically and stays true of that environment — it was never a claim about CI, which is where §2.5 always said the real execution would happen.

---

## 1. Executive summary

Build one journey that exercises the platform end to end and **fails CI when it breaks**.

**Why now:** every module except `marketing-crosswalk` is `scaffolded`, and promotion to
`implemented` requires evidence. Nothing in this repository produces end-to-end evidence, so no
module can be promoted regardless of how finished it is. `storage-data` is the live example — its
work is done (`P-024`), and it is still `scaffolded` because nothing proves the path works.

**Smallest shippable result:** a single test that brings up the default Compose profile, drives a
stream through create → event → read-back → stop, asserts the asset and the metric landed, and
tears down. One test, one command, red when broken.

**What it does not do:** prove OBS, ComfyUI, a GPU, or any desktop application works. Nothing can
automate those, and pretending otherwise is the failure mode this repo already documents.

**Scope, settled (`D-01`):** the complete journey is **UC-1** in
[`../../tests/USE-CASES.md`](../../tests/USE-CASES.md) — 15 steps, of which this harness proves 4.
The release-checklist line closes when UC-1 passes end to end, not when this harness goes green.
This proposal closes the automatable portion and states that plainly.

---

## 2. Verified current state

### 2.1 There is no end-to-end coverage

**Verified** — `tests/` contains exactly two suites, both offline:

| Suite | Covers | Touches a service? |
|---|---|---|
| `tests/storage_data/test_setup_scripts.py` | Shell portability, migration ordering, bucket declarations | No |
| `tests/docs/test_docs_integrity.py` | Links, index coverage, module/matrix/status coverage, doc headers | No |

`python3 -m pytest` reports **453 passed in 0.31s**. That runtime is itself the evidence: nothing
starts a container.

### 2.2 The release checklist names this work verbatim

**Verified** — `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md:19`:

> - [ ] At least one complete local-first creator journey passes automatically or by a scripted acceptance harness.

Unchecked. No work package in `P-001` owns it (`P-001` §3.1).

### 2.3 What a journey could actually exercise today

**Verified** by reading the routers and compose file.

Default Compose profile (no flag needed): `postgres`, `redis`, `minio`, `fastapi`, `prometheus`,
`source-health-exporter`, `loki`, `promtail`, `grafana`.

Routes that exist and are reachable:

| Route | File | Behaviour |
|---|---|---|
| `GET /health`, `GET /ready` | `routers/health.py:10,16` | Liveness and readiness |
| `POST /streams` | `routers/streams.py:28` | Creates a stream |
| `POST /streams/{id}/stop` | `routers/streams.py:43` | Stops it |
| `POST /events` | `routers/events.py:34` | **Publishes to Redis** (`events.py:64`) and persists |
| `GET /events/recent` | `routers/events.py:85` | Reads back |
| `GET /metrics` | `main.py:45` | `prometheus-fastapi-instrumentator`, scraped by `prometheus.yml`'s `fastapi` job |

That set spans `storage-data` (all three services), `backend-api`, and `observability` — three of
the five root modules, and the two with the highest usage counts in
`docs/agent/MODULE-MATRIX.md`.

### 2.4 This environment cannot run it — **Blocked**

**Verified** on 2026-08-31: `docker info` fails, and neither `psql` nor `mc` is on `PATH`.

This matters for scoping, not just disclosure: **I cannot validate the journey by running it
here.** The harness will be written against verified route signatures and compose service names,
and its first real execution will be in CI. Expect the first CI run to fail on something this
proposal did not anticipate — that is normal for a harness and is why §8 phases it.

### 2.5 CI would run it today

**Verified** — `.github/workflows/ci.yml` has five steps: Install tooling, Ruff lint, Validate
docker-compose, compose config, Tests. The Tests step is now unconditional `pytest -q` (`P-024`),
so a new suite is picked up with no workflow change. `ubuntu-latest` provides a Docker daemon.

---

## 3. Problem, goals, and non-goals

**Actor:** a maintainer, and CI on every PR.

**Pain:** "does the platform work?" has no answer that is not a human clicking. Seventeen modules
are documented; zero have been proven to interoperate.

### Goals

| # | Goal | Measurable as |
|---|---|---|
| G1 | One journey passes automatically | A single `pytest` marker runs it; green means the path worked |
| G2 | It fails when the platform breaks | Mutation: stop `redis`, the journey fails with a useful message |
| G3 | It does not slow the offline suite | Default `make test` stays under a second and starts no container |
| G4 | It unblocks promotion | `storage-data` can move to `implemented` with this as its evidence |
| G5 | Its limits are stated, not implied | The harness itself reports what it did **not** cover |

### Non-goals

- **Not** a general test framework. One journey, plus the seam to add a second.
- **Not** desktop, GPU, OBS, ComfyUI, or Krita coverage. Those stay manual in
  `tests/ACCEPTANCE-CHECKLIST.md` — 28 lines are marked **manual** for reasons no harness changes.
- **Not** a replacement for `CLAUDE.md` §9's per-bug regression test.
- **Not** multi-node, DigitalOcean, or Tailscale. `P-001` owns release evidence.

### Constraints

- `CLAUDE.md` §2: local-first. The harness must not require a network beyond the local stack.
- `CLAUDE.md` §10: no cross-module imports. The harness talks HTTP and S3, never imports module code.
- `tests/README.md`: hardware and live-cloud checks stay out of the required offline suite.

---

## 4. User paths and states

| Path | Expected behaviour |
|---|---|
| **First run, no Docker** | Skipped with a named reason, not failed. `pytest.skip("docker unavailable")`. A developer without Docker still gets a green offline suite |
| **Normal success** | Stack up → journey passes → stack down. Exit 0 |
| **Missing dependency** | A service never becomes ready → fail after the readiness budget with **which** service and its last health response |
| **Invalid state** | A route returns an unexpected shape → fail naming the route, the expected field, and what arrived |
| **Offline / degraded** | Redis reachable but Postgres down → fail at the first assertion that needs Postgres, naming it. Never a bare `ConnectionError` traceback |
| **Retry** | Readiness polls with a bounded budget. The journey body itself does **not** retry — a flaky journey is a finding, not something to paper over |
| **Cancellation** | `Ctrl-C` mid-run still tears the stack down (fixture teardown, not `atexit`) |
| **Recovery** | Teardown is idempotent. A previous crashed run's containers are removed before the next starts |
| **Re-run** | Fully repeatable: unique per-run identifiers, no state carried between runs |

**The skip path is the important one.** If the harness fails where Docker is absent, every
contributor without Docker gets a red suite, learns to ignore red, and the harness stops working
as a signal.

---

## 5. Injection map

| Location | Symbol / surface | Change | Verification |
|---|---|---|---|
| `tests/acceptance/conftest.py` | `docker_stack` session fixture | **New.** Bring up the default profile, poll readiness, yield, tear down | Fixture runs twice in a row cleanly |
| `tests/acceptance/conftest.py` | `pytest_collection_modifyitems` | **New.** Skip `live` when Docker is absent | Suite green on a machine without Docker |
| `tests/acceptance/test_creator_journey.py` | `test_creator_journey` | **New.** The journey below | Passes in CI; fails with `redis` stopped |
| `pyproject.toml` | `[tool.pytest.ini_options] addopts` | Add `-m "not live"` so the default run stays offline | `make test` starts no container |
| `pyproject.toml` | `markers` | `live` already declared (`P-024`) | — |
| `Makefile` | `test-acceptance` | **New** target: `pytest -m live` | `make test-acceptance` runs only the journey |
| `.github/workflows/ci.yml` | new step after `Tests` | **New.** `make test-acceptance` | CI red when the journey breaks |
| `tests/ACCEPTANCE-CHECKLIST.md` | Cross-cutting section | Flip the journey line from **blocked** to **auto** | The line names the test |

### The journey

```
1. make up                      → default profile
2. poll GET /health             → 200 within the readiness budget
3. POST /streams                → 201, capture id
4. POST /events {stream_id}     → 201; publishes to Redis (events.py:64)
5. GET /events/recent           → the event is present
6. PUT an object to MinIO       → then GET it back, bytes identical
7. POST /streams/{id}/stop      → 200
8. GET /metrics                 → the request counter moved
9. make down                    → teardown, idempotent
```

Steps 3–5 prove `backend-api` + `postgres` + `redis` interoperate. Step 6 proves `minio`. Step 8
proves `observability` sees the traffic. **That is the platform's backend half working together —
the first evidence of interoperation this repo would have.**

---

## 6. Contract details

**No API, schema, or migration changes.** The harness is a consumer; if it needs a route that does
not exist, that is a separate proposal.

**Telemetry:** none added. It reads `/metrics`, it does not emit.

**Privacy:** no real credentials. `.env.example` values or per-run generated ones. The harness must
never read a developer's real `.env` — asserted in `tests/docs/` alongside the other guards.

**Compatibility:** pinned to the default Compose profile. Adding a service does not break it;
removing or renaming one does, and should.

---

## 7. Scenarios and pressure tests

Defined before implementation, per SOP step 7.

| # | Scenario | Expected |
|---|---|---|
| S1 | Happy path, clean machine | Passes |
| S2 | Run twice back to back | Passes both; no leaked state |
| S3 | Docker absent | Skipped with a named reason; suite green |
| S4 | `redis` stopped before the run | Fails at step 4, naming Redis |
| S5 | `postgres` stopped before the run | Fails at step 3, naming Postgres |
| S6 | `minio` stopped before the run | Fails at step 6, naming MinIO |
| S7 | `fastapi` slow to start | Passes — readiness budget absorbs it |
| S8 | `fastapi` never starts | Fails after the budget with its last health response |
| S9 | `Ctrl-C` mid-journey | Stack torn down |
| S10 | Previous run crashed, containers left | Cleaned before starting |

**S4–S6 are the ones that matter.** A harness that passes is worth nothing until it has been seen
to fail for the right reason — that is `CLAUDE.md` §9's revert-and-watch-it-fail rule applied to
the harness itself, and §9 of this proposal requires it as evidence.

---

## 8. Phases, gates, rollout, rollback

| Phase | Work | Gate |
|---|---|---|
| **1** | Fixture + skip logic + `-m "not live"`. No journey yet | `make test` unchanged and offline; `make test-acceptance` runs zero tests cleanly |
| **2** | The journey, steps 1–5 (`backend-api` + `postgres` + `redis`) | Passes in CI; S4 and S5 verified by stopping each service |
| **3** | Steps 6–8 (MinIO, metrics) | S6 verified. **Superseded by D-01's later resolution (see below): the checklist line does not flip to auto** — it names UC-1, not this harness, and this harness proves 4 of UC-1's 15 steps |
| **4** | CI step + `storage-data` promoted to `implemented`, citing this | `marketing-crosswalk validate` still passes after the §11 edit |

**Phase 1 is independently valuable** — it establishes the offline/live split that
`tests/README.md` already asks for, even if Phase 2 stalls.

**Rollout:** additive. No existing test changes behaviour.

**Rollback:** delete `tests/acceptance/`, drop the CI step, revert the `addopts` line. Nothing else
depends on it.

**Dependencies:** none. `storage-data` (`P-024`) is done; the routes exist.

### Unresolved decisions

| ID | Question | Recommendation |
|---|---|---|
| **D-01** | Does this close the release-checklist line, or only part of it? | **Resolved 2026-08-31 (owner-directed): only part.** The owner asked for a use-case summary defining what the system working at the highest level actually looks like — that is [`../../tests/USE-CASES.md`](../../tests/USE-CASES.md). The complete journey is **UC-1**, 15 steps, of which this harness proves 4. Closing the line on a backend journey would claim 25 steps while proving 8. **The line closes when UC-1 passes end to end**, by any mix of command and human; `P-016` closes its automatable portion and says so |
| **D-02** | Does CI run the journey on every PR, or nightly? | **Every PR.** It is the only interoperation signal; nightly means finding breakage a day late. Revisit if it exceeds ~3 minutes |
| **D-03** | Real MinIO, or `moto`/stub? | **Real MinIO.** A stub proves the client, not the platform, and `minio` is already in the default profile |
| **D-04** | Does a failed journey block merge? | **Yes, once Phase 3 lands.** A non-blocking signal is one people learn to ignore — the same argument that made the Tests step unconditional in `P-024` |

---

## 9. Local verification

Per `PROPOSAL_CREATION_SOP.md` step 9 and `docs/agent/VERIFICATION-MATRIX.md`.

| Row | Command | When |
|---|---|---|
| Python in a module | `make test` | Every phase — must stay offline and fast |
| Docker-compose change | `docker compose config -q`, both files | Phase 1 |
| A bug fix, anywhere | S4/S5/S6 — stop a service, watch the journey fail for the right reason | Phase 2 and 3, **required** |
| A module you consider finished | `storage-data`'s `ACCEPTANCE-CHECKLIST.md` section | Phase 4 |

**Cannot be run in the authoring environment** — `docker info` fails and neither `psql` nor `mc` is
installed (§2.4). First real execution is CI. The `P-016` queue row must record that honestly:
*"Not run locally — no Docker daemon. Verified in CI run <link>."*

---

## 10. Documentation updates

| Doc | Change |
|---|---|
| `tests/README.md` | The offline/live split becomes real; document `make test-acceptance` |
| `tests/ACCEPTANCE-CHECKLIST.md` | **Done differently than planned:** journey line stays **blocked** per D-01's later resolution (it names UC-1, not this harness) — updated to cite the passing CI run instead |
| `docs/agent/VERIFICATION-MATRIX.md` | **Done differently than planned:** the journey row is not removable — "not every authoring environment has Docker" stays true even with a passing CI run — updated to cite the run rather than removed |
| `docs/agent/MODULE-ITEM-MATRIX.md` | New `tests/acceptance/` entry |
| `Makefile`, `docs/README.md` | New target and index row |
| `CLAUDE.md` §11 | `storage-data` → `implemented` (Phase 4, only with CI evidence) |
| `tests/USE-CASES.md` | Mark UC-1 steps 5, 8, 12, 15 and UC-2 steps 1, 8 as covered, naming the test |

`DM-ACCEPTANCE` fires on the checklist edit; `DM-DOCS-INDEX` on any new doc.
