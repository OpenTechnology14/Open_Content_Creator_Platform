# content-creation — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

> The [local Shorts pipeline](../stream_shorts/README.md) now provides selection, review and
> rendering code inside this module. Blender/DaVinci still require manual desktop setup.
> The Blender addon lives outside this folder — see below.

## Blender

Install from https://www.blender.org/. Project files belong in
`modules/content-creation/blender/projects/` — but **never commit anything over 5 MB**
(`CLAUDE.md` §10). Push renders and heavy assets to MinIO instead.

### The Creator Extend Blender addon

Real, working code at [`plugins/blender-addon/`](../../../plugins/blender-addon/) — see
[automated.md](automated.md) for exactly which of its five operators are implemented versus a
stub. To install:

1. Zip `plugins/blender-addon/` (or symlink it into Blender's addons directory).
2. In Blender: **Edit → Preferences → Add-ons → Install...**, pick the zip.
3. Enable **Creator Extend** in the addon list.
4. Open the addon's preferences and set `MinIO Endpoint`/`Access Key`/`Secret Key`/`Bucket` — same
   values as your `.env`'s `MINIO_*` vars (the addon reads them from Blender's own preferences UI,
   not from the environment, since Blender's embedded interpreter doesn't inherit shell env the
   way a terminal-launched script does).
5. The panel appears under **View3D → Sidebar → Creator Extend**.

### Why Blender first

Blender is the reliable half of the content pipeline: deterministic, scriptable, and it produces
the same frame every time. Establish it before adding generative steps, so when a ComfyUI result
is wrong you know the problem is the generative stage.

## DaVinci Resolve

Install from Blackmagic. Free tier covers the whole edit path for most creators.

## Moving assets

The addon's **Export** panel (`CE_OT_UploadToMinio`) does this from inside Blender once installed.
Without it, use MinIO directly:

- Renders → `project-assets`
- Recordings → `recordings`
- AI outputs → `comfyui-outputs`

`modules/realtime-ai/comfyui/scripts/output_to_minio.py` is a working reference for uploading
from a watched directory — the same pattern applies to a Blender output folder.

## Where the generative half lives

ComfyUI setup is in [realtime-ai](../../realtime-ai/setup/manual.md), and image and video editing
is in [image-editing](../../image-editing/setup/manual.md). This module is the traditional DCC
half; those two are the AI half.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] Blender renders to a local folder
- [ ] The addon's **Upload to MinIO** button lands that render in `project-assets` (or `renders`,
      whichever bucket the addon preferences point at)
- [ ] The addon's **Send to ComfyUI** button reaches a running ComfyUI and reports a filename back
- [ ] Resolve can open and edit the render
- [ ] Batch Render reports its placeholder message — it does not actually iterate scenes yet
      (`CE_OT_BatchRender` is a stub; see `automated.md`)

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.
## Troubleshooting

- **Addon panel doesn't appear** — check it's enabled under Preferences → Add-ons, and look for
  `[Creator Extend] Addon registered` in Blender's system console.
- **"boto3 not installed" on Upload to MinIO** — Blender's bundled Python needs `boto3` installed
  into it specifically, not your system Python. Blender's own Python console:
  `import sys, subprocess; subprocess.run([sys.executable, "-m", "pip", "install", "boto3"])`.
- **Batch Render does nothing but report a message** — that's correct today; it's a documented
  stub (`CE_OT_BatchRender`), not a bug.
- If something else here does not work, it is because it was never built. Check
  `docs/architecture/roadmap.md` for intended scope and open a proposal per
  `docs/PROPOSAL_CREATION_SOP.md` before implementing.

## Stream Shorts verification (P-056)

Start a managed session with **Go Live + Record** in Stream Extend. Stop it with **Stop + Send to
Creator**, then open Creator Extend → **Recordings**. Confirm the non-empty OBS file appears once,
retains the source Stream profile, targets the active Content profile, and can be revealed in its
original folder. Change the Content profile and workflow status, restart Creator Extend, and confirm
both persist. Also use **Add existing recording** for one video created outside the managed path.

Then follow [the local Shorts workflow](../stream_shorts/README.md). With that recording, verify
that manual ranges and supplied edit cues survive export, clips play with synchronized normalized
audio, captions are readable, punch-ins land on their intended subjects, and overlays/HUD remain
legible at phone size. Check the manifest reports complete and records the applied cue counts.
Synthetic-video rendering is evidence of the renderer; a real stream with chat timestamps is still
required for live acceptance.

Creator Extend has [per-run image, prompt and seed controls](workflow-inputs.md) for its bundled
workflows. Its in-app preflight reports endpoint, node/model inventory and current VRAM before
queueing, but models/nodes remain separate installs and a real output still needs review.
