# Crosswalk schema (schema_version: 1)

Every file under `crosswalk/` declares `schema_version: 1`. The loader rejects any other value
rather than guessing at an unfamiliar shape.

## `modules.yml` — modules the Content Platform generates content for

| Field | Required | Meaning |
|---|---|---|
| `module` | yes | Registry key. Need not correspond to a directory under `modules/`. |
| `kind` | yes | `external-app`, `product`, `series` (a set of lessons, not a product), `internal-tool` (a local-only project; always `visibility: private`, and never committed), or `design-system-hub` (a folder of this repository that other repositories mirror through pointer docs). |
| `target` | yes | Key in `targets.yml` — where content is delivered. |
| `subjects` | yes | Path (relative to `crosswalk/`) of this module's subjects file. |
| `onboarded` | no | Date the module joined the registry. |
| `visibility` | no | `private` marks a local-only module: findable by whoever registered it, never claimable, never named by a public row, and never committed — no private row ships in this repository. **Read by `validate`** — see [§ Private modules](#private-modules). Absent means public. |
| `notes`, `discovery_keywords`, `not_to_be_confused_with`, `counts`, `status`, `last_verified`, `pending_pr`, `merged_pr`, `source_revision`, `files` | no | Discovery metadata — see [§ Discovery metadata](#discovery-metadata). The loader ignores all of it. |

There is **no** requirement that every `modules/` directory appear here. Onboarding a sibling
module is an explicit act, not a coverage obligation.

## `subjects/<module>.yml` — what the content is about

Top level: `module`, `product` (key in `products.yml`), `source_docs`, `plan_notes`,
`asset_landing`, `channels`, `icps`, and `subjects`. An optional `discovery:` block carries
the same navigation metadata as a registry row — see [§ Discovery metadata](#discovery-metadata)
— and an optional `promotion:` block appears on a discovery-only module.

Source-backed blog modules may use a YAML `script_defaults` anchor to repeat conservative
subject fields. YAML expands it before validation; it grants no special claim or playback
permission. Their per-guide title evidence only establishes source presence. `scaffolded`
retains the lowest claim gate; publication, app capability and approved narration need separate
evidence. `stream-script` is a reviewable outline, never an executable or automatically approved
script.

**Five blocks are module-scoped, not global**, because each module targets a different repo with
a different audience, doc set, and pricing model:

| Block | Why it is per-module |
|---|---|
| `icps` | Who buys OpenTechnology is not who buys Stream Extend. A shared file would misattribute provenance. |
| `channels` | Labels reference the doc each set was transcribed from. |
| `plan_notes` | OpenTechnology's queue caps mean nothing to Stream Extend's cloud tiers. |
| `asset_landing` | Maps each asset onto **this** target's docs and anchors. |
| `subjects` | The content itself. |

| Subject field | Required | Meaning |
|---|---|---|
| `id` / `name` | yes | Template id and display name, as the target app uses them. |
| `what_it_is` | yes | One sentence, transcribed from the target's PRODUCT.md. |
| `upstream` | yes | `owner/repo` this template models, or `none`. |
| `visibility` | yes | `public` or `private`. Gates whether a link may appear in a draft. |
| `status` | yes | `shipped` · `target-architecture` · `unverified` · `scaffolded` (lowest). |
| `status_evidence` | yes | `{file, contains}` in the **target** repo. Re-read on every run. Optional `target:` names a different key from `targets.yml` when the subject is authored in one repo and delivered to another (`ai-learning`). |
| `plan` | yes | A key in this file's `plan_notes` block. |
| `coverage` | yes | Transcribed from BLOG_MARKETING_CONNECTION.md §2. `false` = a gap. |
| `icps` | yes | Keys from `icps.yml`, in priority order. First is primary. |
| `channels` | yes | Anchor keys from `targets.yml` → `marketing_playbook.anchors`. |
| `assets` | yes | Keys from `assets.yml`. Only these can be generated for the subject. |
| `keywords` | no | SEO terms and F5Bot alert keywords. First is primary. |
| `competitors` | no | Populate comparison tables as `_TODO: verify_` rows. |

## `assets.yml`

`engine_order` lists the five-format content engine in MARKETING.md §4's order; `generate` emits
in that order. Per asset: `template`, `claim_level` (`roadmap` | `shipped`), optional
`engine_step`, and `summary`.

**Where an asset lands is not declared here** — that is `asset_landing` in each module's subjects
file, because targets differ. `validate` fails on any declared asset with no landing.

## `targets.yml`

`path_env` / `default_path` resolve a local checkout. Each doc lists `anchors` as **exact heading
text**; `validate` fails if any is missing. `draft_dir` is where `--apply` writes.

The `optional` key (`optional: true`) lets a target's checkout be absent: `validate` logs the absence
instead of failing. Use it only on a target that declares no `docs` — a discovery-only module has
nothing to verify, so a machine or CI runner without that checkout loses nothing. It never weakens a
checkout that is present: declared docs and anchors are still checked.

`visibility: private` marks a target for local-only modules. None ships in this repository; the rule is
exercised on synthetic crosswalks in the tests. Only a `visibility: private` module may use one (§ Private modules).

## Discovery metadata

Added 2026-09-23 because a module could not be found by name: sessions looking for the **AI
Learning Series** routed to **AI Control Layer** twice. Three modules carry "AI" in their name, so
a name match alone is not enough to pick one.

These fields exist so `rg` finds the right module and so a reader can tell confusable modules
apart. They appear on each row in `modules.yml` and under a `discovery:` key in each
`subjects/<module>.yml`.

**The loader ignores every field below.** It reads only `module`, `kind`, `target`, `subjects` and
`visibility` from a registry row (`visibility` is a rule, not metadata — see § Private modules), so
enriching one with the fields below can never break `validate` — and equally, nothing validates
these fields. They are prose and hand-counted numbers. The one exception is a discovery-only
project row, whose `status` is checked against its `counts` (see § Discovery-only modules).

| Field | Meaning |
|---|---|
| `notes` | 2–3 sentences of plain language: what the module **is**, and what kind of request should route to it. |
| `discovery_keywords` | The terms someone would grep for. Include product names, feature names, synonyms, spelling variants, and proposal IDs. |
| `not_to_be_confused_with` | The load-bearing field. Each entry names a confusable module and the distinction. Populate it whenever two modules share a word. |
| `counts` | Hand-counted snapshot with a required `basis` line naming what was counted and from where. |
| `status` | `planned` · `outlined` · `drafted` · `partially-shipped` · `fully-shipped`. Coarser than a subject's `status`, and about the module as a whole. |
| `last_verified` | Date the counts and files were checked. |
| `pending_pr` | Present only when the module's artifacts live in an unmerged pull request. |
| `merged_pr`, `source_revision` | Merge reference and inspected source commit. Navigation provenance, not a publication or capability claim. |
| `consumers` | Hub rows only (`kind: design-system-hub`): the downstream repositories that mirror the hub, each with `name`, `repo`, `pointer_doc` (the path it is expected to keep) and `pointer_state` (`present`, `absent` or `local-draft`). The authority is `design-system/crosswalk/consumers.md`; a test keeps the two lists in step. |
| `files` | Real paths to the module's key artifacts. Paths are relative to the **target** repo unless the key says otherwise. `*_unmerged` keys mark paths that exist only on a PR branch. |
| `promotion` | Present only on a discovery-only module. `blocked_on` plus the ordered `steps` that turn it into a generating module. |

### Counts are transcribed, not computed

Nothing recomputes `counts`. It is true as of `last_verified` and drifts silently. **When a count
disagrees with the repository, the repository wins** — correct the count. A count is a navigation
aid, never evidence for a claim; a public claim still needs a subject's `status_evidence`.

### Discovery-only modules

A module whose artifacts live in an unmerged PR is registered with `subjects: []`. This is
deliberate. § "Status is evidenced, not asserted" below forbids a status claim whose evidence a
validator cannot re-read, and evidence on an unmerged branch is absent from every normal checkout —
citing it would fail `validate` for everyone.

So the module becomes **findable** without becoming **claimable**. `validate` iterates zero
subjects and reports no findings; `generate` produces nothing. Its `promotion` block is the
checklist for lifting it once the PR merges.

The same shape registers a **project that is not part of this platform** — a game, a separate
product repository, a private tool — that a session should be able to find but that nothing here
markets. Its subjects file is the minimum the loader accepts: `product: none`; an `icps:` block
holding one `unspecified` placeholder (the loader refuses a file with no ICPs — the placeholder is
not an audience); `subjects: []`; a `discovery:` mirror of the row; and a `promotion` block. The row
is canonical and the mirror copies `status`, `last_verified`, `notes`, `discovery_keywords`,
`not_to_be_confused_with`, `counts` and `files`; a test fails if they diverge.

A **hub row** (`kind: design-system-hub`) is the same shape for a different reason: it registers a folder of *this* repository so a
session can find it. Its `status` is the review state of its content (`drafted` = authored, awaiting owner review), not the
project-count rule below, and it lists `consumers` instead of `files` that exist only in another repository.

**`status` on a project row is mechanical**, so it cannot be a hunch: `drafted` = source code **and**
at least 10 maintained docs; `outlined` = some code or some docs, short of that bar; `planned` =
neither. It is computed from `counts.code_files` and `counts.doc_files`, and
`tests/marketing_crosswalk/test_discovery_modules.py` enforces it. It describes the underlying
project, never marketing content, and no public claim may cite it. Give `counts.basis` the revision
(or say there is none), the date, and the rule used for each count.

Persona, show profile and social account are required only of a *generating* module; a
discovery-only row has none until it is promoted (`tests/automation_control/test_personality_bindings.py`).

### Private modules

`visibility: private` registers a local-only project so whoever registered it can find it. **None ships in this
repository:** a private row belongs in an uncommitted local copy of `modules.yml`, and `test_no_private_row_ships`
and `scripts/testing/public_release_guard.py` fail if one is committed. `validate` still enforces, on whatever is
registered:

- a private module targets a `visibility: private` target, and no public module does;
- a private module declares no subjects, so it can never generate content;
- no public module's row, subjects or metadata contains a private module's **id**.

`generate --module <id>` refuses a private module before it validates anything (exit 2), and
`coverage` / `selftest` see no subjects to render.

**What this does not guard: topics.** A public subject may legitimately share a topic with a private row, so a
topic word in public text is not a leak signal; only the registry id is matched. A list of forbidden names is
deliberately unsupported — committing one would be the leak. Keep any private text generic: no tenant, hostname,
ID, credential, URL or path.

Do not confuse this with the **subject-level** `visibility` (`public` | `private`) in
`subjects/<module>.yml`: that only says whether a subject's `upstream` repository may be linked in a
draft. A subject with `visibility: private` is still a normal, claimable subject.


## Status is evidenced, not asserted

A subject may not declare a status without naming the file and text that establishes it. An
unevidenced status is a load-time error, because a status is what gates every public claim.
