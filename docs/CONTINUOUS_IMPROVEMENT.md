# Continuous Improvement

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a recurring audit cadence, not a priority queue and not an authorization. A finding from a cadence run is routed, not started here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

## Cadence

- **Every pull request:** lint, unit/contract tests, secret scan, documentation-link check, changed-route ledger review.
- **Weekly:** scenario suite, dependency review, flaky-test and TODO inventory.
- **Monthly:** setup matrix on supported operating systems, backup/restore exercise, route/auth review.
- **Before each release:** clean-clone build, pressure tests for changed services, license/SBOM review, rollback rehearsal.
- **Quarterly:** threat model, roadmap/status reconciliation, public claims review, dependency/license audit.

## Tracked indicators

| Indicator | Initial target |
|---|---|
| Enforced CI jobs | 100% required jobs fail closed |
| Critical user journeys with success + recovery scenarios | 100% of release scope |
| Routes with explicit trust-boundary decision | 100% |
| Setup checks with structured remediation | 100% of required checks |
| Documentation claims linked to evidence | 100% of “implemented/production” claims |
| Known default credentials in production configs | 0 |
| Mean recovery time for local dependencies | Baseline, then reduce each release |

## Feedback loop

Every escaped defect creates: a regression test, a gap-ledger entry if systemic, a documentation correction if expectations were wrong, and an owner/date. Close items only with linked evidence; moving text into a “future” document is not closure.
