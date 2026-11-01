<!-- Generated from CLAUDE.md by scripts/testing/generate_docs.py; edit the source, then regenerate. -->
# AGENTS.md — Open Content Creator Platform

This file gives Codex (and any other AI coding assistant) the project context, conventions, and guardrails needed to work productively in this repository.

Read this **first** before generating or modifying any code in this repo.

---

## 1. Project Identity

**Name:** Open Content Creator Platform
**Type:** Modular, AI-native creator / streaming / sports-CV platform
**Philosophy:** Local-first. Cloud-augmented. Stability before AI.

The platform combines:

- Live streaming and broadcast production (OBS)
- Realtime AI effects (face swap, segmentation, stylization)
- Sports computer vision (golf shot tracer, pose estimation, swing analysis)
- AI-powered avatars and agents
- Broadcast graphics and overlays
- Automation, orchestration, and observability
- Content creation pipelines (Blender, ComfyUI, DaVinci)
- AI image + video editing (Krita, inpainting, mobile tap-to-edit)

The roadmap canonical source is `docs/architecture/roadmap.md`. All module boundaries map 1:1 to the layers in that roadmap.

---

## 2. Implementation Philosophy (non-negotiable)

When generating or modifying code in this repo, follow these principles:

1. **Local-first.** Default to running on the creator's workstation. Cloud services are *opt-in* for scaling, dashboards, backups, and burst compute — never required for the core path.
2. **Latency-sensitive code stays on the local GPU.** OBS, webcam capture, realtime AI inference, and overlay rendering must not depend on a network round-trip to function.
3. **Stability before complexity.** Do not introduce Kubernetes, distributed workers, or service meshes into a module that doesn't yet have a working single-node implementation.
4. **Modules are independent.** Each module under `modules/` must be runnable in isolation. A broken `sports-analytics` module must not break `creator-experience`.
5. **Configuration over code.** Per-environment differences (local vs DigitalOcean) live in `configs/`, not in branching logic inside modules.
6. **Roadmap is the source of truth.** If a request contradicts the roadmap's layering or ordering, surface the conflict before implementing.

---

## 3. Repository Layout

```
hybrid-creator-platform/
├── AGENTS.md                        # This file
├── README.md                        # Human-facing project overview
├── docker-compose.yml               # Local infra orchestration (MinIO, Postgres, Redis, etc.)
├── docker-compose.digitalocean.yml  # Cloud overlay for DO deployments
├── .env.example                     # Required environment variables
│
├── docs/
│   ├── architecture/
│   │   └── roadmap.md               # Master roadmap (canonical)
│   └── guides/                      # Retired numbered-guide series; redirect map to module setup docs
│
├── design-system/                   # Ecosystem design-system hub (drafted, awaiting owner review); other repos keep pointer docs
│   ├── tokens.yaml                  # Machine-readable tokens + every consumer's observed value
│   ├── crosswalk/consumers.md       # Downstream repos and the pointer doc each keeps
│   └── proposals/TEMPLATE.md        # Design-artifact template (mockup, data flow, decision gates)
│
├── apps/                            # Two existing Tauri apps plus the private P-072 shell preview
│   ├── stream-extend/               # Stream Extend: OBS control and relay contracts (builds+bundles; external acceptance open)
│   ├── creator-extend/              # Creator Extend: ComfyUI/Blender/Krita orchestration (builds+bundles; batch jobs still pending)
│   ├── extend/                      # Private shared-shell preview; native acceptance/parity/migration remain gated
│   └── shared/
│       ├── relay-client/            # Real: Rust crate, hosted+self-hosted relay client (~800 lines)
│       ├── local-settings/          # Atomic endpoints + OS credential-manager secrets
│       ├── recording-library/       # Shared locked local Stream → Creator recording inbox
│       ├── setup-wizard/            # Shared local Tauri module setup plugin
│       ├── social-manager/          # Shared native social catalog/OAuth-service bridge
│       ├── ui/                      # Shared Svelte module selection/readiness panel
│       └── api-client/              # Empty — no files yet
│
├── modules/                         # One folder per roadmap layer; each carries setup/manual.md + setup/automated.md
│   ├── creator-experience/          # OBS, scenes, overlays
│   ├── soundboard/                  # DJ-style sound bar — named, hotkeyed clips (OBS plugin)
│   ├── realtime-ai/                 # DeepFaceLive, segmentation, ComfyUI
│   ├── sports-analytics/            # Golf tracer, pose, YOLO
│   ├── character-avatar/            # PNGTubers, VTube Studio
│   ├── automation-control/          # n8n, OBS WebSocket, scene switcher
│   ├── backend-api/                 # FastAPI, WebSocket services
│   ├── storage-data/                # MinIO, Postgres, Redis
│   ├── observability/               # Prometheus, Grafana, Loki
│   ├── infrastructure/              # Docker, Tailscale, DO, K8s (later)
│   ├── audio-production/            # VoiceMeeter, VB-Cable, VST chains
│   ├── broadcast-graphics/          # NodeCG, lower thirds, scoreboards
│   ├── ai-agents/                   # AITuberKit, local LLM, memory
│   ├── content-creation/            # Blender, DaVinci, render pipelines
│   ├── image-editing/              # Krita + AI Diffusion, inpainting, mobile editing
│   ├── nature-generation/          # Corpus-learned landscape generation + tone grading
│   ├── cityscape-generation/       # Corpus-learned urban generation + perspective + tone
│   ├── marketing-crosswalk/        # Generates marketing content for registered consumer modules
│   ├── social-management/          # Profiles, brands, account connections, publishing/live gates
│   ├── asset-pipeline/             # One storage contract for MinIO/S3 clients across modules
│   └── model-registry/             # Model/adapter provenance — checksum, license, distributability
│
├── scripts/
│   ├── setup/                       # First-time install scripts
│   ├── deploy/                      # Local + DO deployment scripts
│   └── maintenance/                 # Backups, cleanups, health checks
│
├── configs/
│   ├── local/                       # Workstation configuration
│   └── digitalocean/                # DO droplet / managed service configs
│
├── plugins/                         # Third-party-app plugins, outside the modules/ layer
│   ├── blender-addon/               # Creator Extend Blender addon — see content-creation/setup
│   ├── obs-plugin/                  # C, OBS Studio — scene import, encoder config (~450 lines)
│   └── krita-integration/           # Python, Krita — menu items + docker panels (~260 lines)
│
└── tests/                           # Cross-module integration tests
```

---

## 4. Modules, Labels, and Setup

Guides are **not** a separate series. Each module carries its own setup guides:

```
modules/<name>/setup/manual.md      # by hand
modules/<name>/setup/automated.md   # what a script/Compose does — and what it does not
```

Every module is labelled by the product it belongs to. `Content` = Creator Extend /
ContentExtend. `Stream` = Stream Extend. Both = a shared foundation, set up once for either.

| Module folder | Labels | Automated setup |
|---|---|---|
| `modules/creator-experience` | `Content` `Stream` | partial — Windows prerequisite bootstrap + cross-platform capture discovery; OBS scene/device acceptance remains manual |
| `modules/soundboard` | `Content` `Stream` | none — OBS plugin, GUI install and dock config |
| `modules/realtime-ai` | `Content` `Stream` | none — local GPU by design |
| `modules/automation-control` | `Content` `Stream` | full — `make up-with-automation` |
| `modules/storage-data` | `Content` `Stream` | full — `make up`, `make migrate` |
| `modules/sports-analytics` | `Content` | deps only — `pip install -r requirements.txt` |
| `modules/content-creation` | `Content` | partial — local Shorts CLI; desktop DCC setup manual |
| `modules/image-editing` | `Content` | none — Krita is a desktop app |
| `modules/nature-generation` | `Content` | partial — Tier 0 grading CLI; learned tiers not built |
| `modules/cityscape-generation` | `Content` | partial — Tier 0 grading CLI; learned tiers not built |
| `modules/marketing-crosswalk` | `Content` | full — it is a CLI |
| `modules/social-management` | `Content` `Stream` | partial — local picker/OAuth/adapters; account registration manual |
| `modules/asset-pipeline` | `Content` `Stream` | none — plain importable library, nothing to run |
| `modules/model-registry` | `Content` `Stream` | CLI only — `validate`/`checksum`/`verify`/`status` |
| `modules/backend-api` | `Stream` | full — `make up` |
| `modules/broadcast-graphics` | `Stream` | full — `make up-with-graphics` |
| `modules/observability` | `Stream` | full — `make up` |
| `modules/infrastructure` | `Stream` | full — `make deploy-do`, `make backup` |
| `modules/audio-production` | `Stream` | partial — native speech export, dependencies and in-app routing-tool checks; OS routing remains manual |
| `modules/character-avatar` | `Stream` | none — VTube Studio is a desktop app |
| `modules/ai-agents` | `Stream` | partial — datastore yes, Ollama no |

Index and setup order: [`modules/README.md`](modules/README.md). The numbered guides are retired
and fully migrated — [`docs/guides/README.md`](docs/guides/README.md) is a redirect map from each
old guide to the module setup docs and config docs that absorbed it. There is no archive.

**When adding a module:** it needs a row in `docs/PROPOSALS.md` first — module work is proposal
work. Then create `setup/manual.md` and `setup/automated.md`, assign labels, and add a row here,
in `modules/README.md`, and in both matrices under `docs/agent/`. If nothing about it is automated, `automated.md` must
say so plainly — never imply a script exists.

## 5. Tech Stack Conventions

### Languages
- **Python 3.11+** for AI/CV pipelines, backend services, automation
- **TypeScript/Node** for NodeCG overlays, broadcast graphics, automation scripts
- **Bash** for setup scripts (POSIX-compatible; tested on Ubuntu 22.04 and macOS)
- **Lua** for OBS scene scripting where unavoidable

### Frameworks
- **FastAPI** for all internal HTTP/WebSocket APIs (`modules/backend-api`)
- **OpenCV + MediaPipe + Ultralytics YOLO** for CV (`modules/sports-analytics`)
- **ComfyUI** for image/video generation (`modules/realtime-ai/comfyui`)
- **n8n** for workflow automation (`modules/automation-control/n8n`)

### Data
- **PostgreSQL** for relational state (creator profiles, session metadata)
- **Redis** for ephemeral pub/sub, WebSocket fanout, rate limiting
- **MinIO** (S3-compatible) for assets, models, recordings, AI outputs

### Observability
- **Prometheus** for metrics scraping
- **Loki** for log aggregation
- **Grafana** for dashboards (single pane of glass)

### Infrastructure
- **Docker + Docker Compose** for everything that isn't a desktop app
- **Tailscale** for hybrid local ↔ cloud networking (do not expose services publicly without it or an auth proxy)
- **DigitalOcean** Droplets, Managed Databases, Spaces (S3) for cloud
- **Kubernetes** is explicitly *out of scope* until the `infrastructure` module is complete and all four conditions in `docs/architecture/k8s-decision.md` hold. Do not introduce it earlier.

---

## 6. Coding Standards

### Python
- Use `ruff` for linting/formatting (config in `pyproject.toml` at repo root once added)
- Type hints on all public functions
- Async by default in backend services (FastAPI is ASGI)
- Use `pydantic` v2 models for all API request/response bodies
- Use `loguru` over the stdlib `logging` module for application logs
- No prints in production code paths

### TypeScript / Node
- ESM modules only (`"type": "module"` in `package.json`)
- Prettier defaults; no opinions on top of that
- NodeCG bundles follow NodeCG's standard layout

### Bash
- `set -euo pipefail` at the top of every script
- Quote all variable expansions
- Provide a `--help` flag on any script meant to be run by a human

### Git
- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
- Reference the module in the scope: `feat(sports-analytics): add club detector`
- No secrets in commits; `.env` is gitignored, `.env.example` is committed

---

## 7. Environment & Secrets

- **Never commit `.env`.** Only `.env.example` with placeholder values.
- All modules read configuration from environment variables, loaded via `python-dotenv` or Node's built-in `process.env`.
- Local secrets live in `.env` at repo root.
- Cloud secrets (DigitalOcean) are managed via the DO console or a sealed-secrets equivalent — never checked in.
- Tailscale auth keys are ephemeral; regenerate per-node.

Required env vars are documented in `.env.example`. If you add a new one, update `.env.example` in the same commit.

---

## 8. Local vs DigitalOcean

The same `docker-compose.yml` runs locally. For DigitalOcean, layer the cloud overlay:

```bash
# Local
docker compose up -d

# DigitalOcean droplet (additive overrides)
docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml up -d
```

What runs **only locally** (low latency required):
- OBS Studio (desktop app)
- DeepFaceLive / Deep-Live-Cam (GPU realtime)
- Golf tracer / pose estimation (camera input)
- ComfyUI realtime mode

What can run **locally OR on DigitalOcean**:
- FastAPI backend
- MinIO (or DO Spaces in cloud)
- Postgres (or DO Managed Postgres in cloud)
- Redis
- Prometheus / Grafana / Loki
- n8n
- ComfyUI batch / burst rendering

Tailscale connects the two halves. The creator's workstation joins the tailnet; DO droplets join the same tailnet; services discover each other by tailnet hostname.

---

## 9. Working With Codex in This Repo

**Owner workspace preference:** On the MacBook, use its built-in display for UI work and
native app acceptance. Move test windows to the built-in display before interacting.

When asked to add a feature:

1. Identify which **roadmap layer** the feature belongs to and place code in the corresponding `modules/<layer>` folder.
2. Check that module's `setup/manual.md` and `README.md` for the intended scope of the layer. If the feature exceeds it, flag it.
3. Prefer adding configuration to `configs/` over hardcoding values.
4. Add a `README.md` to any new module subfolder explaining what it does, how to run it locally, and how it differs in DigitalOcean (if at all). A new **module** also needs `setup/manual.md` and `setup/automated.md`, plus labels (`Content` / `Stream` / both) in §4 and `modules/README.md`.
5. Update `docker-compose.yml` if the feature requires a new service.
6. Update `.env.example` if the feature requires new environment variables.

**Choose the best model before proposal work.** Every `docs/PROPOSALS.md` item must name its
agent model, reasoning effort and scope-based rationale. Follow the
[model selection policy](docs/PROPOSALS.md#agent-model-selection), keep the detailed proposal's
assignment consistent, check availability and select that model/effort in the execution client.
Reassess when scope changes and record any replacement. Child tasks inherit the parent assignment
unless an explicit override is recorded. These are development-agent choices; runtime AI models
remain in module configs. A model assignment does not authorize Pending or Deferred work.
Default to `gpt-6.1-sol` for coding; reserve Astra for explicitly justified demanding integration
or escalation. Sensitive paths require their full verification bar with either model.

**Put the question beside every owner decision.** A decision row, gate or open question you add or change keeps its full
explanation and ends it with `**Question:** <one short sentence>` — plain English, answerable yes or no where it can be, and
no identifiers (`docs/todo/README.md` row format; `tests/docs/test_decision_questions.py` enforces it).

**Verify locally after implementing — always.** Look up what proves the change in
the matrix. `make verify` runs recognized local CI gates and lists every NOT RUN check;
inspect with `make verify ARGS=--list`. `make proposal-report ARGS='--check --summary'`
checks unfinished proposal IDs against the lane map. Neither replaces required offline
or live acceptance evidence.

Look up what proves the change in
`docs/agent/VERIFICATION-MATRIX.md`, run it, and record what it returned. "Tested" is not a
verification. `make test` is the required offline suite. A `docs/PROPOSALS.md` row does not
reach `Done` without recorded verification. After changing this file, run
`python3 scripts/testing/generate_docs.py --write` and inspect the generated AGENTS.md;
`--check` is enforced by the offline suite and CI. Preserve the generated registry alongside
any canonical queue/matrix/status change.

When asked to fix a bug:

1. Reproduce locally before changing code.
2. Add a test under `tests/` that fails before the fix and passes after — prove it by reverting
   the fix and watching it fail.
3. Keep the fix scoped to the affected module unless the bug is genuinely cross-cutting.

When asked to do something that contradicts the roadmap's ordering (e.g., "set up Kubernetes" before the `infrastructure` module is complete):

- Surface the conflict.
- Ask whether to proceed anyway or defer.
- If proceeding, document the deviation in `docs/architecture/deviations.md`.

---

## 10. What NOT To Do

- Do **not** add Kubernetes, service mesh, or distributed workers before the `infrastructure` module is complete. See `docs/architecture/k8s-decision.md` for the four conditions.
- Do **not** expose any service to the public internet without an auth layer.
- Do **not** route realtime webcam / OBS traffic through the cloud.
- Do **not** commit model weights, recordings, or any binary >5 MB. Use MinIO / DO Spaces.
- Do **not** mix module boundaries — `sports-analytics` should not import from `realtime-ai` directly; if they need to share data, it goes through `backend-api`.
- Do **not** rely on `localhost` hardcoded in module code; use service hostnames from compose or env vars.

---

## 11. Module Status (update as work progresses)

| Module | Labels | Status |
|---|---|---|
| creator-experience | `Content` `Stream` | scaffolded |
| soundboard | `Content` `Stream` | scaffolded |
| realtime-ai | `Content` `Stream` | scaffolded |
| automation-control | `Content` `Stream` | scaffolded |
| storage-data | `Content` `Stream` | implemented |
| sports-analytics | `Content` | scaffolded |
| content-creation | `Content` | scaffolded |
| image-editing | `Content` | scaffolded |
| nature-generation | `Content` | scaffolded |
| cityscape-generation | `Content` | scaffolded |
| marketing-crosswalk | `Content` | implemented |
| social-management | `Content` `Stream` | scaffolded |
| backend-api | `Stream` | scaffolded |
| broadcast-graphics | `Stream` | scaffolded |
| observability | `Stream` | scaffolded |
| infrastructure | `Stream` | scaffolded |
| audio-production | `Stream` | scaffolded |
| character-avatar | `Stream` | scaffolded |
| ai-agents | `Stream` | scaffolded |
| asset-pipeline | `Content` `Stream` | implemented |
| model-registry | `Content` `Stream` | implemented |

"Scaffolded" = directory exists, README + setup guides + minimum config present, ready for
implementation.
"Implemented" = working, tested, documented.
"Production" = deployed locally AND on DigitalOcean, monitored.

`docs/AUDIT.md` is the repository's own verdict on what is real. Nothing may be promoted here
without evidence — a passing offline suite (`make test`) is necessary but not sufficient;
promotion to `implemented` needs the live evidence `docs/AUDIT.md` and each proposal row record.

## 12. Quick Reference

- Roadmap: `docs/architecture/roadmap.md`
- Proposal queue (what is authorized): `docs/PROPOSALS.md`
- Proposal dashboard and Testing workflow: `docs/PROPOSAL_DASHBOARD.md`; browsable snapshot `docs/proposal-dashboard.html` (queue state remains authoritative)
- Owner decisions and runs waiting on a person (by lane): `docs/todo/README.md`
- Module usage/complexity: `docs/agent/MODULE-MATRIX.md`
- Module inventory: `docs/agent/MODULE-ITEM-MATRIX.md`
- Which docs go stale when you change X: `docs/agent/DOC-UPDATE-MATRIX.md`
- What proves a change works: `docs/agent/VERIFICATION-MATRIX.md`
- Marketing playbook (a registered crosswalk artifact): `MARKETING.md`; module registry: `modules/marketing-crosswalk/crosswalk/modules.yml`
- Design-system hub (drafted, awaiting owner review): `design-system/README.md`; tokens `design-system/tokens.yaml`
- Setup friction: `docs/SETUP-TECHNIQUE-NOTES.md`
- Future state (compass): `docs/architecture/future-state.md`
- Parking lot: `docs/architecture/future.md`
- Module index + setup order: `modules/README.md`
- Archived guides: `docs/guides/README.md`
- Local up: `docker compose up -d`
- DO up: `docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml up -d`
- Health check: `scripts/maintenance/healthcheck.sh`
- Backups: `scripts/maintenance/backup.sh`

---

## 13. Two-phase routing: HF/OpenCode drafts, Claude reviews

**This is an option, not a mandate.** Nothing in this repo requires it. Use it where the economics
are obviously right and skip it everywhere else — a bad draft you have to rewrite costs more than
writing it once.

The proposal model assignment in §9 controls Codex execution. This section describes an optional
draft/review workflow; its shared tier-table authority remains specific to that workflow.

The same pattern is documented in OpenTechnologyApp and OpenTechnologyBlog so all three repos stay
coherent. The **tier-table authority** is OpenTechnologyApp's
[OpenTechnologyApp:docs/readable/MODEL_ROUTING_POLICY.md](https://github.com/OpenTechnology14/Task-Management/blob/main/docs/readable/MODEL_ROUTING_POLICY.md)
— a different repository, not a file in this one. This section is the hybrid-creator-platform
boundary list, not a second policy.

### When to use it

Bulk, structured, heavily-templated work where the shape is known and the review is mechanical:

- Bulk profile-config generation (`profiles/<name>/config.yaml` fan-out)
- Template and shot-list drafting — `marketing-crosswalk` templates, walkthrough scripts, run-of-show
- First-pass module docs — `setup/manual.md`, `setup/automated.md` skeletons
- Translations
- Content drafting for stream shows — episode premises, viewer-interaction lines
- PR description writes

What these share: a known output shape, many near-identical instances, and defects that are visible
on inspection rather than at runtime.

### When NOT to use it

These use the assigned Sol or Astra model in Codex, or Claude when following the optional review workflow.
Each boundary exists for a specific reason, not as a general preference:

| Path | Why |
|---|---|
| `apps/*/src-tauri/**` | Native code plus entitlements and capability files. A wrong capability is a security defect that compiles and passes tests |
| `modules/character-avatar/**` | Avatar pipeline; security-sensitive rendering and the VTS token path |
| `configs/local/**` *when credentials are involved* | Credential handling. Config that is purely structural is fine |
| Cross-app orchestration spanning both apps | The shared-crate contracts (`recording-library`, `local-settings`, `social-manager`) are the one place a local change has non-local consequences |
| Streaming and gameplay pipeline changes | The character-avatar ↔ Creator Extend integration is too tightly coupled — playback-event contracts, session/generation guards and stale-event rejection are subtle and their failures are silent |

The streaming/gameplay boundary is the one most likely to be argued with. Do not: the guards in
`modules/character-avatar/stream_avatar/runtime.py` reject stale, duplicate, off-air and
mismatched-finish events, and a plausible-looking rewrite that drops one of those conditions
produces an avatar that animates on the wrong event and no failing test.

### Mechanics

Identical to the other two repos.

**Phase 1 — draft:**

```bash
opencode run --auto --model huggingface/Qwen3-Coder-480B "prompt" .
```

**Phase 2 — review.** A Claude session runs the checklist. This is the half that makes the pattern
work, and skipping it makes it worse than not using the pattern at all:

- Imports — resolve, and are actually used
- API surfaces — the called function exists with that signature
- Types — no invented fields; check against the real struct or model
- Security — credentials, entitlements, capability files, anything touching a token
- `npm run build` for app-side changes
- **A runtime check, not just an exit code.** A build that exits 0 and a page that renders are
  different claims
- **No fix-until-green.** If the draft needs more than small corrections, discard it and write it
  directly. Iterating a model toward a passing test is how wrong code acquires a green check

### Review discipline

The blog post at
<https://www.opentechnologyblog.com/blog/hybrid-ai-hugging-face-claude> covers the reasoning behind
the review half. Read it before relying on the pattern for anything non-trivial.

---

## 14. Agent skills (shared across tools)

Task playbooks live in `.claude/skills/<name>/SKILL.md`. Each is plain markdown with a `name`, a
`description` and a `when_to_use` in its frontmatter. Claude Code loads them by description and appends
`when_to_use` to it in its skill listing; **Codex, ChatGPT and any other tool read the same files by path**
and ignore the extra field, so the `description` stays self-sufficient — open the skill whose description
matches the task and follow it. `AGENTS.md` is generated from this file, so it carries this pointer; the
skills are not duplicated into it.

| Skill | Use when |
|---|---|
| `marketing-discovery` | a request names a marketing module, or you are about to write marketing content or register a module |
| `code-creation` | adding or changing code or a module: conventions, the Blender still-job lifecycle, test discipline |
| `docs` | editing the crosswalk registry, `MARKETING.md`, a pointer doc, or anything under `docs/` |
| `design` | personas, voices, show profiles, app profiles, marketing-module parity |
| `audits` | crosswalk coverage audits and the static test-coverage / dead-export pattern |
| `security` | secrets, `.env`, ports and authentication, or a sensitive path (Tauri capabilities, the avatar module, credential configs, the shared crates); not path-bound, so open it yourself |

Commands that sit beside them in `.claude/commands/` (`audit`, `pre-merge`) also begin by reading `AGENTS.md`.
A skill summarises the documents it cites; where they disagree the cited document wins and the skill is the
thing to fix. `docs/design/BUILD-PROMPTING-DIGEST.md` is the prompt kit for asking an agent to extend this
repository. Voice registers are described, never attributed to a real person — see the `design` skill.

---

## 15. Design system

`design-system/` is the hub for the ecosystem's visual and voice conventions. This repository holds the source of truth; every
other repository keeps a pointer doc plus its own local overrides, never a copy. **Everything in it is `drafted`, awaiting owner
review.** Read `design-system/README.md` first.

| File | Holds |
|---|---|
| `design-system/tokens.yaml` | color, type, space, radius, shadow and motion tokens: the hub's proposed default, every consumer's verbatim observed value, computed contrast results and the open owner decisions |
| `design-system/components.md` | component specs (buttons, cards, modals, forms, badges, navigation, feedback, overlays): usage rules and anti-patterns, no code |
| `design-system/voice-and-tone.md` | per-profile voice, as registers |
| `design-system/iconography.md`, `design-system/accessibility.md` | icon rules and licensing; the WCAG AA baseline, contrast, keyboard and focus rules |
| `design-system/crosswalk/consumers.md` | the downstream repositories and the pointer-doc path each is expected to keep |
| `design-system/proposals/TEMPLATE.md` | the template for design artifacts: mockup, data flow, interaction notes, open questions, decision gates |

Rules for any agent:

- **Adopt a token only when it is `approved`.** A `drafted` value documents what exists; it is not an instruction, and a consumer must
  not change its implemented values because of it.
- **Do not copy token values into other documents or repositories.** Name the role (`surface.raised`) and point here.
- **Voice is described by register, never by a real person's name** (§14, the `design` skill). The hub, every pointer doc and every
  prompt follow `docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md` §7.3.
- The hub is registered in the marketing crosswalk as the `design-system` row (`kind: design-system-hub`), so
  `modules/marketing-crosswalk/crosswalk/modules.yml` finds it by name.
- `tests/design_system/` checks the hub; run `make test` after any change there.

---

## 16. Contribution workflow

How a change gets from a task to a pull request. The rules bind every agent and tool; `AGENTS.md` is generated from this file.

- **Work on a task branch in your own Git worktree.** First inspect `git status`, open PRs and `git worktree list` for overlapping
  work (`.claude/skills/code-creation/SKILL.md` step 4; `.claude/commands/pre-merge.md`).
- **Preserve changes you did not make.** If the checkout holds uncommitted work that is not yours, build in a separate worktree off
  `origin/main`, and never clean up what you did not create.
- **Check before you claim a number.** Take the next proposal ID only after the queue, open PRs and other worktrees show it free
  (`.claude/commands/pre-merge.md` step 3).
- **Record verification.** Find what proves the change in `docs/agent/VERIFICATION-MATRIX.md`, run it, and write the command and its
  result in the pull request. "Not run" is acceptable; silence is not (`docs/PROPOSALS.md`, "Adding a proposal", step 5).
- **Describe the change as `CONTRIBUTING.md` asks:** user outcome and layer, exact verification, privacy and security impact,
  rollback, and any scaffold or proposal labelled as one.

---

## 17. Work registration (entry gate)

Every agent session registers its work **before it starts** and gives each item exactly one Kind. This repository keeps no list of Kinds of its own: the work types and the gate live in the public AgentWorkflows library, read at the pinned revision below.

- **Register, then start.** Look for the item first (`docs/PROPOSALS.md`, the lane docs under `docs/todo/`, open PRs and the owner's private work view). Attach to it if it exists; otherwise write one short row with its Kind and state. The project's facilitator persists the row and a worker proposes it. Work with no row does not start; urgent security triage is registered as soon as it is safe to. The library's [entry gate](https://github.com/OpenTechnology14/AgentWorkflows/blob/9495bfb6a62ddda692150b69b6f20da605cdf238/workflows/ENTRY_GATE.md) has the steps.
- **One Kind per item**, from the library's [work types](https://github.com/OpenTechnology14/AgentWorkflows/blob/9495bfb6a62ddda692150b69b6f20da605cdf238/workflows/WORK_TYPES.md). At this pin the catch-all for upkeep, and for anything that fits no other Kind, is `housekeeping`; it is never a way around review or security gates.
- **Hybrid's own vocabularies stay as they are.** Queue states in `docs/PROPOSALS.md`, lane row prefixes in `docs/todo/README.md` and the evidence vocabulary in `docs/PROPOSAL_CREATION_SOP.md` describe a proposal's life or what a row waits on. They are not a work's Kind.
- Pinned library revision: `9495bfb6a62ddda692150b69b6f20da605cdf238`, a pending pull request in the library, so the links resolve while that pull request exists. `tests/docs/test_work_registration_pointers.py` keeps this section, its links and the four skills' pointers in step.
