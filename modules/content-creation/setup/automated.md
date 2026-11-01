# content-creation — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

**Partial automation:** the [stream Shorts CLI](../stream_shorts/README.md) installs through its
requirements file and selects/renders one completed local recording. Stream Extend's managed live
control now starts a local OBS recording before the stream and registers OBS's finalized path in a
locked, atomic cross-app inbox; Creator Extend lists, imports, routes, reveals, and archives that
metadata without copying or uploading video. The CLI also generates a local video review page for
manual section selection. Optional edit plans render supplied captions, brand layout, event-linked
punch-ins and loudness-normalized audio on CPU. Follow that README for executable commands. There is
no generic OBS recording-finished listener, synchronized chat job, transcription, subject tracker,
platform upload or desktop DCC installer.

Creator Extend packages fixed Krita helper and posture-analysis sources for its local package/import
checks. The Creative Tools panel runs each bundled script with `--help` and reports missing Python
imports without touching user files; this is an app-owned readiness check, not a DCC installer or a
completed render/edit workflow. It also offers a dry-run Blender batch-render plan for an
operator-selected `.blend` file and output directory, followed by an explicit confirmation before
running the render; process completion and visual output review remain separate acceptance steps.

The real Blender addon lives at `plugins/blender-addon/`; its earlier "unwritten" description
was corrected in P-036. The breakdown below concerns that separate addon. The module remains
`scaffolded`: local clip rendering does not complete all Content Creation acceptance requirements.

## What the product claims

The roadmap's Content Creation layer lists Blender, DaVinci Resolve, motion graphics, YouTube
workflows, shorts/reels pipelines, and film rendering. A free Blender addon (template gallery,
MinIO upload, ComfyUI triggers) is advertised in `README.md`.

## What's actually in `plugins/blender-addon/` (verified 2026-09-01)

Four Python files, 440 lines, a real `bl_info` registration block, four panels, five operators:

| Operator | Status |
|---|---|
| `CE_OT_OpenTemplateGallery` | **Working** — lists `.blend` files under the configured template directory |
| `CE_OT_UploadToMinio` | **Working** — `boto3`-based upload of the current render to MinIO/S3 |
| `CE_OT_SendToComfyUI` | **Working** — pings ComfyUI, uploads the current frame for a named workflow |
| `CE_OT_OpenCreatorExtend` | **Working** — opens the `creatorextend://` URL scheme, falls back to the website |
| `CE_OT_BatchRender` | **Stub** — reports a message; its own comment says `# TODO: Iterate scenes, render each, upload` |

`CE_OT_UploadToMinio` keeps its own `boto3` client rather than importing
[`asset-pipeline`](../../asset-pipeline/README.md) — Blender's embedded Python interpreter can't
import a sibling repo package without vendoring infrastructure this repo doesn't have, the same
constraint `asset-pipeline`'s own README documents as an intentional exception, not an oversight.

## The nearest working thing

Asset storage is real and running — see
[storage-data](../../storage-data/setup/automated.md). Renders can be pushed to the
`project-assets` and `recordings` buckets by hand today, or via the addon's working upload
operator once it's installed.

## What automation would still take

Only `CE_OT_BatchRender`'s actual scene-iteration and render loop — everything else in the "What
the Blender addon is supposed to do" list below is already built. The full job lifecycle is now
queued as pending proposal [P-061](../../../docs/proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md).

## What the Blender addon is supposed to do

The free [Blender Addon](https://creatorextend.com/blender-addon) is specified to add a template
gallery, one-click MinIO upload for renders, and ComfyUI workflow triggers from inside Blender —
no terminal. Creator Extend then adds workflow management, output browsing, and remote render
triggering with push notifications on completion.

Four of those five pieces are shipped in `plugins/blender-addon/` today. Batch rendering is the
one still to write. `docs/AUDIT.md`'s "Desktop app completeness" finding is about the separate
Tauri apps (`apps/stream-extend`, `apps/creator-extend`), not this addon — don't conflate the two
when reading that row.

Install instructions: [manual.md](manual.md).
