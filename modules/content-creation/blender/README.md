# blender

Blender project files and render scripts. See [`realtime-ai`](../../realtime-ai/setup/manual.md). Avoid committing large .blend files.

## Local still-job lifecycle — P-061

Creator Extend → tools → Plan Blender batch render inspects a saved project. Select 1–16
scenes, then start a local PNG-still job. It renders each selected scene's current saved
frame at its saved resolution (up to 4096 pixels per dimension). No animation or upload is
implied. Outputs use a new `blender-<job-id>` attempt folder; existing work is never replaced.

The app polls atomic per-scene manifests, bounds retained process logs, cancels only its
owned process and verifies successful artifact hashes. Retry creates a new attempt for
unfinished scenes and rejects a changed project. After restart, unresolved running records
are reported interrupted; no persisted PID is claimed or killed. Confirm the old worker has
stopped before retrying an interrupted job. The bundled code always launches with factory
startup and project auto-execution disabled.

The addon uses explicit scene checkboxes and a modal owned-process job. Escape cancels;
previous outputs remain. Creator's exported addon includes the fixed worker. A repository
checkout can resolve the same worker locally. The old “render and upload started” stub is
removed; the existing manual upload operation remains separate.

From a checkout, with Blender installed and an existing output folder:

```bash
blender --factory-startup --disable-autoexec --background project.blend \
  --python modules/content-creation/blender/scripts/batch_render.py -- \
  --output /path/to/output --scene=Scene --dry-run
```

Remove `--dry-run` to render the explicitly named scenes. The project is never saved by the
worker; output filepath/format settings are restored in its loaded state. The manifest retains
project checksum, selected scene names, results, artifact sizes/hashes/dimensions and elapsed time.
Failed scenes do not discard successful results. Relative external project assets are loaded from
the original saved project location; their separate content is not archived by this still-job mode.

Local and DigitalOcean differ only in operator-supplied tool/storage configuration; this runner
is local workstation code. No cloud service is added, and background rendering can contend with
live production, so the app asks for an off-air batch confirmation. Remote job control, animated
exports and optional batch asset-pipeline upload are not certified by this first mode.

## Verification

Ten offline worker cases and five native process contracts cover selection limits, containment,
settings restoration, partial failure, cancellation, restart ownership and changed artifacts.
An opt-in native test runs the real Blender executable against an owned fixture. On this Mac,
Blender 5.2.1 LTS rendered two real 64×64 PNGs and retained a successful scene when a no-camera
scene failed; the owned native launcher also completed and verified the two artifacts.
Native UI acceptance is currently blocked by the locked Mac. Physical Windows, production
projects/assets, animation and upload need their separately recorded acceptance.
