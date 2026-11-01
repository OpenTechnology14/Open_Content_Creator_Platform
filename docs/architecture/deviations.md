# Deviations from the roadmap

Append-only log of intentional deviations from `roadmap.md`. The roadmap is
canonical; this file is where we record where reality diverged and why.

Entry format:

```
## YYYY-MM-DD — short title

- **What:** what changed
- **From:** what the roadmap said
- **Why:** the trigger
- **Effect on:** which other guides/modules need to follow
```

---

## 2026-10-12 — Private combined-shell preview before convergence

- **What:** Build the P-072 setup/navigation/profile/library/readiness preview alongside the
  two existing apps before the five convergence acceptance gates are complete.
- **From:** The roadmap allowed planning but gated combined-app implementation.
- **Why:** The owner requested continuing both Accepted proposals until ready for Testing,
  then explicitly answered "Build the private preview first" to the staged authorization question.
- **Effect on:** P-072, the roadmap, app build CI and testing lanes gain the private preview.
  This does not approve credential/device migration, full parity, public release, commercial
  changes, cloud phases or legacy replacement. Existing apps and acceptance gates remain.

---

## 2026-05-18 — Initial scaffold

- **What:** Built the full repo scaffold (9 guides, modules, observability,
  CI/CD, deploy script) in one pass instead of iterating phase-by-phase.
- **From:** Roadmap implies sequential bring-up (Guide 1 → Guide 9).
- **Why:** Scaffolding is cheap; populating each module is the actual phased
  work. The phase order in `CLAUDE.md` still governs which modules get
  attention first.
- **Effect on:** Nothing — guides remain in roadmap order. The repo is
  "ready for" each phase; the user still does the phases in order.

---

## 2026-08-30 — Marketing Crosswalk layer added

- **What:** Added `modules/marketing-crosswalk/`, a 15th top-level module, plus a
  matching "Marketing Crosswalk Layer" in `roadmap.md`. It generates marketing
  content for consumer modules registered in its own `crosswalk/modules.yml`. The
  first registered module is Task Management (`OpenTechnology14/Task-Management`);
  its content subjects are that app's six built-in project templates.
- **From:** `CLAUDE.md` §2.6 requires module boundaries to map 1:1 to roadmap layers,
  and the roadmap's fourteen layers are all runtime layers in the capture → process →
  publish path. This module is in none of them.
- **Why:** It is cross-cutting by construction — a content-generation capability whose
  consumers are registered one at a time. Filing it under `content-creation` (Guide 4:
  Blender, DaVinci, render pipelines) would have kept the 1:1 rule at the cost of
  misrepresenting its scope. The layer entry states explicitly that it owns no runtime
  and ships in neither app, so the fourteen product layers keep their meaning.
  Placement was confirmed with the repository owner before implementation.
- **Effect on:** No guide. It has no service, no port, no container, and no
  `docker-compose.yml` entry. Guides 1–9 are unchanged. **The fourteen modules under
  `modules/` are not registered as content consumers** — onboarding each is a separate,
  explicit step, and `validate` does not require a registry row for them.

---

## 2026-08-30 — Guides merged into modules; product labels added

- **What:** Retired the numbered guide series (Guides 1–9 + 4B). Setup steps moved into the
  module they set up, as `modules/<name>/setup/manual.md` and `setup/automated.md` — 30 docs
  across 15 modules. Every module is now labelled `Content`, `Stream`, or both. `roadmap.md`'s
  Guide Index became a Module Index; `CLAUDE.md` §4 and §11 are keyed by module instead of guide.
- **From:** The roadmap defined a parallel guide series with a many-to-many relationship to
  modules — Guide 7 set up three modules, and `realtime-ai` was owned by three guides. Module
  READMEs carried "Owner: Guide N" pointers.
- **Why:** The indirection made setup hard to follow in either direction and drifted silently.
  `modules/observability/README.md` claimed "Owners: Guides 6 + 10" — Guide 6 is audio production
  and Guide 10 has never existed. Owner-guide pointers are exactly the kind of hand-maintained
  cross-reference that goes stale unnoticed. Requested by the repository owner.
- **Effect on:** Every module gained a `setup/` directory, and the guide files are **gone** — the
  migration is complete, with no archive. Content was routed by kind: setup steps to
  `setup/manual.md`; automated paths and "use the app" sections to `setup/automated.md`, rewritten
  as *specified, not shipped*; and everything else — architecture rationale, latency budgets,
  trajectory math, NodeCG recipes, the Kubernetes deferral test, model-selection guidance — into
  the README beside the config file it explains. Six config docs were created to receive it
  (`sports-analytics/golf-tracer`, `sports-analytics/pose-estimation`, `ai-agents/local-llm`,
  `observability/prometheus`, `observability/grafana`, plus additions to nine existing ones).
  `docs/guides/README.md` is a redirect map from each old guide to both destinations.
  New modules must ship both setup docs and a label (`CLAUDE.md` §4, §9.4).

---

## 2026-08-30 — Nature and Cityscape Generation layers added

- **What:** Added `modules/nature-generation/` and `modules/cityscape-generation/` as two separate
  modules and two roadmap layers, plus a shared cross-module guide at `docs/IMAGE_INTAKE.md`.
  Each module spans an operation ladder from Tier 0 deterministic grading (CPU, no AI) to Tier 4
  LoRA adapter training.
- **From:** The roadmap had no layer for corpus-driven generation. The nearest existing layers are
  Image Editing (interactive, single-image, human-masked) and Content Creation (Blender/DaVinci).
  A first pass filed both domains as one `landscape-generation` module with two corpus folders.
- **Why two modules, not one:** the domains fail differently and the fix for one is wrong for the
  other. Cityscape requires ControlNet lineart at Tiers 2–3 — without it, straight edges bend and
  window grids melt, which is unusable rather than merely worse — while conditioning foliage on
  lineart freezes texture that should vary. Cityscape also has Tier 0 operations nature has none
  of (perspective correction, mixed-source white balance) and a night sub-domain needing its own
  adapter. A single mixed adapter softens architecture *and* over-structures foliage, satisfying
  neither. Splitting was the owner's call after the one-module draft.
- **Why intake is shared:** ingestion is identical for both — same buckets, same provenance
  record, same rights rules. Only *curation* differs, and that lives in each module's
  `corpus/README.md`. `docs/IMAGE_INTAKE.md` sits outside `modules/` because duplicating it into
  both would guarantee the copies drift; it is listed in `docs/guides/README.md` as the one
  cross-module guide.
- **Effect on:** No existing module changes behaviour. Both talk to ComfyUI over HTTP rather than
  importing `realtime-ai` (`CLAUDE.md` §10), and add `nature-corpus` / `cityscape-corpus` to
  `scripts/setup/minio_init.sh` when implemented. Their Tier 2 workflows may become additional
  consumers of `image-editing/workflows/inpaint-fill-v1.json` — recorded as an explicit decision
  in each module's workflow index. Cityscape likely needs its own variant (lineart conditioning);
  nature could plausibly reuse.

---

## 2026-09-01 — Asset Pipeline and Model Registry layers added (recorded 2026-09-02)

- **What:** Added `modules/asset-pipeline/` and `modules/model-registry/` as two new top-level
  modules, plus matching "Asset Pipeline Layer" and "Model Registry Layer" entries in
  `roadmap.md`. This entry is dated 2026-09-01 (when `P-017`/`P-018` actually shipped) but
  recorded 2026-09-02 — both modules' own `PROPOSALS.md` rows claimed "full module scaffolding,"
  but neither the roadmap layer nor this deviation entry was actually added at the time, despite
  `CLAUDE.md` §2.6 and `PROPOSAL_CREATION_SOP.md` both requiring both for any new top-level
  module. Found during an exhaustive `docs/` sweep (`P-048`), not by re-reading either proposal.
- **From:** The roadmap had no layer for cross-cutting storage/provenance infrastructure — the
  fourteen original layers are all runtime layers in the capture → process → publish path, and
  these two modules own no runtime.
- **Why:** `asset-pipeline` — four module files hand-rolled their own MinIO/S3 client before it
  existed, with two dedicated uploaders doing the same job; both generation modules specified a
  fifth and sixth consumer. `model-registry` — no manifest, checksum, or recorded license existed
  for any weight, while both generation modules require a pinned `manifest_sha256` that nothing
  enforced. Same reasoning as Marketing Crosswalk's own entry below: cross-cutting infrastructure
  consumed by other layers, not a product-facing capability with its own runtime.
- **Effect on:** No existing module's runtime behavior changes. `asset-pipeline` is consumed as a
  small library (`sys.path` insert, no `pip install` step) — never imported across a module
  boundary the way `CLAUDE.md` §10 forbids for peer modules; `model-registry` stores its manifests
  through `asset-pipeline`, not a second client. Both are `implemented` (`CLAUDE.md` §11) with
  real offline test coverage; `registry.yml` itself ships empty until a real downloaded weight is
  checksummed.

---

## 2026-09-02 — Soundboard layer added

- **What:** Added `modules/soundboard/` as a 20th top-level module, plus a matching "Soundboard
  Layer" in `roadmap.md`. A DJ-style sound bar: named, hotkeyed audio clips triggered live during
  a stream or recording, built on the third-party OBS plugin
  [`cg2121/obs-soundboard`](https://github.com/cg2121/obs-soundboard) (GPL-2.0) rather than a new
  standalone app.
- **From:** The roadmap had no layer for canned-clip playback. Owner-directed, requested by name
  ("a DJ sound bar setup ... load audio files and name them").
- **Why this tool, not a standalone soundboard app:** researched the field before building —
  `Soundux`, the most commonly recommended option, turned out to have **no macOS support** in its
  actual GitHub README (only Linux/Windows runtime deps and build steps are documented there,
  contradicting a secondary source that claimed cross-platform support) and is mid a "major
  rewrite" per its own README warning. `EXP Soundboard`'s original is effectively abandoned
  (community-maintained decompiled-source revivals only) and its own docs point at Soundflower, a
  macOS virtual-audio driver deprecated in favor of BlackHole years ago — the tool this platform
  already uses. `obs-soundboard` is a real, actively maintained OBS plugin (2.0.0, 7 releases,
  single maintainer but current) confirmed via its own GitHub repo and the OBS Forums resource
  page — cross-platform including Apple Silicon, and because it's an OBS-native audio source it
  needs **no separate virtual-audio-cable routing** the way `audio-production`'s tools do; it
  plays directly into OBS's own mixer.
- **Why the starter pack draws a copyright line:** the owner explicitly asked for "memes and
  popular editing sounds." The genuinely iconic ones (Vine Boom, Bruh, Windows Error, MLG Air
  Horn, "emotional damage," anime "wow," the Half-Life metal pipe, etc.) are every one of them
  extracted from a specific copyrighted movie, game, show, or piece of branded software — no
  meme-soundboard site's copy is actually public domain, whatever the site implies. This platform
  doesn't ship audio it doesn't have rights to, the same rule `docs/IMAGE_INTAKE.md` already holds
  photo corpora to. `sounds/manifest.yaml` ships 8 real CC0 clips (Kenney.nl, verified license per
  entry) covering the same functional categories — stingers, dings, a record scratch — and names
  every iconic slot as an explicit `placeholder` the creator fills in themselves, so the board has
  the right shape and hotkeys on day one even where the audio has to come from the creator.
- **Effect on:** No existing module changes behaviour. `audio-production`'s routing table is
  unaffected — the soundboard needs an OBS output-track assignment, not a virtual-audio-cable
  entry, and `soundboard/README.md` states that boundary explicitly so a future session doesn't
  try to force it into the routing matrix. `tests/USE-CASES.md`'s UC-1 gained a step (a stinger
  firing on a tracked golf highlight) so the module composes with the rest of the platform, not
  just exists in isolation — module count and coverage numbers throughout that file recomputed
  mechanically (`grep`, not by hand) alongside it.

---

## 2026-09-10 — Social Management layer added

- **What:** Added `modules/social-management/` as a 21st top-level module and a matching Social
  Management layer in the roadmap. It owns Stream/Content identities, approved logos, provider
  capabilities, OAuth account bindings, and the final posting/live-destination approval gate.
- **From:** The roadmap previously ended content flow at generation and stream flow at OBS
  automation. Automation Control emitted a disabled YouTube draft but no module owned reusable
  external-account identity, credentials, or publication execution.
- **Why:** The owner requested one place to manage many Stream and Content profiles, preload the
  main product and OpenTechApp logos, connect the actual accounts, and support both live streaming
  and content posting. Putting tokens in Automation Control or Marketing Crosswalk would mix
  scheduling/generation with the external trust boundary.
- **Effect on:** Both products may consume the same versioned dropdown and redacted connection
  records. Provider tokens stay in the OS credential manager; public publishing remains an exact
  approved-job action. The first adapters cover YouTube, Twitch, and X. Other catalog entries
  remain visibly registration-required or planned until their provider review and acceptance pass.

---

## 2026-10-04 — Plan desktop consolidation before convergence acceptance

- **What:** Added [P-072](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md), an accepted
  consolidation direction and planning contract for one desktop app with Stream/Create workspaces,
  plus candidate scope for an optional cloud companion and batch services. No app was merged.
- **From:** The roadmap's Future convergence path delayed proposal work itself until five
  workflow, shared-package, cross-product, relay and packaging gates passed. Their complete
  acceptance is not established today.
- **Why:** The owner explicitly requested the proposal now, stated that consolidation should
  happen to make distribution easier, and asked for risks and possible cloud scope. That request
  authorizes early planning; it does not supply missing acceptance evidence.
- **Effect on:** The queue, roadmap and product spec now link the plan and distinguish the
  intended single-app target from the two current delivery surfaces. Existing convergence gates
  still govern implementation; native replacement, branding/pricing decisions and C1–C3 cloud
  implementation do not follow automatically from this planning exception. Module layering,
  independent execution and local-first realtime paths are unchanged.
