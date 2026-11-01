# Future State & Goals

The compass, not the backlog. What "done" looks like, which pillar is furthest from it, and what
the next highest-leverage move is.

- The **parking lot** — deferred items with trigger conditions — is [`future.md`](future.md).
- The **canonical layer/module map** is [`roadmap.md`](roadmap.md).
- The **evidence of what is actually real** is [`../AUDIT.md`](../AUDIT.md). Nothing here may
  contradict it.

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a compass, not a priority queue and not an authorization. Work it
> points at becomes real only as a row in [`../PROPOSALS.md`](../PROPOSALS.md); what then waits on a
> person is tracked in the [decision and run lanes](../todo/README.md), and documents that do not
> exist yet in [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md).
>
> **Nothing reads this file automatically yet.** OpenTechnologyApp's audit reads its compass and
> appends a one-line "furthest pillar, highest-leverage move" to a capped log; that audit is proposed
> here as FD-11 in [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md) ([P-071](../proposals/PROPOSAL_DOCUMENT_GAPS.md)).
> Until it exists, the review date is the only freshness signal — and this file was found stale on
> 2026-10-04, as the corrected figure below shows.

---

## North-star

One modular platform that turns open-source creative tools into a creator system that can be
driven from any device — **without paying a subscription to use local hardware**. Stream Extend
and Creator Extend are the current desktop entry points; their shared architecture preserves a
future unified desktop shell and one companion mobile experience.

**One-liner:** OBS, ComfyUI, Blender, Krita, agents, and broadcast graphics behind one dashboard,
running locally, for a one-time $20.

**The wedge:** Local-first (the latency path never leaves the workstation) · One-time price, not
per-seat forever · One control surface instead of a plugin per capability · Cloud is opt-in for
exactly five features and nothing else.

---

## Strategic pillars

1. **Open the app, then build the local journey.** A packaged Stream Extend or Creator Extend
   reaches a usable setup window before OBS, Docker/WSL, Python, models or cloud setup. The app
   helps install/configure selected capabilities and records real verification. Standard setup
   runs without AI supervision; clean-machine launch and a complete creator journey need separate
   evidence. Keep source-build prerequisites separate from the user install path.
2. **Claims match evidence.** Nothing is described as shipped that `AUDIT.md` or `CLAUDE.md` §11
   calls scaffolded. This is now mechanically enforced for marketing copy by
   [`modules/marketing-crosswalk`](../../modules/marketing-crosswalk/README.md); it is not yet
   enforced anywhere else.
3. **Local-first holds under pressure.** No latency-sensitive path routes through the cloud.
   `product-spec.md` names exactly five cloud-gated features; that list does not grow quietly.
4. **Release posture is legitimate.** A root license, accurate source-available wording, no weak
   default secrets, no publicly bound datastores.
5. **A module is understandable from its own directory.** README with labels, `setup/manual.md`,
   `setup/automated.md`, and a config doc beside every config. ✅ **Met 2026-08-30.**

---

## Focal points (lead with these)

Current module status and operating-system evidence live in `AGENTS.md` §11 and
[`../AUDIT.md`](../AUDIT.md). The onboarding priority was updated after the Windows setup report
on 2026-09-12; a functioning Compose stack is useful after selecting features that require it.

1. **Both desktop apps open early.** P-003 already supplies shared selection, dependency installs,
   guides and readiness. [P-063](../PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup)
   plans Windows installable artifacts and additional app-run setup recipes. OBS or Docker failures
   must not strand users outside the apps. Track installer-to-window time, clicks and terminal/AI
   interventions per app, then selected-workflow completion separately. No measured speed claim yet.
2. **One complete creator journey.** The release checklist asks for exactly this — *"at least one
   complete local-first creator journey passes automatically or by a scripted acceptance
   harness."* Keep real capture, generation, credentials and service acceptance distinct from
   opening a dashboard or completing a dependency install.

**Depth stance:** promote modules past `scaffolded` **one at a time, with evidence**, rather than
raising the whole table. A single module at `implemented` unblocks its shipped-claim marketing
assets and proves the promotion mechanism works.

**The status table is wrong in both directions** (verified 2026-08-31). `storage-data`,
`observability`, and `backend-api` all actually run — they are mostly third-party services under
Compose, and what they lack is *evidence*, not code. Meanwhile `creator-experience`'s committed
scene collection is a self-described placeholder with eight empty scenes, and six modules assume
it is configured. The sequenced fix is [`../PROPOSALS.md`](../PROPOSALS.md) § "Build-out sequence"
(`P-016`, `P-024`–`P-028`).

---

## Honest positioning — what may and may not be claimed

`docs/REPOSITORY_ALIGNMENT.md` forbids claiming a feature is Implemented because another
repository holds a scaffold. The same discipline applies outward.

| Can be claimed today | Cannot be claimed until there is evidence |
|---|---|
| Module guides and the shared P-003 selection/dependency/readiness panel | Complete in-app prerequisite installation or a verified clean Windows first run |
| A running Compose stack with provisioned dashboards | That Docker is required to open either app |
| Bundled ComfyUI workflows and recorded Mac output runs (P-054/P-057) | That every workflow works on every GPU or Windows workstation |
| An offline test suite, CI acceptance harness and recorded native Mac app runs | Windows desktop installation, credential and physical capture acceptance without corresponding evidence |
| Source-available intent | "Open source" — no root license exists (`D-01`) |

---

## Horizons

### Now → next (ship-blockers)

Use `AUDIT.md`, `OPEN_SOURCE_RELEASE_CHECKLIST.md` and the proposal queue for current release
state. Earlier CI/build-scaffold findings were addressed by P-049–P-055; the remaining desktop
setup work is delivery and native acceptance, not rebuilding those foundations.

- **Root `LICENSE` and accurate wording.** Blocked on decision `D-01` in
  [`PROPOSAL_RELEASE_GAP_CLOSURE.md`](../proposals/PROPOSAL_RELEASE_GAP_CLOSURE.md). Everything
  else can proceed while it is pending.
- **App access before optional setup.** Deliver and verify both native Windows app installers;
  keep OBS, Docker/WSL, Python, models and accounts out of the packaged shell's launch gates.
- **Shared in-app setup actions.** Extend P-003 through P-063 with selected prerequisite recipes,
  progress, retry/skip and restart recovery. Keep routine execution off the AI operator's hands.
- **One verified local journey per claimed target.** Retain the automated harness and add the
  outstanding Windows desktop/hardware evidence. A first app window and an installed package
  are milestones, not proof of a working broadcast or generated output.

### Near (compounding moats)

- **Promote one module to `implemented` with evidence.** `storage-data` (`P-024`) is now the
  first candidate rather than `observability` — it is the smallest real work and eight modules
  depend on it. Proves the mechanism and unblocks the first shipped-claim marketing assets.
- **Resolve the ContentExtend naming decision.** `REPOSITORY_ALIGNMENT.md` says the product is
  ContentExtend; every surface says Creator Extend. Until settled, every generated guide-page and
  comparison-page draft carries a do-not-publish banner.
- **One storage contract and one model contract** — `P-017` is now **Phase 1**, not later: four
  modules already hand-roll a MinIO client and two more are specified, so doing it at four
  consumers is cheaper than at six.
- **Close the guide-page coverage gaps.** Seven modules have no planned page; `creator-experience`
  has one only on the Stream site, so Creator Extend readers are sent to the wrong domain.
- **Make the workflow indexes true.** Six indexed ComfyUI workflows do not exist; two live in a
  different module than the index claims.

### Later (vision)

- A unified desktop shell that enables Stream, Content, or both capability packs after both
  existing desktop journeys pass acceptance and cross-product use is proven.
- One mobile companion for readiness, approval-gated remote control, monitoring, notifications,
  and content review across either desktop shell or the future unified shell.
- Video generation from a learned style — the generation modules do stills only.
- Multi-camera sports fusion and a ball-flight physics model (see [`future.md`](future.md)).
- Captions and an auto-clipper driven from the event bus.
- A template/workflow marketplace.
- Kubernetes — only when all four conditions in [`k8s-decision.md`](k8s-decision.md) hold.

---

## Candidate module intake — direction, not approval

Suggested modules the future state implies. **None was approved at intake time** — three of the
four below have since been built. Kept here as a record of the intake reasoning, not as still-open
candidates. Re-verified 2026-09-02 (`P-046` doc sweep): a section titled "direction, not approval"
that quietly describes shipped modules as pending candidates is exactly the class of drift
`CLAUDE.md` §9 asks a session to correct, not just work around.

| Candidate | Labels | Outcome |
|---|---|---|
| `asset-pipeline` | `Content` `Stream` | **Built** (`P-017`, 2026-09-01) — `implemented`. See `../PROPOSALS.md` and `../../modules/asset-pipeline/README.md` |
| `model-registry` | `Content` `Stream` | **Built** (`P-018`, 2026-09-01) — `implemented`. See `../PROPOSALS.md` and `../../modules/model-registry/README.md` |
| `acceptance-harness` | repo tool, ships in neither app | **Built** (`P-016`, all 4 phases, 2026-09-01) — `tests/acceptance/`, CI-wired, first green run 33452956159 (private development evidence; not distributed) |
| `captions` | `Stream` `Content` | **Still a candidate** — `Deferred` as `P-019`. Later horizon. Already in [`future.md`](future.md) with a trigger; listed here so it is not intaken early |

### `asset-pipeline` — one storage contract

**Built, 2026-09-01 (`P-017`).** The rest of this subsection is the original intake reasoning,
kept as the record of why — the boundary it describes is what actually got built.

**Evidence it is needed.** Four module files carry their own MinIO/S3 client today, including two
dedicated uploaders doing the same job —
`realtime-ai/comfyui/scripts/output_to_minio.py` (104 lines) and
`image-editing/krita/scripts/export_to_minio.py` (255 lines) — plus
`realtime-ai/comfyui/bursts/worker.py` and `image-editing/krita/scripts/apply_style.py`.
`nature-generation` and `cityscape-generation` both specify corpus upload, which would make five
and six. Bucket names are repeated as literals across a dozen documents.

**Required boundary.** Owns the bucket layout, upload/download, presigned URLs, retention, and
the `landscape-corpus`-style bucket provisioning currently deferred in `minio_init.sh`. Does
**not** own what goes into a bucket, does not own model semantics, and must not become a
general-purpose service — `CLAUDE.md` §10 forbids cross-module imports, so it is consumed as a
small library or over HTTP through `backend-api`, decided in the proposal.

### `model-registry` — weights and adapters with provenance

**Built, 2026-09-01 (`P-018`).** The rest of this subsection is the original intake reasoning,
kept as the record of why — the boundary it describes is what actually got built.

**Evidence it is needed.** Model tracking today is a hand-maintained markdown table
(`realtime-ai/comfyui/models.md`) spanning four consuming modules, plus a second table in
`sports-analytics/models/README.md`. Weights live in MinIO with no manifest, no checksums, and no
recorded license. Meanwhile the two generation modules **require** a pinned `manifest_sha256` and
per-image rights for an adapter to be distributable — a contract nothing enforces and no schema
holds.

**Required boundary.** Owns the registry: entry per model or adapter with checksum, size, source,
license, the corpus manifest hash that produced it, and the conditioning it requires at inference
(`requires_controlnet`). Owns "is this adapter distributable?" as a computed answer rather than
prose. Does **not** own inference, does not own the corpus itself, and does not duplicate
`asset-pipeline` — it stores manifests through it.

### `acceptance-harness` — the executable creator journey

**Built, 2026-09-01 (`P-016`, all 4 phases).** The rest of this subsection is the original intake
reasoning, kept as the record of why — the boundary it describes is what actually got built.

**Evidence it is needed.** `OPEN_SOURCE_RELEASE_CHECKLIST.md` P0 engineering names it verbatim:
*"At least one complete local-first creator journey passes automatically or by a scripted
acceptance harness."* `AUDIT.md` records `tests/` as containing no tests against `TESTING.md`'s
126 described scenarios, and CI's pytest step as a placeholder.

**Required boundary.** Owns one journey end to end — bring up the Compose stack, assert service
readiness, drive a documented path, assert the observable outcome, tear down. Owns the CI wiring
that makes failure fail. Does **not** become a general test framework, and does **not** relax:
`CLAUDE.md` §9 already requires a failing-then-passing test per bug fix, and this module is what
makes that possible rather than a replacement for it.

It is a repo tool like `marketing-crosswalk` — it ships in neither app and owns no runtime.

### Why not other candidates

Considered and deliberately **not** suggested, so they are visibly rejected rather than missed:

| Considered | Why not now |
|---|---|
| `licensing` / activation | `product-spec.md` prices a $100 codebase license, but `D-01` has not settled what the license *is*. A module cannot enforce an undecided policy |
| `video-generation` | Later horizon. Both generation modules are `scaffolded` — Tier 0 (deterministic tone/geometry) is real and tested as of `P-041`, 2026-09-01, but Tiers 1–4 (the generative capability itself) are still design-only. Extending a generation design that has never generated anything is speculation |
| `consent-and-rights` as its own module | The rights rules already live in one place — `docs/IMAGE_INTAKE.md` — and are consumed by two modules. A module would add indirection without adding enforcement. Revisit if a third consumer appears |
| A `creator-extend` crosswalk module | Already covered: `content-extend` is registered in `marketing-crosswalk` |

---

## How we measure progress

Per pillar, a done-enough signal:

| Pillar | Done-enough signal |
|---|---|
| Local path works | One creator journey passes in CI on a clean clone |
| Claims match evidence | No module's status in `CLAUDE.md` §11 exceeds what a test or a run demonstrates |
| Local-first holds | The cloud-gated list is still exactly five features |
| Release posture | Root license present, no weak defaults, no public datastore ports **in the relay overlay**, secret scan clean |
| Module comprehensibility | Every module has README + both setup docs + config docs ✅ |

The most useful single number today: **modules past `scaffolded` — currently 4 of 21**
(`marketing-crosswalk`, `asset-pipeline` and `model-registry` — repo tools — and `storage-data`, the
first product module, promoted 2026-09-01 with real CI evidence via `P-016`). *Corrected 2026-10-04;
this said 2 of 17.* One caveat belongs beside it: `storage-data`'s evidence is a live CI run, and the
first real CI run since the billing block is red on that module's image pull —
[`PL-D08`](../todo/README.md#platform-and-release-decisions-no-lane-doc-yet).

---

## Maintenance

This is a compass; keep it short. When a Now item ships, move it out — into `roadmap.md` as a
layer capability or `PRODUCT`-facing docs — rather than letting this grow. Deferred ideas belong
in [`future.md`](future.md) with a trigger condition, not here.

Nothing enters the candidate table without evidence of the gap it closes, and nothing leaves it
without either a proposal or a recorded reason for rejection.
