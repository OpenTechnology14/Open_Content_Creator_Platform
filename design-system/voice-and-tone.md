# Voice and tone

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory.** Labels (Verified, Sourced, Proposed, Blocked) are defined in the
> [README](README.md#evidence-labels).

## Registers, not names

Voice in this ecosystem is described as a **register**: a set of descriptors for pace, energy, warmth and delivery. It is
never described by naming a real person, and no file in this folder does.

The owner once cited real people as inspiration when choosing voices. `docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md`
§7.3 turns that into a hard guardrail, and this hub inherits it:

- Choose **pre-built voices matched to the register**, never clones of a real person. Cloning anyone's voice without written
  consent breaks provider terms and creates right-of-publicity exposure.
- The people named as references are **selection references only**. Their names never appear in a prompt, a voice name, a
  config comment or marketing copy, and that includes every file in this folder and every consumer's pointer doc.
- A distinctive OpenTechnology voice comes from the owner's own voice (a recommendation, `P-068`), not from approximating
  anyone.

| Write this | Not this |
|---|---|
| "Deep, warm, measured; short sentences; a pause before a key claim." | A person's name, "sound like", "in the style of", "do an impression of" |
| "Young, energetic, expressive; quick payoffs; plain words." | A prompt that asks a model to impersonate a named creator |
| "A natively accented voice speaking English." | An accent applied as an overlay on a neutral voice (it reads as an impression; a native accent reads as a person) |

## The three registers

One on-air identity, **Nova**. Each account has its own register while the character, name and avatar stay fixed. The owner
selected this on 2026-09-22 (P-067 §7.2: three Nova variants sharing one core identity). The account split is fixed by
`docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §3.0.

| Register | Descriptors | Account and profiles (Sourced) | Audio policy (Sourced) |
|---|---|---|---|
| **Games** | young, energetic, expressive | Games account: Main Stream (`stream-main`), Agent Game Labs (`agent-labs`), every game session | `gaming-reactive`: approved short reaction clips for mapped game events, AI voice for chat and commentary |
| **Reactions** | young, energetic, Latin-accented | Reactions account: the `video-review` profile, whose shows are Try Not to Laugh Review and Nova Reviews the Edit | `review-scripted`: operator-approved commentary through the AI voice, Soundboard off |
| **OpenTechnology family** | deep, warm, measured, narrative | OpenTechnology account: `opentech-marketing` and the six marketing show profiles; Blog walkthroughs, the Build Brief, Workflow Clinic and other app and blog-side content | `opentech-scripted`, or `technical-scripted` for `ai-learning` and `ai-control-layer`: approved script segments through the AI voice, Soundboard off |

The audio policy is separate from the register and from who controls the game; one path per utterance, never both
(`docs/architecture/stream-personality-audio-routing.md`).

**Status of the voices themselves.** The per-account provider voices are *proposed* starting bindings in P-067 §7.3
(`Pending`). P-068 recommends moving only the OpenTechnology account to a local clone of the owner's own voice
(decisions D1 to D3 are open, and no local engine is installed). The shipped speech configuration is the operating-system
default voice (`voices: {nova-local: null}` in `configs/local/stream-speech.yaml`). Describe the registers; do not describe
the bindings as built.

## Nova's core character (Sourced)

Common to every register (`docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md`):

- A curious, warm experimenter with dry humor and clear explanations, willing to laugh at a failed plan.
- Never mocks a viewer's ability. Never invents having seen a game event.
- Game variations change **vocabulary and delivery energy**, not the character. Who is pressing the controls (a human or an
  agent, a console or a PC) never selects the personality.
- Runtime prompts use **original descriptions** of delivery; they never ask a model to impersonate a named creator.

## Energy by game (Sourced)

Editorial hypotheses from the show bible, not audience facts.

| Delivery | Games |
|---|---|
| High expressive energy | Fortnite, Roblox, GTA V, Among Us |
| Balanced | Minecraft, League of Legends, Valorant, Overwatch |
| Measured | Dota 2, CS2, World of Warcraft, Escape from Tarkov |

All variants avoid repetitive all-caps, prolonged shouting, manufactured rage and invented game moments. Humor targets Nova's
predictions and the situation. Audience prompts are occasional and never pressure anyone to spend, spam or share personal
information.

## Review commentary (Sourced)

Commentary targets the work and the editing choices, never the person in the video, and rights are confirmed before any clip
airs (`docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §6.2; the show bible's rule for video review).

## Written voice

**Marketing copy (Sourced).** Lead with the problem the reader already has, and let every claim stand on what the repository can
evidence; never promise ahead of `status` (`MARKETING.md`, status rule). Claims follow status, not ambition.

**Documentation (Sourced).** Plain, evidence-first, and blunt about what is not shipped. The production-setup guides mark every
step SHIPPED, EXTERNAL ACCEPTANCE or NOT SHIPPED and say which parts exist as code
(`docs/guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md`).

**Product UI copy.**
- *Games register* (Verified as a consumer-local draft): Ironfall's pointer, drafted on a local branch and not on its
  remote as of 2026-10-21, asks for direct, kinetic copy with concrete nouns, and brief actionable errors. It also says this register does not
  apply to documentation, commit messages or pull-request descriptions.
- *OpenTechnology family*: **Proposed** — measured, plain and concrete, matching the register's descriptors. The Blog's pointer
  already says the Blog inherits this register (`OpenTechnologyBlog:docs/design/DESIGN-SYSTEM-POINTER.md`). No source defines the
  App's or MyFeed's UI copy tone.
- *Reactions register*: **Proposed** for UI copy; its on-air rule (the work, not the person) is Sourced above.

## Per-profile guide

| Profile or surface | Register | What is Sourced | What is open |
|---|---|---|---|
| `stream-main`, `agent-labs` (Games) | Games | account, audio policy, energy by game | the bound voice (P-067, P-068) |
| `video-review` (Reactions) | Reactions | account, `review-scripted`, the work-not-the-person rule | the Latin-accented voice binding |
| `opentech-marketing` and the six marketing profiles | OpenTechnology family | account, audio policy, one module per profile | the narrator voice decision (P-068 D1 to D3) |
| `content-main` | Blocked | — | no source assigns it a register |
| Ironfall | Games (per its draft pointer) | — | confirm; D-8 |
| OpenTechnologyBlog | OpenTechnology family (per its pointer) | — | — |
| OpenTechnologyApp, MyFeed, Job Hunter, AnimalHouse | Blocked | — | no source assigns a register |

## Where consumers record divergence

A consumer's pointer doc names the register it sits in and any place its copy differs, with the reason. It does not restate the
descriptors. See [`crosswalk/consumers.md`](crosswalk/consumers.md).
