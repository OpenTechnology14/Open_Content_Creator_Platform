# Use-case walkthroughs

> **Status:** Living · **Last reviewed:** 2026-09-10 · **Owner:** OpenTechnology14

<!-- PROPOSAL_WORK_INTAKE -->
> **Work intake:** this file is a set of use-case walkthroughs, not a priority queue and not an authorization. A failing step is a finding to route, not a task to start here.
> Unresolved implementation becomes a row in [`PROPOSALS.md`](../docs/PROPOSALS.md); what then waits on a person goes in the
> [decision and run lanes](../docs/todo/README.md); a document that does not exist yet is tracked in
> [`FUTURE_DOCS.md`](../docs/FUTURE_DOCS.md).

**What "the system works" means, end to end.** Two flagship workflows — one per product — that a
real creator would actually run. Between them they exercise **all 21 modules**.

**Enforcement: release gate, with the checklist.** A use case passing is the highest-level proof
the platform can offer. It is not a per-module gate: a step failing is a finding against the module
that owns it, and never blocks work elsewhere.

## Why this is a fourth document and not sprawl

`TESTING.md`'s division-of-labour table warns against exactly this, so the reason has to hold:

| Document | Shape | Question |
|---|---|---|
| `ACCEPTANCE-CHECKLIST.md` | Atomic lines, grouped by module | Is each capability true? |
| `TESTING.md` | Scenarios, grouped by module | How do I test one capability? |
| `docs/agent/VERIFICATION-MATRIX.md` | By change type | What proves the edit I just made? |
| **This file** | **Narrative sequence across modules** | **Does the whole thing work together for a real job?** |

The first three are all *per-module*. None of them asks whether the modules compose. That is a
different question, and it is the one an owner actually cares about.

**No capability appears here that is not also a checklist line.** This file sequences them; it does
not invent new ones. If a step here has no checklist line, the checklist is missing one.

---

## UC-1 — Live coaching stream with an AI co-host  (`Stream`)

*A golf coach streams a lesson. Their camera has a replaced background, a shot tracer draws on
each swing, an AI co-host reads chat and answers through an avatar, and the whole thing is
recorded and monitored.*

| # | What the creator does | Module | Proof |
|---|---|---|---|
| 1 | Brings up the platform stack | `infrastructure`, `storage-data` | **live** — `make up`, `make ps` |
| 2 | Opens OBS with the committed scene collection and encoder settings | `creator-experience` | **blocked** — scene collection is a placeholder (`P-027`) |
| 3 | Selects the stream profile/logo, connects the intended channel, and prepares its live destination | `social-management` | **manual** — contracts are automated; real account and provider acceptance are P-062 |
| 4 | Mic chain is live; AI voice on its own bus with mix-minus | `audio-production` | **manual** |
| 5 | Background removal running on the camera | `realtime-ai` | **manual** — needs a GPU |
| 6 | Stream session starts; a record lands in Postgres | `backend-api`, `storage-data` | **auto (P-016)** — `POST /streams` |
| 7 | Stream-start fires the automation workflow | `automation-control` | **manual** — needs OBS WebSocket |
| 8 | A swing is traced and composited into OBS over NDI | `sports-analytics` | **manual** — needs camera + GPU |
| 9 | The tracer emits a `shot_detected` event | `backend-api` | **auto (P-016)** — `POST /events` |
| 10 | A victory-fanfare stinger fires on the highlight | `soundboard` | **manual** — needs a live OBS + `obs-soundboard`; the clip itself ships (`sounds/manifest.yaml`, `P-044`) |
| 11 | Scoreboard/lower-third updates from that event | `broadcast-graphics` | **manual** — needs NodeCG + OBS |
| 12 | Chat reaches the agent; it answers and moderates | `ai-agents` | **manual** — needs Ollama |
| 13 | The answer drives the avatar's mouth and expression | `character-avatar` | **manual** — bridge wiring is `auto (P-042)` (`tests/character_avatar/test_avatar_control.py`); needs a live VTS + Redis to prove end to end |
| 14 | Recording is written and lands in MinIO | `storage-data` | **auto (P-016)** — round-trip |
| 15 | Grafana shows sources, buses, and GPU alive throughout | `observability` | **live** |
| 16 | Coach checks stream health from their phone | `infrastructure` | **blocked** — app is scaffolded |
| 17 | Session ends; the stream record closes | `backend-api` | **auto (P-016)** — `POST /streams/{id}/stop` |

**Modules exercised:** 14 of 21. Four steps marked `auto (P-016)` are **CI-verified as of 2026-09-01** — run 33452956159 (private development evidence; not distributed), the acceptance harness's first passing execution. The inserted Social Management step shifts the displayed row numbers without changing those four checks.

---

## UC-2 — Turn that recording into a published short  (`Content`)

*The same coach takes the recording, cuts a vertical short, restyles the stills with a look
trained on their own photographs, and produces the copy to post it.*

| # | What the creator does | Module | Proof |
|---|---|---|---|
| 1 | Pulls yesterday's recording from object storage | `storage-data` | **auto (P-016)** — round-trip |
| 2 | Extracts the best swing and its analysis overlay | `sports-analytics` | **manual** |
| 3 | Cuts a 9:16 short in Resolve; renders via Blender for titles | `content-creation` | **manual** — zero code, all desktop |
| 4 | Generates a thumbnail from a prompt in ComfyUI | `realtime-ai` | **blocked** — no committed txt2img workflow (`P-004`) |
| 5 | Cleans the thumbnail — removes a distraction, extends the frame, uploads it via `export_to_minio.py` | `image-editing`, `asset-pipeline` | **manual** — needs Krita for the interactive edit itself; the underlying `inpaint-remove-v1.json`/`outpaint-expand-v1.json` workflows are `auto`-adjacent (GPU-run verified, `P-043`) and the MinIO upload step is `auto` (`tests/asset_pipeline/`) |
| 6 | Applies their own landscape look to the course stills — the trained adapter's `manifest_sha256` comes from a registered entry | `nature-generation`, `model-registry` | **blocked** — design only, no code (`P-011`); the registry side is `auto` (`tests/model_registry/`) but there is no adapter to register yet |
| 7 | Corrects converging verticals on the clubhouse shot | `cityscape-generation` | **auto (P-041)** — `grading.geometry.perspective_correction()`; correctness proven by `tests/cityscape_generation/test_geometry.py`, not run against this specific photo |
| 8 | Renders land back in object storage | `storage-data` | **auto (P-016)** |
| 9 | Generates the post copy and a comparison-page brief | `marketing-crosswalk` | **auto** — `validate` + `selftest` |
| 10 | Copy correctly refuses to claim unshipped capabilities | `marketing-crosswalk` | **auto** — claim gating |
| 11 | Selects the Content profile/logo and approves a private upload to its connected account | `social-management` | **manual** — job gating is `auto` under P-062; real provider publication is pending |

**Modules exercised:** 11 of 21 (`asset-pipeline` added 2026-09-01 P-017 — step 5's MinIO upload; `model-registry` added 2026-09-01 P-018 — step 6's adapter provenance). Union with UC-1: **21 of 21.** Steps 1 and 8 (marked `auto (P-016)`) are **CI-verified as of 2026-09-01** — same run as UC-1.

---

## Coverage — the honest number

| Proof | UC-1 | UC-2 | Total | Share |
|---|---|---|---|---|
| **auto** — a command proves it | 4 | 5 | 9 | 35% |
| **live** — needs the stack up | 2 | 0 | 2 | 8% |
| **manual** — needs a human | 9 | 4 | 13 | 46% |
| **blocked** — cannot be proven yet | 2 | 2 | 4 | 15% |

**Nine of 28 steps can be automated today, and `P-016` covers six of them.** That is the
answer to "how much of the highest-level workflow can we prove by command" — a little over a
third, and it is the backend spine that every other step hangs off.

### What the 4 blocked steps are waiting on

| Step | Waiting on |
|---|---|
| UC-1.2 — scene collection | `P-027` — the committed file is a placeholder with 8 empty scenes |
| UC-1.15 — phone check | Both desktop apps are `scaffolded`; `docs/AUDIT.md` records no build scaffold |
| UC-2.4 — thumbnail generation | `P-004` — no committed text-to-image workflow |
| UC-2.6 — learned look (nature adapter) | `P-011` — Tier 4 (adapter training) is design-only; Tier 0 (`P-041`) is built but this step needs the trained adapter, not tone grading |

**None of these is blocked on `P-016`.** They are module work, and they are why the build-out
sequence exists.

---

## How this resolves `D-01`

`P-016`'s open decision asked whether a service-backed journey closes the release checklist's
*"at least one complete local-first creator journey."*

**It does not, and this file is why.** The complete journey is UC-1 — 16 steps, of which the
harness proves 4. Marking the checklist line closed on a backend journey would claim 26 steps
while proving 6.

**The line is closed when UC-1 passes end to end**, by any mix of command and human. `P-016`
closes its automatable portion and should say exactly that.

This also gives the manual work a target: **11 manual steps** across both use cases. Automating one
and deleting it is progress, the same measure `ACCEPTANCE-CHECKLIST.md` uses.

---

## Running a use case

1. Set up every module the use case names — `docs/agent/MODULE-MATRIX.md` for the cost.
2. Walk the steps in order. Order matters: step 8 cannot fire before step 7 produces a swing.
3. Record the result in the relevant `docs/PROPOSALS.md` rows — which steps passed, which were not
   run and why. **"Not run" is acceptable; silence is not.**
4. A failing step is a finding against its own module. Do not stop the walkthrough — finish it and
   record every failure, so one broken module does not hide three others.

## Adding a use case

Only when it exercises a combination the existing two do not. A third that re-walks UC-1 with a
different subject is not a new use case; it is the same one. Every step must map to a module and
to an existing `ACCEPTANCE-CHECKLIST.md` line.
