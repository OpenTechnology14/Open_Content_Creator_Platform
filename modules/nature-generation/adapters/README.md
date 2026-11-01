# adapters — nature

Tier 4 output, Tier 3 input. **Not committed** — adapters live in MinIO under
`models/nature/`. What is committed here is the training config that produced each one.

## Why LoRA

| Approach | Size | Train time | Verdict |
|---|---|---|---|
| **LoRA** | 50–200 MB | 1–3 h on a 12 GB card | **Default** — small enough to hold several and weight per job |
| Full fine-tune | 2–7 GB | days | Only if a LoRA demonstrably cannot hold the look |
| Textual inversion | KB | minutes | Too weak for a whole look; fine for one recurring motif |

Keeping adapters small is what makes per-condition adapters affordable — overcast, golden hour,
and winter as three weighted adapters rather than one averaged compromise.

## Training config

One YAML per adapter, committed, named for what it produces:

```yaml
adapter: nature-overcast-v1
base_checkpoint: SDXL base 1.0
corpus:
  bucket_prefix: nature-corpus/curated/
  manifest_sha256: …          # pins the exact training set
  image_count: 84
rank: 32
learning_rate: 1e-4
steps: 2400
resolution: 1024
trigger_word: ovrcst_landscape
```

`manifest_sha256` is the point of the file — see
[`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §4 step 5. Once the adapter is trained,
register it in [`model-registry`](../../model-registry/README.md)'s `registry.yml` with
`kind: adapter` and this same `manifest_sha256` — the registry's `is_distributable()` check treats
a missing `corpus_manifest_sha256` on an adapter entry as **not distributable**, so this field
being real (not the `…` placeholder above) is enforced there, not just documented here.

## Naming

`nature-<condition>-v<N>`. The domain prefix is load-bearing: applying a cityscape adapter to a
forest is a mistake the filename should make obvious at a glance.

## Inference weight

| Strength | Effect |
|---|---|
| 0.3–0.5 | A tint of the look; structure is the base model's |
| 0.6–0.8 | **Usual working range** |
| 0.9–1.0 | Strong; starts reproducing corpus composition, not just palette |

If output resembles specific training frames, the corpus is too small or too uniform. Fix the
corpus, not the strength — see [`../corpus/README.md`](../corpus/README.md).

## Distribution

Distributable only if **every** image in the pinned manifest is `owned`, `licensed` (with an ML
clause), `cc-by`, or `public-domain`. One unclear image makes the adapter unclear — the weights do
not separate. Rights matrix: [`docs/IMAGE_INTAKE.md`](../../../docs/IMAGE_INTAKE.md) §2.
