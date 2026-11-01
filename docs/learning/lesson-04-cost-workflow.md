# Lesson 4 — Cutting cost with an AI workflow

> **Status:** Outlined · **Series:** [AI Learning Series](README.md) · **Queue:** P-064
> **Builds on:** lessons [1](lesson-01-model-usage.md), [2](lesson-02-prompting-context.md) and
> [3](lesson-03-app-building.md) — this lesson is last on purpose

## The promise

After this lesson the viewer can measure what one AI task costs, find where the spend actually
goes, and cut it with changes they can name — without making the result worse. The claim the
lesson earns is **"less for the same result, measured on screen"**, never a percentage quoted from
elsewhere.

## Why it is last

Cutting cost is choosing among levers the earlier lessons taught:

| Lever | Taught in | Cost effect to demonstrate |
|---|---|---|
| Right-size the model for the job | Lesson 1 | Same task on a smaller model — does it still pass? |
| Send less, better-chosen context | Lessons 1 and 2 | Whole file vs. relevant section — tokens and result compared |
| Get it right the first time | Lesson 2 | Acceptance criteria up front — fewer retry rounds |
| Load only what a task needs | Lesson 3 | Layered docs, rules and skills instead of one large always-loaded blob |

A viewer who skipped those has nothing to cut. Segment 1 says so plainly.

## What this lesson deliberately does not cover

- Provider negotiation, enterprise discounts, or self-hosting models to avoid API spend.
- Any price, discount, or savings percentage stated as fact. Numbers on screen come from the
  presenter's own usage that week, shown with their source.

## Segments

| # | Segment | On-screen proof |
|---|---|---|
| 1 | Recap: the four levers above; you cannot cut what you have not measured | The lever table |
| 2 | Baseline: pick one real repeated task, run it as it is today, record tokens in and out, retries, and pass/fail | The recorded baseline, before any change |
| 3 | Find where it goes: which step, which context, which retries account for the spend | The baseline broken down by step |
| 4 | Apply one lever at a time, re-measure each, keep only what does not lower quality | A running table: change, tokens, cost, still passes? |
| 5 | Workflow shape: split a task so cheap steps run on a small model and only the hard step on a large one; batch work that is not urgent | The task rebuilt as a multi-step workflow, run end to end |
| 6 | Guardrails: a stop condition and a budget on any automated loop so a mistake cannot run up a bill unattended | A loop deliberately made to overrun, stopped by its limit |
| 7 | Final table: before vs. after for cost **and** quality; say what got worse, if anything | The full table, on screen and in the blog post |

## Rules for the lesson

- Quality is measured alongside cost every time. A cheaper run that fails the check is a loss, not
  a saving, and stays in the table as one.
- One lever per re-run, or the table cannot say what worked.
- If a lever gave no saving, show it. Leaving it out would misstate the method.

## Facts that must be verified before airing

- [ ] Current price per model and whether input, output and cached input are billed differently —
      taken from the provider's pricing page **that week**, with the date shown on screen
- [ ] Whether prompt caching and batch processing exist for the model and tool shown, what they
      are called, and their constraints
- [ ] How the tool shown reports token usage per request, so the baseline is real and not estimated
- [ ] That the chosen task is one the presenter genuinely repeats, and is safe to run on stream
- [ ] Any spend limit or usage cap features in the tool shown, for segment 6

## Deliverables

| Surface | Deliverable | Generated with |
|---|---|---|
| Stream | Run of show | `--asset stream-runofshow` |
| Blog | Source post brief | `--asset lesson-brief` |
| X | Thread from the recorded clips | `--asset x-thread` |
| Reply threads | F5Bot reply skeleton | `--asset comment-ammo` |

Because this lesson's promise is a measured result, the blog post must publish the presenter's own
baseline and final table. If the measured saving is small or zero, the post says so.
