# Creator Extend — production setup

**Labels:** `Content` · Companion guide: [Stream Extend production setup](STREAM_EXTEND_PRODUCTION_SETUP.md)
**Games authority:** [`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md)
**Distribution name:** Creator Extend ships as **ContentExtend**. The `apps/creator-extend` path is
the legacy internal name and is unchanged during the repository import — see
[`docs/REPOSITORY_ALIGNMENT.md`](../../REPOSITORY_ALIGNMENT.md).

This guide takes the same MacBook Pro from a clean checkout to a published YouTube video made from
a Stream Extend recording. It assumes nothing. Every step ends with something you run or look at,
and a stated pass condition.

> **Read this first.** The repository's own verdict on what is real is
> [`docs/AUDIT.md`](../../AUDIT.md); per-module maturity is [`CLAUDE.md`](../../../CLAUDE.md) §11.
> This guide is blunt about which parts of the "AI content pipeline" exist as code and which are
> you, doing it by hand, today.

**Markers used throughout:**

| Marker | Meaning |
|---|---|
| **SHIPPED** | Code exists and offline tests cover it. You can run the step now. |
| **EXTERNAL ACCEPTANCE** | Code exists but only a live run with real accounts proves it. You are the acceptance. |
| **NOT SHIPPED** | Documented intent only. Do it by hand; no command in this repo does it. |

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Hardware baseline](#2-hardware-baseline)
3. [Creator Extend build + install](#3-creator-extend-build--install)
4. [Recording library setup](#4-recording-library-setup)
5. [AI-driven content pipeline](#5-ai-driven-content-pipeline)
6. [Publishing](#6-publishing)
7. [Cross-links to OpenTechnologyApp + OpenTechnologyBlog](#7-cross-links-to-opentechnologyapp--opentechnologyblog)
8. [Test end-to-end](#8-test-end-to-end)
9. [Failure modes and recovery](#9-failure-modes-and-recovery)

---

## 1. Prerequisites

### 1.0 Repository and toolchain

Same toolchain as Stream Extend. If you have already done
[Stream Extend §1.0](STREAM_EXTEND_PRODUCTION_SETUP.md#10-repository-and-toolchain), skip to §1.1.

```bash
git clone https://github.com/OpenTechnology14/Open_Content_Creator_Platform.git
cd Open_Content_Creator_Platform
```

```bash
xcode-select --install || true
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
brew install node@22 python@3.12
```

**Verify:**

```bash
git --version && rustc --version && cargo --version && node --version && python3.12 --version
```

### 1.1 ComfyUI — required, not optional

Unlike Stream Extend, ComfyUI is a **hard dependency** here. Creator Extend's readiness manifest at
[`configs/setup/creator-extend.json`](../../../configs/setup/creator-extend.json) gates the
`comfy-workflows` capability on two checks — `creator.comfyui.api` and
`creator.comfyui.workflows` — and the workflow runner stays disabled until both are ready.

Authority: [`modules/realtime-ai/setup/manual.md`](../../../modules/realtime-ai/setup/manual.md).
The macOS path:

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git modules/realtime-ai/comfyui/app
cd modules/realtime-ai/comfyui/app
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Apple Silicon, torch installs with MPS support from the default index. Skip the
`--index-url .../cu121` line in the module doc — that is the CUDA path for Linux/WSL, and the
evaluation doc is explicit that the Mac cannot run CUDA.

ComfyUI Manager, which the module doc calls non-negotiable:

```bash
cd custom_nodes && git clone https://github.com/Comfy-Org/ComfyUI-Manager.git && cd ..
```

```bash
python3.12 main.py --listen 127.0.0.1 --port 8188
```

**Verify:**

```bash
curl -fsS http://localhost:8188/system_stats | head -c 200
```

Pass condition: JSON. The app's readiness check calls this same endpoint and records `gpuBackend`
and `vramTotalMb` as evidence.

**Models — the render-side set.** The shopping list is
[`modules/realtime-ai/comfyui/models.md`](../../../modules/realtime-ai/comfyui/models.md). This is
the opposite budget from the streaming host: nothing is competing with a game or an encoder, so
take quality over speed.

| Slot | Model | Size | For |
|---|---|---|---|
| checkpoint | **SDXL base 1.0** | ~7 GB | Thumbnails and high-quality stills. This is the workhorse |
| VAE | **SDXL VAE** | small | Fixes washed-out colors. Not optional with SDXL |
| LoRA | LCM-LoRA SDXL | ~50 MB | Fast iteration while you are choosing a thumbnail composition |
| upscaler | 4x-UltraSharp | small | Pre-encode upscales |
| checkpoint | SDXL Inpainting 0.1 | ~7 GB | Only if you are fixing thumbnails rather than regenerating them |

Do **not** download Flux Fill dev (~12 GB) or SAM ViT-H (~2.5 GB) for this workflow. They are for
the image-editing and generation modules, and on 16 GB shared memory they will cost you more in
swap than they return.

The models doc is explicit that it has "no checksum or license column — it's a shopping list, not
provenance." For a real record per downloaded weight, use
[`model-registry`](../../../modules/model-registry/README.md)'s `registry.yml`. That module is
`implemented`, and its CLI is one of the few things in this repo that is fully automated:

```bash
python3.12 -m model_registry.cli status
```

Run it from `modules/model-registry/`. This matters more than it sounds: a LoRA with no license
record is a LoRA you cannot ship in a distributable adapter.

### 1.2 Blender

```bash
brew install --cask blender
```

Or download from <https://www.blender.org/>.

**Verify:**

```bash
/Applications/Blender.app/Contents/MacOS/Blender --version
```

The Creator Extend Blender addon is real code at
[`plugins/blender-addon/`](../../../plugins/blender-addon/). Per
[`modules/content-creation/setup/manual.md`](../../../modules/content-creation/setup/manual.md),
not all five of its operators are implemented — the module's
[`automated.md`](../../../modules/content-creation/setup/automated.md) says exactly which are
stubs. Check it before relying on one.

The app can package the addon for you — `creator_tool_archive_blender_addon` prepares it as a ZIP
for Blender's installer. Use that rather than zipping by hand (§3.6).

> **Never commit anything over 5 MB** ([`CLAUDE.md`](../../../CLAUDE.md) §10). Blender projects
> belong in `modules/content-creation/blender/projects/`; renders and heavy assets go to MinIO.

### 1.3 Krita

```bash
brew install --cask krita
```

Or download from <https://krita.org/>.

The plugin is at [`plugins/krita-integration/`](../../../plugins/krita-integration/) — Python,
menu items and docker panels. Setup is
[`modules/image-editing/setup/manual.md`](../../../modules/image-editing/setup/manual.md), and that
module's automated path is **none** — Krita is a desktop app.

Krita is optional for the §8 end-to-end test. Install it when you start hand-finishing thumbnails.

### 1.4 FFmpeg — required

Unlike the streaming host, where OBS brings its own, here FFmpeg does real work: it is how you cut
clips out of a recording.

```bash
brew install ffmpeg
```

**Verify:**

```bash
ffmpeg -version | head -1 && ffprobe -version | head -1
```

Both must print a version.

### 1.5 GStreamer

GStreamer appears in the platform's dependency surface, but **nothing in the Creator Extend
critical path requires it.** The app shells out to Blender and Krita and talks HTTP to ComfyUI;
clip cutting is FFmpeg. Install it only if a module you add later asks for it:

```bash
brew install gstreamer gst-plugins-base gst-plugins-good
```

```bash
gst-launch-1.0 --version
```

### 1.6 Storage services — recommended

```bash
cp .env.example .env
docker compose up -d
```

```bash
docker compose ps
```

Pass condition: Postgres, Redis and MinIO healthy. MinIO is where renders and AI outputs belong;
[`storage-data`](../../../modules/storage-data/setup/manual.md) is `implemented`, one of only four
modules at that level, so this path is reliable.

Buckets, per the content-creation doc: renders → `project-assets`, recordings → `recordings`,
AI outputs → `comfyui-outputs`.

> **Recordings themselves are not uploaded.** The shared inbox stores a canonical local path and
> never copies video. The `recordings` bucket is for what *you* deliberately push there.

### 1.7 Social auth — YouTube

Per your setup, the OpenTechnologyApp / OpenTechnologyBlog content track is **YouTube-only**. From
[`modules/social-management/catalog.yaml`](../../../modules/social-management/catalog.yaml), the
YouTube provider is `adapter: youtube`, `connection_status: available` — a real adapter, not
catalog-only.

Before you can authorize:

1. At <https://console.cloud.google.com/apis/credentials>, create a project.
2. Enable **YouTube Data API v3** and **YouTube Live Streaming API**. Both — the catalog's notes
   require it.
3. Create an **OAuth 2.0 Client ID**, type **Desktop app**.
4. Export the credentials so the Social Management service can read them:

```bash
export SOCIAL_YOUTUBE_CLIENT_ID='your-client-id'
export SOCIAL_YOUTUBE_CLIENT_SECRET='your-client-secret'
```

The env var names are not arbitrary — they are `client_id_env` and `client_secret_env` in the
catalog. The YouTube flow uses PKCE with `access_type: offline` and `prompt: consent`, so you get a
refresh token and are not re-consenting weekly.

Capability scopes you will use:

| Capability | Scope | Needed for |
|---|---|---|
| `account-read` | `youtube.readonly` | Listing your channel |
| `post-video` | `youtube.upload` | Uploading a clip |
| `live-stream` | `youtube` | Only if this machine also goes live |

Authorize in the app in §3.6, not here. Tokens go to the macOS Keychain and never enter the webview.

---

## 2. Hardware baseline

Same M1 Pro — 8 CPU cores, 14 GPU cores, 16 GB unified memory — from
[`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md).
**Different workload.**

### 2.1 Render-heavy, not encode-heavy

| | Stream Extend | Creator Extend |
|---|---|---|
| Hot path | Sustained H.264 encode + capture, 60 fps, for hours | Bursty GPU inference and Blender renders |
| Latency requirement | Hard realtime. A 200 ms stall is a visible dropped frame | None. A 90-second render is fine |
| Memory profile | Steady, must not spike | Spiky, and the spikes are large |
| Failure mode | Dropped frames on a live broadcast | A slow render, retried |
| Can it share the machine? | Barely | **Not with a live stream** |

**The operational rule this implies:** do not run Creator Extend renders while Stream Extend is
live on the same Mac. SDXL at ~7 GB on a 16 GB shared pool, alongside an encoder and a game, is how
you get the memory pressure that crashes OBS
([Stream Extend §10.2](STREAM_EXTEND_PRODUCTION_SETUP.md#102-obs-crashes)).

The handoff is designed for exactly this separation. The proposal is explicit that registration
"does not require Stream Extend and Creator Extend to be open together." Stream first; produce
after.

### 2.2 What the Mac does well here

Unified memory is a genuine advantage for a single large model. SDXL at 1024×1024 fits comfortably
when nothing else is competing. What you do not get is CUDA — so any node or custom extension that
requires it is unavailable, and that is a hardware fact, not a configuration problem.

### 2.3 Disk

A 20-minute 1080p60 OBS recording is roughly 2–5 GB depending on encoder settings. Clips, renders
and ComfyUI outputs accumulate fast.

```bash
df -h ~
```

Keep **≥ 100 GB** free for a working content pipeline. The recording inbox refuses zero-byte files
but does nothing about a full disk.

### 2.4 The tower changes this calculus later

When the planned tower arrives — RTX 3060 12 GB, 32 GB RAM, ceiling $949.99, **nothing purchased**
— it opens the CUDA path for generation. Two cautions from the evaluation doc apply directly here:

- The 3060's 12 GB "does not guarantee photorealistic full-body generation."
- Keep AI and gaming benchmarks **separate**. A card that games well is not thereby an AI
  workstation, and the doc says to benchmark your AI software against an AMD card before choosing
  one.

---

## 3. Creator Extend build + install

### 3.1 What you are building

A Tauri 2 desktop app. Rust backend at
[`apps/creator-extend/src-tauri/src/`](../../../apps/creator-extend/src-tauri/src/) — `comfyui.rs`,
`blender.rs`, `krita.rs`, `posture.rs`, `workflow_inputs.rs`, `tool_runtime.rs` — and a SvelteKit
frontend at [`apps/creator-extend/src/`](../../../apps/creator-extend/src/).

An `apps/creator-extend/README.md` does not exist. This section is written from the source
and from
[`modules/infrastructure/setup/desktop-setup.md`](../../../modules/infrastructure/setup/desktop-setup.md).

### 3.2 Frontend dependencies

```bash
cd apps/creator-extend && npm ci
```

**Verify:**

```bash
npm run check
```

Pass condition: **0 errors** from `svelte-check`.

### 3.3 Build the frontend

```bash
npm run build
```

```bash
ls build/index.html
```

### 3.4 Rust tests, then bundle

```bash
cargo test --locked --manifest-path src-tauri/Cargo.toml
```

Pass condition: all pass. This includes
[`apps/creator-extend/src-tauri/tests/comfyui_contract.rs`](../../../apps/creator-extend/src-tauri/tests/comfyui_contract.rs)
and
[`workflow_inputs_contract.rs`](../../../apps/creator-extend/src-tauri/tests/workflow_inputs_contract.rs),
which are what prove the queue path against a fake ComfyUI rather than a live one.

```bash
npm run tauri build
```

10–25 minutes on a first run.

**Verify:**

```bash
ls -d src-tauri/target/release/bundle/macos/*.app src-tauri/target/release/bundle/dmg/*.dmg
```

### 3.5 First launch and entitlements

Ad-hoc signed, not notarized. In Finder, **right-click → Open → Open**. Double-clicking will be
blocked.

If Gatekeeper still refuses:

```bash
xattr -dr com.apple.quarantine src-tauri/target/release/bundle/macos/Creator\ Extend.app
```

Creator Extend needs **Files and Folders** access, which macOS prompts for the first time you use
**Add existing recording** or **Show in folder**. Grant it — the reveal action and the file picker
both depend on it. It needs no camera, microphone or screen-recording permission; it does not
capture anything.

**Verify:** the app opens with six tabs — **Module setup**, **Connections**, **Remote control**,
**Social**, **Recordings**, **Dashboard**.

### 3.6 First-run wizard

**Step 1 — Connections.** Creator Extend's Connections form is different from Stream Extend's,
because it configures ComfyUI, MinIO and desktop tool paths rather than OBS.

1. **ComfyUI URL**: `http://localhost:8188`
2. **MinIO endpoint**: `http://localhost:9000`, plus access key and secret key from your `.env`
3. **Blender path**: leave blank if Blender is on PATH; otherwise
   `/Applications/Blender.app/Contents/MacOS/Blender`
4. **Krita path**: same pattern
5. Save.

MinIO credentials go to the macOS Keychain via the shared `local-settings` contract, exactly as the
OBS password does in the other app.

**Step 2 — Module setup.**

1. Tick **Social Management** — required for §6 and §7. Its isolated Python environment is shared
   between both apps, so if you installed it for Stream Extend it is already here.
2. Tick **Content Creation** and **Image Editing** if you will use the Blender and Krita actions.
3. Run the installer; wait for durable progress to finish.
4. Click **Check readiness**.

Pass condition: both checks green — `creator.comfyui.api` ("ComfyUI answered system and queue
requests") and `creator.comfyui.workflows` ("The app loaded its committed workflow catalog").

> **The workflow catalog is the app's own, not ComfyUI's.** `comfyui_workflows` lists *committed*
> workflows shipped with the app — deliberately not whatever a live ComfyUI's userdata happens to
> have saved. If `creator.comfyui.workflows` is blocked with "No runnable committed workflows are
> bundled", that is a build problem, not something you fix in ComfyUI's web UI.

Until both pass, `canRunWorkflows` is false and the workflow runner stays disabled. This is the same
capability-gate pattern as Stream Extend's `obs-control`.

**Step 3 — Tool checks.**

Open the Dashboard and run the tool check (`creator_tool_status`). It verifies the packaged Creator
scripts can start with their selected Python environment **without modifying your files or
contacting ComfyUI/MinIO**. A pass proves the script starts — the code comment says so directly:
"the real DCC workflow still needs live acceptance." **EXTERNAL ACCEPTANCE.**

If the `blender-addon` check says "Addon payload is packaged, but Blender was not found", set the
Blender path in Connections.

To install the addon, use the app's own packaging action rather than zipping by hand, then in
Blender: **Edit → Preferences → Add-ons → Install…**, pick the ZIP, enable **Creator Extend**, and
set `MinIO Endpoint` / `Access Key` / `Secret Key` / `Bucket` in the addon's preferences. The addon
reads them from Blender's preferences UI, not from your shell environment — Blender's embedded
interpreter does not inherit shell env. The panel then appears under
**View3D → Sidebar → Creator Extend**.

**Step 4 — Social.**

1. **Social** tab. Select **Main Content** (`content-main`) or **OpenTechMarketing**
   (`opentech-marketing`).
2. Provider **YouTube**, capability **post-video**. Authorize.

Consent opens in the system browser. The loopback service binds `127.0.0.1:8765`.

**Verify:** the header switcher shows `youtube · account routed`.

---

## 4. Recording library setup

This is the P-065 work merged in `c409a34`:
[`PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md`](../../proposals/PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md).
Queue state `Code complete — external acceptance open`, authoritative in
[`docs/PROPOSALS.md`](../../PROPOSALS.md). **SHIPPED**, with the live-OBS half open.

### 4.1 Where recordings land

They land **nowhere new.** This is the single most important thing to understand about this feature,
and it is by design.

The crate is [`apps/shared/recording-library/`](../../../apps/shared/recording-library/). Its README
is unambiguous: "Video is not copied or uploaded." What exists is a **JSON ledger** holding a
canonical path and private local metadata:

```
~/Library/Application Support/HybridCreatorPlatform/recording-library/
```

The video file itself stays exactly where OBS wrote it — your OBS recording folder.

Consequences you must plan around:

| Behavior | Consequence |
|---|---|
| The ledger stores a canonical path | **Move the file and the inbox marks it unavailable.** Organize your recording folder *before* you start, not after |
| Registration deduplicates by canonical path | Re-importing the same file updates the existing record. Safe to retry |
| Only canonical, **non-empty** local video files are accepted | A zero-byte file from a failed encode is rejected at the door, not silently catalogued |
| Atomic writes through `local-settings`, guarded by a cross-process file lock | Both apps can be open at once without overwriting each other's updates |

### 4.2 How Stream Extend hands off

The chain, from
[`apps/stream-extend/src-tauri/src/obs.rs`](../../../apps/stream-extend/src-tauri/src/obs.rs) and
[`lib.rs`](../../../apps/stream-extend/src-tauri/src/lib.rs):

1. You click **🔴 Go Live + Record** in Stream Extend.
2. `start_live_session` checks OBS is not already streaming, then checks whether OBS is already
   recording. **If OBS was already recording, Stream Extend does not claim it** — `recording_owned`
   is false and it will never stop that recording.
3. It starts recording, *then* starts streaming. If streaming fails, it rolls back the recording it
   started.
4. You click **⬛ Stop + Send to Creator**.
5. `stop_live_session` stops the stream, then stops the recording **only if it owned it**, and OBS
   returns the finalized path.
6. `library.register(path, RecordingOrigin::StreamSession, source_profile_id, content_profile_id)`
   writes the ledger entry — tagged with the Stream Extend profile that was active.
7. Creator Extend's `recordings_list` reads that same ledger. The UI polls every 4 seconds.

The full walkthrough from the other side is
[Stream Extend §6.4](STREAM_EXTEND_PRODUCTION_SETUP.md#64-the-mid-stream-profile-switch-test).

**The apps do not need to be open together.** The ledger is the contract; there is no live IPC.

### 4.3 The Recordings view

Open **Recordings**. The component is
[`apps/shared/ui/RecordingLibrary.svelte`](../../../apps/shared/ui/RecordingLibrary.svelte).

| Control | What it does |
|---|---|
| **Add existing recording** | File picker (`mkv, mp4, mov, webm, m4v, avi, ts`). Registers with origin `manual-import`, assigned to your active content profile |
| **Refresh** | Re-reads the ledger now instead of waiting for the 4-second poll |
| **Show archived** | Archived rows are hidden by default |
| **Content profile** dropdown | Routes this recording to a content profile. Lists `content` and `hybrid` profiles only |
| **Start editing** | Sets status `editing` |
| **Mark ready** / **Mark published** | Sets `ready` / `published` |
| **Show in folder** | Reveals the file in Finder |
| **Archive** | Sets `archived` |

**Status is workflow metadata, not proof.** The proposal says so directly: `ready`, `editing`,
`archived` are "not proof that editing or publishing completed." Marking something `published` does
not publish it. It is a note to yourself.

The **From** column shows the Stream Extend source profile — so a recording made under
`stream-main` is visibly distinct from one made under `opentech-marketing`, which is what drives the
routing decision in §7.

### 4.4 Set up your recording folder first

Because the ledger stores paths, folder discipline is not optional.

1. In OBS: **Settings → Output → Recording → Recording Path**.
2. Point it at a dedicated folder on a **local SSD** — for example `~/Recordings/stream/`.
3. Never a network volume, never an external drive you unplug, never a path with a symlink in it.
   Each of those breaks canonicalization and produces the registration failure in §9.3.
4. Confirm ≥ 20 GB free before a session.

**Verify the whole path works before you need it:**

1. In OBS, press **Start Recording**, wait 10 seconds, press **Stop Recording**.
2. In Creator Extend → **Recordings** → **Add existing recording**, pick that file.
3. Pass condition: it appears with a plausible size, status `ready`, origin shown as
   **Manual import**.
4. Click **Show in folder**. Finder reveals it.

If step 3 fails on a file OBS just wrote, fix it now — the automatic handoff will fail the same way,
but at the end of a real stream.

---

## 5. AI-driven content pipeline

**Be clear about what this section is.** There is no clip-selection model, no thumbnail-generation
command, no title generator and no description generator in this repository. `comfyui_queue`,
`comfyui_queue_configured`, `blender_batch_render`, `krita_run_script` and `posture_analyze` are the
Creator Extend commands that exist. A pipeline from recording to published clip is **you, using
those tools in order**.

| Stage | Status | What actually does it |
|---|---|---|
| Clip selection | **NOT SHIPPED** as an app command | You, scrubbing. A local Shorts pipeline exists in [`modules/content-creation/stream_shorts/`](../../../modules/content-creation/stream_shorts/) — selection, review and rendering code inside that module |
| Clip cutting | **NOT SHIPPED** in the app | FFmpeg, by hand |
| Thumbnail generation | **SHIPPED** as a ComfyUI queue path | `comfyui_queue_configured`, against a committed workflow |
| Thumbnail finishing | **SHIPPED** via Krita | `krita_run_script` |
| Title generation | **NOT SHIPPED** | You. Or the marketing-crosswalk templates for the OpenTech track (§7) |
| Description generation | **NOT SHIPPED** | Same |
| Quality gates | Partly **SHIPPED** | `comfyui_preflight` gates the render. Everything else is your eyes |

Writing this honestly is the point. Follow the steps and you will produce clips; expect a button
that does it for you and you will waste an evening looking for it.

### 5.1 Pick a clip

1. **Recordings** → **Show in folder** on your target recording.
2. Scrub in QuickTime or IINA. Note in/out timecodes.
3. Aim for **30–60 seconds** with a visible payoff in the first 3 seconds.

For a repeatable selection pass rather than eyeballing it, read
[`modules/content-creation/stream_shorts/README.md`](../../../modules/content-creation/stream_shorts/README.md)
— that is real selection, review and rendering code in the module, and it is the nearest thing to
automated clip selection that exists here.

### 5.2 Cut it

```bash
ffmpeg -ss 00:12:30 -to 00:13:15 -i ~/Recordings/stream/your-recording.mkv \
  -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k \
  ~/Recordings/clips/clip-01.mp4
```

Re-encoding rather than `-c copy` is deliberate: stream copy cuts only on keyframes, so with OBS's
2-second keyframe interval your in-point can be off by up to 2 seconds. CRF 18 is visually lossless
for a source that is already encoded.

**Verify:**

```bash
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 ~/Recordings/clips/clip-01.mp4
```

Pass condition: duration within a second of what you asked for, size non-zero.

**Quality gate 1 — watch the whole clip.** If the payoff is not obvious in the first 3 seconds, cut
it again. Nothing downstream fixes a bad clip.

### 5.3 Generate a thumbnail

This is the one genuinely app-driven stage.

1. Grab a reference frame:

```bash
ffmpeg -ss 00:00:03 -i ~/Recordings/clips/clip-01.mp4 -frames:v 1 ~/Recordings/clips/frame.png
```

2. In Creator Extend, open the workflow list. Pick a committed workflow.
3. Click **Preflight**.

**Quality gate 2 — preflight.** `comfyui_preflight` inspects the workflow against the **live
ComfyUI node and model inventory** before the input editor will queue it. A workflow that needs a
model you have not downloaded is caught here, not after a 90-second render. If it reports
incompatible, read which node or model is missing and install it via ComfyUI Manager.

4. Edit the exposed inputs. The editor shows only the fields `workflow_inputs::fields` exposes —
   `comfyui_queue_configured` reloads the approved template from disk and applies *only supported
   per-run values*. You cannot rewrite the graph from the UI, which is the point.
5. Upload `frame.png` if the workflow takes an image input (`comfyui_upload_image`).
6. Queue.

Prompts that work for a gaming thumbnail:

```
dramatic close-up game scene, high contrast, vivid saturated color, bold rim lighting, cinematic
```

```
bold flat-illustration background, single strong focal point, high contrast, empty space upper left for text
```

Keep a negative of `text, watermark, blurry, cluttered, low contrast`.

7. Poll status (`comfyui_prompt_status`), then preview the result (`comfyui_output_preview`).

**Quality gate 3 — the 200-pixel test.** Shrink the thumbnail to 200 px wide and look at it. If you
cannot tell what it is, regenerate. That is the size it will appear at in a YouTube sidebar.

### 5.4 Finish the thumbnail

Text on thumbnails should be added by a text tool, not a diffusion model — SDXL renders text badly
and the negative prompt above tells it not to try.

Open Krita from the app (`krita_open`), add your title text, export at **1280×720 JPEG under 2 MB**
— that is YouTube's limit.

```bash
ffprobe -v error -show_entries stream=width,height -of csv=p=0 ~/Recordings/clips/thumb-01.jpg
```

Pass condition: `1280,720`.

For batch operations there is `krita_run_script`, which runs the packaged image-editing scripts
under the module's Python interpreter.

### 5.5 Title and description

**NOT SHIPPED.** Write them.

Two constraints worth knowing: YouTube truncates titles around **60 characters** in most surfaces,
and only the **first ~120 characters** of a description show before "more."

For the OpenTech track specifically, the marketing-crosswalk generator produces *drafts* from
templates — §7. It generates marketing copy for registered consumer modules; it does not write
titles for arbitrary gaming clips.

### 5.6 Where the models run

All locally, all on this Mac:

| Stage | Runs on | Typical |
|---|---|---|
| FFmpeg cut | CPU | Seconds |
| ComfyUI SDXL 1024×1024 | GPU via MPS | 60–120 s on M1 Pro |
| ComfyUI SDXL + LCM-LoRA | GPU via MPS | 15–30 s, lower quality |
| Krita | CPU | Interactive |
| Blender render | CPU + GPU | Minutes to hours |

Nothing leaves the machine. The only network calls in this pipeline are the YouTube upload in §6
and the OAuth consent in §3.6.

---

## 6. Publishing

> **Everything published from here lands on the public gamer profile you set up in
> [Stream Extend §3](STREAM_EXTEND_PRODUCTION_SETUP.md#3-streaming-platform-setup).** Clips carry
> further than streams — a stream reaches whoever was there, a clip reaches whoever the algorithm
> shows it to. Treat this section as identity work with an upload step attached.

### 6.0 Consistency gate — check before every publish

The handle, branding and About copy were settled in
[Stream Extend §3.0](STREAM_EXTEND_PRODUCTION_SETUP.md#30-reserve-three-handles--do-this-before-installing-anything)
and [§3.6](STREAM_EXTEND_PRODUCTION_SETUP.md#36-branding-artifacts--prepare-these-during-setup-not-after).
Publishing is where they get tested, because this is where a mismatch becomes visible to strangers.

- [ ] Uploading to the **account matching this recording's profile** — there are three, and they do
      not share an audience:

      | Recording came from | Account | Platforms |
      |---|---|---|
      | Any game profile | **Games** | Twitch + YouTube Gaming |
      | TNTL, Nova Reviews the Edit | **Reactions** | Twitch + YouTube |
      | Blog walkthrough, Build Brief, Workflow Clinic, working session | **OpenTechnology** | YouTube only |

      Check the account label in the profile switcher, not your memory. A gaming clip on the
      OpenTechnology channel is not a small mistake — it teaches the algorithm the wrong thing
      about a channel you are trying to position professionally
- [ ] Each account has its **own** avatar, banner and About copy — current, and verified **logged
      out**. See [Stream Extend §3.6](STREAM_EXTEND_PRODUCTION_SETUP.md#36-branding-artifacts--prepare-these-during-setup-not-after)
- [ ] Thumbnail uses the **same palette and typeface** as that account's other thumbnails. One
      visual system per account — not one across all three
- [ ] Title voice matches your other titles — you are building a recognizable shelf, not a pile
- [ ] Description ends with the same links block every time

**Why the palette line matters more than it looks:** a viewer's first encounter with you is usually
a grid of your thumbnails in a sidebar. A consistent grid reads as a channel. An inconsistent one
reads as reuploads.

### 6.1 What is shipped

The Social Management module has a **real YouTube adapter** — `adapter: youtube`,
`connection_status: available`. But note the boundary from the P-065 proposal: "Uploads, posts, and
live destinations keep the P-062 human-approval boundary." There is no unattended publish. You
approve each one. **EXTERNAL ACCEPTANCE** — no upload in this repo has been proven against a live
account.

### 6.2 Upload

1. Creator Extend → **Social**.
2. Active profile: **Main Content** for gaming clips, **OpenTechMarketing** for OpenTech content.
3. Provider **YouTube**, capability **post-video**.
4. Select the connected account. The switcher's sub-label must read `account routed`.
5. Provide the clip path, title, description and thumbnail.
6. **Set visibility to Private for your first upload.** Not unlisted — private. You want it
   invisible while you check it.
7. Approve.

**Private-first applies here exactly as it does to streaming.** The rule from
[Stream Extend §8](STREAM_EXTEND_PRODUCTION_SETUP.md#8-private-test-stream-dry-run) is: never let
untested output reach a public surface, because you cannot retract it from the surfaces that carry
it. For publishing, that means **every clip goes up Private first and is watched on YouTube before
it goes Public** — §8 Phase 6. Unlisted is not private; unlisted URLs get shared, indexed and
embedded.

**Verify:** the video appears in **YouTube Studio → Content**, marked Private.

If the app's upload path fails, upload by hand at <https://studio.youtube.com> → **Create →
Upload videos**. This is a perfectly good fallback and you should not treat it as defeat — the app's
value here is metadata routing per profile, not the HTTP PUT.

### 6.3 Per-platform metadata mapping

Your content track is YouTube-only, so this is a one-row table today. It is worth writing down
because the catalog is built to grow:

| Field | YouTube | Source |
|---|---|---|
| Title | ≤ 100 chars, ~60 visible | Written by you (§5.5) |
| Description | 5000 chars, ~120 visible before "more" | Written by you |
| Thumbnail | 1280×720, < 2 MB, JPEG/PNG | §5.4 |
| Tags | 500 chars total | Optional |
| Visibility | private / unlisted / public | `default_visibility` in the catalog where declared |
| Category | Gaming (20) or Science & Technology (28) | Set at upload |

Two catalog profiles set `default_visibility: private` on their destinations — `video-review`'s
YouTube and TikTok, and `content-main`'s TikTok. That is a deliberate safety default, and the
`video-review` profile exists precisely as a private staging identity. Use it when you want a clip
reviewed before it goes anywhere.

Providers you will see in the picker but cannot use: TikTok, Instagram, Facebook and LinkedIn are
`adapter: catalog-only`, `connection_status: registration-required`. TikTok's note is worth reading
before you plan around it — "Direct Post requires app review; unaudited clients are private-only."
**NOT SHIPPED.**

### 6.4 Scheduling

**NOT SHIPPED.** There is no scheduler in this repository. Use YouTube Studio's own: upload as
Private, then **Visibility → Schedule**, set the date and time. That is a first-party feature and it
is reliable.

Do not build a cron job around the app's upload command to fake scheduling. The human-approval
boundary is there on purpose.

---

## 7. Cross-links to OpenTechnologyApp + OpenTechnologyBlog

### 7.1 The three repositories

| Repository | Role |
|---|---|
| Open_Content_Creator_Platform | This one. Canonical combined integration and shared desktop source |
| ContentExtend | Content-focused product distribution |
| StreamExtend | Streaming-focused product distribution |

The marketing-crosswalk generator also reads a **Task-Management** checkout — the OpenTechnologyApp
repository — and writes drafts into it.

### 7.2 marketing-crosswalk — what it is

[`modules/marketing-crosswalk/`](../../../modules/marketing-crosswalk/) is `implemented` and is
**full automation**: a CLI, not a service. It generates marketing content *for registered consumer
modules*, reading two local git checkouts and writing markdown.

```bash
cd modules/marketing-crosswalk
pip install -r requirements.txt
python3 -m generator.cli validate
```

Pass condition: exit 0. `validate` confirms marketing-doc anchors and status claims still hold in
the target repo.

| Command | Purpose |
|---|---|
| `validate` | Anchors and status claims still hold |
| `coverage` | Per-subject render/blocked counts and content-ledger gaps |
| `selftest` | Renders every template in memory; writes nothing |
| `generate` | Renders drafts to `out/`, or `--apply` to the target repo's draft dir |

Target resolution: `--target-path` → `$TASKMGMT_REPO_PATH` → `../Task-Management`.

```bash
export TASKMGMT_REPO_PATH=/path/to/Task-Management
python3 -m generator.cli coverage
```

### 7.3 The AI Learning Series — P-064

Commit `353406c` registered `ai-learning` as a fourth marketing-crosswalk consumer. This is the
concrete cross-link between your streams and the blog.

What it added:

- The `ai-learning` module and product in the crosswalk, with **four lesson subjects**
- A new **`opentechnology-blog`** target, anchored on `AI_CONTENT_INVENTORY.md` in that repo
- An optional `status_evidence.target` in the generator, so a lesson's status is verified against
  *this* repo while its drafts are delivered to the blog
- Two templates: **lesson-brief** and **stream-runofshow**
- [`docs/learning/`](../../learning/README.md) — the series index plus one source doc per lesson

The four lessons, in order:

| # | Lesson | Source doc |
|---|---|---|
| 1 | Model usage | [`lesson-01-model-usage.md`](../../learning/lesson-01-model-usage.md) |
| 2 | Prompting with project and context | [`lesson-02-prompting-context.md`](../../learning/lesson-02-prompting-context.md) |
| 3 | App building with docs, rules and skills | [`lesson-03-app-building.md`](../../learning/lesson-03-app-building.md) |
| 4 | Cost workflow | [`lesson-04-cost-workflow.md`](../../learning/lesson-04-cost-workflow.md) |

Each lesson is **streamed with Stream Extend and produced with Creator Extend**, then delivered to
OpenTechnologyBlog. That is the full loop this pair of guides exists to support.

> **No lesson has aired.** All four subjects are `scaffolded`. Reddit and LinkedIn assets are
> deliberately not declared until lesson-shaped templates exist.

### 7.4 The loop, concretely

1. **Stream Extend**, profile **OpenTechMarketing**, YouTube-only destination
   ([Stream Extend §3.5](STREAM_EXTEND_PRODUCTION_SETUP.md#35-the-opentech-youtube-only-track)).
   Use the **stream-runofshow** template to plan the episode.
2. Stream the lesson. Stop with **⬛ Stop + Send to Creator**.
3. **Creator Extend → Recordings.** The row shows source profile `opentech-marketing`. Assign it to
   the `opentech-marketing` content profile.
4. Produce clips (§5).
5. Generate marketing drafts:

```bash
cd modules/marketing-crosswalk && python3 -m generator.cli generate
```

Drafts land in `out/`. Review them there before considering `--apply`.

6. Publish the video to the OpenTech YouTube channel (§6).
7. `--apply` writes drafts to the target repo's **draft directory**. It never edits a marketing doc
   in place — moving a draft into `MARKETING.md` is a human decision. Every draft carries a
   checklist of what the generator could not know. **Read that checklist; it is the quality gate.**

### 7.5 What the crosswalk does not do

**Publishing.** It writes markdown drafts. It does not post, upload, or open a pull request. The
final move into a live marketing doc is always yours.

---

## 8. Test end-to-end

**Record 10 minutes via Stream Extend → hand off → generate 3 clips → publish one privately →
verify.** Budget 2 hours the first time, most of it ComfyUI render waits.

### Phase 1 — Record (Stream Extend, ~15 min)

- [ ] ComfyUI **stopped** — you need the memory for the encoder
- [ ] OBS open, WebSocket on 4455, recording path a local SSD folder with ≥ 20 GB free
- [ ] Stream Extend: **OBS Connected**; **Module setup → Check readiness** both green
- [ ] Header profile set — **Main Stream** for gaming, **OpenTechMarketing** for a lesson
- [ ] Click **🔴 Go Live + Record**
- [ ] Stats row reads **`Recording for Creator Extend`**
- [ ] Record **10 minutes** with at least three distinct moments worth clipping
- [ ] Click **⬛ Stop + Send to Creator**
- [ ] Message: `Recording <name> is ready in Creator Extend.`

**Pass condition:** that exact message shape, naming a real file.

### Phase 2 — Hand off (Creator Extend, ~2 min)

- [ ] Open Creator Extend → **Recordings**
- [ ] The recording appears **without** you importing it
- [ ] **From** shows the Stream Extend profile you used
- [ ] Size is plausible for 10 minutes (roughly 1–3 GB)
- [ ] Status `ready`, not greyed out as unavailable
- [ ] Assign a **Content profile** from the dropdown
- [ ] Click **Show in folder** — Finder reveals the actual file
- [ ] Click **Start editing** — status becomes `editing`

**Pass condition: the recording appeared on its own.** That is the whole handoff, proven. If you had
to import it manually, the automatic path failed — see §9.3 before continuing.

### Phase 3 — Three clips (~30 min)

For each of your three moments:

- [ ] Note in/out timecodes
- [ ] Cut with the FFmpeg command in §5.2
- [ ] `ffprobe` confirms duration and non-zero size
- [ ] Watch the clip start to finish. Payoff visible in the first 3 seconds

**Pass condition: three playable clips, each 30–60 seconds.**

**Then the channel review gate, per clip — before any of them goes near §6.** This is the same gate
as [Stream Extend §7.4 step 10](STREAM_EXTEND_PRODUCTION_SETUP.md#74-the-end-to-end-captured-session),
applied to the cut clip rather than the raw recording, because a clip concentrates whatever was in
the source:

- [ ] **Would I put this on my channel?** Asked about the clip as a whole
- [ ] Every AI-generated frame is coherent — no melted geometry, no pseudo-text
- [ ] Nothing in it fails the **strictest** audience bar
      ([Stream Extend §4.1](STREAM_EXTEND_PRODUCTION_SETUP.md#41-the-mac-rotation--three-games) —
      Roblox's standard governs all three games)
- [ ] No generated likeness of a real person
- [ ] Audio has no moment you would not say again
- [ ] Nothing private on screen — no notifications, no desktop, no account details

**A failed clip is deleted, not shelved.** A clip you were unsure about and kept is a clip that gets
published by accident three weeks later.

### Phase 4 — One thumbnail (~20 min)

- [ ] Start ComfyUI. `curl -fsS http://localhost:8188/system_stats` returns JSON
- [ ] Creator Extend → **Check readiness** → `creator.comfyui.api` green
- [ ] Extract a reference frame from clip 1
- [ ] Select a committed workflow → **Preflight** → reports compatible
- [ ] Set inputs, queue, wait
- [ ] Preview the output
- [ ] Shrink to 200 px — still legible
- [ ] Add title text in Krita, export 1280×720 JPEG < 2 MB
- [ ] `ffprobe` confirms `1280,720`

**Pass condition: a thumbnail that reads at 200 px.**

### Phase 5 — Publish one, privately (~10 min)

- [ ] Write a title under 60 characters
- [ ] Write a description whose first 120 characters stand alone
- [ ] Creator Extend → **Social** → profile set → YouTube → `post-video`
- [ ] Switcher sub-label reads `account routed`
- [ ] Attach clip 1 and the thumbnail
- [ ] **Visibility: Private**
- [ ] Approve the upload

**Pass condition:** it appears in **YouTube Studio → Content** as Private.

### Phase 6 — Verify (~15 min)

- [ ] Play the video **on YouTube**, not locally. Full screen
- [ ] Picture sharp; no compression mush in motion
- [ ] Audio in sync start to finish
- [ ] Thumbnail is the one you made, not an auto-generated frame
- [ ] Title and description render correctly, no truncation surprises
- [ ] Watch on your **phone** — this is where thumbnail and title failures become obvious
- [ ] Creator Extend → **Recordings** → mark the source recording `published`
- [ ] Write down what took longest and what you would change

**Overall pass condition: all six phases.** Phase 2 is the one that proves the integration; the rest
prove you can operate it.

Then, and only then, set the video to Public or schedule it.

---

## 9. Failure modes and recovery

There is no incident playbook for content production in this repository.
[`docs/architecture/disaster-recovery.md`](../../architecture/disaster-recovery.md) is the backup
and restore runbook for the data services, not this. What follows is derived from the actual error
paths in the code.

### 9.1 ComfyUI unreachable

**Symptom:** readiness shows `creator.comfyui.api` blocked — "Start ComfyUI and verify the saved
local endpoint." The workflow runner is disabled.

| Priority | Action |
|---|---|
| 1 | Is ComfyUI actually running? `curl -fsS http://localhost:8188/system_stats` |
| 2 | Port match? App default is `http://localhost:8188`; ComfyUI defaults to 8188 but honors `--port` |
| 3 | Bound to the right interface? Start it with `--listen 127.0.0.1` |
| 4 | Fix the URL in **Connections**, save, then **Check readiness** again |
| 5 | Still blocked → read ComfyUI's console. A failed custom node import stops startup |

The capability stays locked until this passes. That is the gate working.

### 9.2 Workflow preflight reports incompatible

**Symptom:** preflight fails; the input editor will not queue.

This is the gate doing its job — `comfyui_preflight` compares the workflow against the **live node
and model inventory**. Read which node or model is named:

| Cause | Fix |
|---|---|
| Missing custom node | ComfyUI Manager → **Install Missing Custom Nodes** → restart ComfyUI |
| Missing model | Download to the right subfolder of `ComfyUI/models/`, restart ComfyUI |
| Node exists but version differs | Update via Manager |

Then **Check readiness** and preflight again. Do not attempt to bypass preflight — it is cheaper
than a failed 90-second render.

### 9.3 A recording does not appear in the inbox

**Symptom:** Stream Extend said it stopped, but **Recordings** is empty or missing the file.

First, establish which failure you have — the Stream Extend message tells you:

| Message | Meaning |
|---|---|
| `Recording <name> is ready in Creator Extend.` | Registration **succeeded**. The problem is in Creator Extend — click **Refresh** |
| `OBS finalized the recording, but Creator Extend inbox registration failed: …` | Video safe, registration failed |
| `The stream stopped, but OBS did not confirm recording finalization.` | Stop recording in OBS by hand first |
| `Stream stopped. The pre-existing OBS recording was left running and was not claimed.` | OBS was already recording when you clicked Go Live. Correct behavior, not a bug |

Registration failure causes, given the inbox accepts only canonical, non-empty local video files:

| Cause | Fix |
|---|---|
| Recording path on a network or external volume | Set OBS's recording path to a local SSD folder |
| Zero-byte file | Encoder failed. Read OBS's log |
| Path with a symlink or unusual mount | Use a plain path under your home directory |
| Disk was full | Free space; the file is likely truncated — check it plays |

**Recovery, always the same:** **Recordings** → **Add existing recording** → pick the file. The
inbox deduplicates by canonical path, so this is safe to repeat.

### 9.4 A recording shows as unavailable

**Symptom:** the row is outlined in red: "The original file moved or was deleted. Locate it and add
it again."

Expected behavior. The ledger stores a path; you moved the file. Either move it back, or use
**Add existing recording** at the new location and archive the stale row.

**Prevention:** decide your folder layout before recording, not after. This is §4.4.

### 9.5 Blender or Krita not found

**Symptom:** tool check reports "Addon payload is packaged, but Blender was not found."

| Priority | Action |
|---|---|
| 1 | Is it installed? `ls /Applications/Blender.app` |
| 2 | Set the full binary path in **Connections** — `/Applications/Blender.app/Contents/MacOS/Blender`, not the `.app` bundle |
| 3 | Re-run the tool check |
| 4 | For Krita: `/Applications/krita.app/Contents/MacOS/krita` |

Remember what a passing tool check proves: the script can start with its selected Python
environment. Not that the DCC workflow works. **EXTERNAL ACCEPTANCE.**

### 9.6 Render falls behind or the machine swaps

**Symptom:** SDXL renders take minutes; the whole Mac is sluggish.

| Priority | Action |
|---|---|
| 1 | Activity Monitor → Memory. Red pressure means the OS is swapping and everything is now slow |
| 2 | Quit Stream Extend, OBS and any game. **Never render while streaming** (§2.1) |
| 3 | Drop to 768×768 — SDXL's quality loss below 1024 is smaller than the time saved |
| 4 | Add LCM-LoRA SDXL and drop to 4–8 steps for iteration; switch back for the final render |
| 5 | Restart ComfyUI between long sessions. It does not always release memory between runs |

### 9.7 A published clip should not have gone out

AI-gen artifacts, an off-tone moment, or something private on screen reached a public video. The
publishing-side twin of
[Stream Extend §10.4](STREAM_EXTEND_PRODUCTION_SETUP.md#104-ai-gen-ships-junk-to-a-public-vod), and
worse in one respect: a clip is built to travel.

**Act within hours, not days.** The window before it is embedded, indexed or re-uploaded is short.

| # | Action |
|---|---|
| 1 | **YouTube Studio → set visibility to Private immediately.** Private first, decide second. Do not start editing while it is public |
| 2 | Fixable by trimming? **Studio → Editor → Trim & cut.** Editing in place keeps the URL and the view count |
| 3 | Not fixable? **Delete it.** A deleted video costs you a URL; a bad one costs you the channel's credibility |
| 4 | Check for re-uploads and embeds — search your handle plus the clip title |
| 5 | In Creator Extend → **Recordings**, set the source recording back to `editing`. Its `published` status is now a lie, and that status is only ever a note to yourself |
| 6 | Re-cut from the source with the §8 Phase 3 review gate actually applied |

**Prevention, ranked:** the §8 Phase 3 per-clip review gate catches most of it; Private-first
(§6.2) catches the rest; a full logged-out watch before going Public catches what both missed.

**The structural fix if this happens twice:** stop publishing on the same day you record. A clip
reviewed the next morning gets a judgment the clip reviewed at midnight does not.

### 9.8 YouTube upload fails

| Cause | Fix |
|---|---|
| Token expired | Re-authorize in **Social**. YouTube's flow requests `access_type: offline`, so this should be rare |
| Missing scope | `post-video` needs `youtube.upload`. Re-authorize with the right capability selected |
| API not enabled | Enable **YouTube Data API v3** in Google Cloud Console |
| Quota exceeded | YouTube's upload quota is daily. Wait, or upload by hand |
| File too large / wrong format | Re-encode to H.264 MP4 |

**Fallback that always works:** upload at <https://studio.youtube.com>. The clip and thumbnail are
already on disk. Do not let an OAuth problem block a finished video.

### 9.9 marketing-crosswalk validate fails

**Symptom:** `python3 -m generator.cli validate` exits non-zero.

It is checking that marketing-doc anchors and status claims still hold in the **target** repo. A
failure usually means:

| Cause | Fix |
|---|---|
| Target repo not found | `export TASKMGMT_REPO_PATH=/path/to/Task-Management`, or pass `--target-path` |
| Target checkout is stale | `git pull` in that repo |
| An anchor moved | A heading was renamed in the target's marketing doc. Fix the anchor, in the right repo |
| A status claim no longer holds | A module's status changed here. That is the check working — it is telling you a marketing doc now lies |

Run `python3 -m generator.cli selftest` to confirm the templates themselves render — it writes
nothing, so it isolates template problems from target-repo problems.

### 9.10 "No runnable committed workflows are bundled"

The app's own catalog, not ComfyUI's, is empty. This is a **build** problem: the committed workflows
did not make it into the bundle. Rebuild from §3.3–3.4. Adding workflows in ComfyUI's web UI will
not fix it — `comfyui_workflows` deliberately lists committed workflows rather than whatever a live
ComfyUI's userdata happens to have saved.

---

## Where this guide's material comes from

| Section | Sources |
|---|---|
| Prerequisites | [`realtime-ai`](../../../modules/realtime-ai/setup/manual.md), [`models.md`](../../../modules/realtime-ai/comfyui/models.md), [`content-creation`](../../../modules/content-creation/setup/manual.md), [`image-editing`](../../../modules/image-editing/setup/manual.md), [`storage-data`](../../../modules/storage-data/setup/manual.md), [`model-registry`](../../../modules/model-registry/README.md) |
| Hardware | [`STREAM_AUTOPILOT_GAME_EVALUATION.md`](../../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md) |
| Build | [`apps/creator-extend/src-tauri/src/lib.rs`](../../../apps/creator-extend/src-tauri/src/lib.rs), [`comfyui.rs`](../../../apps/creator-extend/src-tauri/src/comfyui.rs), [`workflow_inputs.rs`](../../../apps/creator-extend/src-tauri/src/workflow_inputs.rs), [`tool_runtime.rs`](../../../apps/creator-extend/src-tauri/src/tool_runtime.rs), [`configs/setup/creator-extend.json`](../../../configs/setup/creator-extend.json), [`desktop-setup.md`](../../../modules/infrastructure/setup/desktop-setup.md) |
| Recording library | [`apps/shared/recording-library/README.md`](../../../apps/shared/recording-library/README.md), [`src/lib.rs`](../../../apps/shared/recording-library/src/lib.rs), [`RecordingLibrary.svelte`](../../../apps/shared/ui/RecordingLibrary.svelte), [`PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md`](../../proposals/PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md) |
| Pipeline | [`stream_shorts`](../../../modules/content-creation/stream_shorts/README.md), [`plugins/blender-addon/`](../../../plugins/blender-addon/), [`plugins/krita-integration/`](../../../plugins/krita-integration/) |
| Publishing | [`catalog.yaml`](../../../modules/social-management/catalog.yaml), [`apps/shared/social-manager/README.md`](../../../apps/shared/social-manager/README.md), [`social-management`](../../../modules/social-management/setup/manual.md), [`ProfileSwitcher.svelte`](../../../apps/shared/ui/ProfileSwitcher.svelte) |
| OpenTech cross-links | [`marketing-crosswalk`](../../../modules/marketing-crosswalk/setup/automated.md), [`PROPOSAL_AI_LEARNING_SERIES.md`](../../proposals/PROPOSAL_AI_LEARNING_SERIES.md), [`docs/learning/`](../../learning/README.md) |
