---
name: audits
description: Audit procedures for this repo - the marketing-crosswalk coverage audit (validate, selftest, coverage; ledger gaps versus blocked assets) and the static test-coverage and dead-export audit pattern (scripts/audit_test_coverage.py, scripts/audit_dead_exports.py - run, triage false positives first, ship thematic quick-win PRs, ratchet with a baseline). Use when asked to audit crosswalk completeness, find untested or dead code, or measure coverage. For the repo-wide quick/standard/deep review use the /audit command instead.
when_to_use: "Examples: 'audit the crosswalk', 'is every module covered?', 'find untested code', 'which exports are dead?', 'measure test coverage', 'run the static audits'. Not for a repo-wide review: that is the /audit command."
---

# Audits

Read-only first. An audit reports; it does not silently fix what it finds. Fixes are a separate, explicitly
authorised step (Part B below describes that step).

**Register first.** An audit run is registered with its one Kind before it starts (`CLAUDE.md` section 17, the entry gate). What it finds is filed as findings, and a fix that follows is a separate item with its own Kind.

## Which audit?

| Question | Use |
|---|---|
| Is the repo healthy overall (verify gates, queue, CI, claims)? | the `/audit` command - `.claude/commands/audit.md` (tiers `quick`, `standard`, `deep`; appends a bounded entry to `docs/AUDIT_LOG.md`) |
| Is the marketing crosswalk complete and honest? | Part A |
| Which public code has no test, or no caller? | Part B |
| Is a branch ready to merge? | `.claude/commands/pre-merge.md` |

Use the evidence vocabulary in `docs/PROPOSAL_CREATION_SOP.md`: **Verified** (observed in code or an executed check),
**Inferred**, **Proposed**, **Blocked** (a named dependency was unavailable). Never present inferred behaviour as built, and
list every check you did not run.

## Part A - crosswalk coverage audit

```bash
cd modules/marketing-crosswalk
export OTBLOG_REPO_PATH=<blog main checkout> OPENTECHAPP_REPO_PATH=<app main checkout>
python3 -m generator.cli validate                      # anchors + status claims still hold in the target repos
python3 -m generator.cli selftest                      # every template renders, no private links
python3 -m generator.cli coverage --module <name>      # once per module that has subjects
```

**Reading `coverage` - two kinds of gap, deliberately separate:**

- **Ledger gaps** (the last column) - the target's own ledger says a blog post, guide page, course lab or lead email does not
  exist. This is **work to do**.
- **Blocked assets** - the subject's verified `status` is too low for an asset that asserts the thing works today. This is
  **not a defect and not work to do**: it is a claim we are not entitled to make. When the cited line in the target repo
  changes, update `status` and `status_evidence` together and the assets unblock. Never edit a status to clear a blocked row.
- **Channel coverage** lists how many subjects each channel serves. A zero needs an explanation; the module README lists the
  expected ones (for example `directories`), so check it before reporting a gap.

**Also check by hand, because nothing validates them:**

1. **Counts versus the repo.** Re-derive `counts` from the source named in its `basis` line (e.g. `CLAUDE.md` §4 for module
   labels). The repo wins; correct the count and bump `last_verified`.
2. **Keyword collisions.** List keywords two rows share; each row involved must say how they differ in `not_to_be_confused_with`.
3. **Visibility.** No `visibility: private` row or target is committed (`test_no_private_row_ships`). On a local private row,
   `validate` enforces that it targets a private target, declares no subjects and is named by no public row.
4. **Discovery-only rows.** `status` still follows `counts` (`drafted` = code and at least 10 docs; `outlined` = some; `planned` =
   none), and `promotion.steps` still describes a real path.
5. **Personas.** Every *generating* module has exactly one persona, show profile and account route
   (`tests/automation_control/test_personality_bindings.py`); discovery-only rows have none.

`validate` fails if a required sibling checkout is missing or sits on a feature branch whose headings differ. That is an
environment gap, not a registry defect - say which it was. A registry change needs `validate` **and** `selftest` **and**
`ruff check modules/ scripts/`.

## Part B - the static coverage and dead-export pattern

Two read-only, standard-library tools modelled on Ironfall's audits. They read source text only (Python through `ast`, Rust
through a comment- and string-stripping brace scanner), import nothing, and run in about a second.

```bash
ls scripts/audit_*.py                  # they must exist on your branch; if not, your base predates them - do not re-create them
make audit-coverage                    # summary, then every MISSING unit        (add ARGS=--missing-only)
make audit-dead                        # DEAD and TEST-ONLY public symbols       (add ARGS='--show DEAD,TEST-ONLY,INTERNAL --lang rust')
```

| Tool | Statuses | Exit |
|---|---|---|
| `scripts/audit_test_coverage.py` | *covered*, *indirect* (called by code tests touch - read before trusting), *weak* (a test names it, module link unproven), *missing*, *skipped* (entrypoints, framework handlers, data classes, Tauri commands) | 1 on MISSING; `--report-only` always 0 |
| `scripts/audit_dead_exports.py` | *DEAD* (no code, test or config use), *TEST-ONLY*, *INTERNAL* (hidden by default) | 0; `--strict` is 1 on DEAD |

Both take `--lang python|rust`, `--area <path text>`, `--json`, and `--baseline FILE` / `--write-baseline FILE`.

**The triage method (this order matters):**

1. **Run against clean `main`**, not a dirty tree, and save the numbers (summary counts per language) so the effect of each
   change is measurable.
2. **False positives first.** These are name-matching heuristics, not compilers: a hit is a candidate to read, not a verdict, and
   dynamic callers (`getattr`, a plugin host, a config string) can hide a real use. When a finding is a tool limitation, fix the
   tool with a **filter**, and pin the filter with a case in `tests/audit/` that **fails without it**. Add one case per filter.
3. **Classify what remains**: a real gap, by design (entrypoint, hook, data class), or dead. Read the code before deciding.
4. **Ship thematic PRs** - one theme each so every PR reviews and reverts alone (e.g. the tools; tests for one CLI; tests for two
   shared crates plus the CI step that runs them). Report before/after counts in each PR body.
5. **Mutation-check every new test**: break the behaviour it pins, watch it fail, restore. A test that never saw the bug proves nothing.
6. **Freeze the backlog, then ratchet.** Only after the first triage, write a baseline so new gaps fail and the known backlog does
   not. The tools are deliberately **not wired into CI** until that is a decision.
7. **Verify with the matrix row** for `scripts/audit_*.py` in `docs/agent/VERIFICATION-MATRIX.md`: the synthetic-tree tests in
   `tests/audit/`, then run both tools on the repo and read what they print. "It ran and printed something" is not a verification.

## Reporting

State scope, source revision, commands run with results, **checks not run**, the highest-priority fixable finding, and the
highest-leverage next move. Do not claim CI is green or red without reading why: a job that fails in seconds with zero steps and
a spending-limit annotation is the account billing block, not a finding about the code.

## Sources

`modules/marketing-crosswalk/README.md` - `modules/marketing-crosswalk/generator/coverage.py` (the docstring defines the two gaps) -
`scripts/testing/README.md` § Static audits - `docs/agent/VERIFICATION-MATRIX.md` - `.claude/commands/audit.md` -
`.claude/commands/pre-merge.md` - `docs/PROPOSAL_CREATION_SOP.md` § Evidence vocabulary.
