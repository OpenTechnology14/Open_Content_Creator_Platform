# Third-party provenance

> **Status:** Living ledger — one row per third-party component this repository imports, links, builds, pulls or
> recommends. · **Last reviewed:** 2026-10-23 · **Enforcement:** reference — it binds no one; its job is to make a
> flagged component impossible to miss.

**Maintainer:** the repository owner. **Pattern:** Ironfall's `Docs/CONTENT-PROVENANCE.md` — one row per component,
the license read from its source and flagged, attribution tracked in `THIRD_PARTY_NOTICES.md` — adapted from imported
art packs to software and models. **Plan:** [P-075](proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md); the owner decisions
this ledger feeds are `OSS-D07` to `OSS-D10`.

**Not legal advice.** Every license below was read on 2026-10-23 from the source named in its row: PyPI metadata for the
pinned version, `cargo metadata --locked`, the npm lockfiles, GitHub's license API, a model card, or the project's own
LICENSE file. A flag is a question for the owner, not a determination.

**Policy.** Ironfall rejects NC, SA, GPL, AGPL and unlicensed content because it ships a commercial game. This
repository is a platform that *integrates with* many tools, so it ledgers rather than forbids. A flagged component may
be imported, linked or recommended **only with its license named here**, and must not be bundled into a hosted paid
feature without an owner decision. The root license is MIT ([`../LICENSE`](../LICENSE)); it covers this repository's own
code and does not change any third party's terms.

**Flags.** **AGPL**, **GPL**, **LGPL**, **MPL** (copyleft, strong to weak) · **NC** non-commercial · **SA**
share-alike · **Non-OSI** source-available or custom terms · **Review** the license depends on something not verified
here. A dash means no flag.

## 1. Flagged components — owner review

### 1.1 Python libraries the code imports

| Component | Source | Version | License (source) | Use here | Flag | Bundled or redistributed? | Gate |
|---|---|---|---|---|---|---|---|
| `ultralytics` | PyPI | 8.3.0 | AGPL-3.0-or-later (PyPI) | `modules/sports-analytics/golf-tracer/tracer.py`, `pose-estimation/yolo_pose.py` | **AGPL** | No — installed by the user | `OSS-D07` |
| `pyvirtualcam` | PyPI | 0.11.1 | GPL-2.0 (PyPI) | `modules/realtime-ai/ar-filters/face_mesh_filter.py`, `comfyui/bridges/webcam_bridge.py`; `modules/sports-analytics/golf-tracer/ndi_output.py` | **GPL** | No — installed by the user | `OSS-D07` |
| `obsws-python` | PyPI | 1.8.0 (`>=1.7` in the exporter) | GPL-3.0-only (PyPI) | `modules/observability/source-health-exporter/exporter.py`, `scripts/setup/test_obs_websocket.py` | **GPL** | No — installed by the user | `OSS-D07` |
| `imageio-ffmpeg` | PyPI | 0.6.0 | BSD-2-Clause wrapper; the wheels ship an FFmpeg executable and the package page does not state its license | `modules/content-creation/stream_shorts/render.py`, `scripts/setup/capture_devices.py`, `scripts/setup/stream_autopilot.py` | **Review** | The wheel carries the binary; nothing is committed | `OSS-D07` |
| `opencv-python`, `opencv-python-headless` | PyPI | 4.10.0.84, `>=4.9` | Apache-2.0 (wrapper) | `modules/sports-analytics/`, `modules/observability/source-health-exporter/` | — | No; the wheels bundle other libraries, not verified here | — |

### 1.2 Services the compose files pull or build

| Component | Source | Version | License (source) | Use here | Flag | Bundled or redistributed? | Gate |
|---|---|---|---|---|---|---|---|
| MinIO server and `mc` client | `github.com/minio/minio`, `minio/mc` | pinned in `modules/storage-data/minio/Dockerfile` | AGPL-3.0 (GitHub) | S3-compatible object storage | **AGPL** | Built locally from pinned sources; CI pushes only the FastAPI image | `OSS-D08` |
| Grafana | `grafana/grafana` image | `:latest` | AGPL-3.0 (GitHub) | Dashboards | **AGPL** | No — pulled by the user | `OSS-D08` |
| Loki | `grafana/loki` image | `:latest` | AGPL-3.0 (GitHub) | Log aggregation | **AGPL** | No | `OSS-D08` |
| promtail | `grafana/promtail` image | `:latest` | not separately checked | Log shipping | **Review** | No | `OSS-D08` |
| n8n | `n8nio/n8n` image, two services | `:latest` | Sustainable Use License; `.ee.` files need an Enterprise License (its LICENSE.md) | Workflow automation | **Non-OSI** | No | `OSS-D08` |
| Redis | `redis:7-alpine`, in `docker-compose.yml` and `cloud/docker-compose.relay.yml` | floating 7.x | BSD-3-Clause to 7.2.x; RSALv2 or SSPLv1 from 7.4; AGPLv3 added at 8 (redis.io/legal/licenses) | Cache and pub/sub | **Non-OSI** on current 7.x | No | `OSS-D08` |
| Valkey | `valkey-io/valkey` | — | BSD-3-Clause (GitHub) | A drop-in alternative to Redis, not used | — | — | `OSS-D08` |

The base images (`python`, `debian`, `golang`, `alpine`) carry their distribution packages' usual mixed licenses, as
any container does. The only image this repository publishes is the FastAPI one, on `v*` tags
(`.github/workflows/build-images.yml`); it installs the permissive Python packages in section 2.1.

### 1.3 Hosts the in-repo plugins link or import

| Component | Source | Version | License (source) | Use here | Flag | Bundled or redistributed? | Gate |
|---|---|---|---|---|---|---|---|
| OBS Studio (libobs) | `github.com/obsproject/obs-studio` | not pinned | GPL-2.0 (GitHub) | `plugins/obs-plugin/CMakeLists.txt` links `obs` | **GPL** | The plugin binary would be a combined work | `OSS-D09` |
| Blender | `github.com/blender/blender` mirror | not pinned | multiple licenses (GitHub reports `NOASSERTION`); GPL application | `plugins/blender-addon/` imports `bpy`; its `bl_info` declares MIT | **GPL** (host) | No | `OSS-D09` |
| Krita | `github.com/KDE/krita` | not pinned | GPL-3.0 (GitHub) | `plugins/krita-integration/` scripts the `krita` module | **GPL** (host) | No | `OSS-D09` |

Plugins that use a host's API are commonly treated as covered by the host's license. MIT source is GPL-compatible, but a
distributed plugin binary follows the host's terms. `plugins/LICENSE` is MIT.

### 1.4 Models the docs recommend

Nothing is committed. `modules/model-registry/registry.yml` is deliberately empty because no weight has been downloaded
and checksummed; the shopping lists are `modules/realtime-ai/comfyui/models.md` and
`modules/sports-analytics/models/README.md`.

| Model | Source | License (source) | Flag | Gate |
|---|---|---|---|---|
| SDXL Turbo | `stabilityai/sdxl-turbo` | `sai-nc-community` (model card) | **NC** | `OSS-D10` |
| FLUX.1 Fill [dev] | `black-forest-labs/FLUX.1-Fill-dev` | `flux-1-dev-non-commercial-license`; the card says outputs may be used commercially | **NC** (the model) | `OSS-D10` |
| RMBG-1.4 | `briaai/RMBG-1.4` | `bria-rmbg-1.4`, a non-commercial Creative Commons license; commercial use needs an agreement | **NC** | `OSS-D10` |
| 4x-UltraSharp | OpenModelDB | CC-BY-NC-SA-4.0 | **NC**, **SA** | `OSS-D10` |
| YOLOv8 weights (`yolov8n.pt`, `yolov8n-pose.pt`) | Ultralytics | the Ultralytics terms; AGPL-3.0 for the library (weights not separately checked) | **AGPL** | `OSS-D07`, `OSS-D10` |
| SDXL base 1.0, SD 1.5, LCM-LoRA, ControlNets, IP-Adapter, SAM and variants, the inpainting checkpoints, SDXL VAE | various | not recorded here and not verified | **Review** | `OSS-D10` |

### 1.5 External tools the docs integrate with, not bundled

| Tool | License (source) | Flag | Note |
|---|---|---|---|
| ComfyUI | GPL-3.0 (GitHub) | **GPL** | The user installs it; the platform talks to it over HTTP |
| DeepFaceLive | GPL-3.0 (GitHub) | **GPL** | Local GPU tool |
| Deep-Live-Cam | AGPL-3.0 (GitHub) | **AGPL** | Local GPU tool |
| Krita AI Diffusion | GPL-3.0 (GitHub) | **GPL** | Krita plugin |
| AITuberKit | A custom license that offers a non-commercial license or a commercial one (its LICENSE) | **NC** | Read it before recommending it in a product that charges |
| OBS Studio | GPL-2.0 (GitHub) | **GPL** | See 1.3 |
| NodeCG, Ollama | MIT (GitHub) | — | |
| Prometheus | Apache-2.0 (GitHub) | — | |
| Tailscale | BSD-3-Clause for the client (GitHub) | — | The service itself is proprietary |
| VTube Studio, VoiceMeeter, VB-Cable, DaVinci Resolve | proprietary | **Non-OSI** | Not redistributed |

## 2. Direct dependencies

None is vendored: there are no submodules and no vendored directories. Compiled Rust crates and built frontend assets are
inside the desktop installers, which today are private, unsigned CI artifacts; the full per-crate notice texts are a
release artifact (`OSS-D15`, [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)).

### 2.1 Python — 35 distinct packages in the requirements files

| Package | Spec | License read at | License | Used by | Flag |
|---|---|---|---|---|---|
| `aiohttp` | `>=3.9` | 3.14.5 | Apache-2.0 AND MIT | observability | — |
| `asyncpg` | `==0.29.0, ==0.30.*` | 0.29.0 | Apache-2.0 | ai-agents, backend-api, cloud/relay-api | — |
| `boto3` | `==1.35.*` | 1.43.118 | Apache-2.0 | cloud/relay-api | — |
| `fastapi` | `==0.115.*, ==0.115.0` | 0.115.0 | MIT | backend-api, cloud/relay-api | — |
| `filterpy` | `==1.4.5` | 1.4.5 | MIT | sports-analytics | — |
| `httpx` | `==0.27.2, ==0.28.*` | 0.27.2 | BSD | ai-agents, audio-production, automation-control, backend-api, cloud/relay-api, sports-analytics | — |
| `imageio-ffmpeg` | `==0.6.0` | 0.6.0 | BSD-2-Clause (wrapper) | content-creation | Review: bundled FFmpeg binary |
| `keyring` | `==25.6.0` | 25.6.0 | MIT | social-management | — |
| `loguru` | `==0.7.2, >=0.7.2` | 0.7.2 | MIT | ai-agents, asset-pipeline, audio-production, automation-control, backend-api, character-avatar, cloud/relay-api, model-registry, sports-analytics | — |
| `mediapipe` | `==0.10.14` | 0.10.14 | Apache-2.0 | sports-analytics | — |
| `minio` | `==7.2.8, >=7.2.0` | 7.2.8 | Apache-2.0 | asset-pipeline, backend-api | — |
| `numpy` | `==1.26.4, >=1.24` | 1.26.4 | BSD | observability, sports-analytics | — |
| `obsws-python` | `==1.8.0, >=1.7` | 1.8.0 | GPL-3.0-only | observability, scripts/setup | GPL |
| `opencv-python` | `==4.10.0.84` | 4.10.0.84 | Apache-2.0 (wrapper) | sports-analytics | Note: wheels bundle other libraries; not verified here |
| `opencv-python-headless` | `>=4.9` | 5.0.0.93 | Apache-2.0 (wrapper) | observability | Note: wheels bundle other libraries; not verified here |
| `passlib` | `==1.7.*` | 1.7.4 | BSD | cloud/relay-api | — |
| `pgvector` | `==0.3.3` | 0.3.3 | MIT | ai-agents | — |
| `prometheus-client` | `==0.20.0` | 0.20.0 | Apache-2.0 | backend-api | — |
| `prometheus-fastapi-instrumentator` | `==7.0.0` | 7.0.0 | ISC | backend-api | — |
| `psutil` | `>=5.9` | 7.2.2 | BSD-3-Clause | observability | — |
| `pydantic` | `==2.*, ==2.9.2` | 2.9.2 | MIT | ai-agents, audio-production, automation-control, backend-api, character-avatar, cloud/relay-api, content-creation, social-management | — |
| `pydantic-settings` | `==2.*, ==2.5.2` | 2.5.2 | MIT | backend-api, cloud/relay-api | — |
| `pytest` | `==8.3.2` | 8.3.2 | MIT |  | — |
| `python-jose` | `==3.3.*` | 3.5.0 | MIT | cloud/relay-api | — |
| `python-multipart` | `==0.0.*, ==0.0.10` | 0.0.10 | Apache-2.0 | backend-api, cloud/relay-api | — |
| `pyvirtualcam` | `==0.11.1` | 0.11.1 | GPL-2.0 | sports-analytics | GPL |
| `pyyaml` | `==6.0.2, >=6.0` | 6.0.2 | MIT | ai-agents, audio-production, automation-control, character-avatar, marketing-crosswalk, model-registry, observability, social-management | — |
| `redis` | `==5.*, ==5.0.8, >=5.0` | 5.0.8 | MIT | ai-agents, backend-api, cloud/relay-api, observability | — |
| `sqlalchemy` | `==2.0.35` | 2.0.35 | MIT | backend-api | — |
| `stripe` | `==11.*` | 16.0.0 | MIT | cloud/relay-api | — |
| `tzdata` | `==2026.3` | 2026.3 | Apache-2.0 | automation-control | — |
| `ultralytics` | `==8.3.0` | 8.3.0 | AGPL-3.0-or-later | sports-analytics | AGPL |
| `uvicorn` | `==0.30.6, ==0.32.*` | 0.30.6 | BSD | backend-api, cloud/relay-api | — |
| `voicemeeter-api` | `>=2.0` | 2.7.2 | MIT | observability | — |
| `websockets` | `==13.*, ==13.0.1, ==13.1, >=12.0` | 13.0.1 | BSD | ai-agents, audio-production, automation-control, backend-api, character-avatar, cloud/relay-api, observability | — |

### 2.2 Rust — 23 direct third-party crates of the 10 first-party crates

| Crate | Version | License | Used by |
|---|---|---|---|
| `base64` | 0.21.7, 0.22.1 | MIT OR Apache-2.0 | creator-extend, extend-preview |
| `fs2` | 0.4.3 | MIT/Apache-2.0 | stream-extend |
| `futures-util` | 0.3.34 | MIT OR Apache-2.0 | stream-extend |
| `obws` | 0.15.0 | MIT | extend-preview, stream-extend |
| `reqwest` | 0.12.28, 0.13.4 | MIT OR Apache-2.0 | creator-extend, extend-preview |
| `serde` | 1.0.229 | MIT OR Apache-2.0 | creator-extend, extend-preview, stream-extend |
| `serde_json` | 1.0.151 | MIT OR Apache-2.0 | creator-extend, extend-preview, stream-extend |
| `sha2` | 0.10.9, 0.11.0 | MIT OR Apache-2.0 | creator-extend, extend-preview |
| `tauri` | 2.11.5 | Apache-2.0 OR MIT | creator-extend, extend-preview, stream-extend |
| `tauri-build` | 2.6.3 | Apache-2.0 OR MIT | creator-extend, extend-preview, stream-extend |
| `tauri-plugin-dialog` | 2.7.3 | Apache-2.0 OR MIT | creator-extend, extend-preview |
| `tauri-plugin-http` | 2.6.0 | Apache-2.0 OR MIT | creator-extend, stream-extend |
| `tauri-plugin-notification` | 2.4.0 | Apache-2.0 OR MIT | creator-extend, stream-extend |
| `tauri-plugin-shell` | 2.3.6 | Apache-2.0 OR MIT | creator-extend, stream-extend |
| `tauri-plugin-store` | 2.4.4 | Apache-2.0 OR MIT | creator-extend, stream-extend |
| `time` | 0.3.55 | MIT OR Apache-2.0 | extend-preview, stream-extend |
| `tokio` | 1.53.1 | MIT | creator-extend, extend-preview, stream-extend |
| `tokio-tungstenite` | 0.24.0 | MIT | stream-extend |
| `tracing` | 0.1.44 | MIT | creator-extend, extend-preview, stream-extend |
| `tracing-subscriber` | 0.3.23 | MIT | creator-extend, extend-preview, stream-extend |
| `url` | 2.5.8 | MIT OR Apache-2.0 | creator-extend, extend-preview, stream-extend |
| `uuid` | 1.26.0 | Apache-2.0 OR MIT | creator-extend, extend-preview |
| `wiremock` | 0.6.5 | MIT/Apache-2.0 | creator-extend, extend-preview |

All 23 are MIT, Apache-2.0 or both.

### 2.3 Node — 17 direct packages

| Package | Version | License | Kind | Used by |
|---|---|---|---|---|
| `@sveltejs/adapter-static` | 3.0.10 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@sveltejs/kit` | 2.70.3 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@sveltejs/vite-plugin-svelte` | 5.1.1 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/api` | 2.11.1 | Apache-2.0 OR MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/cli` | 2.11.4 | Apache-2.0 OR MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/plugin-dialog` | 2.7.3 | MIT OR Apache-2.0 | build tooling | apps/creator-extend, apps/extend |
| `@tauri-apps/plugin-http` | 2.6.0 | MIT OR Apache-2.0 | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/plugin-notification` | 2.4.0 | MIT OR Apache-2.0 | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/plugin-shell` | 2.3.6 | MIT OR Apache-2.0 | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@tauri-apps/plugin-store` | 2.4.4 | MIT OR Apache-2.0 | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `@types/node` | 22.20.1 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `mineflayer` | 4.39.0 | MIT | runtime | automation-control/stream_autopilot/minecraft |
| `redis` | unpinned | MIT (npm registry, latest) | runtime | broadcast-graphics/nodecg/bundles/hcp-starter |
| `svelte` | 5.57.0 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `svelte-check` | 4.7.6 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `typescript` | 5.9.3 | Apache-2.0 | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |
| `vite` | 6.4.3 | MIT | build tooling | apps/creator-extend, apps/extend, apps/stream-extend |

### 2.4 Transitive summary

**Rust:** 614 third-party crates across the three desktop apps, 33 distinct license expressions. The most common:

| License expression | Crates |
|---|---|
| MIT OR Apache-2.0 | 295 |
| MIT | 136 |
| Apache-2.0 OR MIT | 57 |
| MIT/Apache-2.0 | 29 |
| Unicode-3.0 | 18 |
| Zlib OR Apache-2.0 OR MIT | 17 |
| Unlicense OR MIT | 9 |
| MPL-2.0 | 5 |
| Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT | 5 |
| BSD-3-Clause | 4 |
| Apache-2.0/MIT | 4 |
| ISC | 3 |

Plus 21 more, all permissive combinations of MIT, Apache-2.0, BSD, ISC, Zlib, Unicode and Unlicense. **Flagged:** five
**MPL-2.0** crates — `cssparser`, `cssparser-macros`, `dtoa-short`, `option-ext`, `selectors` (file-level copyleft;
unmodified here) — one **CDLA-Permissive-2.0** data crate, `webpki-roots`, and `r-efi` (two versions), whose license
offers MIT or Apache-2.0 beside an LGPL-2.1-or-later option. No GPL or AGPL crate.

**Node:** `apps/stream-extend`, `apps/creator-extend` and `apps/extend` have 125, 126 and 126 lockfile entries, all
build tooling (MIT 103, Apache-2.0 OR MIT 13, MIT OR Apache-2.0 4 or 5, Apache-2.0 3, ISC 1, BSD-3-Clause 1).
`modules/automation-control/stream_autopilot/minecraft` has 90 (MIT 76, BSD-3-Clause 4, Apache-2.0 3, BSD 2,
BSD-2-Clause 2, CC0-1.0 1, ISC 1, 0BSD 1). No copyleft.

### 2.5 Mobile bridges — no manifest

`mobile/` holds four source files (two Kotlin, two Swift) and no Gradle or Swift package manifest, so there is nothing to
walk. The Kotlin files import `kotlinx.coroutines` and `okhttp3`; both are Apache-2.0 upstream, which was **not** read here.
HaishinKit is named only in TODO comments (BSD-3-Clause per GitHub). Add rows here when a manifest exists.

## 3. Assets

| Asset | Source | License | Note |
|---|---|---|---|
| Eight soundboard files in `modules/soundboard/sounds/` | Kenney.nl, Interface Sounds, per `manifest.yaml` | CC0 1.0 | Thirteen further slots are placeholders with no audio, because the obvious clip is copyrighted |
| Desktop app icons and `icon-source.png` | `scripts/setup/generate_placeholder_icons.py` | First-party | Flat placeholders, not branding |
| `docs/assets/logo.svg` and four marks in `modules/social-management/assets/brands/` | First-party | MIT, as the repository | |
| UI icons | `lucide-react`, imported inline by web consumers | not committed | |
| Screenshots | none tracked | — | The README's hero image is a commented placeholder |
| Fonts | none tracked | — | |

## 4. Before adding a dependency or recommending a model

- [ ] The license is read from its source (registry metadata, the project's LICENSE, or the model card), not from memory.
- [ ] A row is added here with source, version, license, use and flag.
- [ ] An NC, SA, GPL, AGPL, non-OSI or custom license is flagged, and not bundled into a hosted paid feature without an
      owner decision.
- [ ] Attribution is added to `THIRD_PARTY_NOTICES.md` if the license requires it.
- [ ] Weights and binaries are not committed; a weight gets a `model-registry` entry with a real checksum.

## 5. Reproduce

```bash
# Python: the license of one pinned requirement (PyPI metadata)
curl -s https://pypi.org/pypi/<name>/<version>/json | python3 -c "import json,sys;i=json.load(sys.stdin)['info'];print(i.get('license_expression') or i.get('license'))"
# Rust: every crate with its license, per app
cargo metadata --locked --format-version 1 --manifest-path apps/stream-extend/src-tauri/Cargo.toml
# Node: license counts of one lockfile
python3 -c "import json,collections;l=json.load(open('apps/stream-extend/package-lock.json'))['packages'];print(collections.Counter(p.get('license') for k,p in l.items() if k))"
# A tool or service repository
gh api repos/<owner>/<repo>/license --jq .license.spdx_id
```
