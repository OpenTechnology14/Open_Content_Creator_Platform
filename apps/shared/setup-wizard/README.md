# Shared module setup backend

P-003 native Tauri plugin used by Stream Extend and Creator Extend. The catalog, manual guides,
requirement files, Python installer/checker, capture-device scanner and selected local Compose
runtime are embedded at build time.
The main local window has explicit permissions for catalog, module selection, capture selection,
bounded capture testing, fixed Python/OBS/Docker bootstrap, detected-app launch, OBS scene and
Docker service-plan preview, installation, report and check commands.
Remote web origins are not granted these permissions.

The plugin extracts immutable, versioned installer resources under the operating system's local
data directory, in `HybridCreatorPlatform/module-setup`. Both apps share `.venv-modules` there;
selections are saved separately by app identifier. Capture choices must match the latest local
scan before they can be saved. No credentials are stored in setup preferences.
The original CLI still defaults to environments in the repository; these are separate from the
desktop environments. The desktop installer sets `HCP_MODULE_DATA_ROOT` to its shared data directory.

Install commands accept only module IDs from the compiled catalog and pass an argument list to
an installed Python 3.11+ interpreter. Requirements are installed from their declared package
sources, without a shell. An OS file lock serializes installation across both apps and the CLI
when they use the same data directory. The panel checks Python before enabling dependency
installation. When it is missing, Windows can install the fixed `Python.Python.3.12` winget
package for the current user; macOS can install `python@3.12` when Homebrew is already present.
The package-manager command and arguments are fixed in the native plugin, run without a shell, and
write a local resumable job record. Manual installation remains the fallback when winget/Homebrew
is unavailable.

OBS onboarding follows the same boundary. Windows can run the fixed `OBSProject.OBSStudio` winget
package and macOS can run `brew install --cask obs`; the app accepts no package or executable
argument from the webview. It detects standard OBS locations, distinguishes missing and stopped
states, opens only the detected executable, and reports whether the default WebSocket port answers.
Stream Extend adds an authenticated protocol diagnostic that separates an unreachable server,
rejected password and incompatible version. Its explicit three-second recording test refuses to
run while OBS is already recording and returns only the finalized file name and size. The bundled
eight-scene asset is preview-only because it remains a source-free skeleton.

FFmpeg follows the same bounded package-job path. The app checks known system and package-manager
locations plus `PATH`, verifies the executable with `-version`, and shows only its path and first
version line. When it is missing, Windows can run the fixed `Gyan.FFmpeg` winget package and macOS
can run `brew install ffmpeg`; no webview-supplied executable, package or argument is accepted.
The system helper is optional for app launch, but enables the exact capture-device and short capture
test commands when a Python environment has no `imageio-ffmpeg` fallback.

Docker onboarding detects the Desktop executable, CLI, daemon and Compose separately. Windows
also reports WSL status without assuming every daemon failure is a WSL failure. The app can run
the fixed `Docker.DockerDesktop` winget package or Homebrew `docker-desktop` cask, open only the
detected Docker Desktop executable and start only services resolved from selected catalog modules
through a compiled allowlist. It invokes `docker compose` directly without a shell, using the
versioned Compose file and runtime trees bundled with the app. A private app-local environment is
generated once with random credentials and reused across both apps. If an existing source checkout
already owns the same Compose project, the action stops before generating different credentials.
After selected services are healthy, a second fixed job applies both migration trees, creates and
verifies the expected MinIO buckets and lifecycle, and imports the stable inactive n8n workflow
when automation is selected. It uses profile-gated helper containers and accepts no command, path,
image or service from the webview. Generated local credentials stay out of command arguments and
logs, are saved to the OS credential manager, and can be copied individually to the system
clipboard through allowlisted actions. Creator Extend reuses the generated MinIO pair after restart.

FFmpeg supplies exact DirectShow/AVFoundation names when available; Windows Plug and Play and
macOS `system_profiler` provide first-run fallback discovery. A saved capture choice is
configuration only, never a claim that an OBS recording passed. The setup panel can run an
explicit three-second capture test after a scan; its report separates device detection, signal,
recording and accepted evidence.

Dependency, capture and Docker job reports are written atomically. Capture discovery and the bounded test invoke
only bundled scripts and accept no executable or path from the frontend. A fresh scan invalidates
older test evidence; the test records only a short temporary sample and does not change device
formats. A closed app does not cancel its Python installation;
it may continue. On restart, a completed installer report is recognized, while unobserved running
work is labelled unknown. Rechecking dependencies is read-only; retrying an install cannot bypass
the OS lock. Job logs stay local. No arbitrary subprocess commands or file paths are exposed to UI.

Run from the full source repository:

```bash
cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml -p tauri-plugin-module-setup
python3 -m pytest tests/setup
```

App builds compile this crate and bundle its assets automatically. The separate shared
`setup-engine` turns app-native OBS/ComfyUI probes into versioned capability evidence and optional
OpenTechnology events; this installer owns selection, fixed prerequisite actions, guides, capture
discovery and bounded probes. Dependency checks prove
required package versions, pip consistency, application presence or device enumeration, not
complete module readiness. Physical cabling, HDCP and picture/audio judgement remain separate
work. Cloud deployments do
not use this local workstation installer.

The parameter-free `audio_setup_status` command reads only compiled platform recipes and standard
filesystem locations, then returns current routing-tool presence and bundled reference text. It
requires no Python, starts no process and writes no readiness flag. `configs/local/audio-setup.json`
owns the platform paths and guidance. All three audio references are included in the versioned
asset set; custom installations, live routing, levels and hotkeys require separate acceptance.
