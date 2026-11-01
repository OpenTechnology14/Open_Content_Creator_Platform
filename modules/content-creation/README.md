# content-creation

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (local Shorts CLI; desktop tools manual)

Content Creation layer. Blender, DaVinci Resolve, longform + shorts pipelines.

For AI-powered image and video editing (Krita + ComfyUI inpainting),
see `modules/image-editing/` ([`image-editing`](../image-editing/setup/manual.md)).

**The Blender addon this module's docs describe as unwritten actually exists** at
[`plugins/blender-addon/`](../../plugins/blender-addon/) — template gallery, MinIO upload, and
ComfyUI triggers are real and working; only batch-render's actual render/upload loop is a stub.
See `setup/automated.md` for the corrected breakdown (found 2026-09-01, `P-036`).

The [stream Shorts pipeline](stream_shorts/README.md) now selects interaction highlights, accepts
manual timeline sections and renders real vertical MP4s locally. A live session started from Stream
Extend now records through OBS and registers the finalized local file in Creator Extend's shared
**Recordings** inbox with its Stream and Content profile routing. Generic OBS sessions, synchronized
chat/job ingress, automatic editing, and automatic publishing are not connected. Module status
remains scaffolded pending broader acceptance.

Creator Extend has [per-run image, prompt and seed controls](setup/workflow-inputs.md) for its bundled workflows. Required ComfyUI models/nodes remain separate installs.
