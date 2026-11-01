# Proposal: Cityscape Generation learned tiers

**Queue row:** P-060
**Agent model / effort:** `gpt-6.1-sol` / `high` — Structural conditioning, corpus privacy and learned GPU tiers
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** Pending — [the queue](../PROPOSALS.md) is authoritative
**Owner:** Owner + agent
**Date:** 2026-09-09
**Roadmap layer:** Cityscape Generation
**Evidence level:** Verified current state; proposed implementation

## 1. Executive summary

Build the learned Cityscape Generation path above deterministic Tier 0. Begin with local
reference restyling, then add lineart-conditioned facade repair, outpainting, relighting, signage
removal, generated scenes and separately trained day/night adapters. Every structural workflow
must preserve straight edges and regular window grids.

## 2. Verified current state

- `modules/cityscape-generation/grading/` implements tested tone and perspective operations under
  P-041.
- `modules/cityscape-generation/workflows/README.md` specifies six Tier 1–3 workflows; none exists.
- The adapter guide requires separate day/night adapters and lineart metadata; no config or adapter
  exists.
- The `cityscape-corpus` bucket and privacy/rights guidance exist. No authorized corpus was inspected.
- Required IP-Adapter, SAM, depth and lineart models are not registered for this module.

## 3. Problem, goals, and non-goals

The module documents learned editing and generation but can currently perform only deterministic
grading and geometry. The goal is reproducible, provenance-bound local execution with geometry
acceptance at full resolution. This proposal does not authorize source photographs, model
downloads, face/license-plate publication, automatic readable-sign generation, or a cloud service.

## 4. User paths and states

The creator selects a workflow, source, mask and registered model set. Preflight requires lineart
conditioning for structural operations and rejects missing dependencies. Completed jobs record
workflow/model/corpus versions and outputs. Missing models, malformed masks, GPU exhaustion and
ComfyUI failures produce recoverable terminal states. Cancellation and restart never overwrite a
prior output or claim success without a completed artifact.

## 5. Architecture and data flow

Local Creator Extend and ComfyUI remain the primary path. Inputs, outputs and model weights stay
outside Git. Existing API and asset contracts connect modules; Cityscape Generation does not
import Image Editing or Realtime AI. Corpus manifests include privacy review and rights metadata.
Optional cloud batch execution may reuse the same contract only after local acceptance.

## 6. Direct injection map

| Location | Surface | Before | Proposed change | Verification |
|---|---|---|---|---|
| `modules/cityscape-generation/workflows/` | Tier 1–3 graphs | Index only | Add six versioned workflows with required lineart/depth contracts | Structural checks and real ComfyUI runs |
| `modules/cityscape-generation/adapters/` | Tier 4 configs | Documentation example | Add separate validated day/night configs | Schema/provenance tests |
| `modules/cityscape-generation/corpus/` | Corpus manifest | Guidance only | Add rights/privacy metadata validation; no images in Git | Negative privacy/rights tests |
| `modules/model-registry/registry.yml` | Required models | No cityscape entries | Register real checksummed dependencies/adapters | Registry verification |
| `apps/creator-extend/` | Workflow execution | General ComfyUI input editor | Expose only preflight-ready workflows and retained job results | Rust/UI and native acceptance |

## 7. Contracts and compatibility

Structural workflow metadata declares `requires_controlnet: [lineart]`; missing conditioning is a
validation error rather than a degraded run. Adapter configs reference a real corpus hash and
time-of-day. Existing Tier 0 behavior remains unchanged. Unknown paths, model IDs, node classes,
or output destinations fail before queueing.

## 8. Security, privacy, accessibility, and observability

Corpus intake must screen faces, license plates, addresses and location metadata according to the
shared intake guide. Logs contain identifiers and state, not media or credentials. Creator Extend
surfaces preflight, cancellation and errors accessibly. Metrics record duration, failure class,
GPU memory failure and geometry-review outcome without storing source media.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Level | Release gate |
|---|---|---|---|---|
| C1 | Structural workflow lacks lineart | Preflight rejects it | Automated | Tiers 2–3 |
| C2 | Corpus entry lacks privacy/rights review | Validation rejects training | Automated | Tier 4 |
| C3 | Reference restyle | Output retains building geometry at 100% | Local GPU + visual | Tier 1 |
| C4 | Facade/outpaint operation | Verticals and window grids remain regular | Local GPU + visual | Tier 2 |
| C5 | Sign removal | Region contains no generated pseudo-text | Local GPU + visual | Tier 2 |
| C6 | Day/night adapters | Each changes the intended look without cross-contamination | Local GPU + visual | Tiers 3–4 |
| C7 | Cancel/retry/restart | State remains truthful and outputs are immutable | Contract + live | App exposure |

## 10. Delivery plan

1. Resolve corpus privacy/rights and model/node decisions; register checksums.
2. Build and verify Tier 1 reference restyling.
3. Build Tier 2 facade repair, outpaint, relight and signage removal with lineart enforcement.
4. Train and register distinct day/night adapters.
5. Add Tier 3 generation and expose verified tiers in Creator Extend.

## 11. Rollout and rollback

Version and gate every workflow independently. Remove a failing workflow from the ready catalog
without deleting prior manifests or outputs. Tier 0 remains available throughout.

## 12. Risks and unresolved decisions

| Item | Impact | Decision owner |
|---|---|---|
| Rights/privacy-cleared day and night corpora | Blocks training **Question:** Will you supply rights- and privacy-cleared day and night cityscape corpora for training? | Owner |
| Lineart/depth node and checkpoint versions | Determines compatibility and output geometry **Question:** Will you confirm the lineart and depth node versions and the checkpoint for learned cityscape generation? | Owner + implementation |
| Local GPU benchmark and target resolution | Determines speed, quality and cloud need **Question:** Will you run a local GPU benchmark and set the target resolution for cityscape generation? | Owner |
| Separate workflow versus shared inpaint contract | Affects module independence **Question:** Keep the cityscape workflow separate, or share an inpaint contract with Image Editing? | Architecture review |

## 13. Documentation updates

Update the module README/setup guides, workflow and adapter indexes, model registry evidence,
Creator Extend readiness, `docs/AUDIT.md`, both module matrices, verification matrix, acceptance
checklist and this queue row as each phase becomes real.
