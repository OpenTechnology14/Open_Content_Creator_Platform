# Choose modules à la carte

**Labels:** `Content` `Stream` · P-003 local setup slice

Open Stream Extend or Creator Extend first using the [desktop launch guide](desktop-setup.md).
This CLI path is optional module setup; it does not install or launch either Extend app.

The repository has twenty-one modules with different installation requirements. Neither the
Windows bootstrap nor `make up` installs all twenty-one. The bootstrap installs an explicit preset
or module list. `make up` starts the configured core containers and requires Docker.
Desktop applications, plugins, drivers, models, accounts and OBS scenes remain separate steps.
Full Mac/Windows compatibility is not certified. The module catalog exposes these limits.

## Choose, preview, install

### Guided Windows bootstrap

Open PowerShell in the repository. This installs Python 3.12 when it is missing, installs the
streaming preset into isolated environments, checks the selection, and writes a capture-device
report. `-InstallDesktopApps` also installs OBS Studio and FFmpeg through winget, not the Extend
apps. Omit that flag to defer OBS setup; Docker is not installed or required by this bootstrap:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -InstallDesktopApps
```

Use `-Preset creator` for the creator preset, or choose exact modules:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -Preset custom -Modules soundboard,audio-production
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -PlanOnly
```

`-PlanOnly` requires Python 3.12 already installed. A winget failure stops this script; it does
not prevent opening an existing Extend app or working on unrelated modules there.

The script does not install game clients, sign in to accounts, download model weights, choose a
vendor driver, or claim that a detected capture device can record. Review
`output/module-setup/windows-capture-report.json`, then finish the OBS recording test.

### Lower-level Python commands

With Python 3.12 already installed:

```powershell
py -3.12 scripts/setup/modules.py list
py -3.12 scripts/setup/modules.py plan --modules ai-agents audio-production content-creation
py -3.12 scripts/setup/modules.py install --modules ai-agents audio-production content-creation
```

On Mac, use `python3.12` instead of `py -3.12`. No shell activation, Make or Docker is required
for this installer. The `plan` command has no installation side effects. There is no default
selection; spelling mistakes fail instead of selecting a different module.

Starter profiles are optional and additive:

| Profile | Selection |
|---|---|
| `stream-test` | AI Agents host, saved-reply audio, director/planner, Shorts dependencies |
| `broadcast` | OBS guide, DJ Soundbox guide, audio dependencies, graphics and backend/storage guides |
| `creator` | Shorts dependencies, image-editing guide, asset-pipeline and model-registry dependencies |

```powershell
py -3.12 scripts/setup/modules.py plan --profile broadcast --modules ai-agents
```

Dependencies added to your selection are explicitly marked in the plan. Dependencies refer to
module setup relationships; they do not start services. For instance, selecting graphics also
includes backend/storage setup. Every module's remaining work and both setup-guide paths are
included, alongside informational Compose service names.

## What installation does

The installer reads the repository-owned catalog in `configs/local/module-install-catalog.json`
and installs only the listed Python requirement files. Environments live under
`.venv-modules/<module-id>/`; rerunning setup reuses them. Installations can download sizable
Python dependencies, especially sports CV. No model weights, desktop apps or cloud resources
are installed. Manual-only choices generate a report without invoking pip.

Each module uses its own interpreter:

```powershell
.\.venv-modules\audio-production\Scripts\python.exe modules/audio-production/tts/render_reply.py --help
```

On Mac that interpreter is `.venv-modules/audio-production/bin/python`. Follow the selected
module's guide for its entrypoint and import paths. Never copy virtual environments between
Mac and Windows; rerun setup on each device. The shared Stream Autopilot rehearsal environment
remains separate; use its existing installer for the combined smoke test.

Reports/logs are written to a new `output/module-setup/<timestamp>/` directory. Each module
reports dependency installation separately from capability readiness. `action_required` means
the dependency attempt finished but manual setup and acceptance still remain. `failed` means
at least one dependency installation failed; other selected modules are still attempted.
An exit code of zero does not certify OBS, GPU/model support, a service or a game.

Read `report.json` and the relevant module log on failure, correct prerequisites and rerun the
same selection. The installer does not delete environments, uninstall modules, change account
credentials or start containers. Catalogued modules can be documentation/scaffolding only.

## Acceptance

Local Mac evidence: real selective Audio Production dependency installation; Soundboard stayed
manual; the resulting audio interpreter launched its CLI. Offline tests cover catalog coverage,
explicit selection, dependency resolution/cycles, platform interpreter paths, failure isolation
and manual-only behavior. Native Windows execution remains pending. Both apps now provide a
[desktop setup panel](desktop-setup.md) backed by this installer. `doctor --modules <ids>`
checks installed requirement versions, dependency consistency and configured application paths.
These checks do not certify full capabilities; service workflows and hardware acceptance remain separate.
The desktop panel uses shared OS-local data storage; the CLI defaults to this checkout.
`HCP_MODULE_DATA_ROOT` can explicitly select another environment/report root.

Capture hardware can also be scanned separately on Windows or macOS:

```powershell
py -3.12 scripts/setup/capture_devices.py --output output/module-setup/capture-report.json
```

The scanner uses DirectShow on Windows and AVFoundation on macOS through FFmpeg. Windows also
records present Camera, Image and Media devices reported by Plug and Play. The desktop setup
panel bundles the same scan and lets the user save a discovered video device plus optional game
audio device. This is local configuration evidence; it does not replace a real OBS recording.
