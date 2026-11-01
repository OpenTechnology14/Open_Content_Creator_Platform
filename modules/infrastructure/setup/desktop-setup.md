# Desktop module setup and readiness

**Labels:** `Content` `Stream` · P-003

## Open an app first

**Private P-072 preview, 2026-10-12:** [Extend Preview](../../../apps/extend/README.md) adds one
local Home/Stream/Create/Library/Settings shell beside the existing apps. Setup/profile/inbox
and read-only readiness build as a private Mac debug app/DMG. Credentials/settings are not
migrated; broadcasts/renders/publishing stay in the existing apps. U-01/U-02/U-07 native opening,
restart, vault, keyboard/narrow-window and denied-origin acceptance are open. This is not a
public installer/support claim or permission to replace the existing apps.

The first milestone is an open **Stream Extend** or **Creator Extend / ContentExtend** window.
OBS, Docker/WSL, Python, ComfyUI, model downloads and cloud/account setup are not prerequisites
for the packaged setup view. Missing services should block only the controls that require them.
Python is needed later for dependency installation/checks and capture scanning.

**Current distribution limit:** this is a private pre-release repository. No published releases
were listed when checked on 2026-09-12. Native installers are built separately from the module
bootstrap; clean Windows install/open acceptance remains distinct from a CI build. Use the
private installer path below when artifacts are available. A source ZIP or the streaming rehearsal
ZIP is not an Extend app installer.

### Private installers

The Desktop installers workflow (private development evidence; not distributed)
builds release-profile Windows x64 NSIS packages for both products and retains artifacts for
30 days. Open a successful run while signed into a GitHub account with repository access and
download `stream-extend-windows-x64` or `creator-extend-windows-x64`. Extract the artifact ZIP,
then run the included `*-setup.exe`. These are unsigned private pre-release builds, so Windows
may show an unknown-publisher/SmartScreen prompt; public signing remains P-001 work.

The installer installs for the current user and adds a shortcut under **Start → Hybrid Creator
Platform**. Launch from the finish page or shortcut to reach Module setup. WebView2 is reused
when present; the embedded Microsoft bootstrapper downloads it when missing, which requires
internet. No separate Node, Rust, Python, OBS or Docker installation is required to open the app.
This runtime handling follows [Tauri's Windows installer support](https://v2.tauri.app/distribute/windows-installer/).

Each artifact includes `SHA256SUMS.txt`, `build-info.json` (version, source commit, target and
signing status), and `INSTALL.txt`. On Windows, compare `Get-FileHash -Algorithm SHA256` for the
setup file against the supplied checksum. The separate `*-windows-smoke` artifact records the
CI install result, native window title, timing, and available screenshot/accessibility evidence.
Hosted runners already have developer tools and WebView2; that smoke is not a clean-workstation
or physical capture test.

Apple Silicon Mac packages are built with the command below and collected under
`output/installers/<app>-macos-arm64/`, also with checksums and build metadata. Open the `.dmg`,
drag the app into Applications, then open it. Current builds have an ad-hoc executable signature
and are not notarized; they are private acceptance artifacts. Intel Mac installers are not part
of this build slice.

### Source-checkout fallback (developer tools required)

Use the full repository so the shared crates and bundled guides/workflows are available.
Install Node.js 22 (the CI version), npm and stable Rust. On Windows, install Visual Studio
Build Tools with **Desktop development with C++**, a Windows SDK and the WebView2 runtime;
use the Rust MSVC toolchain. On macOS, install Xcode Command Line Tools.
See the [official Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).
These are build requirements; users of packaged apps should not need Node/Rust/build tools.

In PowerShell at the repository root, build an installable debug bundle:

```powershell
cd apps/stream-extend
npm ci
npm run tauri build -- --debug
```

Run each command only after the previous succeeds. Open the generated installer under
`apps/stream-extend/src-tauri/target/debug/bundle/`. For Creator Extend, start at the repository
root again and use `cd apps/creator-extend`; its output is under that app's corresponding
`src-tauri/target/debug/bundle/`. On macOS the same build commands produce `.app`/`.dmg` bundles.
Build failures belong to this developer path, not OBS or Docker setup. These commands match the
repository scripts and recorded Mac build path; clean Windows execution remains pending.

For a quicker development launch after `npm ci`, `npm run tauri dev` opens the native app
without packaging; plain `npm run dev` only serves the web frontend. Stream Extend uses development port 5173 and Creator Extend uses 5174. Installed bundles
do not need a development server.

## Continue inside the app

Both Creator Extend and Stream Extend open a **Module setup** view. The **Dashboard** button
remains available even if another module is missing or not ready.

1. Choose individual modules or add a starter profile. Required dependencies are shown and
   cannot be removed while another selected module needs them. Selections save automatically.
2. Read each module's remaining steps or open its bundled setup guide.
3. With Python 3.12 installed, click **Install selected Python dependencies**. Only the selected
   catalog requirements are installed. This is not an OBS/plugin/driver/model installer.
4. Watch installation progress. A failed module is recorded while the installer attempts other
   selected modules. Logs stay on the local computer.
5. Click **Check readiness** after installation. Review dependency evidence and the app's
   service connection check, then complete the remaining module-specific manual acceptance.
6. Under **Capture hardware**, scan for local camera/capture-card video and audio inputs. Select
   the devices OBS should use and save them. The scanner uses DirectShow on Windows and
   AVFoundation on macOS; Windows also shows present Plug and Play driver inventory.
7. Under **OBS Studio**, install or open the detected desktop app. In Stream Extend, test the
   configured WebSocket and run the explicit three-second recording test after choosing a safe
   scene. The test will not interrupt an existing recording. Review picture and audio yourself.
8. Under **Local Docker services**, review the services resolved from the current module selection.
   Install or open Docker Desktop when needed, recheck the separate Desktop/daemon/Compose/WSL
   states, then start the selected services. The app starts only its compiled service allowlist and
   retains the job log and final service states.

On Windows, `scripts/setup/windows.ps1` is an optional **module prerequisite** bootstrap after
app launch. It can install Python 3.12 and, with `-InstallDesktopApps`, OBS Studio and FFmpeg
through winget. That flag does **not** install either Extend app. It runs the selective module
installer and capture scan, using repository-local environments by default. It does not set up
Docker. Prefer the app's selected-dependency installer when Python is already available.

If OBS installation fails, continue using the app and defer broadcast/capture acceptance. If
Docker is unavailable, defer only container-backed features. Do not run `make up` just to open
an app. Source users who need Python can use the bootstrap with a small explicit selection,
without `-InstallDesktopApps`; see [module selection](module-selection.md).

The active extension is [P-063](../../../docs/PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup):
the installer slice is built and Module setup now detects and can install Python 3.12, OBS and
Docker Desktop through winget on Windows or an existing Homebrew installation on macOS. It can
open OBS and Docker Desktop, classify the Stream Extend WebSocket connection, run a bounded
recording check, report Docker daemon/Compose/WSL failure states and start the selected bundled
local services. FFmpeg installation, migrations, bucket initialization, workflow import and local
credential handoff remain later recipes. Routine repeatable
steps should move into these recipes so users do not need an AI session to execute and monitor
standard setup commands.
The follow-up inventory is in the [setup automation audit](../../../docs/SETUP-AUTOMATION-AUDIT.md).
In particular, **Scan capture hardware** enumerates names and **Test selected capture (3s)** runs
a bounded local probe. Physical cabling, HDCP and picture/audio judgement remain a separate
acceptance milestone.

## Connection settings

Open **Connections** in either desktop app before running a service check:

- Stream Extend saves the OBS host and WebSocket port plus local ComfyUI, Grafana and API URLs.
  Entering a new OBS password replaces the saved credential; leaving it blank preserves the
  existing credential. **Clear saved OBS password** removes it explicitly.
- Creator Extend saves ComfyUI, MinIO and API URLs plus optional Blender and Krita executable
  paths. MinIO access and secret keys can be replaced or cleared independently.

Ordinary settings are written atomically under the OS local-data directory with private file
permissions on macOS/Linux. OBS and MinIO credentials use macOS Keychain, Windows Credential
Manager or the operating system credential store. `get_config` returns only boolean
`*_set` indicators; secret values are never returned to the webview or written to JSON/logs.
**Save and test** persists the values before running the existing OBS or ComfyUI connection
probe. A failed probe does not undo valid saved settings.

## What the checks mean

| Result | What was observed | What it does not prove |
|---|---|---|
| Python dependencies: Check passed | Required package versions match; `pip check` passes | A module's inference, camera, network or runtime integration works |
| Application: Check passed | An executable or app exists at a known location | Its plugin, device or audio configuration is correct |
| Application: Not found | Standard locations/PATH did not contain it | The application is definitely uninstalled |
| OBS control connection: Check passed | The app's existing OBS client requested the scene list | Capture, audio, encoding or streaming passed acceptance |
| ComfyUI connection: Check passed | Status and queue endpoints responded | Models/custom nodes are compatible or a workflow completed |
| Capture device: discovered | FFmpeg enumerated the local DirectShow/AVFoundation name | The device can sustain resolution/FPS, carries audio, or records correctly in OBS |

No module becomes fully ready just because dependencies install or an application is found.
Checks carry a timestamp and are not reused as fresh evidence after reopening the panel.
Service checks use the app's persisted connection configuration. Relay access tokens now use the
OS credential manager and the desktop remote-control path requires local approval. Full feature
readiness gating, hosted-relay acceptance and end-to-end service acceptance remain separate work.

## Storage and recovery

The installer and guides are packaged with each app, so this setup panel does not depend on
launching from a source repository. Guides may still reference module runtimes and files that
require the full source checkout; installing requirements does not bundle all those runtimes.

Both apps share environments under the OS local-data directory:

- macOS: `~/Library/Application Support/HybridCreatorPlatform/module-setup/`
- Windows: `%LOCALAPPDATA%/HybridCreatorPlatform/module-setup/`

Choices are saved separately for each app. `.venv-modules/` holds environments, `runtime/` holds
versioned installer resources, `docker/local.env` holds private generated local service credentials,
and `jobs/` contains progress reports and logs. The CLI defaults
to repository-local environments; it only shares desktop environments when explicitly given
the same `HCP_MODULE_DATA_ROOT`. The earlier streaming rehearsal environment is also separate.

An OS file lock permits only one install into a shared data directory at a time. A second
install attempt fails safely and can be retried after the first finishes. The same lock covers
package bootstrap, Python dependencies and Docker service startup across both apps. Closing the app
does not cancel a package installer or Docker Compose child process; it may continue. On reopening,
a finished report is recognized.
If completion was not observed, the UI says the previous installation needs review rather than
claiming success. Check readiness and logs before retrying. No automatic uninstall, deletion of
environments, cloud provisioning or game/account setup occurs.

Python and Docker discovery check standard platform locations before PATH. If Docker reports a
generic daemon failure, the app preserves that diagnostic instead of claiming WSL is the cause.
On an existing `hybrid-creator-platform` Compose project, the first app-owned startup refuses to
replace unknown credentials; use that project's original workspace. The app-owned and source
checkout stacks share fixed local ports and must not run concurrently. Clean Windows
missing-prerequisite, WSL/reboot recovery and real service startup still need native acceptance.

## Verification

Run the [CLI selection guide](module-selection.md) for repository-local setup. Development checks:

```bash
python3 -m pytest tests/setup
cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml -p tauri-plugin-module-setup
npm --prefix apps/creator-extend run check
npm --prefix apps/stream-extend run check
make test
```

Native acceptance: open a built app without the repository as its working directory, select
Audio Production and Soundboard, check before installation, install the selected dependencies,
check again, and reopen the app to confirm choices/job history persist. Check the second app
finds the shared audio environment while preserving its own independent selection.
