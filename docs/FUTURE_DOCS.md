# Future documents — proposed docs and their state

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**Enforcement: reference.** This is the registry of documents this repository does not have yet, plus
the ones the document-gap proposal ([P-071](proposals/PROPOSAL_DOCUMENT_GAPS.md)) builds. It answers
one question — *what documentation is missing, and what state is it in?* — which is distinct from
[`architecture/future.md`](architecture/future.md) (features deferred, each with a trigger) and
[`architecture/future-state.md`](architecture/future-state.md) (the compass). It will keep growing as
proposals are added; that is expected.

It authorizes nothing. A proposed document becomes work only through a [queue row](PROPOSALS.md).

## State vocabulary

| State | Meaning |
|---|---|
| **Built** | Exists in the tree and its links resolve |
| **Proposed** | Named and scoped, not written. Has a trigger that has fired or a concrete next step |
| **Deferred** | Wanted eventually; waits on a trigger that has not fired |
| **Rejected** | Considered and declined. The reason is recorded so it is not proposed again |

An entry without a trigger or a reason is a wish, not a decision. Rejected entries stay.

## What was copied from OpenTechnologyApp's future docs — and what was not

OpenTechnologyApp keeps a feature backlog (`FUTURE.md`) and a target-state compass
(`FUTURE_STATE.md`). This repository already had that split ([`architecture/future.md`](architecture/future.md)
and [`architecture/future-state.md`](architecture/future-state.md)), so the transferable part is the
**mechanism**, not the text:

| Mechanism | In OpenTechnologyApp | Here |
|---|---|---|
| An intake banner at the top of each future doc: *this is an idea source, not a queue or an authorization — route work through the intake rule* | On both files | **Added to both** (FD-05) |
| Future docs are **read by the audit**, which appends a one-line "furthest pillar and highest-leverage move" | `/audit` and `/daily` read them | **Proposed** (FD-11). The compass now says plainly that nothing reads it automatically yet |
| Stale claims are corrected in place, struck through and dated | `CORRECTED 2026-07-21` entries | **Followed**: the compass's stale module count is corrected with its date (FD-05) |
| A candidate-intake table marked *direction, not approval* | In `FUTURE_STATE.md` | **Already present** in `future-state.md`; unchanged |
| Owner-only external actions kept out of the implementation backlog | *Operator action handoffs* in `PRIORITY.md` | **Built** as the [decision and run lanes](todo/README.md) (FD-01–FD-03) |

**Not copied:** the content — monetisation, an ITSM replacement path, serverless hardening. It is
specific to that product (FD-26).

## Registry

Source models are files in OpenTechnologyApp under `docs/readable/` unless a path is given. "Trigger
fired" means the condition that should reopen the question has already happened, with the evidence.

### Built by P-071

| ID | Document | Answers | Source model | State | Trigger or next step |
|---|---|---|---|---|---|
| FD-01 | [Lane index](todo/README.md) | What is waiting on a person, in which lane, and how do I add to it? | *Operator action handoffs* in `PRIORITY.md` | **Built** | Grows by one row per item |
| FD-02 | [Content create to-do](todo/CONTENT_CREATE_TODO.md) | Which content decisions and runs are open? | — (suggested by the owner) | **Built** | Grows with proposals |
| FD-03 | [Stream decisions and to-do](todo/STREAM_DECISIONS_AND_TODO.md) | Which stream decisions, live runs and tests are open? | — (suggested by the owner) | **Built** | Grows with proposals |
| FD-04 | This registry | What documentation is missing, and in what state? | — | **Built** | One row per proposed document |
| FD-05 | Intake banner and corrected metric in [`future.md`](architecture/future.md) and [`future-state.md`](architecture/future-state.md) | Where does a future idea go, and is the compass current? | `FUTURE.md`, `FUTURE_STATE.md` | **Built** | — |

### Gates and generated documents

| ID | Document | Answers | Source model | State | Trigger or next step |
|---|---|---|---|---|---|
| FD-06 | **One-command local verify** — a `make verify` target plus a row in the [verification matrix](agent/VERIFICATION-MATRIX.md). Proposed contract: read the CI workflow at run time rather than keeping a hand-copied list, refuse to report a clean run if it parses fewer steps than a stated minimum, and print an explicit *not run* list for anything needing hardware, accounts or a real database | Did I run everything CI runs? | `verify-all.ts`, generated from the CI workflow, with a tripwire | **Built — 2026-10-08** | **Trigger fired:** CI could not run at all until the billing block cleared, and six PRs merged on 2026-09-26 on local suites alone. P-071 phase 3 implemented and locally verified; installer/service/hardware checks remain explicit NOT RUN |
| FD-07 | **Generated `AGENTS.md`** — one instruction file written, the other generated from it, with a check | Are the two agent instruction files the same? | `generate-agents-md.ts`, written because `AGENTS.md` "had silently fallen behind on rules" | **Built — 2026-10-09** | **Trigger fired:** the two files are hand-kept; the pairing test covers only §4 and §11, so `AGENTS.md` §12 listed six pointers where `CLAUDE.md` §12 listed fifteen — no queue, no matrices, no parking lot, and a pointer to the retired "All guides" (synced by this change); and §3 of both still calls the apps' OBS and ComfyUI commands "still stubbed", which P-054 (`Done`) and P-055 (code done) contradict. Needs owner decision OD-3 |
| FD-08 | **Generated-registries directory** — files that are generated, never hand-edited, and checked by regenerating. First candidate: the [doc update matrix](agent/DOC-UPDATE-MATRIX.md) rules held as data | Is this table still what the data says? | `docs/agent-registries/README.md` | **Built — 2026-10-09** | **Trigger fired:** [`agent/README.md`](agent/README.md) says "none of it fires automatically" and the matrix says "no CI posts this" |
| FD-09 | **Generated rows in the project crosswalk** — module-to-proposal links derived from the queue and module READMEs | Is the crosswalk current? | The registries above | **Built — 2026-10-09** | After FD-08. [`PROJECT_CROSSWALK.md`](PROJECT_CROSSWALK.md) states it has no regeneration command |
| FD-10 | **Docs gate workflow** — a CI job that regenerates the generated docs and fails on a difference | Did a hand-edit survive? | `doc-matrix.yml` | **Built — 2026-10-09** | After FD-08, and after CI health is green (ST-T13) |
| FD-21 | **Machine-readable proposal registry and queue check** — and the same check diffs open queue rows against the [lane map](todo/README.md#queue-to-lane-map) | Does every row's section match its state, and does every open row have a lane? | `proposal-registry.json` and its validator | **Built — 2026-10-09** | **Trigger fired:** four `Done` rows sit under "Pending — candidate modules" and the "Accepted — build-out work" section is mostly `Done`. Two of this change's own rows used a state outside the six. Today the only check is that every proposal document has a row Runtime JSON checker, state-grouped queue, extracted history and generated registry now verified. |
| FD-22 | **Queue hygiene pass** — an edit, not a document: move `Done` rows to `Done`, keep to the six states, and move P-063's roughly 450 lines of inline slice history into its own proposal, and correct P-064's row, whose sentence that `validate` "still exits 1" is no longer true | — | — | **Built — 2026-10-09** | Waits for another session's uncommitted `PROPOSALS.md` edits to land; a large move now would conflict with them |
| FD-23 | **Work intake SOP** — an intake record (source, evidence, candidate parent, result) and the result categories, including *owner-only external action*, which the lanes now cover | Where does this item go? | `WORK_INTAKE_SOP.md` | **Proposed** | A third lane, or lane rules that outgrow a page |

### On-demand audits and testing documents

| ID | Document | Answers | Source model | State | Trigger or next step |
|---|---|---|---|---|---|
| FD-11 | **Audit command and capped log.** Tiers — quick: run the gates and read the open items; standard: plus a documentation sweep and a **future-state gap pass** naming the furthest pillar; deep: plus a security and code review. Read-only on code. A log capped at the last ten entries | Where are we, right now, against the compass? | `.claude/commands/audit.md`, `AUDIT_LOG.md` | **Instructions/log built — 2026-10-08** | P-071 phase 4, after FD-06 (the quick tier *is* `make verify`) |
| FD-12 | **Run evidence log** — one dated record per completed lane run: commands, numbers, failures, files | Where does a closed run's evidence live? | `testing/manual-evidence/` | **Proposed** | The first lane run completes (ST-R01). Until then, record in the owning proposal |
| FD-13 | **Pre-merge command** — branch and PR state first (behind `main`? worktrees mid-work? is the proposal number already claimed, including in another session's uncommitted queue edit? is a stacked PR's base branch about to be deleted?), then the gates, then queue bookkeeping | Is this ready to push? | `.claude/commands/pre-merge.md`, written after three round trips "each catchable locally first" | **Instructions/log built — 2026-10-08** | **Trigger fired three times:** PR #44 was permanently closed when #43's merge deleted its base branch; P-066 was claimed by two proposals at once (2026-09-26); P-070 was claimed in another session's uncommitted edit while this was being written (2026-10-04) |
| FD-14 | **Manual testing workflow** — how an owner-run live test is performed and recorded, what only a manual run can catch, and the credential rule (the owner signs in; an agent never types a secret) | How do I run a live test properly? | `MANUAL_TESTING_WORKFLOW.md` | **Proposed** | ST-R01 done, so there is a first run to write from. The lane docs are its ordered owner-action list |
| FD-15 | **Voice A/B runbook** — one procedure merging P-067 §7.5 and P-068 §6.1, with a blind-order sheet and a results table | Which voice, and is Nova still Nova? | — (a new need) | **Proposed** | CT-D03 answered, so an ElevenLabs account exists |
| FD-16 | **Stream performance and pressure test plan** — P-056's gates and A1–A11 as a runnable procedure with a budget and an A-row → test → result table | Does the host hold up under load? | `PRESSURE_TEST_LOAD.md` and siblings. Here [`PRESSURE_TEST_LOAD.md`](PRESSURE_TEST_LOAD.md) exists but records no measured numbers | **Proposed** | ST-D11 answered, so a reference workstation is declared |
| FD-17 | **Incident runbooks** — stream and creator recovery as standalone documents | What do I do when it breaks live? | `docs/runbooks/` | **Proposed** | The first live go-live rehearses them (ST-T10). Today they live inside the two production guides |

### Deferred

| ID | Document | Answers | Source model | State | Trigger or next step |
|---|---|---|---|---|---|
| FD-18 | **Scheduled audit workflow** | Does it still pass, unattended? | `weekly-e2e.yml`, `org-audit.yml` | **Deferred** | CI health green **and** a live acceptance suite worth scheduling |
| FD-19 | **Finding ledger and audit workflow** — fingerprinted findings, a triage clock, a routing chain | Has this been found before? | `AUDIT_WORKFLOW.md`, `AUDIT_FINDING_LOG.md` | **Deferred** | Two audits produce the same finding |
| FD-20 | **Bug tracker and bug creation SOP** | Where do defects live? | `BUG_TRACKER.md`, `BUG_CREATION_SOP.md` | **Deferred** | The first escaped defect found by live acceptance. Default: extend [`GAP_AUDIT.md`](GAP_AUDIT.md) (OD-4) |
| FD-24 | **Session handoff** — branch, uncommitted work, claimed numbers | What did the last session leave? | `HANDOFF.md` | **Deferred** | The next collision between parallel sessions. Two so far; the shared checkout currently holds another session's uncommitted edits to files this change also edits |
| FD-25 | **Platform decisions lane doc** (`docs/todo/PLATFORM_DECISIONS.md`) | The same as the lane docs, for license, OS matrix, API trust and infrastructure images | — | **Deferred** | The platform table in the [lane index](todo/README.md) passes about ten live rows |

### Rejected

| ID | Document | Why not | State |
|---|---|---|---|
| FD-26 | A verbatim copy of OpenTechnologyApp's `FUTURE.md` and `FUTURE_STATE.md` | Their content is product-specific — monetisation, an ITSM replacement path, serverless hardening. What transfers is the mechanism, which FD-05 took | **Rejected** |
| FD-27 | A copy of OpenTechnologyApp's `MODEL_ROUTING_POLICY.md` | [`../AGENTS.md`](../AGENTS.md) §13 links to it as the tier-table authority. A copy would drift — the same reasoning as the marketing pointer documents | **Rejected** |
| FD-28 | An autonomous daily routine that builds features unattended | The owner is the acceptance step for this repository's live paths, and nothing on them can be proven by an unattended run. Revisit only through owner decision OD-5 | **Rejected** |

## Adding to this registry

One row per proposed document, with a state and a trigger or a reason. Rows are never deleted: a
built document keeps its row as **Built**. When a document is written, change its state in the same
change that adds the file, and add it to the [documentation index](README.md).

## Related

- [`proposals/PROPOSAL_DOCUMENT_GAPS.md`](proposals/PROPOSAL_DOCUMENT_GAPS.md) — why these gaps, the evidence, and the phase order (P-071).
- [`todo/README.md`](todo/README.md) — the decision and run lanes.
- [`DOCUMENTATION_WORKFLOW.md`](DOCUMENTATION_WORKFLOW.md) — how to prepare or refresh a document.
- [`PROPOSAL_CREATION_SOP.md`](PROPOSAL_CREATION_SOP.md) — the form a proposal takes.
