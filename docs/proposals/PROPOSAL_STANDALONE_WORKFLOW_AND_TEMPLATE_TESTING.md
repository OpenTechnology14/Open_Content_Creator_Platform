# Proposal: Standalone Workflow and OpenTech Template Testing

**Queue row:** `P-005`
**Agent model / effort:** `gpt-6.1-sol` / `medium` — Scoped journey and companion test design
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — operational scenario design completed; connected/mobile/live acceptance remains dependent on its owning implementation.
**Date:** 2026-08-12
**Owner:** —
**Roadmap layer(s):** Cross-cutting; Creator Experience; Automation/Control
**Evidence level:** Verified against current repo state; test scenarios not yet written

## Purpose

This document owns operational workflow and acceptance-scenario design for the standalone
apps and the planned OpenTech `extend_platform` connection. The dated matrix records what
already has executable proof and what remains blocked. Connected/mobile acceptance is not
implied by the standalone results.

This is deliberately narrower than [`PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md`](PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md), which owns the integration *architecture* (setup/status contract, privacy boundary, sanitized handoff). This doc owns the *operational workflow* — how you actually run Stream Extend / Creator Extend, standalone and connected — and the test scenarios that prove it works. Per [`REPOSITORY_ALIGNMENT.md`](../REPOSITORY_ALIGNMENT.md), this repo (`Open_Content_Creator_Platform`) is the canonical combined workspace; `ContentExtend`/`StreamExtend` are downstream standalone exports, not where this doc's workflow lives.

## 1. Standalone workflow (no OpenTech involved)

Per `README.md` and `CLAUDE.md` §3–4 (Repository Layout, Roadmap → Module Mapping):

1. **Setup:** local dev via `docker-compose.yml` (or `docker-compose.digitalocean.yml` for the hosted profile), configuration in `configs/` per environment — not hardcoded or branched in module code.
2. **Stream Extend** (`apps/stream-extend`): OBS scene/stream control, broadcast graphics.
3. **Creator Extend** (`apps/creator-extend`, aliased legacy name for ContentExtend per `REPOSITORY_ALIGNMENT.md`): ComfyUI, Blender, Krita orchestration for content creation.
4. **Shared** (`apps/shared`): the setup/readiness engine and relay client/protocol both apps depend on — canonical here, versioned/exported to the standalone product repos.
5. **Planned unified control:** combined desktop and mobile scope belongs to P-072; parity is not currently proven.
6. **Local-first boundary:** realtime webcam/OBS traffic never routes through the cloud (`CLAUDE.md` §10); no service is exposed to the public internet without an auth layer.

## 2. Connected workflow (via the OpenTech `extend_platform` template)

Per [`PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md`](PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md)'s design (architecture, not yet built): an app requests setup status on launch and renders required/optional checks; failures block the corresponding action with a copyable fix. If OpenTech integration is enabled, only check ID, state, safe reason code, platform version, and timestamp cross the wire — never media, secrets, model inputs, or filesystem paths, and never through the realtime path. A bounded local queue retries idempotently if OpenTech is unreachable; disabling integration deletes the unsent queue.

On the OpenTech side, the counterpart is the `extend_platform` built-in project template (`src/lib/templates.ts` in `Task-Management`), currently tracked at `CONTENT-04` in that repo's `PRIORITY.md` — a stub walkthrough doc lives at `Task-Management/docs/runbooks/PROJECT_TEMPLATE_TESTING.md#automation-kb--extend-platform-extend_platform`, to be filled in from both sides together.

## 3. Standalone and connected acceptance scenarios

### Executable references and acceptance design — 2026-10-09

The former scaffold now has concrete inputs, outcomes and evidence boundaries. Recorded
contract or backend proof does not close physical capture/account/mobile acceptance.

| ID | Input / operation | Success and recovery expectation | Current proof / dependency |
|---|---|---|---|
| SW-01 | Supported OS, selected capabilities, missing optional tool | Required action is blocked with remediation; unrelated local work remains usable | Shared setup/readiness contracts; physical clean-host acceptance stays P-003/P-063 |
| SW-02 | Owned OBS session, scene switch, failed stream start | Observe scene state; owned recording starts first and rolls back on failed stream start | Stream fake-OBS contracts; actual picture/audio/profile acceptance stays P-055/P-065 |
| SW-03 | Committed ComfyUI graph, bounded source input, missing model | Preflight names the missing resource; successful history resolves verified output | Creator ComfyUI/workflow-input contracts; real target-model/device acceptance stays P-057/P-028 |
| SW-04 | Saved Blender project, explicit scenes, per-scene failure | Unique attempt, retained successful PNG, owned cancellation and guarded retry | P-061 worker/native contracts and real two-scene smoke; GUI/physical acceptance remains open |
| SW-05 | Backend stream/event plus object round trip | Read back the event/object, then stop the stream and observe the metric | P-016 live creator journey passed in CI 37876242044 and 37881497742 |
| SW-06 | MinIO absent during generation | Local generation/output remains independent of upload | P-004 local graph acceptance not yet complete; do not infer from SW-05 |
| CW-01 | Explicit consent plus configured OpenTech target | Only approved check IDs/states/reason codes/version/timestamps cross the boundary | P-002 adapter/target contract not implemented; no traffic proof claimed |
| CW-02 | OpenTech outage and replay | Bounded retry and one logical update; local service remains usable | Blocked by P-002 implementation and selected target identifiers |
| CW-03 | Disable integration while events queued | Stop new sends and remove unsent metadata without touching media/local state | Blocked by P-002 implementation |
| CW-04 | Inject token/path/hostname/media into candidate event | Reject/drop forbidden fields and verify sanitized wire/log output | P-002 privacy contract; executable adapter acceptance remains open |
| MW-01 | Mobile request against known desktop action | Denial/expiry/approval enforced; no automatic parity claim | P-058/P-072 two-device and companion scope; mobile parity is planned |

Run sequence: selected setup → standalone contract checks → owned private native drill →
reviewed connected target → outage/privacy replay → mobile approval test. An absent companion
is not a failure of the local creator path. No test here authorizes external publishing or
live broadcasting; operator sign-in and exact action approval remain separate.

The checklists below remain live acceptance work. Record observed results and dates against
the matrix above; a written scenario alone does not close its gate.

### Standalone only

- [ ] Fresh setup on a clean machine via `docker-compose.yml`; readiness checks all pass or give a copyable fix.
- [ ] Stream Extend: OBS scene switch and stream start/stop from the dashboard.
- [ ] Creator Extend: a ComfyUI/Blender/Krita job runs end to end from the dashboard.
- [ ] Mobile control surface reaches parity with desktop for the core actions above.

### Via the OpenTech connection (once the companion contract from `PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md` exists)

- [ ] Setup/status checks surface in the OpenTech `extend_platform` template.
- [ ] A required-check failure blocks the corresponding service action in the app itself, not just in OpenTech.
- [ ] No media, secret, model input, or filesystem path ever appears in an OpenTech request/response — spot check real traffic, not just the code path.
- [ ] Outage: OpenTech unreachable — local queue retries idempotently, creator service stays usable throughout.
- [ ] Disabling integration clears the unsent queue and stops new handoffs without touching local app state.

## 4. How to keep this doc alive

- When you build a piece of the connection, move its scenario from "stub" to a real pass/fail with a date and what you actually did.
- When the standalone workflow changes (new module, new dashboard feature), update §1 first — this doc should always describe what's actually running, not what's planned.
- Cross-link new findings back into `PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md` if they change the architecture, not just this doc.
