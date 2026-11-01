# Audit — quick, standard or deep

Read AGENTS.md, docs/PROPOSALS.md and the owning proposal before interpreting scope.
Arguments: tier `quick` (default), `standard` or `deep`, followed by an optional path/proposal.
Audit code read-only. Log findings without changing code or performing account actions.

For every tier:

1. Run `make verify`; retain the complete PASS/FAIL/NOT RUN summary and exit code.
   Missing prerequisites are coverage gaps. Do not describe a partial local run as green CI.
2. Run `make proposal-report ARGS='--check --summary'`; inspect unfinished model assignments
   and lane discrepancies. Read both lanes' Next three and the platform decisions.
3. Read current main CI with `gh run list --branch main --workflow ci.yml --limit 3` if
   available. Report unavailable access rather than guessing from historical run notes.

For `standard`, also run the marketing CLI validate/selftest and read AUDIT.md, FUTURE_DOCS.md,
architecture/future.md and future-state.md. Check counts and product claims against canonical
module status/evidence; mark overclaims as high credibility findings. Check queue state versus
lane text, not just whether a proposal ID is present.

For `deep`, add a diff review of native commands, credentials, social actions, relay trust,
path/process boundaries, session ownership and cancellation. Select relevant verification-matrix
checks. Clearly distinguish source inspection from actual hardware/account acceptance.

Append one dated entry to docs/AUDIT_LOG.md using apply_patch; retain the latest ten entries.
Each entry has at most 15 current-state lines and three future-state lines. Include scope,
source revision, commands/results, unrun checks, highest-priority fixable finding and
highest-leverage future-state move. Include no secrets, private identifiers or raw stack traces.
Return findings and evidence paths. Do not silently fix a defect as part of an audit.
