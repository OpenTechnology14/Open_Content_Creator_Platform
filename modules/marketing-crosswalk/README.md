# marketing-crosswalk

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (automated)

The Content Platform's content-generation module. It generates marketing content **for** the
modules registered in [`crosswalk/modules.yml`](crosswalk/modules.yml).

---

## This is the canonical marketing-module registry

**Working in any of the three repositories — hybrid-creator-platform, OpenTechnologyApp, or
OpenTechnologyBlog — and need to know what marketing modules exist? Read one file:**

```
hybrid-creator-platform/modules/marketing-crosswalk/crosswalk/modules.yml
```

There is no second list. A marketing module that is not registered there is not discoverable, which
is the whole reason the registry exists.

### Find a module by what you know about it

```bash
# From this repo
rg -i "ai learning|control layer|chatbot" modules/marketing-crosswalk/crosswalk/modules.yml

# From another repo, if the platform is a sibling checkout
rg -i "<your term>" ../hybrid-creator-platform/modules/marketing-crosswalk/crosswalk/modules.yml

# Not sure where the platform is checked out
find ~ -maxdepth 4 -path '*/marketing-crosswalk/crosswalk/modules.yml' 2>/dev/null
```

Match against two fields on every row:

| Field | Use it to |
|---|---|
| `discovery_keywords` | Hit the module from a search term, a synonym, a spelling variant or a proposal ID |
| `notes` | Read in plain language what the module **is**, and whether your request belongs to it |

### Check `not_to_be_confused_with` before you act

**Three registered modules have "AI" in the name.** Sessions looking for the AI Learning Series
routed to AI Control Layer twice, which is why that field exists. A name match is not a match:

| If you want | Use | Not |
|---|---|---|
| Four lessons teaching how to use AI | `ai-learning` | `ai-control-layer` |
| An ongoing AI governance / practice library | `ai-control-layer` | `ai-learning` |
| How OpenTechApp routes chat requests between vendors | `chatbot-routing` | `ai-control-layer` |

`crosswalk/schema.md` § Discovery metadata documents every discovery field, and says plainly which
of them the loader ignores.

### Merged blog sources now support draft scripts

OpenTechnologyBlog PRs #38 and #49 merged on 2026-09-26. Verified against local blog `main`
`03970722` on 2026-09-30: `ai-control-layer` has ten source guides (including the app-control
explainer added after the original nine), and `chatbot-routing` has seven. Both now generate
`stream-script` outlines. Update the local blog checkout if validation reports missing sources.

Each guide remains conservatively `scaffolded`: its exact MDX title proves source presence and
detects drift, **not** publication, app capability, script approval or an aired episode. No
deployment check was performed. The three older background articles linked from the AI Control
Layer hub are not new subjects; that module's source docs flag them for a separate refresh.

---

| Module | Target | Subjects | Ledger |
|---|---|---|---|
| `task-management` | [OpenTechnology14/OpenTechnologyApp](https://github.com/OpenTechnology14/OpenTechnologyApp) | its six built-in project templates | `BLOG_MARKETING_CONNECTION.md` §2 |
| `stream-extend` | this repo | the fifteen modules labelled `Stream` | `product-spec.md` §Marketing (streamextend.com rows) |
| `content-extend` | this repo | the thirteen **product** modules labelled `Content` (fourteen carry the label) | `product-spec.md` §Marketing (creatorextend.com rows) |
| `ai-learning` | [OpenTechnologyBlog](https://github.com/OpenTechnology14/OpenTechnologyBlog) (status read from this repo) | the four lessons of the [AI Learning Series](../../docs/learning/README.md) | `docs/learning/README.md` § Where each lesson is delivered |
| `ai-control-layer` | [OpenTechnologyBlog](https://github.com/OpenTechnology14/OpenTechnologyBlog) | ten source guides | `OpenTechnologyBlog:docs/AI_CONTROL_LAYER_MODULE.md` |
| `chatbot-routing` | [OpenTechnologyBlog](https://github.com/OpenTechnology14/OpenTechnologyBlog) | seven source guides | `OpenTechnologyBlog:docs/CHATBOT_ROUTING_MODULE.md` |

`marketing-crosswalk` carries the `Content` label but is **not** a `content-extend` subject: the
roadmap says it "owns no runtime and ships in neither app". Marketing copy about it would describe
something no customer can buy.

### Discovery-only rows

Registered so a session can *find* them. None generates content (`subjects: []`) and none has a
persona; see [`crosswalk/schema.md`](crosswalk/schema.md) § Discovery-only modules. Their `status`
describes the underlying project (code and docs found), never marketing content; the one exception is the `design-system`
hub row, whose `status` is the review state of its content.

| Module | Where it lives | What it is |
|---|---|---|
| `myfeed` | [OpenTechnology14/MyFeed](https://github.com/OpenTechnology14/MyFeed) | a separate single-user local media reader |
| `ironfall` | [OpenTechnology14/Ironfall](https://github.com/OpenTechnology14/Ironfall) | a UE 5.8 game specification and C++ project |
| `animalhouse` | local project, no repository yet | a UE 5.8 animal-collection prototype |
| `gist` | [OpenTechnology14/Gist](https://github.com/OpenTechnology14/Gist) | a separate mobile-first grocery list and food health-scoring web app with a product directory |
| `design-system` | this repo, [`design-system/`](../../design-system/README.md) | the ecosystem design-system hub (`kind: design-system-hub`): tokens, component specs, voice registers, and the downstream repositories that mirror it through pointer docs; drafted, awaiting owner review |

**Direction matters.** This repository is the Content Platform; a registered module is a
*consumer* of generated content. `validate` does not require a registry row per `modules/`
directory — onboarding one is an explicit act, not a coverage obligation.

`stream-extend` targets **this repo** because Stream Extend's marketing surfaces live here today:
`README.md` carries the product comparison and pricing, and `product-spec.md`
§"Marketing: Guides as Content" specifies how a module's setup docs become a website page. There
is no StreamExtend checkout, and `REPOSITORY_ALIGNMENT.md` makes this the canonical source.

The Stream Autopilot catalog uses these same module IDs as direct source bindings. Each scripted
marketing show profile names exactly one module ID and its crosswalk target, so `task-management`
is the OpenTechApp profile while `ai-learning`, `ai-control-layer` and `chatbot-routing` are
OpenTechnologyBlog profiles. The profile is still Nova with a module-specific teaching mode; it is
not a second avatar identity. All six modules now have source-backed script outlines; none of
these bindings starts a broadcast, approves narration or establishes publication rights.

**Why it exists.** The target repo's `Task-Management:docs/readable/BLOG_MARKETING_CONNECTION.md` §1 says the
product↔content relationship is "kept in sync by hand", with "no code dependency in either
direction" and that "nothing here alerts on drift; the only defense is checking the blog's
matrix after a template change." This module is that alert, plus the generator for the gaps
it finds.

Local-first: no network calls, no API keys, no services. It reads the configured local checkouts and
writes markdown.

---

## Quick start

```bash
cd modules/marketing-crosswalk
python3 -m generator.cli validate
```

| Command | What it does |
|---|---|
| `validate` | Every marketing-doc anchor still resolves in the target repo, and every subject's status claim is still backed by the line it cites. Exit 1 on any error. |
| `coverage` | Per-template render/blocked counts, ledger gaps, and channel coverage. |
| `selftest` | Renders every template in memory, ignoring claim gating. Writes nothing. Exit 1 on any template failure. |
| `generate` | Renders drafts. Dry-run and gating rules below. |

```bash
# what content exists per subject, and what is missing
python3 -m generator.cli coverage --module task-management
python3 -m generator.cli coverage --module stream-extend

# one subject, every asset it declares, in content-engine order
python3 -m generator.cli generate --module task-management --subject pm_requests

# one format across a whole module, previewed
python3 -m generator.cli generate --module stream-extend --asset guide-page --dry-run

# write drafts into the target checkout
python3 -m generator.cli generate --module task-management --subject pm_requests --apply
```

`--module` is required once more than one module is registered.
Target resolution: `--target-path` → the target's `path_env` → its `default_path`.

---

## What gets generated

Everything comes from the target repo's own marketing docs, not from invention.

| Input | Source doc |
|---|---|
| **Subjects** — the six built-in project templates | `OpenTechnologyApp:docs/readable/PRODUCT.md` § Project Templates |
| **ICPs** — five, in priority order | `MARKETING.md` §2 |
| **Channels** — Reddit, X, LinkedIn, SEO, directories, email | `MARKETING.md` §3a–3f |
| **Asset set** — the five-format content engine | `MARKETING.md` §4 |
| **Coverage ledger** — which templates lack a post / lab / email | `OpenTechnologyApp:docs/readable/BLOG_MARKETING_CONNECTION.md` §2 |
| **Status + upstream + visibility** | `OpenTechnologyApp:docs/readable/TEMPLATE_REPO_CROSSWALK.md`, template READMEs |

The five-format engine is MARKETING.md §4 verbatim — one blog post becomes five pieces:

| Step | Asset | Channel |
|---|---|---|
| 1 | `blog-brief` | SEO (§3d) |
| 2 | `reddit-post` | Reddit (§3a) |
| 3 | `x-thread` | X (§3b) |
| 4 | `linkedin-post` | LinkedIn (§3c) |
| 5 | `comment-ammo` | F5Bot alert replies (§3a) |

Plus `comparison-page` (§3d), `lead-email-angle` (§3f), and `matrix-row` (keeps the §2 ledger
current). `generate` emits them in engine order.

Directory listings are deliberately **not** generated: `MARKETING.md` §3e's paste-ready copy is
product-level — one listing for OpenTechnology — not per-template, and it is already written.

---

## Walkthrough briefs

`walkthrough-brief` creates a demonstration plan for all 26 subjects in `stream-extend`,
`content-extend` and `task-management`. These existing consumers cover this app's own marketing
and OpenTechnologyApp's templates. This format needs no new runtime module.

After `validate`, preview one brief from this directory:

```bash
python3 -m generator.cli generate --module stream-extend --subject creator-experience --asset walkthrough-brief --dry-run
python3 -m generator.cli generate --module content-extend --subject content-creation --asset walkthrough-brief --dry-run
python3 -m generator.cli generate --module task-management --subject extend_platform --asset walkthrough-brief --dry-run
```

Omit `--dry-run` to write the brief into ignored `out/`; review existing drafts before rerunning
because the same filename is overwritten. Each brief includes source/status provenance, actions,
expected results, recovery, capture evidence, captions/transcript and an engineering companion.
It is a roadmap-level preparation artifact, including for scaffolded subjects. It does not assert
that the demonstration happened or automate recording, voice, uploads or public publication.
P-067 retains automated capture runtime; P-070 owns this draft workflow.

See the [documentation website](../../docs/public/index.html) and
[reference review](../../docs/PUBLIC_DOCS_AND_MARKETING_REVIEW.md) for the beginner/engineer split.

## Scripted marketing shows

Every subject in all six modules supports `stream-script` (55 subjects as of 2026-10-20). This is
a roadmap-level **outline for human completion**, with a draft opening, stable segment labels,
source evidence, explicit narration TODOs and review gates. It is not an approved script or a
source-reading/live-playback engine. The lesson-specific `stream-runofshow` remains available for
`ai-learning`; it is not repurposed as a product script.

From this module directory, after `validate` succeeds:

```bash
# Preview, without writing. Use the module bound to the intended show profile.
python3 -m generator.cli generate --module ai-control-layer --asset stream-script --dry-run

# Write one local draft outline; no --apply, sibling edits, provider call or upload.
python3 -m generator.cli generate --module chatbot-routing \
  --subject chatbot-routing-for-beginners --asset stream-script
```

The output is `out/<module>--<subject>--stream-script.md`. The
[show-profile mapping](../../docs/architecture/stream-personality-audio-routing.md#how-personalities-are-organized)
resolves the module to its Nova persona and scripted audio policy. Complete every TODO, review
the cited source and current claim ledger, approve the spoken text, then record through the
existing operator workflow. A completed recording and its source outline can enter the
[draft YouTube handoff](../automation-control/show_planner/README.md#stream-profiles-and-scoped-youtube-handoff),
which retains module, target, persona and audio policy; approval is still required and upload
stays disabled. Filename/path scoping is not proof that the text was reviewed or that the media
contains the approved narration.

**AI-VOICE only; no Soundboard.** Script sequencing and live source retrieval are not built by
this change. The [future question-pause scope](../../docs/architecture/stream-personality-audio-routing.md#scripted-pause-boundary)
preserves the cursor, bounds one question, defers unsupported answers and resumes after policy
approval; it remains disabled pending its own runtime implementation and acceptance.

---

## The hybrid playbook (MARKETING.md)

This repository's own go-to-market plan is [`MARKETING.md`](../../MARKETING.md) at the repository root.
It keeps OpenTechnologyApp's section numbering, is registered as the `marketing_playbook` doc of the
`hybrid-creator-platform` target in `crosswalk/targets.yml` (so `validate` fails if a heading is renamed),
and is listed as `files.marketing_doc` on the `stream-extend` and `content-extend` rows. It repeats
registry data on purpose — ICPs, the persona chain, the shipped list, the engine order — and
`tests/marketing_crosswalk/test_playbook.py` fails when a copy drifts from the YAML or the stream config.

## The three rules that make output trustworthy

**1. Status is evidenced, and the evidence is re-read every run.**

Each subject declares a `status` *and* the file and text in the target repo that establishes it.
`validate` re-reads that line. If `templates/device-audit/README.md` stops saying
`**Status:** Target architecture.`, that is a status change the generator surfaces rather than
papers over.

Assets are `claim_level: roadmap` (brief or describe — safe at any status) or `shipped` (assert
it works). A `shipped` asset will not render for a subject below `shipped`. Blocked assets are
reported with their evidence line — they are not defects.

**2. A private repo link never reaches a draft.**

`TEMPLATE_REPO_CROSSWALK.md` § Known gaps: *"Job Hunter is public; everything else is private.
Linking a Hybrid_Creator_Platform doc in any public-facing material (the blog, the course)
produces a 404 for readers."* Generated copy is public-facing, so every rendered draft is scanned
for `github.com/OpenTechnology14/*` URLs and rejected unless the repo is the subject's own public
upstream. A private upstream renders as an explicit "do not link" note instead.

**3. `--apply` never edits a marketing doc in place.**

It writes to `docs/readable/crosswalk-drafts/` in the target repo. Moving a draft into
`MARKETING.md` is a human's decision. Every draft carries a DRAFT banner, the source commit, the
status and its evidence, and a "before publishing, a human must" checklist naming what the
generator could not know — a real metric, a screenshot, a verified competitor claim.

---

## Layout

```
crosswalk/
  modules.yml               Registry of modules the Content Platform generates content for
  subjects/<module>.yml     What the content is about, per module
  targets.yml               Target repos, their marketing docs, and each anchor's exact heading
  products.yml              Product identity and canonical links (MARKETING.md §1, §3e)
  icps.yml                  ICPs, transcribed from MARKETING.md §2
  assets.yml                Asset catalogue: template, claim_level, engine step, landing anchor
templates/                  One markdown template per asset. {{ placeholder }} only
generator/                  status.py · crosswalk.py · render.py · coverage.py · cli.py
out/                        Generated drafts (gitignored — regenerate, never commit)
```

## Onboarding the next module

This is the "separate step" for any module not yet registered, or any other consumer.

1. Add a row to `crosswalk/modules.yml` naming its `target` and `subjects` file.
2. Add `crosswalk/subjects/<module>.yml`. Every subject needs `status` **and** a
   `status_evidence` file + text that exists in the target repo.
3. If the target is a new repo, add it to `crosswalk/targets.yml` with the exact heading text
   of every anchor content will land under.
4. `python3 -m generator.cli validate` — it fails on any unresolved ICP, channel, asset, anchor,
   or status claim.
5. `python3 -m generator.cli coverage --module <name>` then `generate --dry-run`.

## Adding an asset type

1. Add an entry to `crosswalk/assets.yml` with `template`, `claim_level`, and `lands_in`.
2. Write `templates/<name>.md.tmpl`. Placeholder names are listed in any `RenderError`.
3. Add the asset to the `assets:` list of each subject that should produce it.
4. `python3 -m generator.cli selftest` — this renders the new template even when claim gating
   would block it for every subject today.

## Local vs DigitalOcean

No difference, and nothing to deploy. This module reads the configured local git checkouts and writes
markdown. It has no service, no port, no container, and no `docker-compose.yml` entry.

## Known gaps

**content-extend**

- **The product name is unsettled, and it blocks publication.** `REPOSITORY_ALIGNMENT.md`
  §"Naming decision" states the product and repository are **ContentExtend**, while `README.md`,
  the roadmap, `product-spec.md`, and the live domain all say *Creator Extend* / creatorextend.com.
  Every `guide-page` and `comparison-page` draft carries a warning banner about this, generated
  from the product's `alias` field. Nothing publishable should ship under either name until a
  rename proposal resolves it.
- **Three shared modules have no creatorextend.com page** — `automation-control`, `storage-data`,
  and `creator-experience`. The last is the sharper one: its guide page exists but only at
  `streamextend.com/guides/obs-setup`, so a Creator Extend reader gets sent to the other product's
  site. Recorded as `guide page` gaps with the Stream URL alongside.

**stream-extend**

- **Four modules have no planned website page** — `automation-control`, `backend-api`,
  `storage-data`, `character-avatar` are absent from `product-spec.md`'s URL table. Reported as
  `guide page` gaps by `coverage`.
- **Every subject is `scaffolded`**, so all 16 shipped-claim assets are blocked. That is the
  honest state per `CLAUDE.md` §11 and `docs/AUDIT.md`, not a defect — promoting a module there
  unblocks its assets, and `validate` fails until this file's `status` is updated to match.

**task-management**

- **`site_monitoring` is absent from the coverage ledger.** `BLOG_MARKETING_CONNECTION.md` §2
  lists five templates; the app ships six. Recorded as `in_ledger: false` and reported by
  `coverage` rather than silently filled in.
- **The `email` channel is gated on Brevo segmentation.** `MARKETING.md` §3f documents one
  combined "IT/consulting/MSP" tag. Splitting it is a manual dashboard step that must happen
  before any targeted send.
- **`directories` shows zero subjects** in `coverage`. Expected — see the note above on why
  directory listings are product-level.
- **Anchors match on exact heading text.** A reworded heading in the target repo is reported as
  drift. Deliberate: a fuzzy match would place content under the wrong section.
