# Streaming personality audio routing

**Status:** P-066 local prompt/review, clip routing and manual script Q&A built; OBS/Windows production acceptance open · **Last reviewed:** 2026-10-02

This is the short operational reference for deciding whether a streaming personality uses the
Soundboard or the normal AI voice path. The detailed scope, contracts, rollout, and acceptance
criteria live in [P-066](../proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md).

## The rule

The Soundboard is for short, pre-created gaming reactions. The AI voice bus is for live
conversation and scripted delivery. A personality must select one audio policy per utterance;
the same phrase must never be sent to both paths.

| Personality class | Current examples | Primary output | Soundboard | Question pause |
|---|---|---|---|---|
| `gaming-reactive` | Nova's game variations and future gaming hosts | Approved short reaction clips for game events; AI voice for chat and normal commentary | Enabled for mapped reactions | Gameplay/conversation pause only; not a script Q&A flow |
| `opentech-scripted` | `nova-opentech` (OpenTechApp), `nova-stream-extend`, `nova-content-extend`, `nova-chatbot-routing` | Approved script segments through the AI voice bus | Disabled | Operator-controlled boundary pause, one source-reviewed answer, manual resume |
| `technical-scripted` | `nova-ai-learning`, `nova-ai-control`, and future general AI/technology hosts | Approved script segments through the AI voice bus | Disabled | Same source-reviewed pause/answer/resume path |
| `review-scripted` | `nova-reviewer` (VideoReview) and similar commentary programs | Operator-approved commentary through the AI voice bus | Disabled | Same manual script controls when needed |

The class is now a declared, enforced field (`audio_policy`) on every persona in
`configs/local/stream-autopilot.yaml` and every show profile in
`configs/local/stream-programming.yaml`. The planner rejects a marketing profile that declares
`gaming-reactive`, the host stamps the policy on each reply, and the director skips any mapped
Soundboard slot for a scripted policy (`scripted_audio_policy`). P-066 now adds a reviewed phrase
manifest, exclusive clip/speech routing and a separate operator-controlled script player.

This policy is separate from voice/avatar identity. A gaming host and a technical host may share
the same approved voice binding, but their delivery policy still differs. A gameplay handoff also
does not change the audio policy: it changes who controls the game, not whether the host is
reactive or scripted.

## How personalities are organized

There is one on-air identity, **Nova**. What this repository calls a *personality* is a Nova
**persona** (a mode with its own system prompt, catchphrases and audio policy). Each marketing
persona is scheduled through exactly one **show profile**. A marketing show profile binds to exactly one
Marketing Crosswalk **module**, which names the **target** repository the content is for.

```text
persona (stream-autopilot.yaml)
  -> show profile (stream-programming.yaml)        audio_policy must match the persona
       -> Marketing Crosswalk module (modules.yml)  one profile per generating module
            -> target (targets.yml)                 OpenTechApp / this platform / OpenTechnologyBlog
       -> social account (social-management/catalog.yaml)  exactly one owner per show profile
```

| Target | Module | Show profile | Persona | Audio policy |
|---|---|---|---|---|
| OpenTechApp (`task-management`) | `task-management` | `opentech-marketing` | `nova-opentech` | `opentech-scripted` |
| This platform (`hybrid-creator-platform`) | `stream-extend` | `marketing-stream-extend` | `nova-stream-extend` | `opentech-scripted` |
| This platform (`hybrid-creator-platform`) | `content-extend` | `marketing-content-extend` | `nova-content-extend` | `opentech-scripted` |
| OpenTechnologyBlog (`opentechnology-blog`) | `ai-learning` | `marketing-ai-learning` | `nova-ai-learning` | `technical-scripted` |
| OpenTechnologyBlog (`opentechnology-blog`) | `ai-control-layer` | `marketing-ai-control-layer` | `nova-ai-control` | `technical-scripted` |
| OpenTechnologyBlog (`opentechnology-blog`) | `chatbot-routing` | `marketing-chatbot-routing` | `nova-chatbot-routing` | `opentech-scripted` |

`opentech-marketing` keeps its original ID because the social account profile shares it; the
other marketing profiles use `marketing-<module>` so the ID never implies the wrong destination.
`chatbot-routing` is delivered to OpenTechnologyBlog but describes OpenTechApp product behavior,
so it is `opentech-scripted`; `ai-learning` and `ai-control-layer` teach general AI practice, so
they are `technical-scripted`. All six are configured to route through the one OpenTech social
account; this mapping is not evidence of an upload or post.

Only generating modules appear above. A discovery-only row (`subjects: []` with a `promotion` block)
has no persona, show profile or social account until it is promoted, and a `visibility: private` row
must never have one; `tests/automation_control/test_personality_bindings.py` enforces both.

All six modules can now produce [source-backed script outlines](../../modules/marketing-crosswalk/README.md#scripted-marketing-shows).
AI Control Layer and Chatbot Routing no longer have empty discovery-only subject lists: their
merged blog sources supply ten and seven guide subjects respectively. These drafts require human
completion, claim review and approval. A draft filename allowlist is not a content approval gate.
The voice studio now sequences operator-approved script paragraphs. The host still has no live
source-retrieval adapter or scheduled script/chat-question integration; those are not implied by
the manual player.

This preserves the existing executable profiles. The broader consolidated profile registry and
walkthrough engine in [P-067](../proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md) remain proposed;
this source connection does not silently adopt that new runtime or create another Nova identity.

### Adding a marketing personality

`tests/automation_control/test_personality_bindings.py` fails until all of these agree:

1. Register the module in `modules/marketing-crosswalk/crosswalk/modules.yml` (proposal first).
2. Add a persona with `game_id: <module>` and a scripted `audio_policy` to `stream-autopilot.yaml`.
3. Add a `kind: marketing` profile `marketing-<module>` with the same persona, audio policy,
   `marketing_module_id`, `marketing_target` and a one-entry `allowed_refs` to
   `stream-programming.yaml`, plus at least one show that is reachable from the rotation.
4. Route the profile to exactly one account in `modules/social-management/catalog.yaml`.
5. Do not add the module ID to `reaction_sounds` in `configs/local/stream-director.yaml`.

## Routing decision

```text
event or script segment
        |
        v
resolve personality audio policy
        |
        +-- gaming-reactive + approved clip + bound OBS hotkey
        |       -> Soundboard phrase clip
        |       -> suppress duplicate stream_speech utterance
        |
        +-- gaming-reactive + no usable clip
        |       -> configured live-voice fallback, or explicit drop
        |
        +-- scripted personality
                -> stream_speech on AI-VOICE
                -> never Soundboard
```

The existing [stream director](../../modules/automation-control/stream_director/README.md)
already maps game reactions to configured Soundboard slots. P-066 extends that mapping with an
approved generated-phrase asset type; it does not let a model choose raw OBS hotkeys, filenames,
or scenes.

## Astra's role

Astra names the requested off-air creation workflow, not a new on-air personality or TTS engine.
The implementation uses an installed Ollama model and native OS speech. The author may read the
selected gaming personality's approved identity, game variation, reaction type, energy band, and
phrase constraints to produce candidate text and render candidate speech. Astra may not trigger
OBS, change a live show, or silently replace an approved clip. Technical scripts are supplied and
approved by the operator; question answers require separate source review before speech.

Every candidate must be reviewed before it becomes an available Soundboard clip. The saved record
needs the personality, game, reaction, phrase text, approved voice binding, duration, checksum,
generation/config revision, and review state. Generated audio is local creator data; only small
metadata belongs in version control unless the owner intentionally chooses to bundle an asset
with verified rights.

## Prompt review and app backlog

For Soundboard personalities, the implemented review loop is **generate an editable personality
prompt → generate immediate audio previews → compare and give feedback → approve the exact
revision → select it for production**. Later improvements create a new draft while the approved
production version stays available. Prompt approval does not automatically approve future audio.
“Immediate” means on-demand audition generation; latency remains to be measured and previews
must stay off the stream output.

See [P-066's starter prompt and review flow](../proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md#prompt-audition-alignment-and-improvement).
The **P-066-UI** backlog item is built at **Stream Extend → Automated streaming → Personalities → Prompt & Voice
Preview**, with prompt editing, Play/Stop, feedback, revision comparison, approval and rollback.
See the [voice studio operator guide](../../modules/automation-control/voice_studio/README.md)
for setup, review gates, paired director/speech configuration and remaining OBS acceptance.

## Scripted pause boundary

The owner's full-build request includes the manual OpenTech/technical pause flow:

1. Pause finishes the current segment; Stop immediately cancels current speech.
2. Enter `paused_for_question` and keep the script cursor stable.
3. Accept at most one bounded question from the approved input path.
4. Draft an answer from the episode's approved sources/context; if evidence is missing, defer.
5. Speak the answer through AI-VOICE after operator policy permits it.
6. Resume from the saved script cursor or end the segment.

For a marketing personality, "the episode's approved sources" means only the Marketing Crosswalk
artifacts of its one bound module (the profile's `artifact_prefixes`). A question about another
module, an unreleased feature, pricing, or anything the brief does not cover gets a short deferral
("that's outside today's brief") rather than an improvised answer. `technical-scripted` answers
use the supplied sources only in this implementation, as do `opentech-scripted` answers. Questions
are operator-entered, every answer requires review, and resume is explicit; no automatic resume
timer or live chat ingress is implemented. The generator's grounding instruction is not proof of
factual correctness, so the operator checks the answer against the brief before speech.

The answer is never saved as a Soundboard clip automatically. This keeps a technical answer
contextual and reversible, and prevents a one-off viewer question from becoming a reusable
reaction asset.

## Where to look

- [P-066 proposal](../proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md): implementation scope and contracts.
- [Nova show bible](../proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md): personality energy and show intent.
- [Stream Autopilot config](../../configs/local/stream-autopilot.yaml): current profiles and phrases.
- [Soundboard module](../../modules/soundboard/README.md): OBS-native clip ownership and licensing boundary.
- [Audio Production speech worker](../../modules/audio-production/stream_speech/README.md): live AI voice ownership.
