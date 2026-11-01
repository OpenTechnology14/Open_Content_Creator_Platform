# Lesson 1 — Model usage

> **Status:** Outlined · **Series:** [AI Learning Series](README.md) · **Queue:** P-064

## The promise

After this lesson the viewer can look at a task and say which model to use for it, how much
context to give it, and roughly what that will cost — before they type anything.

## What this lesson deliberately does not cover

- Prompt wording and project setup — lesson 2.
- Rules files, skills, and documentation structure — lesson 3.
- Reducing spend — lesson 4. Lesson 1 only teaches the *vocabulary* of cost (tokens, context,
  input vs output) so lesson 4 has something to stand on.

## Segments

| # | Segment | On-screen proof |
|---|---|---|
| 1 | The model line-up and what "bigger" buys you: capability, speed, and price move together, not independently | Same task run on a small and a large model, results side by side |
| 2 | Match the model to the job: lookup and classification vs. drafting vs. multi-step reasoning vs. long-running agent work | Three real tasks from this repo, each assigned a model with a stated reason |
| 3 | Context window: what fits, what silently falls off, and why more context is not always better | A long file pasted in whole vs. only the relevant section |
| 4 | Tokens: input vs. output, how to estimate before you send | Token count of a real prompt and its response |
| 5 | Effort / thinking settings — when extra reasoning pays for itself | One hard task at low and high effort |
| 6 | Recap: a one-page "which model" decision table the viewer keeps | The table, on screen and in the blog post |

## Facts that must be verified before airing

This outline states no current model names, prices, or limits, on purpose — they go stale between
outlining and airing. Before going live, check each against the provider's current documentation
and record the date checked here:

- [ ] Current model names and which tier each sits in
- [ ] Context window size per model
- [ ] Input and output price per model (do **not** show a price that was not re-checked that week)
- [ ] Whether the effort/thinking setting exists on the models shown, and what it is called

## Deliverables

| Surface | Deliverable | Generated with |
|---|---|---|
| Stream | Run of show | `--asset stream-runofshow` |
| Blog | Source post brief | `--asset lesson-brief` |
| X | Thread from the recorded clips | `--asset x-thread` |
| Reply threads | F5Bot reply skeleton | `--asset comment-ammo` |
| Reddit, LinkedIn | Not generated yet — needs lesson-shaped templates after lesson 1 airs | — |
