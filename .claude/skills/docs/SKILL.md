---
name: docs
description: Documentation conventions for this repo - the marketing-crosswalk registry (modules.yml, targets.yml, subjects files and their schema), the root MARKETING.md playbook and its Registry lines, the discovery_keywords / not_to_be_confused_with pattern, pointer docs in OpenTechnologyApp and OpenTechnologyBlog, and the docs-integrity rules under docs/. Use before editing any registry file, playbook, pointer doc, CLAUDE.md or anything under docs/.
when_to_use: "Examples: 'register a module in modules.yml', 'rename a MARKETING.md heading', 'write a pointer doc', 'add discovery keywords', 'a docs-integrity test fails', 'update CLAUDE.md or a file under docs/'."
---

# Docs

Authority order when sources disagree: the **YAML and configs**, then `modules/marketing-crosswalk/crosswalk/schema.md`
(the field reference), then this skill. Pick the right module for a request with the
`marketing-discovery` skill first; this skill is about *editing* the documentation layer.

**Register first.** Before you edit, register the task with its one Kind (`CLAUDE.md` section 17, the entry gate). A decision row or gate you add still ends with its `**Question:**` line.

## The registry (one file, three repositories)

`modules/marketing-crosswalk/crosswalk/modules.yml` is the only list of marketing modules. OpenTechnologyApp and
OpenTechnologyBlog hold pointers, never copies, because two copies of a registry drift.

| File | Holds |
|---|---|
| `modules.yml` | one row per registered module |
| `targets.yml` | where content lands: repo, `path_env` / `default_path`, docs and their **exact-heading** anchors |
| `products.yml`, `assets.yml` | product copy; the asset catalogue and `engine_order` |
| `subjects/<module>.yml` | what content is about: `icps`, `channels`, `asset_landing`, `subjects`, plus a `discovery:` mirror |

**The loader reads only** `module`, `kind`, `target`, `subjects` and `visibility` from a row. Everything else is
discovery metadata: prose and hand-counted numbers that nothing validates, so enriching a row cannot break
`validate` - and a wrong value is never caught for you.

## Row metadata (`schema.md` § Discovery metadata)

| Field | Rule |
|---|---|
| `notes` | 2-3 plain sentences: what the module **is** and what kind of request routes to it |
| `discovery_keywords` | what a person would grep: product and feature names, synonyms, spelling variants, proposal IDs. Search is `rg -i`, so **case-only variants are noise** (a test rejects them in the discovery-only rows) |
| `not_to_be_confused_with` | the load-bearing field. Populate it whenever two modules share a word. A keyword shared with another module must name that module here (a test enforces it for the discovery-only rows) |
| `counts` | hand-counted snapshot with a required `basis` line (what, where, revision, date). **The repo wins** when a count disagrees; a count is never evidence for a claim |
| `status`, `last_verified` | module-level status; the date counts and files were checked |
| `files` | real paths; relative to the **target** repo unless the key says otherwise. `*_unmerged` keys mark paths that exist only on a PR branch |
| `promotion` | discovery-only rows only: `blocked_on` plus the ordered `steps` that make it generate |

Row and `discovery:` mirror carry the same values; the row is canonical and a test fails if they diverge.

## Statuses are evidenced

A subject needs `status` **and** `status_evidence` (a file + text that exists in the target). `validate` re-reads it
every run. Subjects cite the `CLAUDE.md` §11 row verbatim (`DM-STATUS`), so editing that table without the subjects
fails loudly. Update `status` and `status_evidence` together; never lower a gate by editing one.

## Discovery-only and private rows

- **Discovery-only**: `subjects: []` plus a `promotion:` block. Findable, not claimable. The same shape registers a
  project that is not part of this platform; its subjects file is the loader's minimum (`product: none`, one
  `unspecified` placeholder ICP, `subjects: []`, a `discovery:` mirror, `promotion`). A project row's `status` is
  mechanical: `drafted` = code **and** at least 10 maintained docs; `outlined` = some of either; `planned` = neither.
- **Private** (`visibility: private`, `kind: internal-tool`): a local-only row. **None ships:** never commit one
  (`test_no_private_row_ships` and `scripts/testing/public_release_guard.py` fail). On whatever is registered
  locally the loader still requires a `visibility: private` target, no subjects and no public row naming its id,
  and `generate` refuses it (exit 2). The guard matches **ids, not topics**, and a list of forbidden names is
  deliberately unsupported - committing one would be the leak.
- **Hub rows** (`kind: design-system-hub`, e.g. `design-system`) register a folder of this repo that other repos mirror through pointer
  docs. They list `consumers`, and their `status` is the content's review state, not the project-count rule.
- Subject-level `visibility` is a different thing: it only says whether a subject's `upstream` repo may be linked.
- `optional: true` on a target lets its checkout be absent. Use it only where the target declares no `docs`.

## MARKETING.md - the playbook convention

Each target has a go-to-market playbook registered as a `targets.yml` doc (`marketing_playbook`) with its headings
as anchors, so renaming a heading fails `validate` (`DM-MARKETING-ANCHOR`). The root `MARKETING.md` of this repo:

- **keeps OpenTechnologyApp's section numbering** (§1 Positioning ... §8 Mistakes; §3a-3g channels), so a section number
  means the same step in both - but the audiences, claims and evidence are this repo's own;
- opens **every numbered section with a `**Registry:**` line** naming the registered modules it depends on;
- is listed as `files.marketing_doc` on the `stream-extend` and `content-extend` rows;
- **repeats registry data on purpose** (shipped list, ICP tables, persona chain, engine order) because a human must
  be able to read the plan. Duplication is only safe when verified: `tests/marketing_crosswalk/test_playbook.py` fails the
  moment a copy drifts, and the registry wins (`DM-PLAYBOOK`);
- claims follow `status`. A `scaffolded` subject gets roadmap-level copy only.

## Pointer docs (sibling repos)

OpenTechnologyApp (`OpenTechnologyApp:docs/readable/MARKETING_CROSSWALK_POINTER.md`) and OpenTechnologyBlog (`OpenTechnologyBlog:docs/MARKETING_CROSSWALK_POINTER.md`)
each hold a **pointer plus facts local to that repo**: a statement that the registry lives in the platform repo; links to
`modules.yml`, `schema.md` and the module README; how to find the platform checkout locally; the `not_to_be_confused_with`
warning with a request-to-module table; a pointer to the platform's `MARKETING.md`; and how *this* repo relates (the target
docs the crosswalk re-reads). The Blog pointer also lists the modules whose artifacts live there, dated, with "the registry is
the source, re-read it". Update a pointer when a module is added or removed, when a playbook moves, or when an anchor it lists
is renamed. Never paste registry rows into one.

## Rules for anything under `docs/` (`tests/docs/test_docs_integrity.py`)

- A new file under `docs/` needs an entry in `docs/README.md` (`DM-DOCS-INDEX`); proposals are indexed by the queue instead.
- Living reference docs under `docs/agent/` declare `**Status:**`, `**Last reviewed:**` and their enforcement.
- Relative links must resolve; a backticked repo path (`docs/`, `modules/`, `scripts/`, `tests/`, `apps/`, `cloud/`, `plugins/`)
  must exist unless the line says it is proposed, deferred, missing or "does not exist". Describe only what exists.
- **Generated files are never hand-edited.** After changing `CLAUDE.md` or a source it reads, run
  `python3 scripts/testing/generate_docs.py --write`, inspect the diff, then `--check` (`DM-CONTEXT`). `AGENTS.md` is the
  generated mirror of `CLAUDE.md`.
- Use the evidence vocabulary: **Verified**, **Inferred**, **Proposed**, **Blocked**. Never present proposed behaviour as built.

## Verify before you say it is done

```bash
cd modules/marketing-crosswalk
OTBLOG_REPO_PATH=<blog checkout> OPENTECHAPP_REPO_PATH=<app checkout> python3 -m generator.cli validate
python3 -m generator.cli selftest            # every template still renders
cd ../.. && python3 -m pytest tests/marketing_crosswalk tests/docs -q
python3 scripts/testing/generate_docs.py --check
```

`validate` fails when a sibling checkout is missing (use a clean checkout of each repo's `main`, not a feature branch).
A registry change needs `validate` **and** `selftest` **and** `ruff check modules/ scripts/`; `validate` alone proves
the registry, not the templates.

## Sources

`modules/marketing-crosswalk/crosswalk/schema.md` - `modules/marketing-crosswalk/README.md` - `MARKETING.md` -
`tests/marketing_crosswalk/test_playbook.py` - `tests/marketing_crosswalk/test_discovery_modules.py` -
`docs/agent/DOC-UPDATE-MATRIX.md` - `tests/docs/test_docs_integrity.py` - the two sibling pointer docs named above.
