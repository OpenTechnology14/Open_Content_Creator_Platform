# Modules

Every module is self-contained and carries its own setup guides. There is no separate numbered
guide series — **guides live with the module they set up**:

```
modules/<name>/
├── README.md
└── setup/
    ├── manual.md      # step-by-step, by hand
    └── automated.md   # what a script/Compose does, and what it does not
```

The [module subfeature checklist](../docs/agent/SUBFEATURE-CHECKLIST.md) rolls up what is built,
what the automated workflow proves, and which live/manual acceptance steps remain. Proposal status
and priority stay in [`docs/PROPOSALS.md`](../docs/PROPOSALS.md).

## Labels

Each module is labelled by the product it belongs to. Labels group relevant modules; they do not require installing every module for that product.

- **`Content`** — Creator Extend / ContentExtend: ComfyUI, Blender, Krita, sports CV, image and
  video editing
- **`Stream`** — Stream Extend: OBS, AI effects, overlays, agents, audio, monitoring

Modules carrying both are shared foundations — set them up once for either product.

## Index

| Module | Labels | Automated setup | What it is |
|---|---|---|---|
| [creator-experience](creator-experience/) | `Content` `Stream` | ◐ Windows bootstrap + capture discovery | OBS, scenes, encoder config, multi-platform |
| [soundboard](soundboard/) | `Content` `Stream` | ✗ none | Named, hotkeyed DJ-style sound clips, OBS-native |
| [realtime-ai](realtime-ai/) | `Content` `Stream` | ✗ none | Face filters, background removal, ComfyUI stylization |
| [automation-control](automation-control/) | `Content` `Stream` | ✓ full | OBS WebSocket, n8n workflows |
| [storage-data](storage-data/) | `Content` `Stream` | ✓ full | Postgres, Redis, MinIO |
| [sports-analytics](sports-analytics/) | `Content` | ✗ deps only | Golf tracer, pose estimation, swing analysis |
| [content-creation](content-creation/) | `Content` | ◐ local Shorts CLI | Blender, DaVinci, render pipelines |
| [image-editing](image-editing/) | `Content` | ✗ none | Krita + AI Diffusion, inpainting, mobile edit |
| [nature-generation](nature-generation/) | `Content` | ✗ none | Corpus-learned landscape generation, sky replace, tone grading |
| [cityscape-generation](cityscape-generation/) | `Content` | ✗ none | Corpus-learned urban generation, facade repair, perspective + tone |
| [marketing-crosswalk](marketing-crosswalk/) | `Content` | ✓ it is a CLI | Marketing content generation for registered modules |
| [social-management](social-management/) | `Content` `Stream` | ◐ local picker + adapter CLI | Profiles, logos, OAuth accounts, publish/live approval |
| [backend-api](backend-api/) | `Stream` | ✓ full | FastAPI, WebSocket fanout, overlay APIs |
| [broadcast-graphics](broadcast-graphics/) | `Stream` | ✓ full | NodeCG lower-thirds, scoreboards, sponsors |
| [observability](observability/) | `Stream` | ✓ full | Prometheus, Grafana, Loki, source-health-exporter |
| [infrastructure](infrastructure/) | `Stream` | ✓ full | Compose topology, Tailscale, DigitalOcean, backups |
| [audio-production](audio-production/) | `Stream` | ◐ speech CLI + tool checks; manual routing | VoiceMeeter / BlackHole / PipeWire routing |
| [character-avatar](character-avatar/) | `Stream` | ✗ none | PNGTubers, VTube Studio, VRM |
| [ai-agents](ai-agents/) | `Stream` | ◐ partial | Local LLM persona, memory, moderation |
| [asset-pipeline](asset-pipeline/) | `Content` `Stream` | ✗ none — plain library | One storage contract for MinIO/S3 clients across modules |
| [model-registry](model-registry/) | `Content` `Stream` | ◐ CLI only | Model/adapter provenance — checksum, license, distributability |

## Setup order

**Open either app first, then choose capabilities.** The [desktop launch guide](infrastructure/setup/desktop-setup.md)
separates native bundles from the developer build path. Neither OBS nor Docker/WSL, Python,
models or cloud accounts gate the packaged shell. Both apps provide a Module setup panel.
The [à la carte CLI installer](infrastructure/setup/module-selection.md)
lists every module and installs selected Python dependencies. OBS is needed for actual broadcast
work, but a local host or Shorts test can run independently. The following orders describe full
workflows, not mandatory installation bundles.

**Stream Extend:** creator-experience (+ soundboard) → audio-production → storage-data →
backend-api → broadcast-graphics → ai-agents (+ character-avatar) → observability →
infrastructure → automation-control → social-management

**Creator Extend / ContentExtend:** creator-experience → storage-data → asset-pipeline →
model-registry → realtime-ai → content-creation → image-editing →
nature-generation / cityscape-generation → sports-analytics → automation-control → social-management

`asset-pipeline` has nothing to "set up" beyond `pip install -r requirements.txt` — it's placed
here because `realtime-ai` and `image-editing`'s MinIO-touching scripts import it, and it needs
`storage-data`'s MinIO actually running to be useful, not to exist first.

`model-registry` has the same nothing-to-set-up shape — placed right after `asset-pipeline` (whose
shared client it stores its registry file through) and before the weight-downloading modules, so
there's somewhere to record a real checksum the first time `realtime-ai` or a generation module
downloads something, instead of retrofitting it later.

The two generation modules sit after `realtime-ai` and `image-editing` because they drive the same
ComfyUI backend and reuse their models — except Tier 0 (tone, and for cityscape perspective),
which needs neither and can be set up standalone.

**Feeding either one images starts with [`docs/IMAGE_INTAKE.md`](../docs/IMAGE_INTAKE.md)** — the
shared intake guide: buckets, provenance, the rights and format matrices, and the rule for
deciding which of the two a photo belongs to.

`storage-data` comes early in workflows that consume Postgres, Redis or MinIO, and it is
automated (`make up`). Start it only when a selected workflow needs those services.

## Automated setup, honestly

The index above distinguishes container automation, local CLI installers and manual acceptance.
The desktop panel already installs selected Python dependencies, and the optional Windows
bootstrap installs OBS/FFmpeg. Other application, driver and model steps remain manual where
their module guides say so. Repeatable installation/configuration is a candidate for the shared
in-app runner in [P-063](../docs/PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup);
physical capture/audio checks and account/OS handoffs still need user participation.

```bash
make up                  # storage-data, backend-api, observability
make up-with-graphics    # + broadcast-graphics
make up-with-automation  # + automation-control
```

## When is a module done?

**When its section of [`../tests/ACCEPTANCE-CHECKLIST.md`](../tests/ACCEPTANCE-CHECKLIST.md)
passes.** That file is the single list of what must be true; each module's
`setup/manual.md` § Verification is where the human half of that lives.

Every module's setup ends the same way: run the automated checks, tick the manual ones, then run
that module's checklist section end to end.

**A failing line never blocks the next module.** It is a finding against the module it belongs to.
The full checklist is a **release gate** — the platform is done when every section passes, and the
11 currently-blocked lines mean that cannot happen until `P-016` and `P-001` close, however many
modules individually pass.

## Implementation status

Implementation varies by module. The current status tables are in `AGENTS.md` / `CLAUDE.md` §11;
[`docs/AUDIT.md`](../docs/AUDIT.md) records evidence and open limitations. Installing dependencies
never promotes a module to implemented or proves it works on either operating system.
