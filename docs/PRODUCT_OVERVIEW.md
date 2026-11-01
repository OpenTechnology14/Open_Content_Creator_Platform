# Product overview

> **Status:** Product description and plans · **Last reviewed:** 2026-10-23 · **Enforcement:** reference. This is the product
> and commercial half of the former root `README.md`, moved here whole on 2026-10-23 when the README was rewritten for a
> public reader ([P-075](proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md)). **Prices, tiers and store descriptions below are
> product plans, not offers or installed capabilities**; whether to keep them public is an owner decision (`OSS-D13`).

> **Pre-release integration repository.** This combined workspace is the canonical source for shared desktop setup, both Extend app prototypes, the relay client, cloud services, plugins, mobile bridges, cross-product scenarios, and platform documentation. It is not yet a production release. See [the audit](AUDIT.md), [release checklist](OPEN_SOURCE_RELEASE_CHECKLIST.md), and [repository alignment policy](REPOSITORY_ALIGNMENT.md).

## Repository map

| Repository | Role |
|---|---|
| [Open_Content_Creator_Platform](https://github.com/OpenTechnology14/Open_Content_Creator_Platform) | Canonical combined integration and shared desktop source |
| [ContentExtend](https://github.com/OpenTechnology14/ContentExtend) | Content-focused product distribution, modules, guides, and release documentation |
| [StreamExtend](https://github.com/OpenTechnology14/StreamExtend) | Streaming-focused product distribution, modules, guides, and release documentation |

The existing code path `apps/creator-extend` is the legacy/internal name for the ContentExtend desktop prototype. It remains unchanged during the initial repository import; its controlled rename/export is tracked in the alignment policy.

<!-- TODO: Add hero screenshot — 1280x720 of the Stream Extend dashboard
<p align="center">
  <img src="assets/screenshots/hero.png" alt="Stream Extend dashboard" width="100%" />
</p>
-->

## Why Stream Extend / Creator Extend

Most creators juggle a dozen free tools with no central control. These apps wrap them into one dashboard you can access from any device — without locking you into a subscription for local features.

| | Stream Extend | Creator Extend | OBS alone | Doing it manually |
|---|---|---|---|---|
| One-click setup | Planned | Planned | No | No |
| Mobile control | Yes | Yes | No | No |
| AI effects dashboard | Yes | — | Plugin-by-plugin | DIY |
| ComfyUI workflows | — | Yes | No | CLI only |
| Blender + Krita integration | — | Yes | No | Separate apps |
| Free without cloud | Yes | Yes | Yes | Yes |
| Remote access from phone | $5/mo | $5/mo | No | VPN setup |

**Local-first is the design target.** Implementation and operating-system acceptance are incomplete;
paid remote features described here are product plans, not installed setup capabilities.

These are product targets with uneven implementation and OS verification — see [Features, organised by module](#features--organised-by-module)
for which one, and [`modules/README.md`](../modules/README.md) for how to set it up.

---

## Get Started

New to streaming? Start with the [beginner documentation website](public/index.html).
It covers a private practice recording, common problems, clipping and an engineering reading path.

The complete platform is not yet certified on both Mac and Windows. Installing a desktop
app or running the first setup command does not install every module, external app or model.

**Open an app first.** Follow the [desktop launch and setup guide](../modules/infrastructure/setup/desktop-setup.md)
for Stream Extend or Creator Extend / ContentExtend. Use the private installers from the
Desktop installers workflow (private development evidence; not distributed)
or the documented source-build fallback. Reach
**Module setup**, then choose capabilities. OBS, Docker/WSL, Python, models and cloud accounts
are not gates on opening the packaged setup view; their checks apply when a feature needs them.
Private Windows x64 and Apple Silicon Mac installers are built; additional in-app setup actions are planned in
[P-063](PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup).

### Select the modules you need

After opening the app, prefer its **Module setup** panel. If Python is missing or you are using
the source CLI, the optional Windows bootstrap can install Python 3.12, OBS Studio and FFmpeg,
install the selected local module dependencies, run readiness checks and create a capture-device
report:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -InstallDesktopApps
```

Use `-Preset creator`, or `-Preset custom -Modules soundboard,audio-production`, to avoid the
default streaming selection. `-InstallDesktopApps` refers to OBS/FFmpeg, not either Extend app;
omit it to defer an OBS installation blocker. Docker is not installed by this script.
Add `-PlanOnly` to preview without installing (Python 3.12 must already be installed). See the
[à la carte setup guide](../modules/infrastructure/setup/module-selection.md).

On either platform, Python 3.12 can drive the lower-level catalog directly:

```powershell
py -3.12 scripts/setup/modules.py list
py -3.12 scripts/setup/modules.py plan --modules ai-agents audio-production content-creation
py -3.12 scripts/setup/modules.py install --modules ai-agents audio-production content-creation
```

On Mac, replace `py -3.12` with `python3.12`. Each selected module gets its own environment;
the report links remaining manual setup. OBS, plugins, game clients, models, audio drivers and
containers are not installed by the Python command. Both desktop apps also open a shared
[Module setup panel](../modules/infrastructure/setup/desktop-setup.md), with saved checkboxes,
profiles, Python dependency installation, capture-device discovery, checks and bundled manual
guides. Native Mac acceptance is recorded; native Windows acceptance remains pending.

The apps' **Connections** view persists local service endpoints. OBS and MinIO secrets are kept
in the operating system credential manager and are represented in the UI only as saved/not-saved.

For the bundled streaming rehearsal, use the [Windows/Mac test guide](../modules/ai-agents/stream_host/WINDOWS_TEST.md),
which installs a shared test environment and exercises real speech and synthetic Shorts.

The remaining app-store, subscription and one-click onboarding descriptions are product plans,
not a claim that a fresh Mac or Windows installation has every feature working.

### Step 2 — Add free plugins (optional)

The plugins work inside OBS and Blender even without the apps. Free, open source, MIT licensed.

| Plugin | What it does | Install |
|--------|-------------|---------|
| **OBS Plugin** | Imports scenes, configures encoder, creates Browser Sources | [Download](https://streamextend.com/obs-plugin) → drop in OBS plugins folder |
| **Blender Addon** | Template gallery, MinIO upload, ComfyUI triggers | [Download](https://creatorextend.com/blender-addon) → Edit > Preferences > Add-ons > Install |
| **Krita Plugin** | AI editing, batch upscale, style transfer, MinIO export | [Download](https://creatorextend.com/krita-plugin) → copy to Krita's pykrita folder |

---

## Subscribe for Cloud

**Only needed if you want remote access from your phone or another device.** All local features work without a subscription.

### How to subscribe

1. Open Stream Extend or Creator Extend
2. Go to **Settings > Cloud**
3. Pick a tier
4. Done — the app connects automatically

| | Free | Connect | Pro | Team |
|---|---|---|---|---|
| **Price** | $0/mo | $5/mo | $12/mo | $25/mo |
| All local features | Yes | Yes | Yes | Yes |
| Remote access from mobile | — | Yes | Yes | Yes |
| Push notifications | — | Yes | Yes | Yes |
| Cloud dashboards (Grafana) | — | — | Yes | Yes |
| Multi-device sync | — | — | Yes | Yes |
| Multi-user / team access | — | — | — | Yes |

The cloud relay runs on DigitalOcean. Your data stays isolated — every subscriber gets their own tenant with row-level security in Postgres and prefix-isolated storage in Spaces.

**What the subscription actually does:** the app opens a WebSocket to `relay.streamextend.com` (or `relay.creatorextend.com`). Your desktop and mobile apps relay messages through it. That's the entire cloud component — a WebSocket bridge with auth and storage.

---

## Self-Hosting (Advanced)

**For developers and teams who want to run their own cloud relay** instead of using the hosted one. This replaces the subscription — connect your apps to your own relay and pay nothing monthly.

### What you need

| Service | Cost | Purpose |
|---------|------|---------|
| A Linux server (any VPS) | ~$12–24/mo | Runs the relay API |
| PostgreSQL | Included or ~$15/mo managed | Multi-tenant database |
| Redis | Included | WebSocket pub/sub |
| Domain name | ~$12/year | HTTPS for your relay |

### Option A — Docker Compose (simplest)

```bash
git clone https://github.com/OpenTechnology14/Open_Content_Creator_Platform.git
cd Open_Content_Creator_Platform/cloud

# Set your secrets
cp .env.example .env
# Edit .env — set RELAY_JWT_SECRET, POSTGRES_PASSWORD

# Start everything
docker compose -f docker-compose.relay.yml up -d
```

Your relay is now running at `http://your-server:8000`. Put it behind a reverse proxy (Caddy, nginx) for HTTPS.

### Option B — DigitalOcean with Terraform

```bash
cd cloud/terraform

# Set variables
export TF_VAR_do_token="your-do-api-token"
export TF_VAR_ssh_key_fingerprint="your-key-fingerprint"
export TF_VAR_domain="yourdomain.com"

terraform init
terraform plan
terraform apply
```

This provisions: a Droplet, Managed Postgres, Spaces bucket, firewall, and DNS records.

### Option C — Manual setup

1. Provision a server (Ubuntu 24.04 recommended)
2. Install Docker: `curl -fsSL https://get.docker.com | sh`
3. Install Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh`
4. Clone the repo and run the Docker Compose stack
5. Run the database migration: `psql -f cloud/migrations/001_init.sql`
6. Put a reverse proxy in front (Caddy recommended for auto-HTTPS)

### Connect your apps to your relay

Once your relay is running:

1. Open Stream Extend or Creator Extend
2. Go to **Settings > Cloud > Self-Hosted**
3. Enter your relay URL (e.g., `https://relay.yourdomain.com`)
4. Enter your API key (generate one from the relay admin)
5. Done — same features as the hosted subscription, on your infrastructure

### Self-hosted relay API reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Health check |
| `POST /api/v1/auth/verify-purchase` | Verify app store receipt |
| `POST /api/v1/auth/self-hosted-key` | Generate API keys |
| `WS /ws` | WebSocket relay (main connection) |
| `GET/PUT /api/v1/sync/{key}` | Multi-device sync |
| `POST /api/v1/notifications/send` | Push notifications |
| `POST /api/v1/metrics/push` | Metric persistence |

Full API docs available at `https://your-relay/docs` (auto-generated Swagger UI).

---

## Features — organised by module

**Every feature belongs to a module, and the module is the root of understanding it.** A module
owns its setup (manual and automated), its configuration docs, its dependencies, and its
implementation status. There is no separate feature list to drift out of step — this table *is*
the feature list, and each row links to the module that defines it.

Full index with setup order: **[`modules/README.md`](../modules/README.md)**.

### `Stream` — Stream Extend

| Module | Feature |
|---|---|
| [creator-experience](../modules/creator-experience/) | OBS scene collections, encoder config, mic filter chain |
| [realtime-ai](../modules/realtime-ai/) | Face filters, background removal, ComfyUI stylization |
| [broadcast-graphics](../modules/broadcast-graphics/) | NodeCG overlays, alerts, sponsor rotation, scoreboards |
| [audio-production](../modules/audio-production/) | VoiceMeeter / BlackHole / PipeWire routing, VST chains |
| [ai-agents](../modules/ai-agents/) | Local-LLM co-hosts with memory, moderation, avatar control |
| [character-avatar](../modules/character-avatar/) | PNGTubers, VTube Studio, VRM |
| [soundboard](../modules/soundboard/) | DJ-style sound bar — named, hotkeyed audio clips, OBS-native |
| [observability](../modules/observability/) | Grafana dashboards — stream health, GPU, dropped frames |
| [backend-api](../modules/backend-api/) | FastAPI + WebSocket fanout for overlays, mobile, automation |

### `Content` — Creator Extend

| Module | Feature |
|---|---|
| [realtime-ai](../modules/realtime-ai/) | ComfyUI workflows — queue, monitor, manage |
| [content-creation](../modules/content-creation/) | Blender projects, DaVinci Resolve, render pipelines |
| [image-editing](../modules/image-editing/) | Krita AI editing — inpaint, upscale, SAM segmentation |
| [nature-generation](../modules/nature-generation/) | Landscape generation from your own photographs — full scenes down to tone grading |
| [cityscape-generation](../modules/cityscape-generation/) | Urban generation from your own photographs — plus perspective correction |
| [sports-analytics](../modules/sports-analytics/) | Golf shot tracing, pose estimation, swing analysis, replay |
| [marketing-crosswalk](../modules/marketing-crosswalk/) | Marketing content generation for registered consumer modules |

> **Bringing your own photographs in?** Both generation modules learn from a corpus you supply.
> Start at **[`docs/IMAGE_INTAKE.md`](IMAGE_INTAKE.md)** — it covers the buckets, the
> provenance record that keeps a trained adapter distributable, the rights and format matrices,
> and the rule for deciding whether a photo is nature or cityscape.

### `Content` `Stream` — shared foundations

| Module | Feature |
|---|---|
| [storage-data](../modules/storage-data/) | Postgres, Redis, MinIO — assets, state, recordings |
| [asset-pipeline](../modules/asset-pipeline/) | One storage contract — the shared MinIO/S3 client every module uses |
| [model-registry](../modules/model-registry/) | Model/adapter provenance — checksum, license, distributability |
| [automation-control](../modules/automation-control/) | OBS WebSocket, n8n workflows |
| [infrastructure](../modules/infrastructure/) | Docker Compose, Tailscale, DigitalOcean, backups |
| [social-management](../modules/social-management/) | Stream/content profiles, logos, connected accounts, approved posting and live destinations |

### Cloud-gated (subscription, not a module)

These five are the *only* features that need a network connection —
[`product-spec.md`](architecture/product-spec.md) §Pricing:

- **Remote access** — drive your setup from outside your network (Connect+)
- **Push notifications** — stream alerts, render completion, errors (Connect+)
- **Metric persistence** — dashboards from any device (Pro+)
- **Multi-device sync** — settings, presets, workflows (Pro+)
- **Team access** — multiple people, one platform (Team)

Everything else in the tables above works locally, forever, for free.

> **Read the status before believing a row.** Module maturity varies; [`CLAUDE.md`](../CLAUDE.md)
> §11 records the current level and [`docs/AUDIT.md`](AUDIT.md) records the evidence and
> limitations behind it.

---

## Pricing

### Apps (one-time purchase)

| App | Price | Platforms |
|-----|-------|-----------|
| Stream Extend | $20 | Mac, Windows, iOS, Android |
| Creator Extend | $20 | Mac, Windows, iOS, Android |

### Cloud subscription (optional)

| | Free | Connect | Pro | Team |
|---|---|---|---|---|
| **Price** | $0/mo | $5/mo | $12/mo | $25/mo |
| Local features | All | All | All | All |
| Remote access | — | Yes | Yes | Yes |
| Push notifications | — | Yes | Yes | Yes |
| Cloud dashboards | — | — | Yes | Yes |
| Multi-device sync | — | — | Yes | Yes |
| Team access | — | — | — | Yes |

### Source code

The root license is MIT ([`LICENSE`](../LICENSE)); plugins carry [`plugins/LICENSE`](../plugins/LICENSE). Optional integrations can carry copyleft or non-commercial terms of their own: see [Third-party provenance](THIRD_PARTY_PROVENANCE.md).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop + Mobile Apps | Tauri 2 (Rust + SvelteKit) |
| Mobile Streaming | HaishinKit (Swift / Kotlin) — RTMP + SRT |
| OBS Plugin | C (libobs) |
| Blender Addon | Python (bpy) |
| Krita Plugin | Python (PyQt5) |
| Cloud Relay | FastAPI, asyncpg, WebSockets |
| Database | PostgreSQL 16 with row-level security |
| Cache / Pub-Sub | Redis 7 |
| Object Storage | MinIO (local) / DigitalOcean Spaces (cloud) |
| Infrastructure | Docker, Terraform, Tailscale |
| Observability | Prometheus, Grafana, Loki |
| AI Backend | ComfyUI, Ollama, XTTS v2 |
| Payments | Stripe + App Store / Play Store receipts |

---

## Project Structure

```
apps/
  stream-extend/          Tauri desktop+mobile — OBS, AI, overlays, agents
  creator-extend/         Tauri desktop+mobile — ComfyUI, Blender, Krita, sports CV
  shared/relay-client/    Rust crate — dual-mode relay (hosted or self-hosted)

plugins/                  Free, MIT licensed
  obs-plugin/             C — scene import, encoder config, Browser Sources
  blender-addon/          Python — templates, MinIO, ComfyUI triggers
  krita-integration/      Python — AI editing, batch upscale, style transfer

cloud/
  relay-api/              FastAPI multi-tenant relay with subscription auth
  migrations/             PostgreSQL schema with row-level security
  terraform/              DigitalOcean infrastructure as code

mobile/
  ios/                    HaishinKit Swift — RTMP/SRT from iPhone camera
  android/                HaishinKit Kotlin — RTMP/SRT from Android camera

modules/                  Platform modules (local tools, no cloud required)
                          each has README.md + setup/{manual,automated}.md + config docs
  creator-experience/     OBS configs, scene collections
  realtime-ai/            ComfyUI, background removal, face filters
  automation-control/     n8n, OBS WebSocket, Advanced Scene Switcher
  storage-data/           MinIO, PostgreSQL, Redis configs
  sports-analytics/       Golf tracer, pose estimation, YOLO
  content-creation/       Blender projects, DaVinci Resolve
  image-editing/          Krita scripts, ComfyUI inpainting workflows
  nature-generation/      Corpus-learned landscape generation + tone grading
  cityscape-generation/   Corpus-learned urban generation + perspective + tone
  marketing-crosswalk/    Marketing content generation for consumer modules
  social-management/      Profiles, logos, account connections, publishing/live gates
  backend-api/            FastAPI, WebSocket services
  broadcast-graphics/     NodeCG overlays, alerts, scoreboards
  observability/          Prometheus, Grafana, Loki, alerting
  infrastructure/         Docker, Tailscale, DigitalOcean
  audio-production/       VoiceMeeter, BlackHole, VST routing
  character-avatar/       PNGTubers, VTube Studio, VRM
  ai-agents/              Local LLMs, memory, personas, moderation

design-system/           Ecosystem design-system hub: tokens, component specs, voice registers (drafted; other repos keep pointer docs)

docs/
  guides/                 Redirect map — setup now lives in modules/<name>/setup/
  architecture/           Product spec, roadmap, decision docs, deviations
```

---

## Environment Variables

### Apps (set in app Settings UI — no files to edit)

The apps auto-detect local services. Override in Settings if needed:

| Setting | Default | Purpose |
|---------|---------|---------|
| OBS WebSocket URL | `ws://localhost:4455` | OBS connection |
| ComfyUI URL | `http://localhost:8188` | ComfyUI API |
| MinIO Endpoint | `http://localhost:9000` | Object storage |
| Grafana URL | `http://localhost:3000` | Dashboards |

### Cloud relay (`.env` file — only for self-hosted)

| Variable | Required | Purpose |
|----------|:--------:|---------|
| `RELAY_JWT_SECRET` | Yes | Token signing (min 32 chars) |
| `RELAY_DATABASE_URL` | Yes | Postgres connection string |
| `RELAY_REDIS_URL` | Yes | Redis connection string |
| `RELAY_STRIPE_SECRET_KEY` | For billing | Stripe API key |
| `RELAY_STRIPE_WEBHOOK_SECRET` | For billing | Webhook verification |
| `RELAY_SPACES_ACCESS_KEY` | For storage | DO Spaces / S3 key |
| `RELAY_SPACES_SECRET_KEY` | For storage | DO Spaces / S3 secret |
| `RELAY_APNS_KEY_PATH` | For iOS push | Apple Push Notification key |
| `RELAY_FCM_CREDENTIALS_JSON` | For Android push | Firebase Cloud Messaging |

---

## Module setup

The feature tables above link to each module. This is what you find inside one — the same shape
every time, so knowing one module means knowing all of them:

```
modules/<name>/
├── README.md          # labels, architecture, boundaries, config-doc index
├── setup/
│   ├── manual.md      # step by step, by hand
│   └── automated.md   # what a script or Compose does — and what it does not
└── <config-dir>/
    └── README.md      # how that config works and why it is shaped that way
```

There is no separate guide series. A module's setup docs *are* its guide, which is why a feature
and its instructions cannot drift apart.

**Six modules have a genuinely automated path** — all containerised services:

```bash
make up                  # storage-data, backend-api, observability
make up-with-graphics    # + broadcast-graphics
make up-with-automation  # + automation-control
```

Desktop setup is partly automated: selected Python requirements can be installed in either app,
and the Windows bootstrap can install OBS/FFmpeg. Other tool/configuration steps and physical
acceptance remain manual where the module's `automated.md` says so. Supported repeatable steps
should move into shared in-app recipes under P-063.

Full index, labels, and setup order per product: **[`modules/README.md`](../modules/README.md)**.

---

## Documentation

**Start with the module.** Every feature's setup, configuration, dependencies, and status live in
`modules/<name>/`. These documents describe the platform *around* the modules.

| Document | Contents |
|----------|----------|
| **[Module index](../modules/README.md)** | Every module, its labels, and setup order per product — **start here** |
| **[Docs index](README.md)** | Everything else, grouped by what you are trying to do |
| **[Proposal queue](PROPOSALS.md)** | What work is authorized, and what state it is in |
| **[Module usage & complexity](agent/MODULE-MATRIX.md)** | What depends on a module, and what it costs to stand up |
| **[Setup technique notes](SETUP-TECHNIQUE-NOTES.md)** | Friction you will hit during setup — port collisions, GUI-only steps, colour-space traps |
| **[Image Intake](IMAGE_INTAKE.md)** | Feeding your own photographs in: buckets, provenance, rights + format matrices, tips |
| **[Roadmap](architecture/roadmap.md)** | The layer each module implements, and implementation philosophy |
| **[Future State](architecture/future-state.md)** | North-star, pillars, horizons, and candidate modules — the compass |
| **[Future work](architecture/future.md)** | Deferred items, each with the trigger that reopens it |
| **[Product Spec](architecture/product-spec.md)** | App architecture, pricing model, build order, guides-as-content |
| **[Marketing playbook](../MARKETING.md)** | Go-to-market plan for both products — ICPs, channels, content engine, 30-day plan; registered in the marketing crosswalk |
| **[Audit](AUDIT.md)** | The repository's own verdict on what is real vs. scaffolded |
| **[CLAUDE.md](../CLAUDE.md)** | Developer conventions, module→label map, module status |
| **[Deviations](architecture/deviations.md)** | Where reality diverged from the roadmap, and why |
| **[Guides](guides/README.md)** | Redirect map — the numbered guide series is retired |
| **[Setup Timeline](setup-timeline.html)** | Interactive visual timeline of the full platform |
