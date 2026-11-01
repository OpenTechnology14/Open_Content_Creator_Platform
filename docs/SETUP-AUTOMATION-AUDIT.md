# Setup automation audit

**Status:** Working inventory · **Reviewed:** 2026-09-13 · **Owner:** OpenTechnology14

This audit identifies which workstation steps belong in the native installers, which belong in
Stream Extend or Creator Extend, and which still need a person. It extends
[P-063](PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup), and does not promote any
scaffolded module. Routine, deterministic work should be available locally without an AI session
having to paste commands or watch a process.

## Current evidence

The packaged apps open to Module setup without OBS, Docker, Python or a cloud account. The shared
setup plugin bundles the catalog, guides, requirement files, dependency runner, capture scanner
and the files needed by its selected local Compose plan. The UI invokes the scan, lets the operator
choose video and audio devices, and saves only IDs from the latest report.

The capture scan starts as an inventory check. `scripts/setup/capture_devices.py` uses FFmpeg
DirectShow/AVFoundation enumeration and Windows Plug and Play fallback; it does not open a capture
stream. The new **Test selected capture (3s)** app action adds a bounded probe after selection. It
records separate signal and recording evidence, but a discovered card or passing probe still does
not replace physical cabling, HDCP or picture/audio acceptance.

The Docker action now detects Desktop, CLI, daemon and Compose separately; reports WSL status on
Windows; previews the exact catalog-resolved service list; and starts only a compiled service
allowlist from versioned bundled resources. It creates a private persistent local environment,
retains job logs and final service states, and leaves unrelated app controls usable. The follow-on
app job applies migrations, initializes and verifies MinIO buckets, imports the selected stable
n8n workflow, saves credentials to the OS store and exposes bounded clipboard handoffs. Real
Docker execution, repeat-run and clean Windows credential acceptance remain open.

Several native bridges still assume a source checkout. Creator's Blender, Krita and posture
commands use repository-relative paths and `python3` (`apps/creator-extend/src-tauri/src/blender.rs`,
`krita.rs`, `posture.rs`). Stream Autopilot is a useful counterexample: it unpacks an allowlisted
runtime into app data and uses the selected module environment (`apps/stream-extend/src-tauri/src/autopilot.rs`).
That pattern is the right basis for packaged deterministic actions.

## What belongs where

| Priority | Capability | Installer or app action | Human handoff / boundary | Evidence and gap |
|---|---|---|---|---|
| P0 | Open and repair the shell | Installer installs per-user app, shortcut, WebView runtime and versioned resources; app offers repair/recheck | SmartScreen, UAC, reboot, network outage | Windows NSIS and Mac DMGs exist. Public signing/notarization and clean-host acceptance remain open. |
| P0 | Python availability | App detects a supported interpreter and offers a fixed Python 3.12 package-manager bootstrap; persist progress and resume | Package-manager availability, OS elevation, reboot, proxy and license prompts | Built for Windows winget and an existing Homebrew installation on macOS. Clean Windows install/restart acceptance remains open; bundling a sidecar remains an alternative. |
| P0 | Capture-card readiness | **App:** Scan → select card/audio → bounded test signal/recording → report signal/video/audio/frames and accept evidence | Plugging HDMI/USB, granting camera/mic permissions, judging picture/audio, HDCP or vendor driver/licence issues | Scan/save and the three-second probe exist. Preview mode, sync measurement and physical Windows acceptance remain open. Keep “detected”, “signal”, and “recorded” as separate states. |
| P0 | OBS launch and connection | **App:** locate/install OBS, launch it, show WebSocket state and actionable error class; preview the versioned scene skeleton and run bounded recording acceptance | OBS first-run prompts, encoder choice, permissions, password, scene sources and real picture/audio judgement | Built: fixed winget/Homebrew install, standard-path launch, process/WebSocket states, rejected-password/version classification and Stream three-second recording proof. The bundled source-free scene skeleton is preview-only; real collection import, encoder, filters and WebSocket configuration remain manual. |
| P0 | Docker-backed features | **App:** detect Docker Desktop/CLI/daemon/Compose/WSL state, preview and start only selected allowlisted services, retain logs and final health states | Docker first-run/elevation, virtualization/WSL enablement, reboot, credentials and cloud endpoints | Code built: fixed winget/Homebrew bootstrap, detected-app launch, catalog dependency plan and bundled Compose runtime. Clean Windows install/recovery and real daemon/service acceptance remain open. Never let this block unrelated controls. |
| P1 | FFmpeg and small local helpers | **App:** detect the system path/version, install a fixed verified package, retain a durable job and recheck | Firewall, antivirus, codec/licence and PATH policy | Built: Windows uses fixed `Gyan.FFmpeg` winget arguments and macOS uses an existing Homebrew. The app verifies `ffmpeg -version` after success; clean Windows install/recovery and a pinned sidecar decision remain open. Capture discovery can still use `imageio-ffmpeg` as a local Python fallback. |
| P1 | Selected Python modules | **App:** choose modules, create shared environment, install requirements, check versions, retry failed modules and reuse the environment from the other app | Packages requiring GPU drivers, private indexes or model terms | Selective install, lock, atomic reports and retry already exist. This is the strongest current in-app automation slice. |
| P1 | ComfyUI and local GPU | **Creator app:** preflight each bundled workflow against the endpoint, graph node classes and fixed model choices; show GPU/VRAM, then queue/poll and preserve outputs; offer a launcher only when a supported runtime is packaged | GPU driver, VRAM sufficiency, model download/licence, custom node installation and visual quality | Built: Configure and every native/approved relay queue repeat the inventory preflight. It reports missing nodes/models and current VRAM, but has no invented VRAM threshold and does not claim that inventory proves a usable output. The realtime module has no launcher; live ComfyUI and visual acceptance remain open. |
| P1 | Creator tool launch | **Creator app:** detect Blender/Krita and open a selected project/file; package allowlisted scripts or sidecars with explicit inputs | Install/update the DCC, plugin enablement, file permissions and visual review | Krita/posture helpers, the Blender addon payload, a bounded batch-render planner and their small asset-pipeline import tree now unpack from a versioned private runtime. The Creative Tools panel runs fixed `--help` package/import checks, reports the selected module virtualenv and Blender executable state, and links missing Posture dependencies back to Sports Analytics setup. It can plan an operator-selected `.blend` and exposes rendering only after an explicit confirmation; output and visual acceptance remain manual. Blender addon installation/enablement and real DCC acceptance remain open. |
| P2 | Storage and workflow bootstrap | **App:** for selected local features, apply migrations, initialize buckets, import reference workflows, and run their checks as resumable jobs | Account/provider credentials, cloud endpoints and destructive data operations | Code built with fixed profile-gated helper containers, durable step states, OS credential storage and bounded clipboard handoff. Real Docker/repeat-run/Windows credential acceptance remains open. |
| P2 | Audio routing and soundboard | **App:** detect routing tools, open the right guide/config import, verify levels, and show configured OBS hotkeys | Driver install, GUI routing, mix-minus judgement, plugin dock and copyrighted user audio | Routing is OS/driver-bound; soundboard loading is OBS GUI-only. The app can guide and verify, but should not claim a successful mix from a config file. |
| P2 | Models, accounts and publishing | **App:** show model/credential/account readiness and link the exact next step | License acceptance, multi-GB downloads, OAuth/provider review, account ownership and publishing approval | These are intentionally user-owned or license-gated. AI can explain a failure, but must not be the required operator. |

## Capture-card workflow to build

The existing **Scan capture hardware** button should grow into a staged, local acceptance flow:

1. Enumerate the card and separate video/audio endpoints, as it does today.
2. Ask for the intended mode (for example 1080p60), then open a short read-only preview through
   the platform backend. Record whether frames arrive, observed rate, dimensions and timestamp
   continuity. Do not silently change the device format.
3. Measure audio presence, sample rate and video/audio drift when the card exposes both. Report
   “no audio endpoint” separately from “audio silent.”
4. Create or select a temporary OBS scene/profile, start a bounded local recording, stop it, and
   inspect the file for duration, video frames, audio stream and expected cadence.
5. Save device IDs and evidence timestamp only after the operator accepts the result. A saved
   selection remains configuration, not readiness.

The app should make physical actions visible (“connect console HDMI out → card HDMI in; connect
USB 3; wake the console”) and preserve a redacted report for retry. It must never bypass HDCP,
infer a working signal from Plug and Play, or turn a failed optional capture test into a global app
failure. Deterministic probes and the existing OBS client are sufficient; no AI inference is
needed.

## Installer design decisions

Keep the installer small and predictable: app binary, guides, manifests, icons, WebView handling,
shortcuts and repair/uninstall metadata. Large GPU models, Docker images, OBS plugins, vendor
drivers and account data should be downloaded or configured from an app action after the shell
opens. If Python or FFmpeg is bundled, use a pinned target-specific artifact, record its license
and checksum, scan/update it independently, and keep it out of the launch gate. Tauri's
[sidecar mechanism](https://v2.tauri.app/develop/sidecar/) can package a helper, but it does not
decide runtime licensing, GPU compatibility or safe updates.

Every app action should use a catalog-owned action ID and validated arguments. Show the affected
package/configuration before changes, stream redacted logs, make optional actions skippable, and
resume by rechecking state after an app restart or OS reboot. The same runner should serve the CLI
and both apps so a fix is made once.

## Recommended implementation order

1. Extend the new capture acceptance command with preview, sync measurement and a Windows
   physical-card pass; the bounded signal/recording probe and fixture tests now exist.
2. Complete clean-host acceptance for the built Python, FFmpeg and OBS actions, including
   package-manager failure, restart recovery and a real bounded capture probe.
3. Complete clean-host acceptance for the built selected Docker service and storage/workflow
   initialization actions, including repeat-run and Windows credential-manager behavior. Gate only
   container-backed controls.
4. Move Creator's repository-relative Blender/Krita/posture scripts into versioned bundled
   runtimes, then expose their existing deterministic operations as app actions.
5. Exercise the built ComfyUI preflight against a clean packaged Creator shell and a live server,
   then retain model terms, downloads and visual acceptance as operator handoffs.

This order keeps the first usable window fast, makes the stream-card blocker observable, and
replaces routine AI-operated shell work with reviewable local jobs.

## Verification required

For each new action, run the offline contracts and `make test`, then exercise it on a clean Windows
host with no Python, OBS or Docker. Capture-card work additionally needs a physical card with a
known HDMI source and a real OBS recording. Record artifact hash, OS, elapsed time, user handoffs,
report JSON and whether any terminal or AI intervention occurred. A passing package install,
device enumeration, or service connection is not a broadcast/content acceptance proof.
