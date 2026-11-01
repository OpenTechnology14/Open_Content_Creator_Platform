# Pressure and Failure Test Plan

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a pressure-test plan, not a priority queue and not an authorization. A scenario that fails or has no measured number is a finding to route, not a task to start here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

The platform is latency-sensitive and local-first, so pressure testing must measure graceful degradation as well as throughput. Do not route realtime media through cloud load tests.

## Required scenarios

| Scenario | Load/failure | Pass condition |
|---|---|---|
| Setup fan-out | 25 readiness checks with 3 slow dependencies | UI remains responsive; each check times out independently; retry is targeted |
| OBS reconnect | Drop WebSocket during scene/status polling | Exponential reconnect; no false “streaming” state; user sees recovery |
| ComfyUI queue | Queue 100 metadata-only test jobs with bounded workers | Stable IDs, bounded memory, no duplicate completion |
| Overlay mutation | Concurrent PUT/GET/DELETE on the same name | Defined conflict result; no corrupt state |
| Event WebSocket | 500 synthetic clients, slow consumers included | Backpressure or disconnect policy prevents unbounded memory |
| Relay sync | Conflicting writes from two devices | Documented winner/version behavior and tenant isolation |
| Metrics ingestion | Oversized and burst payloads | Size/rate limit returns a stable error without process failure |
| Storage outage | MinIO/Postgres/Redis unavailable separately | `/ready` degrades accurately; local realtime path continues where designed |
| Disk pressure | Asset volume at 90% and full disk | Safe failure, no partial metadata claim, actionable alert |
| OpenTech handoff | Endpoint offline for one hour, then restored | Local bounded queue retries idempotently; no media/secrets leave device |
| Restart recovery | Kill backend/relay during an active non-media job | No phantom success; state reconciles after restart |
| Invalid configuration | Missing/weak production secret | Startup fails closed with a precise remediation message |

## Metrics

Record p50/p95/p99 latency, error rate, reconnect time, queue depth, dropped events, CPU/GPU/RAM, file descriptors, disk use, and recovery time. Define budgets per module before claiming a performance pass.

## Test data and safety

Use synthetic video metadata, generated assets under 5 MB, fake credentials, and isolated tenants. Never use a creator's recordings, model weights, production purchase data, or active stream keys.

## Release evidence

Archive the command, commit SHA, environment, fixtures, raw result, summarized result, and known deviations. A screenshot alone is not pressure-test evidence.
