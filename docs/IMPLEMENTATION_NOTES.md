# Implementation Notes

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a record of decisions and verification, not a priority queue and not an authorization. A decision that needs work is routed, not started here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

## 2026-07-12 documentation and readiness audit

- Preserved `docs/architecture/roadmap.md` as the canonical ordering source.
- Added an OpenTech-style audit package without upgrading any module from Scaffolded.
- Kept setup readiness as a pre-service gate: service actions should be unavailable until required checks pass, while optional checks may degrade visibly.
- Chose a shared setup contract for both desktop apps rather than duplicating platform detection and status logic.
- Proposed OpenTech integration as an opt-in metadata handoff. Realtime video/audio, local paths, credentials, model inputs, and private assets remain local.

## Constraints discovered

- Docker and Cargo were unavailable during the audit, so Compose and Tauri builds remain unverified.
- This checkout did not expose Git history, so historical secret scanning and provenance checks remain unverified.
- The present CI configuration is not a release gate because lint failures are ignored and tests are placeholders.

## Implementation guardrails

1. Keep setup detection read-only; require explicit confirmation before install or configuration mutation.
2. Return structured check IDs and machine-readable remediation actions; do not parse human messages in the UI.
3. Use bounded timeouts and never make cloud connectivity a requirement for local capture or realtime inference.
4. Record idempotency keys for OpenTech events and strip local filesystem paths.
5. Refuse production startup when secrets equal examples/defaults.

## Decision log format

Future entries should include date, decision, affected files, alternatives, reason, verification, rollback, and unresolved risk.
