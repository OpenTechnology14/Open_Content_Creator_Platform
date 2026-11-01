# Lesson 3 — App building: documentation structure, rules, and skills

> **Status:** Outlined · **Series:** [AI Learning Series](README.md) · **Queue:** P-064
> **Builds on:** [Lesson 1 — Model usage](lesson-01-model-usage.md) and
> [Lesson 2 — Prompting and context](lesson-02-prompting-context.md)

## The promise

After this lesson the viewer can give a repository three things — a documentation structure the
model can navigate, rules it must follow, and skills it can reuse — and can say which of the three
a given piece of guidance belongs in.

## Builds on lessons 1 and 2

Lesson 2's standing project context was one blob. This lesson splits it into layers with different
jobs, so each session loads only what it needs (lesson 1's context-window cost, applied). Both
lessons are assumed; segment 1 recaps them in one minute.

## What this lesson deliberately does not cover

- Measuring or reducing spend — lesson 4. This lesson may mention that smaller loaded context is
  cheaper but puts no numbers on it.
- Building a full application from scratch. The build here is small on purpose; the subject is the
  structure around it.

## The worked example: this repository

The lesson uses a real repo the viewer can read instead of a toy. Everything below exists today and
was checked on 2026-09-20; re-check before airing.

| Layer | Real example | What it shows |
|---|---|---|
| Entry-point rules | `CLAUDE.md`, mirrored in `AGENTS.md` for other agents | One file read first; what to do and what **not** to do |
| Enforced, not just written | `tests/docs/test_docs_integrity.py` fails when `CLAUDE.md` and `AGENTS.md` drift | A rule a test holds is stronger than a rule a paragraph asks for |
| Decision queue | `docs/PROPOSALS.md` | Work is authorized in writing before it starts |
| Change-impact table | `docs/agent/DOC-UPDATE-MATRIX.md` | "If you change X, these docs go stale" — read instead of rediscovered |
| Proof of done | `docs/agent/VERIFICATION-MATRIX.md` | What "verified" means per kind of change |

This repo has **no project skills directory** today. Skills are therefore built live in segment 5,
not shown from existing files — the lesson must not imply one exists.

## Segments

| # | Segment | On-screen proof |
|---|---|---|
| 1 | Recap of lessons 1 and 2, then the problem: a model that re-learns the project every session and quietly breaks its conventions | A fresh session making a change that violates an unwritten convention |
| 2 | Documentation structure: an index, one owner per fact, and a change-impact table so docs stay findable and current | The docs index and `DOC-UPDATE-MATRIX.md` opened; one change traced through it |
| 3 | Rules: what belongs in the always-loaded file vs. a linked doc; write the *don'ts* and the *why* | `CLAUDE.md` §10 (what not to do) and how a rule cites its reason |
| 4 | Make a rule enforceable: turn one written rule into a failing test | The `CLAUDE.md`/`AGENTS.md` pairing test, broken on purpose, then fixed |
| 5 | Skills: a repeatable procedure the model loads only when needed — write one live for a task the viewer repeats | A new skill created, then invoked on a real task, output compared to no skill |
| 6 | Which layer? A decision guide: fact → docs, always-true constraint → rules, repeatable procedure → skill | Five pieces of guidance sorted live, one deliberately wrong and corrected |
| 7 | Recap: a one-page "structure a repo for AI" checklist the viewer keeps | The checklist, on screen and in the blog post |

## Facts that must be verified before airing

- [ ] Every path in the worked-example table still exists and says what this outline says
- [ ] What the tool shown calls a rules file and a skill, where each lives, and how each is loaded
- [ ] Whether skills are loaded on demand or always, in the tool shown — segment 5's claim depends on it
- [ ] Whether the rules-file size guidance in this outline still matches the provider's current advice
- [ ] The skill built on stream is one the presenter actually reuses; do not invent a demo need

## Deliverables

| Surface | Deliverable | Generated with |
|---|---|---|
| Stream | Run of show | `--asset stream-runofshow` |
| Blog | Source post brief | `--asset lesson-brief` |
| X | Thread from the recorded clips | `--asset x-thread` |
| Reply threads | F5Bot reply skeleton | `--asset comment-ammo` |
