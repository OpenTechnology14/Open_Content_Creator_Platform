# Proposal dashboard and Testing workflow

> **Status:** Reference · **Last reviewed:** 2026-10-19 · **Owner:** OpenTechnology14

[Open the proposal dashboard](proposal-dashboard.html). It is a self-contained documentation
page and can be opened locally without either app or any provider account. The project picker
shows Hybrid Platform or MyFeed; this repository initially selects Hybrid Platform.

The [canonical proposal queue](PROPOSALS.md) owns IDs, states, assignments and authorization.
The dashboard is a dated view of those records, not a competing backlog. Its source snapshot
also reads MyFeed's own canonical queue; neither project imports the other's runtime or data.

Choose Testing, then All testing, Mainly acceptance or Remaining features. Select an ID to see
its recorded status, next step, implementation/proof limits, dependencies and agent assignment.
Prepare work request displays text to hand to an agent; it does not send a message, run a test,
start a game/account action, publish or spend on AI. Selection persists locally in the browser.

Testing means a working core or bounded build slice mainly needs acceptance or named leftover
work. Keep substantial new implementation in Build and conditional work behind its original
gates. Move an item back to Build when acceptance exposes substantial missing implementation.
Hybrid Testing rows retain In progress as their canonical state; completion still needs the
recorded verification bar. MyFeed's Work view remains independent of its local-delivery status.

## Sources and refresh

- [Dashboard source](assets/proposal-dashboard-source.html): editable exported visual fragment.
- [Snapshot receipt](proposal-dashboard-snapshot.json): source queue hashes, work counts and date.
- [P-071 tracker](proposals/PROPOSAL_DOCUMENT_GAPS.md#proposal-dashboard-tracking).
- `scripts/testing/proposal_report.py` derives Hybrid counts and checks the owner lane map.
- MyFeed's own queue, `docs/readable/PROPOSAL_WORK_QUEUE.md` (in the MyFeed repo; it does not exist here),
  owns each item's Work view and Next step.

This is a checked-in snapshot; opening the page does not fetch current queue data. After queue
changes, derive both work views from their canonical sources, reconcile every ID/count and
refresh the embedded source data, dated label and snapshot receipt in both repositories. Export
the source to `proposal-dashboard.html` with the Visualize renderer, preserving local-only state
and request preparation. Keep this guide and the dated tracker totals consistent. Automated
regeneration/freshness CI is a separate future build; the existing proposal report remains the
current command to check Hybrid queue/lane integrity.

Run `make proposal-report ARGS='--check --summary'`, generated-doc write/check, required
`make test`, local links/ID/count/receipt checks and `git diff --check`. Open the exported page
and check project selection, Testing filters, empty sections, selected details, work request,
reload persistence and narrow layout. None of these checks establishes live acceptance.

## Merge handoff

Include this guide, the exported page, its source/receipt, the docs-index/queue/tracker links,
and the generated documentation registry. Review the complete working tree before staging:
this checkout also contains independent platform work. This documentation handoff is not an
instruction to merge those unrelated changes or alter proposal states. The MyFeed counterpart
is `docs/readable/PROPOSAL_DASHBOARD.md` in the MyFeed repo (it does not exist here), with links from
its README and canonical queue.
