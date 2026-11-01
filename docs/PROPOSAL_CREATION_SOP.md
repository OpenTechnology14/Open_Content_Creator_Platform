# Proposal Creation SOP

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**Enforcement: required.** A proposal that does not meet this bar is not ready for acceptance.

This doc owns **form and evidence** — what a proposal must contain to be reviewable.
[`PROPOSALS.md`](PROPOSALS.md) owns **state** — whether it is authorized and what is happening to
it. A proposal document that no queue row points at is not queued work, however well argued.

A proposal is an implementation contract, not an idea list. It must let a reviewer identify exactly what changes, where it changes, how each path behaves, and how the result is proven.

## Required process

1. Verify the current repository state. Cite files, routes, commands, tests, and observed limitations, and record the commit or
   branch and the date you verified against in the header's **Verified against** field.
2. **Set the best available model for the proposal work.** Record its exact agent model ID,
   reasoning effort and scope-based rationale in the queue's **Agent model / effort** column and
   the detailed proposal header. Follow [the model selection policy](PROPOSALS.md#agent-model-selection),
   confirm availability and select it in the execution client before starting. Reassess when scope
   changes; record replacements rather than silently inheriting a default. Child tasks inherit the
   parent assignment unless an explicit override is recorded. Keep runtime model choices separate.
3. State the user problem and explicit non-goals.
4. Define actors, trust boundaries, local/cloud data flow, and failure states.
5. Provide exact injection locations: file path, symbol/route/component, before/after behavior, and representative code or payload.
   Name the files a reader would expect to change that are **intentionally unchanged**, with the reason.
6. Trace every user path: first run, normal success, missing dependency, invalid input, offline/degraded mode, retry, cancellation, and recovery.
7. Specify API/schema changes, compatibility/versioning, migrations, telemetry, and privacy.
8. Define automated scenarios and pressure tests before implementation.
9. Provide phases, dependencies, release gates, rollout, rollback, and unresolved decisions, and name the **first implementation
   slice**: the smallest change that can merge on its own.
10. **Name the local verification.** Which row of [`agent/VERIFICATION-MATRIX.md`](agent/VERIFICATION-MATRIX.md)
   proves each change, what it returned, and what could not be run and why. Implementation is not
   finished until it has been verified locally, and a queue row does not reach `Done` without it.
10. **Record what waits on a person.** Every owner decision, and every run only a person or
    hardware can do, gets **one row** in the matching lane in [`todo/README.md`](todo/README.md) in
    the same change, naming this proposal and section as its canonical parent. A `Pending` proposal
    also gets its *Awaiting acceptance* row. The lanes are a derived index and never authorize anything.
    Every such row, and every decision gate in the proposal itself, keeps its full explanation and ends it with
    `**Question:** <one short sentence>` — plain English, answerable yes or no where it can be, no identifiers — so the owner
    can find the ask without reading the rest ([`todo/README.md`](todo/README.md#row-format); enforced by
    `tests/docs/test_decision_questions.py`).

The model is the best fit for the required capability, tools, risk and acceptance bar; price alone
does not justify a weaker model for sensitive work. A model assignment is required even for Pending
and Deferred items, but it grants no implementation approval. Historical Done rows carry a current
follow-up recommendation, not an invented record of the model originally used.
Start with `gpt-6.1-sol` for coding, including native and security contracts. Choose Astra for a
specific demanding integration or escalation, not solely because a path is sensitive. Keep the
same verification requirements with either model.

## Evidence vocabulary

- **Verified:** directly observed in code or an executed check.
- **Inferred:** likely from code structure but not executed.
- **Proposed:** does not exist yet.
- **Blocked:** could not be verified because a named dependency was unavailable.

Never present inferred or proposed behavior as implemented.

## Minimum injection-map row

| Location | Symbol/surface | Change | Example | Verification |
|---|---|---|---|---|
| `modules/backend-api/...` | `GET /api/v1/setup/status` | Add versioned readiness result | `{\"overall\":\"blocked\",\"checks\":[...]}` | Contract + timeout + degraded-mode tests |

Use [the proposal template](proposals/TEMPLATE_PROPOSAL.md) for all material changes.

## Module work is proposal work

A module is not built, split, retired, or promoted past `scaffolded` without a row in
[`PROPOSALS.md`](PROPOSALS.md). A **new top-level module** additionally requires, per
`CLAUDE.md` §2.6 and §9:

1. A roadmap layer in [`architecture/roadmap.md`](architecture/roadmap.md).
2. An entry in [`architecture/deviations.md`](architecture/deviations.md) explaining why it is not
   an existing layer.
3. Labels (`Content` / `Stream` / both) in `CLAUDE.md` §4 and [`../modules/README.md`](../modules/README.md).
4. `setup/manual.md` and `setup/automated.md` — and if nothing about it is automated,
   `automated.md` says so plainly rather than implying a script exists.
5. Rows in [`agent/MODULE-MATRIX.md`](agent/MODULE-MATRIX.md) and
   [`agent/MODULE-ITEM-MATRIX.md`](agent/MODULE-ITEM-MATRIX.md).

`DM-MODULE` in [`agent/DOC-UPDATE-MATRIX.md`](agent/DOC-UPDATE-MATRIX.md) lists the same set as a
trigger rule, so the requirement is discoverable from either direction.

## Testing queue placement

Use `docs/PROPOSALS.md` **Testing** for a working core whose next work is mainly acceptance,
configuration, delivery or bounded remaining features. Keep its canonical status In progress
and its model assignment unchanged. Name both **Build/Delivery left** and **Test next** in the
row, preserve historical evidence, and move it back to In progress if substantial build work
returns. Testing placement neither closes the proposal nor authorizes external actions.
