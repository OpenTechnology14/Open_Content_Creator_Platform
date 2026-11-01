# Pre-merge review

Read AGENTS.md, the proposal queue and the owning proposal. This command reports readiness;
it does not merge, delete a branch or change a PR without task authorization.

1. Inspect status, current branch, base and changed paths. Preserve unrelated work.
2. Inspect attached/open PRs and Git worktrees. Check whether the current base is stacked
   and whether deleting an ancestor branch would close or orphan a child PR. Name the child
   PRs that need retargeting before ancestor cleanup.
3. Inspect proposal IDs in local changes and open PRs; record duplicate claims or overlapping
   work rather than overwriting them. Run `make proposal-report ARGS='--check --summary'`.
4. Run `make verify` and appropriate live/manual checks from the verification matrix.
   Report every NOT RUN item and any unmet release gate. Inspect current CI separately.
5. Confirm the queue row, detailed model assignment, lane decisions, documentation index and
   verification record agree. Run `git diff --check`.
6. Record a bounded entry in docs/AUDIT_LOG.md as described by audit.md, and return the
   concrete blocking findings and ready-to-review artifact. Green local checks alone do not
   authorize public release, creative approval or external publishing.
