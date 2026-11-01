# Documentation index

> **Status:** Living · **Last reviewed:** 2026-09-30 · **Owner:** OpenTechnology14

The operating record for the Open Content Creator Platform. **A doc that is not in this index is a doc
nobody opens** — `DM-DOCS-INDEX` in [`agent/DOC-UPDATE-MATRIX.md`](agent/DOC-UPDATE-MATRIX.md)
fires on every new file under `docs/`.

> Found 7 files stale on 2026-08-31, which is why that rule now exists.

## Start here

For a task-focused introduction, open the [documentation website](public/index.html).
The [first-recording narration, glossary and FAQ](BEGINNER_WALKTHROUGH.md) provide reviewable
walkthrough material; capture and publication remain separate acceptance steps.
It separates first-time streaming, recording-to-clip guidance and engineering review.
It is local website source, not a deployed public service. The
[marketing and documentation review](PUBLIC_DOCS_AND_MARKETING_REVIEW.md) records the
reference comparison, release decisions and remaining publication work.

| Document | Purpose |
|---|---|
| [Module index](../modules/README.md) | Every module, its labels, and setup order per product — **the root of understanding any feature** |
| [Architecture roadmap](architecture/roadmap.md) | Canonical layers, module map, and sequencing |
| [Project crosswalk](PROJECT_CROSSWALK.md) | Products, all 21 roadmap modules, proposals and acceptance evidence in one map |
| [Product overview](PRODUCT_OVERVIEW.md) | The product and commercial description formerly in the root README: plans, self-hosting, features by module |
| [Essential document workflow](DOCUMENTATION_WORKFLOW.md) | Which documents to maintain, how to verify them, and how to generate marketing drafts |
| [Marketing playbook](../MARKETING.md) | Go-to-market plan for Stream Extend and Creator Extend — positioning, ICPs, channels, content engine, 30-day plan; a registered marketing-crosswalk artifact |
| [Streaming personality audio routing](architecture/stream-personality-audio-routing.md) | Quick map for gaming Soundboard reactions versus OpenTech/technical scripted AI voice |
| [Future state](architecture/future-state.md) | North-star, pillars, horizons, candidate modules — the compass |
| [Proposal queue](PROPOSALS.md) | What work is authorized, and what state it is in |
| [Owner decisions and runs](todo/README.md) | What is waiting on a person — decisions and live runs, by lane: content create and stream |
| [Application audit](AUDIT.md) | Evidence-backed readiness verdict — read before believing any capability claim |

## Working the repo with an agent

[Generated registries](agent-registries/README.md) enforce instruction/source freshness
alongside the existing readable matrices and proposal queue.

[Complete proposal assignment review](agent/PROPOSAL-ASSIGNMENTS.md): all 73 primary
assignments, bounded Terra/Luna children, and preserved execution/acceptance boundaries.

| Document | Answers |
|---|---|
| [Agent docs index](agent/README.md) | What reference material exists |
| [Module usage & complexity matrix](agent/MODULE-MATRIX.md) | What depends on this module, and how expensive is it to stand up? |
| [Module item matrix](agent/MODULE-ITEM-MATRIX.md) | What does this module own — services, ports, buckets, scripts, config? |
| [Module subfeature checklist](agent/SUBFEATURE-CHECKLIST.md) | Which subfeatures are built, automatically proven, or waiting on a live/manual pass? |
| [Doc update matrix](agent/DOC-UPDATE-MATRIX.md) | I changed X — which docs just went stale? |
| [Verification matrix](agent/VERIFICATION-MATRIX.md) | I changed X — what proves it works locally, and what is **not** enough? |
| [Design system hub](../design-system/README.md) | Tokens, component specs, voice registers, iconography and accessibility for the ecosystem — drafted, awaiting owner review; downstream repositories keep pointer docs, not copies |
| [Build prompting digest](design/BUILD-PROMPTING-DIGEST.md) | How do I prompt an agent to extend this repo — crosswalk discipline, marketing parity, voice guidance, and where the stream setup came from? Task playbooks live in `.claude/skills/` (`CLAUDE.md` §14) |
| [Setup technique notes](SETUP-TECHNIQUE-NOTES.md) | What friction will I hit while doing a setup? |
| [Setup automation audit](SETUP-AUTOMATION-AUDIT.md) | Which installer/app setup actions are ready to move out of AI-operated shell work? |
| [Acceptance checklist](../tests/ACCEPTANCE-CHECKLIST.md) | What must be true for a module — and the platform — to be done |
| [Use-case walkthroughs](../tests/USE-CASES.md) | Two flagship workflows covering all 21 modules — does the whole thing compose? |

## Setup and operation

| Document | Purpose |
|---|---|
| [Image intake](IMAGE_INTAKE.md) | Feeding your own photographs in — buckets, provenance, rights and format matrices, tips |
| [Guides redirect map](guides/README.md) | Where each retired numbered guide's content went |
| [Stream Extend production setup](guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) | Clean checkout → public gaming stream: prerequisites, capture hardware, Twitch + YouTube, games, build, profile switching, go-live and failure recovery |
| [Creator Extend production setup](guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) | Clean checkout → published YouTube video: prerequisites, build, recording handoff, content pipeline, publishing and failure recovery |
| [AI Learning Series](learning/README.md) | Four-lesson streamed AI series — syllabus, stream format, delivery surfaces (P-064); [lesson 1](learning/lesson-01-model-usage.md), [lesson 2](learning/lesson-02-prompting-context.md), [lesson 3](learning/lesson-03-app-building.md), [lesson 4](learning/lesson-04-cost-workflow.md) |
| [Disaster recovery](architecture/disaster-recovery.md) | Backup and restore runbook |

## Proposals and process

[Open the proposal dashboard](proposal-dashboard.html) to select Hybrid Platform or MyFeed,
review Testing and remaining features, and prepare a bounded work request. See the
[dashboard workflow and refresh guide](PROPOSAL_DASHBOARD.md).

[P-063 setup scope and dated evidence](proposals/PROPOSAL_IN_APP_SETUP.md) now owns the
installer history; the queue retains its original inbound anchor as a redirect.

| Document | Purpose |
|---|---|
| [Proposal queue](PROPOSALS.md) | State of every proposal — the source of truth |
| [Proposal dashboard tracker](proposals/PROPOSAL_DOCUMENT_GAPS.md#proposal-dashboard-tracking) | Work-section breakdown, Testing rules and dashboard refresh contract under P-071 |
| [Proposal creation SOP](PROPOSAL_CREATION_SOP.md) | How to write one that will be accepted |
| [Proposal template](proposals/TEMPLATE_PROPOSAL.md) | The starting shape |
| [Content create to-do](todo/CONTENT_CREATE_TODO.md) | Content decisions and runs waiting on you |
| [Stream decisions and to-do](todo/STREAM_DECISIONS_AND_TODO.md) | Stream decisions, live runs and testing waiting on you |
| [Future documents](FUTURE_DOCS.md) | Documents that do not exist yet, each with a state and a trigger |
| [`proposals/`](proposals/) | Full proposal documents, linked from queue rows |

## Architecture and decisions

| Document | Purpose |
|---|---|
| [Product spec](architecture/product-spec.md) | App architecture, pricing, build order, guides-as-content |
| [Repository alignment](architecture/../REPOSITORY_ALIGNMENT.md) | Canonical ownership and standalone export policy |
| [Deviations](architecture/deviations.md) | Where reality diverged from the roadmap, and why |
| [Kubernetes decision](architecture/k8s-decision.md) | The four conditions that would justify it |
| [Future work](architecture/future.md) | Deferred items, each with the trigger that reopens it |

## Release gates and evidence

Recent local checks and on-demand audit findings: [capped audit log](AUDIT_LOG.md).

| Document | Purpose |
|---|---|
| [Open-source checklist](OPEN_SOURCE_RELEASE_CHECKLIST.md) | Release gates and required evidence |
| [Open-source release plan](proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md) | Every step to a publishable repository, which are done, and the owner gates (P-075) |
| [Third-party provenance](THIRD_PARTY_PROVENANCE.md) | Every third-party component with its license and flags |
| [Gap audit](GAP_AUDIT.md) | Prioritized gaps and acceptance criteria |
| [Full audit matrix](FULL_APPLICATION_AUDIT_MATRIX.md) | Surface-by-surface coverage |
| [API route ledger](API_ROUTE_AUDIT_LEDGER.md) | HTTP, WebSocket, and Tauri command inventory |
| [Pressure-test plan](PRESSURE_TEST_LOAD.md) | Reliability and failure-mode scenarios |
| [Implementation notes](IMPLEMENTATION_NOTES.md) | Decisions, constraints, and verification record |
| [Continuous improvement](CONTINUOUS_IMPROVEMENT.md) | Recurring audit cadence and metrics |

## Status vocabulary

Used throughout, and in `CLAUDE.md` §11:

| Status | Meaning |
|---|---|
| `scaffolded` | Directory, README, setup docs, and config present. **Not** working, tested, or documented |
| `implemented` | Working, tested, documented |
| `production` | Deployed locally **and** on DigitalOcean, monitored |

Currently **4 of 21 modules** are past `scaffolded`, all `implemented`: `marketing-crosswalk` and
`asset-pipeline`/`model-registry` (repo tools/infrastructure, not product capabilities) and
`storage-data` (2026-09-01, the first product module — see `P-016` in
[`PROPOSALS.md`](PROPOSALS.md) for the CI evidence). Nothing in these docs may claim otherwise.

## Retired

| Document | Retired | Why |
|---|---|---|
| `architecture/guide-review.md` | 2026-08-31 (P-014) | Reviewed the retired numbered guides; findings verifiably absorbed into module setup docs |
| `SUGGESTED_EXISTING_DOC_UPDATES.md` | 2026-08-31 (P-015) | A parallel backlog duplicating P-001's injection map; its two uncovered items moved to P-016/P-017 |
| `architecture/setup-readiness-proposal.md` | 2026-08-31 (P-003) | Not retired — **moved** to `proposals/PROPOSAL_SETUP_READINESS.md`; it was a proposal filed outside the proposal directory |
