# Guides

**The numbered guide series is retired, and fully migrated.** Nothing is archived — every section
now lives with the module it belongs to:

| Kind of content | Where it lives |
|---|---|
| Manual setup steps | `modules/<name>/setup/manual.md` |
| Automated setup, and what is *not* automated | `modules/<name>/setup/automated.md` |
| How a config file works, and why it is shaped that way | the README next to that config file |

Start at **[`modules/README.md`](../../modules/README.md)** — the module index, with each module
labelled `Content`, `Stream`, or both, and the setup order for each product.

## Where each old guide went

| Old guide | Setup steps | Config + reference material |
|---|---|---|
| **1** OBS Foundation | [creator-experience](../../modules/creator-experience/setup/manual.md) · [automation-control](../../modules/automation-control/setup/manual.md) (WebSocket) | [scenes](../../modules/creator-experience/scenes/README.md) (scene structure, what to commit) · [obs-config/plugins.md](../../modules/creator-experience/obs-config/plugins.md) · [obs-config/multi-platform.md](../../modules/creator-experience/obs-config/multi-platform.md) |
| **2** Face Filters + Background | [realtime-ai](../../modules/realtime-ai/setup/manual.md) · [character-avatar](../../modules/character-avatar/setup/manual.md) | [realtime-ai](../../modules/realtime-ai/README.md) (swap vs AR lens, tool selection, pipeline, virtual camera) · [background-removal](../../modules/realtime-ai/background-removal/README.md) (recipes) · [pngtuber](../../modules/character-avatar/pngtuber/README.md) |
| **3** Golf Tracer + Sports CV | [sports-analytics](../../modules/sports-analytics/setup/manual.md) | [golf-tracer](../../modules/sports-analytics/golf-tracer/README.md) (trajectory math, calibration, frame-skip) · [models](../../modules/sports-analytics/models/README.md) (model choice, training) · [pose-estimation](../../modules/sports-analytics/pose-estimation/README.md) |
| **4** ComfyUI Content Creation | [realtime-ai](../../modules/realtime-ai/setup/manual.md) · [content-creation](../../modules/content-creation/setup/manual.md) · [storage-data](../../modules/storage-data/setup/manual.md) | [comfyui/workflows](../../modules/realtime-ai/comfyui/workflows/README.md) (versioning, ReActor caveat, index accuracy) · [comfyui/models.md](../../modules/realtime-ai/comfyui/models.md) |
| **4B** Image + Video Editing | [image-editing](../../modules/image-editing/setup/manual.md) | [krita](../../modules/image-editing/krita/README.md) (core operations) · [workflows](../../modules/image-editing/workflows/README.md) (inpainting index, video editing) · [mobile](../../modules/image-editing/mobile/README.md) |
| **5** ComfyUI + OBS Realtime | [realtime-ai](../../modules/realtime-ai/setup/manual.md) | [realtime-ai](../../modules/realtime-ai/README.md) (architecture, latency budget, out-of-scope) · [comfyui/workflows](../../modules/realtime-ai/comfyui/workflows/README.md) (framerate table) · [comfyui/bursts](../../modules/realtime-ai/comfyui/bursts/README.md) |
| **6** Audio Production | [audio-production](../../modules/audio-production/setup/manual.md) | [routing](../../modules/audio-production/routing/README.md) (TTS routing, podcast tracks, VST chains) · [voicemeeter](../../modules/audio-production/voicemeeter/README.md) |
| **7** Broadcast Graphics + NodeCG | [broadcast-graphics](../../modules/broadcast-graphics/setup/manual.md) · [backend-api](../../modules/backend-api/setup/manual.md) · [storage-data](../../modules/storage-data/setup/manual.md) | [nodecg](../../modules/broadcast-graphics/nodecg/README.md) (why NodeCG, ports) · [hcp-starter](../../modules/broadcast-graphics/nodecg/bundles/hcp-starter/README.md) (replicants, recipes, animations) · [hcp-alerts](../../modules/broadcast-graphics/nodecg/bundles/hcp-alerts/README.md) |
| **8** AI Agents + Avatars | [ai-agents](../../modules/ai-agents/setup/manual.md) · [storage-data](../../modules/storage-data/setup/manual.md) (pgvector) · [character-avatar](../../modules/character-avatar/setup/manual.md) | [local-llm](../../modules/ai-agents/local-llm/README.md) (architecture, tool selection, moderation, latency budget) · [character-avatar](../../modules/character-avatar/README.md) (agent-driven avatars) |
| **9** Advanced Infra + Ops | [observability](../../modules/observability/setup/manual.md) · [infrastructure](../../modules/infrastructure/setup/manual.md) · [automation-control](../../modules/automation-control/setup/manual.md) | [prometheus](../../modules/observability/prometheus/README.md) (alert rules, routing) · [grafana](../../modules/observability/grafana/README.md) (dashboards, provisioning) · [infrastructure automated](../../modules/infrastructure/setup/automated.md) (CI/CD, Kubernetes deferral test, backups) |

## The "use the app" sections

Each guide ended with a pitch for Stream Extend / Creator Extend doing that guide in one click.
Those now live in the relevant `setup/automated.md`, rewritten as **specified, not shipped** —
`CLAUDE.md` §11 has 17 of 21 modules at `scaffolded` (4 are `implemented`: `storage-data`,
`marketing-crosswalk`, `asset-pipeline`, `model-registry`), and `docs/AUDIT.md` records both
desktop apps as lacking a complete build scaffold. Each notes what *does* work today instead.

## Modules with no predecessor guide

`nature-generation`, `cityscape-generation`, `marketing-crosswalk`, `asset-pipeline`,
`model-registry`, `soundboard`, and `social-management` were all added after the guide series was retired. They have no
row above because no numbered guide ever covered them — their setup docs are the originals, not a
migration.

## Cross-module guides

One guide is not a module's setup doc, because it is shared by two modules:

| Guide | Covers | Used by |
|---|---|---|
| [`docs/IMAGE_INTAKE.md`](../IMAGE_INTAKE.md) | Feeding your own photographs in — buckets, provenance, rights and format matrices, curation tips | `nature-generation`, `cityscape-generation` |

It lives outside `modules/` precisely because duplicating it into both would guarantee the two
copies drift.
