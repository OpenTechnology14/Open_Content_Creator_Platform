# Proposal: Content Asset Generation (text-to-image)

**Queue row:** `P-004`
**Agent model / effort:** `gpt-6.1-sol` / `medium` — One versioned ComfyUI graph with reproducible GPU evidence
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Draft — scoped, not started
**Owner:** Project owner
**Date:** 2026-08-23
**Roadmap layer(s):** Content Creation (Guide 4); Storage / Data
**Evidence level:** Verified against repo state at `main` on 2026-08-23. Nothing below has been run — ComfyUI was not reachable at `127.0.0.1:8188` during this pass, so no workflow was executed or load-tested.

## 1. Executive summary

Commit a **versioned text-to-image workflow** so generating an image from a prompt is a reproducible platform capability rather than an ad-hoc local action.

**This is a reproducibility gap, not a capability gap — read this before scoping anything on top of it.** ComfyUI generates images from text natively; that is its primary function, and its default graph on first launch *is* a text-to-image workflow. `models.md` already recommends SDXL base 1.0 ("High-quality stills") and SDXL Turbo ("Single-step generation") as checkpoint slots. So an operator with ComfyUI installed and either checkpoint downloaded can generate images **today**, with no change to this repo.

What's missing is narrower and worth stating precisely: **this repo commits no workflow that does it.** Every workflow versioned here begins by loading an image that already exists, so the generation path is whatever each operator wires up by hand in their own ComfyUI — unversioned, unreviewed, not reproducible on another machine, and not covered by the workflows README's own conventions. The export half is already solved: `modules/realtime-ai/comfyui/scripts/output_to_minio.py` watches the output directory and uploads to MinIO.

**Smallest shippable result:** one committed, load-tested SDXL text-to-image workflow JSON plus its README index row and model entry. That alone closes the capability gap; everything else in this proposal is optional layering on top.

## 2. Verified current state

Verified by reading files and parsing node graphs on 2026-08-23, not inferred from documentation.

**Workflows that exist and what they actually do** — parsed `class_type` values from each JSON:

| File | Entry node | What it does |
|---|---|---|
| `modules/realtime-ai/comfyui/workflows/realtime-lcm-stylize-v1.json` | `LoadImage` | Style-transfers an existing image via LoRA + LCM |
| `modules/realtime-ai/comfyui/workflows/realtime-segmentation-v1.json` | `LoadImage` | Background removal (`BRIA_RMBG_Zho`) |
| `modules/image-editing/workflows/video-frame-edit-v1.json` | `VHS_LoadVideo` | Inpaints a single frame of an existing video |
| `modules/realtime-ai/comfyui/workflows/00-starter.json` | — | **Empty stub** — `"nodes": []`, `"links": []` |

All three functional workflows begin at `LoadImage` or `VHS_LoadVideo`. **No committed workflow contains `EmptyLatentImage`**, the node that starts a generation from nothing.

To be precise about what that does and does not mean: it means no *committed* generation workflow exists. It does **not** mean the platform cannot generate images — ComfyUI does that natively, and `models.md` already lists suitable checkpoints (see below). The gap is versioning and reproducibility, not capability.

**Checkpoints are already documented.** `modules/realtime-ai/comfyui/models.md` already recommends SDXL base 1.0 (~7 GB, "High-quality stills"), SDXL Turbo (~7 GB, "Single-step generation"), and SD 1.5, plus LCM-LoRAs and an SDXL VAE. No new model entry is required for a basic SDXL text-to-image workflow — a correction to an earlier draft of this proposal, which wrongly listed adding one as work.

**What already works downstream:** `modules/realtime-ai/comfyui/scripts/output_to_minio.py` — real, complete code. Watches an output dir, uploads `.png/.jpg/.jpeg/.webp/.mp4/.gif` to a MinIO bucket (default `comfyui-outputs`). No change needed to it.

**The roadmap already asks for this.** `modules/realtime-ai/setup/manual.md` + `modules/content-creation/setup/manual.md` (was Guide 4, retired) states its status target as *"ComfyUI generating thumbnails/overlays, outputs landing in MinIO."* Generating a thumbnail from a prompt is squarely inside Guide 4's scope — this proposal does **not** exceed its guide, so no `docs/architecture/deviations.md` entry is required under `CLAUDE.md` §9.

Guide 4B is a different thing and is *not* where this belongs: its manual-steps checklist is generative fill, object removal, outpaint, upscale — all edits to an existing image.

**Incidental finding — documentation overstates what's committed.** `modules/realtime-ai/comfyui/workflows/README.md` indexes 8 image-editing workflows. Seven do not exist on disk:

| Documented in README | On disk? |
|---|---|
| `inpaint-fill-v1.json` | **missing** |
| `inpaint-remove-v1.json` | **missing** |
| `outpaint-expand-v1.json` | **missing** |
| `upscale-4x-v1.json` | **missing** |
| `auto-select-sam-v1.json` | **missing** |
| `background-replace-v1.json` | **missing** |
| `video-range-edit-v1.json` | **missing** |
| `video-frame-edit-v1.json` | present |

Not caused by this work and not fixed by it — recorded because anyone reading that index to decide what already exists will be misled, which is exactly the failure mode `docs/REPOSITORY_ALIGNMENT.md` warns about ("No repository may claim a feature is Implemented or Production solely because another repository contains a proposal or scaffold"). See §13.

**Resolved, 2026-09-01/02, by a different proposal — this finding is now stale, kept as history.**
`P-028` built all 7 of the "missing" files (`docs/PROPOSALS.md`), and `P-043` GPU-run verified 5
of them working end to end on real hardware (the 6th, `auto-select-sam-v1.json`, is confirmed
blocked on an upstream `transformers` incompatibility, not a naming gap). Both `workflows/README.md`
index tables now carry verified on-disk tables. **This proposal's own core ask — a committed,
load-tested SDXL text-to-image workflow — is unaffected and still open:** none of the 8 files
`P-028` built are text-to-image; every one of them loads an existing image (inpaint, outpaint,
upscale, segment, background-replace, video-frame/-range-edit). `00-starter.json` in
`modules/realtime-ai/comfyui/workflows/` remains a stub, not a real committed workflow. Found
during an exhaustive `docs/` sweep (`P-048`), matching `docs/PROPOSALS.md`'s own P-004 row
("Partly overtaken").

## 3. Problem, goals, and non-goals

**Actor:** the operator, running the platform locally, who needs an illustrative image for a blog post, a video thumbnail, or a stream overlay.

**Pain:** the operator can do this today, but only outside anything this repo versions — by hand-wiring a graph in their own ComfyUI, or in a different tool entirely. Nothing about that run is reproducible: not the graph, not the sampler settings, not the checkpoint it assumed. A second machine, or the same machine after a reinstall, starts from scratch. Every *other* ComfyUI operation the platform performs is a committed, reviewed, versioned workflow; generation is the one that isn't.

**Goals** (measurable):

- G1. A **committed** workflow file produces an image in ComfyUI's output directory from a text prompt and no other input — reproducibly, on a machine that has never generated one before.
- G2. That file reaches MinIO automatically via the existing `output_to_minio.py` watcher, with no change to that script.
- G3. The workflow loads on a clean ComfyUI install given only the models named in its README row — no absolute paths, per the workflows README convention.

**Non-goals** — each is a deliberate exclusion, not an oversight:

- **N1. No remote/HTTP generation endpoint.** Nothing here becomes callable from a website, a serverless function, or any non-local process. `CLAUDE.md` §10 forbids exposing a service to the public internet without an auth layer, and building an unauthenticated generation endpoint is precisely that.
- **N2. No media, prompt, or model input crosses to OpenTech or the cloud.** `PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md` lists those fields as forbidden across the companion boundary. Generation is local; only the operator moves the resulting file.
- **N3. No automated publishing pipeline.** Getting a generated image into a blog post is a manual step the operator takes (download from MinIO, commit it). Automating that is a separate decision with its own trust boundary, and it is not proposed here.
- **N4. No video generation.** Out of scope entirely. `modules/content-creation/` is READMEs with no code today; a text-to-video capability is a materially larger effort and needs its own proposal.
- **N5. Not fixing the seven missing workflows** from §2. Recorded, not adopted.

**Constraint:** the operator has stated they will generate images with another tool in the meantime. Nothing here is on a deadline, and no downstream work is blocked on it.

## 4. User paths and states

- **First run:** operator loads the workflow in ComfyUI → the referenced checkpoint is absent → ComfyUI reports the missing model by name. The README row must name the exact checkpoint file so this error is self-resolving.
- **Success:** prompt entered → queue → image written to the output dir → watcher uploads to MinIO → operator retrieves it from the console at `localhost:9001`.
- **Missing dependency (MinIO down):** generation still succeeds; the file sits in the local output dir. `output_to_minio.py` is a watcher, not a gate — generation must not depend on storage being up.
- **Missing dependency (ComfyUI down):** nothing to degrade gracefully — this is a manual, operator-initiated local action, not a service. There is no queue and no retry, by design (N1/N3).
- **Invalid input:** an empty or nonsense prompt produces a poor image, not an error. Quality review is the operator's eye; no automated quality gate is proposed.
- **Offline:** fully supported — this is the normal case. No network dependency beyond the local MinIO.
- **Cancellation:** ComfyUI's own queue-cancel. No platform-level state to unwind.
- **Recovery:** re-run. Generation is idempotent in the sense that nothing persists but the output file; a bad run costs GPU time and nothing else.

## 5. Architecture and data flow

```text
operator types a prompt
          |
          v
  ComfyUI (127.0.0.1:8188)          <-- entirely local, never exposed
  txt2img workflow
  CheckpointLoader -> CLIPTextEncode
    -> EmptyLatentImage -> KSampler
    -> VAEDecode -> SaveImage
          |
          v
  ComfyUI output directory
          |
          v
  output_to_minio.py (existing watcher)
          |
          v
  MinIO bucket `comfyui-outputs`     <-- local infrastructure
          |
          v
  operator downloads and uses the file
```

**Trust boundary:** everything above the last line is local to the operator's machine. There is no outbound call, no cloud relay involvement, and no OpenTech handoff anywhere in this path. The relay (`cloud/`) is deliberately not in this diagram.

**Module boundaries** (per `CLAUDE.md` §10 — no cross-module imports): the workflow JSON belongs in `modules/realtime-ai/comfyui/workflows/`, alongside the two workflows that already live there and the `output_to_minio.py` script that consumes their output. It does **not** go in `modules/image-editing/`, which is Guide 4B's editing scope.

**Sensitive data / retention:** prompts are typed into a local ComfyUI instance and are not logged by anything in this repo. Generated images persist in the local output dir and in MinIO until the operator deletes them. No retention policy is proposed — local storage the operator controls.

## 6. Direct injection map

| Location | Symbol | Before | Proposed change | Verification |
|---|---|---|---|---|
| `modules/realtime-ai/comfyui/workflows/10-txt2img-sdxl-v1.json` | new file | does not exist | SDXL text-to-image graph: `CheckpointLoaderSimple` → `CLIPTextEncode` ×2 (positive/negative) → `EmptyLatentImage` → `KSampler` → `VAEDecode` → `SaveImage` | Loads in ComfyUI from the Load menu with no missing-node errors; produces an image |
| `modules/realtime-ai/comfyui/workflows/README.md` | Index table | 00-starter only in the main table | Add a row: file, purpose, required model, custom nodes (none) | Row matches the committed file exactly |
| `modules/realtime-ai/comfyui/models.md` | checkpoint table | SDXL base 1.0 and SDXL Turbo **already listed** | No new entry needed. Optionally add the SHA256 + license to the existing SDXL base row, per Guide 4B's "update models.md with SHA256" convention | Hash matches the downloaded file |
| `modules/realtime-ai/setup/manual.md` + `modules/content-creation/setup/manual.md` (was Guide 4, retired) | Manual steps | no txt2img step | Add the checkpoint download to the manual-steps checklist | Step is followable on a clean machine |

Filename follows the README's stated `NN-shortname.json` convention, numbered `10-` to sort after the `00-starter` stub.

## 7. Contracts and examples

There is no API contract — this adds no endpoint (N1). The contract is the **workflow file format** and the README index row, both governed by conventions already written in `modules/realtime-ai/comfyui/workflows/README.md`:

- one workflow per file, no scratch JSON
- `models/<file>` relative paths, never absolute — so it loads on another machine
- custom-node dependencies documented in both the file metadata and the README (this workflow should need **none**; if a candidate design requires a custom node, prefer the stock-node version)

Configuration: none. No new environment variables, no `.env.example` change, no `docker-compose.yml` service — so `CLAUDE.md` §9 steps 5 and 6 do not apply.

## 8. Security, privacy, accessibility, and observability

- **Security:** no new attack surface. No listening port is added; ComfyUI's existing local bind is unchanged and stays unexposed (`CLAUDE.md` §10).
- **Privacy:** prompts never leave the machine. This is the concrete reason N1/N2 are hard non-goals rather than "later" — a remote generation endpoint would put prompts and generated media on the wire, which the companion proposal's forbidden-fields list rules out.
- **Accessibility:** N/A — no UI is added. Interaction is through ComfyUI's own interface.
- **Observability:** `output_to_minio.py` already logs uploads via `loguru`. No new metrics or alerts; a manual local action does not warrant them.
- **Repo hygiene:** the checkpoint is several GB. `CLAUDE.md` §10 forbids committing model weights or any binary >5 MB — the model is a documented download in `models.md`, never a committed file.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| T1 | Load the workflow in a clean ComfyUI with the checkpoint present | Loads, no missing-node errors | Manual | **Yes** |
| T2 | Queue a prompt end to end | Image appears in the output directory | Manual | **Yes** |
| T3 | Run with `output_to_minio.py` watching | File lands in the `comfyui-outputs` bucket | Manual | **Yes** |
| T4 | Load with the checkpoint **absent** | ComfyUI names the missing model; error is self-resolving from the README row | Manual | Yes |
| T5 | Generate with MinIO stopped | Generation still succeeds; file stays local | Manual | Yes |
| T6 | Inspect the committed JSON for absolute paths | None present — `models/<file>` form only | Review | **Yes** |
| T7 | Confirm no listening port or endpoint was added | `git diff` touches no compose/env/service file | Review | **Yes** |

All manual — this repo has no automated ComfyUI harness today, and building one is out of scope. T1–T3 and T6–T7 must pass before the workflow is described as working anywhere.

## 10. Delivery plan

**Phase 1 — the workflow (the whole shippable unit).** Author `10-txt2img-sdxl-v1.json`, run T1–T7, add the README row, the `models.md` entry, and the Guide 4 manual step. Acceptance evidence: a generated image plus its MinIO object key, recorded in the PR. Dependency: a machine with ComfyUI running and the checkpoint downloaded — which did not exist during this pass, and is why nothing here is built yet.

**Explicitly out of scope of Phase 1, listed so they are not assumed:** batch generation, prompt templating or presets, a dashboard UI for generation, the seven missing editing workflows, anything remote (N1–N3), and video (N4).

**Possible Phase 2, deliberately unscoped:** if generation gets used often enough for the manual loop to chafe, revisit — but revisit with usage evidence, not preemptively. The right shape of that layer depends on how it actually gets used, which nobody knows yet.

## 11. Rollout and rollback

No feature flag, no compatibility window, no data migration — adding a JSON file to a folder changes nothing about existing behavior. Rollback is deleting the file and its README row.

The one real risk to reverse is documentation: if the README row lands and the workflow turns out not to load, the repo now overstates itself in exactly the way §2's incidental finding describes. **Mitigation: the README row and `models.md` entry must land in the same commit as a workflow that has passed T1–T3, never ahead of it.**

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation / decision owner | Due |
|---|---|---|---|
| Workflow committed without being load-tested | Repeats the seven-missing-workflows pattern | Gate on T1–T3 with recorded evidence; do not merge on a written-but-unrun graph | Before merge |
| Checkpoint choice (SDXL base vs. a fine-tune) | Affects output style and disk cost | Operator decision; SDXL base is the conservative default because Guide 4B's inpainting models are already SDXL-family **Question:** Use the SDXL base checkpoint for text-to-image rather than a fine-tune? | Before Phase 1 |
| Scope creep toward a remote endpoint | Would breach `CLAUDE.md` §10 and the companion proposal's forbidden-fields list | N1/N2 are hard non-goals; any change to them needs its own proposal and an explicit owner decision, not an incremental PR | Standing |
| Generated-image licensing for public use | Blog/marketing use is public-facing; model licenses vary | Record the checkpoint's license alongside its `models.md` entry | Before first public use |

## 13. Documentation updates

- `modules/realtime-ai/comfyui/workflows/README.md` — add the index row (same commit as a tested workflow, per §11).
- `modules/realtime-ai/comfyui/models.md` — add the checkpoint entry with SHA256 and license.
- `modules/realtime-ai/setup/manual.md` + `modules/content-creation/setup/manual.md` (was Guide 4, retired) — add the checkpoint download to manual steps.
- `modules/realtime-ai/comfyui/workflows/README.md` — **separately**, correct the seven index rows in §2 that name files which do not exist. This is not part of Phase 1 and should not be bundled into it; it is a standalone honesty fix to an index that currently misleads.

## Related

- `modules/realtime-ai/setup/manual.md` + `modules/content-creation/setup/manual.md` (was Guide 4, retired) — the guide whose status target this closes.
- `modules/image-editing/setup/manual.md` (was Guide 4B, retired) — the editing scope this is deliberately *not* part of.
- `PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md` — the companion boundary that makes N1/N2 hard non-goals.
- `docs/REPOSITORY_ALIGNMENT.md` — the "don't claim it's implemented because a scaffold exists" policy that §11's gating rule enforces.
