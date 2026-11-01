<p align="center">


  <img src="docs/assets/logo.svg" width="60" alt="Open Content Creator Platform logo" />
</p>

<h1 align="center">Open Content Creator Platform</h1>

**Public source preview:** [what is included and how privacy is preserved](PUBLIC_SOURCE.md).

<p align="center">
  A local-first toolkit that connects OBS, ComfyUI, Blender, Krita, AI agents and broadcast graphics.<br />
  Two desktop apps, <strong>Stream Extend</strong> for live streaming and <strong>Creator Extend</strong> for content creation,
  and the modules behind them.
</p>

<p align="center">
  <a href="#install-from-source">Install</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="docs/README.md">Docs</a> ·
  <a href="design-system/README.md">Design system</a> ·
  <a href="modules/marketing-crosswalk/crosswalk/modules.yml">Module registry</a> ·
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

---

> **Status: pre-release.** Read this before you build anything on it.
>
> - **4 of the 21 modules are implemented** (`storage-data`, `marketing-crosswalk`, `asset-pipeline`, `model-registry`).
>   The other 17 are scaffolded: a directory, a README, setup guides and minimum configuration. The table is in
>   [`CLAUDE.md`](CLAUDE.md) §11.
> - **Both desktop apps build and bundle**, but live acceptance (real OBS, real accounts, capture hardware, two-device
>   relay) is incomplete, and the platform is not certified on both macOS and Windows.
> - [`docs/AUDIT.md`](docs/AUDIT.md) is this repository's verdict on what is real. Trust it over any claim here.
> - Hosted cloud tiers and app-store listings are product plans, not shipped. See
>   [`docs/PRODUCT_OVERVIEW.md`](docs/PRODUCT_OVERVIEW.md).

## Why it exists

Most creators run a dozen free tools with no common control surface: OBS plugins, ComfyUI, Blender, Krita, a local LLM,
overlays. This project wraps them in one **local-first** workflow. Your camera, OBS and GPU stay on your machine; anything
that talks to a cloud is optional and never sits in the realtime video or audio path.

| | What it does |
|---|---|
| **Stream Extend** | OBS control and setup, overlays, AI-agent and voice hosts, audio monitoring, a recording handoff |
| **Creator Extend** | ComfyUI workflows, Blender production jobs, Krita editing, a local recording library |
| **Modules** | 21 independently runnable pieces, each with its own README and `setup/manual.md`, labelled **Content**, **Stream** or both |
| **Plugins** | OBS, Blender and Krita integrations in [`plugins/`](plugins/) |

Principles that decide most design questions: local first; modules are independent (a broken one must not break another);
stability before AI; configuration over code. They are written down in [`CLAUDE.md`](CLAUDE.md) §2.

## What is in this repository

| Path | Holds |
|---|---|
| [`apps/`](apps/) | The desktop apps (Tauri 2 and Svelte 5) and the Rust and Svelte code they share |
| [`modules/`](modules/README.md) | One folder per capability, with setup guides and the module index |
| [`plugins/`](plugins/) | OBS plugin (C), Blender add-on and Krita script (Python) |
| [`cloud/`](cloud/README.md) | An optional relay API (FastAPI) and its Docker Compose and Terraform files |
| [`mobile/`](mobile/) | Source for two relay stream bridges (iOS and Android); there is no packaged mobile app |
| [`design-system/`](design-system/README.md) | The design-system hub: tokens, components, voice registers, accessibility |
| [`docs/`](docs/README.md) | Roadmap, audit, proposals, guides and the beginner site |
| `scripts/`, `configs/`, `tests/` | Setup and maintenance scripts, local configuration, the offline test suite |

### The apps today

**Stream Extend and Creator Extend are two separate apps, not one.** Each has its own window, installer identity and
entry point, and they share a component library.

| App | Entry point | Notes |
|---|---|---|
| Stream Extend | [`apps/stream-extend/`](apps/stream-extend/) | OBS-centred |
| Creator Extend | [`apps/creator-extend/`](apps/creator-extend/) | ComfyUI, Blender and Krita-centred |
| Extend Preview | [`apps/extend/`](apps/extend/README.md) | A private preview of the one-app direction ([P-072](docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md)): a Stream or Create workspace choice, one shared setup, one recording library. It does not replace either app yet |
| Shared | [`apps/shared/`](apps/shared/) | Setup panel, profile switcher, recording library, settings and relay client |

## Install from source

You need Node.js 22 and npm, stable Rust, and Python 3.11 or newer. Docker is needed only for the optional service stack,
and OBS Studio only for streaming. On Windows, also install the Visual Studio C++ build tools and WebView2; see the
[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).

```bash
git clone <repository-url> open-content-creator-platform
cd open-content-creator-platform
make test                               # the offline test suite; needs no service
cd apps/stream-extend && npm ci         # or apps/creator-extend
npm run tauri dev                       # opens the native app without packaging
```

`npm run tauri build -- --debug` produces a bundle under `src-tauri/target/debug/bundle/`. The full walk-through,
including the Windows installer path, is [`modules/infrastructure/setup/desktop-setup.md`](modules/infrastructure/setup/desktop-setup.md).

## Quickstart

1. **Open an app and reach Module setup.** Choose the capabilities you want. OBS, Docker, Python, models and cloud accounts
   are checked only when a feature needs them, not before the app opens.
2. **Select modules.** The [à la carte guide](modules/infrastructure/setup/module-selection.md) explains the Module setup
   panel and the lower-level `scripts/setup/modules.py` catalog.
3. **Start the optional services** if a module needs storage or observability:

   ```bash
   cp .env.example .env     # then set the secrets it lists; never commit .env
   make up                  # Postgres, Redis, MinIO, the FastAPI backend, Prometheus, Loki, Grafana
   make healthcheck
   ```

4. **Follow the module's `setup/manual.md`.** [`modules/README.md`](modules/README.md) lists every module, its labels and the
   order to set them up in. Installing an app does not install every module, external tool or model.

## Documentation

| Start here | For |
|---|---|
| [Beginner site](docs/public/index.html) | A private practice recording, common problems, clipping |
| [`docs/README.md`](docs/README.md) | The index of every document |
| [`modules/README.md`](modules/README.md) | Modules, labels, setup order |
| [`docs/architecture/roadmap.md`](docs/architecture/roadmap.md) | The layers every module maps onto |
| [`docs/PROPOSALS.md`](docs/PROPOSALS.md) | The work queue and what is authorized |
| [`docs/THIRD_PARTY_PROVENANCE.md`](docs/THIRD_PARTY_PROVENANCE.md) | Every third-party component, with its license and flags |

## Design system and module registry

- **Design-system hub.** [`design-system/`](design-system/README.md) holds the platform's design tokens
  ([`tokens.yaml`](design-system/tokens.yaml)), component rules, voice registers and accessibility baseline. Other repositories
  mirror it through pointer documents ([`consumers.md`](design-system/crosswalk/consumers.md)). Its content is drafted and
  awaiting owner review.
- **Module registry.** [`modules/marketing-crosswalk/crosswalk/modules.yml`](modules/marketing-crosswalk/crosswalk/modules.yml)
  is the single registry of which products and modules exist, how to find them and what may be claimed about them; the
  [module README](modules/marketing-crosswalk/README.md) explains the schema and the generator, and
  [`MARKETING.md`](MARKETING.md) is the playbook built on it.

## Contributing

Contributions are welcome. **The module is the unit of contribution:** a new capability is a new or extended module, with a
README, `setup/manual.md`, `setup/automated.md` and a config document beside any configuration it adds. Read
[`CONTRIBUTING.md`](CONTRIBUTING.md) first; it covers the workflow, the checks to run and the pull-request description. By
taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). Report a vulnerability as [`SECURITY.md`](SECURITY.md)
describes, not in a public issue.

## License

The code in this repository is released under the [MIT License](LICENSE). The plugins in [`plugins/`](plugins/) carry
[their own license file](plugins/LICENSE). MIT covers this project's own code only: optional integrations depend on
software under other terms, some of it copyleft or non-commercial, and those terms apply to you when you install it. They
are listed in [`docs/THIRD_PARTY_PROVENANCE.md`](docs/THIRD_PARTY_PROVENANCE.md), and required notices are in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
