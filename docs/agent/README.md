# Agent working docs

> **Status:** Living · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14

Reference material for working this repository with an AI agent. Full instruction/registry
freshness now fires through the offline suite and CI; semantic review rules still need an
agent to apply them before starting work.

For every proposal item, **set the best available model for the work**, its reasoning effort and
rationale in [the proposal queue](../PROPOSALS.md#agent-model-selection), then select it in the
execution client. The queue and detailed proposal must agree. Check availability and reassess the
choice when scope changes; child tasks inherit the assignment unless an override is recorded.
Sol 6.1 is the coding default; Astra is an explicit exception for demanding integration or
escalation. The same acceptance requirements apply to both.

| Doc | Answers |
|---|---|
| [Proposal assignment review](PROPOSAL-ASSIGNMENTS.md) | Who owns every proposal, which bounded Terra/Luna children fit, and which inputs still gate execution? |
| [`MODULE-MATRIX.md`](MODULE-MATRIX.md) | How much depends on this module, and how expensive is it to stand up? |
| [`MODULE-ITEM-MATRIX.md`](MODULE-ITEM-MATRIX.md) | What does this module actually own — services, ports, buckets, scripts, config? |
| [`SUBFEATURE-CHECKLIST.md`](SUBFEATURE-CHECKLIST.md) | Which module subfeatures are built, automatically proven, or waiting on a live/manual pass? |
| [`DOC-UPDATE-MATRIX.md`](DOC-UPDATE-MATRIX.md) | I changed X — which docs just went stale? |
| [`VERIFICATION-MATRIX.md`](VERIFICATION-MATRIX.md) | I changed X — what proves it works, and what is *not* enough? |

Related, outside this directory:

| Doc | Answers |
|---|---|
| [`../SETUP-TECHNIQUE-NOTES.md`](../SETUP-TECHNIQUE-NOTES.md) | What friction will I hit while actually doing a setup? |
| [`../PROJECT_CROSSWALK.md`](../PROJECT_CROSSWALK.md) | How do products and roadmap modules connect to proposals and acceptance evidence? |
| [`../DOCUMENTATION_WORKFLOW.md`](../DOCUMENTATION_WORKFLOW.md) | Which important documents should I maintain, and what can the existing generator produce? |
| [`../PROPOSALS.md`](../PROPOSALS.md) | Is this work authorized, and what state is it in? |
| [`../todo/README.md`](../todo/README.md) | What is waiting on a person — which owner decisions and live runs are open, in which lane? |
| [`../PROPOSAL_CREATION_SOP.md`](../PROPOSAL_CREATION_SOP.md) | How do I write a proposal that will be accepted? |
| [`../design/BUILD-PROMPTING-DIGEST.md`](../design/BUILD-PROMPTING-DIGEST.md) | How do I prompt an agent to extend this repo, and which skill under `.claude/skills/` fits the task? |
| [`../architecture/future-state.md`](../architecture/future-state.md) | What are we aiming at, and what is the next highest-leverage move? |
| [`../../modules/README.md`](../../modules/README.md) | Which modules exist, what are their labels, and in what order? |
