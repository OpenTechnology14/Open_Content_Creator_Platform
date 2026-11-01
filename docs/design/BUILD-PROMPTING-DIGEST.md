# Build prompting digest

> **Status:** Reference · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory.** A prompt points an agent at the sources; it never overrides
> [`CLAUDE.md`](../../CLAUDE.md) / [`AGENTS.md`](../../AGENTS.md), the [proposal queue](../PROPOSALS.md) or the
> [verification matrix](../agent/VERIFICATION-MATRIX.md). Where this digest and those disagree, they win and this is the one to fix.

How to ask an agent — Claude Code, Codex, ChatGPT or any other — to extend this repository without it re-learning
the same lessons. Every block below is a prompt you can paste; every rule in it cites the document that owns the rule.

## 1. How to use it

The agent's reading order is fixed: **`AGENTS.md` (or `CLAUDE.md`, its source) → the skill that matches the task → the
owning proposal row → the verification matrix.** The skills are plain markdown under `.claude/skills/<name>/SKILL.md`;
Claude Code loads them natively, and any other tool reads the same files by path through the pointer in `CLAUDE.md` §14
(mirrored into `AGENTS.md`).

| The task is about | Skill |
|---|---|
| a new module, a check, native/process/credential code, the Blender job lifecycle, tests | [`code-creation`](../../.claude/skills/code-creation/SKILL.md) |
| the crosswalk registry, `MARKETING.md`, pointer docs, anything under `docs/` | [`docs`](../../.claude/skills/docs/SKILL.md) |
| personas, voices, show profiles, app profiles, marketing-module parity | [`design`](../../.claude/skills/design/SKILL.md) |
| coverage, untested or dead code, crosswalk completeness | [`audits`](../../.claude/skills/audits/SKILL.md) |
| secrets, `.env`, ports and auth, or a sensitive path (Tauri capabilities, the avatar module, credential configs, the shared crates) | [`security`](../../.claude/skills/security/SKILL.md) (not path-bound: open it yourself) |
| visual tokens, component rules, icons, contrast, or a consumer's pointer doc | the [design-system hub](../../design-system/README.md) (drafted; adopt only what is `approved`) |
| *which* marketing module a request belongs to | [`marketing-discovery`](../../.claude/skills/marketing-discovery/SKILL.md) |

A good prompt names the goal, the slice, the skill, the stop conditions and the report format. It does not restate the rules.

## 2. The standing preamble

Paste this first, then the task.

```text
You are extending the Open Content Creator Platform. Read AGENTS.md (or CLAUDE.md) first, then the skill under
.claude/skills/ that matches the task.
- Find the roadmap layer and the docs/PROPOSALS.md row that authorises this work. If there is none, stop and say so.
- Register the task with its one Kind before you start (CLAUDE.md section 17, the entry gate).
- Work in a separate git worktree off the branch I name. Do not touch uncommitted files you did not create.
- Do the smallest slice that can be verified. Anything not evidenced is Proposed; never write it as built.
- Look up docs/agent/VERIFICATION-MATRIX.md and run the row for what you changed.
- Do not push, open a PR, merge, or change account or CI settings unless this message says to.
```

## 3. Crosswalk discipline

The registry is one file for three repositories, and it refuses claims it cannot evidence. Prompt around that.

**Register a project or module so it can be found** (nothing is marketed):

```text
Register <project> in modules/marketing-crosswalk as a discovery-only row (skill: docs). Re-count its files from the real
folder and write the basis line (what, where, revision, date). Add discovery_keywords including spelling variants and
not_to_be_confused_with for every module that shares a word. Status comes from the mechanical rule in schema.md, not from me.
Do not create a persona, profile or subject. If the project must not be published, do not commit a row for it: a `visibility: private` row lives only in an uncommitted local copy of the registry.
```

Must run: `validate` **and** `selftest` **and** `ruff check modules/ scripts/`, plus `pytest tests/marketing_crosswalk tests/docs`.
Usual failure: a count copied from memory (the repo wins), or a private id named in a public row.

**Refresh counts or statuses**

```text
Re-derive the counts in the <module> row from the source its basis line names. Correct them, bump last_verified, and change
a status only together with its status_evidence. If a count disagrees with the repo, the repo is right.
```

**Promote a discovery-only row** — only after the owner decision in its `promotion.blocked_on` is resolved, and in the order of
`promotion.steps`. Promotion is also what forces a persona, show profile and one account route (section 4).

**Edit `MARKETING.md`** — headings are registered anchors, so a rename fails `validate`; every numbered section keeps its
`**Registry:**` line; after any ICP, persona or engine change run `tests/marketing_crosswalk/test_playbook.py`.

## 4. Marketing parity

```text
Add a marketing module for <name> (skill: design). First prove it should generate: a registry row plus a subjects file is the whole
module; do not create a new top-level directory. Then, in this order: persona with a scripted audio_policy, a kind: marketing
profile named marketing-<module>, exactly one account route in social-management, not in reaction_sounds. Run
tests/automation_control/test_personality_bindings.py until all five files agree. Update the playbook rows it repeats.
```

Sibling-repo pointers (OpenTechnologyApp, OpenTechnologyBlog) are separate pull requests in those repositories: they point at
the platform registry and are never a copy of it.

## 5. Voice guidelines per profile

One on-air identity, **Nova**. Option B (owner-selected 2026-09-22) gives each account its own *register* while the character,
name and avatar stay fixed. Registers are described, never impersonated. The canonical text is
[`design-system/voice-and-tone.md`](../../design-system/voice-and-tone.md); this section summarises it.

| Account / profile | Register to describe | Audio policy | Source |
|---|---|---|---|
| **Games** (Nova's game variations) | young, energetic, expressive; energy band per game (high expressive / balanced / measured) | `gaming-reactive` (Soundboard on for mapped events) | [show bible](../proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md) |
| **Reactions** (Try Not to Laugh, Nova Reviews the Edit) | young, energetic, Latin-accented — a natively accented voice, not an accent overlay; commentary targets the work, never the person | `review-scripted` (profile `video-review`, persona `nova-reviewer`; both shows run under it) | [P-067 §7](../proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md), [routing doc](../architecture/stream-personality-audio-routing.md) |
| **OpenTechnology** (the six marketing show profiles) | deep, warm, measured, narrative | `opentech-scripted`, or `technical-scripted` for `ai-learning` and `ai-control-layer` | [routing doc](../architecture/stream-personality-audio-routing.md) |

What is built versus proposed: the shipped speech config is the operating-system default voice (`voices: {nova-local: null}` in
`configs/local/stream-speech.yaml`). The per-account provider voices are proposed starting bindings (P-067, `Pending`), and a local
clone of the owner's own voice for the OpenTechnology account is a recommendation awaiting owner decisions (P-068).

Paste into any persona-writing prompt:

```text
Describe the delivery in original words: pace, energy, warmth, what the humor targets, what to avoid. Do not name a real person,
do not write "sound like" or "do an impression of", and do not propose cloning anyone's voice. Choose among pre-built voices by
register. Keep Nova's core character: curious, warm, dry humor, never mocks a viewer's ability, never invents a game event.
No repetitive all-caps, prolonged shouting or manufactured rage. Audience prompts are occasional and never ask for money, spam
or personal information.
```

**Why the names are absent:** the real creators the owner cited are *selection references only*. P-067 §7.3 forbids them in a
prompt, a voice name, a config comment or marketing copy, and forbids cloning any real person's voice without written consent.
Their provenance lives in that section and in the show bible; it is deliberately not repeated here.

## 6. Stream production setup lineage

Read the lineage to find which document owns a fact before you change it.

| Step | What it added | Read | State |
|---|---|---|---|
| Numbered guides 1–9 | OBS foundation through advanced infra | retired and **fully migrated**; [`docs/guides/README.md`](../guides/README.md) maps each guide to the module docs that absorbed it | no archive |
| Module setup docs | one manual and one automated doc per module, labelled `Content` / `Stream` | [`modules/README.md`](../../modules/README.md) (setup order) | `CLAUDE.md` §4 |
| Production setup, Stream Extend | clean checkout to a public gaming stream: accounts, games, profiles, dry run | [guide](../guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md) | markers: SHIPPED / EXTERNAL ACCEPTANCE / NOT SHIPPED |
| Production setup, Creator Extend | a Stream Extend recording to a published video | [guide](../guides/production-setup/CREATOR_EXTEND_PRODUCTION_SETUP.md) | same markers |
| Stream Autopilot (P-056) | the embodied host, show bible, game evaluation | [proposal](../proposals/PROPOSAL_STREAM_AUTOPILOT.md), [show bible](../proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md), [games](../proposals/STREAM_AUTOPILOT_GAME_EVALUATION.md) | queue: In progress |
| Reaction audio and scripted routing (P-066) | one audio path per utterance; the policy classes | [proposal](../proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md), [routing doc](../architecture/stream-personality-audio-routing.md) | queue: In progress |
| Nova registry and mascot system (P-067) | three-account voice model (Option B) | [proposal](../proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) | queue: Pending |
| Local TTS stack (P-068) | provider seam, audition rig, recording checker | [proposal](../proposals/PROPOSAL_LOCAL_TTS_STACK.md) | queue: Pending; no local engine installed |
| Social profiles (P-062), recording handoff and profile workspaces (P-065), in-app setup (P-063) | the app-level profiles, the Stream → Creator inbox, assisted setup | [P-062](../proposals/PROPOSAL_SOCIAL_MANAGEMENT.md), [P-065](../proposals/PROPOSAL_RECORDING_HANDOFF_AND_PROFILE_WORKSPACES.md), [P-063](../proposals/PROPOSAL_IN_APP_SETUP.md) | queue: In progress; external acceptance open |

The queue ([`docs/PROPOSALS.md`](../PROPOSALS.md)) is authoritative for state; the column above can go stale. Native hardware,
account and platform acceptance are separate from anything an agent can run headless.

## 7. Prompt anti-patterns (each breaks a rule that already exists)

| Do not prompt | Why |
|---|---|
| "Make CI green" / "skip the failing test" | `CLAUDE.md` §13: no fix-until-green; security contracts run with `no_skips` |
| "Mark it Done" / "call it shipped" | a queue row needs recorded verification; claims follow `status` |
| "Use a named real person's voice" | the P-067 §7.3 hard guardrail (section 5) |
| "Clean up the working tree" | preserve unrelated work; another session's uncommitted files are not yours |
| "Merge it" with no read of why CI failed | a billing block is not a verdict on the code, and merging is the owner's call (`.claude/commands/pre-merge.md`) |
| "Add a marketing module" with no registry check | a registry row is the module; use `marketing-discovery` first |
| "Add Kubernetes", "route the webcam through the cloud" | `CLAUDE.md` §2 and §10 |
| "Describe it as working" for a `scaffolded` module | the status gate; `docs/AUDIT.md` is the verdict on what is real |
| "Improve the docs" | name the file, the `DM-` rule it triggers and the check that proves it |

## 8. Close every task with this

```text
Before you stop, reply with: files changed; the VERIFICATION-MATRIX row you ran, the exact command and its result; every check
you did NOT run and why; what is Proposed versus built; and the decisions that are the owner's. Do not push or merge.
```

## Sources

[`CLAUDE.md`](../../CLAUDE.md) · [`docs/agent/VERIFICATION-MATRIX.md`](../agent/VERIFICATION-MATRIX.md) ·
[`docs/agent/DOC-UPDATE-MATRIX.md`](../agent/DOC-UPDATE-MATRIX.md) · [`docs/PROPOSAL_CREATION_SOP.md`](../PROPOSAL_CREATION_SOP.md) ·
[`modules/marketing-crosswalk/README.md`](../../modules/marketing-crosswalk/README.md) ·
[`docs/architecture/stream-personality-audio-routing.md`](../architecture/stream-personality-audio-routing.md) ·
[`docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md`](../proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) ·
[`docs/guides/README.md`](../guides/README.md).
