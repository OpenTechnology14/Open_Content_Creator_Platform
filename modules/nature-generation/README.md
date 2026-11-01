# Nature Generation

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

Learns a look from your own landscape photographs — terrain, sky, water, foliage, weather — and
applies it, from a full generated scene down to a saturation nudge.

**Image intake is shared with cityscape and documented once:**
[`docs/IMAGE_INTAKE.md`](../../docs/IMAGE_INTAKE.md). Read it before ingesting anything; it
carries the rights rules, the provenance record, and the matrix for deciding which module a photo
belongs to.

## The operation ladder

This module spans five orders of magnitude of cost. A saturation change and a trained adapter are
both "nature work", and treating them alike makes one absurdly slow and the other impossible.

| Tier | Operation | Backend | Cost | Deterministic? |
|---|---|---|---|---|
| **0** | Tone & colour — saturation, vibrance, exposure, white balance, curves | CPU | ms | **yes** |
| **1** | Reference restyle — match a corpus image's look | ComfyUI + IP-Adapter | s | no |
| **2** | Structural edit — sky replace, outpaint, relight | ComfyUI inpaint | s | no |
| **3** | Full generation — a new scene in a learned style | ComfyUI txt2img + adapter | s | no |
| **4** | Style learning — train an adapter | local training | hours | n/a |

**Route to the cheapest tier that does the job.** Pushing a saturation change through diffusion is
slower, non-reproducible, and destroys detail nobody asked to lose. Tier 0 is the correct answer
for tone work, not a fallback — and it is the only tier that is an exact function rather than a
sample.

## What makes nature different from cityscape

The two modules are separate because they fail differently, and the fix for one is wrong for the
other.

| | Nature (this module) | [Cityscape](../cityscape-generation/README.md) |
|---|---|---|
| Geometry | Organic, no hard priors | Straight lines, window grids, vanishing points |
| Characteristic failure | **Over-structuring** — output looks CGI; repeated foliage textures | Bent edges, melted windows, pseudo-text signage |
| ControlNet | Optional; depth helps terrain | **Lineart required**, depth for occlusion |
| Flagship Tier 2 op | Sky replacement | Facade and perspective repair |
| Tier 0 extras | — | Perspective correction, mixed-source white balance |
| Corpus variance that matters | Season, weather, time of day | Time of day, and night as its own sub-domain |

A single mixed adapter softens architecture *and* over-structures foliage — it satisfies neither
domain. That is the reason for two modules rather than two folders.

## Architecture

```
Your photographs ──► docs/IMAGE_INTAKE.md ──► nature-corpus (MinIO, never git)
                                                     │
                                    ┌────────────────┴─────────────┐
                                    ▼                              ▼
                        Tier 4 training ──► adapters/     Tier 0 grading (CPU)
                                    │                              │
                                    ▼                              │
                    Tiers 1–3 via ComfyUI HTTP (127.0.0.1:8188)    │
                                    └──────────────┬───────────────┘
                                                   ▼
                                    outputs → MinIO project-assets
```

This module talks to ComfyUI over HTTP; it does not import `realtime-ai` code (`CLAUDE.md` §10).

## Boundary with image-editing

[`image-editing`](../image-editing/README.md) also does inpaint-based edits. The split is who
drives: a human editing one image interactively there, a corpus and a learned style in batch here.
Fix one photograph there; make two hundred agree with each other here.

## Submodules

| Folder | Purpose |
|---|---|
| [`corpus/`](corpus/README.md) | Nature-specific curation criteria; intake itself is the shared guide |
| [`adapters/`](adapters/README.md) | Style adapter training config |
| [`workflows/`](workflows/README.md) | Committed ComfyUI workflow JSON, one per tier |
| [`grading/`](grading/README.md) | Tier 0 — deterministic tone operations, no AI |

## What lives where

Workflow JSON, grading presets, training configs — **committed**. Corpus images, adapters,
weights, outputs — **MinIO** (`CLAUDE.md` §10: never commit over 5 MB).

## Status

`scaffolded` (`CLAUDE.md` §11) — Tier 0 is real, tested code (`grading/`, 2026-09-01, `P-041`);
Tiers 1–4 are still just this README and the other config docs. Tier 0 was the cheapest first
implementation: no GPU, no models, no ComfyUI, and exactly testable — and now it's built.
Remaining learned tiers are queued separately as pending proposal
[P-059](../../docs/proposals/PROPOSAL_NATURE_GENERATION_TIERS.md); P-041 does not authorize them.
