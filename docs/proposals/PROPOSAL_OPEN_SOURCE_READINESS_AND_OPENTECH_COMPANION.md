# Proposal: Open-Source Readiness and OpenTech Companion

**Queue row:** `P-002`
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — Release and companion boundaries across repositories
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Draft
**Date:** 2026-07-12
**Roadmap layers:** Cross-cutting release engineering; Backend/API; Creator Experience; Automation/Control
**Evidence:** Current gaps verified; implementation proposed

## 1. Executive summary

Publish a truthful, buildable local-first alpha and add an optional OpenTech companion template that receives sanitized setup/service status. The companion is not in the realtime path and cannot receive media, secrets, model inputs, or local filesystem paths.

## 2. Verified current state

### Owner refresh — 2026-10-05

The owner wants eventual open-source distribution. The root license remains absent and the
repository private (GitHub metadata checked). JobHunter is public with an MIT license;
OpenTechnologyApp's marketing describes paid source access, a different distribution policy.
P-001 owns release engineering; this proposal retains the license/distribution decision and
optional companion boundary. The new [reference review](../PUBLIC_DOCS_AND_MARKETING_REVIEW.md)
and public-docs source implement the separately authorized P-071/P-070 documentation follow-up.
They do not approve the companion adapter or public release. Below is historical evidence,
not a current comprehensive audit; consult `docs/AUDIT.md` for present capability evidence.

### Historical audit and corrections

- The roadmap and module scaffolds are extensive, but `tests/` has no automated suite and CI does not enforce tests or lint.
- Stream Extend and Creator Extend are not yet proven production builds; core OBS/workflow paths include placeholders.
- A detailed setup-readiness proposal exists, but there is no implemented shared endpoint for the desktop apps.
- The relay includes production-unsafe fallbacks and broad network exposure.
- No root license/governance package establishes a public contribution contract.
- OpenTech is not connected from this repository.

**Correction, 2026-09-02 (exhaustive `docs/` sweep, `P-048`), two bullets above no longer hold as
written — this file predates ~20 proposals of engineering and has never been re-verified since
2026-07-12, unlike `PROPOSAL_RELEASE_GAP_CLOSURE.md`'s (`P-001`) equivalent section:**
- The first bullet is false: the offline suite has 900+ cases, CI-enforced and unconditional
  (`P-024` onward). Lint remains advisory (`\|\| true`), so that half still holds.
- The governance half of the fifth bullet is false: `CONTRIBUTING.md`/`SECURITY.md`/
  `CODE_OF_CONDUCT.md` all exist at root with real content. No root `LICENSE` still exists — that
  half still holds, and remains the actual blocker (`D-01`).
- Everything else above (desktop-app placeholders, no shared setup endpoint, relay's unsafe
  defaults, OpenTech not connected) was re-checked directly and still holds unchanged.

## 3. Goals and non-goals

### Goals

- Establish a reproducible, secure, clearly labeled alpha release.
- Implement a shared setup/status contract used before service actions.
- Provide an importable OpenTech project template and opt-in, idempotent status handoff.
- Add scenarios that prove success, blocking, retry, recovery, and privacy behavior.

### Non-goals

- Sending realtime audio/video through OpenTech or the cloud.
- Claiming all roadmap modules are implemented.
- Adding Kubernetes or a distributed media plane.
- Selecting a license without maintainer/legal approval.

## 4. User paths

1. On first launch, an app requests setup status and renders required/optional checks.
2. Required failures block the corresponding service action and show a copyable command or deep link; mutations require confirmation.
3. After retry succeeds, the app enables the service without restart where possible.
4. If OpenTech integration is enabled, the backend sends only check ID, state, safe reason code, platform version, and timestamps.
5. If OpenTech is unavailable, a bounded local queue retries with the same idempotency key; the creator service remains usable.
6. Disabling integration deletes unsent events and stops new handoffs.

## 5. Architecture and data flow

```text
Stream Extend / Creator Extend
            |
            v
 local Backend Setup API ---- local dependency probes
            |
     opt-in metadata only
            v
 OpenTech ingest endpoint -> Companion project status/tasks
```

The adapter allow-list serializes known fields. Unknown fields are dropped. Logs redact tokens and never serialize environment values.

## 6. Direct injection map

| Location | Symbol/surface | Proposed change | Example | Verification |
|---|---|---|---|---|
| `modules/backend-api` setup router | `GET /api/v1/setup/status` | Return versioned aggregate and checks | response below | Contract, timeout, partial failure |
| `modules/backend-api` setup router | `POST /api/v1/setup/checks/{id}/run` | Rerun one read-only check | `202` with operation ID | Invalid ID, concurrent retry |
| `apps/stream-extend/src/routes/setup/+page.svelte` | Setup gate | Render OBS/relay checks before stream actions | “OBS WebSocket is unreachable” | Component + keyboard tests |
| `apps/creator-extend/src/routes/setup/+page.svelte` | Setup gate | Render ComfyUI/Blender/Krita/storage checks | optional tools degrade | Component tests |
| `modules/backend-api` integration adapter | `OpenTechStatusSink` | Allow-list, queue, retry, idempotency | event below | Offline/replay/privacy tests |
| `.env.example` | OpenTech variables | Document endpoint, project/queue ID, token reference, disabled default | `OPENTECH_ENABLED=false` | Config validation |
| OpenTech template repository | `templates/hybrid-creator-platform/template.json` | Add phases, setup blockers, service readiness, release checklist | importable template | Template schema/import test |
| `.github/workflows/ci.yml` | required jobs | Enforce lint/tests/build/docs/security | no ignored failures | Deliberate failure tests |

## 7. Contracts and examples

### Setup status

```json
{
  "schema_version": "1.0",
  "overall": "blocked",
  "checked_at": "2026-07-12T18:00:00Z",
  "checks": [
    {
      "id": "obs.websocket",
      "scope": "stream",
      "required": true,
      "state": "failed",
      "reason_code": "connection_refused",
      "message": "OBS WebSocket is not reachable.",
      "remediation": {"kind": "docs", "label": "Open setup steps", "target": "/guides/obs"}
    }
  ]
}
```

### Sanitized OpenTech event

```json
{
  "event_id": "01J...",
  "idempotency_key": "setup:device-hash:obs.websocket:failed:2026-07-12T18",
  "source": "hybrid-creator-platform",
  "type": "setup.check.changed",
  "data": {
    "check_id": "obs.websocket",
    "scope": "stream",
    "state": "failed",
    "reason_code": "connection_refused",
    "platform_version": "0.x"
  }
}
```

Forbidden fields include environment contents, access tokens, stream keys, local paths, hostnames/IP addresses, media, prompts, recordings, and model inputs.

## 8. Security, privacy, accessibility, observability

- Keep integration disabled by default and require explicit consent with a field-level disclosure.
- Store tokens in the OS credential store or secret reference, never plain config returned to the UI.
- Bind local setup endpoints to the documented local trust boundary; mutating checks require anti-CSRF/origin protection if browser-accessible.
- Provide text plus icon/status, focus management after retry, keyboard actions, and live-region updates.
- Emit check duration/state metrics and adapter queue/retry/drop metrics without private labels.

## 9. Scenario and pressure matrix

| ID | Scenario | Expected result | Gate |
|---|---|---|---|
| OSR-01 | Clean clone on supported OS | Documented alpha path builds | P0 |
| OSR-02 | OBS absent | Stream action blocked with remediation | P0 |
| OSR-03 | ComfyUI optional and absent | Creator UI remains usable with degraded label | P0 |
| OSR-04 | Dependency becomes healthy | Targeted retry enables service | P0 |
| OSR-05 | OpenTech disabled | No outbound request or queued event | P0 |
| OSR-06 | OpenTech offline | Bounded retry; local service unaffected | P1 |
| OSR-07 | Event replay | One logical OpenTech update | P1 |
| OSR-08 | Forbidden field injected | Adapter drops/rejects field and redacts logs | P0 |
| OSR-09 | Weak production secret | Startup fails closed | P0 |
| OSR-10 | Slow readiness checks | Independent timeout; responsive UI | P1 |

## 10. Delivery plan

1. **Truth and safety:** select license, add governance, correct README, sync env contract, harden relay.
2. **Executable alpha:** complete one Stream/Creator path, enforce CI, add scenario harness.
3. **Setup contract:** implement read-only status and targeted rerun; connect both UIs.
4. **OpenTech companion:** create template and opt-in adapter behind a feature flag.
5. **Release proof:** clean-clone matrix, pressure tests, SBOM/checksums, known limitations.

## 11. Rollout and rollback

Ship setup status first with OpenTech disabled. Enable the adapter only for test projects, then opt-in alpha users. Roll back by disabling `OPENTECH_ENABLED`, draining/deleting unsent sanitized events, and retaining the local setup API. No database migration should be required for disabling the integration.

## 12. Risks and unresolved decisions

| Item | Owner/decision |
|---|---|
| Root license and accuracy of “open source” wording **Question:** Confirm MIT as the repository's root license? | Maintainer/legal before public release |
| Local API authentication model | Backend/security design before implementation |
| OpenTech queue/project identifiers and template schema **Question:** Will you provide the OpenTech queue and project identifiers and the template schema? | OpenTech template owner |
| Supported OS matrix for alpha **Question:** Make macOS and Ubuntu the supported operating systems for the alpha? | Release owner |
| Retention limit for unsent integration events **Question:** Will you set a retention limit for unsent integration events? | Privacy/product owner |

## 13. Documentation updates

Update the root README, testing guide, environment reference, setup guide, privacy/data-flow guide, API ledger, release notes, and OpenTech template documentation in the same changes that implement each phase.
