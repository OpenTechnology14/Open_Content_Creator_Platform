---
name: design
description: Design intent for the Open Content Creator Platform - local-first philosophy, the Stream Extend / Creator Extend split, the single Nova identity and its per-account voice registers (games, reactions, OpenTechnology), audio-policy classes, the persona to show profile to crosswalk module to social account chain, the Stream/Creator Extend app profiles, and the marketing-module parity pattern across the three repositories. Use before designing or changing a persona, show, voice, profile, marketing module, or how a product presents itself.
when_to_use: "Examples: 'add a persona or show profile', 'which voice register does this use?', 'how do Stream Extend and Creator Extend differ?', 'set up marketing-module parity', 'what is the audio policy for this show?'."
---

# Design

Design here is **constrained by what is evidenced**. Every claim below names its source; `docs/AUDIT.md` is the
repository's verdict on what is real, and `CLAUDE.md` §11 is per-module maturity (most modules are `scaffolded`).
Label anything you design as **Proposed** until it is built and verified.

**Register first.** Before you start, register the task with its one Kind (`CLAUDE.md` section 17, the entry gate); designing is not approval to build.

## Intent (`CLAUDE.md` §1-2)

Local-first, cloud-augmented, **stability before AI**. Latency-sensitive work (OBS, webcam, realtime inference,
overlays) stays on the creator's GPU. Cloud is opt-in for scaling, dashboards and burst compute. Modules are
independent, per-environment differences live in `configs/`, and `docs/architecture/roadmap.md` is the source of truth.

Two products come from one codebase: **Stream Extend** (modules labelled `Stream`) and **Creator Extend** (labelled
`Content`; it ships as ContentExtend and `apps/creator-extend` is the legacy internal name - the naming is unsettled
and blocks publication, see `docs/REPOSITORY_ALIGNMENT.md`). Shared foundations carry both labels.

## The design-system hub

Visual tokens, component specs, iconography, accessibility and the **canonical voice registers** live in `design-system/` (this repo is
the hub; other repos keep pointer docs). Read `design-system/README.md` first. Everything in it is `drafted`, awaiting owner review:
adopt a token only once it is `approved`, and never copy a value into another document - name the role and point there.

## One on-air identity: Nova

A "personality" in this repo is a Nova **persona**: a mode with its own system prompt, catchphrases and audio policy.
The same name, voice and avatar persist across games and human/agent handoffs
(`docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md`).

- Core character: a curious, warm experimenter with dry humor and clear explanations who laughs at a failed plan. Nova
  never mocks a viewer's ability and never invents a game event it was not given.
- Game variations change **vocabulary and delivery energy**, not the character. Who is pressing the controls (human or
  agent, console or PC) never selects the personality.
- Runtime prompts use **original descriptions** of the delivery. They never ask a model to impersonate a named creator.
- Energy bands are editorial hypotheses, not audience facts: *high expressive* (Fortnite, Roblox, GTA V, Among Us),
  *balanced* (Minecraft, League of Legends, Valorant, Overwatch), *measured* (Dota 2, CS2, World of Warcraft, Escape from
  Tarkov). Avoid repetitive all-caps, prolonged shouting, manufactured rage and invented moments. Humor targets Nova's
  own predictions and the situation. Audience prompts are occasional, never pressure to spend, spam or share personal data.

## Voice registers per account (Option B)

`design-system/voice-and-tone.md` is canonical for the registers; this section summarises it.

The owner selected **Option B** on 2026-09-22: three Nova variants sharing one core identity, one voice register per
account. The accounts are fixed by `docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §3.0.

| Account | Carries | Register (describe it this way) |
|---|---|---|
| **Games** | all game content | young, energetic, expressive |
| **Reactions** | Try Not to Laugh; Nova Reviews the Edit | young, energetic, **Latin-accented** - prefer a natively accented voice speaking English over an accent overlay on a neutral voice |
| **OpenTechnology** | Blog walkthroughs, Build Brief, Workflow Clinic, app and blog-side content | deep, warm, measured, narrative |

**Status, so you do not overclaim:** the bindings to specific provider voices are *proposed starting bindings* in
`docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md` §7.3 (`P-067` is `Pending`). `P-068` recommends moving only the
OpenTechnology account to a local clone of **the owner's own voice** and keeping Games and Reactions on pre-built voices
(owner decisions D1-D3 still open; no local engine installed). Shipped config is `voices: {nova-local: null}` in
`configs/local/stream-speech.yaml` - the operating-system default voice. Check those files before saying anything else.

**Hard guardrail (P-067 §7.3).** Choose **pre-built voices matched to the register, never clones of real people**. Cloning
anyone's voice without written consent breaks provider terms and creates right-of-publicity exposure. The real people the
owner named as inspiration are *selection references only*; their names must never appear in a prompt, a voice name, a config
comment or marketing copy - which includes this skill, `CLAUDE.md`/`AGENTS.md` and `docs/design/BUILD-PROMPTING-DIGEST.md`.
Describe the register; point to §7.3 and the show bible for provenance. A distinctive OpenTechnology voice comes from the
owner's own voice, not from approximating anyone.

## Audio policy: one path per utterance (`docs/architecture/stream-personality-audio-routing.md`)

| Class | Examples | Output | Soundboard |
|---|---|---|---|
| `gaming-reactive` | Nova's game variations | approved short reaction clips; AI voice for chat and commentary | on, for mapped events |
| `opentech-scripted` | `nova-opentech`, `nova-stream-extend`, `nova-content-extend`, `nova-chatbot-routing` | approved script segments on the AI voice bus | off |
| `technical-scripted` | `nova-ai-learning`, `nova-ai-control` | same | off |
| `review-scripted` | `nova-reviewer` (VideoReview) | operator-approved commentary | off |

The same phrase never goes to both paths. The class is separate from voice identity and from who controls the game. The
planner rejects a marketing profile declaring `gaming-reactive`. Review commentary targets the work and editing choices,
never the person in the video, and rights are confirmed before any clip airs.

## The chain, and what a new marketing module forces

```text
persona (configs/local/stream-autopilot.yaml)
  -> show profile (configs/local/stream-programming.yaml)    audio_policy must match the persona
       -> crosswalk module (modules.yml)                     one profile per GENERATING module
            -> target (targets.yml)
       -> social account (modules/social-management/catalog.yaml)   exactly one owner per show profile
```

Six modules generate and have a profile: `task-management` (`opentech-marketing`), `stream-extend`, `content-extend`,
`ai-learning`, `ai-control-layer`, `chatbot-routing` (`marketing-<module>`). Adding one means: registry row (proposal first),
persona with a scripted `audio_policy`, `kind: marketing` profile, exactly one account route, and **not** adding it to
`reaction_sounds`. `tests/automation_control/test_personality_bindings.py` fails until all of them agree. Discovery-only rows
have no persona, profile or account until promoted, and a `visibility: private` row must never have one.

## App profiles (workspaces)

A profile is a brand, provider, capability and connected account remembered as a set (`modules/social-management/catalog.yaml`:
`stream-main`, `content-main`, `opentech-marketing` (hybrid), `video-review`, `agent-labs`). Stream Extend's switcher shows
`stream` and `hybrid` profiles; Creator Extend's shows `content` and `hybrid`. Routing memory is **per profile**. The catalog is
compiled into the Tauri plugin, so adding a profile is a code change with a queue row. A profile changes routing, not your
behaviour: hold the **strictest common standard** across every session under it (Roblox assumes minors).

## Marketing-module parity across the three repositories

1. **The registry is canonical in this repo.** A marketing "module" is a registry row plus a subjects file. OpenTechnologyApp
   has no marketing module directory; its module is the `task-management` row.
2. **Each target keeps its own playbook** (`MARKETING.md`) with the same section numbering and its own audiences, claims and
   evidence. A playbook is a registered crosswalk doc, not a floating file.
3. **Sibling repos hold pointers, not copies.** Use the `docs` skill for how.
4. **Duplication is allowed only when a test verifies it** (`tests/marketing_crosswalk/test_playbook.py`).
5. **Claims follow `status`.** Do not promise ahead of the evidence.

## Do not

Add a second identity or a new top-level marketing module; route realtime webcam or OBS traffic through the cloud; expose a
service without an auth layer; present a proposed binding, voice or show as shipped.

## Sources

`CLAUDE.md` §1-2, §11 - `docs/architecture/stream-personality-audio-routing.md` - `docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md`
- `docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md` §7 - `docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md` §3 -
`docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §3, §6 - `MARKETING.md` §3g - `configs/local/*.yaml` -
`design-system/README.md`.
