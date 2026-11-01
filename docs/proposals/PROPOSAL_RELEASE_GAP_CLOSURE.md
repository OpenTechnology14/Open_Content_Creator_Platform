# Proposal: Release Gap Closure

**Queue row:** `P-001`
**Agent model / effort:** `gpt-6-astra` / `xhigh` — Release architecture, security and evidence across both apps
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — Testing; critical release-engineering slice built/verified, native and public-release gates open. State is authoritative in [the queue](../PROPOSALS.md).
**Date:** 2026-07-12
**Roadmap layers:** Cross-cutting release engineering; Creator Experience; Backend/API; Infrastructure
**Evidence:** Current gaps verified in `docs/AUDIT.md` and `docs/GAP_AUDIT.md`

## 1. Executive summary

**Critical-testing continuation — 2026-10-12:** the owner requested continuing P-001/P-072 until
ready for Testing and doing critical testing now. Extend the bounded Sol/xhigh child scope to
observed relay context/role/fixture defects, unfinished provider fail-closed gates and the ComfyUI
queue deadline. Rationale: narrowly reproduced defects, existing contracts and real local Postgres
positive/negative controls. Parent release architecture ownership remains Astra/xhigh; no public
release, legal choice, new provider or hosting deployment is authorized by this work.

Critical checks found and repaired actual defects:

- `SET app.tenant_id = $1` raises a real Postgres syntax error. Bound `set_config` now initializes
  context, rejects invalid tenant IDs before borrowing, and releases/reset connections after
  setup/query failures. Five regression cases fail with the old code, pass after the fix and
  fail again when the fix is reverted.
- The Compose bootstrap superuser and a table-owner runtime role bypass RLS. Migration 002
  creates/grants a separate non-superuser `relay_app`; migration 003 sets its password without
  command-line secrets. Compose requires its URL/password and startup rejects superuser/BYPASSRLS
  roles or inactive row security on any tenant table. The role upgrade and quoted synthetic
  password bootstrap were each exercised twice against an owned Postgres 16 instance.
- The old relay fixture deleted a default Compose project's volumes. The replacement uses an
  owned ephemeral loopback cluster/container. A mocked teardown test fails with the old fixture,
  passes with the new one and is mutation-verified; no actual creator/relay volume was deleted.
- `/subscribe` minted the caller's requested tier without provider validation; purchase/key,
  invitation and push stubs could issue tokens or report success. Unimplemented routes now return
  `501 feature_not_available` before token/database/provider effects; push helpers fail explicitly.
  Eight new provider/refresh cases preserve actual refresh and catch every unavailable route;
  reverting provider gates reproduces failures. No purchase, invitation or notification was sent.
- ComfyUI `/queue` lacked a request deadline after `/system_stats` succeeded. A delayed-server
  test fails at five seconds without the repair, returns an error at the three-second deadline
  with it, and fails again when the repair is reverted.

**Testing readiness:** the built critical-engineering slice is handed to Testing; this is not full proposal completion. Public release/tag/signing and existing-volume delivery remain owner/input gated.

**Critical evidence:** 53 relay offline security cases and 10 pinned-backend cases pass in separate
prepared environments with skip rejection. Three real native Postgres tests pass: same-tenant
positive control; cross-tenant read/write/update/delete rejection on all six scoped tables and exact pooled-connection reuse;
and startup rejection for superuser/table-owner roles. Both legacy app Rust suites and shared
relay/setup/settings/recording/social crates pass. New required CI security jobs install real
dependencies and reject selected test skips; live RLS CI uses only an owned Docker instance.
The ordinary offline environment still lacks optional service dependencies; its green run alone
must not be used as security evidence. Docker execution of the new jobs is not claimed locally.

**HCP-014:** required CI now runs `generator.cli validate-local`, checking this repository's
anchors and 20 registered status claims without a sibling checkout. This closes the unwired
registered-claim gate; freeform prose and provider/release claims still require review.

**Audit artifacts:** full-history Gitleaks reports three candidates and the non-ignored source
snapshot reports one. Review identifies invalid HS256/PEM negative-test fixtures and the fixed
mocked OBS challenge response; raw scanner results remain retained, not relabelled as a zero-findings
pass. A source SPDX SBOM is generated; automatic package/license inventory is not legal review or
a built-container/native dependency SBOM. Local reports live under
`output/release-evidence/p001-critical-2026-10-12/`. Root license/target decisions, production
upgrade/password auth, real OBS/ComfyUI, Docker, clean-host/signing, hosted/device and rollback
acceptance remain release gates. No existing database/deployment was changed by the tests.

**WP-7 private evidence slice — 2026-10-12:** owner requested work on the two Accepted
proposals. Bounded child assignment: `gpt-6.1-sol` / `xhigh` for the CI-plan evidence collector,
failure/skip/source-integrity tests and factual release checklist refresh. Rationale: fixed
local check contracts and reviewable evidence serialization; no new native, relay, licensing or
public deployment design. Parent release ownership stays `gpt-6-astra` / `xhigh`; this is a child
scope override, not a replacement of that assignment. The client model/effort is not independently
reported to this task; these assignments are recommendations, not a claim of model dispatch.

Added [release_check.py](../../scripts/testing/release_check.py) and its
[operator instructions](../../scripts/testing/README.md#private-release-evidence-p-001-wp-7).
The collector reuses the reviewed CI allowlist, refuses dirty/non-root or `.env`-bearing source,
binds commit/tree/collector hashes, records each check's exit code/duration and every NOT RUN
step, rechecks source integrity and writes report/optional installer SHA-256 sums outside the
checkout. It never exports raw tool output or credentials, installs dependencies, starts services
or publishes. Operator-supplied hashes do not prove an artifact's build commit.
It always records `release_ready=false`; this closes a tooling slice, **not HCP-013 or WP-7**.

**Real clean-checkout execution:** fresh local clone at
`718240e42c61715873724ac92309773a2541c688`, with no `.env`, Python-only collection:
3 checks PASS (generated docs, Ruff, offline pytest), 28 CI commands NOT RUN and 6 explicit
release gates NOT RUN; exit 0 and source unchanged. Python tooling was supplied from the existing
prepared environment, so this is not a clean-host dependency-install claim. The clone checks
that existing commit, not this uncommitted collector change; the collector itself is covered by
the current-checkout focused/full tests recorded in the queue. Retain the local JSON/checksum
bundle for review. Docker/container, native builds/installers, full-history secret scanning,
SBOM/license review, signatures, outage/rollback and full native/live acceptance were not run.

**Current dependency check:** installed the pinned `obsws-python==1.8.0` check dependency into
the existing virtual environment, then ran `make test-obs`: exit 2 from make (client exit 1),
connection refused on the configured local OBS port 4455. Local ComfyUI TCP port 8188 also
refused connection. This reconfirms a missing running-service prerequisite; it does not prove a
disabled setting specifically or satisfy OBS acceptance. No OBS configuration, account sign-in,
broadcast or media capture was changed/performed.

Native OBS inspection was then attempted through the UI tool; it reported the Mac locked and
unable to unlock automatically. Manual unlock is required before any GUI acceptance can continue.
No OBS window or server setting was inspected/changed by that attempt.

**Current-checkout verification:** 13 focused collector tests pass; full required `make test`
reached 100%, exit 0 (`/tmp/hcp-accepted-final.log`); Ruff passes for `modules/`, `scripts/` and
the new test file. The earlier full run caught generated-registry drift after queue edits; the
registry was synchronized and the full suite rerun successfully. Proposal/lane reporting has
zero missing/extra IDs and `git diff --check` passes. Final collector execution against the same
clean `718240e` clone again passes the three Python checks; the report and both explicitly
supplied existing release-DMG hashes were independently verified. Evidence is local/ignored at
`output/release-evidence/p001-2026-10-12/`; installer/source association remains unverified.

**Sol continuation — 2026-10-08:** owner requested continuing Sol proposal work. A bounded
child override assigns `gpt-6.1-sol` / `xhigh` to PL-D08: replace retired MinIO image pulls
with checksum-pinned builds of the existing upstream server/client, bundle those recipes in
desktop setup, and verify the live creator journey and client bootstrap in CI. Parent release
ownership stays Astra; root licensing and public release remain separate. The [assignment
review](../agent/PROPOSAL-ASSIGNMENTS.md) records all 73 proposals and bounded child routing.

Reproduction: current main CI run `37486648546` fails at MinIO's unauthorized pull; fresh
anonymous Quay repository API reads returned 403 for both server/client on 2026-10-08.
Three regression checks failed before the source-build change and pass after it; 43 focused
storage/verification checks and 23 shared native setup tests passed locally. Source archive
hashes/base manifest digests were checked from successful HTTPS/registry reads. This host
has no Docker daemon; container/runtime acceptance is pending actual CI, not inferred from
the offline checks. Acceptance teardown now uses an owned `hcp-acceptance-*` project so it
cannot delete the default creator stack's data volumes.

**Verified live, 2026-10-08:** CI run 37876242044 (private development evidence; not distributed)
at source `907c3dc` built both pinned source images and passed both live acceptance tests:
the creator journey plus real `mc` bucket/lifecycle initialization. Both desktop build jobs
and the macOS/Windows native rehearsals passed. This closes PL-D08's image-distribution
decision on PR #67; main remains unchanged until merge. ARM64 container/runtime, existing-data
upgrade, physical Windows/device acceptance and production/licensing review are not asserted.

Close HCP-001 through HCP-014 by producing one secure, buildable, scenario-tested local alpha slice. The release slice is:

1. start the local core services;
2. run the shared readiness checks;
3. connect Stream Extend to OBS WebSocket;
4. list scenes and change a scene;
5. connect Creator Extend to ComfyUI;
6. list workflows, submit a typed workflow request, and observe its terminal state;
7. remain usable when the optional cloud relay and OpenTech companion are disabled or offline.

Other roadmap modules remain Scaffolded or Experimental until separately proven. This proposal does not broaden the release claim to every documented capability.

## 2. Relationship to current proposals

- `docs/proposals/PROPOSAL_SETUP_READINESS.md` owns the setup manifest, native check engine, setup UI, and service gating design.
- `PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md` owns the optional sanitized OpenTech handoff.
- This proposal owns the missing implementation sequence, build/test foundation, secure defaults, route trust boundary, and release evidence. Where proposals overlap, the more detailed setup contract controls setup behavior and this proposal controls release gating.

## 3. Verified current state

- `.github/workflows/ci.yml` allows Ruff to fail and treats an empty `tests/` directory as success.
- `Makefile` also suppresses lint failures.
- Both app `package.json` files call SvelteKit/Vite commands, but the directories lack `svelte.config.*`, `vite.config.*`, `tsconfig.json`, and `src/app.html`.
- `apps/stream-extend/src-tauri/src/obs.rs` returns placeholder OBS state and does not implement the v5 handshake or commands.
- `apps/creator-extend/src/routes/+page.svelte` queues `{}` instead of a selected workflow payload.
- Relay TODOs can initiate purchase/subscription/invite/push behavior without completed provider implementations.
- `cloud/docker-compose.relay.yml` defaults to production with fallback JWT/database credentials and publishes Postgres and Redis ports.
- `cloud/relay-api/app/main.py` combines wildcard origins with credentials.
- `.env.example` does not fully document the relay/Spaces variables referenced by Compose.
- The root now has contribution, security, and conduct documents, but no root license and no completed release evidence.

### 3.1 State refresh — 2026-08-30

Re-verified against the working tree. **Every finding in §3 above still holds** — none of the
release gaps have closed since 2026-07-12. What changed is the documentation structure this
proposal writes into, plus two new facts that affect its scope.

**Still true, re-confirmed:**

| §3 finding | Status on 2026-08-30 |
|---|---|
| CI allows Ruff to fail; empty `tests/` treated as success | Unchanged — `tests/` contains one README and no test files |
| Makefile suppresses lint failures | Unchanged |
| Both apps lack Svelte/Vite/tsconfig scaffolds | Unchanged |
| `obs.rs` returns placeholder state | Unchanged |
| Relay TODOs can initiate purchase/subscription/invite/push | Unchanged |
| Compose defaults to production with fallback credentials; DB/Redis ports published | Unchanged |
| Wildcard origins with credentials | Unchanged |
| `.env.example` incomplete | Unchanged — six Compose-referenced values still missing |
| No root license | Unchanged — `D-01` still open and still the only blocker on public release |

**Changed since this proposal was written — affects where its documentation tasks land:**

1. **The numbered guide series is retired.** Setup docs now live at
   `modules/<name>/setup/{manual,automated}.md`, with a redirect map at `docs/guides/README.md`
   ([`../architecture/deviations.md`](../architecture/deviations.md), 2026-08-30). §13's
   documentation updates should target module setup docs, not `docs/guides/`.
2. **Modules are labelled `Content` / `Stream`.** `D-02`'s supported-OS matrix and the "label
   unproven features" task in Work Package 1 can now be expressed per module against
   `CLAUDE.md` §11, which is a per-module status table rather than a per-guide one.
3. **Module count is 16, not 14.** `marketing-crosswalk`, `nature-generation`, and
   `cityscape-generation` were added; `landscape-generation` was split into the latter two.
4. **Feature labelling now has a mechanism.** `modules/marketing-crosswalk` refuses to generate
   any marketing asset that asserts a capability ships while `CLAUDE.md` §11 says `scaffolded`,
   and verifies each status claim against a named line in the target repo. Work Package 1's
   "label unproven features" task is **partly discharged for marketing surfaces** — 46 of 149
   possible assets are blocked on exactly this rule today. It is **not** discharged for the README,
   product-spec, or in-app copy, which remain manual.

**Two findings that post-date this proposal and belong in its scope:**

- **`docs/AUDIT.md`'s "at least one complete local-first creator journey" gate has no owner.**
  Work Package coverage stops at build-green. [`../architecture/future-state.md`](../architecture/future-state.md)
  proposes an `acceptance-harness` module as the candidate owner; until one is selected, the P0
  engineering checklist item cannot be closed by any work package here.
- **Documentation overstates what is committed, in a second place.** §3 records the app and relay
  TODOs. The same class of problem exists in the workflow indexes: six ComfyUI workflows are
  indexed but do not exist, and two live in a different module than the index claims. Both indexes
  now carry verified on-disk tables. This is the same "release-scope TODO/placeholder paths are
  implemented or feature-flagged" gate, applied to content rather than code.

**No decision changes.** `D-01`–`D-04` stand as written, and `D-01` remains the only gate on
public release; all other engineering may proceed while it is pending.

### 3.2 State refresh — 2026-09-02

Re-verified against the working tree during an exhaustive `docs/` sweep (`P-048`), after ~20
proposals of real engineering since §3.1. **Every relay/desktop-app finding below still holds,
checked directly, not assumed** — this proposal's actual P0 gates are untouched. What changed is
everything §3.1 already flagged as adjacent to this proposal's scope, which has now closed.

**Still true, re-confirmed directly (`cloud/relay-api/`, `apps/*` were not touched by any
proposal this session):**

| §3/§3.1 finding | Status on 2026-09-02 |
|---|---|
| ~~CI allows Ruff to fail~~ | **Closed same day, `P-049` (`P-001` WP-1):** `\|\| true` removed from `ci.yml`; the 4 known errors it was hiding are fixed |
| ~~Makefile suppresses lint failures~~ | **Closed same day, `P-049`:** `Makefile`'s `lint` target matches |
| ~~Both apps lack Svelte/Vite/tsconfig scaffolds~~ | **Closed same day, `P-052` (`P-001` WP-3):** both apps build+bundle for real now — see WP-3's own entry below |
| `obs.rs` returns placeholder state | Unchanged — 4 literal `TODO`s remain (handshake + 4 commands) |
| `+page.svelte` queues `{}` instead of a selected workflow | Unchanged — literal `TODO: Load workflow JSON from file and queue it` |
| Relay TODOs can initiate purchase/subscription/invite/push | Unchanged |
| ~~Compose defaults to production with fallback credentials; DB/Redis ports published~~ | **Closed same day, `P-050` (`P-001` WP-2):** `startup_security.py` fails closed in production on a weak `RELAY_JWT_SECRET` or default `RELAY_DATABASE_URL`; Postgres/Redis ports now `127.0.0.1`-bound |
| ~~Wildcard origins with credentials~~ | **Closed same day, `P-050`:** `main.py`'s CORS now lists the two real Tauri origins (`tauri://localhost`, `https://tauri.localhost`, pulled from each app's own `tauri.conf.json`), not `*` |
| No root license | Unchanged — `D-01` still open and still the only blocker on public release |

**No longer true — closed by work in this session, none of it targeting this proposal directly:**

1. **`tests/` is no longer empty.** §3.1 said "one README and no test files" — the offline suite
   now has 900+ cases across every module, CI-enforced and unconditional (`P-024` onward).
2. **`.env.example` is complete.** Every `${VAR}` in both compose files diffed against it directly
   (`P-016`+`P-035`); the "six values missing" claim is false.
3. **Module count is 20, not 16.** `asset-pipeline`, `model-registry`, `character-avatar` (always
   existed, `Stream`-labelled from the start), and `soundboard` were added since §3.1's count of 16.
4. **The acceptance-harness this proposal's §3.1 said "has no owner" now exists and passed in
   CI.** `P-016` built `tests/acceptance/` — a real 9-step creator journey against live
   Postgres/Redis/MinIO/FastAPI, first green run
   33452956159 (private development evidence; not distributed).
   `D-01` (the acceptance-harness proposal's own decision, not this proposal's) resolved that the
   complete journey is UC-1 in `tests/USE-CASES.md`, not this harness alone — the harness proves 4
   of UC-1's 15 steps.
5. **The workflow-index gap is closed.** §3.1 said "six ComfyUI workflows are indexed but do not
   exist." All 8 are on disk (`P-028`), and 5 of the 6 previously-unverified ones are now GPU-run
   verified working end to end on real hardware (`P-043`), 1 confirmed blocked on a real upstream
   `transformers` incompatibility, not a naming gap.

**Net effect on this proposal's own scope, as of when §3.2 was written:** none of its P0 work
packages were closed by the above — every item this proposal itself owns was exactly as open as
`§3.1` found it. **That changed the same day:** owner asked "what's left to do next," was shown
this proposal's work packages as the standout finding (`P-001`'s own text: "All engineering work
except public release can begin while `D-01` is pending"), and picked WP-1 first, then WP-2.
**WP-1 (`HCP-001`/`HCP-002`) is done** (`P-049`) — Ruff blocking in CI and `make lint`, the 4 known
errors fixed. **WP-2 (`HCP-007`) is done** (`P-050`) — the relay fails closed on weak
secrets/default DB URL in production, internal ports bound `127.0.0.1`, CORS lists real origins.
**WP-3 (`HCP-004`) is done** (`P-052`) — both desktop apps' build scaffolding is complete and
reproducibly buildable: real `svelte.config.js`/`vite.config.ts`/`tsconfig.json`/`app.html`,
generated placeholder icons, `tauri.conf.json`'s `frontendDist` pointing at the real build output,
`@tauri-apps/cli` declared, and — verified live on real hardware, not just structurally — a real
`.app`+`.dmg` produced and launched for both apps. Deliberately narrower than the proposal's own
original WP-3 task list: no component test runner, no full Rust lint/test CI job (only
`cargo check`), and `HCP-005`/`HCP-006`'s actual OBS/ComfyUI command logic is untouched — the
scaffold builds, what's inside it is still stubbed. **WP-6 (`HCP-011`) is done** (`P-053`) — most
of the cloud relay's trust boundary was already real, correctly-enforced code (JWT verification,
Postgres RLS tenant isolation, a real 4-path WS handshake); two real gaps found and fixed
(`GET /connections` had zero auth, `api_rate_limit_per_minute` was dead config), plus body-size
limits added. A third, more severe, unrelated bug found while writing the WS handshake tests:
`main.py`'s `/ws` route was missing a `WebSocket` type annotation FastAPI's routing requires —
every real connection closed immediately after `accept()`, meaning the relay's own "core of the
cloud service" had never actually worked when served by FastAPI, and nothing had ever tested it to
notice. Fixed, verified live both ways (pre-fix reproduction via `git stash`, post-fix all 4
failure paths + success). Full detail: `docs/API_ROUTE_AUDIT_LEDGER.md`'s Cloud relay section.
**WP-5's ComfyUI half (`HCP-006`) is done** (`P-054`) — the real selected workflow reaches ComfyUI
and its terminal state is rendered, verified live against real hardware; a real bug found along the
way (every committed workflow's `_meta` block was rejected by ComfyUI's real `/prompt` endpoint,
fixed). **WP-5's OBS half (`HCP-005`) is code-done** (`P-055`) — real `obws`-backed commands, two real
bugs found and fixed (`get_status()` never read `AppConfig`; `get_config` leaked the OBS password),
12 tests including 8 mutation-verified fake-server contract cases now in CI; only real-hardware
acceptance evidence remains, blocked on enabling this machine's OBS WebSocket server (owner step, not
engineering). **Still open: WP-0/7 (root license, governance sign-off) — confirmed open by direct
file reads, not assumed.**

## 4. Goals, non-goals, and decisions

### Gap ownership matrix

| Gap | Owning work package | Closure outcome |
|---|---|---|
| HCP-001 | WP-1 | Executable unit, contract, and scenario suite |
| HCP-002 | WP-1 | CI and Make targets fail closed |
| HCP-003 | WP-0/WP-7 | Approved root license and matching claims |
| HCP-004 | WP-3 | Complete reproducible desktop build scaffolds |
| HCP-005 | WP-5 | Real OBS v5 commands with observed state |
| HCP-006 | WP-5 | Typed ComfyUI workflow queue lifecycle |
| HCP-007 | WP-2 | Relay fails closed with private internal services |
| HCP-008 | WP-2 | Complete machine-validated environment contract |
| HCP-009 | WP-4 | Shared setup status and service gate |
| HCP-010 | WP-7 | Disabled-default sanitized OpenTech companion |
| HCP-011 | WP-6 | Tested trust-boundary decision for each release route |
| HCP-012 | WP-0/WP-7 | Complete governance/security support contract |
| HCP-013 | WP-7 | Clean-clone release evidence |
| HCP-014 | WP-0/WP-7 | Evidence-linked status vocabulary |

### Goals

- Enforce truthful CI and executable scenarios.
- Complete the two desktop app build scaffolds and the defined alpha journeys.
- Implement the shared setup/status contract before service actions.
- Make local and cloud configuration fail closed at the appropriate trust boundary.
- Inventory and enforce authentication decisions for every API/Tauri mutation in the alpha slice.
- Generate clean-clone release evidence and align documentation claims with it.

### Non-goals

- Completing every roadmap module.
- Enabling incomplete subscription, receipt-validation, invitation, or push-provider paths.
- Publicly exposing OBS, ComfyUI, Postgres, Redis, or local media.
- Adding Kubernetes.
- Selecting the license automatically.

### Decision gates

| ID | Decision | Required before | Owner | Default if unresolved |
|---|---|---|---|---|
| D-01 | Root license and accurate public wording | Accepting outside contributions or publishing alpha | Maintainer/legal | Keep private; do not call open source |
| D-02 | Supported alpha OS matrix | Release workflow | Release owner | macOS + Ubuntu as candidates, both unverified |
| D-03 | Local API trust model and API-key storage | Mutating API exposure | Backend/security owner | Bind local only and require configured API key |
| D-04 | OBS WebSocket Rust client crate versus internal protocol implementation | OBS work package | Desktop owner | Use a maintained v5-compatible crate after license review |

All engineering work except public release can begin while D-01 is pending.

**D-03/D-04 implementation reconciliation — 2026-10-12:** the existing
[route ledger](../API_ROUTE_AUDIT_LEDGER.md) records the local API-key trust boundary and
negative authentication tests; the desktop adapters store connection secrets in the shared
OS-vault contract. `apps/stream-extend/src-tauri/src/obs.rs` imports and uses `obws::Client`;
the maintained-crate choice has already been implemented and protocol-tested under P-055.
These two engineering choices are settled in source, so PL-D03/PL-D04 no longer wait on an
unmade architecture decision. Real-provider/native credential acceptance and third-party
license review remain their existing release gates; this reconciliation is not legal sign-off.

## 5. Target repository structure

```text
pyproject.toml
tests/
  unit/
  contract/
  scenarios/
    test_setup_readiness.py
    test_local_alpha.py
    test_relay_security.py
  fixtures/
scripts/maintenance/
  validate_env_contract.py
  release_check.sh
apps/<app>/
  svelte.config.js
  vite.config.ts
  tsconfig.json
  src/app.html
  src/lib/setup/
modules/backend-api/fastapi/app/
  models/setup.py
  services/setup/
  routers/setup.py
```

The setup service follows the file-level design in `docs/proposals/PROPOSAL_SETUP_READINESS.md`; this tree lists only the release-scope subset.

## 6. Direct injection map

| Gap | Location | Symbol/surface | Implementable change | Verification |
|---|---|---|---|---|
| HCP-001/002 | `pyproject.toml` (new) | Ruff/pytest configuration | Define discovery, markers (`unit`, `contract`, `scenario`, `hardware`, `live`), coverage sources, and Ruff rules | `pytest --collect-only` finds required suite; deliberate failure fails |
| HCP-001/002 | `.github/workflows/ci.yml` | `lint-and-test` | Split enforced Python, Compose/env, Stream UI, Creator UI, Rust, and docs jobs; remove all advisory success paths | Required jobs fail closed |
| HCP-002 | `Makefile` | `lint`, new `test-*`, `release-check` | Remove `|| true`; mirror CI commands | Local and CI commands match |
| HCP-003/012 | `/LICENSE`, `README.md`, package manifests | legal/status wording | Apply D-01 consistently; add support/security links | License scan and documentation review |
| HCP-004 | both `apps/*-extend/` | SvelteKit entry/build config | Add Svelte config, Vite Tauri host config, TypeScript config, app HTML, lockfiles | `npm ci`, `npm run check`, `npm run build` |
| HCP-005 | `apps/stream-extend/src-tauri/Cargo.toml` and `src/obs.rs` | OBS v5 client | Add selected client dependency; implement connect/auth, list scenes, set scene, stream status, toggle stream, typed errors/timeouts | Fake OBS contract plus hardware acceptance |
| HCP-005 | `apps/stream-extend/src/routes/+page.svelte` | OBS controls | Replace optimistic/placeholder states with command results; disable controls unless readiness passes | Component and Tauri integration tests |
| HCP-006 | `apps/creator-extend/src/routes/+page.svelte` | workflow queue | Load selected workflow JSON, collect typed inputs, send actual payload, store prompt/job ID, poll/subscribe to terminal state | Fake ComfyUI success/error/cancel tests |
| HCP-006 | `apps/creator-extend/src-tauri/src/comfyui.rs` | `comfyui_workflows`, `comfyui_queue` | Validate workflow paths/schema, return typed queue result and stable errors | Contract fixtures including invalid graph |
| HCP-007 | `cloud/relay-api/app/config.py` | `Settings` validation | Reject default/short JWT and missing production dependencies; add explicit `cors_origins` | Settings unit tests |
| HCP-007 | `cloud/relay-api/app/main.py` | CORS/lifespan | Parse exact origins; prohibit credentials with wildcard; replace prints with structured logging | CORS preflight and startup tests |
| HCP-007 | `cloud/docker-compose.relay.yml` | services/network | Default to development, require secrets, remove host ports for Postgres/Redis, add internal network | Compose config/security assertions |
| HCP-007 | `docker-compose.digitalocean.yml` | Grafana port | Replace invalid CIDR bind with required single `TAILSCALE_IP` or no host port | Compose validation with test env |
| HCP-008 | `.env.example` | environment contract | Add relay and Spaces variables with local/production requirement notes | Env-contract script finds zero missing refs |
| HCP-008 | `scripts/maintenance/validate_env_contract.py` (new) | Compose/env scanner | Compare `${VAR}` references across Compose files to documented variables; allow explicit generated/system list | Unit fixture + CI execution |
| HCP-009 | backend setup files and both app setup routes | setup contract/gate | Implement Phase 1 of setup-readiness proposal | Contract and UI state scenarios |
| HCP-010 | OpenTech adapter/template locations | companion handoff | Implement only after local alpha passes; disabled by default | Privacy, replay, outage tests |
| HCP-011 | `modules/backend-api/fastapi/app/deps.py`, routers | local authorization | Central API-key dependency for mutations; explicit public health/readiness; authenticated WS handshake | Route/WS auth matrix |
| HCP-011 | relay auth middleware/routers | tenant authorization | Add route-level tenant/object checks and rate/size limits to release-scope routes | Cross-tenant negative tests |
| HCP-013 | `scripts/testing/release_check.py`, future release workflow | clean-clone proof | Collect commit-bound local checks and checksums; secret scan, SBOM, native/live/signing/rollback remain separately recorded release gates | Private JSON/checksum bundle; full tagged OS-matrix evidence still required |
| HCP-014 | docs index/roadmap/module READMEs | claim vocabulary | Add machine-checkable status table and prohibit unlinked Implemented/Production upgrades | Docs check in CI |

## 7. Contract details

### 7.1 Stable error envelope

New setup, OBS, and ComfyUI calls return or map to:

```json
{
  "error": {
    "code": "dependency_unreachable",
    "message": "OBS WebSocket is not reachable.",
    "retryable": true,
    "operation_id": "01J...",
    "details": {"check_id": "obs.websocket"}
  }
}
```

Allowed stable codes include `invalid_config`, `unauthorized`, `dependency_unreachable`, `dependency_incompatible`, `request_timeout`, `invalid_workflow`, `conflict`, and `internal_error`. Do not expose tokens, environment values, database URLs, private paths, or stack traces.

### 7.2 Production settings validation

```python
def validate_production_settings(settings: Settings) -> None:
    if settings.environment == "production":
        if settings.jwt_secret.lower().startswith("change-me"):
            raise ValueError("RELAY_JWT_SECRET must be set for production")
        if "localhost" in settings.database_url:
            raise ValueError("Production database URL must be explicit")
        if not settings.cors_origins:
            raise ValueError("At least one production CORS origin is required")
```

The implementation should use Pydantic v2 model validators; the example defines behavior, not the exact final syntax.

### 7.3 OBS command result

```json
{
  "connected": true,
  "obs_version": "31.x",
  "websocket_version": "5.x",
  "current_scene": "Camera",
  "streaming": false
}
```

`obs_toggle_stream` must return the observed post-command state, not merely acknowledge a request. A timeout must produce `request_timeout`, never a guessed state.

### 7.4 Creator workflow request

```json
{
  "workflow_id": "00-starter",
  "workflow_version": 1,
  "inputs": {"prompt": "synthetic test prompt", "seed": 42},
  "client_request_id": "01J..."
}
```

Paths are resolved against the configured workflow directory and cannot escape it. The response includes a ComfyUI prompt ID and normalized state.

## 8. Work packages and implementation order

### WP-0 — Decision and claim freeze

**Files:** `README.md`, root manifests, release checklist.
**Tasks:** record D-01/D-02/D-03/D-04 owners; label unproven features; disable public distribution claims.
**Exit:** no public claim exceeds audit evidence.

### WP-1 — Test and CI foundation

**Files:** `pyproject.toml`, `tests/`, `.github/workflows/ci.yml`, `Makefile`.
**Tasks:** create deterministic unit/contract fixtures; enforce no-empty-suite; add dependency caching; separate `hardware` and `live` jobs from required offline jobs.
**Exit:** CI fails on lint/test/build error and passes without OBS/GPU/cloud credentials.

### WP-2 — Configuration and relay hardening

**Files:** `.env.example`, Compose files, relay config/main, env validation script.
**Tasks:** close HCP-007/008; feature-disable unfinished commerce/invite/push routes with `501 feature_not_available` unless configured and tested.
**Exit:** production refuses defaults; internal ports are private; CORS tests pass.

### WP-3 — Desktop build baseline

**Files:** both app build scaffolds and lockfiles.
**Tasks:** make check/build deterministic; add component test runner; add Rust formatting/lint/test jobs.
**Exit:** clean UI and Tauri builds on D-02 OS matrix.

**Done, 2026-09-02 (`P-052`) — narrower than originally scoped, disclosed rather than silently
dropped.** What closed: `npm install && npm run build`/`npm run check`/`cargo check`/
`npm run tauri build` all pass clean for both apps, verified live (real `.app`+`.dmg`, both
launched). A `cargo check`/`npm run build`+`check` CI job runs on every PR (`ubuntu-latest` only,
`Swatinem/rust-cache`-cached). **What did NOT close, deliberately:** no component test runner
(vitest/@testing-library/svelte) was added — zero tests exist inside either app still, only the
offline structural contract tests at `tests/desktop_apps/`. No Rust formatting (`cargo fmt --check`)
or `cargo test` CI job — `cargo check` only, chosen for cost (§ below). **"Clean builds on D-02 OS
matrix" did not close** — `D-02` is still an open decision gate, and only macOS was proven this
session (the only hardware available); CI's build job runs on `ubuntu-latest` only, which proves
Linux compiles but not that it bundles (no Windows/Linux bundle was produced or tested). The real
multi-OS installable-artifact proof stays `WP-7`'s release-workflow job, once `D-02` resolves —
building that CI matrix before the OS list is decided means guessing at scope that might get thrown
away.

### WP-4 — Shared setup readiness

Implement Phase 1 of the setup-readiness proposal before enabling service buttons.
**Exit:** required/optional/degraded states and targeted retry pass in both apps.

### WP-5 — Alpha service paths

Implement OBS and ComfyUI paths in HCP-005/006.
**Exit:** local alpha scenario passes with fakes in CI and named hardware acceptance evidence.

**ComfyUI half done, 2026-09-02 (`P-054`).** `HCP-006` resolved: `+page.svelte`'s `queueWorkflow()`
now loads the real selected workflow (`comfyui_load_workflow`), queues the real graph
(`comfyui_queue`), and polls a new `comfyui_prompt_status` command every 1.5s to a rendered terminal
state — previously a hardcoded `'{}'` payload with no terminal-state check at all.
`relay.rs`'s `"comfyui"/"queue_workflow"` TODO is now a real call through the same path. **A real
bug found via hardware evidence, not inspection:** every committed workflow's `_meta` doc block
(added by `P-028`/`P-043`) was being forwarded to ComfyUI verbatim; ComfyUI's real `/prompt`
validates every top-level key as a node and rejects `_meta` with `missing_node_type` — every single
committed workflow would have failed to queue as originally wired. Fixed with a
`strip_workflow_meta` helper, mutation-verified, then reverified live: `upscale-4x-v1.json`
real-queued against the real ComfyUI install (`P-043`'s Apple M1 Pro/Metal machine), polled through
`get_prompt_status` to a real terminal `success`, producing a real 3072×3072 PNG output. New shared
`apps/shared/command-error/` crate (`ErrorEnvelope`/`ErrorCode`, §7.1's own example shape) replaces
bare `.to_string()` errors across `comfyui.rs`'s public functions. Fake-server contract coverage:
`apps/creator-extend/src-tauri/tests/comfyui_contract.rs`, 9 `wiremock`-based cases (status,
successful queue, malformed-graph rejection, prompt pending→success/error transitions) plus 9 inline
unit tests — both now run in CI (`ci.yml`'s `build-desktop-apps` job gained a `cargo test` step, a
disclosed partial reversal of `P-052`/WP-3's cargo-check-only scope, necessary since this work
package's own exit bar is "fakes pass in CI"). **Also fixed:** workflow *listing* previously called
ComfyUI's own userdata API (`GET /api/userdata?dir=workflows`) — a different, unsynced set from this
repo's committed, GPU-verified workflow files; switched to the repo-committed files as the source of
truth, so listing no longer depends on ComfyUI being connected (only queueing does).
**Still open, named not silently dropped:** `"blender"/"render"` stays a TODO in `relay.rs` — no
render-job primitive exists in `blender.rs` yet (only `open()`/`run_script()`), that's new design
work, not a wiring fix; `CreatorRelayManager` is still never instantiated from `lib.rs` (making
remote relay control reachable at all is unscoped, separate from this fix); per-workflow typed input
collection (image upload into `LoadImage`, prompt/seed overrides) — no input-collection UI exists
for any workflow yet, out of scope by this work package's own bar ("the real selected graph reaches
ComfyUI and its terminal state is observed," not a generalized node-field-substitution system).
**OBS half (`HCP-005`) code-done, 2026-09-02 (`P-055`).** All 5 `obs.rs` stubs
(`get_status`/`get_scenes`/`switch_scene`/`get_stream_status`/`toggle_stream`) replaced with real
`obws` 0.15 calls against a persistent connection (`ObsClientCache`, `Arc<tokio::sync::Mutex<Option
<obws::Client>>>`) that reconnects once on a stale/dropped connection before surfacing an error —
verified by a fake-server test that kills the connection between two calls and confirms the second
call still succeeds. **Two real bugs fixed as part of making this real, not separately:** `get_status
()` previously took zero parameters and never read `AppConfig` at all; `get_config` returned the OBS
password in plaintext to any caller (now redacted via a new `AppConfigView` DTO — `obs_password_set:
bool`, never the value; `set_config` is unchanged, still the only way a password gets set). `AppConfig`'s
`obs_ws_url`/`obs_ws_password` split into `obs_host`/`obs_port`/`obs_password`, matching this repo's
own `OBS_WEBSOCKET_HOST`/`PORT`/`PASSWORD` convention (`.env.example`) and `obws::Client::connect`'s
real parameter shape. `switch_scene` returns the freshly re-fetched scene list, not `Ok(())` — checked
directly against the real obs-websocket v5 protocol spec, `SetCurrentProgramScene` has zero response
fields, so a re-read is the only real "observed result." `toggle_stream` returns obws's own
authoritative new-state bool with no redundant re-read (a dedicated contract test asserts exactly one
request is sent). `relay.rs`'s `"obs"/"switch_scene"` and `"obs"/"toggle_stream"` TODOs are now real
calls — `StreamRelayManager` gained the same `Arc<Mutex<AppConfig>>` handle `CreatorRelayManager` got
in `P-054`, plus a shared `Arc<ObsClientCache>`; **still never `.manage()`d/instantiated from
`lib.rs`**, same disclosed unscoped-feature status as its creator-extend counterpart. New shared
`command-error` crate (built in `P-054`) reused, not rebuilt. **A genuine wire-protocol subtlety found
while writing the fakes, not assumed:** `obws::Client::connect()` issues its own internal `GetVersion`
request as part of version verification before it ever returns — confirmed by reading
`obws-0.15.0`'s own source (`~/.cargo/registry/.../obws-0.15.0/src/client/mod.rs`), not the old stub's
unverified TODO comments. An initial version of both the reconnect test and the "exactly one request"
toggle-stream test were structurally wrong until this was found — the connect-time request was being
silently counted as "the" request under test. **12 tests** (4 inline unit tests +
`apps/stream-extend/src-tauri/tests/obs_contract.rs`, 8 cases against a hand-rolled
`tokio-tungstenite`-based fake OBS server — the first Rust test file in this app) run in CI via the
already-existing `build-desktop-apps` `cargo test` step, no CI change needed (`P-054` added that step
specifically anticipating this PR). **4 of the 8 contract tests mutation-verified**
(reconnect-on-error retry, `switch_scene`'s post-set re-read, the per-request timeout wrapper, the
real field-name mapping in `get_stream_status`) — each fix reverted, the matching test confirmed to
fail (one, the timeout-wrapper removal, confirmed by the test genuinely hanging past a 15s bound
rather than completing, since setting `REQUEST_TIMEOUT` to a very large value would otherwise let the
test appear to "pass" by just waiting), then restored and the full suite reconfirmed green.
**Real-hardware evidence not yet gathered** — partway through this work, this machine's OBS WebSocket
server was found disabled via a read-only check of `global.ini` (`ServerEnabled=false`, port 4455, a
password already configured). `cargo build`/`npm run check`/`npm run build`/`npm run tauri build
--debug` all pass and the built `.app` launches and stays running — the outstanding step is enabling
OBS's WebSocket server (Tools → WebSocket Server Settings) and re-running `make test-obs`
(`docs/agent/VERIFICATION-MATRIX.md`'s existing check) followed by the built app itself, not further
engineering. **Explicitly out of scope, named not silently dropped:** a dedicated wrong-password/auth-
rejection test — none of the 8 contract tests need one, and the exact close-frame shape obs-websocket
uses on auth rejection wasn't verified against the spec, flagged rather than guessed;
`command-error`'s `ErrorCode` has no dedicated `Unauthorized` variant despite §7.1 listing one as
allowed — a pre-existing gap in the shared crate, not expanded here.

### WP-6 — Trust-boundary enforcement

Add core API authentication, WS handshake rules, relay tenant negative tests, size/rate limits, and route-ledger evidence.
**Exit:** every release-scope mutating route/command has an explicit tested decision.

**Done, 2026-09-02 (`P-053`).** Core API authentication was already done (`P-026`, `backend-api`).
WS handshake rules were already real code, just untested — and while adding that test coverage, a
real bug surfaced and got fixed: `/ws`'s route handler was missing its `WebSocket` type annotation,
so every connection died immediately after accept, before any handshake logic ever ran. Relay
tenant negative test: `tests/cloud_relay/test_tenant_isolation.py`, `pytest -m live`, proves
Postgres RLS actually blocks a cross-tenant read (not run in this sandbox — no Docker here; will
run for real on its first CI execution or on a machine with Docker). Size/rate limits: both added
(`GET /connections` also gained the admin-token auth it was missing entirely). Route-ledger
evidence: `docs/API_ROUTE_AUDIT_LEDGER.md`'s Cloud relay section now has a real per-row Auth
column, same shape Core backend's already had.

### WP-7 — Release and optional companion

Generate the clean-clone evidence bundle. Only after the local alpha passes, implement the disabled-default OpenTech companion proposal.
**Exit:** checklist signed, artifact tied to commit/tag, rollback exercised.

**Tooling slice built, 2026-10-12:** `scripts/testing/release_check.py` provides private
clean-checkout local evidence as described in §1. The reviewed CI plan is reused rather than
maintaining a second check list. `--python-only` is an explicit reduced scope; exit 0 does not
certify skipped native/Docker checks. Every report keeps public release disabled. This does not
implement a release/publish workflow or authorize Pending P-002 work. D-01/D-02, clean physical
hosts, actual tagged artifact provenance, legal/security/signing review and rollback remain open.

## 9. Scenario and pressure matrix

| ID | Scenario | Level | Expected result | Gate |
|---|---|---|---|---|
| GAP-HCP-01 | Empty/missing test directory | CI meta-test | Required job fails | P0 |
| GAP-HCP-02 | Weak production relay secret | Unit/Compose | Startup fails with remediation | P0 |
| GAP-HCP-03 | Wildcard credentialed CORS | Contract | Configuration rejected | P0 |
| GAP-HCP-04 | Cross-tenant relay resource request | Contract | `403`, no existence leak | P0 |
| GAP-HCP-05 | Both desktop UIs clean build | Build | Check and production build pass | P0 |
| GAP-HCP-06 | OBS absent then started | Scenario | Blocked, retry, ready; no app restart | P0 |
| GAP-HCP-07 | OBS scene switch timeout | Contract | No optimistic state; retryable error | P0 |
| GAP-HCP-08 | ComfyUI invalid workflow | Contract | Stable validation error; nothing queued | P0 |
| GAP-HCP-09 | ComfyUI job reaches terminal error | Scenario | UI shows failure/remediation, not success | P0 |
| GAP-HCP-10 | Relay/OpenTech offline | Scenario | Local OBS/ComfyUI journey remains usable | P0 |
| GAP-HCP-11 | Env variable added to Compose only | CI meta-test | Env-contract job fails | P0 |
| GAP-HCP-12 | 500 slow WebSocket consumers | Pressure | Bounded memory/backpressure policy | P1 |
| GAP-HCP-13 | Clean clone release check | Release | Reproducible evidence bundle | P0 |
| GAP-HCP-14 | Forbidden “Production” doc claim | Docs | CI reports file/claim without evidence | P1 |

## 10. Security, privacy, accessibility, and observability

- Preserve local media paths; tests use synthetic metadata/assets.
- Never log OBS passwords, API keys, workflow prompt contents, local paths, relay JWTs, or database URLs.
- Store desktop secrets using the approved credential-store mechanism rather than returning them via `get_config`.
- Setup/service status must use text and icon, keyboard-operable retry, visible focus, and screen-reader live updates.
- Add metrics for dependency-check duration/state, OBS reconnects, ComfyUI queue outcomes, API auth failures, relay cross-tenant denials, and WS disconnect/backpressure. Avoid tenant/private values in labels.

## 11. Rollout and rollback

1. Merge WP-1/2 behind no feature flag because they enforce truth and safe defaults.
2. Ship desktop build scaffolds internally.
3. Enable setup/OBS/ComfyUI paths with local feature flags: `HCP_SETUP_V1`, `STREAM_OBS_V1`, `CREATOR_COMFYUI_V1`.
4. Promote one path at a time after scenario evidence.
5. Keep relay commerce/invites/push disabled until their own provider tests pass.

Rollback disables the affected feature flag, preserves prior local config, and does not migrate/delete creator assets. Relay hardening must not be rolled back to weak defaults; emergency access uses an explicit operator-supplied secret/configuration.

## 12. Definition of done

- Every HCP gap row is Closed with an evidence link or explicitly Deferred outside the alpha claim.
- D-01 is resolved before public contribution/release.
- Required CI is green from a clean clone and no required job is advisory.
- The local alpha journey and its missing-dependency/recovery paths pass.
- Route/API ledger reflects tested auth and validation behavior.
- Relay production configuration fails closed and exposes no database/cache port by default.
- README, roadmap status, testing guide, environment reference, release notes, and checklist match the shipped evidence.

## 13. Documentation updates

> **Retargeted 2026-08-30 (see §3.1).** The numbered guide series is retired. Documentation tasks
> below that referenced `docs/guides/` now land in `modules/<name>/setup/{manual,automated}.md`,
> or in the config doc beside the config they describe. `docs/guides/README.md` is a redirect map
> only.

Update `docs/GAP_AUDIT.md` with owner/status/evidence columns during implementation; correct `README.md`, `TESTING.md`, `.env.example`, module READMEs, API ledger, setup guide, security policy, and release checklist in the same pull requests that change behavior.

### Final Testing handoff — 2026-10-12

Required `make test` reaches 100%, exit 0; final local CI-derived verification executes 30 checks
PASS and lists 17 installation/Docker/live commands NOT RUN, exit 0. The prepared security
interpreters keep relay/backend dependency pins separate. Separate real Postgres tests pass for
all six tenant tables and pool reuse; provider/database/fixture/deadline regressions are reverted
and reconfirmed failing. Local GUI access became available: the private preview opened and
passed the bounded native checks recorded under P-072. Actual OBS remains running/off-air with
WebSocket disabled on 4455 and authentication required, confirmed by flag-only config inspection.
No control listener, recording, broadcast, account action or deployed database was changed.

Test next: production password/volume upgrade and Docker execution, real OBS/ComfyUI output,
clean supported hosts, native credential/privacy/origin tests, hosted/two-device and outage/rollback
evidence. Root license, target support, legal/signing and tagged public delivery remain open.
