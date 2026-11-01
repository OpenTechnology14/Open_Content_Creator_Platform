# Content create — decisions and to-do

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**Enforcement: reference.** Row format, IDs, states and the intake rule are in the
[lane index](README.md). Every row names its canonical proposal; **the proposal wins** when the two
disagree. Nothing here authorizes work — [`../PROPOSALS.md`](../PROPOSALS.md) does.

**Scope.** Owner decisions and runs about **producing non-live content**: narration and voice, the
pet, walkthrough and reactive clips, clips and thumbnails, publishing, the AI Learning Series,
marketing drafts and the generation modules. Anything that needs OBS, a live account or capture
hardware is in the [stream lane](STREAM_DECISIONS_AND_TODO.md). *Build* work — the walkthrough
engine, the reactive composer, the `provider: local` TTS branch — lives in each proposal's delivery
plan, not here. This lane holds what only a person can do or decide.

## Next three

Ordered by what unblocks the most, counting only what can start today.

1. **CT-R01 — run the content chain once.** It needs no stream, no pet and no unbuilt code, and it
   is the first time the content half of the recording handoff would be exercised end to end.
2. **CT-D09 — choose a target for the first walkthrough.** The one P-067 names does not exist as a UI
   flow (verified 2026-10-04: the blog has no admin). Until this is answered, the walkthrough engine
   has no first customer.
3. **CT-D01 — pick the pet.** The only open decision with no default, and it gates every walkthrough
   and reactive recording. Cheap voice work (CT-D03 → CT-R02) can run beside it.

## Awaiting acceptance

Queue rows in state `Pending`. Per [`../PROPOSALS.md`](../PROPOSALS.md), `Pending` means *raise it for
acceptance; do not start* — so each of these is one yes, amend or defer from the owner. The
decisions below it are what acceptance turns on.

| ID | Proposal | What accepting it settles | If accepted as written | State |
|---|---|---|---|---|
| CT-A01 | [P-067](../proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) Nova profile registry, walkthrough engine and mascot system | The registry model (one base character, ~20 profiles), three execution modes, the account router and voice Option B **Question:** Accept the Nova profile, walkthrough and mascot proposal as written, with the pet and the first walkthrough still to be chosen? | The defaults in its §14 apply to CT-D02, CT-D03, CT-D07, CT-D08, CT-D10 and ST-D16/ST-D17. **CT-D01 has no default, and CT-D09 needs a new answer first** | open |
| CT-A02 | [P-068](../proposals/PROPOSAL_LOCAL_TTS_STACK.md) Local TTS stack for Nova | The hybrid strategy and its test plan **Question:** Accept the plan to clone your own voice locally for OpenTechnology and keep ElevenLabs for the other two, starting with a prototype? | Hybrid; prototype first (CT-D04–CT-D06) | open |
| CT-A03 | [P-004](../proposals/PROPOSAL_CONTENT_ASSET_GENERATION.md) Content asset generation (text-to-image) | A committed text-to-image workflow with recorded load-test evidence before merge; a hard non-goal of any remote endpoint **Question:** Accept one committed text-to-image workflow, merged only after recorded load tests pass and never exposed as a remote endpoint? | SDXL base (CT-D14) | open |
| CT-A04 | [P-059](../proposals/PROPOSAL_NATURE_GENERATION_TIERS.md) Nature generation learned tiers | Learned landscape generation above the finished Tier 0 grading CLI **Question:** Accept the nature learned-tiers proposal now, knowing it stalls until you supply a rights-cleared image corpus? | Stalls on CT-D15 — there is no rights-cleared corpus yet | open |
| CT-A05 | [P-060](../proposals/PROPOSAL_CITYSCAPE_GENERATION_TIERS.md) Cityscape generation learned tiers | The same for urban generation **Question:** Accept the cityscape learned-tiers proposal now, knowing it stalls until you supply rights-cleared corpora and settle the model and GPU choices? | Stalls on CT-D15 and CT-D16 | open |

## Decisions

Columns: **Blocks** is what cannot proceed; **Default** is what applies if nobody answers.

### The pet

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| CT-D01 | **Pet character** — name, species, visual design, emote sheet **Question:** Which character should the pet be — its name, species, look and emote set? | P-067 §14 Q1; §8 | Every walkthrough and reactive recording; CT-R05 | **None — needs you** | open |
| CT-D07 | One pet across all profiles, or per-account pets? Does the sprite pet coexist with `avatar_id: nova-vrm`, or replace it? **Question:** Use one pet across all profiles, varied by emote set, with the sprite pet and the VRM avatar kept side by side? | P-067 §14 Q2 | Asset volume, and whether Nova has two visual forms | One pet, varied emote sets. Sprite and VRM coexist — VRM for gameplay, sprite for walkthrough and reactive | open |

### Voice and narration

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| CT-D03 | ElevenLabs account and budget **Question:** After checking ElevenLabs' current prices, will you open an account and set a budget, starting with pre-built voices? | P-067 §14 Q5; P-068 §1.1 | CT-R02 and all narration | Pre-built voices; the owner clone is deferred to v2. **The $99 Pro / $22 Creator figures in P-068 are owner-supplied and unverified — check ElevenLabs' pricing page before deciding** | open |
| CT-D02 | Confirm the three account voice bindings after the side-by-side: Games → Adam, Reactions → Diego, OpenTechnology → Dave **Question:** After the side-by-side listen, keep Adam for Games, Diego for Reactions and Dave for OpenTechnology? | P-067 §14 Q4; §7.3, §7.5 | All narration | Adam / Diego / Dave | blocked by CT-R02 |
| CT-D04 | Hybrid TTS — OpenTechnology on a local clone of your own voice, Games and Reactions on ElevenLabs — or fully local? **Question:** Go hybrid — your own cloned voice locally for OpenTechnology, ElevenLabs for Games and Reactions — rather than fully local? | P-068 D1 | Everything in P-068 | Hybrid. Fully local means voice-acting three registers, which is a performance problem, not a software one | open |
| CT-D05 | Will you record 3–10 minutes of clean voice sample as the clone source? **Question:** Will you record 3–10 minutes of clean voice sample to clone from? | P-068 D2 | The OpenTechnology local voice, entirely | Yes, if CT-D04 is hybrid or fully local | open |
| CT-D06 | Prototype (about half a day) or production-ready (about a day plus fine-tuning)? **Question:** Build a prototype first, about half a day, rather than going straight to production-ready? | P-068 D3 | The scope of P-068 §5 | Prototype first; decide on production only after the A/B | open |

### First walkthrough and reactive runs

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| CT-D09 | **What does the first walkthrough record?** P-067's Run 1 is "Publish your first post" on OpenTechnologyBlog through an admin flow. **Verified 2026-10-04: no admin, login, editor or CMS route exists on the blog's `main`, and none of its proposals or docs plans one (searched 2026-10-04). There are zero `data-testid` attributes in its `src/` and `e2e/`.** A post is an MDX file in `content/blog/`, published by merging a PR. Options: **(a)** a public-site flow with no sign-in — for example reading a lesson and following its learning hub; **(b)** an OpenTechnologyApp Admin Panel flow — a separate product, which the owner descoped on 2026-09-22; **(c)** the GitHub pull-request publish flow — a third-party site, fragile to select; **(d)** hold the walkthrough engine until a blog authoring UI exists **Question:** Make the first walkthrough a public-site flow that needs no sign-in, such as reading a lesson? | P-067 §14 Q9 (premise false), §9 Run 1 | CT-R06; the walkthrough engine's first target | None. (a) is the smallest and keeps the blog-only scope | open — new |
| CT-D08 | `opentech-operator`: one profile with the four blog themes as content-lens tags, or four profiles? **Question:** Keep the OpenTech operator as one profile with the four blog themes as tags, rather than four profiles? | P-067 §14 Q3; §1.4 | Registry size | One; split later without a schema change | open |
| CT-D10 | Recording target: localhost, or a dedicated staging deploy? **Question:** Record walkthroughs against localhost rather than a dedicated staging deployment? | P-067 §14 Q10 | The allowlist and fixtures | Localhost — no hosting cost, no credentials, fully offline. Moot until CT-D09 is answered | open |

### Series and publishing

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| CT-D19 | **AI content publishing.** **Question:** After concept approval, review the finished video or allow automatic publishing under a separate policy? | [P-062 §14](../proposals/PROPOSAL_SOCIAL_MANAGEMENT.md#14-channel-portfolio-and-agentworkflows-controls--2026-10-31) | Automatic publishing policy only; local queue and concept approval can proceed | Preserve existing final approval gate; silence grants nothing | open |
| CT-D11 | Validate the AI Learning Series audiences — they are derived from lesson topics, not measured demand **Question:** Do you accept the AI Learning Series audiences, which come from lesson topics and not measured demand, before lesson 1 airs? | P-064 §12 | Publishing lesson 1; ST-R09 | None stated; due *before lesson 1 airs* | open |
| CT-D12 | **Creator Extend or ContentExtend** — which name may published copy use? **Question:** Which name should published copy use: Creator Extend or ContentExtend? | P-064 §12; P-023 (Deferred); [`../REPOSITORY_ALIGNMENT.md`](../REPOSITORY_ALIGNMENT.md) | Naming either product in any published copy, including a lesson's run of show | Both are preserved; nothing is named publicly until it resolves | open — needs re-acceptance, P-023 is Deferred |
| CT-D13 | Lesson status vocabulary — the products' `scaffolded`…`shipped` set reads oddly for a lesson **Question:** Keep the products' status words for lessons for now, and defer a lesson-specific set? | P-064 §12 | Nothing | Accept for now; a lesson status set is a later change | open — low |

### Generation modules — these apply once the matching proposal is accepted

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| CT-D14 | Text-to-image checkpoint: SDXL base, or a fine-tune? Record its licence beside its `models.md` entry before first public use **Question:** Use the SDXL base checkpoint for text-to-image rather than a fine-tune? | P-004 §12 | P-004 Phase 1; the first public use of a generated image | SDXL base | open — after CT-A03 |
| CT-D15 | Rights-cleared corpora: nature, and day and night cityscape **Question:** Will you supply rights-cleared nature images and rights-cleared day and night cityscape images for training? | P-059 §12; P-060 §12 | All training, and any distributable adapter | None — you supply them; see [`../IMAGE_INTAKE.md`](../IMAGE_INTAKE.md) | open — after CT-A04/A05 |
| CT-D16 | Base checkpoint, IP-Adapter, SAM and depth nodes (nature); lineart and depth versions (cityscape); local GPU benchmark and target resolution **Question:** Will you run a local GPU benchmark, then confirm the model and node choices and the target resolution? | P-059 §12; P-060 §12 | GPU budget, output geometry, and whether batch cloud compute is justified | None | open — after CT-A04/A05 |
| CT-D17 | Blender jobs: a scene eligibility marker, or an explicit selection UI? **Question:** Should Blender jobs find eligible scenes through a marker on the scene, or through an explicit selection screen? | P-061 §12 | The stable job input | None | open |
| CT-D18 | Blender jobs: default upload policy and bucket **Question:** Should finished Blender renders upload to a bucket by default, and which one? | P-061 §12 | Storage cost and privacy | None | open |

## Runs

**Proof** uses the [lane index](README.md#row-format) vocabulary. Ordered by what unblocks the most.

| ID | Run | Proof | Needs | Source | State |
|---|---|---|---|---|---|
| CT-R01 | **Run the content chain once.** Record a 10-minute session, or import an existing recording with *Add existing recording*; confirm it is in the inbox; cut three 30–60 s clips with FFmpeg; generate one thumbnail through the committed ComfyUI workflow (preflight first); upload **one clip as Private** through Social; watch it on YouTube, including on a phone | **live** | Creator Extend built and readiness green; ComfyUI with SDXL; a YouTube OAuth client (`SOCIAL_YOUTUBE_CLIENT_ID` and `_SECRET`) and a channel you own | [Creator guide §8](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md#8-test-end-to-end); P-065; P-062 | **ready** |
| CT-R02 | **Voice audition.** Render the same real script text in Adam, Diego and Dave plus the `nova-local` incumbent, in blind order; then switch voice mid-clip and confirm Nova is still recognisably one character. The blind-order rig exists (`modules/audio-production/tts/audition.py`, P-068 slice 2: neutral shuffled takes, matched levels, a hidden key, a recorded ranking). The listening, the ElevenLabs renders (WAVs you export yourself) and the mid-clip switch are still yours, and the runbook is still unwritten (`FD-15`) | **manual** | CT-D03 | P-067 §7.5; P-068 §6.1 | blocked by CT-D03 |
| CT-R03 | **Record the voice sample**: 3–10 min, 48 kHz WAV, one sitting, varied real text — your own blog posts work well — in the register Nova should have. Check it afterwards with `modules/audio-production/tts/check_voice_sample.py` (P-068 slice 3): objective pass/fail on format, length, clipping, level, noise, edits and a lossy-source cutoff, while your ears still judge the room, register and content | **manual** | CT-D04, CT-D05 | P-068 §5.4 | blocked by CT-D05 |
| CT-R04 | **Local TTS prototype.** Install one engine (Chatterbox first, F5-TTS as the alternate); confirm `mps True`; clone; blind A/B against ElevenLabs and `nova-local`; p50 and p95 over 20 paragraphs (`python -m stream_speech --prerender` reports them, P-068 slice 4); the same line on three separate days; then the pipeline check — pet mouth-sync, inbox registration, account routing. That last check needs the `provider: local` branch, which slice 1 built on 2026-10-05 with no engine adapter, so it still cannot render until an engine slice lands | **live** | CT-R03, CT-D06 | P-068 §5–§6 | blocked by CT-R03 |
| CT-R05 | **Design the pet**: generate raster art in ComfyUI, assemble a sprite sheet and emote map in Krita | **manual** | CT-D01 | P-067 §8 | blocked by CT-D01 |
| CT-R06 | **Walkthrough prototype (Run 1).** Pass criterion: a 3–5 minute narrated recording, pet animated in time with speech, at least four structured annotations correctly anchored, registered in the inbox and routed to the OpenTechnology account | **live** | CT-D09; the walkthrough engine (not built); CT-R05; CT-D02 | P-067 §9 | blocked by CT-D09 |
| CT-R07 | **Reactive prototype (Run 2, Try Not to Laugh).** One supplied clip with a recorded rights confirmation; the rights gate must **block** a run that has none. The real acceptance criterion: a recognisably different result from Run 1 with no registry schema change | **live** | The reactive composer (not built); CT-R05; CT-D02; ST-D03 for the publish path; a rights record | P-067 §9, §6.2 | blocked |
| CT-R08 | **Three branding sets** — avatar, banner, panels, watermark and About copy for Games, Reactions and OpenTechnology: generate the raster in ComfyUI, assemble in Krita, upload by hand | **manual** | ST-D01 (the handles) | [Stream guide §3.6](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md#36-branding-artifacts--prepare-these-during-setup-not-after) | blocked by ST-D01 |
| CT-R09 | **After lesson 1 airs**: cut clips and stills, write the X thread and comment ammo; declare lesson-shaped Reddit and LinkedIn templates (P-064 Phase 4); flip `Aired` in [`../learning/README.md`](../learning/README.md) **and** the `ai-learning` subjects file together, then run `validate` | **manual**, then **auto** | ST-R09 | P-064 §10 phases 2 and 4 | blocked by ST-R09 |
| CT-R11 | **Marketing drafts per consumer**: `validate` → `coverage --module <id>` → `generate --module <id> --asset <asset> --dry-run` → review → `generate`; read the checklist each draft carries. Blocked claims and discovery-only consumers are expected boundaries — never use `--force` | **auto** and **manual** | CT-R10 for the two blog modules; otherwise a registered consumer with evidence-backed subjects | [Documentation workflow § Marketing drafts](../DOCUMENTATION_WORKFLOW.md#marketing-drafts-and-coverage) | ready for `stream-extend`, `content-extend`, `task-management` and `ai-learning` |
| CT-R12 | **Native Windows acceptance of creator workflow inputs** | **live** | ST-D07 | P-057 | blocked by ST-D07 |
| CT-R13 | **`realtime-ai`: GPU-run verification of the six missing ComfyUI workflows.** About 14 GB of model downloads — budget it as the session, not as setup. Real inference verification was never something an agent could do | **live** | A GPU host and the model downloads | P-028; [`models.md`](../../modules/realtime-ai/comfyui/models.md) | open — owner work |
| CT-R15 | **Recording to reviewed Shorts draft** with source/content profile preserved; beginner inbox → review/trim → verified MP4, not merely an editing-status change; baseline first, combined app repeat later | **live** | ST-R05 recording; ST-T16 for combined repeat; local Shorts pipeline and authorized desktop adapter | [P-072 §9 U-09 journey 1](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | open baseline; combined repeat blocked by build |
| CT-R16 | **Recording to Content profile to explicitly approved private publishing test**; inspect the actual destination account | **live** | CT-R01 baseline; ST-T16 recording for combined repeat; real provider sign-in and exact-job approval | [P-072 §9 U-09 journey 3](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | blocked by accounts/build; no publishing authorized by this index |
| CT-R17 | **Future companion availability and conflict test:** expired session, asleep desktop, reconnect and conflicting drafts | **live** | PL-D14; separately accepted C1/C2 proposal and hosted build | [P-072 §9 U-10](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | blocked — cloud candidate scope only |
| CT-R18 | **Future media review/backup acceptance:** interrupted upload, quota, wrong-tenant access, delete and restore with local original intact | **live** | PL-D14; separately accepted C2 proposal and private storage | [P-072 §9 U-11](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | blocked — cloud candidate scope only |
| CT-R19 | **Future cloud batch acceptance:** small real job with failure/cancel/retry, pinned models/inputs and a hard cost ceiling | **live** | PL-D14; separately accepted C3 proposal, single executor and budget | [P-072 §9 U-12](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#9-test-and-pressure-matrix) | blocked — cloud candidate scope only |

## Resolved

Newest first. A row stays here until it moves to a dated archive (see
[how this grows](README.md#how-this-grows)).

| Date | ID / source | Resolution | Recorded in |
|---|---|---|---|
| 2026-10-09 | CT-A06 — P-061 acceptance | **P-061 accepted for implementation.** The owner's 2026-10-08 direction to continue Sol- and Astra-assigned work, which includes pending development proposals, covered it (P-061 is assigned Sol); the queue moved it from Pending to In progress on 2026-10-09, and the bounded local still-job lifecycle is built. The row sat in *Awaiting acceptance* after that. Its two owner decisions, CT-D17 and CT-D18, stay open | [queue row](../PROPOSALS.md) (moved in `dd17563`); [P-061 status](../proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md); [owner continuation, 2026-10-08](../PROPOSALS.md#owner-continuation--sol-and-astra-work-2026-10-08) |
| 2026-10-08 | CT-R10 | The 17 source subjects are already present on the committed base; the older concurrent-edit warning is resolved. Current registry has 47 subjects and 13 asset formats | P-070; marketing registry |
| 2026-10-08 | CT-R14 | Four public written lesson previews returned HTTP 200 with matching article headings. Updated blog coverage and counts; no live lesson is marked aired | P-064; [series index](../learning/README.md) |
| 2026-10-04 | P-067 Q9 | Resolved by **evidence, not choice**: the blog has no admin UI and no `data-testid`s. Replaced by CT-D09 | P-067 §14 and §9 (correction notes added) |
| 2026-09-22 | P-067 §1 | Nova is **one** character; a profile is Nova-in-a-context; granularity is per game or concept, not per show (about 20 profiles); the four blog themes are content-lens tags on one `opentech-operator` profile unless the voice or pet genuinely shifts | P-067 §1 — owner message |
| 2026-09-22 | P-067 §7.2 | Voice **Option B** — three Nova variants sharing a core identity, one vibe-matched pre-built voice per account. **No voice of any real person named as a style reference is ever cloned**; the honest route to a distinctive voice is cloning the owner's own | P-067 §7 — owner message |
| 2026-09-22 | P-067 Non-goals | Walkthrough scope is **blog content only**; gaming walkthroughs are an explicit non-goal (character-avatar and Creator Extend already cover gameplay); Try Not to Laugh is a registered profile and the reactive-mode test | P-067 — owner message |
| 2026-09-20 | P-064 §12 | Blog target for the AI Learning Series is `opentechnology-blog` | P-064 §12 |

## Pointers to the other lane

Items owned here that also affect the live host's voice: **CT-D02, CT-D03**. Items this lane waits on:
ST-D01 (handles) → CT-R08 · ST-R09 (airing lesson 1) → CT-R09 · ST-D03 → CT-R07 · ST-D07 → CT-R12.
