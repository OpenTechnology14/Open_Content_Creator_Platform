# Open Content Creator Platform — Roadmap

> Canonical source for staging and prioritization. All module ordering in this repo derives from this document.

> **Direction:** [`future-state.md`](future-state.md) is the compass — north-star, pillars,
> horizons, and candidate modules. [`future.md`](future.md) is the deferred-work parking lot.
> This file is the canonical layer and module map.

## Implementation Philosophy

1. Start local-first wherever possible.
2. Prioritize stability before advanced AI pipelines.
3. Add infrastructure only when complexity justifies it.
4. Keep low-latency realtime systems local.
5. Use cloud services selectively for scalability, dashboards, backups, and burst compute.
6. Get Stream Extend and Creator Extend open before setting up optional tools or services.
   The packaged setup view must work without OBS, Docker/WSL, Python, models or cloud accounts;
   missing dependencies gate only the capabilities that consume them.

## Desktop onboarding priority

The first-run order is **install/open app → select capabilities → install/configure only their
dependencies → verify the chosen workflow**. The layers below describe feature dependencies;
they do not require the full stack to exist before either desktop app can launch.

The [desktop launch guide](../../modules/infrastructure/setup/desktop-setup.md) separates the
current private-bundle/source-build paths. P-003 supplies shared module selection, Python
dependency installation, guides and readiness. The next extension,
[P-063](../PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup), prioritizes Windows
installable artifacts and shared in-app setup recipes with progress, retry, skip and recovery.
Routine setup should run without AI supervision; user handoffs remain for OS/account choices
and physical acceptance. Container setup remains opt-in by selected feature. This changes
onboarding order without moving module boundaries or relaxing live capability acceptance.

---

## Full Hybrid Stack Architecture

### Creator Experience Layer
- OBS Studio
- Stream Graphics
- Overlays
- Sponsor Cards
- Multi-platform Streaming
- Broadcast Control

### Soundboard Layer
- Named, hotkeyed audio clips triggered live (OBS-native, `obs-soundboard`)
- Starter pack of CC0 stingers and UI sounds
- Named placeholder slots for clips a creator supplies themselves

### Realtime AI Layer
- ComfyUI
- DeepFaceLive
- Deep-Live-Cam
- LivePortrait
- OBS Background Removal
- Segmentation
- Local GPU Inference

### Sports / Analytics Layer
- OpenCV
- YOLO
- MediaPipe
- Golf Shot Tracing
- Pose Estimation
- Swing Analysis
- Replay Systems

### Character / Avatar Layer
- PNGTubers
- Flood-Tuber
- VTube Studio
- VRM Avatars
- AI Personas

### Automation / Control Layer
- Advanced Scene Switcher
- OBS Websocket
- n8n
- StreamDeck
- Python Automation

### Backend / API Layer
- FastAPI
- Websocket Services
- Internal APIs
- Overlay APIs

### Storage / Data Layer
- MinIO
- PostgreSQL
- Redis
- Asset Storage
- Backups

### Asset Pipeline Layer
- One shared MinIO/S3 client contract — bucket layout, upload/download, presigned URLs
- Replaces per-module hand-rolled clients (four before this layer existed)

*Shared infrastructure, layered on Storage / Data: consumed as a small library, not imported
across module boundaries (`CLAUDE.md` §10). Owns no runtime of its own.*

### Model Registry Layer
- Manifest per model/adapter — checksum, size, source, license, corpus provenance hash
- "Is this adapter distributable?" as a computed answer, not prose
- Stores manifests through the Asset Pipeline Layer, not a second MinIO client

*Shared infrastructure: tracks the weights other layers download and use. Owns no runtime of its
own; `registry.yml` ships empty until a real weight is checksummed and registered.*

### Observability Layer
- Prometheus
- Grafana
- Loki
- Telemetry
- Operational Dashboards

### Infrastructure Layer
- Docker
- Docker Compose
- Tailscale
- DigitalOcean
- Kubernetes (later-stage)
- GPU Burst Workers

### Content Creation Layer
- Blender
- DaVinci Resolve
- Motion Graphics
- YouTube Workflows
- Shorts/Reels Pipelines
- Film Rendering

### Image Editing Layer
- Krita + AI Diffusion Plugin
- ComfyUI Inpainting / Outpainting
- SAM Auto-Segmentation
- Video Frame Editing
- Mobile Tap-to-Edit (Creator Extend)

### Nature Generation Layer
- Style adapter training (LoRA) from owned landscape photographs
- Reference-conditioned restyle
- Sky replacement, outpaint, relight
- Full scene generation from a learned style
- Deterministic tone + colour grading (no AI)

### Cityscape Generation Layer
- Style adapter training from owned urban photographs, day and night separately
- Reference-conditioned restyle
- Facade repair, outpaint, relight, signage removal — **lineart-conditioned**
- Full scene generation from a learned style
- Deterministic tone, **perspective correction**, and mixed-source white balance

*Two layers, not one: the domains fail differently and the fix for one is wrong
for the other. Both span five orders of magnitude of cost, from a CPU tone curve
to hours of GPU training — the operation ladder in each module README governs.
Image intake is shared and lives at `docs/IMAGE_INTAKE.md`.*

### Social Management Layer
- Stream and content profiles with approved brand/logo choices
- Capability-aware social-platform account registry
- OAuth account verification with OS credential storage
- Human-approved publishing, upload, and live-destination handoff
- Shared contract for both desktop apps and a future mobile companion

*Cross-cutting: consumes show profiles and finished content, then owns the final external-account
action boundary. Provider registration and live acceptance remain per account.*

### Marketing Crosswalk Layer
- Registry of modules the Content Platform generates content for
- Cross-repository anchor + status-evidence drift detection
- Channel asset generation (the five-format content engine, comparison pages, lead-email angles)
- Claim gating against each subject's evidenced status
- Coverage + gap reporting against the target's own content ledger

*Cross-cutting: generates content for registered consumer modules rather than
sitting in the capture → process → publish pipeline. Owns no runtime and ships
in neither app.*

---

## Module Index

Setup guides live with the module they set up — a manual path and an automated path each.
Full index, labels, and setup order: [`modules/README.md`](../../modules/README.md).

| Module | Labels | Automated setup |
|---|---|---|
| [creator-experience](../../modules/creator-experience/) | `Content` `Stream` | none |
| [soundboard](../../modules/soundboard/) | `Content` `Stream` | none |
| [realtime-ai](../../modules/realtime-ai/) | `Content` `Stream` | none |
| [automation-control](../../modules/automation-control/) | `Content` `Stream` | full |
| [storage-data](../../modules/storage-data/) | `Content` `Stream` | full |
| [asset-pipeline](../../modules/asset-pipeline/) | `Content` `Stream` | none — plain library |
| [model-registry](../../modules/model-registry/) | `Content` `Stream` | CLI only |
| [sports-analytics](../../modules/sports-analytics/) | `Content` | deps only |
| [content-creation](../../modules/content-creation/) | `Content` | none |
| [image-editing](../../modules/image-editing/) | `Content` | none |
| [nature-generation](../../modules/nature-generation/) | `Content` | none |
| [cityscape-generation](../../modules/cityscape-generation/) | `Content` | none |
| [marketing-crosswalk](../../modules/marketing-crosswalk/) | `Content` | full (CLI) |
| [social-management](../../modules/social-management/) | `Content` `Stream` | partial — picker + adapters |
| [backend-api](../../modules/backend-api/) | `Stream` | full |
| [broadcast-graphics](../../modules/broadcast-graphics/) | `Stream` | full |
| [observability](../../modules/observability/) | `Stream` | full |
| [infrastructure](../../modules/infrastructure/) | `Stream` | full |
| [audio-production](../../modules/audio-production/) | `Stream` | config only |
| [character-avatar](../../modules/character-avatar/) | `Stream` | none |
| [ai-agents](../../modules/ai-agents/) | `Stream` | partial |

The retired numbered guides are archived at [`docs/guides/`](../guides/README.md), which maps
each old guide to the modules its setup steps moved into.

---

---

## Product surfaces

The platform currently develops two companion desktop shells plus free plugins. They consume one
shared module graph, setup contract, storage contract, relay protocol, and evidence model. Every
guide above works standalone; the apps add a dashboard, guided setup, remote control, and
capability readiness gates.

| Product | Module label | What it wraps |
|---------|--------------|--------------|
| **[Stream Extend](https://streamextend.com)** | `Stream` | OBS, AI effects, overlays, agents, audio, monitoring |
| **[Creator Extend](https://creatorextend.com)** | `Content` | ComfyUI, Blender, Krita, sports CV, image/video editing |
| **OBS Plugin** *(free)* | `Content` `Stream` | One-click scene import, encoder config, Browser Sources |
| **Blender Addon** *(free)* | `Content` | Template gallery, MinIO upload, ComfyUI triggers |

Modules labelled both are shared foundations — set up once for either product. The labels are
capability selections, not permanent application boundaries: no module may be duplicated merely
to keep the two desktop shells separate.

### Future convergence path

The architecture must preserve an option to ship a **unified desktop shell** that can enable the
`Stream` pack, the `Content` pack, or both. The existing Stream Extend and Creator Extend apps
remain the current delivery surfaces while their native workflows are still reaching acceptance;
this roadmap does not authorize merging their binaries or changing their names, pricing, or store
listings yet.

A future **single mobile companion** may control either desktop experience or a later unified
shell. Its first scope is setup/readiness status, approval-gated remote control, notifications,
stream monitoring, and content review/upload. Realtime OBS, camera effects, gameplay inference,
ComfyUI inference, and desktop DCC execution remain on the workstation.

**Owner direction, 2026-10-04:** plan one combined desktop app now to simplify distribution.
[P-072](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md) records the design, migration
risks and optional cloud feature scope. This is a planning-only exception to the earlier rule
that proposal work itself waited for the gates below; see [deviations](deviations.md).
It does not authorize replacing the current apps, changing commercial terms or implementing
the optional cloud phases.

**Owner-authorized private preview exception, 2026-10-12:** the owner explicitly chose
"Build the private preview first" when asked whether to build before the five checks finish.
P-072 may build an opt-in local setup/navigation/profile/library/readiness preview alongside
the existing apps. Migration, full parity, public release and legacy replacement retain their
gates. The preview does not certify the convergence conditions; see
[the exception](deviations.md#2026-10-12--private-combined-shell-preview-before-convergence).

Consolidation parity/migration and replacement remain gated by all of these:

1. Stream and Content desktop journeys each pass their own acceptance path.
2. Shared setup, settings, readiness, relay, API, and UI packages cover both apps without
   product-specific forks.
3. At least three real workflows cross the current product boundary, such as stream recording to
   Shorts, generated assets to broadcast graphics, or mobile review to approved publishing.
4. The relay and local approval model passes a real two-device test.
5. A packaging review shows that one shell reduces setup and switching cost without making the
   first-run experience harder for a user who needs only one capability pack.

See [`product-spec.md`](product-spec.md) for pricing, architecture, and build order.

---

## Key Architectural Principle

Keep low-latency systems — OBS, realtime AI inference, webcam processing — local whenever possible. Use cloud infrastructure selectively for scaling, dashboards, backups, remote access, orchestration, and burst rendering.
