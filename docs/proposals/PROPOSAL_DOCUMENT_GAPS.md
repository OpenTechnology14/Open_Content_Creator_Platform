# Proposal: Document gaps — from advisory documents to a documentation system that fires

> Copied from [`TEMPLATE_PROPOSAL.md`](TEMPLATE_PROPOSAL.md). **Numbers live in the queue, not in the
> filename.**

**Queue row:** `P-071`
**Agent model / effort:** `gpt-6.1-sol` / `high` — Documentation-system design, generated registries and CI-gated drift checks (phases 2–6)
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Done` — approved phases 1–5 implemented and verified; phase-6 future items retain their deferred triggers.
State remains authoritative in [the queue](../PROPOSALS.md). Phase 1 is built; the dated
continuation below records further implementation and outstanding dependencies.
**Owner:** OpenTechnology14 + agent
**Date:** 2026-10-04
**Roadmap layer(s):** None — process and documentation; no new module. The one proposed code change is a `make verify` target (§10, phase 3)
**Evidence level:** *Verified (read)* for OpenTechnologyApp — its files were read, none of its scripts were run. *Verified* for this repository. *Proposed* for everything not built in phase 1

## 1. Executive summary

**Phase-1 follow-up, 2026-10-05:** the owner requested better public-facing beginner and
engineering documentation, using JobHunter/OpenTechnologyApp as references. The
[reference review](../PUBLIC_DOCS_AND_MARKETING_REVIEW.md) records the findings and
verification; the [local documentation website](../public/index.html) provides the new
task-first entry point. P-070 adds walkthrough briefs to the existing marketing generator.
This authorized documentation extension does not accept phases 2–6 below or deploy a website.

[P-069](../PROPOSALS.md) gave this repository a way to **navigate** — a project crosswalk and a
documentation workflow. It did not change how the operating documents behave: they are advisory.
[`agent/README.md`](../agent/README.md) says of its own matrices that "none of it fires
automatically", and [`agent/DOC-UPDATE-MATRIX.md`](../agent/DOC-UPDATE-MATRIX.md) says "no CI posts
this". OpenTechnologyApp, read on 2026-10-04, solves each of those with a specific mechanism:
generated and CI-gated registries, a generated `AGENTS.md`, one command that runs every CI gate,
tiered on-demand audit commands with a capped log, an intake SOP, and a queue section for
owner-run actions.

This proposal records the verified gap table (§2), builds the three cheapest pieces now as
documents only, and proposes the rest as ordered, triggered future documents:

- **Built now (phase 1):** the [content](../todo/CONTENT_CREATE_TODO.md) and
  [stream](../todo/STREAM_DECISIONS_AND_TODO.md) lanes — every owner decision and live run pulled
  out of twelve proposals into two lists, with a [lane index](../todo/README.md); the
  [future-documents registry](../FUTURE_DOCS.md); the OpenTechnologyApp intake mechanism added to
  the two future docs; and a SOP step, a new advisory matrix rule and an extended one that keep the lanes current.
- **Proposed, with the evidence that its trigger has fired:** `make verify`, a generated
  `AGENTS.md`, an on-demand audit command, a pre-merge command, a machine-readable queue check, and
  a queue hygiene pass.

The smallest shippable result is the documents in this change. **No code is proposed for merge here.**

Three findings surfaced while reading, each of which changes a decision:
**(a)** CI is no longer billing-blocked — and its first real run on `main` is red (§2, row 3);
**(b)** the blog has no admin UI, so P-067's first walkthrough target does not exist as a UI flow
([`CT-D09`](../todo/CONTENT_CREATE_TODO.md)); **(c)** the AI Learning posts have been live since
2026-09-26 while this repository's crosswalk still marks them unpublished
([`CT-R14`](../todo/CONTENT_CREATE_TODO.md)).

## 2. Verified current state

OpenTechnologyApp was read at `~/Downloads/OpenTechnologyApp`, branch `feature/ui-hamburger-view-toggle`,
clean tree, on 2026-10-04. This repository is `origin/main` at `4fbed5e`.

| # | Mechanism (OpenTechnologyApp, read) | This repository today (verified) | Gap |
|---|---|---|---|
| 1 | **Generated, CI-gated registries.** `docs/agent-registries/README.md`: "every file in this directory is generated. Do not hand-edit"; each is written by a script and checked by a gate that regenerates it and fails on a difference | `docs/agent/*` are hand-maintained and say they do not fire. The only docs gate, [`tests/docs/test_docs_integrity.py`](../../tests/docs/test_docs_integrity.py), checks **structure** — links, index, queue rows, backticked paths — not whether a document is **current** | **G1** — FD-08, FD-09, FD-10 |
| 2 | **Generated `AGENTS.md`**, from `CLAUDE.md`, by `scripts/generate-agents-md.ts`, with a CI check — written because `AGENTS.md` "had silently fallen behind on *rules*" | Two hand-kept files. The pairing test covers **§4 and §11 only**, so `AGENTS.md` §12 listed **six** pointers where `CLAUDE.md` §12 listed **fifteen** — no queue, no matrices, no parking lot, and a pointer to the retired "All guides" (synced by this change). §3 of both still calls the apps' commands "still stubbed" ([`CLAUDE.md`](../../CLAUDE.md) lines 59–60; [`AGENTS.md`](../../AGENTS.md) lines 59–60), which P-054 (`Done`) and P-055 (code done) contradict | **G2** — FD-07 |
| 3 | **One command that runs every CI gate**, `scripts/verify-all.ts`, generated from `ci.yml` at run time with a minimum-steps tripwire and an explicit *not run* list | [`Makefile`](../../Makefile) has `test`, `test-acceptance`, `test-obs` and `lint` separately; no `verify`. **CI health:** every run on 2026-09-26 failed after about two seconds (the billing block). The 2026-10-03 run **executed** — both desktop-app builds passed, 10–18 minutes each — and `lint-and-test` **failed** at `make test-acceptance`, because `docker compose up -d` could not pull `quay.io/minio/minio:latest` (`unauthorized`). Quay's public API answered `401` for that repository on 2026-10-04. The five PRs merged on 2026-09-26 had no meaningful CI run | **G3** — FD-06, and [`PL-D08`](../todo/README.md#platform-and-release-decisions-no-lane-doc-yet) |
| 4 | **On-demand audit commands** in `.claude/commands/`: `audit` (tiered quick, standard, deep), `pre-merge`, `daily`, `bug-sweep`, `migration-check` | `.claude/` tracks one skill, `marketing-discovery`. No command | **G4, G5** — FD-11, FD-13 |
| 5 | **A capped audit log** (`AUDIT_LOG.md`, last ten entries) and a **finding ledger** (`AUDIT_FINDING_LOG.md`) with fingerprints and triage windows — Critical 24 hours, High 3 days, Medium 14 days, Low 30 days | [`AUDIT.md`](../AUDIT.md) is a point-in-time verdict; [`GAP_AUDIT.md`](../GAP_AUDIT.md) is a ledger re-verified 2026-09-02. No append-only log, no triage clock | **G6** — FD-11, FD-19 |
| 6 | **A governed queue**: `PRIORITY.md`, a 60-entry `proposal-registry.json`, a validator, and `WORK_INTAKE_SOP.md` | [`../PROPOSALS.md`](../PROPOSALS.md) is a 700-line table. **Sections do not match states**: four `Done` rows (P-031, P-016, P-017, P-018) sit under "Pending — candidate modules", and "Accepted — build-out work" is mostly `Done`. **Two rows use a state outside the six** — P-067 and P-068, both written by this agent, say "Proposed — awaiting owner decision". P-063's inline slice history is roughly 450 lines. The only check is that every proposal document has a row | **G7** — FD-21, FD-22, FD-23 |
| 7 | **Operator action handoffs** — owner-run actions inside the queue, each naming its canonical proposal | Owner decisions and live runs are scattered across **twelve proposals** (P-001, -002, -004, -056, -059, -060, -061, -062, -064, -066, -067, -068), each in its own section 12 or equivalent, with no single list | **Built here** — FD-01 to FD-03 |
| 8 | **Future docs read by the audit** — `FUTURE.md` and `FUTURE_STATE.md` carry an intake banner and are read by `/audit` and `/daily` | [`architecture/future.md`](../architecture/future.md) and [`future-state.md`](../architecture/future-state.md) already exist and already split backlog from compass, with triggers. They have no intake banner, nothing reads them, and the compass said "currently 2 of 17" modules past `scaffolded` — [`CLAUDE.md`](../../CLAUDE.md) §11 says **4 of 21** | **Built here** — FD-05 |
| 9 | **A manual testing workflow** with an ordered owner-action list and a scheduled weekly run (`weekly-e2e.yml`) | [`TESTING.md`](../../TESTING.md), [`ACCEPTANCE-CHECKLIST.md`](../../tests/ACCEPTANCE-CHECKLIST.md), [`USE-CASES.md`](../../tests/USE-CASES.md) and the [verification matrix](../agent/VERIFICATION-MATRIX.md) are procedure-rich, with proof markers. There is **no scheduled run and no home for run evidence**. [`PRESSURE_TEST_LOAD.md`](../PRESSURE_TEST_LOAD.md) is 32 lines with no measured number, and P-056's performance gates are "targets to measure, not claims" | **G8, G9** — FD-12, FD-14, FD-16, FD-18 |
| 10 | **A runbooks directory** (`docs/runbooks/`, eight files) | Recovery procedures exist only **inside** the two production guides ([§10](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#10-failure-modes-and-recovery) and [§9](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md#9-failure-modes-and-recovery)); never rehearsed | **G10** — FD-17 |
| 11 | **Session handoff**, `HANDOFF.md` | None. Parallel sessions edit one checkout. Observed: a commit on 2026-09-26 carried another session's concurrent edits; P-066 was claimed by two proposals at once; P-070 was claimed in another session's uncommitted queue edit while this proposal was written (hence **P-071**) | **G11** — FD-24 |
| 12 | **A bug tracker and bug SOPs**, `BUG_TRACKER.md`, `BUG_CREATION_SOP.md`, `SECURITY_TRACKER.md` | [`GAP_AUDIT.md`](../GAP_AUDIT.md) (`HCP-001`…) is the de facto tracker; [`SECURITY.md`](../../SECURITY.md) is 27 lines | **G12** — FD-20 |

One strength worth stating plainly: the docs-integrity suite is large and good. The gap is not that
documents are unchecked; it is that **nothing checks them for being current, and nothing tells an
agent to look.**

## 3. Problem, goals, and non-goals

**Problem.** The documents describe what to do but nothing makes them fire; what is waiting on the
owner is invisible; testing documents hold procedures but have no on-demand entry point and no
evidence home; and the repository's first real CI run is red for a reason no document records.

**Goals.**

- One place per lane to see **what waits on a person** — built.
- Every documentation gap has a **state and a trigger**, in one registry — built.
- Testing documents gain the two properties OpenTechnologyApp's have: they are **built into agent
  work** (an agent is told, by instruction files and one command) and they come with **on-demand
  audits** (named, tiered, logged) — §7, proposed.
- The queue's sections, states and vocabulary agree — proposed, phase 2.

**Non-goals.**

- **No code in this change.** `make verify`, the audit commands and generation are proposed.
- **No autonomous daily routine** (FD-28). The owner is this repository's acceptance step.
- **No bug tracker yet** (FD-20), and **no change to a CI workflow.**
- **No reordering of `PROPOSALS.md`.** Rank is not approval, and another session has uncommitted
  edits to that file.
- **No copy of OpenTechnologyApp's content** — only its mechanisms (FD-26).

## 4. User paths and states

| Path | Today | With phase 1 |
|---|---|---|
| **Owner asks "what is waiting on me?"** | Read twelve proposals | Open the [lane index](../todo/README.md); each lane opens with its next three |
| **An agent starts a proposal** | Follows the SOP's nine steps | A tenth step records its decisions and runs in a lane; `DM-PROPOSAL-OPEN` says the same |
| **The owner answers a decision** | The answer lives in chat | Recorded in the source proposal first, then moved to the lane's *Resolved* log with its date |
| **A run completes** | Nothing says where the numbers go | Recorded in the owning proposal until the evidence log exists (FD-12); its row moves to *Resolved* |
| **CI is red** | Unknown until someone opens Actions | [`ST-T13`](../todo/STREAM_DECISIONS_AND_TODO.md) names the cause; `PL-D08` is the decision |
| **A lane row goes stale** | Silent | The lane index says **the source wins**; `Last reviewed` is on every doc; FD-21 would diff the queue against the lane map |
| **An on-demand audit** (proposed) | No command | `/audit quick` runs `make verify`, reads the lanes and CI state, and logs a capped entry |

## 5. Architecture and data flow

Everything stays in the repository; no service, no network, no secret.

| Layer | Owns | Authoritative for |
|---|---|---|
| [`PROPOSALS.md`](../PROPOSALS.md) | The queue | **State and authorization.** Only the owner accepts |
| Proposal documents | Rationale and contract | What a change is, and how it is proven |
| **Lane docs** (new) | What waits on a person | **Nothing.** A derived index; the source wins |
| **Future-documents registry** (new) | Missing documentation | State and trigger of each *document* |
| `architecture/future.md`, `future-state.md` | Deferred features; the compass | Triggers; targets |
| Generated registries (proposed) | Derived facts | Only what a script regenerates |

**Rules for runs that touch a real account**, carried from OpenTechnologyApp's manual testing
workflow: the owner performs the sign-in; an agent continues from an authenticated session and never
types a credential into a form; secrets stay in environment variables and the OS credential manager,
never in a lane row or a log.

**Sanitized evidence.** A lane row, an audit log entry and a run record contain no tokens, keys,
private emails, account identifiers or unredacted provider payloads. Public handles are fine.

## 6. Direct injection map

| Location | Change | Example | Verification |
|---|---|---|---|
| `docs/todo/README.md`, `CONTENT_CREATE_TODO.md`, `STREAM_DECISIONS_AND_TODO.md` | **New** — the lanes | `\| CT-D01 \| **Pet character** … \| P-067 §14 Q1 \| … \| None — needs you \| open \|` | Docs-integrity suite; anchor check; every ID the index cites exists |
| [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md) | **New** — the registry | `\| FD-06 \| One-command local verify … \| **Proposed** \| **Trigger fired:** … \|` | Same |
| [`../PROPOSALS.md`](../PROPOSALS.md) | Add the P-071 row; normalise P-067 and P-068 to the six-state vocabulary; one sentence pointing at the lanes | `\| P-071 \| … \| **Pending** — … \|` | Docs-integrity suite (`test_every_proposal_has_a_queue_row`) |
| [`../README.md`](../README.md) | Index rows for the lanes and the registry | — | `DM-DOCS-INDEX`; the index-completeness test |
| [`../PROPOSAL_CREATION_SOP.md`](../PROPOSAL_CREATION_SOP.md) | New step 10 — record what waits on a person | "Add one row per item to the matching lane in the same change" | Read-through |
| [`../agent/DOC-UPDATE-MATRIX.md`](../agent/DOC-UPDATE-MATRIX.md) | New rule `DM-PROPOSAL-OPEN`; `DM-PROPOSAL-DONE` also resolves lane rows | "a proposal is added, or gains an owner decision or a live run" | Docs-integrity suite (living docs declare status and enforcement) |
| [`../agent/README.md`](../agent/README.md) | One row pointing at the lanes | — | Link test |
| [`../architecture/future.md`](../architecture/future.md), [`future-state.md`](../architecture/future-state.md) | Intake banner; compass note that nothing reads it yet; stale module count corrected | "currently 4 of 21" | Link test; the count re-read from `CLAUDE.md` §11 |
| [`PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md`](PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) | Dated correction to Q9 and Run 1 | "Premise false — verified 2026-10-04" | Link test |
| [`CLAUDE.md`](../../CLAUDE.md), [`AGENTS.md`](../../AGENTS.md) §12 | One Quick Reference line each | "Owner decisions and runs waiting: `docs/todo/README.md`" | `test_agents_and_claude_stay_paired` (§4 and §11 are untouched) |
| *Proposed:* `Makefile`, a verify script | `make verify` | §7 | §9 scenarios V1–V4 |
| *Proposed:* `.claude/commands/` | `audit`, `pre-merge` | §7 | §9 scenarios A1–A3 |

## 7. Contracts and examples

### Testing documents: built into agent work, and on-demand audits

OpenTechnologyApp's two properties, in this repository's terms.

| Property | Already here | Built by phase 1 | Proposed |
|---|---|---|---|
| **Built into agent work** — an agent is told, at the moment it matters | [`CLAUDE.md`](../../CLAUDE.md) §9 says to verify locally and consult the matrix; the [verification matrix](../agent/VERIFICATION-MATRIX.md) and the [acceptance checklist](../../tests/ACCEPTANCE-CHECKLIST.md) carry proof markers | A SOP step and a matrix rule that route owner decisions and live runs to the lanes; a `Quick Reference` line in both instruction files | **`make verify`** named in both instruction files (FD-06); a **generated** `AGENTS.md` (FD-07) so the two cannot drift |
| **On-demand audits** — named, tiered, logged | The `marketing-discovery` skill is the one on-demand entry point | The lane `Next three` blocks and the [testing inventory](../todo/STREAM_DECISIONS_AND_TODO.md#testing) give an audit something to read | **`/audit`** and **`/pre-merge`** commands and a capped log (FD-11, FD-13) |

### Proposed: `make verify`

```bash
make verify              # every gate ci.yml runs, in CI's order
make verify ARGS=--list  # the parsed steps and the NOT-run list, without running
```

- **Reads the CI workflow at run time** with a real YAML parser — the workflow has multi-line `run:`
  blocks, so line parsing is not enough — rather than keeping a second, hand-copied list.
- **Tripwire:** refuses to report a clean run if it parses fewer steps than a stated minimum.
- **Skips loudly** what cannot run locally — Docker absent, hardware, real accounts — and prints a
  *not run* list. Exit status is non-zero on any failed gate **or** a tripped wire.
- **Never** runs anything that writes to a real service (`make up`) or needs OBS (`make test-obs`).

### Proposed: `/audit [quick|standard|deep] [scope]`

| Tier | Does | Cost |
|---|---|---|
| **quick** | `make verify`; the lane `Next three` blocks; the CI state of `main` | One gate sweep |
| **standard** | quick, plus a documentation sweep (docs-integrity, `marketing-crosswalk validate`), a stale-number scan against [`CLAUDE.md`](../../CLAUDE.md) §11, a diff of open queue rows against the lane map, and a **future-state gap pass** that names the furthest pillar. A public claim above a module's status is a **credibility gap — treated as high** | + a read of the docs |
| **deep** | standard, plus a security review on diffs touching `apps/*/src-tauri/`, `apps/shared/social-manager`, `apps/shared/local-settings`, `cloud/relay` or `modules/social-management`, and a code review | Highest; before a release or after a large merge |

**Read-only on code** — it produces findings and does not fix them. It ends by naming the single
highest-priority fixable finding and the single highest-leverage future-state move, and the path to
the log. The log keeps the **last ten entries**, at most **15 current-state lines and 3 future-state
lines** each, no code and no stack traces.

### Proposed: `/pre-merge`

Branch and PR state first — behind `origin/main`? worktrees mid-work? is the proposal number already
claimed, including in another session's uncommitted queue edit? is a stacked PR's base branch about to
be deleted (retarget children first)? — then `make verify`, then queue bookkeeping: row, lane rows,
index entry.

### Lane row example

```text
| CT-D09 | **What does the first walkthrough record?** … | P-067 §14 Q9 | CT-R06 | None. (a) is the smallest | open — new |
```

## 8. Security, privacy, accessibility, and observability

- **No secrets or private identifiers** in any lane row, audit entry or run record (§5).
- **Credential rule** for live runs is in the lane index and is the same boundary the agent already
  operates under: the owner signs in; the agent never types a secret.
- **Accessibility.** Plain Markdown tables and headings; every doc opens with a one-sentence scope.
- **Observability.** Every living doc carries `Last reviewed`. The lane index states that the source
  wins. The audit's capped log is the proposed time series; until it exists, `Last reviewed` is the
  only freshness signal, and it is manual.
- **A wrong lane row is low-harm and a wrong *claim* is not.** A lane row never authorizes anything
  and never states a capability; it points at a proposal.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| D1 | A new doc under `docs/` is not in the index | Docs-integrity suite fails | Auto | Phase 1 |
| D2 | A lane row links to a missing file | Link test fails | Auto | Phase 1 |
| D3 | A lane index cites an ID no lane defines | Caught by the ID check run for this change; **no standing check** | Manual now; FD-21 later | Phase 2 |
| D4 | A proposal gains an owner decision and no lane row | `DM-PROPOSAL-OPEN` says it must; **nothing enforces it** | Advisory | Phase 2 (FD-21) |
| D5 | Two sessions add rows to one lane doc | One row per line, so conflicts are line-local | Design property | — |
| D6 | A row is marked resolved while its source still shows the question open | The intake rule forbids it | Manual review | — |
| V1 | `make verify` parses a CI fixture missing steps | Tripwire fails the run | Auto (fixture) | Phase 3 |
| V2 | A gate fails | Non-zero exit; the summary names it | Auto (fixture) | Phase 3 |
| V3 | Docker is absent | Steps needing it are SKIPPED, listed in *not run* | Manual | Phase 3 |
| V4 | A step is added to the CI workflow | Picked up with no edit to the verify script | Auto (fixture) | Phase 3 |
| A1 | `/audit quick` on a clean tree | Gate summary, lane `Next three`, CI state, a capped log entry | Manual | Phase 4 |
| A2 | `/audit` finds a claim above a module's status | Reported as a credibility gap, high | Manual | Phase 4 |
| A3 | `/pre-merge` on a branch whose proposal number is claimed elsewhere | Reports the claim before pushing | Manual | Phase 4 |

## 10. Delivery plan

Source/bundled-setup CI prerequisite was verified on PR #67, run `37876242044` at `907c3dc`:
both app jobs and the live storage/creator acceptance passed. Phase-5 integration proceeds
against that tested branch; it does not claim main was merged or a release approved.

**Integrated Sol continuation, 2026-10-08:** the owner requested continuing Sol work to
completion after the assignment review. The parent performs queue-state normalization,
lossless P-063 extraction and generator integration as `gpt-6.1-sol` / `high`; this explicitly
overrides L1/L2's Luna recommendation for this coupled pass. Their original checkpoint text
and all evidence are preserved. Routine future row moves/indexing still fit Luna; no Luna
execution is claimed here. Canonical state prefixes supersede the preservation-only L1
contract where old Code complete/Partially done aliases need an In progress prefix.
The parent also completes the source-bounded T1/T2 draft material for integration, explicitly
overriding Terra for this pass; future first drafts remain suitable for Terra. The
[walkthrough artifact](../BEGINNER_WALKTHROUGH.md) contains narration/screen cues, a transcript,
15 glossary entries and eight recovery answers. It does not assert captured or approved media.

| Phase | Scope | Depends on | Acceptance evidence | State |
|---|---|---|---|---|
| **1** | The two lanes and the index; the future-documents registry; the intake banner and corrected metric; the SOP step, matrix rule and index rows; the P-067 correction; the P-071 row | — | Docs-integrity suite, anchor check and `git diff --check`, recorded in §14 | **Built 2026-10-04** |
| **2** | Queue hygiene: move `Done` rows to `Done`, keep to six states, move P-063's slice history to its own proposal; then the queue check (FD-21, FD-22) | Another session's uncommitted `PROPOSALS.md` edits landing | Every row's section matches its state; the check diffs open rows against the lane map cleanly | **Built and verified — 2026-10-09** |
| **3** | `make verify` (FD-06) and a verification-matrix row | Owner decision OD-2 | §9 V1–V4 on a fixture; one real run's output recorded | **Built and verified — 2026-10-09** |
| **4** | `/audit`, `/pre-merge` and the capped log (FD-11, FD-13); `.gitignore` re-includes `.claude/commands/` the way it already re-includes `.claude/skills/` | Phase 3 (the quick tier *is* `make verify`) | §9 A1–A3 | **Built and verified — 2026-10-09** |
| **5** | Generated `AGENTS.md` (FD-07); generated registries and a docs gate (FD-08–FD-10) | OD-3; green CI (ST-T13) | A check fails on a hand-edit | **Built and verified — 2026-10-09** |
| **6** | FD-18, FD-19, FD-20, FD-24, FD-25 | Their triggers | Per row | Deferred |

**Out of scope:** CI workflow changes while ST-T13 is red; an autonomous routine; any module.

## 11. Rollout and rollback

### Terra/Luna child scopes — 2026-10-08

Owner requested scoping suitable work for Terra and Luna. The four tasks below are **scoped;
execution not started**. They remain children of P-071, so they add no top-level proposal IDs.
The parent retains `gpt-6.1-sol` / `high`; these explicit overrides apply only to their named
outputs. Sol reviews each result before parent acceptance. Choose the named model in the
execution client and record the actual executor; a scope document does not switch this session.

#### L1 — Queue organization

**Agent model / effort:** `gpt-6-luna` / `high` — Mechanical row relocation with fixed inputs and count/content checks.

Input: the committed proposal queue and the current machine-readable report. Move completed
rows into a clearly labelled completed section; keep pending, accepted, active and deferred
work discoverable. Preserve every ID, complete status cell, model assignment, evidence note,
relative link and existing inline heading. Do not normalize a partial state into Done or change
authorization. Limit changes to the queue and index pointers needed by the move.

Acceptance: before/after proposal-report counts and assignments identical; every row's cells
unchanged except its location; `make proposal-report ARGS='--check --summary'`, required
`make test` and `git diff --check` pass. Escalate any conflicting state/evidence to Sol rather
than guessing. FD-22 remains open until this actually runs.

#### L2 — Extract installer slice history

**Agent model / effort:** `gpt-6-luna` / `high` — Lossless documentation extraction with link/heading preservation.

Input: P-063's inline history in the queue. Move the dated history into a dedicated P-063
proposal document, preserving its model/effort header, evidence dates, commands, hashes and
remaining acceptance gates. Keep the existing queue anchor as a short redirect and link the
new document from P-063's row. No changes to installers, package identifiers, acceptance
claims or native code. Work after L1 so both tasks do not rewrite the queue concurrently.

Acceptance: all extracted history preserved; old inbound anchor resolves; new proposal has
matching P-063 metadata and a queue link; relative paths/fragments checked explicitly; required
`make test` and `git diff --check` pass. Sol resolves any stale evidence discovered during the move.

#### T1 — First-recording walkthrough narration

**Agent model / effort:** `gpt-5.6-terra` / `medium` — Source-bounded editorial drafting from an established storyboard.

Input: the beginner recording path in the [local documentation website](../public/index.html),
the capture module's setup guide and the existing walkthrough-brief format. Draft one 3–5 minute
spoken walkthrough of a private OBS practice recording: picture, sound, record, replay and one
recovery example. Supply screen cues, a text transcript and suggested screenshot captions.
Keep source citations in reviewer notes. Estimated timing is a draft, pending timed rehearsal.

No generated footage or invented capture evidence; any unverified step remains explicitly
marked for rehearsal. Preserve current versus planned app boundaries, optional tools and local
operation. Native controls, account connections, publishing and product naming are outside scope.

Acceptance: Sol traces each instruction/claim to a supplied source, checks the timing estimate
and reviews beginner readability. Draft contains no private repository URLs or claim that a
recording already happened. Marketing validate/selftest, required `make test` and diff checks pass.
A real recorded walkthrough remains separately awaiting operator/device acceptance.

#### T2 — Beginner glossary and recovery FAQ

**Agent model / effort:** `gpt-5.6-terra` / `medium` — Small structured explanations derived from reviewed documentation.

Input: the same beginner path and canonical setup guides. Draft up to 15 glossary entries and
eight FAQ answers. Each term gets one plain-language definition and a concrete example; each
FAQ gets a visible symptom, a bounded next action, expected result and escalation reference.
Cover scene, source, capture, audio meter, mute, recording, remux, profile, inbox, clip, render,
export and optional setup. Link to technical references instead of duplicating their contracts.

Acceptance: Sol checks factual/UI-label accuracy and local/cloud distinctions. Planned combined
navigation must remain labelled planned. No prices, new feature promises or installation commands
may be invented. Publish-ready site edits require Sol review after the draft; no deployment is
included. Required `make test`, link/fragment review and diff checks pass.

L1/L2 can use objective preservation checks; T1/T2 need editorial and factual review. Native
permissions, credentials, process execution, session ownership, realtime audio and combined-app
migration stay with the assigned Sol/Astra work.

Scoping verification: four proposal-model checks passed; required `make test` reached
100%, exit 0 (`/tmp/hcp-terra-luna-scopes-20261008.log`); child-section fragment and all
four task headers checked; proposal report still has 73 top-level proposals / 29 unfinished
and no lane discrepancies; `git diff --check` passed. This verifies the scope documents,
not execution by the assigned child models.

Phase 1 is additive documentation plus advisory rules. **Rollback = revert the change.** No data,
no service and no behaviour is touched; the only consequence is that an agent following the new SOP
step or matrix rule has nowhere to write. Phases 3–5 add behaviour and each gets its own queue row,
verification and rollback.

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation / decision owner | Due |
|---|---|---|---|
| Lane docs rot — nothing yet checks them | A stale row misleads | The source wins; `Last reviewed`; the intake rule; FD-21 | Phase 2 |
| A shared item is mis-laned | Work looks done in one lane and open in another | Split, never duplicate; link through *Needs* | Standing |
| This change edits three files another session has uncommitted | A textual conflict on pull | Surfaced to the owner; the edits are small and line-local | At merge |
| **OD-1** — give platform and release decisions their own lane doc now? | A decision is easy to miss | **Default: later** (FD-25), when the table passes about ten live rows | Owner |
| **OD-2** — build `make verify` before the audit commands? | Order of work | **Default: yes** — the quick audit tier is `make verify`, and CI's first real run is red | Owner |
| **OD-3** — generate `AGENTS.md` from `CLAUDE.md`, making `CLAUDE.md` the source? | Ends the drift; changes who may edit what | **Default: yes**, in phase 5 | Owner |
| **OD-4** — defects: extend `GAP_AUDIT.md`, or start a bug tracker? | Where defects live | **Default: extend `GAP_AUDIT.md`** until volume justifies a tracker | Owner |
| **OD-5** — adopt an autonomous daily routine? | Unattended builds on live paths | **Default: no** (FD-28) | Owner |
| **OD-6** — when to run the queue hygiene pass? | A large `PROPOSALS.md` edit | **Default: right after the other session's edits merge** | Owner |
| **OD-7** — a proposal-number reservation rule: add the queue row first, in its own tiny change? | Two collisions in nine days | **Default: yes** | Owner |

## 13. Documentation updates

Built by this change: the three lane documents, [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md), the
[docs index](../README.md), the [SOP](../PROPOSAL_CREATION_SOP.md), the
[matrix](../agent/DOC-UPDATE-MATRIX.md) and [agent index](../agent/README.md), the two
[future docs](../architecture/future-state.md), the P-067 correction, the queue row, and one line in
each instruction file. Proposed, per phase: [`../agent/VERIFICATION-MATRIX.md`](../agent/VERIFICATION-MATRIX.md),
`CLAUDE.md` §9, and a new audit log.

## 14. Verification

### Documentation-system implementation — 2026-10-08

Phases 2–5 are implemented on `feat/sol-documentation-closure`: all 73 rows are grouped
under canonical states, eight old partial/code-complete labels have an In progress prefix
with the original implementation checkpoint preserved verbatim, and the unfinished count
remains 29. P-063's 509 history lines were extracted into its queued proposal; reversing
the relative-link rebasing reproduced the original history exactly. Existing inbound P-063
links still reach the old anchor, which now redirects to the proposal.

`generate_docs.py` generates AGENTS.md from CLAUDE.md plus a registry of proposals, module
statuses and documentation rules. It preserves the full optional Claude-review policy,
rejects escaping generated paths, and catches full-file edits rather than only table drift.
Canonical sources remain authoritative; freshness is required in CI and the offline suite.

Local verification: 22 focused generation/model/verifier cases passed; required staged
`make test` reached 100%, exit 0 (`/tmp/hcp-docs-closure-offline.log`); Ruff and diff checks
passed; marketing validation passed 55 anchors/47 claims and selftest rendered 238 pairs.
The first full pass caught an externally owned policy path written as a local backticked
path; qualifying its OpenTechnologyApp ownership fixed it. Registry generation is deterministic.
The narration draft has 590 spoken words (about 4.2 minutes at 140 words/minute); rehearsal,
capture and approval remain explicitly pending. Hosted CI for this new slice is pending.

Phase 6 remains future/deferred work under its own triggers, not a daily automation.

**Closure, 2026-10-09:** CI run `37881497742` at `0693805` passed the generated-doc gate,
blocking lint/offline suite, both desktop jobs and both live acceptance tests. Native smoke
run `37881497783` passed macOS and Windows rehearsals. These results complete the approved
documentation-system scope (phases 1–5); optional phase-6 items stay in FUTURE_DOCS under
their deferred triggers, requiring their own intake when actionable. No module, hardware,
account or public-release acceptance is promoted by this closure.

### Continuation — 2026-10-08

Built `make verify`, reading YAML/matrices/run blocks from CI at runtime with an allowlisted
classifier, a 15-eligible-check tripwire, per-check timeout/process-tree cleanup, and a final
PASS/FAIL/NOT RUN summary. It preserves local `.env`; Compose rendering uses `.env.example`.
Tool installation and live acceptance service startup are always skipped and explained.
Unknown commands/expressions/unsafe working directories reject the plan before execution.

Built `make proposal-report`, deriving JSON counts/model assignments from the canonical
queue and checking unfinished IDs against the lane map. Duplicate IDs, unknown states and
missing assignments fail explicitly. This is the first phase-2 slice, not the complete queue
section/history cleanup or a substitute for the canonical Markdown authorization text.

Added `.claude/commands/audit.md`, `pre-merge.md` and the capped [audit log](../AUDIT_LOG.md),
with scope, credential-safe evidence, stacked-PR checks and distinct current/future findings.
The instructions are reviewable; real future audit invocations must record their own results.

Verification on base `44d624e` plus this slice: 11 new focused tests passed; Ruff passed;
real `make verify` exited 0 with 18 gates passed and 11 run commands explicitly not run.
Both frontends built and checked; both native app suites and CI-listed shared suites passed.
`make proposal-report ARGS='--check --summary'` found 73 proposals / 29 unfinished and no
missing or extra lane IDs. Log: `/tmp/hcp-sol-astra-verify-20261008.log`.
No Docker executable is available locally; no Compose/live acceptance, physical Windows,
real-account operation or release sign-off was exercised. Generated instruction/registry
phase 5 remains behind its existing green-CI dependency; section/history hygiene remains open.

Final required `PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test` reached 100%, exit 0
with the new files staged (`/tmp/hcp-sol-astra-offline-20261008.log`). Marketing validation
passed 55 anchors/47 claims; selftest rendered 238 pairs with zero failures. Ruff and
`git diff --check` passed. Queue lane IDs remained consistent after moving P-071 into progress.

**Current-main integration:** fetched `origin/main` at `73928c1` and merged its P-068
slices 1–4 plus the OBS setup fix, preserving both the new P-071 row and upstream P-068
evidence in the sole queue conflict. Repeated verification on merge `ebcbea7`: 18 local
gates passed, 11 commands explicitly not run, exit 0; required `make test` reached 100%,
exit 0. Logs: `/tmp/hcp-sol-astra-verify-current-20261008.log` and
`/tmp/hcp-sol-astra-offline-current-20261008.log`. Current main CI run `37486648546`
still fails at MinIO's unauthorized image pull, confirmed from its failed-step log.

Run 2026-10-04 in an isolated worktree of `origin/main` (`4fbed5e`), with this change staged so the
tracked-files filter sees the new documents — the trap [`DOCUMENTATION_WORKFLOW.md`](../DOCUMENTATION_WORKFLOW.md)
warns about. Documentation verification proves the **reference structure**, not any capability.

| Check | Result |
|---|---|
| `python -m pytest tests/docs/test_docs_integrity.py` | **723 passed.** 14 of the 15 changed Markdown files are collected by it. `AGENTS.md` is **outside the suite's file set** — only its §4/§11 pairing is tested — which is further evidence for FD-07 |
| Why 723 and not the ~19,800 seen in the main checkout | One test is parametrized per source file under `modules/`. The main checkout holds a gitignored ComfyUI clone — **19,289** source files there against **155** in a clean tree. An environment difference, not lost coverage |
| Full offline suite, `python -m pytest` | **1244 passed, 16 skipped, 1 xfailed** |
| Heading fragments, which the link test does not check | **37 fragment links across the 15 changed Markdown files; all resolve** |
| Every ID the lane index's queue map cites exists in a lane document | **74 cited, none missing** |
| Every open queue row appears in the map, and nothing else does | **28 open rows, 28 mapped, none missing or extra.** Run by script; there is no standing check yet (FD-21) |
| `git diff --check` | **clean** |
| `CLAUDE.md` and `AGENTS.md` §4 and §11 | Untouched; the pairing test passes. `AGENTS.md` §12 was synced to `CLAUDE.md` §12 (six pointers to fifteen, plus the new lane pointer) |

**Not run.** Every *live* row in the lanes — by design, none can be run by this change. `ruff` — no
Python changed. Anything in OpenTechnologyApp — it was read and never executed. A local `docker pull`
of the MinIO image — that finding rests on the CI log and on Quay's API answering `401`, not on a
reproduction.

**What this proves:** links, index entries, queue rows, fragment targets and ID consistency. It does
**not** prove any capability, and it promotes no module.

## Related

- [`../todo/README.md`](../todo/README.md) · [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md) · [`../DOCUMENTATION_WORKFLOW.md`](../DOCUMENTATION_WORKFLOW.md) · [`../PROJECT_CROSSWALK.md`](../PROJECT_CROSSWALK.md)
- OpenTechnologyApp, read-only sources: `docs/agent-registries/README.md`, `docs/readable/AUDIT_WORKFLOW.md`, `docs/readable/MANUAL_TESTING_WORKFLOW.md`, `docs/readable/FUTURE.md`, `docs/readable/FUTURE_STATE.md`, `docs/proposals/PRIORITY.md`, `docs/proposals/WORK_INTAKE_SOP.md`, `.claude/commands/audit.md`, `.claude/commands/pre-merge.md`, `.claude/commands/daily.md`, `scripts/verify-all.ts`, `scripts/generate-agents-md.ts`

### Testing queue follow-up — 2026-10-12

Owner requested grouping mostly-testing proposals and making remaining features visible.
Assignment remains `gpt-6.1-sol` / `high`. Moved twelve current In progress rows into Testing
(seven mainly acceptance, five with configuration/features/content delivery left); retained
P-005 and P-056 in the implementation section. Canonical states, assignments, admission
conditions and evidence are preserved. No duplicate proposal rows or completion claims.
The SOP and owner-lane index explain placement; the generated registry is refreshed.
An in-conversation selector uses these reviewed fourteen current-work items, with actual
blockers and concrete next slices rather than invented completion percentages.
Verification: required `PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test` reached
100%, exit 0 (`/tmp/hcp-testing-section-offline.log`). Proposal/lane `--check --summary`
passed with 73 rows, 14 In progress and 43 Done preserved; the Testing section contains
12 unique rows and every one names remaining work and its next test. Generated docs were
regenerated and `--check` passed; `git diff --check` passed. The visual rendered in the
browser, changing selection updated the detail/next slice, selection survived reload, and
layouts were checked at 736px and 360px. No proposal was completed or runtime action taken.

## Proposal dashboard tracking

**Owner request:** 2026-10-12 — redo the queue breakdown with Testing and track the dashboard
in a proposal document. This is a bounded follow-up under P-071; the approved phases 1–5
remain Done. **Assignment:** `gpt-6.1-sol` / `high`, inherited from P-071 for queue semantics,
derived counts and verification. The task cannot independently switch its execution model.

### Dashboard contract

The dashboard reads the canonical [proposal queue](../PROPOSALS.md), rather than maintaining
another backlog. Its work breakdown uses the queue's sections: Accepted, In progress (build),
Testing, Pending, Deferred, Done and standing practices. Testing remains an **In progress
state** for authorization and completion; the dashboard must not count those rows twice.
The legacy state counts remain available separately for compatibility.

Within Testing, show **Mainly acceptance** and **Testing with remaining features or delivery**.
For a selected item, expose what is proven, remaining build/delivery, next acceptance check,
prerequisites, agent assignment and a bounded next slice. Never invent completion percentages,
effort estimates or permission to perform external actions. A selected slice is a request,
not evidence that execution occurred or that a model was switched.

### Current breakdown — 2026-10-12

| Queue work section | Proposals |
|---|---:|
| Done | 43 |
| Testing | 16 |
| In progress — substantial build | 0 |
| Accepted | 0 |
| Pending | 7 |
| Deferred | 5 |
| Standing practices | 2 |
| **Total** | **73** |

Testing comprises **7 mainly acceptance** and **9 with remaining features or delivery**.
There are **28 unfinished** proposals. The separate authorization-state view still has
16 In progress (16 Testing + 0 build); those 16 must not be added again to the table above.

### Implementation and update tracker

- [x] Testing section with remaining work and next acceptance checks in the queue.
- [x] Reviewed in-conversation work selector for source-derived current-work items.
- [x] Machine-readable `work_counts`, `testing_counts` and per-row `work_focus`, with existing state fields preserved.
- [x] Refreshed full-queue breakdown in conversation, including accepted/pending/deferred/done/standing sections.
- [x] Verify count reconciliation, Testing admission rules, existing report compatibility and generated registry freshness.
- [x] Checked-in browsable dashboard and editable source/receipt, linked from docs index and canonical queue (owner follow-up 2026-10-12).
- [ ] Future scope: automatic dashboard regeneration and CI freshness checks. The checked-in page is a dated snapshot.

**Refresh procedure:** run `make proposal-report ARGS='--check --summary'`; reconcile this dated
snapshot and the visual against its work counts after queue changes. Preserve full states and
canonical gates. Run `python3 scripts/testing/generate_docs.py --write` after canonical queue
changes and inspect the generated registry. A future generated page should consume this same
report and fail on duplicate IDs, stale snapshots or section totals that do not reconcile.

**Inputs and proof:** `scripts/testing/proposal_report.py`,
`tests/docs/test_local_verification.py`, the canonical queue and owner lane map. The new report
checks fail against the old implementation; after implementation run them, Ruff, generated docs,
proposal/lane checks and the required `make test`. No app, runtime service or account is changed.

**Dashboard verification — 2026-10-12:** three new report checks failed against the old
implementation (3 failed, 11 passed) and all 14 verifier/report checks passed afterward.
The actual report returned work counts 43 Done, 12 Testing, 2 build, 2 Accepted, 7 Pending,
5 Deferred and 2 standing; Testing split 7/5 and all work counts reconcile to 73. Legacy
state counts retain 14 In progress. Proposal/lane check, Ruff and generated-doc freshness
passed. Required `PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test` reached 100%,
exit 0 (`/tmp/hcp-dashboard-offline.log`). The local browser showed Testing's twelve items,
Build's two items and Pending's seven after selection; layouts were inspected at 736px/360px.
The inline snapshot reads this actual report and preserves canonical IDs, states and assignments.
No persistent dashboard page, website hosting or runtime work is claimed by this follow-up.

**Work-focus update — 2026-10-12:** P-005's fixed executable scenario runner passed its
available contract scenarios and moved to Testing with remaining dependency/acceptance work.
At the workflow-runner handoff, the work breakdown was 13 Testing / 1 active build; historical
verification snapshots earlier in this document retain their original counts. P-056 still
needs a permitted game environment and reference workstation plus its remaining native/game
implementation; its diagnostic command does not close those gates.

P-056 bounded native/game/rig integration moved to Testing on 2026-10-12. Current work
counts are 14 Testing / 0 active build; earlier verification snapshots retain their counts.
Real phase evidence and dependent expansion remain open, with no Done promotion.

The latest canonical report also includes the independently closed P-065/P-066 build slices:
16 Testing (7 mainly acceptance, 9 remaining work), 0 active build and 0 Accepted; total 73.

### Hybrid Platform / MyFeed proposal selector — 2026-10-12

Owner requested the proposal visual and Testing option for both projects. This bounded P-071
follow-up retains Sol/high and existing authorization states. It refreshes the Hybrid queue
snapshot and adds a project selector, all work sections, Testing subgroup selection, exact
proposal IDs, source-based status/next-step/proof limits and a Discuss next slice action.
Selection is local presentation; a discussion request does not start live tests or grant
publishing, account, game or paid-AI permission. The visual remains a conversation snapshot;
the future committed self-refreshing page above remains separate scope.

MyFeed's existing canonical `docs/readable/PROPOSAL_WORK_QUEUE.md` now owns explicit Work view
and Next step fields for all 35 items and a Testing admission policy. Its 24 implemented/local
specifications versus 11 remaining baseline is preserved. Eleven work-view items need mainly
acceptance (eight already built locally); 16 are Implemented locally, seven Conditional, one
Unsupported. Exact item execution models are not inferred from MyFeed's coordination labels.
Its queue links `docs/readable/PROPOSAL_DASHBOARD.md` for tracking; no product runtime changed.

Hybrid's snapshot has 73 proposals, 16 Testing (7 mainly acceptance / 9 remaining work),
43 Done, 7 Pending, 5 Deferred and 2 standing. No active-build/Accepted rows are invented.
Refresh both source queues after changes, reconcile every work-view count to its own total,
and retain dated statuses/dependencies and NOT RUN/provider/asset/hardware gates.

Verification for this selector: both source-derived work views reconcile (Hybrid 73 / MyFeed
35), MyFeed's 35 ordered IDs and dated statuses match its HEAD and 50 maintained links/anchors
resolve. Browser checks passed project switching, selected proposal details, subgroup filters,
empty-group behavior and selection persistence after reload. 736px/360px viewports showed no
horizontal overflow. Native display positioning was NOT RUN because the Mac was locked;
no physical acceptance is claimed. Hybrid make test reached 100%, exit 0; proposal/lane,
generated-registry and diff checks pass. MyFeed docs generation/synchronization and diff checks
pass. No application/store/provider action or proposal completion occurred.

### Documentation integration and merge handoff — 2026-10-12

Owner requested working the selector into both projects’ docs. The [dashboard](../proposal-dashboard.html)
and [workflow/refresh guide](../PROPOSAL_DASHBOARD.md) are checked-in documentation assets,
with editable source and source-hash/count receipt. MyFeed carries its own exported page and
tracker. Prepare work request generates local handoff text; it never sends to another task.
Existing dated conversation-only statements above record earlier slices; this follow-up adds
persistence in the repositories without hosting or changing product/runtime behavior.

Documentation-export proof: both saved pages load with their repository's default project;
Prepare work request exposes a read-only local request without task messaging. MyFeed's empty
remaining-feature filter disables request preparation, and PROP-031 selection survives reload.
Both receipts match canonical queue SHA-256 values; 73/35 unique ordered IDs and work counts
reconcile; 96 documentation links resolve. Generated docs, queue/lane report and diff checks
pass. Required full make test reaches 100%, exit 0 (`/tmp/hcp-doc-dashboard-integration.log`).
No application runtime, live acceptance or Git merge was performed by this export.
