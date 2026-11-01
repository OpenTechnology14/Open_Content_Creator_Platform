# adapters — cityscape

Tier 4 output, Tier 3 input. **Not committed** — adapters live in MinIO under `models/cityscape/`.
The training config that produced each one is committed here.

## Why LoRA

Same reasoning as [nature](../../nature-generation/adapters/README.md): 50–200 MB, 1–3 h on a
12 GB card, small enough to hold several and weight per job. Full fine-tunes only if a LoRA
demonstrably cannot hold the look.

Holding several matters more here — **day and night must be separate adapters**, so a single
domain already needs two.

## Training config

```yaml
adapter: cityscape-neon-night-v1
base_checkpoint: SDXL base 1.0
corpus:
  bucket_prefix: cityscape-corpus/curated/night/
  manifest_sha256: …
  image_count: 71
rank: 32
learning_rate: 1e-4
steps: 2400
resolution: 1024
trigger_word: neon_ct_night
# Cityscape-specific: record the conditioning the adapter expects at inference.
requires_controlnet: [lineart]
```

`requires_controlnet` is not decoration. An adapter trained on straight-edged architecture and
then run *without* lineart conditioning produces bent output, and the failure looks like a bad
adapter rather than a missing node. Record what it needs.

`manifest_sha256` pins the training set — [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §4.
Register the trained adapter in [`model-registry`](../../model-registry/README.md)'s `registry.yml`
with `kind: adapter`, this same `manifest_sha256`, and `requires_controlnet: [lineart]` — an
adapter entry with no `corpus_manifest_sha256` is computed as **not distributable** there, so a
real value here (not the `…` placeholder above) is enforced, not just documented.

## Naming

`cityscape-<look>-v<N>`, with the time-of-day in the look where it applies:
`cityscape-neon-night-v1`, `cityscape-overcast-day-v2`. Applying a night adapter to a daylight
frame should be visibly wrong from the filename.

## Inference weight

| Strength | Effect |
|---|---|
| 0.3–0.5 | A tint of the look |
| 0.6–0.8 | **Usual working range** |
| 0.9–1.0 | Starts reproducing corpus composition |

Cityscape tolerates high strength **worse** than nature: at 0.9+ the adapter begins reproducing
specific building shapes, which a viewer recognises as a real building rendered wrong — a failure
mode nature does not have, because nobody recognises a specific tree.

## Distribution

Distributable only if every image in the pinned manifest is rights-clear **and** privacy-screened.
Cityscape carries more exposure — see [`../corpus/README.md`](../corpus/README.md) and
[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §5.
