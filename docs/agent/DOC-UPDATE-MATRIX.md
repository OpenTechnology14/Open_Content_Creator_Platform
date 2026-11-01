# Doc update matrix

> **Status:** Living · **Last reviewed:** 2026-10-24 · **Owner:** OpenTechnology14

When a change touches a trigger path, the docs in that row go stale unless you update them **in
the same change**. Check this before opening a PR.

**Enforcement: advisory for review actions; generated-snapshot freshness is CI-gated.** No CI posts review findings. That is a real weakness worth naming: an
advisory list nobody opens is worth nothing. The mitigation is that `marketing-crosswalk validate`
independently catches the subset of drift that reaches marketing surfaces — everything else is on
the author.

To see which rules your change fires, run `python3 scripts/testing/doc_advisory.py` (see [Path triggers](#path-triggers)).
After changing a rule, run `python3 scripts/testing/generate_docs.py --write` and inspect
the generated registry. This gate proves the snapshot matches this source; it does not prove
every semantically affected document was reviewed.

**Trigger design.** Rules fire on **convention** changes, not churn. `modules/**` is edited
constantly, so a blanket rule there would fire on everything and train everyone to skip the
section. The rules below use *new module* / *new file* / *specific file* triggers, so they fire
when a pattern is established rather than when code under it is edited.

| Rule | Fires when | Re-read these | Why |
|---|---|---|---|
| `DM-MODULE` | a **new directory** under `modules/` | `modules/README.md`<br>`CLAUDE.md` §3, §4, §11<br>`docs/architecture/roadmap.md`<br>`README.md` (feature table + Project Structure)<br>`docs/agent/MODULE-MATRIX.md`<br>`docs/agent/MODULE-ITEM-MATRIX.md`<br>`docs/agent/SUBFEATURE-CHECKLIST.md`<br>`docs/architecture/deviations.md` | A new module is a new roadmap layer and a new label. The module indexes and status tables all go stale at once |
| `DM-MODULE-ITEM` | a **new service, port, script, bucket, or committed config file** inside an existing module | `docs/agent/MODULE-ITEM-MATRIX.md`<br>that module's `setup/automated.md` if it changes what is scripted | The item matrix is read instead of re-deriving "what does this module own". An addition missing from it is invisible to the next session |
| `DM-MODULE-DRIFT` | a module's **manual setup steps are actually walked** and something does not match — a renamed setting, a tool that no longer ships that option, a step that turns out unnecessary | that module's `setup/manual.md` (dated correction)<br>`docs/SETUP-TECHNIQUE-NOTES.md` if it is general friction, not module-specific<br>`docs/agent/MODULE-MATRIX.md` if the real cost diverged from its row | A setup doc is a spec until someone walks it; after that it should read as what is true |
| `DM-STATUS` | a module's row in `CLAUDE.md` §11 changes status | `modules/marketing-crosswalk/crosswalk/subjects/*.yml` (`status` + `status_evidence`) | Subjects cite the §11 row **verbatim**. `validate` fails loudly on drift — this is the one rule with real enforcement, and it fails rather than warns |
| `DM-COMPOSE` | a **new service** in `docker-compose.yml`, or a port/profile change | `docs/agent/MODULE-ITEM-MATRIX.md`<br>`Makefile` (target for a new profile)<br>the owning module's `setup/automated.md`<br>`.env.example` if it adds a variable | The item matrix is the port map. `AUDIT.md` **used to** record six Compose-referenced values missing from `.env.example` (fixed `P-016`/`P-035`, 2026-09-01/02) — this is the rule that stops a seventh from recurring |
| `DM-WORKFLOW` | a **new or removed** `.json` under any `workflows/` directory | that directory's `README.md` index table | Both workflow indexes **used to have** listed files that did not exist. The verified on-disk tables were the fix, and `tests/realtime_ai/test_workflows.py` now checks the index against disk automatically — this rule is what to update when the check would otherwise fail |
| `DM-MODEL` | a new model or weight requirement in any module | `modules/realtime-ai/comfyui/models.md`<br>the consuming module's `setup/manual.md` prerequisites | `models.md` is the single inventory across four consuming modules. A weight documented only in one module's prose is invisible to the others |
| `DM-MARKETING-ANCHOR` | a **heading changes** in `README.md`, `docs/architecture/product-spec.md` or `MARKETING.md` | `modules/marketing-crosswalk/crosswalk/targets.yml` (anchors) | Anchors match exact heading text. `validate` fails on drift — proven 2026-08-30 when a README rename broke it |
| `DM-PLAYBOOK` | a subject's `icps` or `status` changes in `subjects/stream-extend.yml` or `subjects/content-extend.yml`, a marketing profile, persona or show changes in `configs/local/stream-programming.yaml`, or `engine_order` changes in `assets.yml` | `MARKETING.md` §1 (shipped list), §2 (ICP tables), §3g (persona chain), §4 (engine order) | The playbook repeats these on purpose so a human can read the plan. `tests/marketing_crosswalk/test_playbook.py` fails when a copy drifts, so a stale playbook cannot ship quietly |
| `DM-ACCEPTANCE` | a module gains or loses a capability, or a **manual** check becomes automatable | `tests/ACCEPTANCE-CHECKLIST.md` (the line and its marker)<br>that module's `setup/manual.md` § Verification<br>`docs/agent/SUBFEATURE-CHECKLIST.md` | The acceptance checklist defines "done"; the subfeature roll-up exposes implementation and evidence separately. A capability with no line can never be verified, and a manual line that is now automated is a step people keep doing by hand for no reason |
| `DM-VERIFY` | a **new kind of change** with no row in `VERIFICATION-MATRIX.md` — a new language, service, file type, or tool | `docs/agent/VERIFICATION-MATRIX.md` | The matrix is what "verified locally" means. A change type with no row is one nobody knows how to prove, so it gets claimed rather than checked |
| `DM-PROPOSAL-OPEN` | a proposal is **added**, or an existing one gains an **owner decision** or a **run only a person or hardware can do** | `docs/todo/README.md` and the matching lane doc | Owner decisions and live runs were found scattered across twelve proposals on 2026-10-04 with no single list. The lanes are a derived index, and an index nobody updates is the failure this matrix already names for itself |
| `DM-PROPOSAL-DONE` | a `PROPOSALS.md` row moves to `Done` | the doc named in that row<br>that proposal's rows in `docs/todo/` — they must already be resolved | The queue tracks state; the linked doc holds the content. A `Done` row pointing at a doc that never received the decision loses the decision |
| `DM-PROPOSAL-MODEL` | a proposal is added, its scope changes, or its agent model changes | `docs/PROPOSALS.md` model/effort/rationale<br>the detailed proposal's model header<br>`docs/PROPOSAL_CREATION_SOP.md` and proposal template if selection rules change<br>`AGENTS.md` and `CLAUDE.md` if agent instructions change | P-073 found no proposal had an explicit development-agent model. Offline checks now require complete assignments and matching detailed headers; scope and capability judgment remain the author's responsibility |
| `DM-DOCS-INDEX` | a **new file** under `docs/` | `docs/README.md` | A doc that is not in the index is a doc nobody opens. This rule exists because the index was found 7 files stale on 2026-08-31 |
| `DM-CONTEXT` | change to `CLAUDE.md` | regenerate `AGENTS.md` with `scripts/testing/generate_docs.py --write`, then run `--check` | The two carry the same policy with agent-specific self-identification; full-file drift is now checked |
| `DM-DESIGN-SYSTEM` | a **token, component rule, voice register or consumer** changes in `design-system/`, or a consumer's pointer doc is added or moves | `design-system/crosswalk/consumers.md`<br>the `design-system` row in `modules/marketing-crosswalk/crosswalk/modules.yml` (`counts`, `consumers`, `files`)<br>`docs/design/BUILD-PROMPTING-DIGEST.md` and the `design` skill (voice registers) | Pointer docs are the only way a consumer learns of a hub change, and two copies drift. `tests/design_system/` fails when the registry row, the consumers list, the token counts or the register phrases disagree |
| `DM-DEVIATION` | a change that contradicts `roadmap.md`'s layering or ordering | `docs/architecture/deviations.md` | `CLAUDE.md` §9 requires the entry. Three exist; each was written because the deviation was real, not to justify it afterwards |

## Path triggers

`scripts/testing/doc_advisory.py` reads this table, through the generated registry, and lists the rules a change fires from the files it
touches. `python3 scripts/testing/doc_advisory.py` compares your working tree with `origin/main`; `--base REF` compares with another
ref. **It advises and always exits 0.** It maps *paths*, not meaning, so a rule whose trigger is a judgement about content
(`DM-STATUS`, `DM-MODEL`, `DM-ACCEPTANCE`, `DM-VERIFY`, `DM-DEVIATION`) has no row here and never fires there; those stay on the author.
CI does not run it: wiring it in waits until CI executes steps again.

A pattern is a glob over repository-relative paths: `*` stays inside one name and `**` crosses directories. A leading `+` means the
file must be **added**, `-` that it must be **removed**, and `!` that a match is **excluded**; with no prefix an added, changed or
removed file matches. A rule fires when a changed file matches an include pattern and no exclude pattern.

| Rule | Paths |
|---|---|
| `DM-MODULE` | `+modules/*/README.md` |
| `DM-MODULE-ITEM` | `+modules/**/*.sh`<br>`+modules/**/*.yml`<br>`+modules/**/*.yaml`<br>`!modules/marketing-crosswalk/crosswalk/**` |
| `DM-MODULE-DRIFT` | `modules/*/setup/manual.md` |
| `DM-COMPOSE` | `docker-compose.yml`<br>`docker-compose.digitalocean.yml`<br>`cloud/docker-compose.relay.yml` |
| `DM-WORKFLOW` | `+modules/**/workflows/*.json`<br>`-modules/**/workflows/*.json` |
| `DM-MARKETING-ANCHOR` | `README.md`<br>`MARKETING.md`<br>`docs/architecture/product-spec.md` |
| `DM-PLAYBOOK` | `modules/marketing-crosswalk/crosswalk/subjects/stream-extend.yml`<br>`modules/marketing-crosswalk/crosswalk/subjects/content-extend.yml`<br>`modules/marketing-crosswalk/crosswalk/assets.yml`<br>`configs/local/stream-programming.yaml` |
| `DM-PROPOSAL-OPEN` | `+docs/proposals/PROPOSAL_*.md` |
| `DM-PROPOSAL-DONE` | `docs/PROPOSALS.md` |
| `DM-PROPOSAL-MODEL` | `docs/PROPOSALS.md`<br>`docs/proposals/PROPOSAL_*.md` |
| `DM-DOCS-INDEX` | `+docs/**/*.md`<br>`!docs/proposals/**` |
| `DM-CONTEXT` | `CLAUDE.md` |
| `DM-DESIGN-SYSTEM` | `design-system/**` |

## What this does and does not do

- It **advises**. It does not block, and it does not update a doc for you.
- It only knows the rules above. A convention with no rule here is entirely on the author.
- It reduces drift becoming *invisible*. It does not prevent drift — skip the row and you get
  exactly the staleness it predicts.
- Three rules (`DM-STATUS`, `DM-MARKETING-ANCHOR`, `DM-PLAYBOOK`) are backed by a command or test that actually fails.
  The other rules are honour-system except for the module-coverage check on the subfeature index.

## Adding a rule

Add one when a change has actually caused drift, and name the incident in the "Why" column. Every
rule above cites a real one.
