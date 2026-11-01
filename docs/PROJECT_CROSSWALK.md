# Project crosswalk

> **Status:** Living · **Last reviewed:** 2026-09-30 · **Owner:** OpenTechnology14

**Enforcement: reference.** This map connects the platform's products, roadmap modules,
work records and acceptance evidence. It is a manually maintained navigation document;
the linked sources govern scope and status. P-069 in the [proposal queue](PROPOSALS.md)
records this document's creation and verification.

## Sources and authority

| Question | Authoritative source |
|---|---|
| Where does a capability belong, and when should it be built? | [Roadmap](architecture/roadmap.md) |
| Which product selects a module? | [Module index](../modules/README.md) and [agent instructions](../AGENTS.md) §4 |
| Is work authorized; what remains? | [Proposal queue](PROPOSALS.md); follow the row's detailed proposal |
| What is implemented or actually accepted? | [Audit](AUDIT.md), dated proposal evidence and [module status](../AGENTS.md) §11 |
| What proves completion? | [Acceptance checklist](../tests/ACCEPTANCE-CHECKLIST.md), [verification matrix](agent/VERIFICATION-MATRIX.md) and each module's setup guides |
| Which consumer can receive generated marketing content? | [Marketing registry](../modules/marketing-crosswalk/crosswalk/modules.yml), its subjects and status evidence |

A completed proposal can cover one small implementation slice while its module remains
`scaffolded`. An offline test pass does not prove desktop, hardware, provider-account or
DigitalOcean acceptance. Read the dated evidence before using a capability in a product claim.

## Product and shared surfaces

| Surface | Source | Work and evidence entry points |
|---|---|---|
| Stream Extend | [Desktop app](../apps/stream-extend/), modules labelled `Stream` | P-052 desktop builds, P-055 OBS commands, P-056 Autopilot; [production setup](guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) |
| Creator Extend / ContentExtend | [Desktop app](../apps/creator-extend/), modules labelled `Content` | P-054 ComfyUI commands, P-057 workflow inputs; [production setup](guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) |
| Shared module setup and readiness | [Setup wizard](../apps/shared/setup-wizard/README.md), [setup engine](../apps/shared/setup-engine/README.md), [settings](../apps/shared/local-settings/README.md) | P-003 readiness and settings; P-063 app-first onboarding |
| Approved remote control | [Relay client](../apps/shared/relay-client/README.md) | P-058; two-device and native OS acceptance in the verification matrix |
| Recording handoff and profile/account routing | [Recording library](../apps/shared/recording-library/README.md), [Social Manager](../apps/shared/social-manager/README.md) | P-065 handoff; P-062 social connections and external actions |
| Standalone product exports | [Repository alignment](REPOSITORY_ALIGNMENT.md) | Export manifest, naming and release requirements; P-023 naming decision |

Product labels describe capability selection; they do not imply that every labelled module ships
in an app. In particular, the marketing crosswalk is a repository tool. The ContentExtend naming
policy and Creator Extend code/marketing names still need reconciliation through P-023; this map
preserves both names so readers can find the existing paths.

## Roadmap modules to work records

`C` = Content; `S` = Stream. Each module link opens its README and setup guides. Proposal IDs
below are selected traceability links into the [queue](PROPOSALS.md), not a complete history or
a statement that the proposal is accepted or finished. The [subfeature checklist](agent/SUBFEATURE-CHECKLIST.md#module-test-workflow-index)
links every module to its exact automated, manual and acceptance workflows.

| Module / roadmap responsibility | Labels | Related proposal records |
|---|---|---|
| [creator-experience](../modules/creator-experience/README.md) — OBS capture, scenes and recording | C, S | P-027 scenes; P-055 OBS control; P-065 managed recording |
| [soundboard](../modules/soundboard/README.md) — named local reaction clips | C, S | P-044 soundboard; P-066 proposed reaction audio |
| [realtime-ai](../modules/realtime-ai/README.md) — local effects and ComfyUI | C, S | P-028 workflows; P-054 ComfyUI service path; P-057 inputs |
| [sports-analytics](../modules/sports-analytics/README.md) — tracer, pose and replay | C | P-040 calibration and tests |
| [character-avatar](../modules/character-avatar/README.md) — avatar rendering and playback events | S | P-042 control bridge; P-056 timed avatar runtime |
| [automation-control](../modules/automation-control/README.md) — workflows, show planning and orchestration | C, S | P-033 n8n wiring; P-056 Autopilot |
| [backend-api](../modules/backend-api/README.md) — authenticated HTTP/WebSocket contracts | S | P-026 API hardening; P-053 route trust boundaries |
| [storage-data](../modules/storage-data/README.md) — Postgres, Redis and MinIO | C, S | P-024 setup; P-016 live acceptance harness |
| [asset-pipeline](../modules/asset-pipeline/README.md) — shared object-storage contract | C, S | P-017 shared library |
| [model-registry](../modules/model-registry/README.md) — model provenance, checksum and license | C, S | P-018 registry |
| [observability](../modules/observability/README.md) — metrics, logs and dashboards | S | P-025 observability configuration |
| [infrastructure](../modules/infrastructure/README.md) — local services, private cloud and deployment | S | P-035 deploy contracts; P-063 onboarding; P-020 deferred Kubernetes |
| [content-creation](../modules/content-creation/README.md) — Blender, editing and Shorts | C | P-036 addon inventory; P-056 Shorts; P-061 Blender jobs; P-065 inbox |
| [image-editing](../modules/image-editing/README.md) — Krita, inpainting and mobile edits | C | P-037 presets; P-043 local GPU workflow evidence |
| [nature-generation](../modules/nature-generation/README.md) — landscape grading and learned tiers | C | P-011 module boundary; P-041 Tier 0; P-059 learned tiers |
| [cityscape-generation](../modules/cityscape-generation/README.md) — urban grading, perspective and learned tiers | C | P-011 module boundary; P-041 Tier 0; P-060 learned tiers |
| [social-management](../modules/social-management/README.md) — profiles, accounts and approved publishing | C, S | P-062 social management; P-065 account routes |
| [marketing-crosswalk](../modules/marketing-crosswalk/README.md) — evidence-gated content generation | C | P-010 generator; P-008 claim gating; P-064 AI Learning Series |
| [audio-production](../modules/audio-production/README.md) — routing, speech and mix-minus | S | P-038 routing; P-056 speech; P-068 local TTS (slices 1–4 built, proposal still pending) |
| [broadcast-graphics](../modules/broadcast-graphics/README.md) — NodeCG and OBS graphics | S | P-034 Redis bridge; P-056 director bindings |
| [ai-agents](../modules/ai-agents/README.md) — local host, moderation and memory | S | P-039 moderation; P-056 host; P-067 proposed profile/walkthrough system |

## End-to-end evidence

| Journey | Module boundary | Evidence to follow |
|---|---|---|
| Open an app and enable a capability | Desktop shell → shared setup → selected module | P-003/P-063 and the [desktop launch guide](../modules/infrastructure/setup/desktop-setup.md) |
| Produce a stream | Capture → optional effects/host/audio/graphics → approved live destination | [UC-1](../tests/USE-CASES.md), module acceptance sections and P-056/P-062 |
| Turn a recording into content | OBS recording → shared inbox → content editing → approved publication | P-065, [UC-2](../tests/USE-CASES.md), P-056 Shorts and P-062 |
| Generate a marketing draft | Registry → source/status validation → asset template → human review | [Generator](../modules/marketing-crosswalk/README.md) and [document workflow](DOCUMENTATION_WORKFLOW.md#marketing-drafts-and-coverage) |

Realtime capture, inference and rendering remain on the workstation. Shared storage or API
contracts carry cross-module data; optional cloud services do not become a core-path requirement.

## Keeping the map current

Refresh the affected row when a module, product surface or proposal relationship changes.
Re-read the source instead of copying historical pass counts or proposal states into this map.
Use the [document workflow](DOCUMENTATION_WORKFLOW.md) for verification and evidence recording.

<!-- BEGIN GENERATED MODULE PROPOSAL REFERENCES -->

## Generated module-owned proposal references

Explicit references in module README/setup documents; these are discovery links,
not inferred implementation ownership or evidence of completion.

| Module | Explicit proposal references |
|---|---|
| [creator-experience](../modules/creator-experience/README.md) | — |
| [soundboard](../modules/soundboard/README.md) | [P-044](PROPOSALS.md), [P-056](PROPOSALS.md), [P-066](PROPOSALS.md) |
| [realtime-ai](../modules/realtime-ai/README.md) | [P-043](PROPOSALS.md) |
| [automation-control](../modules/automation-control/README.md) | [P-056](PROPOSALS.md), [P-058](PROPOSALS.md), [P-066](PROPOSALS.md) |
| [storage-data](../modules/storage-data/README.md) | — |
| [sports-analytics](../modules/sports-analytics/README.md) | — |
| [content-creation](../modules/content-creation/README.md) | [P-036](PROPOSALS.md), [P-056](PROPOSALS.md), [P-061](PROPOSALS.md) |
| [image-editing](../modules/image-editing/README.md) | [P-028](PROPOSALS.md) |
| [nature-generation](../modules/nature-generation/README.md) | [P-017](PROPOSALS.md), [P-041](PROPOSALS.md), [P-059](PROPOSALS.md) |
| [cityscape-generation](../modules/cityscape-generation/README.md) | [P-017](PROPOSALS.md), [P-041](PROPOSALS.md), [P-060](PROPOSALS.md) |
| [marketing-crosswalk](../modules/marketing-crosswalk/README.md) | [P-067](PROPOSALS.md), [P-070](PROPOSALS.md) |
| [social-management](../modules/social-management/README.md) | [P-062](PROPOSALS.md), [P-065](PROPOSALS.md) |
| [backend-api](../modules/backend-api/README.md) | — |
| [broadcast-graphics](../modules/broadcast-graphics/README.md) | — |
| [observability](../modules/observability/README.md) | — |
| [infrastructure](../modules/infrastructure/README.md) | — |
| [audio-production](../modules/audio-production/README.md) | [P-056](PROPOSALS.md) |
| [character-avatar](../modules/character-avatar/README.md) | [P-042](PROPOSALS.md), [P-056](PROPOSALS.md) |
| [ai-agents](../modules/ai-agents/README.md) | [P-056](PROPOSALS.md) |
| [asset-pipeline](../modules/asset-pipeline/README.md) | [P-017](PROPOSALS.md) |
| [model-registry](../modules/model-registry/README.md) | [P-018](PROPOSALS.md) |

<!-- END GENERATED MODULE PROPOSAL REFERENCES -->
