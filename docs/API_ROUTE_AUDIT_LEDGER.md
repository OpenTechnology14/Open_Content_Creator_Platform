# API and Command Audit Ledger

> **Status:** Living · **Last reviewed:** 2026-10-19 · **Owner:** OpenTechnology14

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a route and command inventory, not a priority queue and not an authorization. A route that fails its checks, or a missing check, is a finding to route, not a task to start here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

This is the baseline inventory for authorization, validation, observability, and contract testing. Dynamic paths are shown literally.

## Core backend

**Trust-boundary decision recorded 2026-09-02** (`P-046` doc sweep, reading `main.py` and each
router's actual `Depends` wiring directly, not assumed): every mutating route requires
`X-API-Key`, compared with `hmac.compare_digest` (not `!=`, which leaks match-length via timing —
fixed in `P-026`); every read route is deliberately public, unauthenticated by design (so an
overlay browser source or a dashboard can poll without holding a key); `/ws` requires the same key
via header or a `?api_key=` query param (browsers can't set custom WS headers) and closes
unauthorized connections with code `1008` before `accept()`. Full router mount table:
`tests/backend_api/test_routes.py`. **Two routes this table never listed at all:** `POST /streams`
(start a stream) and `POST /events` (publish an event) — both added below. 12 routes total, not 10.

**How auth is tested:** every `AuthDep`-protected route shares one dependency function
(`require_api_key`), so `test_require_api_key_accepts_and_rejects` and
`test_require_api_key_uses_constant_time_comparison` cover all of them functionally by testing that
one function directly (missing key, wrong key, `hmac.compare_digest` actually wired in via source
inspection) rather than via a separate HTTP call per route. `test_documented_routes_exist` confirms
every path below is actually served. `/ws`'s auth is tested via real HTTP/WS calls
(`test_ws_rejects_missing_api_key`, `test_ws_rejects_wrong_api_key`) since it's a distinct
dependency (`WsAuthDep`).

| Method | Path (with router prefix) | Purpose | Auth |
|---|---|---|---|
| POST | `/streams` | Start a stream | **Required** (`AuthDep`) |
| POST | `/streams/{stream_id}/stop` | Stop stream | **Required** (`AuthDep`) |
| GET | `/overlays/{name}` | Read overlay | **Public, by design** — no key |
| PUT | `/overlays/{name}` | Update overlay | **Required** (`AuthDep`) |
| DELETE | `/overlays/{name}` | Delete overlay | **Required** (`AuthDep`) |
| POST | `/events` | Publish an event | **Required** (`AuthDep`) |
| GET | `/events/recent` | Recent events | **Required** (`AuthDep`) |
| POST | `/automation/trigger` | Trigger automation | **Required** (`AuthDep`) |
| GET | `/automation/status` | Automation status | **Required** (`AuthDep`) |
| GET | `/health` | Liveness | **Public, by design** — no key |
| GET | `/ready` | Readiness | **Public, by design** — no key |
| WS | `/ws` | Realtime events | **Required** (`WsAuthDep`, header or `?api_key=`) |

**Not in this table on purpose:** `GET /metrics`, added by `prometheus_fastapi_instrumentator`
(`main.py`), no auth — it's the Prometheus scrape target `prometheus.yml`'s `fastapi` job polls, an
observability endpoint rather than a hand-written command route, same category as `/health`/`/ready`.

**Still open, not audited by this pass:** rate/size limits and structured request-logging on the
authenticated routes above are not implemented or tested — this ledger's own "Definition of
audited" below requires them, so none of these rows are fully closed, only the authentication
column. Idempotency on `POST /events`/`POST /automation/trigger` (`HCP-001`'s original ask for
this route) is also unverified.

## Cloud relay

**Trust-boundary decision recorded 2026-09-02** (`P-053`, `P-001` WP-6, reading every router's
actual `Depends` wiring and `handle_websocket`'s in-band auth directly, not assumed). Most of this
was already real, correctly-enforced code before this pass — JWT verification via
`Depends(get_current_tenant)`/`require_connect`/`require_pro`/`require_team`, real Postgres RLS
tenant isolation, a real 4-path WS handshake (missing Auth key / invalid JWT / malformed JSON /
10s timeout, each closing with an `AuthError`). Two real gaps found and fixed: `GET /connections`
had **no** auth dependency at all despite its own "Admin" docstring (fixed — `require_admin_token`,
unset `RELAY_ADMIN_TOKEN` means the route stays unreachable, fail-closed by default); and
`api_rate_limit_per_minute` was declared but never enforced anywhere (fixed — an in-memory
per-tenant token bucket wired into `get_current_tenant` itself, so every tier-gated dependency
built on it inherits the check for free). Request body size limits added too: a global
`Content-Length` check (`BodySizeLimitMiddleware`) plus per-field `Field(max_length=...)`/dict-size
constraints on `sync.py`/`metrics.py`/`notifications.py`'s free-form payloads. **A third, more
severe bug found while writing the WS handshake tests, unrelated to auth:** `main.py`'s `/ws` route
handler had no `websocket: WebSocket` type annotation — FastAPI's routing (unlike bare Starlette)
needs it, and without it every real connection closed immediately after `accept()`, before
`handle_websocket`'s own body ever ran. The relay's own module docstring calls this endpoint "the
core of the cloud service"; nothing had ever tested it. Fixed; verified live both ways (pre-fix
reproduction via `git stash`, post-fix all 4 failure paths + the success path exercised for real).

**How auth is tested:** `tests/cloud_relay/test_auth.py` — `create_token`/`decode_token` round-trip
and rejection cases, `require_admin_token`/`check_rate_limit` accept/reject (including the same
`hmac.compare_digest`-in-source regression check `test_routes.py` uses for backend-api).
`tests/cloud_relay/test_ws_auth.py` — all 4 real handshake failure paths plus the success path,
via `TestClient(app)` without the lifespan-triggering `with` form (same trick `test_routes.py`
uses, since `handle_websocket`'s failure paths never touch the DB). `tests/cloud_relay/
test_tenant_isolation.py` — `pytest -m live`, needs real Postgres: inserts a row as tenant A,
proves tenant B's `TenantConnection` genuinely cannot read it (RLS enforcement, not just intent).

| Area | Routes | Auth |
|---|---|---|
| WebSocket | `WS /ws` | **Required** — in-band JWT in the first message (`Auth`/`auth` key), 4 real failure paths, 10s timeout |
| Auth | `POST /verify-purchase` | **Public, by design** — issues the first token |
| Auth | `POST /subscribe`, `/refresh`, `/self-hosted-key` | **Required** (`Depends(get_current_tenant)`) |
| Health | `GET /api/v1/health`, `/api/v1/health/db` | **Public, by design** — health check |
| Metrics | `POST /push`, `/query`; `GET /names` | **Required** (`Depends(require_pro)`) |
| Notifications | `POST /send`, `/register-device` | **Required** (`Depends(require_connect)`) |
| Relay | `GET /connections` | **Required** (`require_admin_token`, `RELAY_ADMIN_TOKEN`, `hmac.compare_digest`) — was unauthenticated before `P-053` |
| Sync | `GET/PUT /{key:path}`, `GET /` | **Required** (`Depends(require_pro)`) |
| Tenants | `GET /me`, `/me/devices`, `/me/usage` | **Required** (`Depends(get_current_tenant)`) |
| Tenants | `POST /me/team/invite` | **Required** (`Depends(require_team)`) |

**Still open, explicitly not attempted here, named not silently dropped:** `POST
/self-hosted-key`'s issued key is never persisted (`# TODO: Store in database associated with
tenant`) and nothing anywhere verifies an `shk_...` key against anything — a missing *feature* (a
real API-key system), not a missing *decision* on an existing enforced route. `ws_max_connections_
per_tenant` and the new rate limiter are both per-process only, not shared across horizontally-
scaled relay instances via Redis, despite `main.py`'s own docstring describing horizontal scaling
as supported — a bigger, separate feature.

## Stream Extend Tauri commands

**Relay critical refresh, 2026-10-12 (P-001):** purchase verification, subscription upgrades,
self-hosted key issuance, push send/registration and team invitations now return
`501 feature_not_available` before token/database/provider effects. Authenticated refresh preserves
the existing tier and tenant. This supersedes older descriptions of issued-but-unpersisted keys or
provider success. Real Postgres tests cover all six tenant tables, pooled context reset and unsafe
role startup rejection. The API uses the non-superuser `relay_app` role; bootstrap/table-owner
connections are rejected. Dedicated relay/backend security CI rejects skipped selected tests.

**Private P-072 preview IPC:** `apps/extend` registers preferences/OS-vault save, read-only
readiness/catalog and recording list/import/reveal/ready/archive operations. Disabled packs are
checked in native handlers. Editing/published statuses are denied. There are no broadcast,
render, remote, OAuth or publishing commands/grants; origin/CSP enforcement remains native
acceptance. Shared setup/profile namespaces retain their own validation and selected grants.

P-066 adds `voice_studio_request(request)`: native-only, fixed bundled stdio worker with a 64 KiB
request limit, strict Pydantic action/field validation and a 16 MiB response bound. No shell,
caller-selected executable or public listener. Owns local draft/render/review/selection and manual
script/Q&A commands. `audio` requires connected off-air OBS plus explicit isolated monitoring;
rendering never plays. Approval hashes exact prompt/audio and activation separately requires manual
OBS binding acceptance. See [voice studio](../modules/automation-control/voice_studio/README.md)
and `tests/automation_control/test_voice_studio.py`; real OBS/Windows acceptance remains open.

`get_config`, `set_config`, `remote_get_settings`, `remote_save_settings`, `remote_connect`,
`remote_disconnect`, `remote_status`, `remote_request`, `remote_approve`, `remote_deny`, `obs_status`,
`obs_scenes`, `obs_switch_scene`, `obs_stream_status`, `obs_toggle_stream`,
`obs_start_stream_session`, `obs_stop_stream_session`.

Configuration writes redact secrets and reject unsafe URLs. Relay tokens stay in the OS credential
manager. Remote requests are allowlisted, size-limited, targeted by device ID, correlated by request
ID, and require approval on the target workstation. Stream-changing commands return OBS's observed
result and report dependency failure without exposing its local details to the sending device.
The managed session validates profile IDs, records before streaming, rolls its recording back on a
failed stream start, and stops/registers only a recording it can prove it started in the current
process. The returned OBS path is accepted only as a canonical, non-empty video file.

## Creator Extend Tauri commands

`get_config`, `set_config`, `remote_get_settings`, `remote_save_settings`, `remote_connect`,
`remote_disconnect`, `remote_status`, `remote_request`, `remote_approve`, `remote_deny`,
`comfyui_status`, `comfyui_workflows`, `comfyui_load_workflow`, `comfyui_workflow_inputs`,
`comfyui_upload_target`, `comfyui_queue_configured`, `comfyui_upload_image`, `comfyui_queue`,
`comfyui_prompt_status`, `recordings_list`, `recordings_import`, `recordings_update`,
`recordings_reveal`, `blender_open`, `krita_open`, `krita_run_script`, `posture_analyze`.

Executable/script paths require allow-listing or explicit local trust documentation. Remote queue
requests accept only a committed workflow path, wait for local approval, and return the real prompt
ID; workflow input editing remains a local command path.
Recording import accepts only canonical non-empty video files; update/reveal use a validated record
ID from the private ledger. Reveal passes the registered path as a direct process argument rather
than shell text. Cross-process writes are locked and atomic; media is never copied by these commands.

## Shared Social Manager Tauri commands

`snapshot`, `selection`, `activate_profile`, `save_selection`, `start`, `status`, `authorize`,
`connections`, `disconnect`.

Profile selection is validated against the compiled catalog and persists only public IDs. OAuth
authorization URLs must match the catalog provider endpoint. Connected-account reads are redacted;
disconnect validates the connection ID and asks the fixed loopback service to delete both the
OS-vault credential and public record. No arbitrary URL, port, process, path, or token is accepted
from the webview.

## Definition of audited

A route or command is audited only when its trust boundary, request/response schema, errors, timeouts, authorization, sensitive-data behavior, rate/size limits, logs/metrics, and automated tests are recorded.
