# Proposal: Redesign from the OpenTechnologyApp pattern — a design-parity audit of content and document structure

> Copied from [`TEMPLATE_PROPOSAL.md`](TEMPLATE_PROPOSAL.md). **Numbers live in the queue, not in the
> filename.** The owner named this file `REDESIGN_FROM_OPENTECHAPP_PATTERN.md`. It carries the
> `PROPOSAL_` prefix because the queue-row and model checks in `tests/docs/` select proposal
> documents by that prefix, and an unprefixed file would be exempt from both.

**Queue row:** `P-074`
**Agent model / effort:** `gpt-6.1-sol` / `medium` — Scoped instruction, skill, banner and docs-gate additions with objective checks; no native or credential code
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `In progress` — requested as "Proposed" and queued as `Pending` on 2026-10-22 (the queue has six states and that word is not one of them). On 2026-10-24 the owner directed that the items needing no owner input ship, so five of the eight additions are built, in whole or part, and the rest wait on the gates in §12.1a. State is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md), not here
**Owner:** OpenTechnology14 + agent
**Date:** 2026-10-22
**Roadmap layer(s):** None — process and documentation; no new module
**Evidence level:** *Verified (read)* for OpenTechnologyApp at `d2467d8` and MyFeed at `a7eaf28`: read with `git show` and `git grep`, none of their scripts run. *Verified* for this repository at `54266fc`. *Inferred* for how long the App rows stay true. *Proposed* for everything from §6 on

## 1. Executive summary

**Top line: Hybrid already matches OpenTechnologyApp on every pattern the App itself names as its
template-of-record, so no restructure is warranted.** Of 27 patterns compared (§2.2), **7 match, 9 are
partial, 5 are missing and 6 do not apply**. Of the 14 partial or missing, **8 are worth closing, 4 are
better left, and 2 are already registered** in [`FUTURE_DOCS.md`](../FUTURE_DOCS.md) with triggers. The
recommended redesign is eight small additions — seven small, one medium — behind ten owner decisions
(`HYB-REDESIGN-D01` to `D10`, §12.1). None of it touches Hybrid's registry authority or the design-system hub.

Five findings corrected or reframed the request's premises, and each changed the answer:

1. **The App has no voice-register section.** A search of the App for "voice register", "voice and tone",
   "brand voice" and "tone of voice" finds one unrelated source file and nothing in its documents; its
   `MARKETING.md` mentions voice only for lead emails. Voice registers are Hybrid's —
   [`design-system/voice-and-tone.md`](../../design-system/voice-and-tone.md), merged in PR #82 — and
   MyFeed's pointer already inherits them. That row is N/A and the direction of travel is App to Hybrid.
2. **The App's template-of-record is narrower than the request's list.** `App:docs/design/BUILD-PROMPTING-DIGEST.md`
   §2 records an owner decision (2026-10-20) naming four things: a root `MARKETING.md` with fixed numbering,
   a pointer rather than a copy of the single module registry, a companion ledger that states a tie-break,
   and an engineering crosswalk. Hybrid has all four.
3. **`docs/readable/` is a two-repo habit, not a template.** The App has 33 documents there and MyFeed 17;
   only 3 file names are shared. Hybrid already keeps nine of the App's file names (beyond `README.md`) flat
   in `docs/`, and its generated half is already split out as `docs/agent-registries/`. A rename moves 22
   documents and every inbound link for no content parity.
4. **MyFeed is a selective mirror, so it is weak evidence for "adopt everything".** It took `docs/readable/`,
   `docs/agent-registries/`, four skills, the design pointer and a verify script. It has no `MARKETING.md`,
   PR template, `CONTRIBUTING.md`, commands or `when_to_use` frontmatter, and its `CLAUDE.md` tells agents not
   to copy App infrastructure without a concrete need.
5. **P-071 already ran this comparison for document mechanisms** (gap table G1–G12, registry FD-01 to FD-28,
   `Done` 2026-10-09). This proposal is a delta on that work: five of the seven matching rows were built by it,
   and two more rows are registered there.

| The request asked for | Where it is |
|---|---|
| 1. Audit matrix (Match / Partial / Missing / N/A) | §2.2 |
| 2. Gaps worth closing, ranked, with effort | §10.1 |
| 3. Gaps worth leaving | §10.3 |
| 4. Scope boundaries | §3.4 |
| 5. Decision gates `HYB-REDESIGN-D01` … | §12.1 |
| 6. Status: Proposed, appended at the bottom of the queue | header above, and the last row of the [Pending table](../PROPOSALS.md#pending) |

The smallest shippable result is this document plus its queue row and lane row. **No code, skill or
instruction change is proposed for merge here.**

## 2. Verified current state

### 2.1 Sources and method

| Source | Ref | How read | Called |
|---|---|---|---|
| OpenTechnologyApp (private) | `origin/main` at `d2467d8`, 2026-10-22 | `git show`, `git ls-tree`, `git grep` on the local clone | **App** |
| MyFeed (private) | `origin/main` at `a7eaf28`, 2026-10-21, after its PR #13 | same | **MyFeed** — the reference mirror |
| This repository | `54266fc`, `main` after PR #82 | read, counted, tests run | **Hybrid** |
| Claude Code skill documentation | `https://code.claude.com/docs/en/skills`, fetched 2026-10-22 | web fetch; the first 100,000 of 114,484 characters read | source for the `when_to_use` and `paths` fields (§7.2) |

Paths written `App:` or `MyFeed:` are in those repositories. Three measures are heuristics and are labelled so:
**name overlap** compares file names only, not contents; **status header** means a file's first 15 lines hold a
line starting `Status`, `Last reviewed` or `Last verified` (optionally after `**` or `> **`); **banner** means a file
holding a line that is exactly `<!-- PROPOSAL_WORK_INTAKE -->`.

```bash
# Reproduce the counts (A = App clone, M = MyFeed clone, run from the Hybrid root)
git -C "$A" ls-tree --name-only origin/main docs/readable/ | grep -c '\.md$'                 # 33
git -C "$M" ls-tree --name-only origin/main docs/readable/ | grep -c '\.md$'                 # 17
git -C "$A" grep -l '^<!-- PROPOSAL_WORK_INTAKE -->' origin/main -- docs '*.md' | wc -l      # 18
grep -rl --include='*.md' '^<!-- PROPOSAL_WORK_INTAKE -->' docs | wc -l                      # 2
git -C "$A" ls-tree --name-only origin/main .claude/skills/ | wc -l                          # 7
ls .claude/skills | wc -l                                                                    # 5
```

Legend: **Match** — the same mechanism exists and works. **Partial** — the purpose is served but the mechanism or
coverage differs. **Missing** — the purpose is unserved and nothing equivalent exists. **N/A** — does not apply to
Hybrid, either because Hybrid is the authority or because the pattern is product-specific. *none* — examined and
absent; a bare dash — not examined.

### 2.2 Audit matrix

**Part A — the eight patterns the request names.**

| ID | Pattern | App | MyFeed | Hybrid today | Verdict | Disposition |
|---|---|---|---|---|---|---|
| A1 | `MARKETING.md` playbook | Root file, fixed §1–§8: positioning, ICPs, channels 3a–3f, content engine, cadence, funnel, first 30 days, mistakes | none | Root file with the same §1–§8 numbering plus a Hybrid-only §3g (live streams); registered as a `marketing_playbook` doc in `targets.yml` and checked by `tests/marketing_crosswalk/test_playbook.py` | **Match** | — |
| A2 | `docs/readable/` beside generated `docs/agent-registries/` | 33 hand-written documents; 12 entries in the generated directory, whose README forbids hand edits | 17 documents (3 share a name with the App's); registries directory present | No `docs/readable/`. 22 hand-written documents sit at `docs/` top level, 10 sharing a name with an App readable or registry document; the generated half is already split out (`docs/agent-registries/`: README and `documentation.json`) | **Partial** — split exists, directory name differs | Leave (§10.3.2, D03) |
| A3 | PR template | `.github/pull_request_template.md` (what changed, why, validation, proposal bookkeeping, docs advisory) plus a blocking `bookkeeping` job that reads the PR body | none; also no `CONTRIBUTING.md` | No template; `.github/` holds five workflows. The standard is one paragraph in `CONTRIBUTING.md` ("Pull request description": outcome, layer, exact verification, privacy and security, docs, rollback, blocked checks) | **Partial** — standard exists, template and check do not | Close (R8, D10) |
| A4 | Proposal queue format | `PRIORITY.md` for order, `proposal-registry.json` as source of truth, a validator, `WORK_INTAKE_SOP.md`, IDs such as `AICONN-01` | `PROPOSAL_WORK_QUEUE.md` and a dashboard in `docs/readable/`; `PROP-NNN` IDs | `docs/PROPOSALS.md`: six status-sectioned tables, permanent `P-NNN`, owner-only acceptance, a model and effort column; `proposal_report.py --check` diffs the queue against the lane map (FD-21) | **Partial** — three repos, three formats; Hybrid's is machine-checked | Leave (§10.3.2, D02) |
| A5 | Voice register section | **No such section** (search in §1, finding 1) | Pointer only; inherits the hub's register | `design-system/voice-and-tone.md` (registers, never names), the `design` skill, `docs/design/BUILD-PROMPTING-DIGEST.md` | **N/A** — nothing to adopt; Hybrid is the source | — |
| A6 | Marketing module structure (digest §2: fixed numbering; pointer-not-copy; companion ledger with tie-break; engineering crosswalk) | Template-of-record for this shape only, by owner decision 2026-10-20 | none | Numbering as A1; the single registry is `modules/marketing-crosswalk/crosswalk/modules.yml`, and `MARKETING.md` states that the registry wins where a table repeats it; engineering crosswalk is `docs/PROJECT_CROSSWALK.md` with generated rows (FD-09) | **Match** | — |
| A7 | Crosswalk pointer pattern | `App:docs/readable/MARKETING_CROSSWALK_POINTER.md` points at Hybrid's `modules.yml` | `docs/design/DESIGN-SYSTEM-POINTER.md` (PR #13), hub-pending | Hybrid is the authority; `design-system/crosswalk/consumers.md` names the expected pointer path per consumer | **N/A** as consumer; hub side **Match** | — |
| A8 | Verify-script discipline | `npm run verify:all`, generated from `ci.yml`, with a minimum-steps tripwire and a NOT RUN list | `npm run verify` | `make verify` (`scripts/testing/verify.py`) runs the recognised CI gates and lists every NOT RUN check (FD-06); `make proposal-report`; `generate_docs.py --check` | **Match** | — |

**Part B — other App conventions found while reading.**

| ID | Pattern | App | MyFeed | Hybrid today | Verdict | Disposition |
|---|---|---|---|---|---|---|
| B1 | Generated agent-instruction mirror | `AGENTS.md` generated from `CLAUDE.md` by `scripts/generate-agents-md.ts`, CI-checked | both files exist; generation not checked | `AGENTS.md` generated from `CLAUDE.md` by `scripts/testing/generate_docs.py --write`; `--check` enforced by the offline suite and CI (FD-07) | **Match** | — |
| B2 | Generated-registries directory | `docs/agent-registries/`, 12 entries including the doc-update matrix, route ledger and skill matrix | directory present | `docs/agent-registries/`: README and `documentation.json` (FD-08) | **Match** (smaller set) | — |
| B3 | Owner-run actions kept out of the backlog | "Operator action handoffs" in `PRIORITY.md` | — | `docs/todo/` lane index and two lane docs, with a queue-to-lane check (FD-01 to FD-03, FD-21); the lane index credits the pattern | **Match** | — |
| B4 | Intake banner on parking-lot and compass documents | `FUTURE.md`, `FUTURE_STATE.md` | — | `docs/architecture/future.md` and `future-state.md` carry the marker (FD-05) | **Match** | — |
| B5 | Intake banner on audit ledgers, matrices, trackers and test plans | 18 documents carry the marker; the marker is defined in `App:scripts/audit-proposals.ts` | — | 2 documents carry it. Ten comparable documents carry none: `AUDIT.md`, `GAP_AUDIT.md`, `API_ROUTE_AUDIT_LEDGER.md`, `FULL_APPLICATION_AUDIT_MATRIX.md`, `CONTINUOUS_IMPROVEMENT.md`, `IMPLEMENTATION_NOTES.md`, `PRESSURE_TEST_LOAD.md` (all in `docs/`), root `TESTING.md`, `tests/ACCEPTANCE-CHECKLIST.md`, `tests/USE-CASES.md` | **Partial** | Close (R3, D08) |
| B6 | Work-intake SOP | `App:docs/proposals/WORK_INTAKE_SOP.md` (intake record, result categories, Step 5b) | — | None; the lane index's intake rule covers owner decisions only. FD-23 is `Proposed` and its trigger ("a third lane, or lane rules that outgrow a page") has not fired | **Missing** | Registered (FD-23) |
| B7 | Status and last-reviewed header | 21 of 33 `docs/readable/` documents | 0 of 17 | 11 of 22 top-level `docs/*.md`; the other 11 are `API_ROUTE_AUDIT_LEDGER`, `AUDIT`, `CONTINUOUS_IMPROVEMENT`, `FULL_APPLICATION_AUDIT_MATRIX`, `GAP_AUDIT`, `IMAGE_INTAKE`, `IMPLEMENTATION_NOTES`, `OPEN_SOURCE_RELEASE_CHECKLIST`, `PRESSURE_TEST_LOAD`, `PROPOSAL_DASHBOARD` and `PUBLIC_DOCS_AND_MARKETING_REVIEW`. `test_living_docs_declare_status_and_enforcement` enforces it for `docs/agent/*.md`, `SETUP-TECHNIQUE-NOTES.md` and `PROPOSALS.md` only | **Partial** | Close (R5, D08) |
| B8 | Path-triggered doc-update matrix with a PR advisory | `doc-matrix.yml` and `scripts/check-doc-matrix.ts` post an advisory comment listing the documents mapped to the paths a PR touches | — | `docs/agent/DOC-UPDATE-MATRIX.md` rules (`DM-*`) are parsed into `documentation.json` and drift-checked, but their triggers are prose ("a new file under docs/"), not path globs, and nothing maps a diff to a rule | **Partial** | Close (R4, D07) |
| B9 | Project skills | 7: `agent-work`, `audits`, `code-creation`, `code-health`, `design`, `docs`, `security` | 4: `audits`, `code-creation`, `design`, `docs` | 5: those four plus `marketing-discovery`. No `security` skill; `agent-work` would duplicate `CLAUDE.md` §9; `code-health` is TypeScript, Tailwind and shadcn specific | **Partial** | Close the security half (R2, D05); `agent-work` not adopted (D04) |
| B10 | `when_to_use` skill frontmatter | 7 of 7 skills | 0 of 4 | 0 of 5; `tests/docs/test_agent_skills.py` pins the keys to exactly `name` and `description` | **Missing** | Close (R6, D05) |
| B11 | Skill matrix | `testing/skill-matrix.json` generates `docs/agent-registries/SKILL_MATRIX.md`; maps built-in skills to path globs; `scripts/check-skill-matrix.ts` checks coverage, broken references and shape; declared "reference", not a gate | — | none. `CLAUDE.md` §14 lists five skills with a "use when" sentence and no paths | **Missing** | Leave until a trigger (§10.3.2, D06) |
| B12 | Contribution workflow in the always-loaded instruction file | `CLAUDE.md` "Contribution workflow": never push to `main`; task branch and PR; separate worktree per agent; preserve changes you did not create; name behaviour changes; open the PR by the first push | — | `CLAUDE.md`, `AGENTS.md` and `CONTRIBUTING.md` contain no worktree or branch rule (searched at `54266fc`). The rule exists only inside the `code-creation` skill and `.claude/commands/pre-merge.md` | **Missing** | Close (R1, D04) |
| B13 | Commands layer | 5: `audit`, `bug-sweep`, `daily`, `migration-check`, `pre-merge` | none | 2: `audit`, `pre-merge` (FD-11, FD-13) | **Partial** — by design | Leave (§10.3.2) |
| B14 | Testing and operations documents: manual testing workflow, bug tracker and SOP, finding ledger, scheduled audits, runbooks, session handoff, pressure plans | present | `MANUAL_TESTING_WORKFLOW.md`, `MANUAL_TEST_RESULTS.md` | each registered with a state and trigger: FD-14, FD-16, FD-17 (`Proposed`); FD-18, FD-19, FD-20, FD-24 (`Deferred`) | **Missing** | Registered (FD-14 to FD-20, FD-24) |
| B15 | Proposal closing ritual (Revisit & Review, review notes, Step 5b) | present | — | `DM-PROPOSAL-DONE` and the row's verification record | **N/A** | — |
| B16 | Agent response-style directive | "Response style" section in `CLAUDE.md` | — | none | **N/A** | — |
| B17 | Hosted-app gates: migration safety, tenancy, CSRF, Stripe, Vercel | present | — | Hybrid's local-first equivalents are `CLAUDE.md` §7, §10, §13 | **N/A** | — |
| B18 | UI stack conventions: shadcn, Tailwind, strict TypeScript | present | — | `design-system/` and `CLAUDE.md` §6 | **N/A** | — |
| B19 | Proposal document template | 17 sections, with header fields "Verified against" and "Source intake", separate documentation and code injection maps, "Files intentionally unchanged", "Release gates and definition of done" and "First implementation slice" | `docs/design/proposals/TEMPLATE.md` for design proposals | 13 sections: one direct injection map, "Documentation updates", a delivery plan; no "Verified against", "Files intentionally unchanged" or "First implementation slice" | **Partial** | Close (R7, D09) |

**Part C — Hybrid has it, the App does not.** These are not scored; §10.3.1 explains why each stays Hybrid's.
The crosswalk registry and generator, the design-system hub, the voice-register framework, the Blender
production-job lifecycle, the Stream Extend and Creator Extend profiles with the show bible and Nova persona,
per-module `setup/manual.md` and `setup/automated.md` with Content and Stream labels, the proposal
model-selection policy, the lane index with proof markers, and the roadmap layers with the Kubernetes gate.

**Tally (Parts A and B).**

| Verdict | Part A | Part B | Total |
|---|---|---|---|
| Match | 3 | 4 | **7** |
| Partial | 3 | 6 | **9** |
| Missing | 0 | 5 | **5** |
| N/A | 2 | 4 | **6** |
| Total | 8 | 19 | **27** |

Dispositions of the 14 Partial and Missing rows: **close** 8 (A3, B5, B7, B8, B9, B10, B12, B19);
**leave** 4 (A2, A4, B11, B13); **already registered** 2 (B6, B14).

### 2.3 What the mirror adopted, and what is already registered

MyFeed took the directory names and the shared skills, and left the rest. That is the useful reading of
the mirror: the family adopts by need. **Registered, not re-proposed:** B6 is FD-23; B14 is FD-14, FD-16 to FD-20
and FD-24, each with a trigger in [`FUTURE_DOCS.md`](../FUTURE_DOCS.md). This proposal does not move any of those
triggers.

## 3. Problem, goals, and non-goals

### 3.1 Problem

The documents agree with the App's template-of-record, but three things still reach an agent late or not at all:
the branch and worktree rules (only inside one skill), the credential and capability rules (spread across four
places, loaded by nothing), and the instruction that a finding in an audit ledger becomes a queue row (stated in
two documents of about ten). Separately, the real risk of an audit like this one is over-correction — adopting
the App's shape because it is the App's.

### 3.2 Goals

Each is measured by a check in §9, and each is conditional on the gate in §12.1.

- `CLAUDE.md` carries a contribution-workflow section of 15 lines or fewer, and `AGENTS.md` mirrors it.
- Every document in the banner list (R3) carries the marker, enforced by a test that names the missing document.
- Every top-level `docs/*.md` carries a status header or sits on an explicit exempt list.
- A `security` skill exists, is sourced only from in-repo documents, and loads for the sensitive paths.
- Every skill carries `when_to_use` within the combined 1,536-character cap.
- A local command lists the `DM-*` rules a diff fires.

### 3.3 Non-goals

- No restructure: no directory rename, no change to the queue format, no change to `PROPOSALS.md` beyond one appended row.
- No copy of App content (FD-26, FD-27) and no reversal of the hierarchy.
- No CI workflow change and no billing or branch-protection change.
- No bug tracker, finding ledger, scheduled audit or session-handoff document (FD-18 to FD-20, FD-24).
- No new module, no code under a sensitive path, and no acceptance of this proposal by this proposal.

### 3.4 Scope boundaries

| Boundary | Held by | What this proposal does at it |
|---|---|---|
| Registry authority | `modules/marketing-crosswalk/crosswalk/` (`modules.yml`, `targets.yml`, `assets.yml`) | Nothing. No row, field or file in the registry changes, and Hybrid adds no pointer document for its own registry |
| Design-system hub | `design-system/` and the `design-system` registry row | Nothing. No token, component rule, voice register or consumer changes; `DM-DESIGN-SYSTEM` does not fire |
| Direction of authority | The App is template-of-record for the marketing-module *shape*; Hybrid is the registry and design authority | Borrows mechanisms, never content. No App text becomes authority for Hybrid |
| Modules | `modules/` | No module added or changed |
| Sensitive paths (`CLAUDE.md` §13) | `apps/*/src-tauri/**`, `modules/character-avatar/**`, credential config, cross-app shared crates, streaming and gameplay pipelines | No code in any of them. R2 writes *about* them as a skill and edits no path they cover |
| CI and billing | `.github/workflows/` | No workflow change. R4 and R8 name CI wiring as a later step that waits on CI executing steps again |
| The queue | `docs/PROPOSALS.md` | One row appended. No other row, section or state changes and nothing is reordered |
| Public-bound text | `design-system/voice-and-tone.md` rule; open-source release checklist | No real person is named as a voice and no private tooling is named |
| Authorization | The owner | This proposal is `Pending`; nothing starts until the owner accepts it (D01) |

## 4. User paths and states

| Path | Today | If accepted |
|---|---|---|
| Agent starts a change | Reads `CLAUDE.md` §9; the worktree and "preserve changes you did not make" rules are in the `code-creation` skill and `pre-merge.md` | Reads a short §16 in the always-loaded file; the detail stays in the skill |
| Agent edits a credential, capability or relay path | §13 names the paths and why; nothing loads on the path | The `security` skill loads on those paths in Claude Code and is found by description elsewhere; Codex reads it by pointer (§14) |
| Agent edits an audit ledger | The ledger does not say where a new finding goes | A banner points to the queue, the lanes and `FUTURE_DOCS.md` |
| Agent finishes a change | Reads `DOC-UPDATE-MATRIX.md` by eye | Runs the advisory; it lists the rules the diff fired and the documents to check |
| Contributor opens a PR (after P-002) | One paragraph in `CONTRIBUTING.md` | A template pre-fills the web form; agent-authored PRs are unchanged |
| A guard test fails | — | It names the document; the fix is the banner or header, not the test |
| Owner answers the gates | — | Replies `D01–D10 accept as recommended`, or lists exceptions; the answer is recorded in §12.1 first, then `PL-D15` resolves |
| Cancel or roll back | — | One `git revert` per phase (§11) |

## 5. Architecture and data flow

Everything stays in the repository: Markdown, YAML frontmatter and, at most, one standard-library Python
script (R4). No service, network, secret or OAuth scope.

| Concern | Authority | Effect of this proposal |
|---|---|---|
| State and authorization of work | [`../PROPOSALS.md`](../PROPOSALS.md) | One row appended |
| Rationale and contract | Proposal documents | This document |
| What waits on a person | [`../todo/README.md`](../todo/README.md) | One umbrella row `PL-D15` and one map row |
| Agent instructions | `CLAUDE.md`, with `AGENTS.md` generated from it | A §16 if D04 is accepted |
| Task playbooks | `.claude/skills/` | One new skill and one frontmatter field if D05 is accepted |
| Which documents a change should touch | [`../agent/DOC-UPDATE-MATRIX.md`](../agent/DOC-UPDATE-MATRIX.md), parsed into `documentation.json` | A `Paths` column if D07 is accepted |
| Marketing registry | `modules/marketing-crosswalk/` | Unchanged |
| Design system | `design-system/` | Unchanged |

**Idiom.** Where Hybrid adopts a mechanism it uses its own layout: a hand-written matrix in `docs/agent/`
parsed into `docs/agent-registries/documentation.json` by `generate_docs.py`. It does not copy the App's
JSON-first layout, because [`../agent-registries/README.md`](../agent-registries/README.md) says every file in that
directory is generated.

## 6. Direct injection map

| Location | Symbol/route/component | Before | Proposed change | Example | Verification |
|---|---|---|---|---|---|
| `docs/proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md` | this file | none | added by the pull request that carries it | — | `test_proposal_models.py`, `test_docs_integrity.py` |
| `docs/PROPOSALS.md` | `## Pending` table | ends at P-032 | append the P-074 row | the row | `make proposal-report ARGS='--check --summary'` |
| `docs/todo/README.md` | platform table; queue-to-lane map | last platform row is PL-D14; no P-074 | add the `PL-D15` umbrella row and a map row | — | same check |
| `docs/agent-registries/documentation.json` | source hashes | stale after the edits above | regenerated | — | `generate_docs.py --check` |
| **Phase 1a** `CLAUDE.md` | new §16 | no branch or worktree rule | at most 15 lines; `AGENTS.md` regenerates | §7.3 | `generate_docs.py --check`; paired-file test |
| **Phase 1b** `.claude/skills/security/SKILL.md` | new skill | none | sourced from `CLAUDE.md` §7, §10, §13, `SECURITY.md` and the API route ledger | §7.2 | `tests/docs/test_agent_skills.py` |
| **Phase 1b** `.claude/skills/*/SKILL.md` | frontmatter | `name`, `description` | add `when_to_use` | §7.2 | amended frontmatter test |
| **Phase 1b** `tests/docs/test_agent_skills.py` | `test_frontmatter_is_valid` | pins keys to exactly two | allow `when_to_use` and `paths`; cap the combined text at 1,536 characters | — | mutation run (T-07) |
| **Phase 2** ten source documents (B5) | first lines | none carries the marker | marker and link block | §7.1 | new guard (T-08) |
| **Phase 2** `tests/docs/test_work_intake_banner.py` | new | none | `REQUIRED` list, marker, and resolving links (the existing link test does not cover root `TESTING.md` or `tests/*.md`) | §7.5 | mutation run |
| **Phase 2** eleven headerless documents (B7) | first lines | no header | `> **Status:** … · **Last reviewed:** …` | — | guard (T-09) |
| **Phase 3** `docs/agent/DOC-UPDATE-MATRIX.md`, `scripts/testing/generate_docs.py` | rule table and its parser | prose triggers | additive `Paths` column parsed into the registry | §7.6 | `generate_docs.py --check` |
| **Phase 3** `scripts/testing/doc_advisory.py` | new | none | diff to rules fired to documents to check; advisory | §7.6 | tests (T-10) |
| **Phase 4** `docs/proposals/TEMPLATE_PROPOSAL.md`, `docs/PROPOSAL_CREATION_SOP.md` | template | no "Verified against" and so on | three additions (R7) | — | `test_proposal_template_requires_model_selection` |
| **Phase 5** `.github/pull_request_template.md`, `CONTRIBUTING.md` | none | one paragraph | template, timed to P-002 | §7.4 | manual: web UI pre-fill |

Phases 1–5 are proposed. Phases 2 and 3 touch files that are heavily edited in parallel; §12.2 covers the sequencing risk.

## 7. Contracts and examples

### 7.1 Intake banner (R3)

The marker is the same one `future.md` already carries. The wording varies by what the document is, and the
link prefix by where it sits: the example is written for a document one directory below `docs/`, as
`future.md` is; a document directly in `docs/` drops the `../`, and `TESTING.md` or `tests/*.md` use a
path from the repository root.

```markdown
<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a dated finding inventory, not a priority queue and not an authorization.
> Re-verify a finding before acting on it. Unresolved implementation becomes a row in
> [`PROPOSALS.md`](../PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](../todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](../FUTURE_DOCS.md).
```

### 7.2 Skill frontmatter (R2, R6)

Claude Code accepts `when_to_use` and `paths` and ignores fields it does not know; other tools read the skill
by path and ignore both (`CLAUDE.md` §14), so `description` must stay self-sufficient.

```yaml
---
name: docs
description: Editing the crosswalk registry, MARKETING.md, a pointer doc, or anything under docs/.
when_to_use: Load before changing modules.yml, a playbook heading, or a document the doc-update matrix names.
---
```

```yaml
---
name: security
description: Credential, token, capability-file and relay-authentication rules for this repository, and which paths need the full verification bar.
paths:
  - apps/*/src-tauri/**
  - apps/shared/**
  - cloud/**
  - configs/local/**
  - modules/character-avatar/**
---
```

`paths:` limits *automatic* loading to matching files, so it suits only a skill that is truly file-scoped.
`marketing-discovery` is triggered by a request naming a module, not by an open file, and must not get one.

### 7.3 Contribution workflow, `CLAUDE.md` §16 (R1)

Draft bullets, each tied to a source. The last two are owner practice and need the owner's confirmation at D04.

1. Work on a task branch in your own Git worktree; inspect `git status`, open PRs and worktrees for overlapping work first. *(source: `code-creation` skill, step 4)*
2. If a tree holds changes you did not make, preserve them and stop; never clean up what you did not create. *(same)*
3. Before claiming a proposal number, check the queue, open PRs and other worktrees. *(source: `pre-merge.md`, step 3; FD-24)*
4. Record verification as matrix row, command and result; "not run" is acceptable, silence is not. *(source: `PROPOSALS.md` "Adding a proposal", step 5)*
5. Name every user-facing behaviour change in the commit and the PR text. *(App parity)*
6. One smallest slice per PR. *(owner practice)*
7. A pull request merges only on the owner's instruction for that PR. *(owner practice)*

### 7.4 PR template skeleton (R8)

```markdown
## What changed
## Why
## Verification — matrix row, command, result ("not run" is acceptable; silence is not)
## Proposal bookkeeping — queue row, lane rows, model header, or "no proposal"
## Docs — which DM rules fired
## Privacy and security impact, rollback, blocked checks
```

A template only pre-fills the web form. The App's `doc-matrix.yml` records that every PR opened with
`gh pr create --body` replaced its template, that none of the PRs it checked contained the template's added
sections, and that it therefore added a check reading the PR body through the API. So R8 either ships with such a
check, which needs CI that executes steps, or ships as contributor-facing guidance only. Neither is useful before P-002.

### 7.5 Guard-test contract (R3, R5)

`tests/docs/test_work_intake_banner.py` holds a `REQUIRED` list of repository-relative paths. For each: the file
exists, contains the exact marker line, and its banner links resolve. A new ledger is added to the list; the list
is the contract. The status-header test is a new function over `docs/*.md` minus an explicit `EXEMPT` set
(README, generated and snapshot files); it checks `**Status:**` and `**Last reviewed:**` and does not require the
word "Enforcement", which the existing test requires only of binding documents.

### 7.6 Doc-update advisory (R4)

`python3 scripts/testing/doc_advisory.py [--base origin/main]` reads `git diff --name-only <base>...HEAD` and the
`Paths` column of the `DM-*` rules in `documentation.json`. It prints each rule fired and the documents it names,
prints "no rules fired" for an empty match, and **always exits 0**. A rule with no `Paths` never fires.
Standard library only; no network.

### 7.7 Answering the gates

Reply `D01–D10 accept as recommended`, or list exceptions (for example `D05 no`). Each answer is recorded in
§12.1 with its date, then `PL-D15` moves to the lane's resolved log.

## 8. Security, privacy, accessibility, and observability

- **Security.** Documentation only: no network, secret or scope. The `security` skill is sourced only from
  in-repo documents, contains no secret values and no live endpoints, and defers to the cited document where
  they differ. The existing security-gate tests stay green. The PR template (R8) asks for redacted evidence and
  never for a token.
- **Privacy.** No private tooling and no real person's name appears in any new text. The existing voice
  guardrail in `tests/docs/test_agent_skills.py` already covers every skill, including new ones.
- **Accessibility.** Markdown headings in order and plain tables; no meaning carried by colour.
- **Observability.** Guard tests name the offending document; the advisory prints the rules it fired; `make verify`
  lists every NOT RUN check, and each phase's verification record says what was and was not run.

## 9. Test and pressure matrix

Mutation checks follow the practice this repository uses for new tests: after the test passes, remove the thing
it guards and watch it fail.

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| T-01 | This change: queue row, lane map row, model header | `make proposal-report ARGS='--check --summary'` exits 0; `test_proposal_models.py` green | auto | this PR |
| T-02 | This change: links in the new document and the edited indexes | `test_docs_integrity.py` green after the files are committed (it reads tracked files only) | auto | this PR |
| T-03 | R1: `CLAUDE.md` edited | `generate_docs.py --write` then `--check` clean; paired-file test green | auto | Phase 1a |
| T-04 | R1: each §16 bullet | cites a repository source or is marked owner practice | manual | Phase 1a |
| T-05 | R2: new skill | passes frontmatter, path, link and voice-guardrail tests | auto | Phase 1b |
| T-06 | R2: skill against its sources | never contradicts `CLAUDE.md` §7, §10, §13 or `SECURITY.md` | manual | Phase 1b |
| T-07 | R6: amended frontmatter test | accepts `name`, `description`, optional `when_to_use` and `paths`; rejects any other key; fails over the combined cap | auto, mutation | Phase 1b |
| T-08 | R3: banner guard | fails naming the document when the marker is removed from any required one | auto, mutation | Phase 2 |
| T-09 | R5: status-header guard | fails naming the document when `Status` or `Last reviewed` is removed | auto, mutation | Phase 2 |
| T-10 | R4: advisory | a diff touching `CLAUDE.md` prints `DM-CONTEXT`; an empty diff prints none; exit code 0 in both | auto | Phase 3 |
| T-11 | Public-bound hygiene | no private tooling name, no real person as a voice, in any new text | auto and manual | every phase |
| T-12 | Offline suite | `make test` and `make verify` run; result and NOT RUN list recorded | auto | every phase |

## 10. Delivery plan

### 10.1 Gaps worth closing — ranked

Ranked by value first and cost second. **Effort scale (estimates, nothing timed):** **S** is one PR under about 200
changed lines with no new script, roughly 1–3 agent-hours including the offline suite; **M** is one PR that adds a
script and its tests, roughly 4–8 agent-hours. Owner time is one answer per gate.

| Rank | Gap (matrix ID) | Why it matters here | Value | Effort | Gate | Phase |
|---|---|---|---|---|---|---|
| R1 | Contribution workflow in the always-loaded file (B12) | The worktree and "preserve changes you did not make" rules exist only inside one skill and one command. FD-24 records two parallel-session collisions, and PRs #70 to #73 (merged 2026-10-19) are titled as rescues of work that had not reached `main` | High | S | D04 | 1a |
| R2 | `security` skill with `paths:` (B9) | `CLAUDE.md` §13 says a wrong capability "compiles and passes tests". The rules are spread over §7, §10, §13 and a 27-line `SECURITY.md`, and nothing loads when an agent opens a Tauri source tree or credential config. The App's skill of the same name is 141 lines of pinned rules | High | S | D05 | 1b |
| R3 | Intake banner on ten source documents, with a guard (B5) | 2 of about 10 comparable documents tell a reader where a new finding goes; the App carries the marker on 18 | Medium | S | D08 | 2 |
| R4 | Path-triggered doc-update advisory, local only (B8) | `DM-*` rules exist and are drift-checked, but nothing tells an agent which a diff fires; the App's workflow does exactly that | Medium | M | D07 | 3 |
| R5 | Status header on 11 headerless documents, with a guard (B7) | 11 of 22 top-level documents say nothing about whether they bind or when they were reviewed; the App has 21 of 33 | Low–Medium | S | D08 | 2 |
| R6 | `when_to_use` on every skill, with the frontmatter test amended (B10) | Claude Code appends it to the skill listing; the App has it on 7 of 7, MyFeed on 0 of 4, Hybrid on 0 of 5. Modest value at near-zero cost beside R2 | Low–Medium | S | D05 | 1b |
| R7 | Three proposal-template fields (B19) | Hybrid practice delivers one smallest slice per PR, but the template does not ask for it, nor for a verified-against commit or the files left unchanged | Low–Medium | S | D09 | 4 |
| R8 | PR template, timed to P-002 (A3) | A template alone does nothing for agent-authored PRs (§7.4). Its value arrives with outside contributors | Low now | S | D10 | 5 |

Total if everything is accepted: seven S and one M, about 11–29 agent-hours across five phases. The recommendation
is Phase 1 first; Phases 2–4 are independent of each other and of Phase 1; Phase 5 waits for P-002.

### 10.2 Phases

Each phase is one pull request. None merges without the owner's instruction for that PR.

**State, 2026-10-24:** Phase 1a is built without the two owner-practice rules; Phase 1b is built for `when_to_use` only (R6); Phase 2 is built
for the banner only (R3); Phases 3 and 4 are built; Phase 5 is not started. See §12.1a.

**State, 2026-10-26:** Phase 1b also has the `security` skill without `paths:` (R2); Phase 2 also has the status header on eight
documents and its guard (R5); Phase 5 is not started. See §12.1b.

| Phase | Contents | Depends on | Acceptance evidence | Out of scope |
|---|---|---|---|---|
| 1a | R1: `CLAUDE.md` §16; regenerate `AGENTS.md` | D01, D04 | T-03, T-04 | an `agent-work` skill |
| 1b | R2 and R6: `security` skill; `when_to_use` on every skill; amended frontmatter test | D01, D05 | T-05 to T-07 | any code under a sensitive path |
| 2 | R3 and R5 in one PR: banner and status header; two guards. One PR because 7 of the 11 headerless documents are also banner candidates and both edits sit in the same first lines | D01, D08 | T-08, T-09 | rewriting any document's body |
| 3 | R4: `Paths` column, parser change, `doc_advisory.py` | D01, D07 | T-10 | CI wiring |
| 4 | R7: three template fields; SOP touch | D01, D09 | template test green | retro-editing existing proposals |
| 5 | R8: `.github/pull_request_template.md`; a `CONTRIBUTING.md` pointer | D10 and P-002 | manual: web UI pre-fill | a check that reads PR bodies |

### 10.3 Gaps worth leaving

#### 10.3.1 Hybrid-only — the App lacks these and should not be asked to adopt them

| Feature | Where | Why it stays Hybrid's |
|---|---|---|
| Marketing crosswalk registry and generator | `modules/marketing-crosswalk/` | It is the single registry the App and the Blog point at; a second copy is the failure the pointer pattern exists to prevent |
| Design-system hub | `design-system/` | Hybrid owns tokens, components and registers by owner decision; consumers point here |
| Voice-register framework | `design-system/voice-and-tone.md` | The App has no voice work to attach it to; registers, never names, are Hybrid's guardrail (P-067 §7.3) |
| Blender production-job lifecycle | `modules/content-creation/`, `plugins/blender-addon/`, P-061 | Needs Blender, a local GPU and owned fixtures; nothing in the App's stack uses it |
| Stream Extend and Creator Extend profiles, show bible, Nova persona | `apps/`, `docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md`, P-056, P-067 | Live-stream and creator-workstation concerns; the App is a hosted web product |
| Per-module `setup/manual.md` and `setup/automated.md` with Content and Stream labels | `modules/` | Hybrid's module layering; the App has no module layer |
| Proposal model-selection policy and child-scope pattern | `docs/PROPOSALS.md`, P-073 | Hybrid assigns development-agent models per proposal; the App routes its own tiers |
| Lane index with proof markers and a queue-to-lane check | `docs/todo/`, FD-21 | Hybrid's form of *Operator action handoffs*; it differs because Hybrid has live-hardware runs the App does not |
| Roadmap layers, status ladder, Kubernetes gate | `docs/architecture/roadmap.md`, `docs/architecture/k8s-decision.md` | Local-first constraints belong to Hybrid |

#### 10.3.2 App patterns Hybrid should not adopt

| Pattern | Matrix ID | Why Hybrid leaves it |
|---|---|---|
| Move hand-written documents under `docs/readable/` | A2 | 22 documents and every inbound link move; only 3 names are shared between the App and MyFeed, so there is no content template behind the directory name. D03 keeps the layout flat and records the equivalence |
| Registry JSON as the queue's source of truth, `PRIORITY.md`, four-axis states | A4 | Hybrid's queue is owner-accepted tables with a machine check (FD-21); three repositories use three formats and none depends on another's |
| Generated skill matrix | B11 | Claude Code's own `paths:` covers file-scoped loading for the one skill that needs it, and the matrix's coverage check pays off at more skills than Hybrid has. Register a future-documents row with a trigger (D06) |
| `daily`, `bug-sweep`, `migration-check` commands | B13 | They run on artifacts Hybrid lacks or has rejected: a bug tracker (FD-20, `Deferred`), an unattended routine (FD-28, `Rejected`), Supabase migrations (not applicable) |
| Revisit & Review, review notes, Step 5b | B15 | An App-specific closing ritual; `DM-PROPOSAL-DONE` and the row's verification record close Hybrid's loop |
| Response-style directive | B16 | An owner preference for one repository's agent output, not document structure |
| Hosted-app gates | B17 | Hybrid's local-first equivalents are `CLAUDE.md` §7, §10 and §13 |
| `code-health` skill and UI stack conventions | B18 | TypeScript, Tailwind and shadcn; Hybrid's UI rules are in `design-system/` and §6 |
| An `agent-work` skill | B9 | Would duplicate §9 and the proposed §16 in the file every agent already loads (D04) |
| Copying App text such as its model-routing policy or FUTURE documents | — | FD-26 and FD-27 already reject verbatim copies: mechanisms transfer, copied content drifts |

### 10.4 Optional child assignment

Phase 2 is mechanical documentation editing with known inputs and an objective guard, which the selection policy
lists as Luna work. If the owner wants it split out: `gpt-6-luna` / `high`, with Sol reviewing and owning
acceptance. This is a recommendation, not a claim that any model has executed it.

## 11. Rollout and rollback

- **Rollout.** Each phase is one PR with no feature flag. Documentation and skills are read-only text; the only
  executable additions are tests (Phases 1b, 2) and one advisory script (Phase 3) that always exits 0.
- **Compatibility.** `AGENTS.md` regenerates from `CLAUDE.md`. Skills ignored by a tool that does not read
  `when_to_use` or `paths` still load by description.
- **Rollback triggers.** A guard test that fails on unrelated work; a `security` skill that does not load when needed
  (drop `paths:`, keep the skill); a status header that claims a review that did not happen.
- **Reversal.** `git revert` the phase's merge commit; run `generate_docs.py --write` if `CLAUDE.md` changed. There is
  no data to reverse.
- **Support response.** None; this is repository documentation.

## 12. Risks and unresolved decisions

### 12.1 Decision gates

The recommended answer is the default for the owner's convenience, not for an agent: an unanswered gate means
the status quo. `D01` and parts of `D04`, `D05` and `D08` were answered on 2026-10-24 (§12.1a).

| Gate | Question | Options | Recommended | If unanswered |
|---|---|---|---|---|
| `HYB-REDESIGN-D01` | Accept the verdict (no restructure, eight targeted additions) and authorize Phase 1? **Question:** Accept the audit's verdict: a few targeted additions, no restructure? | accept Phase 1 / accept all phases / amend / defer / retire | Accept Phase 1; Phases 2–5 follow their own gates | Stays `Pending`; nothing built |
| `HYB-REDESIGN-D02` | Keep `P-NNN` status-sectioned tables as the queue format? **Question:** Keep the proposal queue in its current status-sectioned table format? | keep / adopt the App's registry-JSON-as-source-of-truth / adopt MyFeed-style `PROP-NNN` | Keep | Keep |
| `HYB-REDESIGN-D03` | Keep hand-written documents flat in `docs/`? **Question:** Keep the hand-written docs flat in docs/, and add a one-line note explaining the layout? | keep flat / move 22 documents into `docs/readable/` / keep flat and add a one-line equivalence note to `docs/README.md` | Keep flat and add the note | Keep flat |
| `HYB-REDESIGN-D04` | Put a contribution-workflow section in the always-loaded instruction file? **Question:** Confirm or strike two owner-practice rules: one smallest slice per pull request, and a pull request merges only on your instruction? | §16 only / §16 plus an `agent-work` skill / a skill only / neither | §16 only; the owner-practice bullets in §7.3 are confirmed or struck here | Neither |
| `HYB-REDESIGN-D05` | Add the `security` skill with `paths:`, and `when_to_use` on every skill? **Question:** Should the new security skill load automatically whenever an agent opens sensitive files, such as the Tauri sources or credential configs? | both / the security skill only / neither | Both | Neither |
| `HYB-REDESIGN-D06` | Build the App-style generated skill matrix? **Question:** Skip the generated skill matrix for now, and just record it as a future idea with a trigger? | no, register a future-documents row with a trigger / build it (M) / never | No — register it; trigger: an agent session skips a relevant skill, or skills pass eight | No matrix |
| `HYB-REDESIGN-D07` | Build the local path-triggered doc-update advisory? **Question:** Build a local advisory that tells an agent which docs a change should update? | build after Phase 1 / wait / no | Build, local only; CI wiring waits until CI executes steps again | No advisory |
| `HYB-REDESIGN-D08` | Add the intake banner to ten documents and a status header to eleven, each with a guard? **Question:** Review the four documents with no recorded review so they can carry a status header, or leave them exempt? | both / banner only / neither | Both, in one PR | Neither |
| `HYB-REDESIGN-D09` | Add "Verified against", "Files intentionally unchanged" and "First implementation slice" to the proposal template? **Question:** Add the three new fields to the proposal template? | yes / no | Yes | No |
| `HYB-REDESIGN-D10` | When does a PR template land? **Question:** Wait to add a pull-request template until the open-source readiness work is accepted? | with P-002 / now / never | With P-002 | None; `CONTRIBUTING.md` stays as is |

The lane index carries these as one row, `PL-D15`, not ten: the platform table already holds eleven open rows
against a guideline of about ten, and ten more would force the lane-doc split that FD-25 defers.

### 12.1a Owner direction — 2026-10-24

On 2026-10-24 the owner directed, in chat, that the parts of the gates needing no further owner input be shipped and the rest flagged. The
reading below is the agent's, and the test applied was narrow: an item shipped only if its content is sourced from existing repository
documents, or is mechanical and has a test that fails when the thing it guards is removed. No new rule of the owner's own was invented.

| Gate | State | What shipped, or what is open |
|---|---|---|
| `HYB-REDESIGN-D01` | answered in part | Accept the decision-free subset of Phases 1 to 4; every other item stays gated |
| `HYB-REDESIGN-D02` | open, no work | Keeping the `P-NNN` tables is the default, so there is nothing to build |
| `HYB-REDESIGN-D03` | open, no work | Keeping documents flat is the default; the one-line equivalence note in `docs/README.md` is not added |
| `HYB-REDESIGN-D04` | **built in part** | `CLAUDE.md` §16 with five rules, each tied to a repository source. **Open:** the two owner-practice rules (§7.3, bullets 6 and 7) stay out until the owner confirms or strikes them |
| `HYB-REDESIGN-D05` | **built in part** | `when_to_use` on all five skills, and the frontmatter test now requires it. **Open:** the `security` skill and whether it uses `paths:`; a rule pack that binds agents on sensitive paths needs the owner's review |
| `HYB-REDESIGN-D06` | open, no work | The recommended answer is not to build the matrix; registering FD-29 waits for the answer |
| `HYB-REDESIGN-D07` | **built** | `scripts/testing/doc_advisory.py` and the matrix's Path triggers table; CI wiring waits until CI executes steps again |
| `HYB-REDESIGN-D08` | **built in part** | The banner on ten documents, with a guard. **Open:** status headers on eleven documents, each of which needs a status and a review date someone has earned |
| `HYB-REDESIGN-D09` | **built** | The three template and SOP fields, with a test |
| `HYB-REDESIGN-D10` | open | The PR template waits for P-002; on its own it does nothing for agent-authored PRs (§7.4) |

### 12.1b Owner direction — 2026-10-26

On 2026-10-26 the owner directed, in chat, that every open decision gate in this repository carry a one-sentence `**Question:**` beside its
explanation (the explanation stays; the question is additive), and that the rest of the items needing no owner input ship: the `security`
skill without path binding, and status headers on the documents whose review date `git log` supports. The §12.1a test still applies: an
item shipped only if its content is sourced from existing repository documents, or is mechanical and has a test that fails when the thing
it guards is removed.

| Gate | State | What shipped on 2026-10-26, or what is open |
|---|---|---|
| All ten gates | **question added** | §12.1 ends each gate's question cell with a plain-English `**Question:**`, and `tests/docs/test_decision_questions.py` fails when an open gate lacks one. The rule is written in `CLAUDE.md` section 9, the proposal SOP and template, and the lane index |
| `HYB-REDESIGN-D04` | built in part | Unchanged: the two owner-practice rules still wait on the owner |
| `HYB-REDESIGN-D05` | **built in part** | `.claude/skills/security/SKILL.md`, sourced from `CLAUDE.md` sections 7, 9, 10 and 13, `SECURITY.md` and the API route ledger, with a row in `CLAUDE.md` section 14 and a link in the prompt digest. It has no `paths:`, so nothing opens it automatically. **Open:** whether sensitive paths should load it |
| `HYB-REDESIGN-D08` | **built in part** | A status header on eight documents, each dated by the last commit that changed its own claims (never the initial import, a banner or a one-line hygiene edit), and `tests/docs/test_status_headers.py`. **Open:** four documents with no recorded review sit on that test's exempt list until someone reviews them: the continuous-improvement notes, the implementation notes, the pressure-test plan and the repository alignment policy |
| `HYB-REDESIGN-D02`, `D03`, `D06`, `D10` | open, no work | Unchanged |

### 12.2 Risks

| Item | Impact | Mitigation / decision owner | Due date |
|---|---|---|---|
| Skills drift from the documents they summarise | An agent follows a stale rule | The cited document wins and the skill is the thing to fix (`CLAUDE.md` §14); existing tests check paths and links; T-06 is a manual read — owner and agent | each phase |
| `paths:` is too narrow and the `security` skill does not load when needed | A sensitive edit proceeds without the rule pack | The description still lets Claude Code load it by name; drop `paths:` if a miss is seen — owner | Phase 1b |
| More always-loaded text costs every task | Context cost | §16 stays at 15 lines or fewer; detail stays in skills — agent | Phase 1a |
| Status headers go stale | A "Last reviewed" date claims more than was reviewed | Set the date only on a real review; the guard checks presence, not freshness, and a freshness check is not proposed — owner | Phase 2 |
| Hot files | `CLAUDE.md`, `PROPOSALS.md`, the lane index and several ledgers have concurrent edits in flight | Fetch before each phase; build in a worktree off `main`; R1 is the rule that prevents the collision it describes — agent | each phase |
| The App moves faster than this audit | Rows go stale | Pinned SHAs; rerun with the §2.1 commands as an `audits`-skill pass — owner | on demand |
| FD-25 trigger | The platform table is already past its guideline | One umbrella row now; the owner decides FD-25 separately — owner | at acceptance |
| The owner knows of an App voice-register document that was not found | A5 would change | The search covered the App repository only, not the Blog or private notes; point the audit at it — owner | any time |
| Parity becomes a goal in itself | Hybrid inherits choices that do not fit | §3.4 and §10.3; MyFeed's "concrete need" rule is the test for each addition — agent | continuous |

## 13. Documentation updates

**This change** (the pull request that adds this document): `docs/PROPOSALS.md` (one row appended to Pending),
`docs/todo/README.md` (`PL-D15` and one map row), and `docs/agent-registries/documentation.json` (regenerated). Not
touched: `docs/README.md` (proposal documents are indexed by the queue), `CLAUDE.md` and `AGENTS.md`.

**If accepted, by phase.** 1a: `CLAUDE.md`, `AGENTS.md` (generated). 1b: `.claude/skills/`, `tests/docs/test_agent_skills.py`,
`CLAUDE.md` §14 (skill table). 2: the ten banner documents, the eleven header documents, one new test.
3: `docs/agent/DOC-UPDATE-MATRIX.md`, `scripts/testing/generate_docs.py`, a new script and test, `docs/agent/VERIFICATION-MATRIX.md`
(a row for the advisory). 4: `docs/proposals/TEMPLATE_PROPOSAL.md`, `docs/PROPOSAL_CREATION_SOP.md`. 5: `.github/pull_request_template.md`,
`CONTRIBUTING.md`. If D06 is answered "register": one row in [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md) (next free ID is FD-29).
If D03 keeps the layout flat: one line in `docs/README.md`. Rules fired: `DM-PROPOSAL-OPEN`, `DM-PROPOSAL-MODEL`; and
`DM-CONTEXT` from Phase 1a.
