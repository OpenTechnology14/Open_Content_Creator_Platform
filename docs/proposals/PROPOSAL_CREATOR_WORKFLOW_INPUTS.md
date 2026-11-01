# Proposal: Creator workflow inputs

**Queue row:** P-057
**Agent model / effort:** `gpt-6.1-sol` / `high` — Native upload validation, bounded preview and ComfyUI contracts
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Code complete — native Windows acceptance open; [queue](../PROPOSALS.md) is authoritative
**Owner:** Owner + agent
**Date:** 2026-09-08
**Roadmap layers:** Content Creation / Realtime AI / Image Editing, existing Creator Extend app
**Evidence level:** Code inspection; verification recorded below when complete

## User outcome and verified gap

Creator Extend already lists committed workflows, queues their real JSON and polls completion.
Its Run button previously sent the template without collecting any inputs. Several LoadImage
nodes contain PLACEHOLDER_IMAGE or PLACEHOLDER_MASK, so the UI could not provide a creator's image.
P-054 built queueing; this is new input collection, not a claim that queueing was still stubbed.

## Scope and user path

Configure a workflow, upload a PNG/JPEG/WebP to the configured ComfyUI server, edit exposed text
and seeds, then run a validated copy. Invalid inputs or failed uploads keep the editor open.
Changing a workflow discards unsaved edits; uploading does not queue a job. Closing the editor
leaves any uploaded input file on the ComfyUI server. Queueing failure permits correction/retry.
Completed jobs expose bounded image/video previews and a 20-entry history for the current app
session. This does not implement cancellation of running ComfyUI jobs, durable history or
custom-node parameter editors.

## Architecture and contracts

Existing Tauri commands and the app's configured ComfyUI URL are retained. A dedicated Rust
helper exposes supported literal fields and validates edits against the original graph loaded
from approved workflow directories. Linked inputs, model choices and class types cannot be
changed by this editor. Seeds are integers up to JavaScript's safe integer maximum; prompts
are bounded to 16 KiB. Image bytes are bounded to 10 MiB and sent as multipart image/type/overwrite
fields to `/upload/image`; overwrite is false and the returned input reference is validated.
The installed ComfyUI `app/server.py` implementation was read to verify that protocol.

The UI explains the upload destination before selection. Inputs remain on that server under
its ordinary retention policy. No platform storage or cloud service is provisioned. The
existing backend controls queue outcomes. Errors are rendered as text, never HTML. On completion
the app reads only history references returned by ComfyUI, validates their node, filename,
subfolder and folder type, then streams at most 8 MiB from `/view`. PNG, JPEG, WebP, GIF, MP4 and
WebM are accepted by file signature; at most four previews are retained per run and twenty runs
per app session.

## Implementation and verification plan

- Add typed workflow fields, validated per-run edits and bounded image upload in the Creator app.
- Add a Configure panel with labels, previewable values, per-field upload status and Run control.
- Test graph preservation, invalid/duplicate edits, malformed upload responses, bounded requests
  and upload-then-queue HTTP contracts; run Rust tests, Svelte checks/build and `make test`.
- Record actual local evidence separately from native Windows and live GPU acceptance.

## Remaining platform build priorities

| Area | Still needs building | Separate acceptance work |
|---|---|---|
| Setup | Desktop module picker, per-capability readiness probes, durable configuration/secrets | Native Windows installs and app bundles |
| Creator workflows | Video source inputs and the separate video flow-warp design recorded under P-043 | Supported workflows, masks and GPU/tool versions |
| Production jobs | [P-061](PROPOSAL_BLENDER_PRODUCTION_JOBS.md): Blender render-job lifecycle, cancellation/retry and output handoff | Actual Blender/Krita sessions |
| Remote control | Instantiate/wire app relay managers and connection lifecycle; durable pairing/readiness | Authenticated remote device round trips |
| Automated broadcasts | Live chat ingress, continuous speech/avatar integration, scheduler execution, recording-to-Shorts handoff and game adapters | OBS, Soundbox, model, game and operator takeover sessions |
| Advanced generators | [P-059](PROPOSAL_NATURE_GENERATION_TIERS.md) and [P-060](PROPOSAL_CITYSCAPE_GENERATION_TIERS.md): learned tiers beyond deterministic Tier 0 | Authorized corpora and GPU evaluation |

Core OBS commands, ComfyUI queueing, storage, asset pipeline and model registry already have
implementation; they should not be described as absent. Some module status tables are
conservative and some older audit descriptions are stale. No module is promoted by this work.

## Rollout and limits

Changes are local and reversible; template files are not modified and uploads are not overwritten.
Models/plugins remain independently installed. Live UI inspection exposed empty workflow lists caused by repo-relative discovery.
This slice now packages curated JSON at build time and resolves exact bundled IDs at runtime.
The working-directory failure has a regression test; changing curated workflows requires a rebuild. Full Windows, live creative
application and automated broadcast acceptance remain open. No release, push or deployment is
part of this change.


## Verification recorded — 2026-09-08

- Rust offline suite: 26 passed; the explicit live test is ignored by default. Eight new
  input/upload/resource/destination tests passed. Log: `/tmp/hcp-inputs-rust-complete.log`.
- Packaging regression: restored the original `comfyui.rs`, ran the new bundled-workflow
  test from Cargo's crate directory and observed exit 101 (missing upscale workflow); restored
  the fix and verified a pass. Log: `/tmp/hcp-inputs-packaging-regression.log`.
- Svelte checks: zero errors/warnings. Real frontend build and Tauri debug build produced
  `.app` and `.dmg`. Log: `/tmp/hcp-inputs-bundle-complete.log`.
- Native Mac UI: normal bundled launch lists ten executable curated workflows; Configure
  exposes image, positive/negative prompt and seed inputs. A negative seed was visibly rejected.
  Selecting the synthetic fixture through the native file chooser uploaded it and filled the
  returned `creator-input.png` reference. Final build displays the credential-free upload origin.
- Live local ComfyUI (CPU): explicit ignored Rust acceptance passed in 1.07 seconds, including
  upload, validated preparation, queued synthetic LoadImage → SaveImage, terminal success and
  retrieved 32×32 PNG. No model weights were downloaded or GPU inference claimed. Log:
  `/tmp/hcp-inputs-live.log`.
- Full `make test` exited 0 (`/tmp/hcp-inputs-offline-final.log`); new documentation links and
  `git diff --check` passed. Existing Rust dead-code warnings concern uninstantiated relay
  management and are not a claim that remote control is working.

Completion slice, 2026-09-09: ComfyUI history output discovery, bounded preview retrieval and
in-session run history are implemented. Eleven ComfyUI contracts and eight workflow-input
contracts pass; the explicit live local ComfyUI test now exercises the same history discovery
and preview helper and returned a PNG in 1.09 seconds. Svelte check/build report zero errors or
warnings, the native Mac `.app`/`.dmg` builds, and MacBook-screen inspection shows current
ComfyUI readiness unlocking the ten workflows plus the packaged Output history panel.

Native Windows acceptance remains open. Video source
upload and the P-043 flow-warp redesign are separate feature work rather than part of the
image/prompt/seed editor contract. No module-status promotion was performed.
