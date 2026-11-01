# Lesson 2 — Prompting best practices: project and context

> **Status:** Outlined · **Series:** [AI Learning Series](README.md) · **Queue:** P-064
> **Builds on:** [Lesson 1 — Model usage](lesson-01-model-usage.md)

## The promise

After this lesson the viewer can turn a vague request into a prompt that holds up, and can set up a
project so the model starts every session already knowing the work — instead of re-explaining it
each time.

## Builds on lesson 1

Lesson 1 taught which model, how much context, and what it costs. This lesson decides **what goes
into that context**. The context-window and token vocabulary is assumed; if a viewer skipped
lesson 1, the recap in segment 1 points back rather than re-teaching it.

## What this lesson deliberately does not cover

- Rules files, skills, and repository documentation structure — lesson 3. Here, "project" means
  the standing context a model is given, not the full build-with-AI setup.
- Cutting spend — lesson 4.

## Segments

| # | Segment | On-screen proof |
|---|---|---|
| 1 | Recap of lesson 1 in one minute, then the problem: same model, very different results from different prompts | Two prompts for one real task from this repo, results side by side |
| 2 | Anatomy of a prompt that holds up: goal, context, constraints, output format, and what "done" looks like | The vague prompt rewritten live, piece by piece |
| 3 | Say how it will be checked: acceptance criteria and examples, so the model can verify its own work | Same task with and without criteria — does the output pass? |
| 4 | Project vs. chat: what belongs in standing project context and what belongs in a single prompt | A project set up on stream; one instruction moved from the prompt into the project |
| 5 | Feeding context: the relevant files, not everything; quoting the source instead of paraphrasing it | A long file pasted whole vs. the one relevant section — output and token count compared |
| 6 | Iterating: fix the prompt, not the output; when to start a fresh conversation | A failed run, diagnosed, the prompt corrected, re-run |
| 7 | Recap: a one-page prompt checklist the viewer keeps | The checklist, on screen and in the blog post |

## Facts that must be verified before airing

This outline states no product feature names, limits, or prices, on purpose. Before going live,
check each against current provider documentation and record the date checked here:

- [ ] What the tool shown calls its standing-context feature, and what it can hold
- [ ] Size limits on attached files / project knowledge in the tool shown
- [ ] Whether the model shown behaves differently with or without extended reasoning enabled
- [ ] Any advice in this outline that the provider's own prompting guide now contradicts

## Deliverables

| Surface | Deliverable | Generated with |
|---|---|---|
| Stream | Run of show | `--asset stream-runofshow` |
| Blog | Source post brief | `--asset lesson-brief` |
| X | Thread from the recorded clips | `--asset x-thread` |
| Reply threads | F5Bot reply skeleton | `--asset comment-ammo` |
