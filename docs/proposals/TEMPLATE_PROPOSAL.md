# Proposal: <title>

> Copy this file to `PROPOSAL_<SHORT_NAME>.md`, then add a row to
> [`../PROPOSALS.md`](../PROPOSALS.md) that links it. **Numbers live in the queue, not in the
> filename** — a file with no row pointing at it is not queued work.

**Queue row:** `P-0NN`
**Agent model / effort:** `<exact-model-id>` / `<reasoning-effort>` — <scope-based rationale>
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Pending` — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md), not here

**Owner:** <name/team>
**Date:** YYYY-MM-DD
**Roadmap layer(s):** <layers>
**Evidence level:** Verified / Inferred / Proposed / Blocked
**Verified against:** `<commit or branch>`, `<YYYY-MM-DD>` — what §2 was read and tested against

Choose the **best available model** for the actual proposal work before implementation. Confirm
its model ID and effort are available, then select them in the execution client. Copy the same
assignment and rationale into the queue row; reassess both when scope changes. Name draft/reviewer
models separately if used, and document child-task overrides. Runtime inference/TTS/CV models
belong in the relevant contracts/configs. Model selection does not authorize Pending work.
Default to `gpt-6.1-sol` for coding; justify an Astra exception for demanding integration or
escalation. Mechanical documentation may use Luna. Verification requirements still apply.

## 1. Executive summary

What user outcome changes, why now, and the smallest shippable result.

## 2. Verified current state

List exact files, routes, commands, tests, and observed results. Separate verified facts from inference.

## 3. Problem, goals, and non-goals

State actors, pain, measurable goals, exclusions, assumptions, and constraints.

## 4. User paths and states

Cover first run, success, missing dependency, invalid input, offline/degraded state, retry, cancellation, upgrade, and recovery.

## 5. Architecture and data flow

Describe local vs cloud execution, trust boundaries, sensitive data, retention, authentication, and module boundaries.

## 6. Direct injection map

| Location | Symbol/route/component | Before | Proposed change | Example | Verification |
|---|---|---|---|---|---|

**Files intentionally unchanged.** Name the files a reader would expect this change to touch and that it leaves alone, each with the
reason: a sensitive path, a file another proposal owns, a generated file, a consumer maintained elsewhere.

## 7. Contracts and examples

Include request/response schemas, events, configuration, error codes, UI copy, and compatibility/version behavior.

## 8. Security, privacy, accessibility, and observability

State controls, redaction, keyboard/screen-reader behavior, logs, metrics, and alerts.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|

## 10. Delivery plan

Give phases with dependencies, owner, acceptance evidence, and explicit out-of-scope work.

**First implementation slice.** The smallest change that can merge on its own: what it contains, which verification proves it,
and what it leaves for the next slice.

## 11. Rollout and rollback

Define feature flags, compatibility window, rollback triggers, data reversal, and support response.

## 12. Risks and unresolved decisions

An item that waits on the owner keeps its full explanation and ends it with `**Question:** <one short sentence>` — plain
English, answerable yes or no where it can be, no identifiers. A decision-gate table adds one such line per gate.

| Item | Impact | Mitigation/decision owner | Due date |
|---|---|---|---|

## 13. Documentation updates

Name every document whose claims, setup steps, API reference, or support policy must change.
