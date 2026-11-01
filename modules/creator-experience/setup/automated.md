# creator-experience — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

Windows now has a guided bootstrap for prerequisites and capture discovery:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -InstallDesktopApps
```

It can install OBS Studio and FFmpeg through winget, install the chosen platform dependencies,
run readiness checks and write a capture-device report. Both desktop apps now detect, install and
open OBS from **Module setup → OBS Studio**, using fixed winget or existing-Homebrew commands.
The same panel previews the bundled eight-scene skeleton without applying it. Stream Extend tests
the configured WebSocket, identifies an unreachable server, rejected password or incompatible
version, and can run an explicit three-second OBS recording test. It refuses that test when OBS is
already recording and verifies that OBS finalized a non-empty local file.

The Stream Extend Dashboard also owns a managed live-session path: it starts OBS recording before
streaming, rolls back its recording if stream startup fails, stops the stream before finalizing the
recording, and registers OBS's returned non-empty path in the shared Creator Extend inbox. It never
stops or registers a recording that was active before the managed session. Fake OBS protocol tests
cover request ordering and ownership; picture/audio quality and a real provider stream remain manual.

Both apps also bundle the same local
capture scan and a bounded three-second capture test under **Module setup → Capture hardware**.
The test reports detection, signal, video/audio streams and recording separately. Device drivers,
OBS sources, encoder settings, physical cabling and picture/audio judgement remain guided manual
steps.

## What exists

```bash
make test-obs
```

Runs `scripts/setup/test_obs_websocket.py` — **validation, not setup**. It confirms OBS is
reachable once you have configured it by hand.

```bash
python3.12 scripts/setup/capture_devices.py
```

Enumerates capture names with DirectShow on Windows or AVFoundation on macOS and reports OBS and
FFmpeg presence. The desktop **Test selected capture (3s)** action then runs a bounded local probe;
it does not bypass HDCP or claim a complete stream acceptance.

A reference scene collection is committed at `modules/creator-experience/scenes/default.json`.
It is a source-free skeleton, so the app previews its version and scene names but does not import
or overwrite OBS configuration. Importing a real exported collection remains a manual OBS step.

## What the product claims

OBS prerequisite installation, launch, WebSocket diagnosis and bounded recording evidence now
exist. The larger one-click claim still includes scene import, encoder configuration, sources,
filters and device-specific acceptance. Those pieces remain unbuilt; use [manual.md](manual.md).

## What automation would take

A later setup action can apply encoder/video settings and import a real exported scene collection
after preview. The current automation deliberately stops at a read-only skeleton preview because
source creation must be verified against connected hardware.

## What the app is supposed to do

The free [OBS Plugin](https://streamextend.com/obs-plugin) is specified to auto-import scenes,
configure the encoder for your GPU, set up WebSocket, and apply the mic filter chain — with the
Stream Extend desktop app then providing a dashboard for scenes, stream health, and phone control.

That is the intended automated path for this module. It is **specified, not shipped** — see the
status note above. When it lands, this section becomes the automated path and
[manual.md](manual.md) becomes the fallback.
