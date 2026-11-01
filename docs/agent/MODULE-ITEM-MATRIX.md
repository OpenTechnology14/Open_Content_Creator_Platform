# Module item matrix

> **Status:** Living · **Last reviewed:** 2026-09-10 · **Owner:** OpenTechnology14

**Purpose:** given a module, find every service, port, bucket, script, and config file it owns
without re-deriving it from prose. Companion to
[`MODULE-MATRIX.md`](MODULE-MATRIX.md) (how expensive it is) and each module's own
`setup/manual.md` (how to stand it up).

**Enforcement: reference.** If you add a service, port, script, or config file to a module, add
the row here in the same change — an entry missing from this table is invisible to the next
session.

**Not here:** setup friction and gotchas. That is
[`../SETUP-TECHNIQUE-NOTES.md`](../SETUP-TECHNIQUE-NOTES.md). This table is what a module *is*.

Ports are as bound in the root `docker-compose.yml` — all on `127.0.0.1`, never `0.0.0.0`.

---

## Shared foundations — `Content` `Stream`

| Module | Compose services | Ports | Scripts / entry points | Config committed |
|---|---|---|---|---|
| `storage-data` | `postgres`, `redis`, `minio` | 5432, 6379, 9000, 9001 | `scripts/setup/postgres_migrate.sh`, `scripts/setup/minio_init.sh` | `postgres/migrations/0001_init.sql` |
| `creator-experience` | — (desktop) | — | `scripts/setup/windows.ps1` (Windows prerequisites), `scripts/setup/capture_devices.py` (device discovery), `scripts/setup/test_obs_websocket.py` (validation) | `scenes/default.json`, `obs-config/plugins.md`, `obs-config/multi-platform.md` |
| `soundboard` | — (OBS plugin, desktop) | — | — | `sounds/manifest.yaml` + 8 bundled CC0 clips under `sounds/stingers/`, `sounds/ui/`; P-066 local reviewed phrase export from [voice studio](../../modules/automation-control/voice_studio/README.md), manual OBS import |
| `realtime-ai` | — (local GPU) | ComfyUI 8188 (external) | `comfyui/scripts/output_to_minio.py`, `comfyui/bridges/webcam_bridge.py`, `comfyui/bursts/worker.py`, `ar-filters/face_mesh_filter.py`, `background-removal/repaint_region.py` | 3 workflow JSON, `ar-filters/filters/glasses.json`, `background-removal/config.json`, `comfyui/models.md` |
| `automation-control` | `n8n` (profile `automation`) | 5678 | `scripts/setup/n8n_import.sh`; `stream_director` CLI + input-handoff contract; `show_planner` draft calendar; `stream_autopilot` durable lifecycle, production worker supervisor and rehearsal (P-056, native) | `n8n/workflows/on-stream-start.json`; director, supervisor and runtime configs lock live start/gameplay/effects by default |
| `asset-pipeline` | — (plain Python package, no service) | — | `asset_pipeline/client.py` — `get_client`, `ensure_bucket`, `upload_file`, `upload_bytes`, `download_file`, `list_objects` | `requirements.txt` (minio, loguru) |
| `model-registry` | — (plain Python package, no service) | — | `model_registry/schema.py`, `checksum.py`, `registry.py`, `cli.py` (`validate`/`checksum`/`verify`/`status`) | `registry.yml` (empty — see its own header comment), `requirements.txt` (pyyaml, loguru) |
| `social-management` | — (shared Tauri tab + local CLI/UI) | 8765 loopback OAuth service | `social_management` CLI, OAuth callback, profile store, provider adapters; shared Tauri launcher/catalog bridge | `catalog.yaml`, 4 brand assets compiled into both apps; profiles/connections private, tokens and Discord webhook secrets in OS credential manager |

**Buckets** (`storage-data`, created by `minio_init.sh`): `comfyui-outputs`, `recordings`,
`models`, `project-assets`, `backups`, `nature-corpus`, `cityscape-corpus` — all seven are in the
script (verified 2026-09-01; this row previously claimed the last two were missing, which was
false by the time it was written).

## `Stream` modules

| Module | Compose services | Ports | Scripts / entry points | Config committed |
|---|---|---|---|---|
| `backend-api` | `fastapi` | 8000 | `app/main.py` + 6 routers (`health`, `streams`, `overlays`, `ws`, `events`, `automation`). Route-table regression coverage: `tests/backend_api/test_routes.py` | — |
| `observability` | `prometheus`, `source-health-exporter`, `loki`, `promtail`, `grafana` | 9090, 9101, 3100, 3000 | `source-health-exporter/exporter.py` | `prometheus.yml`, `alertmanager.yml`, 3 rule files, 3 Grafana dashboards, 2 provisioning files, `loki-config.yml`, `promtail-config.yml`, `source-health-exporter/config.yml` |
| `broadcast-graphics` | `nodecg` (profile `graphics`) | **9091** (NodeCG's own default 9090 collides with Prometheus) | `hcp-starter/extension/index.js`, `redis-bridge.js` | 2 bundle `package.json`, 6 dashboard/graphics HTML |
| `infrastructure` | — (orchestrates all) | — | `scripts/deploy/deploy-do.sh`, `scripts/maintenance/backup.sh`, `scripts/maintenance/healthcheck.sh` | `docker-compose.digitalocean.yml`, `tailscale/funnel.md`  Selective Python setup: `scripts/setup/modules.py`, `module_readiness.py`; shared desktop plugin/UI in `apps/shared/setup-wizard` and `apps/shared/ui`; manual guides retained. |
| `audio-production` | Shared native `audio_setup_status` (presence only) | — | `tts/render_reply.py` (Mac/Windows file export; native Windows acceptance pending, P-056); `tts/audition.py` (blind voice-audition rig, P-068 slice 2); `tts/check_voice_sample.py` (clone-source recording checker, P-068 slice 3); `stream_speech` worker (`--validate`, `--input`, `--backend`, `--prerender`; P-068 adds the `provider: local` router in `providers.py`, the render cache in `cache.py` and pre-render timing in `prerender.py`, with no engine adapter yet) | `voicemeeter/potato-config.xml`, `routing/blackhole-loopback.json`, `routing/pipewire.conf`; `configs/local/stream-speech.yaml` (voices, plus optional `provider: local` voices and `render_cache_directory`) |
| `ai-agents` | `ollama` (**commented out** in compose) | 11434 (external) | `local-llm/agent.py`, `memory.py`, `moderator.py`; `stream_host` CLI (P-056) | `local-llm/migrations/0002_memory.sql` — **is** applied by `make migrate`; `configs/local/stream-autopilot.yaml` defines the new host's ephemeral sessions/personas |
| `character-avatar` | — (desktop) | — | `vtube/vts_client.py`, `vtube/avatar_control.py` (Redis `agent.reply` -> VTS hotkey bridge, `P-042`) | `pngtuber/example/scene.json`, `vtube/avatar_mapping.yaml` |

## `Content` modules

| Module | Compose services | Ports | Scripts / entry points | Config committed |
|---|---|---|---|---|
| `image-editing` | — (drives ComfyUI) | — | `krita/scripts/apply_style.py`, `batch_upscale.py`, `export_to_minio.py` | `workflows/*.json` — 8 files, all on disk (2026-09-01, P-028); 5 of the 6 previously-unverified ones are now GPU-run verified working (2026-09-02, P-043), 1 blocked on an upstream `transformers` incompatibility — see `workflows/README.md` Status |
| `sports-analytics` | — (local GPU) | NDI (discovery) | `golf-tracer/tracer.py`, `ndi_output.py`, `replay.py`, `pose-estimation/yolo_pose.py`, `mediapipe_swing.py`, `posture_screen.py` | `golf-tracer/calibration.json`, `requirements.txt` |
| `nature-generation` | — (drives ComfyUI) | — | **none — no code** | **none.** Bucket `nature-corpus` exists (`minio_init.sh`); 5 workflows are specified, not built |
| `cityscape-generation` | — (drives ComfyUI) | — | **none — no code** | **none.** Bucket `cityscape-corpus` exists (`minio_init.sh`); 6 workflows are specified, not built |
| `content-creation` | — (desktop) | — | `stream_shorts` local selection/review/MP4 CLI with supplied captions, brand layout, event punch-ins and audio leveling (P-056); shared `apps/shared/recording-library` inbox plus Creator Extend Recordings view (P-065). The real Blender addon lives at repo-root `plugins/blender-addon/` instead — `__init__.py`, `operators/__init__.py`, `panels.py`, `preferences.py` (440 lines; 4 of 5 operators working, `CE_OT_BatchRender` a documented stub) | `configs/local/stream-shorts-demo.json`; `plugins/blender-addon/` has no config files, just Python. Creator app workflow input editor and bundled template resources (P-057). |
| `marketing-crosswalk` | — (CLI) | — | `generator/cli.py` (+ `crosswalk`, `render`, `coverage`, `status`) | 4 registry YAML + 4 subject files, 11 templates |

---

## Cross-module contracts

Shared artifacts with more than one owner. Changing one of these breaks something that is not in
the same directory.

| Artifact | Owner | Consumers |
|---|---|---|
| Shared local recording inbox | `content-creation` contract in `apps/shared/recording-library` | Stream Extend registers OBS-finalized paths; Creator Extend imports, routes, reveals, and updates workflow state |
| `image-editing/workflows/inpaint-fill-v1.json` | `image-editing` | `realtime-ai/background-removal/repaint_region.py`; both generation modules' Tier 2 are pending decisions on whether to become a third and fourth |
| Redis pub/sub | `storage-data` | `backend-api` fanout, `broadcast-graphics` bridge, `ai-agents` event bus, `realtime-ai` burst queue |
| MinIO `models/` | `storage-data` | Tracked by `model-registry` (2026-09-01, P-018) — schema, checksum tool, and distributability check exist; `registry.yml` itself is still empty, no real entries populated yet |
| `realtime-ai/comfyui/models.md` | `realtime-ai` | `image-editing`, both generation modules |
| `docs/IMAGE_INTAKE.md` | shared | `nature-generation`, `cityscape-generation` |
| ComfyUI at `127.0.0.1:8188` | external | `realtime-ai`, `image-editing`, both generation modules — over HTTP, never imported (`CLAUDE.md` §10) |
| `tests/acceptance/` (`docker_stack` fixture + `test_creator_journey`) | `P-016` | Exercises `storage-data`, `backend-api`, `observability` together — the only test in the repo that proves any two modules interoperate. Marked `live`, excluded from `make test`; run with `make test-acceptance` |

## Known inventory gaps

Recorded so they are visibly known rather than silently missing:

- **6 ComfyUI workflows that were indexed-but-absent are now on disk (2026-09-01, P-028).** 5 of
  the 6 are now GPU-run verified working end to end on real hardware (2026-09-02, P-043, 3 real
  bugs found and fixed in the process); 1 (`auto-select-sam-v1.json`) is confirmed blocked on an
  upstream `transformers` incompatibility in its node pack, not a naming or config issue. 2 of the
  8 total live in a different module (`image-editing`) than `realtime-ai`'s own index describes.
  Verified tables in each `workflows/README.md`; structural checks in
  `tests/realtime_ai/test_workflows.py`.
- **`streaming.rules.yml` and `ai.rules.yml` do not exist** in `observability/prometheus/rules/`.
- **5 Grafana dashboards are referenced but not built** — `ai-pipelines`, `sports-cv`, `slo`,
  `cost`, `gpu`.
- ~~Two buckets are specified but not in `minio_init.sh` — `nature-corpus`, `cityscape-corpus`.~~
  **False as of 2026-09-01** — both were already in the script's `BUCKETS` array; this line was
  stale, not a real gap. Found and corrected while scoping `P-017` (`docs/PROPOSALS.md`).
- **`creator-experience/scenes/default.json` is a placeholder**, not an OBS export — it says so in
  its own `_comment`, and all 8 scenes carry `sources: []`. `obs-config/profile.ini` is listed as a
  deliverable and does not exist. Six modules assume OBS is configured. Tracked as `P-027`.

P-056's `stream_autopilot preflight` is a read-only local production diagnostic. It runs
fixed component validators and reports prerequisites; it does not own or stop effects.

P-056 production build (2026-10-12): Stream Extend bundles a persistent `stream_autopilot`
JSONL owner and its fixed workers/manifests, with private operator configs, cancellation,
recording-first OBS ownership and shared recording-inbox handoff. The automation module adds
`gameplay.py` and the pinned Node Minecraft private-world adapter; the avatar module adds
eight configured VTube expression/animation cues. Broadcast/gameplay/body cues default off.
Real account/game/rig, physical Windows, timing/soak and expanded sessions remain unverified.

## Private preview and relay safety follow-up (2026-10-12)

- P-001: `cloud/migrations/002_runtime_role.sql` and `003_runtime_password.sh` configure the
  separate relay runtime role; `RELAY_DATABASE_URL`/`RELAY_DATABASE_PASSWORD` are documented in
  `.env.example`. Existing-volume/Docker/production acceptance stays open; see `cloud/README.md`.
- P-072: `apps/extend/`, `configs/ui/combined-navigation.json`, `extend-preview-defaults.json` and
  `configs/setup/extend-preview.json` reuse existing module setup/profile/recording/readiness
  contracts. Private preview only; no new module/service or public replacement.
