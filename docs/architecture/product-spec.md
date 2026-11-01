# Product Spec — Stream Extend + Creator Extend

Two current desktop products built from one modular hybrid-creator-platform codebase, with thin
native plugins as free funnels. The shared platform must also support a future unified desktop
shell and one companion mobile app without duplicating module implementations.

---

## Products

| Product | Path | Setup order | Current distribution target |
|---------|------|--------------|-----------|
| **Stream Extend** | Streaming | Open app → choose capabilities; see [`modules/README.md`](../../modules/README.md) § Setup order | macOS, Windows, direct desktop download |
| **Creator Extend** | Content creation | Open app → choose capabilities; see [`modules/README.md`](../../modules/README.md) § Setup order | macOS, Windows, direct desktop download |

*(The numbered guide series this table used to cite — "1→2→6→7→8→9" — was retired
`P-006`/`P-029`, 2026-08-30/31; every module carries its own `setup/manual.md` now. Pointing at
`modules/README.md` instead of hardcoding the order here avoids a second copy that can drift the
same way this one did — caught by an exhaustive `docs/` sweep, `P-048`, 2026-09-02, not by the
guide-reference regression test, which only scans `modules/` and the literal phrase `Guide N`.)*

Each current product is a separate Tauri 2 desktop app with its own feature set. This is a delivery
choice for the current acceptance stage, not a permanent module boundary. Shared crates and module
contracts must remain usable by either app and by a possible combined shell.

The owner requested a **single desktop app with Stream/Create workspaces** on 2026-10-04 to
simplify distribution. [P-072](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md) records
that direction, migration/distribution risks and a staged optional cloud companion. Planning is
accepted now; consolidation implementation remains gated by the acceptance conditions in
[`roadmap.md`](roadmap.md#future-convergence-path). Naming, bundle identity, store listings,
purchases and pricing remain release decisions. Cloud expansion is candidate scope, not shipped
functionality or an approved change to the commercial assumptions below.

---

## Architecture

### First launch and assisted setup

Optimize for the shortest path to a usable native setup window in either product. A packaged
app should require only its OS runtime, with no developer toolchain, Python, OBS, Docker/WSL,
models or cloud sign-in before opening. Keep Module setup, bundled guides, saved selections
and the Dashboard accessible while optional capabilities are unavailable.

The shared P-003 panel already handles selective Python dependency installs and readiness.
[P-063](../PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup) plans native installable
delivery and additional in-app recipes for prerequisites and supported configuration. Reuse one
local runner and config-owned recipes across both apps and the CLI. Show affected changes,
progress and actionable failures; retain results for retry, skip and restart/reboot recovery.
Standard installs and checks should not require an AI session to execute or monitor them.
Keep credentials, OS prompts and physical audio/video checks in explicit user handoffs.

OBS/Docker errors must name the affected capability and allow unrelated setup to continue.
Measure time and user actions to first usable window separately from first verified broadcast
or content output. A source build or Windows CI rehearsal does not prove clean-machine app
installation. Current paths and limits are in the
[desktop setup guide](../../modules/infrastructure/setup/desktop-setup.md).

### Desktop Apps (Tauri 2)

```
Tauri 2 (Rust + WebView)
├── Frontend: SvelteKit / React (your choice)
├── Backend: Rust sidecar
│   ├── OBS WebSocket client (Stream Extend)
│   ├── ComfyUI API client (both)
│   ├── MinIO/S3 client (both)
│   ├── Blender subprocess launcher (Creator Extend)
│   ├── Local config/state management
│   ├── Shared social profile/account contract (both)
│   └── Shared local recording inbox (Stream writes, Creator manages)
└── System tray icon + menu bar
```

Distribution: Mac App Store, Microsoft Store (MSIX), direct download (DMG/EXE).

### Future mobile companion (Tauri 2 + native)

One companion app is the preferred future direction. It connects to Stream Extend, Creator
Extend, or a later unified desktop shell through the same device, readiness, relay, and approval
contracts. It does not execute workstation-bound OBS, GPU, gameplay, ComfyUI, Blender, Krita, or
DaVinci workloads.

```
Tauri 2 (mobile)
├── Shared setup/readiness and remote-control UI
├── Local-network or DigitalOcean relay connection
├── Approval, monitoring, notifications, social profiles, and content review/upload
└── Optional phone-camera contribution after the control path is accepted
```

Candidate distribution: iOS App Store and Google Play. No mobile implementation or store release
is currently claimed.

### Free Funnel Plugins

| Plugin | Platform | Language | Purpose |
|--------|----------|----------|---------|
| OBS Plugin | OBS Studio | C | Auto-setup: import scenes, create Browser Sources, configure encoder. Opens Stream Extend app for management. |
| Blender Addon | Blender | Python | Templates, MinIO upload, ComfyUI workflow triggers. Opens Creator Extend app for AI editing. |

Plugins are free, open-source (MIT), distributed through OBS/Blender plugin
registries. They pull users into the paid Tauri app for advanced features.

---

## Pricing

### Current one-time desktop purchase assumption
- **$20** per desktop app (Stream Extend or Creator Extend)
- Mac App Store, Microsoft Store, and direct desktop download
- Includes all local features — no subscription required for local-only use
- Unified-shell capability packs and mobile pricing are deferred to the convergence review

### Codebase License
- **$100** on Gumroad
- Full source code with BSL license (→ Apache 2.0 after 2 years)
- For developers who want to self-host, modify, or learn

### Subscription (cloud features only)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | All local features, local WiFi sync |
| **Connect** | $5/mo | Remote access via DO relay, push notifications |
| **Pro** | $12/mo | Full remote control, metric persistence in cloud, multi-device sync |
| **Team** | $25/mo | Multi-user access, shared dashboards, team permissions |

### What requires cloud (subscription)

Only these 5 features need a DigitalOcean connection:
1. **Remote access** — control your setup from outside your local network
2. **Push notifications** — stream alerts, job completion, error alerts to phone
3. **Metric persistence** — Grafana dashboards accessible from any device
4. **Multi-device sync** — settings, presets, workflows synced across devices
5. **Multi-user access** — multiple team members accessing the same platform

Everything else works 100% locally with no subscription.

---

## DigitalOcean Multi-Tenant Architecture

One DO project serves all paying subscribers:

```
DigitalOcean ($32/mo base)
├── Droplet ($12/mo) — FastAPI relay + Tailscale gateway
├── Managed Postgres ($15/mo) — multi-tenant, row-level security
└── Spaces ($5/mo) — per-tenant asset storage with prefix isolation
```

### Data isolation
- Postgres: `tenant_id` column on every table, row-level security policies
- Spaces: prefix-based isolation (`s3://hcp-assets/{tenant_id}/...`)
- API: JWT with tenant_id claim, middleware enforces isolation

### Scaling
- Droplet: vertical first (upgrade to larger droplet)
- Postgres: connection pooling (PgBouncer), read replicas when needed
- Spaces: unlimited storage, per-tenant quotas in app logic

---

## License

### Source Code
**Owner direction, 2026-10-05: prepare an open-source release.** The earlier BSL-to-Apache
plan is superseded as a release direction; no root license exists yet. The maintainer still
needs to select the license, copyright holder and release scope under P-002/P-001.
JobHunter's public MIT repository is a reference, not automatic authorization to copy its
license or copyright notice. See [the reference review](../PUBLIC_DOCS_AND_MARKETING_REVIEW.md).

### Plugins
Intended **MIT**; verify each component's actual notice and third-party obligations before release.

### Compiled Apps
Distribution terms remain to be reconciled with the selected source license and release channel.

---

## Repository Structure (future)

```
hybrid-creator-platform/          ← This repo (platform core)
├── apps/
│   ├── stream-extend/            ← Tauri app — Stream Extend
│   │   ├── src-tauri/            ← Rust backend
│   │   ├── src/                  ← Web frontend
│   │   └── tauri.conf.json
│   ├── creator-extend/           ← Tauri app — Creator Extend
│   │   ├── src-tauri/
│   │   ├── src/
│   │   └── tauri.conf.json
│   ├── shared/                   ← Shared UI, setup, settings, readiness, relay, API contracts
│   └── unified-extend/           ← Future candidate only; created after convergence approval
├── mobile/
│   └── companion/                ← Future candidate; one control/review app for either shell
├── plugins/
│   ├── obs-plugin/               ← C OBS plugin
│   │   ├── src/
│   │   └── CMakeLists.txt
│   └── blender-addon/            ← Python Blender addon
│       ├── __init__.py
│       └── operators/
├── cloud/
│   ├── relay-api/                ← DO relay FastAPI (multi-tenant)
│   ├── migrations/               ← Multi-tenant Postgres migrations
│   └── terraform/                ← DO infrastructure as code
└── modules/                      ← Existing platform modules (unchanged)
```

---

## Marketing: Guides as Content

Each module's setup documentation (`modules/<name>/setup/`) doubles as marketing content and
website copy. Every module's pair of setup docs supports:

- A contextual CTA blockquote for the relevant product (Stream Extend or Creator Extend)
- Links to the free plugin (OBS Plugin or Blender Addon) as an entry point
- Pricing and platform availability
- The tone: "everything works without the app — the app just makes it faster"

When converting a module's setup docs to a website page — `modules/marketing-crosswalk` generates
this brief automatically via `generate --module stream-extend --asset guide-page`:
- The CTA blockquotes become styled banner components
- `setup/manual.md` steps become "what the app automates for you" selling points
- Validation checklists become "what you'll have when you're done" feature lists
- `setup/automated.md` becomes the honest "already one command" section — and is the guard
  against promoting a *specified* app feature to a shipped one
- The setup-timeline.html is already a standalone interactive page with CTA banners

### URL structure (future website)

| URL | Content source |
|-----|---------------|
| `streamextend.com/guides/obs-setup` | `modules/creator-experience/setup/` |
| `streamextend.com/guides/ai-effects` | `modules/realtime-ai/setup/` |
| `streamextend.com/guides/audio` | `modules/audio-production/setup/` |
| `streamextend.com/guides/overlays` | `modules/broadcast-graphics/setup/` |
| `streamextend.com/guides/ai-agents` | `modules/ai-agents/setup/` |
| `streamextend.com/guides/operations` | `modules/observability/setup/` + `modules/infrastructure/setup/` |
| `creatorextend.com/guides/sports-cv` | `modules/sports-analytics/setup/` |
| `creatorextend.com/guides/comfyui` | `modules/realtime-ai/setup/` + `modules/content-creation/setup/` |
| `creatorextend.com/guides/image-editing` | `modules/image-editing/setup/` |
| `creatorextend.com/guides/landscapes` | `modules/nature-generation/setup/` |
| `creatorextend.com/guides/cityscapes` | `modules/cityscape-generation/setup/` |
| `creatorextend.com/guides/image-intake` | `docs/IMAGE_INTAKE.md` |
| `creatorextend.com/guides/realtime` | `modules/realtime-ai/setup/` |
| Both sites `/setup` | setup-timeline.html |

**No planned page.** Stream: `automation-control`, `backend-api`, `storage-data`,
`character-avatar`, `soundboard`, `social-management`, `asset-pipeline`, `model-registry`.
Content: `automation-control`, `storage-data`, `soundboard`, `social-management`,
`asset-pipeline`, `model-registry`, and `creator-experience` — whose page exists only on the
Stream site, so a Creator Extend reader is sent to the wrong domain.

Tracked as coverage gaps by `modules/marketing-crosswalk`:

```bash
python3 -m generator.cli coverage --module stream-extend
python3 -m generator.cli coverage --module content-extend
```

---

## Build Order

1. **Shared API client** — TypeScript/Rust library for OBS WebSocket, ComfyUI API, MinIO
2. **Stream Extend desktop** — Tauri app, connects to existing OBS + services
3. **Creator Extend desktop** — Tauri app, connects to ComfyUI + Blender
4. **OBS plugin** — C plugin, minimal: scene import + Browser Source creation
5. **Blender addon** — Python addon, minimal: template gallery + MinIO upload
6. **Cloud relay acceptance** — prove hosted device discovery, approval, and two-device control
7. **Convergence review** — apply the roadmap gates; decide separate shells versus one capability-pack shell
8. **Unified mobile companion** — shared readiness, remote approval, monitoring, notifications, and content review
9. **Subscriptions** — Stripe integration, tenant provisioning, feature gating
