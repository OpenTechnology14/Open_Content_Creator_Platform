# Proposal — Guided Setup, Automation, and Service Readiness

**Queue row:** `P-003`
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — Native setup, credentials and shared capability gates
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Code complete — shared readiness contract, desktop capability gates, and companion synchronization built; physical Windows/hardware and hosted acceptance remain

**2026-09-12 direction:** open either Extend app before optional workstation dependencies.
The next extension is tracked separately as
[P-063](../PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup): Windows app delivery and
additional shared in-app install/configure recipes with progress, retry and recovery. This does
not change the completion claim for P-003's recorded scope. The installer slice was subsequently
authorized on the same date; its artifact and acceptance evidence belongs to P-063.
The [desktop launch guide](../../modules/infrastructure/setup/desktop-setup.md) is the current
entry point; OBS and Docker/WSL must not gate the packaged setup view.

**Date:** 2026-07-12
**Products:** Stream Extend, Creator Extend, OpenTechnology Creator Platform template
**Roadmap layers:** Creator Experience, Content Creation, Automation / Control, Observability

## Decision summary

Add a shared setup and readiness system that runs before a product exposes a
service as usable. The system should:

1. discover the local machine and installed dependencies;
2. show complete, product-specific setup steps;
3. automate safe and supported steps with explicit user approval;
4. verify outcomes with real checks rather than completed checkboxes;
5. unlock each service independently when its required checks pass; and
6. publish the same state to the OpenTechnology Creator Platform project.

This is an extension of the current roadmap, not a new platform layer. The
native Tauri applications remain responsible for local discovery and setup.
OpenTechnology displays, coordinates, and audits that work through an
outbound-only companion connection.

## Current-state audit

The documentation contains detailed setup material, but neither application
currently turns it into a complete first-run experience.

| Surface | Setup steps in UI | Real status checks | Readiness gate | Current result |
|---|---:|---:|---:|---|
| Stream Extend | No | No | No | The dashboard shows OBS and relay badges, but the Rust OBS client returns placeholder disconnected/empty values and its control methods are TODOs. Service links are fixed localhost links without health results. |
| Creator Extend | No | Partial | No | It performs a real ComfyUI `/system_stats` and queue probe. Blender and Krita are only discovered when launch is attempted; MinIO, FastAPI, models, custom nodes, workflows, plugins, and output round trips are not checked. Workflow execution still queues an empty JSON placeholder. |
| Setup timeline and guides | Yes, outside the apps | Mostly manual validation lists | No | Useful source material, but checklist completion is not connected to machine evidence or application state. |
| OpenTechnology Creator Platform template | Partial | Proposed through a bridge | No | Six platform-aware playbooks and a setup dashboard exist, but most steps are copy/paste instructions. Auto-detection, command execution, and health evidence depend on a companion bridge that is not yet part of this repository. Some sample services are initially marked Healthy, which can misrepresent a new installation. |

The product README currently promises one-click setup. The implementation
should not present that claim as complete until the readiness criteria in this
proposal are met.

## Product behavior

### First run

On first launch, each desktop app opens **Setup** instead of the operational
dashboard. The user chooses a profile, reviews what will be installed or
configured, and starts a resumable setup run.

Recommended Stream Extend profiles:

- **Stream Core:** OBS, OBS WebSocket, scene collection, encoder, recording,
  camera, and audio validation.
- **Broadcast Graphics:** FastAPI, Redis, NodeCG, overlays, and browser sources.
- **AI Stream:** ComfyUI or other selected local AI runtime and virtual camera.
- **Agent / Avatar:** Ollama, agent runtime, TTS, and avatar connection.
- **Operations:** health exporter, Prometheus/Grafana/Loki, n8n, and optional
  Tailscale or hosted relay.

Recommended Creator Extend profiles:

- **Creator Core:** ComfyUI, one supported compute backend, starter workflow,
  model inventory, and generation smoke test.
- **Image Editing:** Krita, AI Diffusion integration, inpaint model, and edit
  round trip.
- **3D / Motion:** Blender, Creator Extend addon, render smoke test, and asset
  upload.
- **Storage / Sync:** MinIO buckets and authenticated write/read/delete test.
- **Sports CV:** Python environment, camera access, OpenCV/YOLO/MediaPipe, and a
  sample-frame inference test.
- **Realtime Output:** virtual camera or NDI path and an OBS ingestion test.

Profiles are additive. Optional features must never block unrelated local
features.

### Setup step lifecycle

Every step follows the same state machine:

```text
not_checked -> checking -> action_required -> applying -> verifying -> ready
                         \-> blocked                 \-> failed
```

Each visible step includes:

- what is being checked and why it is required;
- detected version, endpoint, or device where applicable;
- whether the action is automatic, requires approval, or must be manual;
- progress and sanitized logs;
- a retry and a manual-instructions path;
- the evidence captured by verification; and
- the feature or service that becomes available after success.

Checkboxes may record that a user read or performed a manual instruction, but
they do not make a service ready. Only a successful verification check does.

### Capability-level service gating

Do not use a single global `setupComplete` flag. Calculate readiness per
capability:

```text
OBS control       = OBS process + WebSocket auth + scene-list request
Go Live           = OBS control + encoder + stream destination + audio/video smoke checks
Comfy workflow    = ComfyUI + workflow schema + required nodes + required models
Krita AI edit     = Krita + plugin + ComfyUI + inpaint workflow
Blender publish   = Blender + addon + output path (+ MinIO only when sync is selected)
Remote control    = local capability + authenticated outbound bridge/relay
```

As of P-058, the two Extend apps implement the relay half of this formula. They persist public
relay settings separately from access tokens, authenticate outbound WebSockets, target requests by
stable device ID, validate a compiled action allowlist, and hold every accepted request for local
approval. OpenTechnology machine pairing and signed readiness-event synchronization remain future
work; a connected relay alone does not mark the underlying OBS or ComfyUI capability ready.

The dashboard can still open in a degraded state. Unready service cards show
**Finish setup** or **Repair** instead of an action that will predictably fail.
Potentially destructive or external actions, especially **Go Live**, remain
explicit user actions and are never performed as setup tests.

## Shared technical design

### 1. Declarative setup manifests

Add configuration-owned manifests rather than embedding setup order in Svelte
components:

```text
configs/setup/
  schema/setup-manifest.schema.json
  shared.yml
  stream-extend.yml
  creator-extend.yml
```

A manifest defines:

- stable IDs, labels, descriptions, and guide links;
- supported operating systems and architectures;
- dependencies between checks;
- capability requirements;
- detector, action, verifier, and rollback/help action IDs;
- whether a step is required, optional, or profile-dependent;
- version constraints and timeouts; and
- safe redaction rules for returned evidence.

Manifests must reference a compiled allowlist of native actions. They must not
contain arbitrary shell commands received from a server.

### 2. Shared native setup engine

Create a Rust workspace library used by both Tauri applications:

```text
apps/shared/setup-engine/
  src/manifest.rs
  src/detection.rs
  src/actions.rs
  src/verification.rs
  src/readiness.rs
  src/events.rs
```

Responsibilities:

- OS, CPU/GPU, RAM, disk, permissions, executable, process, port, HTTP, and
  WebSocket detection;
- allowlisted installation/configuration actions;
- streaming progress events to the UI;
- post-action verification and evidence capture;
- persisted, resumable setup runs;
- capability readiness calculation; and
- generation of a sanitized support bundle.

Tauri commands should expose a small stable contract:

- `setup_get_plan(profile_ids)`
- `setup_scan()`
- `setup_apply(step_id, approval)`
- `setup_verify(step_id)`
- `setup_get_readiness()`
- `setup_get_run(run_id)`
- `setup_cancel(run_id)`
- `setup_export_support_bundle()`

### 3. Direct injection map

The following locations are the first implementation touch points. Line numbers
will move; the named functions and sections are the durable anchors.

| Location | Anchor | Change |
|---|---|---|
| `apps/stream-extend/src-tauri/src/obs.rs` | `get_status`, `get_scenes`, `get_stream_status`, `toggle_stream` | Replace the placeholder responses with an authenticated OBS WebSocket v5 client. Reuse that client from setup verifiers instead of implementing a second OBS probe. |
| `apps/stream-extend/src-tauri/src/lib.rs` | module declarations, app state, `invoke_handler` | Add `setup` command wrappers, manage `SetupEngine`, load `configs/setup/stream-extend.yml`, and publish progress events to the WebView. |
| `apps/stream-extend/src/routes/+page.svelte` | `onMount`, `refreshStatus`, OBS panel, Services panel | Load capability readiness on mount; route a first-run user to Setup; replace raw connectivity booleans with readiness cards; gate scene and Go Live actions. |
| `apps/stream-extend/src/routes/setup/+page.svelte` | new file | Render profile selection, scan results, action approval, verification evidence, and retry/repair controls. |
| `apps/stream-extend/src-tauri/Cargo.toml` | workspace dependencies | Add `setup-engine = { path = "../../shared/setup-engine" }` and the selected OBS WebSocket crate. |
| `apps/creator-extend/src-tauri/src/comfyui.rs` | `get_status`, `list_workflows`, `queue_prompt` | Preserve the working system/queue probe, then add object-info, workflow dependency, model, history, and smoke-output checks. |
| `apps/creator-extend/src-tauri/src/blender.rs` | executable discovery and `open` | Expose version/addon/render verification functions to the setup engine. Do not infer readiness only because the executable launched. |
| `apps/creator-extend/src-tauri/src/krita.rs` | executable discovery and `open` | Expose version/plugin/ComfyUI-connectivity verification functions. |
| `apps/creator-extend/src-tauri/src/lib.rs` | module declarations, app state, `invoke_handler` | Add the same setup command wrappers and engine state using `creator-extend.yml`. |
| `apps/creator-extend/src/routes/+page.svelte` | `onMount`, `queueWorkflow`, tool cards | Replace the ComfyUI-only status model with capability readiness. Fix workflow loading before enabling Run. Show Setup/Repair on unready tools. |
| `apps/creator-extend/src/routes/setup/+page.svelte` | new file | Use the shared setup UI with Creator Extend profiles and branding. |
| `apps/creator-extend/src-tauri/Cargo.toml` | workspace dependencies | Add the shared setup engine dependency. |
| `apps/shared/setup-engine/` | new Rust crate | Own manifest parsing, detectors, allowlisted actions, verifiers, state transitions, evidence, readiness, and OpenTechnology event generation. |
| `apps/shared/setup-ui/` | new Svelte package | Own `SetupWizard`, `SetupStep`, `ReadinessBadge`, `ActionApproval`, and `RepairPanel`. Add it to both app `package.json` files as a local dependency. |
| `configs/setup/` | new configuration directory | Store the schema and shared/product manifests. This is the source of truth for setup order and capability requirements. |
| `tests/setup/` | new tests | Add manifest-schema, readiness-graph, redaction, idempotency, and fixture-based detector/verifier tests. |
| `docs/setup-timeline.html` | existing independent checkboxes | Later, read exported readiness JSON when opened through the app; retain static/manual behavior when opened standalone. |

#### OpenTechnology project injection locations

The OpenTechnology files currently live in a separate checkout. They should be
changed in the same implementation phase, but are not runtime dependencies of
the local creator platform.

| Location | Change |
|---|---|
| `Task-Management:templates/creator-platform/template.json` | Add Setup Runs and readiness/evidence fields; change sample operational states from Healthy/Verified to Unknown/Not Checked. |
| `Task-Management:templates/creator-platform/playbooks.json` | Add Machine Registration and Awaiting Verification steps; generate tool steps from the same manifest IDs. |
| `Task-Management:templates/creator-platform/README.md` | Document pairing, approvals, evidence freshness, repair, and the manual fallback. |
| `Task-Management:src/lib/templates.ts` | Register `creator_platform` only if it should be a built-in template instead of upload-only. |
| `Task-Management:server/routes/setup.ts` | **First ingestion slice implemented 2026-07-12:** `POST /projects/:projectId/setup/events` validates and persists check observations, deduplicates by `eventId`, rejects stale/ambiguous matches, audits the update, and broadcasts SSE. Machine pairing, readiness query, and approved-action endpoints remain proposed follow-up work. |
| `Task-Management:server/index.ts` | Import `setupRoutes` beside the other route modules and mount it with `app.use('/api', setupRoutes)` beside the current SSE/playbook routes. |
| `Task-Management:server/schemas.ts` | Add strict schemas for machine pairing, setup event envelopes, evidence allowlists, and remote action requests. Reject unknown keys and cap evidence/log sizes. |
| `Task-Management:server/store.ts` | Persist machine registrations, used event IDs, setup-run correlation, and machine credential hashes using the project's existing storage conventions. Never store raw machine credentials. |
| `Task-Management:server/routes/sse.ts` | Extend the current user-oriented SSE design only if companions will receive approved action events through it. Add a machine-authenticated audience scoped to one project; do not reuse a user JWT in a long-running companion. |

### 4. Implementation examples

These examples define the intended contract. They are illustrative and should
be validated against the selected crates and the OpenTechnology import schema
during implementation.

#### Setup manifest example

`configs/setup/creator-extend.yml`:

```yaml
schemaVersion: 1
product: creator-extend
profiles:
  - id: creator-core
    label: Creator Core
    requiredCapabilities: [comfy-workflow]

checks:
  - id: creator.comfyui.api
    label: ComfyUI API
    detector:
      type: http-json
      urlFromConfig: comfyui_url
      path: /system_stats
      timeoutSeconds: 3
    verifier: comfyui-system-and-queue
    help: docs/guides/archive/guide-04-comfyui-content-creation.md

  - id: creator.comfyui.starter-output
    label: Starter generation
    dependsOn: [creator.comfyui.api, creator.comfyui.workflow-deps]
    action: comfyui-run-bundled-smoke-workflow
    verifier: comfyui-output-readable
    approval: required

capabilities:
  - id: comfy-workflow
    label: Run ComfyUI workflows
    requires:
      - creator.comfyui.api
      - creator.comfyui.workflow-deps
      - creator.comfyui.starter-output
```

The manifest references registered action/verifier IDs. It does not contain a
shell command that can be replaced by cloud or template data.

#### Rust engine wiring example

Inject the equivalent into each app's `src-tauri/src/lib.rs` near the existing
managed `AppConfig` and command registration:

```rust
use setup_engine::{CapabilityReadiness, SetupEngine, SetupPlan};

#[tauri::command]
async fn setup_scan(
    engine: tauri::State<'_, SetupEngine>,
) -> Result<SetupPlan, String> {
    engine.scan().await.map_err(|error| error.to_string())
}

#[tauri::command]
async fn setup_get_readiness(
    engine: tauri::State<'_, SetupEngine>,
) -> Result<Vec<CapabilityReadiness>, String> {
    engine.readiness().await.map_err(|error| error.to_string())
}

// Builder additions:
// .manage(SetupEngine::load(include_str!(...product manifest...))?)
// .invoke_handler(tauri::generate_handler![..., setup_scan, setup_get_readiness])
```

The production implementation should return structured error codes alongside a
sanitized message so the UI can distinguish retryable, manual, and blocked
outcomes.

#### Svelte service gate example

Replace direct booleans such as `obsConnected` or `comfyConnected` as the sole
action gate:

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let readiness = $state<Record<string, { status: string; summary: string }>>({});
  const canGoLive = $derived(readiness['stream-go-live']?.status === 'ready');

  async function loadReadiness() {
    const results = await invoke<Array<{ capabilityId: string; status: string; summary: string }>>(
      'setup_get_readiness',
    );
    readiness = Object.fromEntries(results.map((result) => [result.capabilityId, result]));
  }
</script>

{#if canGoLive}
  <button onclick={toggleStream}>Go Live</button>
{:else}
  <a href="/setup?capability=stream-go-live">Finish setup</a>
  <p>{readiness['stream-go-live']?.summary ?? 'Not checked'}</p>
{/if}
```

The actual Go Live handler must recheck freshness immediately before acting; a
stale UI snapshot is not sufficient authorization.

#### Verification-result example

```json
{
  "checkId": "stream.obs.websocket",
  "status": "ready",
  "observedAt": "2026-07-12T18:30:00Z",
  "expiresAt": "2026-07-12T18:30:30Z",
  "summary": "Authenticated to OBS WebSocket v5 and listed 8 scenes",
  "evidence": {
    "obsVersion": "31.x",
    "webSocketVersion": "5.x",
    "sceneCount": 8
  },
  "remediation": null
}
```

Failure evidence should be equally actionable:

```json
{
  "checkId": "creator.comfyui.workflow-deps",
  "status": "blocked",
  "summary": "Starter workflow requires two unavailable node classes",
  "evidence": { "missingNodeClasses": ["ExampleNodeA", "ExampleNodeB"] },
  "remediation": {
    "kind": "manual",
    "label": "Open custom-node setup instructions",
    "guide": "docs/guides/archive/guide-04-comfyui-content-creation.md"
  }
}
```

#### OpenTechnology event example

The local companion sends a sanitized, idempotent envelope over the existing
authenticated outbound connection:

```json
{
  "eventId": "01J...",
  "eventType": "setup.check.observed",
  "schemaVersion": 1,
  "manifestVersion": "2026.07.1",
  "machineId": "studio-mac-7f3a",
  "setupRunId": "run-01J...",
  "occurredAt": "2026-07-12T18:30:00Z",
  "payload": {
    "checkId": "creator.comfyui.api",
    "status": "ready",
    "observedAt": "2026-07-12T18:30:00Z",
    "expiresAt": "2026-07-12T18:35:00Z",
    "summary": "ComfyUI system and queue endpoints responded",
    "evidence": { "gpuBackend": "mps" }
  },
  "signature": "machine-credential-signature"
}
```

The OpenTechnology ingestion mapping is:

```text
machineId + checkId  -> Tool Install / Service Health item
setupRunId           -> Setup Runs item
status               -> Readiness Status
observedAt/expiresAt -> Observed At / freshness calculation
summary              -> Evidence Summary
failed or blocked    -> Last Error + repair automation
```

#### First implementation slice

The smallest vertical slice should prove the architecture without attempting
all installers:

1. add the manifest schema, `setup-engine`, and read-only HTTP/WebSocket checks;
2. implement the real OBS handshake and keep the existing ComfyUI probe;
3. add one Setup route to each app;
4. gate **OBS Control** and **ComfyUI Workflows** from readiness results;
5. persist and display evidence;
6. change OpenTechnology seed health to Unknown; and
7. publish one `setup.check.observed` event through the companion contract.

After this slice is verified, add approved installation/configuration actions
one tool at a time.

### 5. Shared UI components

Add a shared frontend package for:

- profile selection;
- environment summary;
- setup stepper;
- action preview and approval;
- progress/log output;
- readiness summary;
- repair mode; and
- settings entry point to rerun checks later.

Both products use the same interaction model while applying their own theme and
manifest.

### 6. Persisted evidence, not assumed state

Store local state with the Tauri store plugin. A check result contains at least:

```json
{
  "checkId": "creator.comfyui.api",
  "status": "ready",
  "observedAt": "2026-07-12T18:30:00Z",
  "expiresAt": "2026-07-12T18:35:00Z",
  "version": "0.x",
  "target": "http://127.0.0.1:8188",
  "summary": "System stats and queue endpoints responded",
  "evidence": { "gpuBackend": "mps" }
}
```

Credentials, stream keys, full environment values, private paths, and model
license tokens must not appear in evidence or logs. Volatile service checks
expire and are refreshed; durable install checks are invalidated by version or
configuration changes.

## Required verification catalog

### Shared platform checks

- supported OS and architecture;
- sufficient disk, RAM, and selected GPU/backend capability;
- required filesystem and camera/microphone permissions;
- Docker/Compose only for profiles that select container services;
- FastAPI health and dependency health;
- Redis ping, Postgres query, and MinIO authenticated bucket round trip when
  those services are selected;
- local-only endpoints bound safely; and
- hosted/self-hosted relay authentication only when remote features are chosen.

### Stream Extend checks

- OBS executable/version and running state;
- authenticated OBS WebSocket v5 handshake;
- scene collection imported and required scene/source names present;
- encoder availability and a short local recording test;
- camera produces frames and selected audio buses produce signal;
- browser-source URLs return successfully;
- NodeCG bundle and overlay endpoints;
- optional ComfyUI/virtual-camera path;
- optional Ollama, TTS, avatar, n8n, and observability endpoints; and
- a preflight summary before Go Live.

Setup must never reveal or test a real stream key by starting a public stream.

### Creator Extend checks

- ComfyUI system, queue, history, and object-info endpoints;
- selected compute backend and minimum memory for chosen workflows;
- workflow JSON validity and required custom-node classes;
- required model files plus known hash/license metadata where available;
- a low-cost starter generation that produces a readable output;
- Blender executable/version, addon enabled, and a tiny local render;
- Krita executable/version, plugin enabled, and ComfyUI connectivity;
- MinIO output bucket write/read/delete when sync is enabled;
- sports-CV Python imports, camera/sample input, and one inference result; and
- virtual camera/NDI output only for realtime profiles.

## OpenTechnology Project template integration

The existing `creator-platform` template is a useful starting point, but it
should consume the same readiness model instead of maintaining a separate
definition of setup.

### Template changes

1. Add a **Machine Registration** playbook that installs and pairs the signed
   outbound companion before any automated local steps are offered.
2. Generate Tool Install playbooks from the shared setup manifests, preserving
   Windows/macOS manual alternatives.
3. Add fields for **Check ID**, **Readiness Status**, **Observed At**,
   **Evidence Summary**, **Detected Version**, **Required Version**,
   **Machine ID**, **Setup Run ID**, and **Last Error**.
4. Add a **Setup Runs** queue for progress, approvals, failures, and audit links.
5. Change all imported install and service-health examples to **Not Checked** or
   **Unknown**. Never seed a new project with Healthy/Verified operational data.
6. Update the Setup dashboard to show required capabilities, stale checks,
   blocked steps, machines awaiting pairing, and recent setup failures.
7. Mark an install Verified only after signed companion evidence arrives. Manual
   playbook completion alone remains **Awaiting Verification**.
8. Add repair automations for expired/down checks, but do not let the server
   execute arbitrary local commands.

### Companion protocol

The companion is the same setup engine used by the Tauri apps, operating in
headless mode where appropriate. It makes outbound authenticated connections;
no local service is exposed publicly.

Minimum event contract:

- `machine.registered`
- `setup.run.started`
- `setup.step.action_required`
- `setup.step.progress`
- `setup.check.observed`
- `capability.readiness.changed`
- `setup.run.completed`
- `setup.run.failed`

Remote requests contain only an allowlisted action ID and parameters validated
against the installed manifest version. Privileged actions require approval on
the local machine. The companion signs results with its machine credential so
OpenTechnology can distinguish live evidence from a manually edited item.

## Security and operational guardrails

- Discovery and verification may run automatically; installation and
  configuration changes require an action preview and consent.
- Use native package managers only where the package and version source are
  trusted. Otherwise open the official installer instructions.
- Never send local secrets, OBS passwords, stream keys, MinIO secret keys, or
  full `.env` contents to OpenTechnology.
- Keep OBS, ComfyUI, and other latency-sensitive services local. Remote setup is
  orchestration, not cloud execution of the realtime path.
- Provide cancellation and idempotency. A retry must not duplicate scenes,
  buckets, plugins, or configuration entries.
- Back up user-managed configuration before changing it and report how to undo
  changes when automatic rollback is not safe.
- Treat optional integrations as optional; their failure cannot break the core
  application.

## Delivery sequence

### Phase 1 — Truthful readiness

- Define the manifest schema and readiness model.
- Implement read-only discovery and real checks.
- Replace placeholder OBS status calls.
- Add Setup/Repair views and capability gates.
- Remove seeded Healthy assumptions from the OpenTechnology template.

**Exit:** both apps accurately explain what is ready, missing, optional, or
broken without installing anything.

### Phase 2 — Guided setup

- Convert relevant guide steps into product manifests.
- Add profiles, resumable runs, manual steps, verification, and support bundles.
- Add smoke tests for OBS recording and Creator Extend generation/rendering.

**Exit:** a new user can reach a working core profile without leaving the app
except for OS/vendor steps that cannot safely be automated.

### Phase 3 — Approved automation

- Implement allowlisted install/configure actions.
- Add backups, idempotency, progress, retry, and repair.
- Package and sign the headless companion mode.

**Exit:** supported machines can complete core setup with explicit approvals and
real post-install verification.

### Phase 4 — OpenTechnology synchronization

- Pair machines and publish readiness events.
- Generate/import updated playbooks and setup fields.
- Add dashboards and automations for stale/failed checks.

**Exit:** the OpenTechnology project shows the same evidence-backed readiness as
the local apps and can coordinate approved setup without becoming a remote shell.

## Acceptance criteria

- A clean supported machine can complete each core profile from the Setup view.
- Restarting either app resumes the setup run without losing evidence.
- No capability becomes Ready from a checkbox alone.
- Every enabled service card links to current successful verification evidence.
- Optional service failure does not disable unrelated capabilities.
- Failed actions provide a retry and a tested manual path.
- Setup actions are idempotent and do not overwrite user configuration without
  preview and backup.
- Secrets are absent from UI logs, support bundles, telemetry, and
  OpenTechnology items.
- The OpenTechnology template imports with all operational health values Unknown
  until companion evidence arrives.
- Stream Extend does not start a public stream during setup validation.
- Creator Extend completes one low-cost local output smoke test for its core
  profile.

## Documentation impact

After approval and implementation:

- update `docs/architecture/roadmap.md` to list Guided Setup & Readiness under
  Creator Experience and Automation / Control;
- update `docs/architecture/product-spec.md` so one-click setup means the
  verified workflow described here;
- keep the existing guides as the detailed manual fallback and link individual
  setup steps to their relevant guide sections; and
- update `docs/setup-timeline.html` to display live app/companion evidence when
  available rather than maintaining an independent completion state.


## Local module-selection slice — 2026-09-08

Owner requested à la carte setup while clarifying Mac/Windows readiness. This authorizes the
local CLI slice under existing infrastructure setup tooling; it does not accept the full remote
companion or app-gating scope. The subsequent desktop slice below was separately authorized.
The older current-state audit above is historical;
consult `docs/AUDIT.md` for subsequent application implementation evidence.

Implemented: `scripts/setup/modules.py list|plan|install`, a twenty-module JSON catalog,
three optional profiles, explicit module dependency expansion, isolated per-module Python
environments, manual steps and per-run reports. Dependency installation never sets a capability
to ready. A failed install is recorded while other selected modules continue. Desktop apps,
models, containers, drivers, cloud provisioning and the Tauri first-run UI remain separate.
The [module-selection guide](../../modules/infrastructure/setup/module-selection.md) is the
current user path. The original P-056 streaming-only ZIP does not contain this new selector.

Verification follows the P-003 installer row in the verification matrix: all 12 setup tests
pass, actual catalog and stream-test plan commands succeed, real Audio Production dependency
installation succeeded in a dedicated environment, and selected Soundboard stayed manual-only.
The installed interpreter successfully ran `render_reply.py --help`. Report:
`output/module-setup/20260908-191609-666273/report.json`. Windows/macOS CI now includes selector
contracts, plan and the same small selective install; remote CI and native Windows evidence
remain pending. Full `make test` exited 0 (`/tmp/hcp-module-full-test.log`); Ruff 0.6.4
lint/format, 73 relative links and `git diff --check` passed.


## Desktop module-selection and checks slice — 2026-09-08

Owner requested the next priority after the CLI slice. Built a shared Svelte panel and a
local Tauri plugin in `apps/shared/ui` and `apps/shared/setup-wizard`, integrated into both
apps' default Setup view. Twenty module choices, three additive profiles and automatically
included dependencies are saved per product. The catalog, installer, requirements and manual
guides are embedded in each bundle; setup no longer depends on launching from this checkout.
Python itself remains an external prerequisite. Installed dependency environments are shared
between apps under the OS-local `HybridCreatorPlatform/module-setup` directory.

The Python installer serializes installs with an OS file lock. Native job metadata and atomic
reports preserve completion evidence; a restarted app labels an unfinished, unobserved job
honestly. Readiness checks verify requirement versions and `pip check`, then configured app
locations/PATH. App service checks use the existing OBS/ComfyUI commands. None of these marks a
whole capability Ready, installs a desktop app/model/driver, provisions cloud compute or blocks
access to the existing dashboard. No credentials are stored by this new plugin.

Mac acceptance on the built-in display: selected Audio Production and Soundboard in Creator
Extend, observed missing packages, installed real Loguru dependencies through the UI, then
observed package/consistency and app-presence checks pass. Soundboard configuration remained
manual. The bundled Soundboard guide opened. Quit/reopened Creator Extend: both choices and
completed job remained, while readiness evidence reset to “Not checked in this session.”
The Creator dashboard still displayed all ten bundled workflows. Stream Extend began with its
own empty selection, reused the audio environment without installation, and reported OBS
connection action required. Adding Broadcast produced four chosen modules plus two required
backend/storage modules. Neither native service was claimed connected.

Verification: 19 Python setup tests; 4 shared-plugin Rust tests; Creator 26 offline Rust tests
(1 explicitly live test ignored), Stream 12; both Svelte checks report zero errors/warnings;
both Mac debug .app/.dmg bundles built. `make test` reaches 100%, exit 0 at
`/tmp/hcp-desktop-setup-full-test.log`; Ruff 0.6.4 passes `modules/ scripts/ tests/setup` at
`/tmp/hcp-setup-ruff.log`. Rust logs: `/tmp/hcp-setup-shared-tests.log`,
`/tmp/hcp-setup-creator-tests.log`, `/tmp/hcp-setup-stream-tests.log`.
Build/check logs: `/tmp/hcp-setup-{creator,stream}-{build,check}.log`.
The native install and checks are retained in local application data under
`HybridCreatorPlatform/module-setup/jobs` and per-product check JSON files.

Overall P-003 remains in progress. Full capability acceptance/gating, relay credential
migration, remote contracts, native Windows execution and release signing are separate
remaining work. CI includes shared-plugin tests and Windows/macOS Python doctor;
no remote run is claimed. The existing streaming-only Windows ZIP predates this desktop slice.
User path: [desktop setup guide](../../modules/infrastructure/setup/desktop-setup.md).


## Persistent desktop connection settings slice — 2026-09-08

Both apps now expose a **Connections** view. Stream Extend persists the OBS host/port and local
ComfyUI, Grafana and API URLs; Creator Extend persists ComfyUI, MinIO and API URLs plus optional
Blender/Krita paths. The values load before the first status poll after restart. Saving changed
OBS settings clears the cached OBS client so the next check reconnects with the new values.

The shared `apps/shared/local-settings` crate writes public JSON atomically under
`HybridCreatorPlatform/connections`, using `0700` directories and `0600` files on Unix. OBS and
MinIO credentials use macOS Keychain, Windows Credential Manager or the platform-native store
selected by the `keyring` crate. Secret values never appear in public JSON, log messages or
frontend responses; `get_config` only returns `*_set` booleans. Blank secret inputs preserve a
credential, while explicit clear controls remove it. URL schemes and OBS host shape are
validated before saving. The previous Creator Extend `get_config` secret-return path is closed.

Native acceptance ran on the MacBook built-in display. Both apps rejected invalid values,
saved changed endpoints and disposable credentials, reloaded the endpoint and saved-credential
indicators after a full quit/reopen, then cleared the disposable Keychain entries and restored
the default localhost endpoints. Both public files were inspected: mode `0600`, no credentials,
and a repository/app-data scan found none of the disposable values. **Save and test** preserved
valid settings while correctly reporting that OBS was not reachable.

Verification: shared local-settings tests pass (2), Stream Extend passes 14 Rust tests,
Creator Extend passes 28 Rust tests with one explicit live test ignored, and both Svelte checks
report zero errors/warnings. Both Mac debug `.app`/`.dmg` bundles build. Final full-suite and
documentation results are recorded in the P-003 queue row. Native Windows credential behavior
and real connected OBS/ComfyUI checks remain pending; no service connection is claimed.


## Windows bootstrap and capture-device slice — 2026-09-08

The owner requested an easy Windows setup script plus capture-device diagnostics in the setup
system. `scripts/setup/windows.ps1` now locates or installs Python 3.12, optionally installs OBS
Studio and FFmpeg through exact winget package IDs, installs an explicit stream/creator/custom
module selection, runs readiness checks and writes a local capture report. It never installs all
modules by default, game clients, accounts, model weights or vendor-specific drivers.

`scripts/setup/capture_devices.py` enumerates exact DirectShow or AVFoundation names through
FFmpeg when available. Windows also records present Camera/Image/Media Plug-and-Play devices;
macOS uses `system_profiler` as a first-run camera/CoreAudio fallback. The shared setup plugin
bundles that scanner, exposes only fixed scan/save commands, and accepts a saved video/audio ID
only when it appears with the correct kind in the latest local report. Both app frontends use the
shared panel. A detected or saved device is never marked as a completed capture test; the user is
directed to make a local OBS recording and check picture, game audio, sync and 1080p60 stability.

Native MacBook-screen acceptance used the rebuilt Stream Extend app. The first scan exposed the
missing-FFmpeg behavior; after adding the OS-native fallback, the panel found OBS, FaceTime HD
Camera and MacBook Pro Microphone, saved both, and restored the exact choices after an app restart.
No physical capture card was connected, so HDMI input, game audio and 1080p60 recording remain
pending. A native Windows GitHub runner subsequently executed the PowerShell plan and capture CLI;
a fresh-host Python/winget installation and Windows desktop UI with real hardware remain pending.

Verification: 26 Python setup tests pass, including DirectShow/AVFoundation parsers, fallback
filtering and static bootstrap ownership; the shared setup plugin passes 5 Rust tests; both
Svelte checks and builds pass with zero errors/warnings; the Stream Extend debug `.app`/`.dmg`
bundle builds; the real local CLI scan found OBS, four AVFoundation video inputs and one audio
input. Full `make test` reached 100%/exit 0 and focused Ruff plus `git diff --check` passed. PR #41
run `34288968870` passed the Windows and macOS native rehearsals, including the Windows PowerShell
plan and capture diagnostic; run `34288968871` passed the full Linux test/acceptance job and both
desktop compile/test jobs.


## Shared readiness contract and companion synchronization — 2026-09-09

Both desktop apps now consume config-owned readiness manifests through the shared
`apps/shared/setup-engine` crate. Schema version 1 defines stable check IDs, required checks,
capability state, five-minute evidence expiry and the exact outbound setup-event envelope.
Stream Extend derives `obs-control` from an authenticated OBS version probe plus a non-empty
scene list. Creator Extend derives `comfy-workflows` from authenticated ComfyUI system/queue
probes plus the bundled workflow inventory. Their operational controls read those capabilities:
Stream scene/start controls and Creator workflow configuration remain locked when evidence is
missing, blocked, failed or expired.

Readiness snapshots persist locally and contain no service credentials. Optional OpenTechnology
synchronization stores its API key in the OS credential manager, validates the URL/project/machine
identifiers, and sends sanitized, idempotent observations to the existing authenticated
`POST /api/projects/{projectId}/setup/events` route. A failed connection leaves the latest snapshot
and event IDs on disk so the same evidence can be retried. Synchronization is outbound-only and
disabled until configured by the operator.

Verification: the shared engine passes seven tests, including expiry/capability recalculation and
a real loopback HTTP assertion over the exact bearer-authenticated event body. Stream Extend and
Creator Extend Rust suites pass, both Svelte checks/builds pass with zero errors/warnings, and the
full offline suite exits 0. The rebuilt Stream Extend app was exercised on the MacBook built-in
display: its Setup panel rendered contract/manifest versions and OpenTechnology settings, a real
OBS-disconnected check produced blocked evidence, and the Dashboard kept OBS controls locked.
The Windows/macOS native workflow now runs the shared Rust contract tests. The companion template
has exact ingestion fields, unknown/unverified defaults and tests preventing playbooks from
claiming manual verification.

This completes P-003's repository implementation. A physical capture card recording, fresh-host
Windows installation/credential-manager UI pass, and a live hosted OpenTechnology synchronization
remain acceptance evidence; they do not require another P-003 design or code slice unless testing
finds a defect.

## Module subfeature evidence index — 2026-09-10

Every module already carried separate manual and automated setup guides, but there was no single
view showing whether each smaller capability was built, automatically proven, or waiting on live
acceptance. [`../agent/SUBFEATURE-CHECKLIST.md`](../agent/SUBFEATURE-CHECKLIST.md) now provides that
roll-up for all twenty-one modules plus P-003/P-056/P-057/P-058 cross-module slices. It links directly
to both setup workflows and the canonical acceptance section for each module.

The shared setup plugin now derives its selection limit from the catalog rather than a hardcoded twenty-module cap; its five Rust tests pass with all twenty-one bundled guides and requirements.

The index does not become a third backlog: `PROPOSALS.md` remains the only work queue and the
acceptance checklist remains the definition of done. Documentation integrity now fails if a new
module is missing from the subfeature index, while `DM-ACCEPTANCE` requires capability changes and
new evidence to update the roll-up. Verified by the documentation integrity suite, the full
offline suite, and `git diff --check`.
