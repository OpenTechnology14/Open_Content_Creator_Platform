# AI actions inventory — Content Creator

> **Status:** Living · **Last reviewed:** 2026-11-10 · **Owner:** OpenTechnology14
> **Verified against:** `main` at `5cc86f3`, read from the code; the Remote control action was added after a completeness review on 2026-11-12. The desktop apps were not launched (see [Checks not run](#checks-not-run)).

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is an inventory, not a priority queue and not an authorization. A finding here is a finding to route, not a task to start.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](FUTURE_DOCS.md).

What AI-related actions the Content Creator apps have **today** (built, not proposed), where each lives, what it does for the person using it, and how to see it. Evidence uses the repository's vocabulary ([`PROPOSAL_CREATION_SOP.md`](PROPOSAL_CREATION_SOP.md)): **Verified** is observed in code or a test file that exists; **Inferred** is likely from code structure but not executed; **Proposed** does not exist yet. "Built" never means "accepted": real-account and live-stream acceptance is tracked in the [run lanes](todo/README.md), and the platform has not yet created an external post, upload or stream (`ST-R15`).

For every Tauri command, not only the AI ones, see the [API route ledger](API_ROUTE_AUDIT_LEDGER.md).

## The short answer

- **Seven AI actions are reachable from the apps today.** Three are in Creator Extend (run a ComfyUI workflow; the Posture Screen; and, from *Remote control*, request a ComfyUI workflow run on another device, which that device must approve), three are in Stream Extend's *Automated streaming* tab (the production runtime that starts the AI host, Personalities prompt and voice preview, and the avatar cues it owns), and one is read-only in the Extend preview (the workflow list).
- **They are all local-first.** They use services you run (ComfyUI, Ollama) and local models (MediaPipe). I found no code that calls a hosted AI API: nothing in `apps/`, `modules/`, `cloud/` or `scripts/` calls an OpenAI, Anthropic or ElevenLabs endpoint.
- **Three AI-capable backend commands have no screen** (`comfyui_queue`, `comfyui_load_workflow`, `krita_run_script`). They are built and registered; nothing in the UI calls them.
- **The *Safe lifecycle rehearsal* button is not an AI action.** Its own note says it "never starts OBS streaming, gameplay, a model, voice, avatar, or chat".
- **No AI action has run on a real account or live stream.** ComfyUI output runs on a Mac are recorded ([`future-state.md`](architecture/future-state.md)); the AI host's live acceptance (`ST-R10`, `ST-R11`) is blocked.

## Built today, in the apps

| # | Action | Where to find it | What it does for you | Code | Evidence |
|---|---|---|---|---|---|
| 1 | **Run a ComfyUI workflow** | Creator Extend → Dashboard → *ComfyUI Workflows* | Lists 11 bundled workflows by category (8 image and video editing: background replace, inpaint fill, inpaint remove, outpaint expand, auto-select with SAM, 4× upscale, video frame edit, video range edit; 3 realtime: starter, LCM stylize, segmentation). *Preflight* checks the live ComfyUI for the nodes and models and shows VRAM; *Configure* opens an editor where you pick or upload an image or mask and set inputs; *Run with these inputs* queues it. The card shows Queueing, Running, then Done, with an *Output history*. | Rust `apps/creator-extend/src-tauri/src/lib.rs` 305–398 (`comfyui_*`), `comfyui.rs`; UI `src/routes/+page.svelte` 569–660, `src/lib/WorkflowInputs.svelte`; workflows in `modules/image-editing/workflows/` and `modules/realtime-ai/comfyui/workflows/`, bundled by `build.rs` | **Verified**: code; contract tests `src-tauri/tests/comfyui_contract.rs`, `workflow_inputs_contract.rs` |
| 2 | **Posture Screen** | Creator Extend → Dashboard → *Posture Screen* | You pick Front, Side or Back and upload a photo. A local MediaPipe Pose model finds body landmarks; the photo comes back with an overlay and metrics (shoulder tilt, hip tilt, forward head, trunk lean) and flags such as "shoulders uneven", or "No alignment issues flagged." | Rust `lib.rs` 578 → `posture.rs` → `modules/sports-analytics/pose-estimation/posture_screen.py` (MediaPipe, OpenCV); UI `+page.svelte` 681–770 | **Verified**: code; `tests/sports_analytics/test_pipeline_contracts.py` references it |
| 3 | **Production runtime that starts the AI host** | Stream Extend → *Automated streaming* → *Local production runtime* | Buttons: *Check production readiness*, *Start local preview*, pause, resume, *Stop runtime*, *Emergency stop*, *Verify OBS is inactive*, *Close production owner*. Under the hood the owner starts worker processes: the AI host `stream_host` (answers through a local Ollama model), `stream_director`, `stream_speech` (voice), `stream_avatar` and `twitch_chat`. Live start stays locked until broadcast is authorized in the policy. | Rust `apps/stream-extend/src-tauri/src/autopilot_control.rs` 503–532; UI `src/lib/ProductionControls.svelte` 69–95; Python `modules/automation-control/stream_autopilot/production.py` | **Verified**: that the owner can start those five workers. **Inferred**: which run in each lifecycle state. Live acceptance blocked (`ST-R10`, `ST-R11`) |
| 4 | **Avatar cues and the optional game session** | Same panel: *Owned avatar cues* buttons; *Optional private-world game setup* | Cue buttons make the avatar react on demand while the runtime is in preview or running. The setup section prepares a pinned game SDK for one permitted private Minecraft world (needs Node.js 22 or newer); only the first bounded game adapter (Minecraft) exists. | `autopilot_control.rs` `autopilot_prepare_game` 532; `ProductionControls.svelte` 92–95; `modules/automation-control/stream_autopilot/minecraft/` | **Verified**: code; `tests/automation_control/test_minecraft_adapter.py` exists. Real world run not done (`ST-R12`) |
| 5 | **Personalities: prompt and voice preview** | Stream Extend → *Automated streaming* → *Personalities — Prompt & Voice Preview* | *Load personalities*, pick one (gaming personalities only), enter the name of an installed Ollama model, *Generate personality prompt*. It returns a reviewable prompt and phrase candidates; you edit them, save a new revision, and *Render saved phrases* to audio with an installed OS voice. You audition off the program mix (OBS must be connected and off air), then *Approve revision* or *Reject revision*, map clips to hotkeys, and test them in OBS. A *Scripted show* section takes a reviewed script and episode brief and answers Q&A through Ollama. Nothing goes on air by itself. | Rust `apps/stream-extend/src-tauri/src/lib.rs` 382 (`voice_studio_request`), `voice_studio.rs`; UI `src/lib/PersonalityVoicePreview.svelte` 110–205; Python `modules/automation-control/voice_studio/`, `modules/ai-agents/stream_host/author.py` (Ollama chat), `modules/audio-production/stream_speech/` | **Verified**: code; `tests/automation_control/test_voice_studio.py`, `test_personality_bindings.py`, `tests/ai_agents/test_stream_host.py`. Owner approval of a real prompt and audio is open (`P-066`) |
| 6 | **Workflow list in the Extend preview** | Extend (combined preview) → *Create* page | Shows the same bundled ComfyUI workflow catalog when the content pack is on. It is read-only: this app has no command that queues a workflow. | `apps/extend/src-tauri/src/lib.rs` 269 (`preview_workflows`); UI `apps/extend/src/routes/+page.svelte` 90 and 114 | **Verified**: code |
| 7 | **Request a ComfyUI workflow run on another device (Remote control)** | Creator Extend → *Remote control* → *Control another device* | Pick a connected target device, type a *Committed workflow path* (a text box whose placeholder is modules/.../workflow.json), then *Request workflow run*. The request goes through the relay and waits under *Pending approvals* on the target, where a person clicks *Approve and run* or *Deny*; nothing runs until then. Stream Extend's version of the tab requests OBS actions, not workflows. | UI `apps/shared/ui/RemoteControl.svelte` 153 (*Control another device*), 175 (`queue_workflow`, *Request workflow run*), 181 and 189 (*Pending approvals*, *Approve and run*); Rust `apps/creator-extend/src-tauri/src/lib.rs` 178 (`remote_request`) | **Verified**: code. A loopback run on one Mac is recorded; the hosted relay and two real devices are not (`ST-R14`, `ST-T12`) |

### How to see each one

1. **ComfyUI:** *Connections* tab, set the ComfyUI URL and *Save and test ComfyUI*; *Module setup*, *Check readiness* (the section says "Workflow controls are locked until the current ComfyUI and committed-catalog checks pass"); then *Dashboard* → *ComfyUI Workflows* → a category tab → *Preflight* → *Configure* → *Run with these inputs*.
2. **Posture Screen:** *Dashboard* → *Posture Screen* → *Front* → *Upload Photo*. If its dependencies are missing, the Creative Tools area offers *Set up Posture Screen dependencies in Module setup*.
3. **Production runtime and cues:** Stream Extend → *Automated streaming* tab → *Local production runtime* → *Check production readiness*. *Start local preview* enables once the check reports ready.
4. **Personalities:** the same tab, scroll to *Personalities — Prompt & Voice Preview* → *Load personalities* → pick a personality → type an installed Ollama model name → *Generate personality prompt*.
5. **Extend preview:** open Extend → *Create*.
6. **Remote control:** in Creator Extend, *Remote control* → connect the relay (*Connect now*), choose a target device under *Control another device*, type a *Committed workflow path*, *Request workflow run*; on the target, *Approve and run*. It needs a relay (hosted subscription or self-hosted) and a second device on the same account.

## Built, but no screen calls it

| Command | What it would do | Code | Evidence |
|---|---|---|---|
| `comfyui_queue` | Queue a raw ComfyUI graph. The screen uses `comfyui_queue_configured` instead. | `apps/creator-extend/src-tauri/src/lib.rs` 378 | **Verified**: registered; no call in `apps/**/src` |
| `comfyui_load_workflow` | Load one bundled workflow's JSON by path. | `lib.rs` 371 | **Verified**: registered; no UI call |
| `krita_run_script` | Run a Krita script. The three in `modules/image-editing/krita/scripts/` are `apply_style.py` (style transfer through ComfyUI's IPAdapter node), `batch_upscale.py` (upscale through ComfyUI's UltimateSDUpscale node) and `export_to_minio.py`. The *Creative Tools* Krita card only opens Krita (`krita_open`). | `lib.rs` 521; `src-tauri/src/krita.rs` | **Verified**: registered; no UI call. The scripts' model use is **Verified** from their docstrings |

## AI that runs beside the apps, not behind a button

| What | What it is | Reach it by | Evidence |
|---|---|---|---|
| `modules/ai-agents/stream_host/` | The AI conversation worker: replies to chat and authors phrases through Ollama (`/api/chat`), or through an explicit offline rehearsal responder | Started by the production runtime (row 3); used by Personalities (row 5) | **Verified** |
| `modules/ai-agents/local-llm/` | A separate agent loop: read chat, retrieve memory, generate, act, with a message moderator | No app command runs it; referenced by the setup catalog and the avatar controller | **Verified**: references; **Inferred**: that it is a reference module |
| `modules/sports-analytics/` | Golf tracer and swing pose (MediaPipe, YOLO) as command-line tools; the posture analyzer in row 2 comes from here | Python command line | **Verified** |
| `modules/realtime-ai/` | Realtime face and background tools (DeepFaceLive notes, face-mesh filter, segmentation); the three realtime ComfyUI workflows in row 1 come from here | Local GPU tools, outside the apps | **Verified** |

## Not AI, so you do not look for it

*Safe lifecycle rehearsal* (Stream Extend, *Automated streaming*): it runs preflight, preview, pause, resume and stop with local state and, per its own note, starts no model, voice, avatar or chat. OBS control, the recordings library, the Blender stills job, the Social and channel tools (`modules/social-management`), remote control, and the marketing crosswalk generator (templated; no model calls found) are also not AI actions.

## Proposed, not built

| Row | What it would add | State in the queue | What it waits on |
|---|---|---|---|
| [`P-067`](proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) | Narrated app walkthroughs with an animated pet mascot, and a reactive "try not to laugh" composer | Accepted for bounded app-owned production; wider creative decisions open | The walkthrough engine and reactive composer are not built (`CT-R06`, `CT-R07`) |
| [`P-068`](proposals/PROPOSAL_LOCAL_TTS_STACK.md) | A local text-to-speech stack for the Nova persona, with a provider seam and blind audition | Pending, slices 1 to 4 listed | `CT-D03` (voice account), `CT-D04`, `CT-D06` |
| [`P-066`](proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md) | The rest of reaction audio and scripted personality routing; row 5 is its built part | In progress | Owner prompt and audio approval, OBS proof, Windows |
| [`P-056`](proposals/PROPOSAL_STREAM_AUTOPILOT.md) | Autonomous play in more games, concurrent sessions, a VRM renderer | In progress; a native production owner and the first game adapter are built | Real acceptance; no multi-host or VRM completion is claimed |
| `P-028` (queue row) | The six missing realtime ComfyUI workflows | Partially done | `CT-R13`: a GPU host and about 14 GB of downloads |
| [`P-004`](proposals/PROPOSAL_CONTENT_ASSET_GENERATION.md) | Text-to-image content asset generation | Pending | `CT-A03` (acceptance) and `CT-D14` |
| [`P-059`](proposals/PROPOSAL_NATURE_GENERATION_TIERS.md), [`P-060`](proposals/PROPOSAL_CITYSCAPE_GENERATION_TIERS.md) | Learned nature and cityscape generation tiers | Pending | `CT-A04`, `CT-A05`, `CT-D15`, `CT-D16` |
| `P-022` (queue row) | `video-generation` | Deferred | A recorded trigger |
| [`P-072`](proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md) | The combined app's Create workspace (row 6 is its preview) and optional cloud stages | In progress, private preview built | `PL-D10` to `PL-D14`, combined-app phase 2 |

## What each action needs

| Needs | Rows |
|---|---|
| A running ComfyUI with the models (URL set in *Connections*) | 1 |
| The `sports-analytics` Python environment (MediaPipe, OpenCV) | 2 |
| A local Ollama with an installed model | 3, 5 |
| OBS connected (and off air for the audition) | 3, 5 |
| An OS voice installed | 5 |
| Twitch credentials, only for real chat (`ST-R02`, `ST-R11`) | 3 |
| A permitted private Minecraft world and Node.js 22 or newer | 4 |
| A relay and a second device on the same account, with ComfyUI running on the target | 7 |

## Findings

1. **Three AI-capable commands are unreachable from the UI** (`comfyui_queue`, `comfyui_load_workflow`, `krita_run_script`). Decide whether each gets a screen or is retired; neither is urgent.
2. **The Extend preview lists workflows but cannot run them.** Running a Create workflow in the combined app is a `P-072` follow-up.
3. **The Stream Autopilot module README is stale.** It says the production driver is unimplemented; the app has one (`autopilot_control.rs`) and the queue row says so.
4. **The AI host has never spoken to a real audience.** Its acceptance rows are blocked on the Twitch developer app, the handles and the dry runs; see the creator-account audit in the run lanes.
5. **No hosted AI service is used anywhere.** If a hosted voice such as ElevenLabs is chosen, it arrives through `P-068`'s provider seam, and `CT-D03` is the decision that opens it.

## Checks not run

- The apps were not launched, so every "what it does for you" is from the code and the labels it renders, not from a session. Treat the click paths as **Inferred** until someone follows them once.
- ComfyUI, Ollama, OBS, MediaPipe's environment and Twitch were not available; nothing here was exercised against them.
- No test was re-run for this document; the repository's offline suite passes on the same commit.
- Hosted AI usage was searched for by endpoint name in non-test code; a dynamically built URL would not be found.

## How to refresh this

Re-derive the command lists with `#[tauri::command]` in each app's `src-tauri/src/`, match each name to its `invoke(` call in `src/`, and re-read the worker list in `modules/automation-control/stream_autopilot/production.py`. Update the *Verified against* commit and the row line numbers together.
