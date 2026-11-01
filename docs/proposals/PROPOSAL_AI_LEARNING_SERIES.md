# Proposal: AI Learning Series marketing module

**Coverage refresh, 2026-10-08:** all four public lesson-preview URLs returned HTTP 200
and their H1 titles matched the blog source. The [series index](../learning/README.md)
records the URLs. Blog coverage/counts now reflect four published written previews;
lesson-airing status remains Outlined/scaffolded. No broadcast or creative approval is
implied by page availability. CT-R10/CT-R14 are resolved in the content lane.
Verification: full required offline `make test` reached 100%, exit 0; crosswalk validation
passed 55 anchors/47 claims, and selftest rendered 238 pairs with zero failures.

**Queue row:** `P-064`
**Agent model / effort:** `gpt-6.1-sol` / `medium` — Lesson authoring and evidence-bound marketing drafts
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `In progress` — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md), not here

**Owner:** Owner + agent
**Date:** 2026-09-20
**Roadmap layer(s):** none new — extends `marketing-crosswalk` (`Content`), delivers through Stream Extend and Creator Extend
**Evidence level:** Verified (registry loads, 165 template pairs render) / Proposed (everything after lesson 1)

## 1. Executive summary

The owner asked for a marketing module covering OpenTechApp, Creator Extend, Stream Extend,
OpenTechnologyBlog and the crosswalks, teaching AI in a fixed order: **model usage → prompting with
project and context → app building with documentation structure, rules and skills → cutting cost
with an AI workflow (last)** — each lesson streamed live using Stream Extend and Creator Extend.

The smallest correct shape is **one new `marketing-crosswalk` registry module, `ai-learning`**, not a
new top-level `modules/` directory. `marketing-crosswalk` already generates content *for*
registered consumers (`task-management`, `stream-extend`, `content-extend`); a fourth consumer is a
registry row plus a subjects file. No new runtime, service, or app.

Lesson sources live in this repo (`docs/learning/`); the blog is the delivery target; the app and product sites are linked surfaces tracked in the coverage ledger.

## 2. Verified current state

- `modules/marketing-crosswalk` registers three consumers; `validate`, `coverage`, `selftest` and
  `generate` exist (`modules/marketing-crosswalk/generator/cli.py`).
- A module has exactly **one** target repo (`crosswalk/modules.yml`). Four delivery surfaces
  therefore cannot each be a target; see §5.
- `stream-extend` and `content-extend` use this repo as their target. `ai-learning` differs: its
  content is delivered to the blog but authored here, which the loader could not express until
  `status_evidence.target` was added (§5).
- The Creator Extend / ContentExtend name is unresolved (`crosswalk/products.yml`); series copy
  must not publish under either name.

## 3. Problem, goals, and non-goals

**Goals**

1. Register the series so `validate` fails loudly when its source doc drifts.
2. Track, per lesson, whether each of five surfaces exists (stream, blog, OpenTechApp link,
   Stream Extend link, Creator Extend link) — every `no` is a reported gap.
3. Generate lesson-shaped drafts: a blog brief and a stream run of show (new templates), plus the
   existing X thread and comment-ammo assets.

**Non-goals**

- No content is published, streamed, or posted by this proposal.
- No edits to the OpenTechnologyBlog or Task-Management repos except drafts written under
  `generate --apply` into the blog's `docs/crosswalk-drafts`; a human moves them into `content/blog`
  and adds the inventory row in the same PR. Not run yet.
- Reddit and LinkedIn assets are not declared: their templates are written for product templates
  and their `shipped` claim level would misstate a lesson. Add lesson-shaped versions after lesson 1 airs.
- No model names, prices or limits are stated anywhere — they go stale. Each is a pre-air checklist item.

## 4. User paths and states

Lesson lifecycle: `Outlined` → drafts generated → rehearsed off-air → streamed → `Aired` (syllabus
row and subject `status_evidence` edited together) → post published → surface coverage cells flip
to `yes`. A lesson never claims to have aired before that row changes.

## 5. Architecture and data flow

One registry row, one subjects file (`crosswalk/subjects/ai-learning.yml`), one product
(`ai-learning`), and one target: **`opentechnology-blog`** (added 2026-09-20), where the written
lessons publish and drafts are applied (`docs/crosswalk-drafts`). Lessons are authored in this repo,
so each subject's `status_evidence.target: hybrid-creator-platform` reads status from
`docs/learning/README.md` — a small generator addition, covered by
`tests/marketing_crosswalk/test_evidence_target.py`. The "four surfaces" requirement is met by
the `coverage` ledger and the lesson delivery table, not by four targets — the generator's
one-target-per-module rule is kept rather than bent. Local-first: no network, no keys, no services.

## 6. Direct injection map

| Location | Change |
|---|---|
| `modules/marketing-crosswalk/crosswalk/modules.yml` | `ai-learning` row (`kind: series`) |
| `…/crosswalk/subjects/ai-learning.yml` | four lesson subjects, three ICPs, four channels |
| `…/crosswalk/products.yml`, `targets.yml`, `assets.yml` | product, `opentechnology-blog` target (+ `ai_learning` anchors on this repo's target), two assets |
| `…/generator/crosswalk.py` | `evidence_root()` — optional `status_evidence.target` |
| `tests/marketing_crosswalk/test_evidence_target.py` | four offline tests; three fail with the change reverted |
| `…/templates/lesson-brief.md.tmpl`, `stream-runofshow.md.tmpl` | new lesson-shaped templates |
| `docs/learning/README.md`, `lesson-01-…` to `lesson-04-…` | series index and lesson sources |

## 7. Contracts and examples

```bash
cd modules/marketing-crosswalk
python3 -m generator.cli coverage --module ai-learning
python3 -m generator.cli generate --module ai-learning --subject model-usage
```

## 8. Security, privacy, accessibility, and observability

No credentials, no network. Private-repo link guard (`check_private_links`) applies to every draft.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| T1 | Syllabus row edited without updating subject evidence | `validate` errors on that subject | `validate` | Yes |
| T2 | Every declared (lesson, asset) pair | Renders, no leftover `{{ }}` | `selftest` | Yes |
| T3 | Docs index / proposal-row / link integrity | Pass | `tests/docs` | Yes |

## 10. Delivery plan

| Phase | Scope | State |
|---|---|---|
| 1 | Proposal, registry scaffold for four lessons, lesson 1 drafts | Done 2026-09-20 — see §14 |
| 2 | Lesson 1 rehearsal, stream, publish; flip `Aired` | Open |
| 3 | Lesson source docs for all four lessons | Done 2026-09-20 |
| 4 | Lesson-shaped Reddit/LinkedIn templates | Open — after lesson 1 airs |

## 11. Rollout and rollback

Additive. Rollback = delete the `ai-learning` rows, subjects file, two templates and `docs/learning/`.

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation/decision owner | Due |
|---|---|---|---|
| ICPs are derived from lesson topics, not measured demand | Wrong audience | Owner validates before publishing | Before lesson 1 airs |
| `status` vocabulary (`scaffolded`…`shipped`) was written for products; its meaning text reads oddly for a lesson | Confusing drafts | Accept for now; a `lesson` status set is a later change | Owner |
| Creator Extend name unresolved | Cannot publish named references | Existing rename proposal path | Owner |
| Blog target | Resolved 2026-09-20 — `opentechnology-blog` is the module target | — | — |

## 13. Documentation updates

`docs/README.md` (index), `docs/PROPOSALS.md` (row), `modules/marketing-crosswalk/README.md` and
`crosswalk/schema.md`, `docs/agent/MODULE-ITEM-MATRIX.md`.

## 14. Verification (2026-09-20)

Run in a scratch venv with `requirements.txt`: registry loaded 4 modules / 30 subjects; `selftest`
rendered 165 pairs with 0 failures; no `validate` finding names `ai-learning` (including the new
blog target's `## Posts` anchor and each lesson's evidence read from this repo); four lesson-1
drafts generated with no unfilled placeholders; `tests/marketing_crosswalk` 4 pass, 3 fail with
`crosswalk.py` reverted. **`validate` overall still exits 1** on a pre-existing,
unrelated `task-management.yml` evidence edit that was uncommitted before this work.
