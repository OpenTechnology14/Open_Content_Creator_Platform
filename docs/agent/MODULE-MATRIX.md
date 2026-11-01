# Module usage & complexity matrix

> **Status:** Living · **Last reviewed:** 2026-09-10 · **Owner:** OpenTechnology14

**Purpose:** given a module, know **how much other work depends on it** and **how expensive it is
to actually stand up** — before committing to a session, not after discovering it three hours in.

Companion to [`MODULE-ITEM-MATRIX.md`](MODULE-ITEM-MATRIX.md) (what a module *is*) and
[`../SETUP-TECHNIQUE-NOTES.md`](../SETUP-TECHNIQUE-NOTES.md) (the friction you hit while doing it).

**Enforcement: reference.** Read before starting a module's setup. Nothing fires it automatically.

---

## Why "unscriptable manual steps" is the cost proxy, not lines of code

Observed while writing all 34 module setup docs (2026-08-30): **code volume does not predict setup
cost, and inverts it.** `observability` has ~750 lines of Python and is one command
(`make up`) — everything it needs is containerised. Content Creation's local Shorts CLI is now
automated, while installing Blender and DaVinci Resolve remains manual. The Blender addon lives
outside the module at `plugins/blender-addon/` (P-036); P-056 adds code inside the module.

The actions no script in this repository can perform:

| Category | Examples |
|---|---|
| **Desktop app install** | OBS, ComfyUI, Krita, Blender, DaVinci, VoiceMeeter, VTube Studio, Ollama |
| **Model weight download** | SDXL (~7 GB), SAM (~2.5 GB), ControlNet, LLM pulls — license-gated, never committed |
| **GUI-only configuration** | OBS settings panels, VoiceMeeter routing matrix, Krita plugin enable, Grafana password |
| **Physical / hardware** | Camera placement and calibration, mic and interface, audio routing |
| **Human judgement** | Image rights and provenance, corpus curation, balance tuning |

Every estimate below counts **those**, because they are what reliably cost far more than
everything around them — regardless of how much code the module contains.

---

## The matrix

**Usage** = how many other modules depend on this one being up.
**Complexity** = unscriptable setup cost, from the categories above.

| Module | Labels | Usage | Depended on by | Complexity | Dominant cost |
|---|---|---|---|---|---|
| `storage-data` | `C` `S` | **High** | 8 modules | **Low** | `make up` + two scripts. Nothing unscriptable except the pgvector extension |
| `creator-experience` | `C` `S` | **High** | 6 modules | **Medium** | Windows bootstrap, capture discovery, and Stream Extend-managed recording handoff are automated; OBS source/profile settings and picture/audio acceptance remain manual |
| `realtime-ai` | `C` `S` | **High** | 4 modules | **Very high** | ComfyUI install + venv + Manager, then ≥2 checkpoints at ~7 GB each. The largest download in the repo |
| `backend-api` | `S` | **Medium** | 3 modules | **Low** | `make up`. Only unscriptable step is choosing an API key |
| `automation-control` | `C` `S` | **Medium** | 2 modules | **Medium** | `make up-with-automation` + import script are scripted; enabling OBS WebSocket and filling n8n credentials are not |
| `observability` | `S` | **Low** | — (consumes) | **Low** | `make up`, dashboards provisioned. Only the Grafana password is manual |
| `infrastructure` | `S` | **Low** | — (hosts) | **Medium** | Compose is scripted; Tailscale install and per-node auth keys are inherently manual  Native CLI and shared desktop panel select/install Python dependencies and check versions/app presence; full service acceptance and native Windows verification remain separate. |
| `broadcast-graphics` | `S` | **Low** | — | **Medium** | `make up-with-graphics`, then `npm install` per bundle and an OBS Browser Source per graphic |
| `soundboard` | `C` `S` | **Low** | — | **Low** | Download the `obs-soundboard` installer, run it, restart OBS. Loading the starter pack is a few clicks |
| `audio-production` | `S` | **Low** | — | **High** | Three OS-specific tools, a routing matrix built by hand, and mix-minus that is wrong until it is right. Routing references are committed; native preset compatibility and hardware setup need acceptance. Native speech-file export has a shared Mac/Windows test runner; native Windows evidence remains pending |
| `ai-agents` | `S` | **Low** | — | **High** | Ollama install + a multi-GB model pull + pgvector by hand + an unapplied migration |
| `character-avatar` | `S` | **Low** | — | **Medium** | PNGTuber is asset prep; VTube Studio is a paid desktop app with face-tracking calibration |
| `image-editing` | `C` | **Low** | — | **High** | Krita install + manual plugin file-copy + GUI enable + SDXL Inpainting (~7 GB) + SAM (~2.5 GB) |
| `sports-analytics` | `C` | **Low** | — | **High** | `pip install` is the only scripted part. Camera placement, calibration, and a model that must be fine-tuned dominate |
| `nature-generation` | `C` | **Low** | — | **Very high** | Everything `realtime-ai` needs, **plus** corpus rights research, curation, and 1–3 h of GPU training. Tier 0 alone is Low |
| `cityscape-generation` | `C` | **Low** | — | **Very high** | Same, plus a required ControlNet download and day/night as two separate corpora and adapters |
| `content-creation` | `C` | **Low** | — | **Medium** | Module folder has the local stream Shorts selector/review/renderer; Stream Extend-managed recordings now enter Creator Extend's local inbox, while generic recording/chat job ingress remains open. The real Blender addon (4 working operators, 1 stub) lives at `plugins/blender-addon/`. P-057 adds per-run workflow image/prompt/seed inputs; desktop/model/OS acceptance remain separate. |
| `marketing-crosswalk` | `C` | **Low** | — | **Low** | `pip install pyyaml`. The only module with no unscriptable step at all |
| `social-management` | `C` `S` | **Low** | automation/content publication | **Medium** | Local picker is scripted; provider registration, OAuth consent, channel eligibility and live acceptance are manual |
| `asset-pipeline` | `C` `S` | **Low** | 2 modules | **Low** | `pip install -r requirements.txt` (minio, loguru). No service, no download, no GUI step at all — a library, not something to stand up |
| `model-registry` | `C` `S` | **Low** | 0 modules (nothing depends on it existing yet — 3 tables reference the weights it *should* track) | **Low** | `pip install -r requirements.txt` (pyyaml, loguru). The unscriptable part is entirely downstream — populating `registry.yml` needs real downloaded weights and license research, not this module's own setup |

`C` = `Content` · `S` = `Stream`

---

## Reading it as a plan

**Cheapest → most expensive:** `marketing-crosswalk` / `storage-data` / `backend-api` /
`observability` / `soundboard` → `creator-experience` / `automation-control` / `social-management` / `infrastructure` /
`broadcast-graphics` / `character-avatar` / `content-creation` → `audio-production` /
`ai-agents` / `image-editing` / `sports-analytics` → `realtime-ai` →
`nature-generation` / `cityscape-generation`.

**The quadrant that matters:**

| | Low complexity | High complexity |
|---|---|---|
| **High usage** | `storage-data` — do it first, everything needs it | `realtime-ai`, `creator-experience` — budget a session each; four and six modules are blocked behind them |
| **Low usage** | `marketing-crosswalk`, `social-management`, `observability`, `backend-api` — safe to fold into any session | `nature-generation`, `cityscape-generation`, `audio-production` — their own session, and nothing else waits on them |

**Two non-obvious consequences:**

1. **`realtime-ai` is the real bottleneck.** It is Very high complexity *and* four modules depend
   on it — `image-editing`, `content-creation`, and both generation modules are unreachable until
   ComfyUI is installed with checkpoints downloaded. It is the single highest-leverage setup in
   the repository, and the one most likely to be underestimated because its own doc reads short.
2. **Tier 0 is an escape hatch from the worst row.** Both generation modules are Very high overall,
   but their Tier 0 grading needs no GPU, no models, and no ComfyUI. If tone or perspective work is
   what you want, the complexity rating does not apply — see each module's `grading/README.md`.

## How to use this before starting

1. Check the row before committing to a single session.
2. **Very high / High:** plan on the download time being the session. Start weight downloads before
   anything else; they are wall-clock, not attention.
3. **Low:** safe to fold in alongside other work — there is no unscriptable tax.
4. Check the **Depended on by** column before starting a Low-usage module. Doing
   `cityscape-generation` before `realtime-ai` means stopping halfway to install ComfyUI anyway.
5. If a module's real cost diverges from its row once you have done it, that is `DM-MODULE-DRIFT`
   ([`DOC-UPDATE-MATRIX.md`](DOC-UPDATE-MATRIX.md)) — update this table in the same session.

## What this deliberately does not rate

**Implementation** cost — how hard the module is to *build*. As of 2026-09-02, four modules are
`implemented` (`CLAUDE.md` §11: `storage-data`, `marketing-crosswalk`, `asset-pipeline`,
`model-registry`) — updated from the original "every module except `marketing-crosswalk`" claim,
which went stale the moment `P-016` Phase 4 and `P-017`/`P-018` promoted the other three.
Implementation cost for the remaining 16 is currently unknowable and a made-up number would be
worse than none. This table rates **setup**: standing up what the docs already describe.
