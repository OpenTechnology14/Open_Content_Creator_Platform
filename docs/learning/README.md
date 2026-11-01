# AI Learning Series

> **Status:** Outlined — no lesson has aired · **Last reviewed:** 2026-10-08 · **Queue:** P-064

A four-lesson series on working with AI, taught by building — each lesson is streamed live and
then repurposed as a blog post and app/product links. It is content **about AI practice**, not a
product feature. The Content Platform generates its marketing drafts through the
`ai-learning` module of [`marketing-crosswalk`](../../modules/marketing-crosswalk/README.md).

The order is deliberate: cost comes **last** because you cannot cut what you have not yet
understood. Each lesson assumes the one before it.

## Syllabus

| # | Lesson | Status | Source |
|---|---|---|---|
| 1 | Model usage | Outlined | [lesson-01-model-usage.md](lesson-01-model-usage.md) |
| 2 | Prompting best practices — project and context | Outlined | [lesson-02-prompting-context.md](lesson-02-prompting-context.md) |
| 3 | App building — documentation structure, rules, and skills | Outlined | [lesson-03-app-building.md](lesson-03-app-building.md) |
| 4 | Cutting cost with an AI workflow | Outlined | [lesson-04-cost-workflow.md](lesson-04-cost-workflow.md) |

`Outlined` = the live lesson scope is written down; it has not been recorded or streamed. Written
previews can be published separately without promoting the live lesson. A
lesson moves to `Aired` only when the stream has happened, and `crosswalk/subjects/ai-learning.yml`
then updates its `status` and `status_evidence` together. Assets that would assert a lesson
already exists (Reddit show-and-tell, LinkedIn) are not declared for this module yet; add them
with lesson-shaped templates once lesson 1 has aired.

## Stream format

Every lesson is a live walkthrough, not a slide talk.

- **Broadcast with Stream Extend** — the lesson is streamed through the platform's own OBS
  control, scenes, and overlays, so the series doubles as a working demonstration of it.
- **Capture and edit with Creator Extend** — the VOD is cut into the clips and stills that feed the
  X thread and the blog post.
- **One build per lesson.** Every lesson works on a real task on screen. A claim with no on-screen
  proof is cut.
- **Run of show** is generated per lesson (`generate --asset stream-runofshow`).

## Where each lesson is delivered

| Surface | What it gets | Tracked as coverage key |
|---|---|---|
| Live stream | The lesson itself | `stream_episode` |
| OpenTechnologyBlog | The written lesson (SEO source post) | `blog_post` |
| OpenTechApp (Task-Management) | A link from the app's learning/help surface back to the lesson | `opentechapp_link` |
| Stream Extend site | A "watch the build" link on the relevant guide page | `stream_extend_link` |
| Creator Extend site | A "watch the build" link on the relevant guide page | `creator_extend_link` |

`coverage` reports each `no` cell as a gap. A cell flips to `yes` only when the surface exists.

**Written previews verified 2026-10-08:** all four public pages returned HTTP 200 and their
article headings matched the lesson source. `blog_post` coverage is now true; stream and app-link
coverage remain false. These are written lesson previews, not recordings of an aired lesson:

- [Lesson 1: Model usage](https://www.opentechnologyblog.com/blog/ai-learning-01-model-usage)
- [Lesson 2: Prompting, project and context](https://www.opentechnologyblog.com/blog/ai-learning-02-prompting-project-context)
- [Lesson 3: Documentation, rules and skills](https://www.opentechnologyblog.com/blog/ai-learning-03-app-building-docs-rules-skills)
- [Lesson 4: Cutting cost](https://www.opentechnologyblog.com/blog/ai-learning-04-cutting-cost-ai-workflow)

## Naming caveat

Creator Extend's product name is unsettled (`ContentExtend` per `docs/REPOSITORY_ALIGNMENT.md`).
Copy for this series names it only in the stream run of show; nothing may be published under
either name until the rename proposal resolves.
