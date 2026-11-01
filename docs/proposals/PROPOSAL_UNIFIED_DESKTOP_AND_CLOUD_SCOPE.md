# Proposal: One desktop app for Stream Extend and Creator Extend

**Queue row:** `P-072`
**Agent model / effort:** `gpt-6.1-sol` / `high` — Desktop consolidation, migration contracts and staged cloud scope
Model assignment: [queue assignment](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — Testing; private shared-shell preview built and critical checks pass. Parity, migration, public release and replacement remain gated. State is authoritative in [the queue](../PROPOSALS.md).
**Owner:** OpenTechnology14 + agent
**Date:** 2026-10-04
**Roadmap layer(s):** Existing product surfaces; Creator Experience, Content Creation, Realtime AI, Automation / Control, Social Management, Backend / API, Storage / Data, Infrastructure and Observability. No new top-level module.
**Evidence level:** Current source inspected; consolidation and cloud expansion are Proposed. Historical acceptance is attributed to its existing proposal, not rerun here.

The owner explicitly wants the apps combined to make distribution to other people easier. This
records that direction and a phased implementation contract. The initial 2026-10-04 task created
the proposal. On 2026-10-12 the owner explicitly authorized the private preview before convergence
checks finish; the preview now exists at `apps/extend/`. Cloud phases remain candidate scope.

The assigned model/effort is offered by this host's execution controls. This drafting interface
does not expose a control to change or independently verify its active model; the assignment above
must be selected and recorded when implementation starts. No historical model execution is claimed.

## 1. Executive summary

**Private-preview authorization and implementation — 2026-10-12:** after requesting continuation
until the two Accepted proposals reach Testing, the owner explicitly answered **"Build the private
preview first"** to the five-gate timing question. The [roadmap exception](../architecture/deviations.md#2026-10-12--private-combined-shell-preview-before-convergence)
authorizes a preview alongside the legacy apps; full parity, migration, public release, commercial
changes, cloud phases and legacy replacement remain gated. Model assignment remains Sol/high;
no model dispatch or independently verified executor identity is inferred from that metadata.

[Extend Preview](../../apps/extend/README.md) is now a real Tauri/Svelte application: guided task
folders and compact layout; persisted Stream/Create/both choices; one shared setup environment;
separate profile selections; the shared locked recording inbox; read-only OBS/ComfyUI readiness
and bundled workflow catalog. Native pack checks reject disabled-domain operations. Invalid
connection drafts preserve saved settings; OBS secret updates use a separate preview vault identity.
No legacy settings/tokens are migrated. There are no native broadcast/render/remote/publishing
commands in its registered IPC surface. Editing/published status changes are denied, including
crafted invokes, and the inbox hides those metadata-only actions in preview mode.

New configuration is `configs/ui/combined-navigation.json`, `extend-preview-defaults.json` and
`configs/setup/extend-preview.json`. The original OBS/ComfyUI modules are included as source
adapters, not independently rewritten; the queue-status timeout repair under P-001 therefore also
applies here. A locked OBS vault yields blocked Stream observations while Create remains usable.
The preview grants no OAuth/remote/publishing plugin permissions and configures a local CSP.
Native GUI/CSP/credential-store enforcement is still an acceptance run, not inferred from builds.

**Built and checked:** 20 Rust unit/adapter tests, four Node navigation tests, native admission/
permission-surface Python checks and frontend check/build pass; an ARM64 Mac `.app` and `.dmg`
are produced by the locked debug bundle command. Both legacy app Rust and frontend checks/builds
are rerun because the shared recording component gained a backwards-compatible preview mode.
CI now includes the preview in the existing desktop matrix. These are private debug artifacts;
Windows/clean-host/signing, native UI/voice/video, restart/vault and public migration are not proved.

**Testing handoff:** U-01/U-02/U-07 apply to the private preview: first opening with prerequisites
absent, pack/layout persistence and keyboard/narrow-window navigation, selected-tool install/retry,
synthetic local import/reveal and profile separation, denied crafted invokes/remote origins and
vault failure recovery. The recording/streaming/export/remote parity journeys U-03–U-09 and public
rollback U-13 remain later gates. No global live stop/mute strip is claimed by this preview, since
it does not own/control a live session. Continue controlling live work in the existing apps.

Ship **one local desktop application**, with **Stream** and **Create** workspaces, one setup flow,
one recording/asset library and one settings/account area. A new user downloads one installer for
their OS, opens it without a developer toolchain or cloud account, and selects Stream, Create, or
both. Shared dependencies are installed once, and additional capabilities can be enabled later.
The product name, application identifier, pricing and store listing are separate release decisions.

This is feasible because both apps already use Tauri 2, Svelte 5 and several shared Rust/UI
packages. It is still substantial integration work: putting the two dashboards in one window does
not resolve settings conflicts, recording ownership, permissions, relay identity or resource use.
The smallest useful preview combines setup, navigation, profiles and recording handoff; replacement
of the existing downloads requires parity for all currently accepted workflows.

**Cloud recommendation:** desktop first, then an optional browser companion for status, planning
and review, followed by explicitly approved remote actions and selected batch jobs. A full browser
replacement is a separate, much larger product: the present UI calls native Rust commands for local
files, credentials, processes and OBS/ComfyUI connections. Reusing visual components does not make
those commands available in a normal browser. This conclusion follows from the current code and
[Tauri's native core/WebView process model](https://v2.tauri.app/concept/process-model/).

## 2. Verified current state

| Evidence inspected | What exists / what it means |
|---|---|
| Both `apps/*/package.json` and `src-tauri/tauri.conf.json` | Matching Svelte/Tauri stacks; separate bundles `com.streamextend.app` and `com.creatorextend.app`. Both currently set `app.security.csp` to null. Combining them requires a permission and content-policy review. |
| `apps/stream-extend/src/routes/+page.svelte` and `apps/creator-extend/src/routes/+page.svelte` | Separate pages and lifecycle polling with direct Tauri `invoke` calls. Both import shared setup, profile, social and remote components; Creator also imports `RecordingLibrary.svelte`. |
| Both `src-tauri/src/lib.rs`, `connection_settings.rs`; `apps/shared/local-settings/src/lib.rs` | Each app registers its own `get_config`/`set_config` and remote/setup commands. Connection files live under the shared OS local-data `HybridCreatorPlatform/connections` directory but are keyed by application identifier. OS-vault entries also use product-qualified keys. |
| `apps/shared/recording-library/` and `apps/shared/social-manager/` | Locked shared recording metadata and separate Stream/Content profile selections already exist. Media is referenced by local path, not copied into the other app. Preserve these contracts. |
| `apps/shared/setup-wizard/`, `setup-engine/`, `ui/`; `configs/setup/stream-extend.json`, `creator-extend.json` | Shared setup/readiness infrastructure exists, with product-specific manifests. This is the consolidation base; no second installer engine is needed. |
| `apps/shared/relay-client/src/lib.rs`, `control.rs`; `cloud/relay-api/app/routers/relay.py` | Product-specific discovery/action validation exists. The server accepts only `StreamExtend` and `CreatorExtend` presence identities today. A new product string would be rejected; a combined shell is a protocol migration too. |
| `cloud/relay-api/app/routers/sync.py`, `metrics.py`, `notifications.py` | Tenant-scoped sync and metrics routes exist. Sync is generic versioned JSON, not application-aware conflict resolution. APNs/FCM delivery helpers still have TODO implementations. These files do not prove a ready hosted companion. |
| `.github/workflows/desktop-installers.yml` | The installer matrix builds both app names and identifies outputs as unsigned private prereleases. One installer does not by itself solve public signing or clean-machine setup. |
| [Audit](../AUDIT.md), P-003/P-058/P-063/P-065 in [the queue](../PROPOSALS.md) | Some native Mac and loopback paths have recorded evidence; clean-host, physical media, Windows, real-account and hosted/two-device acceptance remain open for relevant paths. Consolidation must not convert those gaps into claims of completion. |

The [roadmap convergence rule](../architecture/roadmap.md#future-convergence-path) originally
delayed even proposal work until five acceptance gates passed. The owner's explicit request is a
**planning-only timing exception**, recorded in [deviations](../architecture/deviations.md).
The gates remain required before implementation replaces the two delivery surfaces. Product
branding/pricing and unrelated Pending/Deferred work receive no approval through this proposal.

## 3. Problem, goals, and non-goals

### Phase 0 source inventory and gate review — 2026-10-12

The owner requested work on P-072 and P-001. This pass advances the authorized baseline/contract
phase. It does not mark the five convergence gates passed or authorize a combined binary.
Source anchor: checkout `718240e42c61715873724ac92309773a2541c688`, plus existing unrelated
uncommitted documentation/testing work. The runtime files inspected below were unchanged in
that starting worktree. The P-072 assignment remains `gpt-6.1-sol` / `high`; no model dispatch or
historical executor identity is inferred from that assignment.

#### Current workflow coverage

Both apps expose six navigation views. Each dashboard contains additional task controls; those
controls must be included in parity even when they are not independent navigation entries.
“Source present” below means an implemented path is registered, not full native acceptance.

| Current surface / workflow | Source and evidence owner | State and consolidation requirement |
|---|---|---|
| Both: Module setup, selected tools, installs/retry, guides, capture/audio checks | Shared [ModuleSetup](../../apps/shared/ui/ModuleSetup.svelte), [setup-wizard](../../apps/shared/setup-wizard/README.md); P-003/P-063 | Source present; native Mac evidence recorded; clean physical Windows/capture acceptance open. Reuse the installer/environment locks and manifest resources once. |
| Both: Connections, save/restart, readiness/retry, optional setup sync | Both `connection_settings.rs`/`lib.rs`, shared [local-settings](../../apps/shared/local-settings/README.md), [setup-engine](../../apps/shared/setup-engine/README.md); P-003 | Source present, shared persistence contract but different settings DTOs and probe implementations. Preserve capability-specific readiness; do not merge conflicting endpoints silently. |
| Both: Remote control, discovery, request, approve/deny, correlated result | Both `relay.rs`, shared [relay-client](../../apps/shared/relay-client/README.md); P-058 | Loopback evidence exists; successful hosted action on two real devices remains open (ST-R14). Preserve product allowlists until negotiated migration is separately built. |
| Both: Social and Stream/Content profile switchers | Shared [social-manager](../../apps/shared/social-manager/README.md), `ProfileSwitcher.svelte`, `SocialManagement.svelte`; P-062/P-065 | Source present; real-provider routes/sign-in/private actions remain open. Separate profile selections must survive workspace switches; no publishing is authorized by this inventory. |
| Stream: Dashboard scene selection and observed OBS status | [Stream page](../../apps/stream-extend/src/routes/+page.svelte), `obs.rs`; P-055/P-063 | Real command implementation and fake protocol tests; current local server is unreachable. Native picture/audio and scene-change acceptance still required. |
| Stream: Grafana, Platform API, n8n and NodeCG service links | Stream dashboard Services section | Four external links exist; they use fixed local addresses rather than saved endpoint values. Include configured link routing in the future parity review; a link is not an embedded service or accepted overlay workflow. |
| Stream: managed stream/recording start, stop and handoff | Stream `lib.rs`/`obs.rs`, shared [recording-library](../../apps/shared/recording-library/README.md); P-065 | Ownership/order contracts exist; full real-profile handoff ST-R05 is open. Keep the session controller alive across navigation; never adopt a pre-existing recording as owned. |
| Stream: Automated streaming and Personalities authoring | `Autopilot.svelte`, `autopilot.rs`, `voice_studio.rs`; P-056/P-066 | Rehearsal/authoring paths built; live production/game/account/avatar bindings and audible OBS acceptance open. Preserve live/off-air guards and fixed worker boundaries. |
| Creator: Dashboard workflow catalog, preflight, input/image upload, queue, history and preview | [Creator page](../../apps/creator-extend/src/routes/+page.svelte), `WorkflowInputs.svelte`, `comfyui.rs`, `workflow_inputs.rs`; P-054/P-057/P-063 | Source present; historical local GPU/output evidence recorded; each target/workflow needs its stated acceptance. Current local ComfyUI endpoint is unreachable. |
| Creator: Recordings import/list, profile attribution, reveal/archive/status | Shared `RecordingLibrary.svelte`/recording library; P-065 | Source present; synthetic Mac import/reveal evidence recorded. **Start editing only writes `editing` status; Mark published only writes metadata.** Neither invokes rendering/upload. Real handoff and accounts remain open. |
| Creator: Blender launch, render planning/start/status/list/cancel/retry | Creator `lib.rs`, `blender.rs`, `blender_jobs.rs`, `tool_runtime.rs`; P-061 | Production-job source exists; full native two-scene failure/cancel/recovery acceptance remains open. Preserve manifest/job IDs and existing worker ownership. |
| Creator: Krita launch, packaged scripts, addon archive and tool checks | Creator `krita.rs`/`tool_runtime.rs`; P-057 | Fixed tool adapters exist; live DCC workflow acceptance remains separate. Do not broaden script/executable selection while transporting this page. |
| Creator: Posture Screen analysis | Creator `posture.rs`/`posture_analyze`, Sports Analytics module; P-057 | Native adapter present; physical/input-quality acceptance remains separate. Enabling this optional task must not require it for recording/clip work. |
| Planned combined Home, clip adapter, global live strip and admission policy | P-072 §5 | Proposed only. No combined shell or native recording-to-Shorts adapter exists. Reuse the Content Creation CLI after implementation authorization; status changes cannot satisfy U-09. |

#### Native command and migration map

Inspection of each `generate_handler!` registration found **27 Stream commands, 42 Creator
commands, 15 shared names and 54 distinct names**, excluding the two shared plugin namespaces.
Identical names do not imply identical arguments, validation or result types.

| Group | Registered commands / boundary |
|---|---|
| Shared names (15) | `get_config`, `set_config`; `remote_get_settings`, `remote_save_settings`, `remote_connect`, `remote_disconnect`, `remote_status`, `remote_approve`, `remote_deny`, `remote_request`; `setup_last_readiness`, `setup_refresh_readiness`, `setup_sync_settings`, `setup_save_sync_settings`, `setup_sync_now` |
| Stream OBS (9) | `obs_status`, `obs_connection_diagnostic`, `obs_recording_test`, `obs_scenes`, `obs_switch_scene`, `obs_stream_status`, `obs_toggle_stream`, `obs_start_stream_session`, `obs_stop_stream_session` |
| Stream workers (3) | `autopilot::autopilot_status`, `autopilot::autopilot_rehearse`, `voice_studio_request` |
| Creator workflows (11) | `comfyui_status`, `comfyui_preflight`, `comfyui_workflows`, `comfyui_load_workflow`, `comfyui_workflow_inputs`, `comfyui_upload_target`, `comfyui_queue_configured`, `comfyui_upload_image`, `comfyui_queue`, `comfyui_prompt_status`, `comfyui_output_preview` |
| Creator recording inbox (4) | `recordings_list`, `recordings_import`, `recordings_update`, `recordings_reveal` |
| Creator Blender jobs (7) | `blender_open`, `blender_batch_render`, `blender_job_start`, `blender_job_status`, `blender_job_list`, `blender_job_cancel`, `blender_job_retry` |
| Creator tools (5) | `krita_open`, `krita_run_script`, `creator_tool_status`, `creator_tool_archive_blender_addon`, `posture_analyze` |
| Shared plugins (separate from counts) | `plugin:module-setup` selection/install/check/capture/audio contracts and `plugin:social-manager` catalog/profile/account/publishing contracts. Retain their own native validation and permissions. |

| State / privilege | Conflict or migration policy to implement after approval |
|---|---|
| Shared `comfyui_url` and `api_url` in two app-qualified files | Show both values in import review; require a choice when different. Do not pick the most recently modified file as an implicit winner. |
| Stream-only OBS host/port, vault `obs-password`, Grafana URL | Import only into Stream capability settings; verify vault access with the chosen new identity; retain original namespace for rollback. |
| Creator-only MinIO endpoint/vault keys and Blender/Krita paths | Import into Content capability settings; missing credentials require reconnecting; never serialize them into previews or backups. |
| Remote tokens, stable device IDs, auto-connect and product identity | Keep public settings separate from vault entries. Explicit adoption/re-pairing, v1/v2 negotiation and session shutdown must precede identity migration. |
| Readiness observations, setup selection and shared environments | Reuse the shared installer/environment roots; capability evidence expires normally. Imported selection does not prove a running service or physical acceptance. |
| Recording ledger, social catalog and distinct selections | Reuse locked shared stores without copying video or rewriting their schemas in the first slice. Pin the active session destination independently of Content selection. |
| Stream OBS cache/session and Creator render runtime | Create one owner for each domain; navigation must not mount a second controller or discard an owned session. Legacy/unified concurrent writers require admission checks. |
| Declared capabilities | Both declare `module-setup:default` and `social-manager:default` for `main`; Creator additionally declares `core:default` and `dialog:default`. Both CSP values are null. Audit a minimum combined grant set and content policy; copying the union is not a completed security review. |

#### Measured baseline and remaining measurements

This workstation reports **macOS 26.6.2, ARM64**. Four existing local DMGs were hashed in place
without launching or rebuilding them. These measurements identify those files only: their build
commits, signatures, install time and clean-host provenance were not established in this pass.

| Existing file | Bytes | SHA-256 |
|---|---:|---|
| Stream `target/release/bundle/dmg/Stream Extend_0.1.0_aarch64.dmg` | 7,130,199 | `0eda08c5603d710275cc56cf3ce1729f84bb6c57a51b827cf18394d4bbd26b2c` |
| Creator `target/release/bundle/dmg/Creator Extend_0.1.0_aarch64.dmg` | 7,116,763 | `992717c27d4a93f2dc2036646983ce564ab749521c57e8102c6f4e065a927da7` |
| Stream `target/debug/bundle/dmg/Stream Extend_0.1.0_aarch64.dmg` | 17,380,392 | `c2e5e8124ebdac40606f1aacd4ffbc7542ba4aa6beea5fff34deafe370fd7e87` |
| Creator `target/debug/bundle/dmg/Creator Extend_0.1.0_aarch64.dmg` | 17,370,859 | `a10931ed78f1090d6a05e0bff60c45e9e96c1f73bbd8dd961b8d7d7361b0f062` |

Release DMGs total 14,246,962 bytes; this is the sum of two existing compressed downloads,
not a forecast of combined size. Do not compare debug bytes with future release bytes.
The existing private installer workflow targets Windows x64; local files above are macOS ARM64.
Neither establishes the owner-approved public support matrix (PL-D02/PL-D10).

Startup and resource measurement is still open. For each fresh artifact/target, record hash and
build commit, clean-host prerequisites/network state, install actions/time, launch-to-usable-setup
time (five cold trials), idle process count/RSS after 60 seconds, then task actions/time to a
verified stream recording and content output. Repeat Stream-only, Create-only and both selections
on the same machine/settings. Before contention tests, PL-D10 must select numerical limits for
startup, RAM, package size, stop/mute latency and OBS rendering/encoding lag. No unmeasured budget
is silently treated as passed; this inventory is not a finished performance baseline.

#### Five convergence gates: none closed by this pass

| Roadmap gate | Current evidence / next proof |
|---|---|
| 1. Both desktop journeys accepted | Partial: builds, synthetic/loopback and some Mac workflows recorded. ST-R05 and CT-R01/CT-R15 still require full physical/account/output evidence. |
| 2. Shared contracts without product forks | Partial: shared crates/components exist, but connection DTOs, native probes/controllers and relay product identity differ. The command/migration map above identifies the contracts to reconcile and test. |
| 3. Three real cross-product workflows | Open: recording → reviewed MP4 (CT-R15), generated graphic → visible OBS overlay (ST-T17), and recording → selected Content account → approved private upload (CT-R16). CLI/synthetic output is not these full journeys. |
| 4. Real two-device relay/approval | Open: ST-R14 is still required. One-machine loopback does not close it. |
| 5. Packaging improves first run/switching | Open: concept interactions exist; no combined artifact or comparative clean-host task measurement. PL-D10 baseline/budgets and native single-pack evidence are required. |

Recommended next execution order: restore the local OBS baseline (ST-R01), finish the existing
Stream/Content acceptance journeys, obtain two-device approval evidence, then review PL-D10 and
PL-D13 against this inventory. Public identity/commercial/cloud decisions remain later, separate
gates. Source/planning progress does not close P-072 or its native acceptance rows.

**Verification:** required `make test` reached 100%, exit 0
(`/tmp/hcp-accepted-final.log`); generated documentation is synchronized; proposal/lane report
has zero missing/extra IDs; Ruff and `git diff --check` pass. Source command counts and all four
local DMG byte/hash observations were read directly. Startup/resource benchmarks, native
convergence workflows and two-device acceptance were not run. Native OBS inspection was
attempted but the UI tool reported the Mac locked; manual unlock is required to continue.

**Actors:** a new recipient installing the software; a creator who streams and edits; an existing
user upgrading either/both apps; later, an invited reviewer using a browser; the operator supporting
installations and optional hosting.

**Goals:** one download choice per supported OS/architecture, one installation and app launch,
zero cloud sign-ins for local features, one shared setup history, and zero app switches to move a
finished stream recording into the content workflow. Keep independent Stream and Content account
selections visible so a workspace switch never silently changes a live destination.

Measure clean-host time/actions to the setup window, time/actions to first verified stream and
content output, package/download size, idle RAM, cold start and background processes. Compare
Stream-only, Create-only and combined selections with today's separate-app baselines. At Phase 0,
record hardware and numerical performance budgets before evaluating the merged build. No speed or
size improvement is claimed without that comparison.

**Non-goals:** implementing unfinished module features merely because their tabs move; renaming
every public surface; deciding new commercial terms; bundling all models/DCC tools in the installer;
merging module implementations; requiring Docker for the initial window; introducing Kubernetes or
distributed workers; moving live capture/inference into the cloud; building a new browser editor or
mobile app in the desktop consolidation phase.

## 4. User paths and states

| Path | Proposed behavior and recovery |
|---|---|
| First run | Open guided Home with no OBS, Python, Docker, models or cloud credentials. Choose Stream, Create or both; follow only the next required setup step, inspect optional installs and skip any unavailable step. Preserve P-063's bundled guides and restart recovery. |
| Normal streaming → creation | Run an owned OBS session, stop and finalize its recording, then open that same library item in Create. Carry source profile, content profile and provenance; do not auto-publish or duplicate the media. |
| Stream-only / Create-only | Show the chosen workspace first; keep the other discoverable through capabilities/settings. Lazy-load its UI and start no unused runtime merely because the app contains its code. |
| Missing dependency / service failure | Report the affected capability, offer its setup/retry path, and keep the rest of the app usable. Missing ComfyUI must not block OBS control; an OBS failure must not block content browsing. |
| Invalid input | Native handlers reject invalid endpoints, paths, unsupported schemas and unknown actions before side effects. Show a field-specific correction; preserve the last valid state. |
| Local offline / cloud outage | Installed local capabilities continue. Cloud status is unavailable/stale with a timestamp. A workstation that is asleep or offline cannot execute remote actions; never show a queued action as completed. |
| Retry | Deduplicate migration steps, installs and remote request IDs. Inspect known job status before resubmitting after a timeout; do not repeat stream toggles, uploads or paid renders blindly. |
| Cancel / disable capability | Cancel only the owned job. Ask the operator to stop/drain an active stream or render before disabling its workspace. Preserve external OBS recordings and shared dependencies used by other modules. |
| Upgrade from one/both apps | Preview detected settings and conflicts; copy into the new namespace atomically, retain originals, reuse shared module environments/library, and migrate secrets through the OS vault. Missing secrets require reconnecting, not plaintext export. |
| Relaunch after crash | Recover journaled migration/setup steps, reconcile external job/session state, keep unknown outcomes explicit, and leave stale remote approvals expired. Never infer recording ownership from “OBS is recording.” |
| Later browser use | Show desktop availability, last-seen time and capabilities. Read-only viewing requires a scoped account; remote execution still requires target-side approval. Review an uploaded proxy, not a workstation path. |

## 5. Architecture and data flow

### Beginner navigation direction — owner refinement, 2026-10-05

The owner wants one app that a beginner can understand, with few controls on the main pages
and module groups/folders exposing additional tools through navigation and configuration.
The owner named MYFeed and OpenTechApp as references. This refines P-072's authorized planning;
the combined shell and all proposed UI below remain implementation-gated.

**Source comparison (code inspection, not a new usability study):**

| Reference inspected | Useful pattern | Carry into the combined app |
|---|---|---|
| MYFeed working checkout based on `b2ff1c2` (the inspected UI includes uncommitted changes): `src/App.tsx`, `src/components/FeedReader.tsx`, `SettingsPage.tsx`, `SettingsContent.tsx` | A clear reading view, separate Customize mode, named sidebar entries, Connections and grouped app settings; workspace details expand inside Settings | Everyday work stays on the workspace page; setup/customization opens in context or Settings. Keep labels for beginners and remember the selected workspace |
| OpenTechnologyApp `752b972`: `src/components/Sidebar.tsx`, `sidebar/SidebarRail.tsx`, `SidebarDrawerToolbar.tsx`, `SidebarFolderTree.tsx`, `SidebarProjectNavigation.tsx` | Persistent quick-access rail; drawer for navigation; expandable folders and project sections; Settings remains grouped management even where quick shortcuts exist | Shallow navigation groups and optional compact rail; don't duplicate the same toolbar across rail, drawer and content |
| Current Extend apps: both `src/routes/+page.svelte`, shared `ModuleSetup.svelte`, `RecordingLibrary.svelte` | Six peer tabs per app, a flat module chooser, technical prerequisite/endpoint controls and an existing recording inbox | Preserve native safety/readiness, profile routes and shared data; reorganize discovery around tasks and progressively disclose configuration |

The directory named `OpenTechApp` contains marketing SVG illustrations; the working application
reference is the separate `OpenTechnologyApp` checkout. Reference repositories are read-only:
no code, workspace data, account information or credentials are copied into this platform.

**Current strengths:** shared setup, local operation, recording handoff and a working Shorts CLI
provide useful building blocks. **Current friction for a beginner:** module/package names,
service endpoints, optional ComfyUI/Docker prerequisites and automation compete with the first
recording task. Combining binaries alone does not resolve that learning path.

#### Recommended default: labelled folders and a guided Home

Use five navigation entries: **Home**, **Stream**, **Create**, **Library**, **Settings**. Home is
a page; the other entries expand to shallow task pages. Help remains easy to find. Keep one
group plus one leaf level in the default hierarchy; arbitrary user-defined nesting is a later
usability decision, not part of the first preview. These are UI groups, not new roadmap modules,
filesystem folders, authorization roles or reasons to duplicate module code.

| Navigation | Task pages / controls | Configuration belongs in |
|---|---|---|
| Home | One current next step; at most three prominent task actions, with one primary: Check setup, Practice recording, Make a clip. Completed setup changes the primary action; unrelated missing tools create no global red dashboard | Contextual guided setup, with an explicit link to the same Settings page |
| Stream | Preview & sound, Scenes; enabled Soundboard/overlays and optional Host/avatar/automation pages | Stream customization; camera/mic/account routing, OBS endpoints, encoder details and hotkey bindings in Settings/context panels |
| Create | Make a clip first; enabled image/thumbnail, Blender/scene-asset and sports-analysis pages | Per-job editing controls stay with the job; model/node/provider configuration belongs in Settings |
| Library | Recordings and exported clips, with source/content profile and processing state visible | Storage location, retention and optional backups in Settings; browsing local recordings never requires Docker/cloud |
| Settings | Guided setup; Profiles & accounts; Enabled tools; Advanced connections, services and diagnostics | The full catalog and technical configuration live here, grouped and searchable in the later implementation, rather than as top-level workspace buttons |

Recommend **Guided folders** for first use. **Compact rail** is an optional presentation for
someone already familiar with the tasks: a short labelled/accessible rail opens the same folder
tree. Both layouts expose the same capabilities and readiness rules. Keep layout preference
separate from feature enablement; a hidden navigation item does not revoke or grant permissions.
Settings must allow discovering and enabling optional tools without requiring a second installer.

#### Module groups for discovery, not backend boundaries

| Enabled-tools group | Existing modules surfaced or depended on |
|---|---|
| Streaming basics | `creator-experience`, `audio-production`, `soundboard` |
| Looks, overlays and avatars | `realtime-ai`, `broadcast-graphics`, `character-avatar` |
| Hosts and automation | `ai-agents`, `automation-control` |
| Clips and creative editing | `content-creation`, `image-editing` |
| Sports and motion | `sports-analytics` |
| Landscape and city assets | `nature-generation`, `cityscape-generation` — learned tiers retain their Pending gates |
| Accounts and promotion | `social-management`; `marketing-crosswalk` is identified as a repository CLI, not a shipped desktop page |
| Shared foundations and diagnostics | `storage-data`, `asset-pipeline`, `model-registry`, `backend-api`, `observability`, `infrastructure` |

Every module appears once in the discovery mapping; shared services are dependency-resolved
from selected capabilities. Basic OBS control/local recording and CPU clip work must not require
enabling Docker, generative AI, a cloud account, avatars or unattended automation. Dependency
checks remain installed/running/connected/verified, with the module's real evidence and status.
Navigation visibility never promotes a scaffolded capability or authorizes a Pending proposal.

#### Beginner task and live-safety contract

The first path is **choose streaming/creation goals → picture and microphone checks → short
off-air recording → review → make a clip**. Ask for only the inputs used by the next step;
show advanced values behind labelled configuration sections, with plain-language recovery for a
missing microphone, unavailable OBS or interrupted job. Account sign-in is needed for an external
broadcast, not for a local practice recording. Beginner and advanced presentation share the same
native validation and explicit final account/destination review.

When live, preserve an always-visible session strip across Home, Create, Library and Settings:
live destination/profile, recording ownership/state, microphone mute, Mark moment and End stream.
Critical stop/mute and failure/approval notices are never buried in collapsed folders, an overflow
menu or Advanced mode. Stream and Content profile selections remain separate; changing a Create
view does not change the pinned live destination or stop the owned recording. Mark moment is a
proposed marker action requiring its own real event/time mapping; it is not present today.

The primary cross-workspace product journey is the existing recording inbox into an actual
review/trim/export adapter for `stream_shorts`. Today's Start editing changes metadata only;
the combined app must not claim editing from that flag. Preserve the local original, reviewable
intervals, source/profile provenance and approved content destination. Heavy exports remain
deferred during live work by the resource policy; reviewing a cut never auto-publishes it.

#### Proposed UI injection and acceptance

Add proposed `configs/ui/combined-navigation.json` for stable group/page IDs, user labels,
module/capability mapping and default presentation. Proposed shared `Navigation.svelte` and
`Home.svelte`, plus `apps/extend/src/routes/+layout.svelte`, consume it through the existing
typed desktop adapter/session manager. Existing settings/setup/recording components provide the
underlying contracts; the clip page adapts the existing Content Creation CLI after that slice
is authorized. No new native command is authorized by a navigation configuration.

Extend U-01/U-02/U-07/U-09 with: first-run novice task completion and recovery without exposing
all modules; no more than three prominent Home task actions; single-pack operation without
unrelated readiness warnings; keyboard/touch folder access and usable labels at narrow widths;
enabled-tool discovery and disabled/planned states; navigation changes during a live session
preserving the pinned route, recording and visible stop/mute controls; and a real recording
becoming a reviewed cut and verified MP4, rather than an editing-status change.
The existing ST-T14/ST-T16 and CT-R15 lane items own those native/user acceptance repeats.
Usability is not proven by this source comparison or the isolated concept preview.

Planning verification is recorded at the end of §9 after the local documentation checks.

### Desktop shape

Propose `apps/extend/` as an internal source path, not an approved public brand. Build one Tauri
core and shell with workspace components extracted from the two current pages. Keep OBS, ComfyUI,
Blender, Krita, FFmpeg and speech/avatar workers in their existing local execution boundaries;
the shell orchestrates them. Do not run heavy work on the UI thread or promise that a shared core
cannot crash. Preserve direct OBS access and independent module CLIs as recovery paths.

Shared Home, Library and Settings surround Stream/Create workspaces. Profiles remain visible in
workspace context and managed in Settings; enabled Remote controls and setup use grouped navigation,
with critical approval/status notices available across pages.
An app-owned session manager retains streaming, recording and job state across navigation;
component unmounting cannot stop an active stream, reset ownership or leak polling listeners.
Commands belong to domains (`stream`, `content`, `settings`, `remote`) behind a shared typed
frontend adapter, with native validation independent of UI visibility.

```text
Packaged desktop UI → native validated commands → existing local tools/modules
                              ↓
                  shared settings, profiles, library, readiness

Optional browser → authenticated cloud API/relay → approved local command
                      ↓                              ↓
              opted-in metadata/proxies        workstation execution

Optional batch submission → private asset storage → one approved batch executor
                                                   → reviewed output
```

Live capture/rendering remains local. Local-first does not mean offline streaming to an external
platform; it means the app's core operation has no dependency on our cloud service.

### Cloud feature scope

Difficulty is a relative engineering assessment, not an estimate of elapsed time or a claim that
deployment is complete. Hosting existing APIs privately is less work than operating a public
multi-tenant product. A cloud-hosted download page can distribute the desktop immediately without
turning the software into a cloud runtime.

| Feature | Execution/data location | Suggested stage | Difficulty / main remaining work |
|---|---|---|---|
| Downloads, guides, release notes, workflow catalog metadata | Web hosting; local installer/runtime | Alongside desktop release | Low relative to runtime migration; artifact integrity, signing, support and truthful readiness still required. |
| Readiness, job status, last-seen and stream metrics dashboard | Optional sanitized metadata in cloud; probes on desktop | C1 companion MVP | Moderate: authenticated web UI, tenant scope, stale-state semantics, retention and hosted acceptance. |
| Content calendar, episode plans, scripts and publishing drafts | Local by default; opted-in documents in cloud | C1 | Moderate: document IDs, version conflicts, permissions and actual persisted plans. Scheduling a draft must not launch a local show. |
| Selected preset/workflow/profile sync | Cloud metadata; machine-specific endpoints stay local | C2 | Moderate: allowlisted fields and conflict UI. Never sync tokens, private file paths or hardware mappings as portable settings. |
| Recording/asset review and comments | Explicitly uploaded thumbnails/proxies in private object storage | C2 | Moderate–high: resumable uploads, access control, codecs, quotas, deletion and review links. Large recordings make upload/storage/egress a real cost. |
| Notifications | Local notifications first; cloud delivery after opt-in | C2 | Moderate: provider implementations/credentials, consent, delivery receipts and duplicate suppression; current push helpers are unfinished. |
| Remote scene/workflow controls | Cloud relays bounded messages; desktop approves and executes | C2 | High: capability-aware protocol, identity migration, revocation and real two-device acceptance. No public OBS/ComfyUI port. |
| Social review/approval and scheduled publishing | Drafts can be web-based; execution initially stays with local approved adapters | C2 review, C3 hosted publishing | High for unattended publishing: provider OAuth, server-side token custody, account routing, retry/idempotency and separate exact-job authorization. It will not run while the desktop sleeps unless a hosted adapter is built. |
| Backups of selected assets/project metadata | Private object storage, opt-in from desktop | C2 | Moderate–high: restore tests, checksums, retention, quotas and deletion; exclude credentials and licensed model weights by default. |
| Transcription, captions, Shorts exports, grading and other file jobs | Existing local path first; uploaded inputs processed in a cloud job | C3 | High: durable jobs, cancellation, deterministic manifests, privacy, cost caps and output download. Reuse module APIs/CLIs. |
| ComfyUI batch generation and headless Blender rendering | Opt-in GPU/CPU burst executor with explicit assets/models | C3 | High: hardware/model compatibility, model rights, reproducible tool versions, transfer time and spend limits. One executor first; no worker fleet. |
| OBS capture, live audio routing, soundboard, realtime effects/CV, game input, avatar playback | Creator workstation | Desktop only in this proposal | A full cloud substitute would require media transport, device/input/audio redesign and a different latency/reliability contract. |
| Interactive Krita/Blender/DaVinci editing | Installed desktop tools | Desktop only in this proposal | Remote desktop or a new web editor would be another product; do not promise feature parity from hosting the current Svelte UI. |

**C1 excludes:** remote execution, media upload, publishing, team collaboration, GPU provisioning
and billing. Start with one authenticated user/tenant; isolation tests still precede any external
accounts. C2/C3 need separately accepted queue items and updated operating-cost estimates. The
current product spec's prices and cloud feature list are assumptions, not a budget for this scope.

## 6. Direct injection map

All new paths/symbols below are Proposed. Existing modules keep their own ownership and setup docs.

| Location | Symbol/route/component | Before | Proposed change | Example | Verification |
|---|---|---|---|---|---|
| Both `apps/*/src/routes/+page.svelte`; new `apps/extend/src/routes/+page.svelte` | `activeView`, lifecycle polling, shared UI imports | Two root pages | Extract Stream/Create views, one navigation shell and session manager | Switch to Library during a live session | Navigation/unmount tests and native active-session pass |
| Both `src-tauri/src/lib.rs`; new `apps/extend/src-tauri/src/lib.rs` | `run`, `get_config`, `set_config`, `obs_start_stream_session`, `recordings_list`, `comfyui_queue_configured` | Separate registrations with overlapping names | One registration per domain; adapt existing handlers without changing their safety contracts | Domain-specific settings DTOs under one shell | Both app contract suites plus merged command tests |
| `apps/shared/ui/`; proposed `apps/shared/api-client/` | Shared components; new `DesktopServices` interface | Components invoke native commands directly | Isolate desktop transport from view models; any future browser adapter returns explicit unavailable capabilities | `stream.startSession` and `content.queueWorkflow` | Type checks; no native import in browser build |
| `configs/setup/`; `apps/shared/setup-engine/`, `setup-wizard/` | Product manifests, `SetupEngine::new` | Separate product selections/evidence | Versioned union manifest, per-capability selection, reuse setup locking; invalidate old observations when necessary | `enabled_packs: ["Stream", "Content"]` | Select/skip/retry/restart plus stale-evidence tests |
| Both `connection_settings.rs`; `apps/shared/local-settings/`; new `apps/extend/src-tauri/src/migration.rs` | `ConnectionPersistence`, `LocalSettings`, `OsCredentials` | Product-qualified files/secrets | Idempotent migration journal, conflict preview, separate original backups | Two different ComfyUI endpoints remain unresolved until selected | Crash/failure injection and real OS-vault migration |
| `apps/shared/recording-library/`, `social-manager/`; Stream session handlers | `RecordingLibrary`, `ActiveSelection`, session ownership | Shared files already in use | Reuse ledger and independent profile selections; unify display only | Finalized path opens in Create with source profile intact | P-065 contracts and playable recording acceptance |
| `apps/shared/relay-client/src/lib.rs`, `control.rs`; `cloud/relay-api/app/routers/relay.py`; `apps/shared/ui/RemoteControl.svelte` | `Product`, `DevicePresence`, `validate_command`, `_validate_relay_message` | Product enum/filter and action lists | Versioned capability discovery and server/client negotiation; retain bounded action validation and local approval | New peer advertises OBS and Comfy capabilities | Legacy/new relay matrix, isolation, denial, expiry and two-device action |
| Both `src-tauri/capabilities/`, `tauri.conf.json`, `build.rs`; new shell equivalents | IPC/plugin grants, CSP, resources, bundle ID | Separate privileges/resources | Audit minimum grants per surface; no wildcard union; bundle required guides/templates and enforce tested CSP | Only native UI may invoke local tool commands | Permission negatives, resource checks, packaged runtime pass |
| `.github/workflows/desktop-installers.yml`, `.github/workflows/ci.yml`; `tests/desktop_apps/` | Build matrix and installer contracts | Two product artifacts | Add combined prerelease target, retain legacy checks until retirement | One installer per supported OS/arch | Clean-host install, upgrade, rollback and signatures |
| `cloud/relay-api/app/routers/sync.py`, `metrics.py`, `notifications.py`; future companion UI path selected in C1 | Existing routers; new sanitized view contracts | API building blocks, unfinished push delivery | C1/C2 follow-ups expose only reviewed schemas; do not publish generic native commands | Versioned status DTO with observation time | Hosted tenant/auth/staleness tests before release |

## 7. Contracts and examples

### Local workspace configuration and migration

Example new non-secret shell document; values are illustrative:

```json
{
  "schema_version": 1,
  "enabled_packs": ["Stream", "Content"],
  "active_workspace": "stream",
  "cloud_enabled": false,
  "background_jobs_during_live": "defer",
  "migration": {
    "version": 1,
    "sources": ["com.streamextend.app", "com.creatorextend.app"],
    "state": "needs_review"
  }
}
```

Retain independent profile selections in the existing social contract. Reuse the shared recording
ledger without changing its schema in the first consolidation slice. Snapshot only metadata,
not media. No secret appears in migration previews, backups, logs or browser DTOs.

Migration states: `not_started → needs_review → applying → verified`; any failure becomes
`recoverable_error`. Validate source schema and current session state first. Missing one legacy
app is normal; unsupported/newer schemas block only import. Merge non-conflicting values, require
an explicit choice for conflicting endpoints/accounts, verify new OS-vault entries before marking
success, and retain old entries through rollback support. Interrupted work resumes by journal ID.
The migration must not run while legacy apps are writing settings or controlling a session.

Representative errors: `DEPENDENCY_MISSING`, `SETTINGS_CONFLICT`, `MIGRATION_INCOMPLETE`,
`CAPABILITY_DISABLED`, `LIVE_SESSION_BUSY`, `REMOTE_OFFLINE`, `PROTOCOL_UNSUPPORTED`,
`APPROVAL_EXPIRED`, `JOB_OUTCOME_UNKNOWN`. Native commands enforce these regardless of selected tab.

### Relay compatibility

Proposed version-2 discovery, **not accepted by today's protocol**:

```json
{
  "protocol_version": 2,
  "device_id": "paired-workstation-id",
  "capabilities": ["obs-control", "comfy-workflows"],
  "observed_at": "2026-10-04T12:00:00Z"
}
```

Capability presence supports discovery, not authorization. The authenticated session binds device
and tenant; the workstation revalidates readiness, action, profile/account, request expiry and local
approval immediately before execution. Preserve existing payload/message/queue bounds. Do not add
a new `Product` value without coordinated client/server rollout and a protocol negotiation test.
Unsupported peers receive an upgrade-required state; never silently widen either legacy app's
allowlist. Remote capability migration must pass before the combined app replaces either product.

New-device identity adoption or re-pairing must be explicit; do not reuse two legacy device IDs
concurrently or overwrite their tokens. Old peers retain their v1 discovery/control during the
compatibility window, with no implication that they can discover a v2 combined device.

### Cloud boundaries

Use opaque asset/job IDs, observed timestamps, revision checks and scoped tenant authorization in
cloud contracts. Local path references stay local. An uploaded proxy has separate consent, size,
checksum, retention and access policy; deleting a cloud proxy never deletes its local original.
Cloud batch manifests pin input hashes, workflow/tool/model versions, output destination and maximum
spend. Timeout yields an unknown/pending outcome until reconciled, not an automatic duplicate job.
Full HTTP/job schemas and storage migrations belong to separately accepted C1–C3 proposals.

## 8. Security, privacy, accessibility, and observability

- Keep secrets in the OS vault; treat bundled UI, external web content, local services and cloud
  sessions as different trust boundaries. Loading a cloud page into the desktop does not grant it
  native privileges. Tauri warns that overlapping window capabilities combine permissions; audit
  the merged grants explicitly. [Tauri capabilities](https://v2.tauri.app/security/capabilities/).
- Cloud sync is opt-in and field-allowlisted. Do not send recordings, prompts, account tokens or
  machine paths by default. Cloud retention/deletion and backup expiry must be stated before C1/C2
  release; public sharing links, if later added, expire and can be revoked.
- Private self-hosting uses Tailscale; hosted public endpoints require TLS and an authenticated
  application boundary. Keep OBS, ComfyUI, databases, admin views and local control ports private.
  Tenant checks apply to every asset/job/document ID; a storage prefix alone is not access control.
- Preserve per-action remote approval and social publishing gates. Revocation blocks new actions;
  stale approvals cannot replay after restart. No arbitrary shell or filesystem API is exposed.
- Use keyboard-accessible workspace switching, predictable focus, readable busy/error states and
  screen-reader labels. Always show the active profile and whether a destination is local/cloud.
- Record redacted migration version/results, readiness age, startup timing, owned job IDs and
  command outcomes locally. Cloud metrics are opt-in. Never log bearer tokens, full media paths or
  sensitive prompt content. Alert on repeated migration failures and unknown remote/job outcomes.

## 9. Test and pressure matrix

These are required future implementation checks; none is claimed as completed by writing this doc.

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| U-01 | Clean macOS/Windows, no developer tools or optional dependencies, no network | Installer opens usable setup; missing steps can be skipped and retried | Native clean-host | Preview and replacement |
| U-02 | Stream-only, Create-only, both; enable second pack later | No duplicate install or unrelated background processes; persisted selection | Rust/UI + native | Preview |
| U-03 | Import neither, either or both legacy apps; conflicting/corrupt/newer schema; locked vault; disk full; kill mid-write | No original loss, no secret leak, explicit conflicts, repeatable recovery | Fixtures/fault injection + real vault on both OSes | Upgrade |
| U-04 | Live stream while switching workspace; recording pre-exists or stream start fails | Session retained; only owned recording stopped; playable handoff without duplicate bytes | Existing fake-OBS tests + real picture/audio recording | Replacement |
| U-05 | Long ComfyUI/Blender job during OBS; low disk/memory; worker crash | Default defers new heavy batch jobs during live work; responsive Stop controls; unaffected modules continue | Stress/native, measured against Phase 0 budgets | Replacement |
| U-06 | Cancel/retry/restart setup and jobs; two legacy apps still installed | Shared locks work; no double controller, partial migration or destructive cleanup | Integration/native | Replacement |
| U-07 | Disabled capability, crafted invoke, untrusted preview or remote origin | Native validation denies unauthorized operation; no expanded wildcard privileges | Rust/security/UI | Preview and replacement |
| U-08 | Legacy/new relay combinations, wrong tenant/device, spoofed capabilities, duplicate or stale approval | Fail closed; correct correlated result; explicit unsupported state; approved action runs once | Loopback + hosted real two-device | Replacement for remote parity |
| U-09 | Three cross-workspace journeys | (1) recording → reviewed Shorts draft; (2) generated graphic → OBS overlay; (3) recording → Content profile → approved private publishing test | Real workflow evidence, dependencies in their existing proposals | Roadmap convergence |
| U-10 | Expired cloud session, desktop asleep, reconnect, stale status, conflicting document edits | Local operation continues; browser shows actual availability; no silent overwrite or queued-as-complete result | API/UI + hosted | C1/C2 only |
| U-11 | Proxy upload interrupted; quota exceeded; wrong-tenant download; delete/restore | Bounded resume, authorization, correct retention and original preserved | Integration/storage | C2 only |
| U-12 | Batch executor lost, duplicate submit, cost ceiling, cancellation, model/version mismatch | Durable outcome, no duplicate charge/work, hard admission budget, verifiable artifact | Job contracts + real small batch | C3 only |
| U-13 | Install combined update, then rollback; uninstall either legacy app | Shared environments, settings and recordings survive; incompatible state is not silently restored | Native both OSes | Public release |

Use the existing [verification matrix](../agent/VERIFICATION-MATRIX.md) row **Docs only** for this change, plus an explicit check that the queue and detailed
proposal carry the same model/effort/rationale. Future implementation inherits the rows for
P-003 settings/readiness, P-063 launch/setup, P-065 recordings/profiles, P-058 remote control and
Creator workflow inputs, plus each affected module's [acceptance checklist](../../tests/ACCEPTANCE-CHECKLIST.md).

Required implementation commands include `make test`; `npm run check` and `npm run build` in
each retained app and the new shell; `cargo test --locked --manifest-path <crate>/Cargo.toml` for
the affected apps/shared crates; and Python Ruff for any Python changes. Record actual counts,
native artifact hashes/OS and workflow outputs. A build or empty window does not satisfy U-04/U-09.

**Proposal verification — 2026-10-04:** the initial shared-checkout drafting pass recorded
19,849 documentation tests and a successful offline suite. That checkout also contained unrelated
uncommitted work. The publishable branch is based on `origin/main` at `1072ec6` and carries only
P-072 and its required documentation/index updates. On that isolated branch,
`PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test`
reached **100%, exit 0**. An explicit check resolved **192 local links/fragments across eight
changed documents**, including this new proposal, and verified matching model assignments, all
13 template sections and well-formed lane tables. `git diff --check` passed.
No merged binary, cloud deployment, native migration or performance benchmark was run.

**Beginner navigation planning verification — 2026-10-05:** inspected MYFeed's working UI
(based on `b2ff1c2`, with uncommitted changes) and clean OpenTechnologyApp `752b972`; reference
directories remained read-only. Produced an isolated two-layout concept using sample state,
with no native commands, workspace/provider APIs, camera access or external actions. Browser
checks passed guided setup → recording → cut review, interval updates, enabled-tool navigation,
live stop/mute across Create/Settings, safe state restoration, variant/drawer interactions and
1100/736/360/320px widths; screenshots were visually inspected. Existing UI/lane ownership and
all 21 module mappings were checked. Documentation/queue verification results are recorded
in the P-072 row after the local offline run. No combined application or beginner usability
acceptance is claimed; implementation gates, account routes and module statuses remain unchanged.

## 10. Delivery plan

| Phase | Deliverable / owner | Dependencies and gate |
|---|---|---|
| 0 — Baseline and contract | Owner + agent inventory every currently exposed workflow as verified/partial/planned, measure install/startup costs, map settings/commands/permissions and decide support targets | Planning is authorized now. Track unresolved live evidence under P-003/P-057/P-058/P-062/P-063/P-065 and release work under P-001. Record the five roadmap gates with links to evidence before approving the implementation slice; no assumption they already pass. |
| 1 — Shared shell preview | Agent implements one setup/navigation/profile/library shell and transports the two workspace views; owner evaluates simpler first run | Gate review and queue authorization for implementation; preserve old apps. Acceptance: U-01/U-02/U-07 plus both existing app checks. |
| 2 — Parity and migration | Agent resolves command/settings/relay identities, credential migration, session lifecycle, capability admission and resource policy | Owner-chosen bundle identity, rollback contract, real OS-vault/device access. Pass U-03–U-09; do not hide missing capabilities to claim parity. |
| 3 — Distributable desktop | Release owner produces signed platform artifacts, one download/install guide, migration notes, support diagnostics and a tested update path | P-001/P-063 release prerequisites; native clean-machine install and U-13. Retire old downloads only after the compatibility period and owner release decision. |
| C1 — Optional web companion | Separate proposal: authenticated status/metrics and opted-in planning/drafts | Stable desktop DTO/adapter contract, hosting/auth/tenant acceptance, retention and budget. No runtime migration prerequisite for desktop shipping. |
| C2 — Sync, review and remote actions | Separate proposals: conflict-safe sync, proxies/comments/backups, real notifications and approved remote actions | C1 plus provider/storage/two-device evidence, permission model and per-feature opt-in. |
| C3 — Cloud batch and publishing | Separate proposals for bounded rendering/transcription/export and any server-side publishing | Working single-node module path, provider/token/model rights review, durable job/cancel semantics, quotas and measured cost. |

Relative scope: shared shell is **medium**; production migration/distribution is **large**; a
companion is **medium-to-large**; public batch/publishing services are **large**; complete cloud
replacement is **very large and excluded**. These are planning judgments, not time commitments.
Re-estimate after Phase 0; consolidation must not wait for optional cloud features.

## 11. Rollout and rollback

Start as an opt-in combined preview beside the two existing installers. Use capability flags,
retain shared schemas initially, and reject concurrent legacy/unified control of an owned session.
App updates occur outside active broadcasts/renders; rollback never blindly kills an external job.
Keep legacy installers and original settings/vault entries for at least one explicitly documented
stable-release compatibility window. Preview support duration is set before broad distribution.

Rollback triggers include lost profiles/credentials, recording ownership regressions, setup failure,
remote privilege expansion or measured stream instability. Disable the affected capability/preview,
reconcile active jobs, then reopen the legacy app against its preserved settings. Do not overwrite
newer shared library/profile data with a stale backup; require reviewed reconciliation if a shared
schema ever changes. Uninstalling any shell must leave shared environments and user media intact.
Do not implement unattended bidirectional migration between old and new app settings.

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation / decision owner | Due |
|---|---|---|---|
| One UI becomes crowded | Distribution simplifies but daily use becomes harder | Stream/Create workspaces, capability selection, progressive setup; owner tests both single-purpose journeys | Phase 1 |
| Larger installer and dependency footprint | More downloads and failed first-run installs | Bundle shared shell/resources once; optional tools/models on demand; measure size/actions | Phase 1 |
| Settings, secrets and device migration | Lost connections or wrong remote target | Journaled import, conflict preview, native vault migration, explicit pairing, rollback tests | Before Phase 2 |
| Broader failure/permission boundary | A Creator error affects live control or exposes native actions | Domain validation, least privilege, independent workers, timeouts and session manager; document residual shared-core risk | Phase 2 |
| GPU/CPU/disk contention | Render jobs cause dropped frames or broken recordings | Default defer new heavy batch jobs during live sessions; preflight already-running jobs before stream start; measured budgets | Phase 2 |
| Wrong profile/account after switching | Content posted or streamed to the wrong destination | Persist separate Stream/Content selections and pin live-session destination; explicit final action review | Phase 2 |
| Unfinished features mistaken for parity | “One app” becomes an accidental whole-platform rewrite | Inventory accepted versus planned paths, keep statuses/evidence and existing proposal ownership | Phase 0 onward |
| Public distribution still difficult | Unsigned apps or hidden prerequisites undermine handoff | Signing/notarization as applicable, clean-machine proof, one guide and bounded diagnostics | Phase 3 |
| Name, bundle ID, existing purchases and store listings | Broken upgrades, marketing or entitlements | Owner chooses brand and upgrade policy; coordinate P-023 and unresolved licensing decisions; no price change here | Identity before Phase 2; commercial terms before Phase 3 |
| Cloud transfer, GPU and support costs | Large bills or slower results than local execution | Measure representative jobs; per-tenant quotas, hard budgets, explicit upload and batch opt-in | Before C2/C3 acceptance |
| Cloud credentials, media and team isolation | New operational/security responsibility | Separate threat review, scoped auth, private objects, deletion/restore tests and provider-specific token custody | Before each cloud release |
| Delivery scope and dates | Consolidation stalls behind optional features | Desktop replaces two downloads independently of C1–C3; estimate from Phase 0 inventory | Phase 0 |

## 13. Documentation updates

This proposal change adds the queue row, this contract, the planning exception, pointers in
the roadmap/product spec, and P-072 owner-decision/manual-run entries in `docs/todo/`. Current app names, module statuses and runtime claims remain factual.
Proposal documents are indexed by the queue under the existing documentation-index convention.

When implementation ships, update `README.md`, `AGENTS.md`/`CLAUDE.md` product/path descriptions,
`docs/architecture/product-spec.md`, `roadmap.md`, `docs/PROJECT_CROSSWALK.md`,
`docs/AUDIT.md`, `docs/agent/VERIFICATION-MATRIX.md`, `SUBFEATURE-CHECKLIST.md`,
`tests/ACCEPTANCE-CHECKLIST.md`, affected module setup guides and
`modules/infrastructure/setup/desktop-setup.md`. Preserve `Content`/`Stream` module labels as
capability labels; changing packaging does not create new roadmap layers.

Update installer/build instructions, migration/rollback support, plugin integration references and
marketing subjects/anchors in the same release. Run `marketing-crosswalk validate`/`selftest` for
those claim changes. New configs/services need their module-item/config documentation, Compose and
`.env.example` entries as applicable. Cloud proposals must revise the product spec's cloud scope
and pricing assumptions explicitly instead of treating its historical cost figures as verified.

### Native preview and final Testing handoff — 2026-10-12

The final Mac debug bundle opened through the native UI tool and was moved to the built-in
Retina display before testing. Stream-only hides Create/Library; Create-only hides Stream; both
restore all task folders. Distinct Main Stream/Main Content profile kinds, the shared existing
inbox and bundled catalog render. Missing OBS/ComfyUI produce only relevant blocked observations.
A file-scheme endpoint is rejected and the prior valid address remains saved; valid recovery
works. Keyboard selection changes layout; quit/reopen restores compact layout and selected packs.
Shared setup loads without a cloud account/Docker, with zero selected installs; no install, account,
media edit or broadcast action was run. New library edit/publish and setup sync/record controls
are hidden/denied in preview. Screenshots exposed primary-hover and embedded setup contrast
issues; both are repaired and the rebuilt native layout visually checked. Workflow engineering
notes are collapsed behind friendly task names.

20 locked Rust tests, four Node tests, Python admission/permission checks and all three frontend
checks/builds pass. Legacy/shared crates pass; the CI-derived local verifier accounts for 47
commands (30 PASS, 17 NOT RUN), exit 0. Required `make test` reaches 100%, exit 0. Preserve the
private artifact/hash report under `output/release-evidence/p072-private-preview-2026-10-12/`;
source is an uncommitted worktree, not a signed/tagged release.

U-01/U-02/U-07 still need clean hosts, narrow widths/complete keyboard recovery, vault write/lock,
crafted/foreign-origin denial and synthetic import/reveal on this preview, plus Windows. Existing
legacy shared-inbox display is not new import/reveal acceptance. Real workflows, two devices,
parity/session controls, migration, budgets and public replacement remain gated. This closed
private build slice qualifies for Testing with remaining features/delivery; P-072 is not Done.
