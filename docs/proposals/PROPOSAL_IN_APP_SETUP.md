# Proposal: Open apps first and extend in-app setup

**Queue row:** `P-063`
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — Native installers, shared setup jobs and clean-host recovery
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — clean-host/device/signing acceptance remains open; the queue is authoritative.
**Date:** 2026-10-08 extraction; original dated slice records preserved below.
**Roadmap layers:** Infrastructure; shared desktop setup and module-owned installation.

This document preserves the setup scope and dated evidence formerly inline in the proposal
queue. Extraction does not renew old test results, promote a module or close hardware gates.
The old queue anchor remains a redirect for existing references.

## P-063 — Open apps first and extend in-app setup

**Direction adopted 2026-09-12; installer implementation authorized 2026-09-12.** This is the next setup extension to
P-003, not a new module. Infrastructure owns workstation bootstrap/distribution integration;
`apps/shared/setup-wizard`, `apps/shared/setup-engine` and the shared UI own local execution,
evidence and presentation. Module-specific recipes stay with their modules. P-001 still owns
release signing/distribution gates; opening the private prototype need not wait for public release.

### Evidence and problem

Reviewed PR #41 (private development evidence; not distributed), including
its body, commit list and setup-file patches. Its Windows CI evidence covers a PowerShell plan,
capture diagnostics and streaming rehearsal; it explicitly leaves fresh-host winget installs and
native Windows desktop acceptance open. There are no PR review/comment logs identifying the
owner's workstation failure. OBS trouble and possible Docker trouble are owner-reported;
the exact command, exit code and Docker state remain unknown.

The concrete path gap is visible in `scripts/setup/windows.ps1`: `-InstallDesktopApps` means
OBS/FFmpeg, not the Extend apps; a winget failure throws before later module work; Docker is
neither installed nor started; the final message assumes Stream Extend already exists.
`docs/SETUP-TECHNIQUE-NOTES.md` also previously required `make up` before any desktop app.
That order is superseded by the [desktop launch guide](../../modules/infrastructure/setup/desktop-setup.md).

### Delivery order

1. **Get each app open.** Produce versioned Windows installable artifacts for both apps, with
   checksums, WebView runtime handling and first-launch evidence; keep a clearly separate source
   developer path. End the bootstrap at an open Module setup view. No OBS, Docker/WSL, Python,
   GPU models, account registration or cloud connection may gate the packaged shell. Windows
   signing/public distribution follow P-001; private acceptance artifacts must be labelled.
2. **Move repeatable work into the app.** Extend the existing shared native runner with packaged,
   versioned, allowlisted recipes: detect/install Python first, then selected Python requirements,
   optional OBS/FFmpeg, and supported module configuration. Reuse the same recipes from the CLI;
   do not invoke today's broad Windows preset wholesale from an app button. Keep recipe/package
   choices in config, accept validated action IDs/arguments, and expose no arbitrary shell input.
3. **Guide the remaining steps.** Show installed/running/connected/verified separately. For OBS,
   distinguish missing executable, stopped app, disabled WebSocket, bad credentials and recording
   acceptance. For selected container features only, distinguish absent Docker, stopped daemon,
   unavailable virtualization/WSL, pending reboot and failed service health. Link the exact manual
   step when automation cannot finish. Never infer that the reported Windows blocker was WSL.
4. **Make recovery routine.** Preview the affected packages/configuration and expected downloads,
   request local consent for changes, retain redacted logs and step results, reuse completed work,
   and offer retry or skip for optional steps. Represent installer/UAC/reboot handoffs explicitly;
   resume by rechecking state after restart. Preserve shared-environment locking across both apps.
   Only claim cancellation where the child installer can actually be stopped safely.

AI should explain unusual failures and help improve recipes. It should not be required to paste
standard commands, watch installers, or repeat checks. Account sign-in, OS elevation/reboot,
licence acceptance, physical cabling and picture/audio judgement remain user handoffs where needed.
Local setup must work without an AI session, relay subscription or remote approval service.

### In-app automation work queue

This is the proposal item for setup work that previously lived in scattered module notes. Items
stay here until their app action, failure states and native acceptance are recorded.

| Order | Item | App-owned result | Agent model / effort | State |
|---|---|---|---|---|
| 1 | Python bootstrap | Detect Python 3.11+, install fixed Python 3.12 through winget or existing Homebrew, persist job/log, recheck before enabling module dependencies | `gpt-6.1-sol` / `high` — Fixed native bootstrap and shared job locking | **Built 2026-09-13; Windows installer integration passed; clean missing-Python install/restart acceptance open** |
| 2 | OBS onboarding | Detect/install/launch OBS, classify WebSocket failures, preview versioned scene/profile changes and run recording acceptance | `gpt-6.1-sol` / `high` — Native OBS connection, scene and recording safety | **Code built 2026-09-13; clean Windows install/launch and real picture/audio recording acceptance open; scene application awaits a validated collection export** |
| 3 | Docker/WSL setup | Classify Desktop/daemon/virtualization/WSL/reboot state and start only services required by selected modules | `gpt-6.1-sol` / `high` — Native package jobs, credentials and private service startup | **Code built 2026-09-13; clean Windows install/WSL/reboot recovery and real daemon/service acceptance open** |
| 4 | FFmpeg helper | Detect version/path and install or package a pinned verified helper | `gpt-6.1-sol` / `high` — Fixed native helper installation and restart recovery | **Code built 2026-09-13; clean Windows install/restart and real capture acceptance open; a pinned sidecar remains a future distribution decision** |
| 5 | Selected Python modules | Resolve selected dependencies, create shared environments, install/check, retain logs and retry | `gpt-6.1-sol` / `high` — Shared dependency installs, locking and retry | Built under P-003 |
| 6 | ComfyUI preflight | Check endpoint, nodes, fixed model choices, VRAM and workflow compatibility before queueing | `gpt-6.1-sol` / `high` — Native workflow validation and GPU acceptance | **Code built 2026-09-13; fake-server contract and native packaged-shell acceptance pending. Model terms, model downloads and visual output acceptance remain user-owned.** |
| 7 | Creator tool packaging | Bundle allowlisted Blender/Krita/posture scripts and remove source-checkout path assumptions | `gpt-6.1-sol` / `high` — Packaged native tool execution and approved file paths | **Krita/posture, Blender addon payload, a bounded Blender batch-render planner and required asset-pipeline sources are packaged into a versioned private runtime; the app runs side-effect-free package/import checks and reports selected Python/Blender state. Actual render execution and real DCC acceptance remain open.** |
| 8 | Storage/workflow bootstrap | Run selected Compose profile, migrations, bucket initialization and n8n imports as resumable jobs | `gpt-6.1-sol` / `high` — Database initialization, secrets and repeat-run recovery | **Code built 2026-09-13; real Docker execution, repeat-run and Windows credential-manager acceptance open** |
| 9 | Audio setup | Detect routing tools, guide config import, verify levels and OBS hotkeys | `gpt-6.1-sol` / `high` — Audio isolation, hotkeys and audible track verification | Routing-tool detection and bundled reference guidance built (2026-10-04); live levels/hotkey acceptance open; routing judgement stays manual |
| 10 | Model and social readiness | Verify local files/checksums/licenses and expose exact provider/account handoffs | `gpt-6.1-sol` / `high` — Model rights, OS credentials and account readiness | Partial module checks exist; downloads, terms and accounts stay user-owned |


### Acceptance and measurement

For **each app**, use a clean Windows machine with no developer toolchain, Python, OBS, Docker,
WSL, models or account configuration. Install the artifact and reach a usable Module setup view,
open a bundled guide, save a selection and reopen. Record artifact version/hash, Windows version,
time from installer start to usable view, user actions and any terminal/AI interventions; report
app-open and first verified workflow timings separately. No speed claim before measurement.

Then run a selected small module setup, skip OBS, exercise an OBS install failure and absent/stopped
Docker, and confirm unrelated setup and the Dashboard remain usable. Test retry after interrupted
installation, restart/reboot recovery and reuse from the second app. Retain Windows credential
storage and real OBS recording/Creator output acceptance as separate capability proofs. Repeat
app-shell and runner acceptance on macOS before claiming parity. Add failure/recovery contracts
and run the matching [verification rows](../agent/VERIFICATION-MATRIX.md) plus `make test`.

**This documentation change:** no application/script changes and no fresh Windows acceptance run.
Verified the Docs only row: full `make test` reached 100%, exit 0
(`/tmp/hcp-app-first-docs-test.log`); `git diff --check` passed. Native Windows source-build,
installer, first-launch timing and new runner acceptance were not run; this session changes docs only.


### P-063 installer slice — 2026-09-12

The owner explicitly requested **Build installers** after the documentation change. Added a
Windows x64 release NSIS workflow for both apps with per-user installation, shared Start menu
folder and embedded WebView2 bootstrapper. The bootstrapper downloads the runtime only when
needed; OBS, Docker and Python are not prerequisites for app installation/launch. CI installs
into a temporary path containing spaces, launches outside the source checkout, requires a live
native window with the correct title and records optional accessibility/screenshot evidence.
Artifacts carry SHA-256 checksums, source/target metadata and private pre-release instructions;
the workflow has read-only repository permission and does not publish a GitHub release.

Local evidence: both release Apple Silicon DMGs built successfully (about 6.8 MiB each), passed
`hdiutil verify`, and were mounted/copied to `/tmp/hcp-installer-acceptance/`. Both extracted apps
launched from there; on the MacBook built-in display each rendered Module setup, opened the
bundled Soundboard guide and reached its Dashboard with OBS/ComfyUI disconnected and operational
controls gated. Source paths were not needed to render those guides. Existing machine settings
were present, so this is not clean-machine acceptance. DMGs, checksums and metadata are collected
in `output/installers/stream-extend-macos-arm64/` and `output/installers/creator-extend-macos-arm64/`.
These Mac executables have ad-hoc signatures; no Developer ID signing or notarization is claimed.

Verification: both Svelte checks report zero errors/warnings; Stream native suite 15 passed;
Creator native suite 31 passed and one explicitly live test ignored. Full `make test` reached
100%, exit 0 (`/tmp/hcp-installers-test.log`); docs integrity passed
(`/tmp/hcp-installers-docs.log`); marketing validation confirmed 34 anchors and 26 status claims;
`git diff --check` passed. The first Windows run (34730836855) reproduced a clean-runner packaging-order defect:
Rust tests invoked `generate_context!` before `frontendDist` existed. A regression test failed
before the fix and passed after moving the Tauri build before the tests. CI now tests the release
profile to reuse native build output and retains dependency caches even after failure. Corrected Windows
run 34731199259 (private development evidence; not distributed)
built both release NSIS installers, passed native tests, installed both with exit 0 and opened
each installed executable outside the checkout. Installer-to-native-window times were 2.78 seconds
for Stream and 2.98 seconds for Creator on the hosted runner, where WebView2 already exists.
These are CI measurements, not a clean-workstation speed claim. Windows accessibility returned
only the WebView wrapper (`setup_text_observed: false`); visual inspection of both retained
screenshots separately confirmed the rendered Module setup view with zero modules selected.
The Windows installers are about 6.2 MiB each. Downloaded installer hashes match their manifests.
Downloads (GitHub repository access required; artifacts retained for 30 days):
Stream Extend Windows (private development evidence; not distributed)
and Creator Extend Windows (private development evidence; not distributed).
Local copies are under `output/installers/<app>-windows-x64/`; retained reports/screenshots are
under `output/installer-smoke/<app>/`.
Additional in-app prerequisite recipes, clean physical Windows acceptance and public signing
remain open under P-063/P-001. No module status is promoted.

### P-063 Python bootstrap slice — 2026-09-13

The owner asked for the other repeatable setup features to become one proposal item and for its
first item to be built. The ordered work queue above now holds ten app-owned setup results, led by
Python and followed by OBS, Docker/WSL, FFmpeg, ComfyUI and packaged Creator actions.

Both apps now check for Python 3.11+ before enabling selected dependency installation. When it is
missing, Module setup can run one fixed native command: the per-user `Python.Python.3.12` winget
package on Windows or `python@3.12` through an already-installed Homebrew on macOS. The frontend
cannot supply a command, package, path or argument. The child process runs without a shell and
writes durable job metadata and a local log; completion requires a successful exit followed by a
fresh interpreter check. A shared OS file lock prevents Stream Extend and Creator Extend from
starting the bootstrap together and is released by the operating system if an app exits.

Local verification: the shared plugin has seven passing tests, including exact fixed arguments
and lock contention/release; Stream has 15 passing native tests; Creator has 31 passing native
tests with one live ComfyUI test explicitly ignored. Both Svelte checks report zero errors and
warnings and both production frontend builds pass. A rebuilt native Stream Extend bundle opened
on the MacBook built-in display and showed the Python card, detected Homebrew interpreter path,
enabled dependency action and updated capture test. The package install action was not run because
this host already has a compatible interpreter. The required offline `make test` suite reached
100% with exit 0, Ruff passed across `modules/` and `scripts/`, marketing validation confirmed 34
anchors and 26 status claims, and `git diff --check` passed. Windows installer
run 34770709011 (private development evidence; not distributed)
passed both release builds, native suites, NSIS installs, installed-app launches and artifact uploads.
The resulting private artifacts are Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed),
retained through 2026-10-13. The runner already had Python, so clean Windows missing-Python install,
proxy/error handling and restart acceptance remain open.

### P-063 OBS onboarding slice — 2026-09-13

The second work-queue item now uses the same bounded package-job runner as Python. Both apps detect
OBS in standard Windows and macOS locations and expose one fixed install action: the exact
`OBSProject.OBSStudio` winget package or `brew install --cask obs` through an existing Homebrew.
The frontend cannot supply a package, executable or argument. Package progress, redacted logs,
restart recovery and the shared cross-app file lock use the existing setup job contract. Once OBS
is present, the app opens only the detected executable and reports installed and running states
separately.

Stream Extend adds an authenticated WebSocket diagnostic that distinguishes unreachable service,
rejected password, incompatible OBS/obs-websocket and handshake failure. When the connection is
ready, the operator can explicitly run a three-second recording test. It refuses to interrupt an
existing recording, starts and stops through the existing OBS client, and accepts only a returned,
non-empty local file; the UI displays its basename and size without exposing the recording path.

Both apps bundle and preview `modules/creator-experience/scenes/default.json` as an eight-scene,
versioned plan. That file contains no sources, so this slice deliberately does not import or
overwrite an OBS collection. Encoder choice, filters, capture-source mapping, WebSocket enablement,
password choice and picture/audio judgement remain visible operator steps until a real exported
collection and hardware pass exist.

Local verification: the shared setup plugin has nine passing tests, and the Stream release suite
has seven library plus eleven OBS contract tests. Those contracts cover exact rejected-password
classification, reachable/unreachable states, non-empty recording evidence and refusal while
recording is active. Creator's release suite passes eleven library, twelve ComfyUI and eight
workflow-input tests, with one live test explicitly ignored. Both production frontends build and
both Svelte checks report zero errors and warnings. The rebuilt native Stream Extend bundle opened
on the MacBook built-in display, identified `/Applications/OBS.app` as installed but stopped,
exposed **Open OBS Studio** and **Recheck OBS**, and expanded the source-free eight-scene preview
with its version identifier and overwrite warning. No real OBS process or recording was started
during that inspection. Full `make test` reached 100% with exit 0
(`/tmp/hcp-p063-obs-test.log`); Ruff, marketing validation (34 anchors and 26 status claims) and
`git diff --check` passed. Windows installer
run 34772580178 (private development evidence; not distributed)
passed both release builds, frontend and native suites, NSIS installations, installed-app launches
outside the checkout and evidence uploads. Private artifacts are
Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed).
The runner already had OBS, so clean Windows installation/error recovery and a real local
picture/audio recording remain open.

### P-063 Docker/WSL setup slice — 2026-09-13

The third work-queue item now uses the same shared runner and cross-app lock. Both apps separately
detect Docker Desktop, the Docker CLI, daemon and Compose. Windows additionally runs fixed
`wsl.exe --status` diagnostics and decodes its UTF-16 output. The state machine reports missing
Docker, stopped Desktop, unreachable daemon, missing Compose, requested WSL update, unavailable
virtualization and pending reboot without turning a generic daemon failure into a guessed WSL
problem.

Module setup previews the exact service list resolved from the selected catalog modules and their
dependencies. Service names must also pass a compiled allowlist. The frontend cannot supply a
Compose file, service, executable, package or argument. When Docker Desktop is absent, the app can
run the fixed `Docker.DockerDesktop` winget package or Homebrew `docker-desktop` cask; when present,
it opens only the detected executable and waits a bounded time for the daemon.

The selected-service action unpacks the versioned root Compose file and its required build/config
trees into shared app data, creates a private persistent local environment with random credentials,
and invokes `docker compose` directly without a shell. It starts only the selected services,
retains a local log and job record, and waits up to two minutes for each planned service to report
Up without a starting or unhealthy state. The app refuses to generate new credentials over an
existing `hybrid-creator-platform` Compose project it did not initialize. Migrations on existing
databases, MinIO bucket initialization, n8n workflow import and a safe credential handoff remain
work-queue item 8.

Local verification: the shared plugin has 15 passing tests covering the exact Docker Desktop
package-manager arguments, dependency resolution, service allowlist, exact Compose argument
construction, persistent private credentials, bundled runtime trees, UTF-16 diagnostics and
failure classification. Both Svelte checks report zero errors and warnings and both production
frontends build. Stream's release suite passes seven library plus eleven OBS contract tests;
Creator's passes eleven library, twelve ComfyUI and eight workflow-input tests, with one live test
explicitly ignored. A rebuilt native Stream Extend bundle opened on the MacBook built-in display,
reported Docker Desktop as absent, kept the install and recheck actions usable, disabled service
startup, and previewed exactly `postgres`, `redis`, `minio`, `fastapi` and `nodecg` for the saved
Broadcast Graphics selection. The install action was not run. Full `make test` reached 100% with
exit 0 (`/tmp/hcp-p063-docker-test.log`); Ruff passed; marketing validation confirmed 34 anchors
and 26 status claims; its self-test rendered 149 subject/asset pairs; and `git diff --check` passed.
This Mac has no Docker CLI or Docker Desktop, so Compose configuration against the Docker CLI, the
real daemon/service startup path and clean Windows install/WSL/reboot recovery remain open and are
not claimed from contract tests.

Windows installer run 34774993481 (private development evidence; not distributed)
first passed both builds, native suites, NSIS installs and installed-app launches, but its retained
screenshots exposed a foreground Windows Terminal opened by the Docker status probe. That visual
evidence was rejected even though the workflow was green. Commit `80cc620` applies Windows
`CREATE_NO_WINDOW` to setup probes and background jobs while keeping explicit OBS and Docker
Desktop GUI launches unchanged. Corrected run 34775759921 (private development evidence; not distributed)
again passed both release builds, native suites, NSIS installs, installed-app launches and evidence
uploads. Visual inspection of both corrected screenshots shows the Extend window in front with no
terminal. Stream installed in 5.05 seconds and reached its window in 5.61; Creator installed in
2.89 seconds and reached its window in 3.46 on Windows `10.0.26100.0`. These are hosted-runner
measurements, not clean-host timing. Private artifacts are
Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed).
Their installer SHA-256 values are `613dbfd09ef167c86bc80c698d8919e2b95a996cdb02c2612a42331643f1e093`
and `ee23b325f6cd2478dee2062b13f2b891ec1d4e472dd1d61420ad8b2310cf41f4`,
respectively. The hosted runner did not install Docker Desktop or start real services, so those
acceptance items remain open.

### P-063 storage/workflow bootstrap slice — 2026-09-13

After the selected Docker services are healthy, either app now exposes one explicit
**Initialize data & workflows** action. The job runs fixed Compose helper services directly,
without accepting a command, path, image or service from the frontend. It applies the bundled
storage and AI-agent SQL migrations in filename order, verifies both resulting tables, creates
all seven expected MinIO buckets, reapplies the recordings lifecycle safely, and verifies each
bucket. When `automation-control` is selected it also imports the bundled inactive n8n workflow.
The workflow now has a stable ID, so a repeat import updates the same record instead of creating
another copy.

Each step has a durable pending/running/finished/failed state and shares the existing cross-app
lock. Helper containers receive generated credentials through the private Compose environment;
secrets are absent from command arguments, job JSON and logs. On success the app stores the local
service credentials in the OS credential manager and writes Creator Extend's MinIO pair under its
existing credential names for reuse after restart. Explicit MinIO, n8n, Grafana and local API copy actions
send only the selected value to the Windows/macOS system clipboard and return a redacted label.
Provider credentials inside n8n workflows, cloud resources and destructive resets remain manual.

Contract verification covers the selected-service-to-step plan, exact fixed Compose arguments,
bundled helpers, private environment parsing and credential action allowlist. Both Svelte checks
and production builds pass. The shared plugin has 18 passing tests in both app lockfiles; the full
Stream and Creator release suites pass, with Creator's one explicit live ComfyUI case ignored.
Ruff, the marketing crosswalk validation and 149-pair self-test, `git diff --check`, the required
full `make test`, and a fresh Stream Extend debug app bundle also pass. This workstation has no
Docker daemon, so the helper containers, repeat-run behavior and OS credential handoff have not
received live acceptance; no storage, automation or app module status is promoted from this code
evidence.

Windows installer run 34792596767 (private development evidence; not distributed)
passed both frontend checks, release NSIS builds, native suites, real NSIS installations and
installed-app window launches outside the checkout. Stream installed in 2.24 seconds and reached
its window in 2.81 seconds; Creator installed in 2.37 seconds and reached its window in 2.94 seconds
on Windows `10.0.26100.0`. The retained screenshots show each Module setup shell in front with no
terminal window. Stream rendered its full module catalog; Creator was captured while its catalog
still displayed the loading state, so the Creator image does not prove a completed setup-plugin
response. Installer SHA-256 values are
`913b4c1dad5324b041a47449a53549c9c45faecc6738894641736c97e4811671` for Stream and
`f85d759271f96f77b4f2bdf482ec939a6abbefab6d417942422b60886dd28c75` for Creator. Private
artifacts are Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed),
retained through 2026-10-14. The hosted runner did not install Docker or run the new helper
containers, so real storage/workflow and credential acceptance remain open.

### P-063 FFmpeg helper slice — 2026-09-13

Both apps now expose a local **FFmpeg** prerequisite card before capture setup. The card searches
standard operating-system and package-manager locations plus `PATH`, runs only the discovered
executable with fixed `-version` arguments, and shows the verified path and first version line.
When it is missing, the only install actions are fixed `winget install --id Gyan.FFmpeg --exact`
arguments on Windows and `brew install ffmpeg` through an already-installed Homebrew on macOS.
The webview supplies no executable, package, path or argument. The shared runner keeps the
existing durable job metadata, redacted log, retry/recheck behavior and cross-app OS file lock;
post-install verification requires `ffmpeg -version` to succeed. A successful job directs the
operator to rescan capture hardware so prior discovery does not masquerade as fresh evidence.

Local verification: the shared plugin has 19 passing tests under both Stream and Creator lockfiles,
including exact package-manager arguments and the no-shell metacharacter guard. Both Svelte checks
and production frontend builds pass. The full required `make test` reached 100% with exit 0
(`/tmp/hcp-p063-ffmpeg-test.log`); Ruff passed; marketing validation confirmed 34 anchors and 26
status claims; its self-test rendered 149 subject/asset pairs; and `git diff --check` passed. A
fresh Stream Extend debug app and DMG bundle were built. Native macOS inspection used an isolated
copy of that bundle: it showed the missing-FFmpeg status with enabled **Install FFmpeg** and
**Recheck FFmpeg** actions, while the app shell, selected modules, OBS and optional Docker controls
remained usable. Installation was deliberately not run because it would mutate this workstation;
the host had no system FFmpeg. Clean Windows package installation, failure/restart recovery and a
real post-install capture probe remain external acceptance evidence. No module status is promoted.

Windows installer run 34794409110 (private development evidence; not distributed)
passed both frontend checks, release NSIS builds, native suites, real NSIS installations and
installed-app window launches outside the checkout. Stream installed in 2.39 seconds and reached
its window in 2.95 seconds; Creator installed in 2.55 seconds and reached its window in 3.13 seconds
on Windows `10.0.26100.0`. The retained screenshots show each Module setup shell in front with no
terminal; Creator rendered its full module catalog, while Stream was captured during catalog loading.
They do not exercise the FFmpeg install action. Installer SHA-256 values are
`c9affd2180773c70dbb67ef47eeed12e2529aef4d5867430bf2aafa3fa4ab748` for Stream and
`dd8bee92ac05e26e027ecb66ead8ef314056f81e7ca83aa692e0f070db3317d0` for Creator. Private
artifacts are Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed),
retained through 2026-10-14. The hosted runner has developer tools and WebView2 and did not install
FFmpeg, so clean-host package installation and recovery remain open.

### P-063 ComfyUI workflow preflight slice — 2026-09-13

Creator Extend now requires a bounded preflight before an operator can open the Configure editor
or queue a bundled workflow. The app reads the configured ComfyUI endpoint's `/system_stats`,
`/queue`, and `/object_info` responses and compares the graph's exact `class_type` values and
fixed model selectors (`ckpt_name`, `unet_name`, `clip_name`, `vae_name`, `lora_name`,
`model_name`, and upscale model selectors) with what that server reports. The workflow card
shows missing node classes or model files, selected model files that were found, and current GPU
name/free/total VRAM. It does not invent a VRAM threshold or claim that a compatible inventory
predicts quality. An unavailable model-choice inventory blocks the queue and names the value that
could not be checked. The native queue commands and approved relay queue repeat the preflight so a
stale card cannot bypass a changed server.

The preflight reads only a bundled workflow ID and fixed local endpoint; it accepts no path,
command, package or model download from the webview. Model terms, downloads, custom-node
installation and visual output judgement remain operator handoffs. Fake-server contracts cover a
compatible graph with a reported GPU, missing node/model classification, a disconnected endpoint,
and the queue guard. Local verification passed the complete Creator Rust suite (including the new
16-case ComfyUI HTTP contract), Creator Svelte check and production build, full `make test`, Ruff,
marketing validation (34 anchors/26 claims), marketing self-test (149 rendered pairs), Rustfmt and
`git diff --check`. A fresh Creator debug app and DMG bundle built successfully. An isolated copy
of that bundle rendered all ten workflow cards with the new disabled **Preflight** and
**Configure** controls while its current readiness evidence was blocked, which verifies the safe
disconnected packaged-shell state. No live ComfyUI endpoint was changed or workflow queued during
that inspection. Native happy-path preflight, model blocker and real output acceptance remain
separate Mac and Windows evidence; no module status is promoted by this code slice.

Windows installer run 34795936042 (private development evidence; not distributed)
passed both frontend checks, release NSIS builds, native Rust suites, real NSIS installations and
installed-app launches for source `9abb563`. Stream installed in 2.27 seconds and reached its
window in 2.84 seconds; Creator installed in 2.34 seconds and reached its window in 2.93 seconds
on Windows `10.0.26100.0`. Both reports identify the installed app window and show no terminal;
the Creator screenshot renders the complete Module setup shell. These installer smokes do not
connect ComfyUI or exercise a preflight. Installer SHA-256 values are
`c43ddef5a3a843c7e553703e5c878d97450fbb7f33c669e8b98a5c2d367beb48` for Stream and
`8f99531a348e1fa34596b3169d14de9b39fdfd032f3c501e2cc99451a30b7b9e` for Creator. Private
artifacts are Stream Extend (private development evidence; not distributed)
and Creator Extend (private development evidence; not distributed),
retained through 2026-10-15. The hosted runner includes developer tooling and WebView2, so it is
not clean-host or live-ComfyUI acceptance.

### P-063 Creator tool runtime slice — 2026-09-13

Creator Extend now compiles the three fixed Krita helper sources, its posture analyzer, the Blender
addon payload and the small asset-pipeline import tree into the desktop binary. Before either existing action runs, the
app materializes that exact allowlist under `HybridCreatorPlatform/creator-tools/runtime-v1` in
private local application data. Krita accepts only `batch_upscale`, `apply_style` or
`export_to_minio` and the built-in dry-run argument; it no longer accepts an arbitrary script
name, argument list or repository path. Posture likewise uses only its bundled analyzer. The
runtime contract verifies both its fixed six-file catalog and a reconstruction from a temporary
non-repository path.

This removes the source-checkout assumption for the packaged actions, but it intentionally does
not claim that an interpreter, `requests`/OpenCV, Blender/Krita installation, selected Python
environment, model, MinIO configuration or DCC output is ready. The Creative Tools panel now
offers **Check packaged actions**, which invokes each bundled script with `--help`, uses a selected
module virtualenv when present, and reports missing imports without touching user files or services.
The Blender handoff now also packages an installable addon ZIP and a bounded batch-render planner;
real Mac/Windows tool acceptance remains open. Local verification passed the Creator Rust suite, Svelte check/build,
full `make test`, Ruff, marketing validation/self-test, Rustfmt and `git diff --check`; a fresh
Creator debug app and DMG bundle also built on this Mac. No DCC, model, MinIO service or user file
was changed during the runtime test.

### P-063 packaged action doctor — 2026-09-14

The Creator dashboard now exposes **Check packaged actions** for the four fixed local scripts. The
command unpacks the versioned runtime, prefers the selected module virtualenv under the shared setup
root, and invokes each script with the side-effect-free `--help` flag. The result reports whether
the source is packaged, which interpreter was selected, and the import failure detail when a module
dependency is absent. The former dashboard dry-run buttons no longer send incomplete CLI arguments
that could only fail argparse; they now recheck the package and dependency boundary. This remains a
readiness check: it does not install Krita/Blender, download models, contact ComfyUI/MinIO, or claim
that a real DCC job succeeded. The doctor also reports whether the complete Blender addon payload
and bounded batch-render planner were unpacked and whether Blender itself was found; installing and
enabling that addon remains a Blender handoff. When Posture Screen is missing OpenCV or MediaPipe, the dashboard now
offers a direct link back to Module setup so the operator can select **Sports Analytics** and run the
existing shared dependency installer.

The Creative Tools panel also offers **Plan Blender batch render**. It accepts only an operator-
selected `.blend` file and output directory, then invokes the bundled Blender wrapper with
`--dry-run` to return the project path, output target and scene list. After a plan is visible, the
operator can explicitly confirm **Render planned batch** to run the wrapper's real render path;
the app does not treat process completion as visual or output acceptance.

Local verification: `cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml`
passed (13 unit/integration tests plus one ignored live ComfyUI test), `npm run check` passed with
zero diagnostics, Rustfmt and `git diff --check` passed. Fresh Windows installer acceptance and
the native Creator file-picker path remain open.

### P-063 local acceptance evidence — 2026-09-14

On the Mac acceptance host, Homebrew installed Blender 5.2.1 and Krita 5.3.3. Creator Extend
prepared `~/Library/Application Support/HybridCreatorPlatform/creator-tools/blender-addon.zip`;
Blender installed it through Preferences → Add-ons → Install and showed the enabled **Creator Extend**
sidebar panel. A real `/tmp/hcp-p063-acceptance/acceptance.blend` project was created, the bundled
planner returned its Scene list in dry-run mode, and the confirmed Workbench render wrote a valid
320×240 PNG at `/tmp/hcp-p063-acceptance/blender-output/Scene.png` (SHA-256
`62646407efa9bde8db90cffa16a09b634d5f764a84c92d6d5e51289c576f60a0`).

Sports Analytics requirements were installed into the shared module environment. Posture Screen
processed the real acceptance artifact at the now-absent `modules/realtime-ai/comfyui/app/output/outpaint_00001_.png` and returned
33 landmarks plus shoulder/hip alignment flags. ComfyUI started at `127.0.0.1:8188` on Apple MPS;
MinIO started at `127.0.0.1:9000`, and `export_to_minio.py` uploaded the image to
`artwork/acceptance/outpaint_00001_.png` (209,725 bytes), verified by listing the bucket. The live
batch-upscale and style-transfer actions reached ComfyUI but were rejected with HTTP 400: the
installed ComfyUI node schemas require additional inputs (upscale) and the committed IPAdapter
workflow needs a current node/model contract (style). Their dry-run paths pass with the same real
image. The native Creator picker surfaced after adding the dialog capability; selecting the file
through this automated desktop pass was unreliable, so the planner was also exercised directly
with the same bundled wrapper. The picker capability is now covered; a clean operator click-through
remains for final desktop acceptance.

### P-063 audio setup slice — 2026-10-04

Owner requested a Sol scoped build. Setup item 9 uses `gpt-6.1-sol` / `high` for
bounded local routing-tool detection and configuration guidance. Both apps now show an
Audio routing panel when Audio Production or Soundboard is selected (including dependencies).
A fixed, parameter-free native command checks configured standard locations for BlackHole,
Loopback, VoiceMeeter Potato or PipeWire and returns only current installation evidence.
Missing/custom-path installations are not called uninstalled; tool presence never promotes
an audio capability. No Python, shell, driver installation or audio-routing change is needed.
The platform's bundled reference and four off-air acceptance steps remain accessible even
when no routing tool is found. All three references and the recipe catalog ship in the app.

Review found no proof that the repository's custom VoiceMeeter XML is compatible with
VoiceMeeter's Load Settings format. The panel and setup docs now call it a reference template
and recommend saving an actual tool-generated preset before attempting an import. The macOS
JSON is also a reference, not a Loopback preset. Audible levels, physical mix-minus,
OBS hotkeys and Windows/Linux native acceptance remain open; this slice does not close item 9
or promote audio-production. Model metadata is the assigned execution choice, not evidence
of a client-side model switch.

Verification: `cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml
-p tauri-plugin-module-setup -- --nocapture` passed all 23 shared tests, including four audio
checks. The actual macOS probe reported BlackHole and Loopback not found in standard locations,
with audio capability `not_verified`. Full Stream Rust tests passed (8 unit + 13 integration);
Creator tests passed (13 unit + 16 production-job + 8 workflow tests; one live ComfyUI test
ignored). Both apps' `npm run check` returned zero errors/warnings and `npm run build` passed.
Both `npm run tauri -- build --bundles app` commands produced Mac `.app` bundles.
`PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test` reached 100%, exit 0.
Rustfmt and `git diff --check` passed. Native panel click-through was attempted but computer-use
reported the Mac locked and automatic unlock unavailable; it remains pending along with
physical audio/OBS and Windows/Linux acceptance.

P-063 audio follow-up — 2026-10-04: retrying the actual Stream app through computer-use
again reported the Mac locked; no native UI or physical audio pass is claimed. A reference
review reproduced two defects with offline regression tests: the macOS JSON assigned
Built-in Output as Discord's input, and the canonical bus map disagreed with the recording
track table. Corrected the call input to a physical mic or dedicated mix-minus input;
made Track 1 the full mix with Tracks 2–6 isolating mic, desktop, AI voice, calls and music.
The bundled manual guide and routing guide now agree and distinguish track assignment from
recording-track enablement and listening acceptance. The two checks failed before the fixes
(2 failed, 5 passed) and pass afterward (7 passed in 0.07s); Ruff passed. Both app setup
capabilities grant only the local `main` window, with no remote-origin grant, and the audio
command accepts no paths or executable arguments. Follow-up verification: the fresh full offline `make test` suite reached 100%, exit 0;
the shared plugin suite passed 23 tests; both `npm run tauri -- build --bundles app` commands
finished successfully with the corrected bundled references/manual guide. `git diff --check`
and Ruff passed. Mac executable SHA-256: Stream
`d4357cb9e1c640ff4b88e07d2e7c7250aa1032cec0d2f4c58a99d89a90ba16bb`;
Creator `20d1d25a5fb46658ec15619a738486d21ff0fb557fc6929c0b25f6f43a8b3bfd`.
These identify the built executables, not a native UI or audio acceptance pass.
