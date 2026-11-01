# Proposal: Nova profile registry, walkthrough engine and mascot system

**Queue row:** `P-067`
**Agent model / effort:** `gpt-6-astra` / `xhigh` — Autonomous walkthroughs, account routing and avatar contracts
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Proposed — awaiting owner decision` — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md)
**Owner:** OpenTechnology14 + agent
**Date:** 2026-09-22
**Roadmap layers:** Character / Avatar, Automation / Control, Content Creation, Broadcast Graphics, Social Management
**Evidence level:** None. This is a specification. No code is proposed in this PR.

---

## Non-goals

Read these first. Each exists because it is the obvious wrong turn.

1. **Gameplay rendering is not rebuilt.** [`modules/character-avatar/`](../../modules/character-avatar/)
   plus the Creator Extend pipeline already covers gameplay capture, avatar animation and clip
   production. This proposal **cites** that path and does not respec it.
   **But gameplay profiles *are* in scope for registration** — they live in the same registry as
   everything else, and point at that existing execution path. The registry is the unification; the
   renderer is not.
2. **Not a general screen-recording product.** This drives *our* content against *our* targets from
   committed scripts. It is not a Loom competitor.
3. **No autonomous publishing.** Output lands in the recording inbox and stops. Publishing keeps the
   P-062 human-approval boundary, exactly as `P-065` does.
4. **No voice cloning of any real person named as a style reference.** See §7.3. This is a legal
   boundary, not a preference.
5. **No live real-time narration in v1.** TTS is pre-rendered (§7.4).

---

## 1. The profile registry

### 1.1 Nova is one character, not twenty

The show bible is unambiguous: *"The same name, voice and avatar persist across games and
human/agent handoffs. Game variations change vocabulary and interests; they do not replace the main
character."* The live config backs this — [`configs/local/stream-autopilot.yaml`](../../configs/local/stream-autopilot.yaml)
declares a single `main_personality` block with `voice_id: nova-local` and `avatar_id: nova-vrm`.

**So a profile is not a personality. A profile is Nova-in-a-context.** The base character is defined
once at the registry root; each profile references it and layers on content-scoped tuning.

This matters practically: it means adding a game does not mean inventing a host, and it means a
viewer who follows Nova from Minecraft to a blog walkthrough meets the same character with a
different register — which is the whole value of a shared identity.

```
profiles/
├── nova.yaml                    # the ONE base character record
├── accounts/
│   ├── games.yaml               # account binding + voice binding
│   ├── reactions.yaml
│   └── opentechnology.yaml
├── minecraft/config.yaml
├── dota2/config.yaml
├── ...
├── try-not-to-laugh/config.yaml
└── opentechnologyblog-walkthrough/config.yaml
```

Proposed location: `profiles/` at the repository root, not inside a module — the registry is
consumed by automation-control, character-avatar, content-creation and social-management alike, and
burying it in one of them would make the other three import across a module boundary that
[`CLAUDE.md`](../../CLAUDE.md) §10 forbids.

### 1.2 Granularity: one profile per game or concept, not per show

The catalog in [`configs/local/stream-programming.yaml`](../../configs/local/stream-programming.yaml)
has 45+ scheduled show options. **Those are not profiles.** Minecraft's five formats — The Town That
Chat Built, One Chest Empire, Fix My Disaster, Redstone Court, Biome on a Budget — are one Nova, one
voice, one pet, one progression arc, in five episode shapes.

Making each show a profile would mean five near-identical configs drifting apart, and no coherent
place to record that Minecraft is the flagship or how far its world has progressed.

**Episode formats are subtypes inside a profile** (§1.5). **Progression is a first-class block**
(§1.6). This takes the working set from 54 to ~21.

### 1.3 The registry

**1 base character + 20 profiles**, with Flight Simulator pending a decision (**Q7**).

#### Base character

| Record | Holds |
|---|---|
| `nova.yaml` | `display_name: Nova`, base voice, `avatar_id: nova-vrm`, the two recurring lines ("Let's test that theory.", "Put that on the highlight reel."), the full emote vocabulary, and the values every profile inherits — never mocks a viewer's ability, never invents having seen an event, humor targets Nova's own predictions |

#### Game profiles — 13, all `gameplay-render`, all on the **Games** account

| Profile | Existing persona id | Delivery register (show bible) | Episode formats available |
|---|---|---|---|
| `minecraft` **(flagship)** | `nova-builder` | Balanced; livelier for challenges, calmer for cozy building | 5 concept shows + autonomy run |
| `dota2` | `rook-tactician` | Measured | 2 concept shows + bot-scripting autonomy run |
| `league-of-legends` | `lux-commentator` | Balanced | 2 concept shows |
| `world-of-warcraft` | `ember-storyteller` | Measured | 2 concept shows |
| `counter-strike-2` | `nova-clutch` | Measured | 2 concept shows |
| `gta-v` | `nova-city` | High expressive | 2 concept + City Asset Class + City Workshop Log |
| `valorant` | `nova-utility` | Balanced | 2 concept shows |
| `escape-from-tarkov` | `nova-explorer` | Measured | 2 concept shows |
| `fortnite` | `nova-finale` | High expressive | 2 concept + Island Design Class + Island Workshop Log |
| `overwatch` | `nova-team` | Balanced | 2 concept shows |
| `roblox` | `nova-worldhop` | High expressive | 3 concept + Build Class + Workshop Log + Agent Lab |
| `among-us` | `nova-detective` | High expressive | 3 concept shows |
| `beamng` | `nova-driver` | — | Route Learning Lab, Crash Test Court (experimental) |

#### Non-game streaming profiles — 4

| Profile | Account | Mode | Existing config |
|---|---|---|---|
| `try-not-to-laugh` | **Reactions** | `reactive-commentary` | `video-review` profile, `allowed_refs: [try-not-to-laugh]`, rights confirmation required |
| `nova-reviews-the-edit` | **Reactions** | `reactive-commentary` | same `video-review` profile, `operator-video-review` ref |
| `opentech-build-brief` | **OpenTechnology** | `walkthrough` | `opentech-marketing` profile, `allowed_refs: [opentechblog]` |
| `opentechapp-workflow-clinic` | **OpenTechnology** | `walkthrough` | same profile, `opentechapp` ref |

TNTL and Nova Reviews the Edit share one config profile today but are **separate registry
profiles**: reactive versus analytical is a genuinely different behavioral mode — different pacing,
different emote set, different drawing style — even though both are Nova and both are
commentary-only.

Build Brief and Workflow Clinic are likewise **two**, confirmed by the owner. One briefs, one
diagnoses; the registers differ.

#### Content profiles — 3, all **OpenTechnology**

| Profile | Mode | Notes |
|---|---|---|
| `opentech-operator` | `walkthrough` | **The four blog themes are content-lens tags on this one profile**, not four profiles — see §1.4 |
| `livestreamed-working-sessions` | `walkthrough` | Blog proposal `2026-08-26`, still Draft for owner decision |
| `opentechnologyblog-walkthrough` | `walkthrough` | **New.** The structured tutorial demo profile. Test-run target (§9) |

**Total: 1 base character + 20 profiles.**

### 1.4 Blog themes as content-lens tags, not profiles

The blog's
[`docs/CONTENT_THEMES.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/docs/CONTENT_THEMES.md)
defines four themes: The Operator, The Alternative, Hire the Operator, For Dummies.

**Start as one `opentech-operator` profile with `theme` as a per-episode tag.** Reasoning: the four
differ in *audience, sourcing rules and CTA* — not in who is talking. Nova explaining a comparison
table and Nova explaining it simply is the same Nova at two speeds. Four profiles would duplicate
the pet, voice and progression four times to vary two fields.

Each theme carries hard content rules that the tag must reference, because they are safety
boundaries rather than style:

| Theme | The rule that actually constrains a walkthrough |
|---|---|
| The Operator | An exclusion list: employer, work email, internal hostnames, headcount, and **any specific finding from an actual audit run**. Describing what the audit *system* does is fine; citing a *run* is not, ever |
| The Alternative | Every claim traceable to `src/data/openTechnologyApp.ts` or `PRODUCT.md` |
| Hire the Operator | Bolt-on CTA on Theme 1 pieces, not standalone — resolved 2026-08-29 |
| For Dummies | Every technical term defined inline on first use; never requires a command line. **Simpler wording, never lower accuracy** |

**The split stays available.** If For Dummies' voice and pet genuinely diverge — noticeably more
approachable, slower, a softer emote set — promote it to its own profile. The schema does not
change: a theme tag becomes a `profile_id`, the `mode_overrides` it was already carrying move up a
level, and nothing else moves. Designing for that now costs nothing and avoids a migration later.

### 1.5 Profile config schema

Three first-class blocks — `mode_overrides`, `episode_formats`, `progression` — plus account
binding.

```yaml
# profiles/minecraft/config.yaml
schema_version: 1
profile_id: minecraft
base_character: nova              # the one root record
display_name: "Nova plays Minecraft"
description: "Flagship game profile. Persistent world, viewer-directed building."

account_binding: games            # games | reactions | opentechnology
platforms: [twitch, youtube_gaming]

mode_overrides:
  execution_mode: gameplay-render # walkthrough | reactive-commentary | gameplay-render
  voice_tempo: balanced-warm      # account voice binding supplies WHO; this supplies HOW
  emote_set: [curious, delighted, thinking, proud, oops, celebrate]
  drawing_style: none             # gameplay-render does not annotate
  pacing:
    reaction_delay_ms: 400
  source_module: modules/character-avatar

episode_formats:
  - id: concept_show
    display_name: "The Town That Chat Built"
    show_ref: minecraft-town      # → stream-programming.yaml
  - id: concept_show
    display_name: "Redstone Court"
    show_ref: minecraft-redstone
    overrides:
      voice_tempo: analytical-measured   # format-scoped, same profile
  - id: autonomy_run
    display_name: "Permitted-environment autonomy"
    overrides:
      voice_tempo: calm-narrator
      emote_set: [curious, thinking, proud]
    gate: permitted-environment-confirmed   # §9 of the Stream Extend guide

progression:
  kind: world-state
  current: chapter-2
  timeline:
    - id: chapter-1
      label: "Spawn and first district"
      status: complete
    - id: chapter-2
      label: "Redstone infrastructure"
      status: active
      milestones: [power-grid, sorting-system]
    - id: chapter-3
      label: "The town square"
      status: planned
```

```yaml
# profiles/try-not-to-laugh/config.yaml
schema_version: 1
profile_id: try-not-to-laugh
base_character: nova
display_name: "Nova tries not to laugh"

account_binding: reactions
platforms: [twitch, youtube]

mode_overrides:
  execution_mode: reactive-commentary
  voice_tempo: reactive-fast
  emote_set: [smirk, hold-it, lose-it, deadpan, applaud]
  drawing_style: reaction         # circles, zoom-punches, emphasis marks
  pacing:
    step_dwell_ms: 700
    cut_style: punch-in
  source_module: modules/content-creation/reactive

episode_formats:
  - id: clip_reel
    display_name: "Try Not to Laugh Review"
    rights_gate: required         # non-negotiable — see §6.2

progression:
  kind: running-continuity
  current: season-1
  timeline:
    - id: season-1
      label: "Establishing the format"
      status: active
      running_gags: []            # accumulates; the engine may reference these
      commentary_maturity: establishing
```

```yaml
# profiles/opentechnologyblog-walkthrough/config.yaml
schema_version: 1
profile_id: opentechnologyblog-walkthrough
base_character: nova
display_name: "Nova walks you through the blog"

account_binding: opentechnology
platforms: [youtube_content]

mode_overrides:
  execution_mode: walkthrough
  voice_tempo: structured-teacher
  emote_set: [attentive, point, nod, think, celebrate]
  drawing_style: structured       # arrows, boxes, numbered callouts
  pacing:
    step_dwell_ms: 1800
    cut_style: none               # continuity is the pedagogy
  source_module: modules/content-creation/walkthrough

episode_formats:
  - id: feature_walkthrough
    display_name: "Publish your first post"
    target:
      app: opentechnologyblog
      base_url: "http://localhost:3000"    # never production — §5.3
      auth: fixture

progression:
  kind: catalog-coverage
  current: onboarding
  timeline:
    - id: onboarding
      label: "First-run flows"
      status: active
      covered: []
      planned: [publish-first-post, add-images, translations]
```

**What `progression` buys.** It is the block most likely to be dismissed as premature, so: it is
what lets the engine pick prompts and pet reactions consistent with where a profile actually is.
Nova should not introduce redstone as a new idea in chapter 3, and TNTL's pet should not deploy a
running gag in episode 1 that has not been established. Without a declared arc, every episode is
episode one — which is exactly the failure mode of AI-generated series content.

### 1.6 Account bindings

Three accounts, per the owner's 2026-09-22 correction. Each profile declares exactly one.

| Account | Profiles | Platforms |
|---|---|---|
| **games** | All 13 game profiles | Twitch + YouTube Gaming |
| **reactions** | `try-not-to-laugh`, `nova-reviews-the-edit` | Twitch + YouTube |
| **opentechnology** | `opentech-build-brief`, `opentechapp-workflow-clinic`, `opentech-operator`, `livestreamed-working-sessions`, `opentechnologyblog-walkthrough` | YouTube only |

**Creator Extend needs an account router.** Today its publishing path selects a connected account
from the social catalog by hand. With three accounts it must select the destination from
`profile.account_binding`, because the failure mode is silent and expensive: a gaming clip uploaded
to the OpenTechnology channel does not error, it just mistrains that channel's recommendations.

Routing rule, stated so it can be tested: `recording.content_profile_id` → `profile.account_binding`
→ account's connected YouTube/Twitch connection ID. A recording whose profile has no binding is
**refused**, not defaulted. Defaulting is how clips land on the wrong channel.

This also exposes a real gap:
[`modules/social-management/catalog.yaml`](../../modules/social-management/catalog.yaml) predates
the split and has **no live-capable Reactions profile** — `video-review` is `kind: content` with
`default_visibility: private` on both destinations, a staging identity rather than a broadcast one.
Adding one is a catalog change, and the catalog is compiled into the Tauri plugin, so it is a code
change with its own queue row. → **Q6**.

---

## 2. Three execution modes

The profile's `mode_overrides.execution_mode` picks one. This is the axis that decides what gets
built.

| Mode | What it does | Profiles | Build status |
|---|---|---|---|
| **`walkthrough`** | Autonomous UI driving, screen recording, drawing annotations, pet top-right, TTS narration | `opentechnologyblog-walkthrough`, `opentech-build-brief`, `opentechapp-workflow-clinic`, `livestreamed-working-sessions`, `opentech-operator` | **NEW — §5** |
| **`reactive-commentary`** | Pet + emote + TTS over externally supplied media. Rights gate. Commentary targets the work, never the person | `try-not-to-laugh`, `nova-reviews-the-edit` | **NEW — §6** |
| **`gameplay-render`** | Existing character-avatar + Creator Extend pipeline | All 13 game profiles | **EXISTS — cited, not respec'd** |

Two of three are new. The third is the largest by profile count and requires no work, which is the
main argument for the registry: it unifies how a profile is *declared* without forcing one
implementation of how it is *produced*.

---

## 3. New to build vs. existing to reuse

| New | Why it does not exist |
|---|---|
| Profile registry format + `profiles/` directory | No unified registry exists. `stream-programming.yaml` has show-level profiles; blog themes live in another repo; nothing joins them |
| **Walkthrough execution engine** — driver, recorder, annotation overlay | Nothing drives a UI and records it |
| **Reactive-commentary composer** | Nothing composites Nova over supplied media |
| **Pet render pipeline** | Feeds all three modes. Closest existing thing is VTS hotkey animation, which is a different renderer |
| Account router in Creator Extend | Publishing is single-account today |

| Reuse | What exactly |
|---|---|
| [`modules/character-avatar/stream_avatar/`](../../modules/character-avatar/stream_avatar/) | `runtime.py` drives animation from the speech worker's **real playback start, finish and cancellation events**, and rejects stale, duplicate, off-air and mismatched-finish events. `AvatarAdapter` is a `Protocol`. **This is the mouth-sync substrate** — §8 |
| [`modules/marketing-crosswalk/`](../../modules/marketing-crosswalk/) | `implemented`. 11 templates incl. [`stream-runofshow.md.tmpl`](../../modules/marketing-crosswalk/templates/stream-runofshow.md.tmpl). Generates first-pass scripts — §10 |
| [`configs/local/stream-speech.yaml`](../../configs/local/stream-speech.yaml) | Voice binding config, extended for real providers — §7 |
| [`modules/broadcast-graphics/`](../../modules/broadcast-graphics/) | Considered and **not** reused for the walkthrough overlay — §5.5 says why. Remains the overlay layer for `gameplay-render` |
| [`apps/shared/recording-library/`](../../apps/shared/recording-library/) | Inbox handoff, one new `RecordingOrigin` variant |
| Blog content infrastructure | `2026-08-23-ai-content-creation-module` (approved, infra landed), `2026-09-01-dummies-content-module` (built, zero posts), `course/scripts/*.md`, [`docs/learning/`](../learning/README.md) |

---

## 4. Workflow scripting format

### Decision: Markdown with YAML frontmatter, one fenced `step` block per beat

The blog's existing course shot lists are already 80% of this. `course/scripts/module-01.md`
carries: runtime target, viewer intent, CTA, SEO title, matching blog post (frontmatter); a **beat
sheet table** with `# / Beat / Time / Shot`; numbered **Demo steps** ("New project → Blank template");
narration in block quotes; and a YouTube description template. It even carries annotation directions
in prose — *"Overlay red X's on each manual step"*, *"Zoom on the automation firing"*,
*"Freeze-frame + circle"*.

Those are executable instructions written for a human editor. This format is the same document with
the ambiguity removed.

Pure YAML was rejected — narration is prose, and prose in block scalars is miserable to review.
Pure Markdown was rejected — "circle the button" does not say which button.

````markdown
---
schema_version: 1
profile: opentechnologyblog-walkthrough
episode_format: feature_walkthrough
slug: publish-your-first-post
theme: for-dummies          # content-lens tag (§1.4); omitted for non-blog profiles
runtime_target_seconds: 240
outputs: {video: true, stills: true}
---

## Beat 1 — find the draft

> Everything you've written but haven't published lives in one place.

```step
id: click-drafts
action: click
selector: '[data-testid="nav-drafts"]'
narrate: before
annotate: {kind: arrow, to: selector, label: "Drafts live here"}
pet: point
wait_for: '[data-testid="draft-list"]'
```
````

| Field | Values | Notes |
|---|---|---|
| `action` | `goto`, `click`, `type`, `select`, `scroll`, `hover`, `wait`, `assert`, `keyframe` | Deliberately small. A new verb is a feature request with a review |
| `annotate` | `none`, or `{kind, to, label}`; `kind` ∈ `arrow`, `circle`, `box`, `highlight`, `pen`, `redact` | The script says *what* to point at; **the profile's `drawing_style` says what pointing looks like** |
| `pet` | an emote from the profile's `emote_set` | Validated at lint time. A script cannot invoke an emote its profile lacks |
| `wait_for` | selector | Explicit waits only (§5.2) |
| `confirm` | `true` | Required on any destructive action (§5.3) |

**Lint before record.** Validates frontmatter, that the profile and episode format exist, that every
`pet` emote is in the profile's set, that every `annotate.kind` suits the profile's drawing style,
that no action is off-list, and that destructive verbs carry `confirm`. Lint is cheap; a failed
four-minute record is not.

---

## 5. Walkthrough engine

### 5.1 Playwright, Python, Chromium

The blog already ships Playwright — `playwright.config.ts`, `e2e/`, `playwright-report/`. Reusing
the framework the target tests itself with means selectors, fixtures and auth are shared rather than
reinvented. Python because its siblings here — `marketing-crosswalk`, `stream_autopilot`,
`stream_avatar`, `stream_shorts` — are Python and this must call them.

Desktop targets (OpenTechnologyApp) would need a native driver. **Deferred**, not designed here —
every profile currently marked `walkthrough` has a web target.

### 5.2 No sleeps

Every step waits on a selector or network-idle. A `sleep(2)` produces a recording that is either
visibly laggy or races the UI, differently on every run.

### 5.3 Security surface

An autonomous driver controlling a browser is a real surface. The honest mitigation is a small blast
radius, not a trusted driver.

| Control | Rule |
|---|---|
| **Target allowlist** | `base_url` must match an allowlisted origin — localhost, a preview deploy, or a dedicated staging account. **A production origin fails lint** |
| **Credentials** | Fixture accounts only, from the OS credential manager via `apps/shared/local-settings`. A literal credential in a script fails lint |
| **Destructive actions** | Delete, publish, payment or email-send needs `confirm: true` **and** interactive operator confirmation. Unattended runs **skip** confirmed steps and mark the recording incomplete rather than proceeding |
| **No open-ended navigation** | `goto` takes a path; the origin comes from frontmatter. Script content cannot steer the driver off-target |
| **Page content is data** | Scraped text is never interpreted as an instruction, never chooses the next action, never reaches TTS unreviewed. The script is the only source of control flow |

The last row is the load-bearing one. A driver that read the page and decided what to do next would
be an agent loop pointed at a browser — a different and much larger proposal.

### 5.4 Recorder

**ffmpeg + AVFoundation for v1; ScreenCaptureKit as the upgrade.**

Playwright's `record_video` is rejected: no audio track, no frame-rate control, viewport only — the
pet and annotations would need re-compositing anyway. It is a debugging feature.

Capture **1920×1080 at 30 fps**. Not 60 — this is mostly static pages, and 30 halves the file for no
perceptible loss.

Output registers with [`apps/shared/recording-library`](../../apps/shared/recording-library/) via a
new `RecordingOrigin::Walkthrough`, tagged with `profile_id` as `content_profile_id`. From there it
is an ordinary inbox row and Creator Extend needs no changes beyond the account router (§1.6). That
is the largest single piece of leverage in this proposal.

### 5.5 Annotation overlay — inject into the page, no transparent OS window

The obvious build is a transparent, topmost, click-through window. That is what you need to annotate
*arbitrary* applications. We are not: the target is a browser context we control.

So `page.add_init_script()` injects a fixed-position, `pointer-events: none`, max-`z-index` canvas on
every navigation.

| Consequence | Why it matters |
|---|---|
| Captured natively | No compositing pass, no alignment drift |
| Coordinates from `getBoundingClientRect()` | An arrow points at a button *because it asked the button where it is*. A window overlay guesses, and guesses wrong the moment the page scrolls |
| Survives scroll and resize free | It lives in the page's coordinate space |
| Zero OS permissions | No screen-recording entitlement, no accessibility grant |
| Testable without recording | Assert canvas contents in a normal Playwright test |

Cost, stated honestly: web targets only. That is the scope. A native target brings the
transparent-window design back as a second renderer behind the same interface.

**Not NodeCG.** [`modules/broadcast-graphics/`](../../modules/broadcast-graphics/) renders into *OBS
browser sources* — a separate server producing a source OBS composites. There is no OBS here.
Using it would mean running a NodeCG instance to draw a rectangle on a page we already hold a handle
to. It remains the right tool for `gameplay-render`.

**`redact` earns its place** in the annotation list: The Operator theme forbids hostnames, employer
identifiers and audit findings appearing anywhere. A selector-anchored blur is how a walkthrough
respects that mechanically instead of relying on someone noticing in review.

---

## 6. Reactive-commentary composer

For `try-not-to-laugh` and `nova-reviews-the-edit`. Source media is **operator-supplied or
licensed** — there is no UI to drive.

### 6.1 Shape

Input is a local video file plus a cue script: timecoded reaction beats rather than UI steps.

```step
id: beat-03
action: react
at: "00:01:12.400"
narrate: during
annotate: {kind: circle, to: region, box: [0.62, 0.30, 0.18, 0.22]}
pet: lose-it
```

`to: region` with normalized coordinates, because there is no DOM to query — the one place the
walkthrough engine's selector anchoring does not apply, and the reason this is a separate composer
rather than a flag on the same engine.

Composition is an ffmpeg filter graph: source video, pet overlay top-right, annotation layer,
narration audio mixed under source audio. No browser, no driver.

### 6.2 The rights gate is not optional

`stream-programming.yaml` already sets `rights_confirmation_required: true` on the `video-review`
profile, with `upload_enabled: false`, `visibility: private` and `approval_required: true`.

**Enforce it in the composer, not only in the config:** a cue script whose source media has no
recorded rights confirmation **fails before rendering**. The confirmation record — source, licence
or permission, date, who confirmed — is written next to the output and travels with the recording
into the inbox.

The show bible's rule, which belongs in the profile's system prompt verbatim: *review commentary
targets the work and editing choices rather than the person in the video.*

---

## 7. Voice and accounts

### 7.1 Where it stands

[`configs/local/stream-speech.yaml`](../../configs/local/stream-speech.yaml) declares
`voices: {nova-local: null}` — null meaning the OS default voice. Acceptable for a supervisor
rehearsal; for published content it is the most dated-sounding element you could ship, and viewers
judge it in three seconds.

### 7.2 Option B: three Nova variants sharing core identity

The owner selected this on 2026-09-22 over a single unified voice.

| | **Option A — one voice everywhere** | **Option B — per-account voice (chosen)** |
|---|---|---|
| Recognition | Strongest. Nova is instantly Nova | Weaker across accounts; strong within one |
| Fit | One register cannot serve TNTL and a Morgan-Freeman-vibe narrator | Each account gets a register that fits its content |
| Cost | One binding | Three bindings, three test passes |
| Risk | Wrong register on two of three accounts | Variants drift into three characters (§7.5 mitigates) |

Option A was genuinely viable and is worth recording as the road not taken: it is simpler and
maximizes recognition. It loses because an energetic Roblox register narrating a Build Brief is
worse than a slight identity fracture.

### 7.3 Voice bindings — and the guardrail

> **Hard guardrail.** Voice bindings intentionally use **pre-built voices matched to the requested
> vibe, never clones of the real people named as references.** Cloning iShowSpeed, Morgan Freeman or
> any real person's voice without written consent violates ElevenLabs' terms and creates
> right-of-publicity exposure. The named people are **style references for selection only** and must
> never appear in a prompt, a voice name, a config comment or marketing copy.
>
> If the owner wants a distinctive OpenTechnology voice beyond "Morgan Freeman vibe", the honest
> path is **cloning the owner's own voice** — roughly a 10-minute sample through ElevenLabs Voice
> Clone. Legally clean, and likely more distinctive than any pre-built.

| Account | Vibe | Starting binding | Alternates | Fallback |
|---|---|---|---|---|
| **games** | Young, energetic, expressive | ElevenLabs **Adam** | Josh, Sam | — |
| **reactions** | Young, energetic, Latin-accented | ElevenLabs **Diego** | Mateo | — |
| **opentechnology** | Deep, warm, measured, narrative | ElevenLabs **Dave** | Antoni | OpenAI Onyx |

For Reactions, **prefer a natively Spanish-accented voice speaking English over an accent overlay on
a neutral voice.** An overlay reads as an impression; a native accent reads as a person. This is a
selection criterion, not a synthesis setting.

```yaml
# profiles/accounts/games.yaml
account:
  id: games
  platforms: [twitch, youtube_gaming]
  voice_binding:
    provider: elevenlabs
    voice_id: adam                 # vibe-matched pre-built, NOT a clone
    vibe_reference: "young energetic expressive"   # descriptive; no real person named
    alternates: [josh, sam]
    fallback_provider: openai
```

Note `vibe_reference` carries a **description**, not a name. The named references live in this
proposal and in the owner's head; they do not belong in a config that ships.

### 7.4 Pre-render, never stream

Every narration line is synthesized to WAV before the run starts.

1. **Determinism** — the same script yields the same audio on every take. You iterate on pet,
   drawing and pacing (§10e); the voice must be the fixed variable.
2. **No network during capture** — an API call mid-recording is a stall in the video.
3. **Real durations** — pacing needs to know a line is 4.2 seconds *before* choosing a dwell. This
   turns pacing from a guess into arithmetic.

Cache by hash of `(text, voice_id, settings)`. Changing one line re-synthesizes one line, which is
what makes §10's iterate-independently loop affordable.

Playback emits the same start/finish/cancel events the speech worker already emits, so §8's adapter
needs no special case.

### 7.5 Test before committing a binding

Two passes, both required before any binding is locked:

1. **Side-by-side vibe check.** Play all three account voices against the same sample text. The owner
   confirms each matches intent. Bindings are cheap to change now and expensive after a catalog of
   VODs exists.
2. **Mid-clip identity check.** Switch account voice to account voice inside one clip and confirm
   **Nova is still recognizably Nova** across all three despite the vocal shift. This is the test
   that Option B has not silently become three characters. If Nova is not recognizable, the variants
   are too far apart — narrow them, or reconsider Option A.

### 7.6 Config inconsistencies worth cleaning up

Found while grounding this proposal. Harmless today, confusing later:

| Where | Says | Should be |
|---|---|---|
| [`PROPOSAL_STREAM_AUTOPILOT.md`](PROPOSAL_STREAM_AUTOPILOT.md) §example | `voice_id: local-voice-1` | `nova-local` — the live config's label. Both are labels for the OS default, so nothing is broken; the proposal example simply predates the name |
| `stream-autopilot.yaml` personas | `rook-tactician`, `lux-commentator`, `ember-storyteller` | Non-Nova-named persona IDs whose system prompts all say *"Keep Nova's original identity and phrasing."* The naming implies three separate characters the prompts explicitly deny. Renaming to `nova-tactician` / `nova-commentator` / `nova-storyteller` would match the other thirteen and the registry model |

Both are cleanup, not blockers. The second is worth doing **with** the registry, since the registry
is what makes the one-character model explicit.

---

## 8. Pet mascot pipeline

Feeds all three modes; the profile's `emote_set` selects which emotes are live.

### Decision: render into the injected overlay. Live, not post-composited.

| Approach | Verdict |
|---|---|
| **In-page overlay (chosen, `walkthrough`)** | DOM element in the injected layer, top-right at profile scale. Captured natively, frame-accurate by construction, re-runnable without a render pass |
| **ffmpeg overlay (chosen, `reactive-commentary`)** | No browser to inject into; the composer is already an ffmpeg graph (§6.1) |
| Post-composite for walkthroughs | **Rejected.** Needs an exact timeline export and a second render per iteration, re-introducing the drift the in-page layer eliminates. Its one advantage — re-skinning without re-running — is not worth turning a 30-second iteration into a five-minute one |
| VTube Studio live | **Rejected here.** VTS renders to a window for a webcam-tracked performer. No performer; capturing a second window is post-compositing with extra steps. VTS remains correct for `gameplay-render` |

**Asset format: sprite sheet with named emotes, not a VRM.** A 2D pet at 16–22% of frame height gains
nothing from a 3D rig, and a sheet is something the owner can commission or generate through the
existing ComfyUI path. Note this diverges from `avatar_id: nova-vrm` in the live config — the VRM
remains Nova's `gameplay-render` avatar; the sprite pet is her walkthrough/reactive form. **Q2**
asks whether that is acceptable or whether one asset should serve both.

### Mouth-sync: reuse the event contract, not the renderer

[`modules/character-avatar/stream_avatar/`](../../modules/character-avatar/stream_avatar/) already
solves this. `runtime.py` drives talk and idle animation **from the speech worker's actual playback
start, finish and cancellation events**, and `AvatarAdapter` is a `Protocol` — the VTS implementation
sits behind an interface. Its README states it animates from real playback timing and deliberately
rejects stale, duplicate, off-air and mismatched-finish events.

**That rejection logic is the hard part, and it is written.** Add a second `AvatarAdapter` emitting
to the overlay instead of VTS hotkeys; the event contract, session/generation guards and stale-event
rejection are inherited unchanged.

v1 fidelity is **talk/idle** — mouth moves while audio plays, rests when it stops. That is what the
existing worker provides and what a corner mascot at 18% of frame height can show. Viseme-level sync
has a clear trigger: someone complaining the mouth looks wrong at that size. Nobody will.

---

## 9. Test runs — two modes, two profiles

One profile from each mode being **built**. `gameplay-render` is not tested because it already
exists.

### Run 1 — `walkthrough`

| | |
|---|---|
| **Profile** | `opentechnologyblog-walkthrough`, account `opentechnology` |
| **Target** | "Publish your first post" on OpenTechnologyBlog, localhost |
| **Why** | Small, finite, genuinely first-user, ends in an observable state change. Exercises `goto`, `click`, `type`, `assert` without needing a verb the schema lacks |
| **Pass** | 3–5 min recording; narration in the OpenTechnology voice; pet animated in time with speech; ≥4 structured annotations correctly anchored; registered in the inbox with `content_profile_id` set and routed to the OpenTechnology account |

> **Correction, 2026-10-04.** The target above does not exist as a UI flow: OpenTechnologyBlog has no
> admin, login, editor or CMS route, and posts are published by merging an MDX file. The
> `data-testid` selectors in §4's example (`nav-drafts`, `draft-list`) and the "Publish your first
> post" episode in §1.5 are illustrative and describe a flow that was never real. Run 1 needs a new
> target — decision [CT-D09](../todo/CONTENT_CREATE_TODO.md). Nothing else in this section changes.

### Run 2 — `reactive-commentary`

| | |
|---|---|
| **Profile** | `try-not-to-laugh`, account `reactions` |
| **Target** | One operator-supplied clip with a recorded rights confirmation |
| **Why** | Opposite end of every axis from Run 1 — fast vs slow pacing, reaction marks vs structured arrows, loose vs steady prosody, punch-in vs no cuts, region-anchored vs selector-anchored annotation |
| **Pass** | Recognizably different output from Run 1, produced by **changing only `profiles/` data plus the mode's own composer** — no change to the registry schema. Rights gate blocks a run with no confirmation record |

**The acceptance criterion is Run 2's constraint**, not Run 1's output. Run 1 proves the walkthrough
engine works. Run 2 proves the registry is a *system* rather than one hardcoded format with
config-shaped decoration. If Run 2 forces a schema change, this proposal did not deliver what it
promised.

**Third check, cheap and worth it:** register one game profile — `minecraft` — in the registry
without building anything, and confirm the account router sends its existing Creator Extend
recordings to the Games account. That validates the unification claim without touching the gameplay
pipeline.

---

## 10. Authoring loop

**a. Pick a source.** A blog post, a `docs/learning/` lesson, a course script, a dummies companion,
or supplied media. The profile's `source_module` narrows it.

**b. Generate a first pass.** `marketing-crosswalk` is `implemented` and already renders templated
drafts from subject data. Add `walkthrough-script.md.tmpl` and a `walkthrough` command to
`generator/cli.py`. It emits frontmatter, beat structure and narration; it emits `step` blocks with
`selector: TODO`.

Precedent: `stream-runofshow.md.tmpl` already writes `_TODO_` into its timing column with *"Fill the
timings after the off-air rehearsal; do not invent them."* Same discipline — the generator does not
invent selectors it cannot verify.

**c. Human review.** Fill selectors, cut steps, fix narration. **Also the theme-rules gate** — no
linter can tell whether a sentence leaks an audit finding.

**d. Dry-record.** Full run to a scratch path, not registered. One question: does narration land on
the right frame?

**e. Iterate independently.**

| Change | Cost |
|---|---|
| Pet emote, scale, drawing style, pacing | Re-run, no re-synthesis — profile data |
| One narration line | Re-synthesize that line — hash-keyed cache |
| Voice | Re-synthesize all. Rare |
| Steps | Re-run — script data |
| Progression state | Config edit; affects prompt and emote selection next run |

**f. Final record → inbox → Creator Extend**, routed by account (§1.6). The channel review gate from
[`CREATOR_EXTEND_PRODUCTION_SETUP.md`](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md)
§8 Phase 3 — *would I put this on my channel?* — governs this output exactly as it governs gameplay
clips. An AI-narrated, AI-mascotted walkthrough has more ways to be subtly wrong, not fewer.

---

## 11. Static examples — annotated stills

Same script, headless, no video.

```bash
walkthrough capture --stills profiles/opentechnologyblog-walkthrough/scripts/publish-your-first-post.walkthrough.md
```

At every step carrying `annotate` (or an explicit `action: keyframe`), render the annotation layer,
screenshot the viewport, write a PNG plus a caption from that step's narration, and emit a manifest
mapping step id → file, caption, selector, annotation kind.

**Why a mode rather than frame-grabs:** a headless run takes seconds, needs no audio, pet or
recorder, and produces deterministic full-resolution stills. Extracting from a 30 fps recording gives
compression artifacts and the wrong moment.

**What renders these:** the executor (§5) and the annotation layer (§5.5) *only* — the main elements.
No TTS, no pet, no recorder. Stills mode is video mode with three subsystems off, which is a good
sign the layering is right.

**Where they go:** referenced from the companion blog post. This closes a real gap — the blog's
[`AI_CONTENT_INVENTORY.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/docs/AI_CONTENT_INVENTORY.md)
has an "Images and video (not started)" section stating no AI-generated images or video exist yet,
with columns deliberately not added until the work starts. This is that work.

---

## 12. Implementation map

Nothing here is proposed for *this* PR.

| Area | Change | New or reuse |
|---|---|---|
| `profiles/` (repo root) | Registry: `nova.yaml`, 3 account files, 20 profile configs | New — mostly content |
| `modules/content-creation/walkthrough/` | Schema, lint, executor, recorder, overlay, stills | New |
| `modules/content-creation/reactive/` | Cue schema, rights gate, ffmpeg composer | New |
| `modules/marketing-crosswalk/` | `walkthrough-script.md.tmpl` + `walkthrough` subcommand | **Reuse** |
| `modules/character-avatar/stream_avatar/runtime.py` | Second `AvatarAdapter` → overlay | **Reuse** — Protocol exists |
| `configs/local/stream-speech.yaml` | Provider-backed voice entries per account | **Reuse** — extend schema |
| `configs/local/stream-autopilot.yaml` | Optional persona-ID rename (§7.6) | Cleanup |
| `apps/shared/recording-library` | `RecordingOrigin::Walkthrough`, `::ReactiveCommentary` | **Reuse** |
| Creator Extend publishing | **Account router** (§1.6) | Modify |
| `modules/social-management/catalog.yaml` | Live-capable Reactions profile | Modify — **Q6** |
| `modules/character-avatar/`, `modules/broadcast-graphics/` | **None for gameplay-render** | Cited, not respec'd |
| Stream Extend | **None** | Not involved |

Module-doc obligations if accepted: `setup/manual.md`, `setup/automated.md`, labels, and rows in
`CLAUDE.md` §4 and §11, `modules/README.md`, and both `docs/agent/` matrices — per
[`CLAUDE.md`](../../CLAUDE.md) §4.

---

## 13. Boundaries

- Output lands in the recording inbox and **stops**. No autonomous publishing.
- The executor never runs against production (§5.3).
- Page content is data, never control flow (§5.3).
- A profile cannot relax a theme's content rules (§1.4) or the rights gate (§6.2).
- No voice cloning of any real person named as a style reference (§7.3).
- v1 mouth-sync is talk/idle, not visemes (§8).
- `gameplay-render` profiles are registered but their pipeline is untouched.
- A recording whose profile has no `account_binding` is refused, not defaulted (§1.6).

---

## 14. Open questions

| # | Question | Why it blocks | Default if unanswered |
|---|---|---|---|
| **Q1** | **Pet character — name, species, design, emote sheet?** **Question:** Which character should the pet be — its name, species, look and emote set? | Blocks every recording; most visible single decision | None. Needs the owner |
| **Q2** | **One pet across all profiles, or per-account pets?** And does the sprite pet coexist with `avatar_id: nova-vrm`, or replace it? **Question:** Use one pet across all profiles, varied by emote set, with the sprite pet and the VRM avatar kept side by side? | Asset volume, and whether Nova has two visual forms | **One pet, varied emote sets.** A recurring character builds recognition. Sprite and VRM coexist — different modes |
| **Q3** | **Is `opentech-operator` one profile with theme tags, or four?** **Question:** Keep the OpenTech operator as one profile with the four blog themes as tags, rather than four profiles? | Registry size | **One** (§1.4). Split later without a schema change |
| **Q4** | **Confirm the three account voice bindings** after the §7.5 side-by-side **Question:** After the side-by-side listen, keep Adam for Games, Diego for Reactions and Dave for OpenTechnology? | Blocks all narration | Adam / Diego / Dave as listed |
| **Q5** | **ElevenLabs account and budget?** **Question:** After checking ElevenLabs' current prices, will you open an account and set a budget, starting with pre-built voices? | Blocks §7 | Pre-built voices; owner clone deferred to v2 |
| **Q6** | **Add a live-capable Reactions profile to `catalog.yaml`?** It has none (§1.6) **Question:** Add a live-capable Reactions profile to the catalog? | Blocks Run 2's publish path, not its render | Add it — a compiled-catalog change with its own queue row |
| **Q7** | **Flight Simulator — register a 14th game profile, or drop it?** Marked experimental, adapter not built **Question:** Register Flight Simulator as a fourteenth game profile, even though its adapter is not built? | Registry completeness | Register it. It costs one config file and keeps the catalog honest |
| **Q8** | **Rename `rook-tactician` / `lux-commentator` / `ember-storyteller` to `nova-*`?** (§7.6) **Question:** Rename rook-tactician, lux-commentator and ember-storyteller to nova-prefixed names? | Nothing. Pure clarity | Rename with the registry |
| **Q9** | ~~Does the blog admin have stable `data-testid` attributes?~~ **Premise false — verified 2026-10-04: OpenTechnologyBlog has no admin UI, and zero `data-testid` attributes in `src/` or `e2e/` on `main`.** A post is an MDX file published by merging a PR | Run 1's target is not a UI flow — see [CT-D09](../todo/CONTENT_CREATE_TODO.md) | Replaced by CT-D09; no default |
| **Q10** | **Recording target: localhost or a dedicated staging deploy?** **Question:** Record walkthroughs against localhost rather than a dedicated staging deployment? | Allowlist and fixtures | **Localhost.** No hosting cost, no credentials, fully offline |

---

## 15. Cross-links

**This repository**

- [`configs/local/stream-programming.yaml`](../../configs/local/stream-programming.yaml) — show catalog, existing profile block
- [`configs/local/stream-autopilot.yaml`](../../configs/local/stream-autopilot.yaml) — `main_personality`, 16 personas
- [`configs/local/stream-speech.yaml`](../../configs/local/stream-speech.yaml) — voice bindings (§7)
- [`STREAM_AUTOPILOT_SHOW_BIBLE.md`](STREAM_AUTOPILOT_SHOW_BIBLE.md) — Nova's identity, delivery registers, show catalog
- [`PROPOSAL_STREAM_AUTOPILOT.md`](PROPOSAL_STREAM_AUTOPILOT.md) — P-056 parent
- [`modules/character-avatar/`](../../modules/character-avatar/) · [`stream_avatar/`](../../modules/character-avatar/stream_avatar/) — mouth-sync substrate (§8)
- [`modules/marketing-crosswalk/`](../../modules/marketing-crosswalk/) · [`stream-runofshow.md.tmpl`](../../modules/marketing-crosswalk/templates/stream-runofshow.md.tmpl) — draft generation (§10)
- [`modules/broadcast-graphics/`](../../modules/broadcast-graphics/) — not reused for walkthrough (§5.5); remains correct for gameplay
- [`modules/social-management/catalog.yaml`](../../modules/social-management/catalog.yaml) — account destinations (§1.6)
- [`apps/shared/recording-library/`](../../apps/shared/recording-library/) — inbox handoff
- [`docs/learning/`](../learning/README.md) — P-064 AI Learning Series
- [`PROPOSAL_AI_LEARNING_SERIES.md`](PROPOSAL_AI_LEARNING_SERIES.md) · [`PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md`](PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md)
- [`STREAM_EXTEND_PRODUCTION_SETUP.md`](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) · [`CREATOR_EXTEND_PRODUCTION_SETUP.md`](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) — three-account setup and the review gate

**OpenTechnologyBlog**

- [`docs/CONTENT_THEMES.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/docs/CONTENT_THEMES.md) — the four themes (§1.4)
- [`docs/AI_CONTENT_INVENTORY.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/docs/AI_CONTENT_INVENTORY.md) — output log; the empty images/video section (§11)
- [`course/scripts/module-01.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/course/scripts/module-01.md) — the format's direct ancestor (§4)
- [`proposals/2026-08-23-ai-content-creation-module.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/proposals/2026-08-23-ai-content-creation-module.md) · [`2026-09-01-dummies-content-module.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/proposals/2026-09-01-dummies-content-module.md) · [`2026-08-26-livestream-working-sessions.md`](https://github.com/OpenTechnology14/OpenTechnologyBlog/blob/main/proposals/2026-08-26-livestream-working-sessions.md)

**OpenTechnologyApp**

- [`docs/readable/BLOG_MARKETING_CONNECTION.md`](https://github.com/OpenTechnology14/Task-Management/blob/main/docs/readable/BLOG_MARKETING_CONNECTION.md) · [`TEMPLATE_REPO_CROSSWALK.md`](https://github.com/OpenTechnology14/Task-Management/blob/main/docs/readable/TEMPLATE_REPO_CROSSWALK.md)

---

## 16. Acceptance limits

This is a specification and proves nothing. No code exists, no profile directory has been created,
no walkthrough recorded, no pet drawn, no voice chosen or auditioned.

The reuse and inventory claims in §1, §3 and §7.6 are read from the files cited and are accurate as
of `2026-09-22`. The design arguments in §4–§11 are arguments, not results.

Three claims need live evidence before anyone relies on them: that the injected overlay survives the
blog admin's real navigation and scroll behavior (§5.5); that the existing `AvatarAdapter` contract
accepts a non-VTS implementation unmodified (§8); and that the three account voices remain
recognizably one character across a switch (§7.5). All three are plausible from the code and the
config. None has been run.
