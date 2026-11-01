# Platform acceptance checklist

> **Status:** Living — the single list of what must be true for the platform to be done · **Last reviewed:** 2026-09-10 · **Owner:** OpenTechnology14

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is the platform acceptance checklist, not a priority queue and not an authorization. A failing line is a finding to route, not a task to start here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](../docs/PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](../docs/todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](../docs/FUTURE_DOCS.md).

**Enforcement: release gate, not a per-module gate.** A module is finished when its own section
here passes. **Failing lines in another module's section never block starting the next module** —
they block calling the platform done. `docs/agent/VERIFICATION-MATRIX.md` decides *how* each line
is proven; this file is *what* must be true.

**"Done" for the platform = every line below is true.** Nothing else defines it.

## How a line is annotated

| Marker | Meaning |
|---|---|
| **auto** | Proven by `make test`. Runs offline, every time, no human |
| **manual** | Needs a human. The steps are in that module's `setup/manual.md` § Verification |
| **live** | Needs a running service. Proven by `make up` + the named command |
| **blocked** | Cannot be proven yet. Names what is missing and who owns it |

An unannotated line has never been assessed — that is itself a finding.

**Every line names its owning module.** A line with no owner is a module nobody has scoped; if a
future pass finds one, that is a new module found the same way Ironfall found its Modules 10 and 11.

---

## Foundations — `storage-data`

- Postgres, Redis, and MinIO all reach `Up`. — **live** (`make ps`)
- Migrations apply in filename order across every module directory. — **auto**
- `0001_init.sql` creates the `pgcrypto` and `vector` extensions and four tables. — **live** (`make migrate`, then inspect)
- `0002_memory.sql` applies after `0001` and creates `agent_memories`. — **auto** (ordering) + **live** (application)
- All seven buckets exist after `minio_init.sh`. — **auto** (declaration) + **live** (creation)
- Every shell script parses and runs under macOS bash 3.2. — **auto**

## API — `backend-api`

- `/health` returns 200. — **live** (`make healthcheck`)
- `/metrics` is scraped by Prometheus's `fastapi` job. — **live**
- A message published to Redis reaches a `/ws` subscriber. — **blocked** (no harness; `P-016`)
- Mutating routes reject a missing or wrong `X-API-Key`. — **auto** (`tests/backend_api/test_routes.py::test_require_api_key_accepts_and_rejects`, `P-026`, 2026-09-01)
- `/ws` rejects a connection with no valid key. — **auto** (`test_ws_rejects_missing_api_key`, `test_ws_rejects_wrong_api_key`; `P-026`)

## Monitoring — `observability`

- Prometheus shows every scrape target Up. — **live**
- Grafana renders `platform-overview` with live data. — **live**
- A deliberate error appears in Loki within seconds. — **manual**
- `source-health-exporter` reports on `:9101/metrics`. — **live**
- Alerts route somewhere a human sees. — **blocked** (destinations unfilled; `P-025`)

## Capture — `creator-experience`

- OBS streams at target bitrate with no dropped frames. — **manual**
- A test recording produces a playable MKV that remuxes to MP4. — **manual**
- **auto** + **manual**/pending — A Stream Extend-managed live session starts recording before streaming, stops the stream before
  finalizing its owned recording, and registers the file once in Creator Extend without stopping a
  pre-existing OBS recording. (fake OBS ownership/order contracts and
  shared inbox tests pass; real OBS picture/audio and app-to-app run pending)
- The mic filter chain is audibly clean. — **manual**
- The committed scene collection imports into a clean OBS. — **blocked** (`default.json` is a placeholder with 8 empty scenes; `P-027`)
- `make test-obs` connects and reports state. — **live**

## Sound bar — `soundboard`

- P-056 maps only registered manifest slots and exact configured OBS hotkeys, with clip cooldown and off-air isolation. — **auto** (`tests/automation_control/test_stream_director.py`)
- A configured P-056 reaction plays the intended dock clip on the intended OBS track and stops on pause. — **manual** (OBS unavailable during initial director verification)
- Every bundled sound in `sounds/manifest.yaml` has a real file, a license, and a source. — **auto** (`tests/soundboard/test_manifest.py`, `P-044`)
- No placeholder slot ships a file (the copyright line this module draws). — **auto** (`tests/soundboard/test_manifest.py`, `P-044`)
- The Soundboard dock appears in OBS after installing `obs-soundboard`. — **manual**
- A bundled sound plays with no perceptible lag on its hotkey. — **manual**

## Realtime AI — `realtime-ai`

- ComfyUI serves on `127.0.0.1:8188`. — **manual**
- The LCM stylization workflow runs end to end. — **manual**
- The virtual camera appears as an OBS source. — **manual**
- Webcam → AI → OBS stays under 200 ms. — **manual**
- `output_to_minio.py` uploads to `comfyui-outputs`. — **live**
- Every workflow named in the index exists on disk. — **auto**

## Automation — `automation-control`

- P-056 director previews without side effects, scopes events, invokes configured module APIs and distinguishes queued workflows from completed work. — **auto** (`tests/automation_control/test_stream_director.py`)
- P-056 pause/resume affects only the configured OBS scene/audio bindings; live lower third clears correctly. — **manual**
- OBS WebSocket is enabled with a password and `make test-obs` passes. — **manual**
- n8n starts and the imported workflow is listed. — **live** (`make up-with-automation`)
- A stream-start event fires the workflow end to end. — **manual**

## Graphics — `broadcast-graphics`

- NodeCG serves on 9091 without colliding with Prometheus. — **live**
- The `nodecg` service sets every env var `redis-bridge.js` reads. — **auto** (`tests/broadcast_graphics/test_nodecg_bundles.py`, `P-034`)
- Every documented Redis channel name resolves to a real replicant key. — **auto**
- Every bundle's declared dashboard/graphics files exist on disk, except the disclosed `hcp-alerts` skeleton. — **auto** (1 expected `xfail`)
- A dashboard change updates the graphic live via its replicant. — **manual**
- The graphic renders in OBS as a Browser Source with transparency. — **manual**

## Audio — `audio-production`

- P-056 speech export rejects other sessions and treats reply text as stdin, never shell commands. — **auto** (`tests/audio_production/test_host_speech.py`)
- A selected P-056 voice plays through the intended OBS bus with working mute and timing. — **manual** (continuous playback/routing is not implemented yet)
- A call partner cannot hear themselves. — **manual** (mix-minus; the failure this module exists for)
- Stream captures mic, desktop, and AI voice at correct relative levels. — **manual**
- Recording peaks below −1 dB. — **manual**
- `pipewire.conf` creates a loopback module for every bus in the canonical table. — **auto** (`tests/audio_production/test_routing_configs.py`, `P-038`)
- Every loopback module has both a capture and playback side. — **auto**

## Agents — `ai-agents`

- P-056 conversations isolate sessions, bound queues/history, enforce phrase cooldowns and discard canceled/stale replies. — **auto** (`tests/ai_agents/test_stream_host.py`)
- A real platform message reaches the P-056 host through the backend and is answered by local Ollama. — **manual** (live platform ingress and end-to-end acceptance remain open)
- Ollama responds locally. — **manual**
- A message written now is retrieved as memory in a later session. — **manual**
- `agent.py` checks a flagged incoming message before generating, and a flagged reply before publishing. — **auto** (`tests/ai_agents/test_moderation_gate.py`, `P-039`)
- The moderator actually blocks a bad input **and** a bad output live, end to end. — **manual**
- Agent output visibly drives the avatar. — **manual**

## Avatars — `character-avatar`

- The avatar renders in OBS with a transparent background. — **manual**
- Mouth state responds to voice with no perceptible lag. — **manual**
- `avatar_control.py` triggers the talk hotkey, holds, then idle — never reversed, never skipped. — **auto** (`tests/character_avatar/test_avatar_control.py`, `P-042`)
- A published `agent.reply` actually flips VTube Studio's hotkey live, end to end. — **manual**

## Sports CV — `sports-analytics`

- The tracer draws a plausible arc on recorded footage. — **manual**
- Pose landmarks track through a full swing without dropping. — **manual**
- OBS shows the NDI source at the expected frame rate. — **manual**
- `posture.rs`'s CLI flags and `--view` values match what `posture_screen.py` actually accepts. — **auto** (`tests/sports_analytics/test_pipeline_contracts.py`, `P-040`)
- `calibration.json`'s pixel-to-metre mapping is actually applied to a rendered trajectory. — **blocked** (template only — not read by any code yet; see `golf-tracer/README.md`)

## Image editing — `image-editing`

- Krita's AI Diffusion panel shows a green ComfyUI connection. — **manual**
- A masked region inpaints with no visible seam at 100%. — **manual**
- `export_to_minio.py` lands a file in the bucket. — **live**
- `apply_style.py`/`batch_upscale.py`'s generated ComfyUI workflows have no dangling node references. — **auto** (`tests/image_editing/test_krita_scripts.py`, `P-037`)
- `krita/README.md`'s Workspace Presets section matches what's actually in `presets/`. — **auto**
- A style preset actually produces a distinguishable look from another (needs a real reference image per preset — none exist yet). — **blocked** (`P-037` — noted, not built; see `apply_style.py`'s docstring)
- 5 of the module's 8 committed ComfyUI workflow JSONs (`inpaint-fill`, `inpaint-remove`, `outpaint-expand`, `upscale-4x`, `background-replace`) actually load into a real ComfyUI and produce output, not just parse structurally. — **manual** (done once, 2026-09-02, Apple M1 Pro/Metal, `P-043`; not CI-provable — no GPU in CI — see `workflows/README.md` Status)
- `auto-select-sam-v1.json` executes against a real ComfyUI. — **blocked** (confirmed 2026-09-02, `P-043` — the underlying node pack's vendored GroundingDINO/BERT code is broken against current `transformers`, not a naming or config issue; see `workflows/README.md` Status)
- `video-range-edit-v1.json` executes against a real ComfyUI. — **blocked** (confirmed 2026-09-02, `P-043` — the documented flow-warp node doesn't exist anywhere, and the flow-computation node only outputs a rendered visualization, not a usable flow field; needs real design work, not a rename; see `workflows/README.md` Status)

## Generation — `nature-generation`, `cityscape-generation`

- Tier 0 (both modules) applied twice with one preset gives byte-identical output. — **auto** (`tests/nature_generation/test_tone.py::test_tier0_operations_are_deterministic`, `tests/cityscape_generation/test_geometry.py::test_geometry_operations_are_deterministic`, `P-041`)
- Cityscape Tier 0 geometry runs in the documented order: distortion → perspective → rotation → crop → tone. — **auto** (`tests/cityscape_generation/test_presets.py`)
- Cityscape's homography solver reproduces its own 4 point correspondences exactly. — **auto** (`tests/cityscape_generation/test_geometry.py`)
- Automatic keystone detection and mixed-source white balance fail loudly (`NotImplementedError`), not silently. — **auto**
- An adapter at 0.7 changes palette without inventing structure. — **blocked** (Tier 4 training is queued but not authorized; `P-059`/`P-060`)
- Nature: foliage at 100% still looks organic, not CGI-smooth. — **manual**
- Cityscape: corrected verticals are actually vertical against the frame edge, on a real photo. — **manual**
- Cityscape: a generated skyline holds straight building edges at 100%. — **blocked** (Tier 3 generation is queued but not authorized; `P-060`)
- Outputs land in `project-assets`. — **live**

## Content pipeline — `content-creation`

- **auto** + **manual**/pending — Creator Extend lists Stream Extend-managed recordings in one local inbox, keeps source/target
  profile routing and workflow status across restarts, deduplicates paths, reports moved files, and
  supports manual import/reveal/archive without copying media. (shared
  Rust and desktop structural contracts; native real-file/restart/reveal acceptance pending)
- Blender renders to a folder that reaches `project-assets`. — **manual**
- Resolve opens and edits it. — **manual**
- The Blender addon's registration list matches what's actually defined, and every `bl_idname` is unique. — **auto** (`tests/blender_addon/test_addon_structure.py`, `P-036`)
- The addon's Upload-to-MinIO / Send-to-ComfyUI operators actually work end to end inside Blender. — **manual** — needs a real Blender install
- Batch Render iterates scenes and uploads each. — **blocked** (`P-061` is queued but not authorized; `CE_OT_BatchRender` remains a documented stub)

## Infrastructure — `infrastructure`

- `make up` brings the default profile up cleanly. — **live**
- Both compose files validate, base and DO overlay. — **live** (`docker compose config -q`)
- Every `${VAR}` either compose file references has a matching `.env.example` entry. — **auto** (`tests/infrastructure/test_compose_env.py`, `P-035`)
- `deploy-do.sh` resolves `DROPLET` from `DO_DROPLET_IP`/`DO_SSH_USER` when not passed explicitly. — **auto**
- `tailscale status` lists both nodes and the droplet service is **not** publicly reachable. — **manual**
- `make backup` produces a restorable artifact — proven by restoring it. — **manual**

## Content generation — `marketing-crosswalk`

- `validate` confirms every anchor and status claim in both repositories. — **live**
- `selftest` renders every template with no unfilled placeholders and no private links. — **auto**
- A draft is refused when it would link a private repo. — **auto**
- An asset is refused when its subject's status is below `shipped`. — **auto**

## Social management — `social-management`

- Every profile/provider/brand reference validates and all four preloaded logo files resolve. — **auto** (`tests/social_management/test_social_management.py`)
- OAuth uses scoped state, expires after ten minutes, applies PKCE where supported, and keeps tokens out of public connection state. — **auto** (`tests/social_management/test_social_management.py`)
- An external provider request requires an approved job plus its exact confirmation ID. — **auto** (`tests/social_management/test_social_management.py`)
- **auto** + **manual**/pending — Both apps persist separate active Stream/Content workspaces and restore each profile's last
  brand/provider/capability/redacted account route when switching away and back.
  (shared Rust state/validation tests and Svelte checks; native restart with two real accounts pending)
- **auto** + **manual**/pending — Native disconnect removes both the public connection row and private credential while leaving
  other accounts intact. (Python vault/store regression; real macOS and
  Windows credential-manager deletion pending)
- The standalone picker and both Tauri Social tabs show the intended profile, logo, provider readiness, and connection purpose on the MacBook display. — **manual** (macOS passed: Stream Extend showed OpenTechMarketing/OpenTechApp, Discord available and Kick disabled/planned; Creator Extend defaulted to Main Content/Creator Extend on 2026-09-10)
- A real YouTube, Twitch, X, and Discord account/channel connection returns the intended identity on macOS and Windows. — **manual**
- Private YouTube upload/live, Twitch live, X test-post, and Discord announcement round trips reach the selected accounts without persisting a token, webhook secret, or stream key. — **manual**

## Storage contract — `asset-pipeline`

- `output_to_minio.py`, `worker.py`, and `export_to_minio.py` import `asset_pipeline` instead of hand-rolling a client. — **auto** (`tests/asset_pipeline/test_consumers_migrated.py`, `P-017`)
- `get_client()` reads the four `MINIO_*` env vars and strips a URL scheme from the endpoint. — **auto** (`tests/asset_pipeline/test_client.py`)
- `ensure_bucket`/`upload_file`/`upload_bytes`/`download_file`/`list_objects` call the right SDK method and wrap `S3Error` into `AssetClientError`. — **auto**
- `worker.py` actually creates its bucket if missing before the first upload — the bug this module fixed. — **live** (needs a fresh MinIO instance with the bucket absent; not run against one here)

## Model provenance — `model-registry`

- Every entry in `registry.yml` has all required fields, a well-formed `sha256`, and (for adapters) a well-formed `corpus_manifest_sha256`. — **auto** (`tests/model_registry/test_schema.py`, `P-018`)
- `is_distributable()` returns `False` for an adapter missing `corpus_manifest_sha256` — the exact gap this module was built to close. — **auto**
- `compute_sha256()` matches `hashlib.sha256` and `shasum -a 256` on the same file. — **auto** (`tests/model_registry/test_checksum.py`) + **manual** (cross-checked against `shasum` by hand during development, not re-run automatically)
- `sync_to_minio`/`sync_from_minio` call `asset_pipeline`'s real functions with the right arguments. — **auto** (mocked client, `tests/model_registry/test_registry.py`)
- `registry.yml` has a real entry, checksummed against an actually-downloaded weight. — **blocked** (empty by design; populating it is owner work — see `setup/automated.md`)

## Cross-cutting

- A clean clone installs and builds on every claimed supported OS. — **manual** (macOS proven live 2026-09-02, `P-052`: both desktop apps built and launched from a clean `npm install`/`cargo build`. Rest of `D-02`'s OS matrix — Windows/Linux — still **blocked**, undecided)
- One complete local-first creator journey passes automatically. — **blocked** (`P-016`'s Phases 1-3 shipped and **passed a real CI run** 2026-09-01 — run 33452956159 (private development evidence; not distributed), the first fully-green CI run on this repo's `ci.yml` since at least 2026-08-23 — proving 4 of [UC-1](USE-CASES.md)'s 15 steps against real Postgres/Redis/MinIO/FastAPI. The line stays `blocked` because UC-1 has 15 steps and 11 remain OBS/GPU/desktop-app work no harness can automate; it closes when UC-1 passes end to end, not when the harness alone goes green)
- CI fails on lint, test, and build failures. — **auto** (`ruff check modules/ scripts/` blocking since `P-001` WP-1, 2026-09-02; `pytest -q` already blocking since `P-024`; `P-052`/WP-3 added a `cargo check`/`npm run build`+`check` job for both desktop apps, `ubuntu-latest` only — `cargo check`, not a full release bundle, see `docs/GAP_AUDIT.md` `HCP-004`)
- No secret appears in the working tree or history. — **blocked** (`P-001`)

---

## Current state

| Marker | Lines |
|---|---|
| **auto** | 48 |
| **live** | 19 |
| **manual** | 50 |
| **blocked** | 14 |

Recounted 2026-09-20 while adding the P-065 recording handoff and profile workspaces —
mechanically, by `grep -oE '\*\*(auto|live|manual|blocked)\*\*'` over the per-module sections only,
excluding the legend and this table itself, not hand-adjusted. A line can carry two markers (e.g.
"auto (ordering) + live (application)"), so this counts marker occurrences, not bullet lines.

**The narrative view of these lines is [`USE-CASES.md`](USE-CASES.md)** — two flagship workflows
that sequence them into jobs a creator actually does. This file asks whether each capability is
true; that one asks whether they compose.

**50 manual lines is the real number to drive down.** Each one is a human doing something no
script can — and each module's `setup/manual.md` § Verification is where those steps live. When a
manual line becomes automatable, move it to **auto** and delete the manual step; that is the
measure of progress, not adding more docs.

**14 blocked lines** are the honest ceiling: the platform cannot be called done while they remain,
regardless of how many modules individually pass.

## Daily shows and Shorts — P-056

- `automation-control`: draft calendars cover fourteen games plus OpenTechMarketing and VideoReview, two weekly flagships, stable primary slots when adding a second daily slot, and reject overlaps/DST ambiguity. — **auto** (`test_show_planner.py`)
- `automation-control`: non-game profiles restrict source references, keep YouTube visibility private/unlisted, require review-video rights confirmation and emit non-uploading approval drafts. — **auto** (`test_show_planner.py`); real YouTube upload remains unbuilt.
- `ai-agents`: game variations inherit Nova's fixed identity and core phrases; legacy full-persona configuration still loads. — **auto** (`test_stream_host.py`)
- `automation-control`: gameplay handoff invalidates stale epochs and fails closed on timeout/release failure; late acknowledgements cannot restore control. — **auto** (`test_gameplay_handoff.py`)
- `automation-control`: session lifecycle requires preflight and preview, locks broadcast/gameplay by policy, bounds running sessions, persists idempotency keys, and recovers a crashed active session to operator-reviewed preview. — **auto + native Mac** (`test_stream_autopilot_supervisor.py`; Stream Extend bundled rehearsal on the MacBook display, 2026-09-08). Production driver acceptance remains **blocked**.
- `automation-control`: Take control releases actual held game inputs without restarting OBS or changing the host, and Let agent play synchronizes current game state first. — **blocked** (concrete input adapters and authenticated operator controls not built)
- `content-creation`: Shorts ignore cross-session/bot/duplicate events, cap individual participation, retain exact manual sections and respect exclusions. — **auto** (`test_stream_shorts.py`)
- `content-creation`: validated edit plans render supplied captions, brand text/colors, event-driven punch-ins and normalized audio while keeping the full game frame. — **auto + native Mac** (`test_stream_shorts.py`; real 8-second FFmpeg render and frame inspection, 2026-09-08). Transcription, subject tracking and real-stream phone review remain **manual/pending**.
- `content-creation`: review and render a real stream recording; verify selected boundaries, sound sync and HUD legibility at phone size. — **manual** (synthetic source render and browser range selection verified; real stream pending)
- `automation-control` / `content-creation`: every completed episode delivers a recording and synchronized interaction job, retries failures durably and records produced clips. — **blocked** (P-065 now delivers recordings for Stream Extend-managed sessions; synchronized chat jobs, automatic Shorts-job creation, retries and durable supervisor integration remain missing)

- P-056 native Windows rehearsal installs dependencies, exports real System.Speech audio and renders three verified Shorts. — **auto CI + manual/pending hardware**; PR #41 passed the Windows runner. Repeat `scripts/setup/stream_autopilot.py smoke` on the owner's Windows device and retain `report.json` before claiming that hardware.

- P-003 module choices resolve dependencies, isolate environments and keep package checks separate from full readiness. — **auto** (`tests/setup/` and shared setup-plugin Rust tests). Desktop installation, checks, guides and saved choices exercised on Mac (2026-09-08); native Windows acceptance remains **manual/pending**.
- P-003 capture setup enumerates local video/audio devices, saves only a device from the latest scan and shows Windows driver evidence without claiming a recording passed. — **auto + manual/pending** (parser/plugin contracts; run the bundled panel with a physical capture card on Mac and Windows, then record 1080p60 with game audio).
- P-003 desktop settings persist validated endpoints, keep OBS/MinIO secrets out of public JSON/frontend reads, and reconnect with changed values. — **auto + native Mac** (app/shared Rust contracts, Svelte checks, 0600 file inspection, disposable Keychain save/restart/clear on 2026-09-08). Native Windows credential-manager acceptance and live connected OBS/ComfyUI probes remain **manual/pending**.
- P-003 one versioned readiness contract expires stale evidence, gates Stream/Creator controls, and can synchronize sanitized idempotent observations to OpenTechnology. — **auto + native Mac** (seven shared-engine tests including exact loopback HTTP, both app suites/builds, companion receiver/template tests, and blocked-OBS native UI acceptance on 2026-09-09). Native Windows UI/credential storage and one hosted sync remain **manual/pending**.

- P-057 Creator Extend exposes validated per-run image/prompt/seed inputs, preserves graph connections and templates, and loads curated workflows without a repository working directory. — **auto** Rust workflow-input contracts; native Windows UI acceptance pending.
- P-057 upload → prepare → queue → completion discovery → bounded output preview round trip. — **manual** explicit ignored Rust acceptance test with local ComfyUI; synthetic CPU path only.
- P-057 validates ComfyUI output references, rejects traversal, caps preview bytes and bounds in-session history. — **auto** Rust preview contracts + Svelte check/build; native Mac panel inspected.
- P-057 native Creator UI uploads source/mask inputs, executes a model workflow and renders its returned preview. — **manual/macOS passed** (SDXL inpaint on Apple Metal, 40.37 seconds); native Windows pending.

## P-072 private preview acceptance

- Build the retained apps and private preview; test native pack admission, isolated preferences,
  locked-vault/Create independence and no broadcast/render/remote/publishing IPC. — **auto**,
  Rust/Node/Python contracts; native origin/vault enforcement still **manual**.
- Open the private artifact without optional prerequisites; choose each pack, restart, toggle
  layout, use folders by keyboard at narrow widths, install/retry selected tools and verify no
  unrelated warnings. — **manual/pending**, U-01/U-02/U-07; Windows repeats separately.
- Import/reveal an owned synthetic video, preserve separate profiles and original app data, reject
  crafted disabled-domain/status invokes and remote origins. — **manual/pending**, U-07.
- Real cross-workspace outputs, two-device control, credential migration, public upgrade/rollback
  and legacy retirement. — **blocked**, later P-072 phases and existing owner/acceptance gates.
