# corpus — nature

**Intake process is shared and documented once:**
[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) — buckets, provenance record, rights
matrix, format matrix, and the which-module decision. This file covers only what is specific to
curating a *nature* corpus.

Bucket: `nature-corpus` in MinIO. Nothing here is committed.

## What belongs here

Terrain, forest, water, sky, weather, wilderness, coastline, desert, snow. Judge by **what is in
frame**, not where you stood — a city park with no buildings visible is nature.

**Anything with a hard straight edge a viewer would notice bending goes to
[cityscape](../../cityscape-generation/corpus/README.md)** — a pier, a bridge, a fence line, a
road marking. See the mixed-scene rule in the intake guide.

## Curation criteria

On top of the shared rejects (blur, noise, heavy grade, duplicates, watermarks):

| Reject | Why, specifically for nature |
|---|---|
| Blown-out white sky | Teaches the adapter that sky is featureless — sky is half of most frames here |
| One location dominating the set | Produces a model of that place, not of nature |
| All shot in one season | The adapter cannot generalise weather it never saw |
| Heavy dehaze or clarity already applied | Over-structures foliage, which is this domain's failure mode |
| Obvious focus stacking or HDR halos | The halo is learned as an edge property |

## Variance that matters

Nature adapters generalise on **conditions**, not on subjects. Aim to cover:

| Axis | Spread to aim for |
|---|---|
| Light | Golden hour, overcast, blue hour, harsh midday |
| Weather | Clear, cloud, fog, rain, snow if available |
| Season | At least two, ideally more |
| Distance | Wide vistas *and* mid-range detail — an all-wide corpus cannot generate foreground |
| Focal length | Vary it; a single lens bakes its distortion into the look |

Roughly 30 curated images is the floor before an adapter generalises rather than memorises.
80 varied beats 300 near-identical.

## Sub-domains worth separating later

If your corpus grows past a few hundred images, consider separate adapters rather than one:

- **Sky** — for Tier 2 sky replacement specifically
- **Water** — reflection and motion behave unlike static terrain
- **Foliage close-range** — the texture the over-structuring failure shows up in first

Keep them as sub-prefixes under `curated/` so one manifest still covers the whole set.
