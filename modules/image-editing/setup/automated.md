# image-editing — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

**There is no automated setup script for this module.** Krita is a desktop application and the
plugin install is a manual file-copy plus a restart.

## What exists

Three real Python scripts (~955 lines — the largest Python surface of any module here):

| Script | Purpose |
|---|---|
| `krita/scripts/apply_style.py` | ~427 lines |
| `krita/scripts/batch_upscale.py` | ~273 lines |
| `krita/scripts/export_to_minio.py` | ~255 lines |

Run directly with `python`. No launcher, service, or Make target.

Two committed workflows: `workflows/inpaint-fill-v1.json` and `workflows/video-frame-edit-v1.json`.

## Depends on

- **ComfyUI** running — see [realtime-ai](../../realtime-ai/setup/automated.md). This module has
  no model runtime of its own; the Krita plugin drives your existing ComfyUI instance.
- **MinIO** for `export_to_minio.py` — see
  [storage-data](../../storage-data/setup/automated.md), which *is* automated (`make up`).

## Known documentation gap

The realtime-ai workflows README indexes `auto-select-sam-v1`, `background-replace-v1`,
`inpaint-remove-v1`, `outpaint-expand-v1`, and `upscale-4x-v1`. **None exist anywhere in the repo.**
Only `inpaint-fill-v1` and `video-frame-edit-v1` are real, and they live here rather than where
that index points. Check the directory before assuming a workflow exists.

## What automation would take

A script could place the plugin into `pykrita/` and write the AI Diffusion server URL into Krita's
config. Enabling the plugin is a GUI step; model downloads are license-gated and must not be
committed.

## Tap-to-edit from a phone (the app path)

Creator Extend is specified to bring this module's editing to phone and tablet: tap to select an
area, type what you want, and the **desktop GPU** does the work.

- Scrub video → select a region → edit that frame
- Generative fill, object removal, background swap
- Results sync to MinIO and appear on other devices
- Push notification when an edit finishes

Everything runs on your hardware; the app is a remote control. That is what keeps this inside
`CLAUDE.md` §2's local-first rule — no frame is processed in the cloud.

**Specified, not shipped** — `CLAUDE.md` §11 has this module at `scaffolded`. The API spec is at
[`../mobile/README.md`](../mobile/README.md).

