# Cityscape Generation

**Labels:** `Content` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

Learns a look from your own urban photographs — skylines, streets, facades, night city — and
applies it, from a full generated scene down to a saturation nudge.

**Image intake is shared with nature and documented once:**
[`docs/IMAGE_INTAKE.md`](../../docs/IMAGE_INTAKE.md). Read it before ingesting anything.

## The operation ladder

| Tier | Operation | Backend | Cost | Deterministic? |
|---|---|---|---|---|
| **0** | Tone & colour, **plus perspective correction and mixed-source white balance** | CPU | ms | **yes** |
| **1** | Reference restyle — match a corpus image's look | ComfyUI + IP-Adapter | s | no |
| **2** | Structural edit — facade repair, outpaint, relight, sign removal | ComfyUI inpaint + **lineart** | s | no |
| **3** | Full generation — a new scene in a learned style | ComfyUI txt2img + adapter + **lineart** | s | no |
| **4** | Style learning — train an adapter | local training | hours | n/a |

**Route to the cheapest tier that does the job.** Tier 0 carries more weight here than in nature:
converging verticals and mixed-temperature street lighting are *geometry and colour* problems with
exact solutions, and sending them through diffusion invents new buildings to fix a lens.

## Why this is a separate module from nature

Same ladder, different physics. The fix for one domain is wrong for the other.

| | Cityscape (this module) | [Nature](../nature-generation/README.md) |
|---|---|---|
| Geometry | Straight lines, window grids, vanishing points | Organic, no hard priors |
| Characteristic failure | **Bent edges, melted window grids, pseudo-text signage** | Over-structuring; output looks CGI |
| ControlNet | **Lineart required** at Tiers 2–3, depth for occlusion | Optional; depth helps terrain |
| Tier 0 extras | Perspective correction, mixed-source white balance | — |
| Sub-domain that needs its own adapter | **Night** — different dynamic range entirely | Season |
| Privacy exposure | High — people, plates, interiors | Low |

A single mixed adapter softens architecture *and* over-structures foliage, satisfying neither.

## The three failures you will actually hit

Worth stating plainly, because each has a specific fix:

1. **Bent lines.** Diffusion has no concept of "straight". Fix: ControlNet lineart, weighted high.
   This is not a quality upgrade — without it, output is unusable.
2. **Melted window grids.** Repeating small structures get averaged into mush. Fix: generate at
   higher resolution than you need and downscale; grids survive downscaling, not upscaling.
3. **Pseudo-text on signage.** Models produce text-shaped noise. There is **no fix** — either mask
   signage out, compose the frame to avoid readable text, or accept it. Do not attempt to prompt
   your way to legible signage.

## Architecture

```
Your photographs ──► docs/IMAGE_INTAKE.md ──► cityscape-corpus (MinIO, never git)
                                                     │
                                    ┌────────────────┴─────────────┐
                                    ▼                              ▼
                        Tier 4 training ──► adapters/     Tier 0 grading + geometry (CPU)
                                    │                              │
                                    ▼                              │
                Tiers 1–3 via ComfyUI HTTP + lineart conditioning  │
                                    └──────────────┬───────────────┘
                                                   ▼
                                    outputs → MinIO project-assets
```

Talks to ComfyUI over HTTP; does not import `realtime-ai` code (`CLAUDE.md` §10).

## Boundary with image-editing

[`image-editing`](../image-editing/README.md) is a human editing one image interactively. This is
a corpus and a learned style applied in batch. Fix one photograph there; make two hundred agree
here.

## Submodules

| Folder | Purpose |
|---|---|
| [`corpus/`](corpus/README.md) | Cityscape curation, the night sub-domain, privacy screening |
| [`adapters/`](adapters/README.md) | Style adapter training config |
| [`workflows/`](workflows/README.md) | Committed ComfyUI workflow JSON, one per tier |
| [`grading/`](grading/README.md) | Tier 0 — tone, perspective, mixed-source white balance |

## What lives where

Workflow JSON, grading presets, training configs — **committed**. Corpus images, adapters,
weights, outputs — **MinIO** (`CLAUDE.md` §10).

## Status

`scaffolded` (`CLAUDE.md` §11) — Tier 0 is real, tested code (`grading/`, 2026-09-01, `P-041`),
including perspective correction, which this domain needs most; Tiers 1–4 are still just this
README and the other config docs. They are queued separately as pending proposal
[P-060](../../docs/proposals/PROPOSAL_CITYSCAPE_GENERATION_TIERS.md); P-041 does not authorize them.
