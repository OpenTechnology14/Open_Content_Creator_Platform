# Future work — parking lot

Things deliberately not built yet. **Every entry has a trigger condition** that should reopen the
discussion — an entry without one is a wish, not a decision.

This is the backlog. The compass — north-star, pillars, horizons, and candidate modules — is
[`future-state.md`](future-state.md). An item here graduates by becoming a proposal
([`../PROPOSAL_CREATION_SOP.md`](../PROPOSAL_CREATION_SOP.md)), not by being edited into existence.

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a parking lot, not a priority queue and not an authorization. An entry
> graduates by becoming a row in [`../PROPOSALS.md`](../PROPOSALS.md). Once it has a row, anything that
> waits on a person — an owner decision or a live run — also gets a row in the
> [decision and run lanes](../todo/README.md), and a document that does not exist yet is tracked in
> [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md). Do not duplicate those here.

> **Reconciled 2026-08-30.** Several entries had been overtaken by work in the repo and were
> describing gaps that no longer exist, or existed somewhere other than where this file said.
> Those are marked ✅ **landed** or 🔀 **moved** with what actually happened. Landed entries stay
> for one revision so the trigger history is legible, then get removed.

---

## Infra

- **Kubernetes (DOKS)** — see [`k8s-decision.md`](k8s-decision.md).
  **Trigger:** all four conditions in that doc hold. Restated in
  `modules/infrastructure/setup/automated.md`; if even one is false, stay on Compose.
- 🔀 **Distributed GPU render farm** — **moved.** The architecture, worker, and cost-control design
  now live at `modules/realtime-ai/comfyui/bursts/README.md`, and `worker.py` (~200 lines) exists.
  It is off by default and depends on Redis + FastAPI, which `make up` provides.
  **Remaining trigger:** a single GPU cannot keep up with ComfyUI batch jobs for ≥1 week — then
  provision the droplet, do not build the design again.
- **Edge caching for overlays** — Cloudflare in front of NodeCG.
  **Trigger:** NodeCG saturating uplink during a multi-platform restream.
- **Service mesh / mTLS** — only if and when K8s adoption happens. **Trigger:** inherits K8s's.

## Product surfaces

- **App-assisted workstation setup** — open either packaged Extend app before installing optional
  tools; move repeatable prerequisite/configuration steps into the shared local setup runner.
  **Trigger met 2026-09-12:** the owner reported Windows OBS and possible Docker blockers and
  requested faster app access with less AI-operated setup. Tracked as
  [P-063](../PROPOSALS.md#p-063--open-apps-first-and-extend-in-app-setup); the owner subsequently
  authorized the installer slice on the same date. Additional in-app recipes remain planned.
  Deliver Windows app artifacts first, then selected recipes, visible failures and restart/reboot
  recovery; extend P-003 rather than building another wizard. Docker/WSL is needed only for
  selected container features. Measure both apps on a clean Windows host before claiming speed
  or parity; public signing/distribution remains P-001. This work does not wait for shell unification.
- **Unified desktop shell** — preserve the current Stream Extend and Creator Extend apps while
  their workflows mature, but keep all modules and shared contracts compatible with one shell
  offering `Stream`, `Content`, or both capability packs. **Trigger:** both desktop journeys pass
  acceptance, three cross-product workflows pass with real inputs, the shared packages require no
  product forks, remote approval passes across two devices, and a packaging review shows a simpler
  first run. Then write a proposal covering migration, naming, pricing, stores, and compatibility.
- **Unified mobile companion** — one app for setup/readiness status, approval-gated remote control,
  monitoring, notifications, and content review across either current desktop app or the future
  unified shell. **Trigger:** the relay/device discovery and local approval contracts pass a hosted
  two-device test. Phone-camera contribution is a later slice after the control path is reliable.

## AI

- **Multi-persona orchestration** — several agents conversing on one stream.
  **Trigger:** at least one persona is stable enough to ship. `ai-agents` is still `scaffolded`,
  so this is two promotions away.
- **Voice cloning for the host** — only with an explicit consent flow and watermarking.
  **Trigger:** legal posture is clear. Same consent principle as face swap
  (`modules/realtime-ai/README.md`) and corpus rights
  ([`../IMAGE_INTAKE.md`](../IMAGE_INTAKE.md) §2) — do not treat it as a separate standard.

## Sports / CV

- **Multi-camera fusion** — a second camera for face-on swing capture.
  **Trigger:** ground-truth gathering for a fine-tune dataset begins.
- 🔀 **Custom YOLO fine-tune** for golf ball + club detection — **moved.** The three paths
  (community model, fine-tune on a public dataset, train from scratch) and their costs are now
  documented at `modules/sports-analytics/models/README.md`, including why a stock COCO model will
  not work: "sports ball" overlaps soccer and basketball.
  **Remaining trigger:** collect ≥1k labelled frames, then pick a path from that table.
- **Ball-flight physics model** — launch angle and spin estimation.
  **Trigger:** camera calibration is reliable. The 2D pixel-trail math and its limits are at
  `modules/sports-analytics/golf-tracer/README.md`; a 3D tracer needs stereo cameras and is
  explicitly out of scope there.

## Ops

- 🔀 **Alertmanager → Discord/Pushover** — **partly moved.** `alertmanager.yml` and three rule
  files exist, and the channel trade-offs are documented at
  `modules/observability/prometheus/README.md`. What remains is real: **destinations are unfilled**,
  and `streaming.rules.yml` / `ai.rules.yml` do not exist.
  **Trigger for the destinations:** the first production incident worth being paged for.
  **Trigger for the missing rules:** the modules they watch pass `scaffolded` — an alert on a
  service that never runs is noise.
- **Cost dashboard** pulling from the DO billing API. **Trigger:** monthly spend > $50.
  A `cost.json` dashboard is listed as planned-not-built in `modules/observability/grafana/README.md`.
- **Public status page** (Statuspage / Uptime Kuma). **Trigger:** an external audience depends on
  us being up.

## Audio

- **Live captions / transcription** (Whisper.cpp or Faster-Whisper).
  **Trigger:** an accessibility ask from a viewer, or an auto-clipper that needs a transcript.
  Listed as a candidate module (`captions`) in [`future-state.md`](future-state.md) so it is not
  intaken early — it is a Later-horizon item, not a Now one.

## Content

- **Auto-clipper from the event stream** — an event such as `shot_detected` cuts a 9:16 reel
  candidate. **Trigger:** a post-stream highlight workflow exists to feed.
  Depends on `backend-api`'s event bus and, for captions, on the entry above.
- **Video generation from a learned style** — the generation modules produce stills only.
  **Trigger:** `nature-generation` or `cityscape-generation` passes `scaffolded` with a working
  Tier 3. Extending a design that has never run is speculation
  ([`future-state.md`](future-state.md) records this as a deliberate rejection).
