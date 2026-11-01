# corpus — cityscape

**Intake process is shared and documented once:**
[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md). This file covers only cityscape-specific
curation.

Bucket: `cityscape-corpus` in MinIO. Nothing here is committed.

## What belongs here

Skylines, streets, facades, bridges, interiors, industrial, night city.

**Anything with a hard straight edge belongs here even if the frame is mostly landscape** — a
pier, a bridge, a fence line, a road marking. The mixed-scene rule is in the intake guide: route
by failure mode, not by subject count. When torn, prefer this module — over-conditioning a nature
scene costs inference time; under-conditioning a structural scene produces bent output.

## Curation criteria

On top of the shared rejects:

| Reject | Why, specifically for cityscape |
|---|---|
| Uncorrected converging verticals | The adapter learns the lens, not the architecture |
| Heavy barrel/pincushion distortion | Same — correct at Tier 0 before curation |
| Readable signage dominating the frame | The model will produce pseudo-text there forever |
| Recognisable faces | Privacy — see below and intake §5 |
| Readable license plates | Same |
| Mixed day/night in one adapter's set | Night is a different dynamic range; separate it |
| Extreme HDR tone-mapping halos | Learned as an edge property, and edges are this domain |

## Night is its own sub-domain

Separate `curated/day/` and `curated/night/`, and train separate adapters. Night is not "day but
darker":

- **Dynamic range** — point light sources against near-black, not an evenly lit scene
- **Colour** — sodium, mercury, LED and neon in one frame, each a different temperature
- **Noise** — high ISO, and the adapter learns the noise as texture if the corpus is all noisy
- **Content** — lit windows and signage become the subject rather than the facade

An adapter trained on both produces washed evenings that are neither.

## Variance that matters

| Axis | Spread to aim for |
|---|---|
| Time of day | Day and night as **separate sets**, plus blue hour in each |
| Distance | Skyline, street level, and facade detail — an all-skyline corpus cannot generate a doorway |
| Weather | Wet streets behave completely differently; include them deliberately |
| Architecture era | Mixing brutalist and Victorian in one adapter averages both into neither |
| Focal length | Wide street work and compressed telephoto skylines are different looks |

Floor is ~30 curated images per sub-domain — so a day+night corpus wants ~60 minimum.

## Privacy screening

Higher exposure than nature; screen at curation, not later:

| Situation | Do |
|---|---|
| Recognisable face | Crop out, or set `people_present: true` and exclude from training |
| Crowd, nobody identifiable | Usually fine; record it |
| Readable license plate | Crop or blur before `curated/` |
| Private interior | Needs the owner's consent — record in `location_consent` |
| Restricted landmark | Some carry image restrictions for commercial use — check |

A blur applied *after* an image is already in `curated/` does not help: the training run that
already used it cannot be un-run. Screen before promotion.
