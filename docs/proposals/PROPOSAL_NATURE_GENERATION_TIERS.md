# Proposal: Nature Generation learned tiers

**Queue row:** P-059
**Agent model / effort:** `gpt-6.1-sol` / `high` — Learned GPU tiers, corpus rights and model provenance
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Pending — [the queue](../PROPOSALS.md) is authoritative
**Owner:** Owner + agent
**Date:** 2026-09-09
**Roadmap layer:** Nature Generation
**Evidence level:** Verified current state; proposed implementation

## 1. Executive summary

Build the learned Nature Generation path above the existing deterministic Tier 0. The smallest
shippable increment is one local reference-restyle workflow with a rights-cleared input and pinned
models. Later phases add sky replacement, outpainting, relighting, generated scenes and LoRA
training. Local GPU execution is the default; cloud batch compute remains optional.

## 2. Verified current state

- `modules/nature-generation/grading/` implements tested Tier 0 tone operations under P-041.
- `modules/nature-generation/workflows/README.md` specifies five Tier 1–3 workflows; none exists.
- `modules/nature-generation/adapters/README.md` specifies Tier 4 training metadata; no training
  configuration or adapter exists.
- The `nature-corpus` bucket and shared image-intake rules exist. No authorized corpus was inspected.
- The model registry exists, but the repository does not contain the models needed by these tiers.

## 3. Problem, goals, and non-goals

The module currently cannot perform any learned nature edit despite documenting the operations.
The goal is reproducible local execution with provenance, bounded inputs and visually reviewed
outputs. This proposal does not authorize a corpus, download model weights, train on unclear
rights, publish outputs, or introduce a new service or top-level module.

## 4. User paths and states

The creator selects a supported workflow, source image and explicit model/adapter manifest. A
preflight rejects missing nodes, models, provenance or GPU capacity before queueing. A completed
job records its source, workflow version, model checksums, parameters and output. Failure keeps
the source intact and supports retry. Cancellation stops queue ownership without claiming a GPU
process stopped until ComfyUI confirms it. Offline operation uses only local ComfyUI and storage.

## 5. Architecture and data flow

Creator Extend may submit a validated workflow to local ComfyUI. Large inputs, outputs and weights
remain outside Git in MinIO or local operator-selected storage. The module communicates with other
layers through existing ComfyUI/API and asset contracts; it does not import sibling modules.
Corpus manifests contain provenance metadata, not image binaries. Cloud execution is a later,
opt-in deployment of the same job contract.

## 6. Direct injection map

| Location | Surface | Before | Proposed change | Verification |
|---|---|---|---|---|
| `modules/nature-generation/workflows/` | Tier 1–3 graphs | Index only | Add versioned reference-restyle, sky, outpaint, relight and generation graphs by phase | Structural checks plus real ComfyUI runs |
| `modules/nature-generation/adapters/` | Tier 4 configs | Documentation example | Add validated training config tied to a real corpus manifest | Schema/provenance tests |
| `modules/nature-generation/corpus/` | Corpus manifest | Curation guidance only | Add metadata schema and validation; no images in Git | Invalid-rights and checksum tests |
| `modules/model-registry/registry.yml` | Required models | No nature entries | Register only downloaded, checksummed models/adapters | Registry verify/status |
| `apps/creator-extend/` | Workflow execution | General ComfyUI input editor | Expose ready workflows and output history after module preflight | Rust/UI contracts and native acceptance |

## 7. Contracts and compatibility

Workflow JSON follows the existing ComfyUI graph convention and carries a versioned `_meta`
block. Every adapter config references a non-placeholder corpus manifest hash. Existing Tier 0
CLI behavior remains unchanged. Jobs fail closed on unknown workflow IDs, missing model registry
entries, unsupported node classes, invalid paths, or outputs outside approved storage roots.

## 8. Security, privacy, accessibility, and observability

Inputs stay local unless the creator selects cloud execution. Logs exclude image contents and
credentials. Corpus validation enforces the shared rights vocabulary. Creator Extend must expose
preflight and terminal job states to keyboard and screen-reader users. Job duration, failure class,
GPU memory failure and output location are recorded without media payloads.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Level | Release gate |
|---|---|---|---|---|
| N1 | Missing model or custom node | Preflight names the dependency; nothing queues | Automated contract | Each phase |
| N2 | Invalid or unclear corpus entry | Validation fails before training | Automated | Tier 4 |
| N3 | Tier 1 reference restyle | Output completes and differs from source without losing structure | Local GPU + visual | Tier 1 |
| N4 | Sky replacement and relight | Mask boundary and foreground lighting pass visual review | Local GPU + visual | Tier 2 |
| N5 | Cancel/retry | State is truthful and source/output history is not overwritten | Contract + live | App exposure |
| N6 | Adapter at documented weight | Style changes without reproducing a training frame | Local GPU + visual | Tiers 3–4 |

## 10. Delivery plan

1. Resolve corpus rights and model/node choices; record real checksums.
2. Build and verify Tier 1 reference restyling locally.
3. Build Tier 2 sky replacement, outpaint and relight workflows.
4. Add Tier 3 generation only after a registered adapter exists.
5. Add Tier 4 training config and repeatable training evidence.
6. Expose only verified tiers in Creator Extend and update setup/readiness evidence.

## 11. Rollout and rollback

Each workflow is independently versioned and hidden until its readiness check passes. Rollback
removes it from the ready catalog while preserving manifests and outputs. Tier 0 remains available.

## 12. Risks and unresolved decisions

| Item | Impact | Decision owner |
|---|---|---|
| Rights-cleared corpus | Blocks training and distributability **Question:** Will you supply a rights-cleared nature image corpus for training? | Owner |
| Base checkpoint, IP-Adapter, SAM and depth nodes | Determines compatibility and GPU budget **Question:** Will you confirm the base checkpoint and the IP-Adapter, SAM and depth nodes for learned nature generation? | Owner + implementation |
| Local GPU benchmark | Determines usable resolution and whether batch cloud compute is justified **Question:** Will you run a local GPU benchmark to set the usable resolution and decide whether batch cloud compute is justified? | Owner |
| Reuse of Image Editing inpaint workflow | Could create a cross-module contract **Question:** Reuse the Image Editing inpaint workflow here, or keep a separate workflow so the modules stay independent? | Architecture review |

## 13. Documentation updates

Update the module README/setup guides, workflow and adapter indexes, model registry evidence,
Creator Extend readiness, `docs/AUDIT.md`, both module matrices, verification matrix, acceptance
checklist and this queue row as each phase becomes real.
