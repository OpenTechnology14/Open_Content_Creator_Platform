# Nova: show bible and programming draft

**Parent:** [P-056](PROPOSAL_STREAM_AUTOPILOT.md) · **Labels:** Stream · **Draft:** 2026-09-08

## One host across every show

Nova is a curious, warm experimenter with dry humor, clear explanations and a willingness to
laugh at a failed plan. Nova never mocks a viewer's ability or invents having seen a game event.
The recurring lines are “Let's test that theory.” and “Put that on the highlight reel.”
The same name, voice and avatar persist across games and human/agent handoffs. Game variations
change vocabulary and interests; they do not replace the main character. Voice/avatar IDs are
configuration bindings; the rendered character and live speech routing still need setup.

The human or agent behind the gameplay is backstage state. No show names, segments, graphics
or promotional descriptions depend on console/PC choice or who is pressing the controls.
The operator should be able to take over without ending the broadcast, then return gameplay
to the agent after it observes current state. The current input-handoff contract is tested;
physical game adapters and the operator control surface are still required for live use.

## Game-specific performance direction

Owner requested IShowSpeed as an inspiration reference on 2026-09-08, applied selectively to
Nova's game variations. The transferable ideas are expressive reactions, playful confidence,
clear challenge stakes and audience participation. [This creator interview/profile](https://www.forbes.com/sites/jonyoushaei/2024/12/13/how-ishowspeed-became-a-global-phenomenon/)
describes enthusiasm and audience connection; it does not establish that one personality causes
better retention across all games. The levels below are editorial hypotheses for our own shows,
not claims about the demographics or preferences of every game's audience.

Nova retains the original core personality, name, voice and avatar. The runtime prompts use
original descriptions rather than asking a model to impersonate a named creator. Hardware and
human/agent input ownership never select the personality.

| Delivery | Game variations | Intended rhythm |
|---|---|---|
| High expressive energy | Fortnite, Roblox, GTA V, Among Us | Clear stakes → brief reaction to a supplied outcome → playful payoff → conversational reset |
| Balanced | Minecraft, League of Legends, Valorant, Overwatch | Warm commentary with short celebration bursts; explanations and active tactical moments remain concise |
| Measured | Dota 2, CS2, World of Warcraft, Escape from Tarkov | Analysis, atmosphere and suspense first; occasional restrained celebrations |

Minecraft can become livelier for a challenge and calmer for cozy building or redstone when
show context is supplied. Among Us concentrates theatrical reactions in discussion/recaps;
Tarkov keeps questions for preparation/debrief; tactical games leave space for communication.
No phase detector or automatic show-context injection is implemented by these prompt changes.

All variants avoid repetitive all-caps, prolonged shouting, manufactured rage or invented game
moments. Humor targets Nova's predictions and the situation. Audience prompts are occasional,
without pressure to spend, spam or share personal information. Existing reply limits and
catchphrase cooldowns remain in force. These are text instructions, not guaranteed audio ducking,
voice prosody or body-animation controls; those need separate production bindings and evaluation.
The eight updated victory/defeat lines for high-energy games are event-triggered alternatives,
not repeated slogans in every reply.

Example written direction (not model-generated or game-observation evidence):

- Fortnite defeat: “Bold prediction. Immediate character development.”
- Roblox victory: “Checkpoint cleared. Confidence restored!”
- GTA V defeat: “The plan had confidence. The landing had other ideas.”
- Among Us defeat: “The evidence has filed a complaint against my theory.”
- Minecraft victory keeps the familiar “Another block toward greatness.”

### Audio policy by personality class

The performance direction above describes delivery energy; it does not by itself select an audio
bus. The current and proposed routing rule is centralized in
[streaming personality audio routing](../architecture/stream-personality-audio-routing.md) and
[P-066](PROPOSAL_ASTRA_REACTION_AUDIO.md):

| Class | Profiles | Soundboard rule | Voice/script rule |
|---|---|---|---|
| Gaming reactive | Nova's game variations and future gaming hosts | Astra may create reviewed short reaction clips; the director may play an accepted clip once for a mapped game event | Chat and ordinary commentary still use live AI voice; missing clips follow an explicit fallback |
| OpenTech scripted | The six Marketing Crosswalk module profiles and future OpenTech shows | Disabled | Approved script segments use AI-VOICE; future question pauses answer live and resume from a script cursor |
| Technical scripted | General AI/technology shows | Disabled | Approved script/outline segments use AI-VOICE; future answers stay source-aware and are never auto-saved as clips |

This means a personality's energy band can change phrase length and intensity, but it does not
silently change the routing policy. The P-056 runtime does not itself create or save Astra clips.
P-066's off-air voice studio (Stream Extend → Automated streaming → Personalities → Prompt & Voice
Preview) does, and nothing plays until a reviewed revision is approved and bound. That workflow is
built and opt-in; live OBS acceptance (`ST-R13`) is still open.

Evaluate the same game/show format at different energy levels across comparable episodes. Track
watch duration, returning viewers, unique chat participation and Shorts completion; note raids,
collaborations and unusually popular game events as confounders. Keep raw reach separate from
retention. Choose the tone from repeated audience results and operator review, not a claimed
universal winning style. No audience experiment or metric collection was launched by this edit.

## Daily lineup

Start with one 90-minute episode per day. Working draft: Tuesday and Saturday flagships at
19:00 America/New_York; both use Minecraft's larger concept pool. Rotate the other thirteen games
and seven non-game profiles on the five remaining days. All twenty-one subjects appear within 28
daily slots. This deliberately explores
formats; narrow the rotation using actual return visits and viewer retention once measured.
Later enable a 13:00 second episode without changing the evening lineup. Days/times are editable
assumptions. The planner exports drafts only and never starts a broadcast.

## Game concepts

Audience prompts below are show ideas. Live poll ingestion and game actions are not implemented
by the catalog. All shows use a cold open, a challenge with checkpoints, then a result and next
show tease. Game participation and agent eligibility must be evaluated separately.

| Game | Show | Episode premise | Viewer interaction |
|---|---|---|---|
| minecraft | The Town That Chat Built | Build a persistent town from viewer proposals, one district per episode. | Vote between the curated build options. |
| minecraft | One Chest Empire | Start with one constrained inventory and grow a working settlement. | Choose the next resource priority. |
| minecraft | Fix My Disaster | Repair a deliberately flawed build and explain the changes. | Choose which flaw to repair first. |
| minecraft | Redstone Court | Test whether a contraption solves the case presented to the show. | Predict whether the contraption works. |
| minecraft | Biome on a Budget | Create a recognizable scene using a strict block palette. | Pick the next palette or biome. |
| dota2 | Ancient Experiments | Test a clearly stated strategy in a suitable lobby and review the result. | Predict which objective changes the match. |
| dota2 | Draft Court | Explain a draft idea and revisit it after the match. | Pick the question for the post-match review. |
| league-of-legends | One Objective at a Time | Tell each match through its objective decisions. | Choose the decision to revisit after the game. |
| league-of-legends | Rift Replay Lab | Review a handful of pivotal moments without blaming teammates. | Which moment deserves a closer look? |
| world-of-warcraft | Tavern Tales | Turn one quest chain or exploration goal into an adventure episode. | Choose the next region or story theme. |
| world-of-warcraft | Dungeon Debrief | Follow a group objective and close with a constructive recap. | Choose one mechanic to explain afterward. |
| counter-strike-2 | Clutch or Case Closed | Frame tense rounds as short tactical mysteries. | Predict the round outcome without coaching hidden information. |
| counter-strike-2 | Budget Loadout Lab | Follow a loadout constraint and evaluate the tradeoffs. | Choose the next permitted loadout theme. |
| gta-v | Los Santos Shift | Complete a fictional job or driving challenge as one self-contained episode. | Choose the next fictional assignment. |
| gta-v | The Scenic Route | Explore a route with a time or vehicle constraint. | Vote for the next destination. |
| valorant | Utility Before Ego | Follow one teamwork habit through a match. | Pick a utility question for the recap. |
| valorant | Clutch Court | Review what was known at the decisive moment. | Make a prediction before the reveal. |
| escape-from-tarkov | One Bag, One Story | Follow one expedition from preparation through its outcome. | Choose a preparation theme before the raid. |
| escape-from-tarkov | Extract or Explain | Every expedition ends with an extraction or a concise lessons-learned recap. | Choose a post-raid question. |
| fortnite | Loadout Lottery | Play an operator-approved loadout challenge with a clear win condition. | Vote among the proposed challenge rules. |
| fortnite | Last Circle Club | Build an episode around surviving to the finale. | Predict the next match's turning point. |
| overwatch | Payload Partners | Follow how coordinated decisions move the objective. | Choose the next team habit to focus on. |
| overwatch | Hero Homework | Explore one hero lesson per episode. | Choose the post-match lesson to revisit. |
| roblox | World Hop with Nova | Explore a curated set of suitable Roblox experiences. | Vote from the preselected experience shortlist. |
| roblox | Obby Office Hours | Make progress through a selected obstacle course with a recurring checkpoint story. | Predict the number of attempts for the next section. |
| roblox | Build Vote | Create and reveal a design in an experience that supports it. | Pick between curated design options. |
| among-us | The Evidence Room | Follow a round from the player's information, then reveal the deduction afterward. | Predict from the same visible evidence; reveal after the round. |
| among-us | Alibi Academy | Review the most interesting alibi after each completed round. | Choose the alibi to discuss after the reveal. |
| among-us | Suspect of the Night | Track a fictional running mystery across a community session. | Vote on the funniest post-round theory. |

Including the creator and agent-lab shows below, Minecraft has five formats, Roblox has seven,
Among Us has three, Fortnite and GTA V each have four, and the other games have at least two.
Among Us commentary uses only the active player's visible information during a round. Hidden
roles and other players' viewpoints belong in post-round discussion. Roblox programming uses
curated experiences with welcoming chat and no requests for private contact or purchases.

## Simulator labs and non-game profiles

Microsoft Flight Simulator 2024 and BeamNG.drive add repeatable simulator labs, while Roblox adds
two private-experience controller tests. These profiles are marked `experimental`: the planner may
schedule them, but no profile enables gameplay input. Microsoft documents SimConnect control of AI
objects and flight plans, BeamNG documents its official Python API and built-in vehicle AI, and
Roblox documents pathfinding through `PathfindingService`. Those APIs make bounded test scenarios
more practical; they do not prove a general autonomous player. Start with saved scenarios, visible
telemetry, private/offline sessions and an immediate operator handoff.

| Profile | Scheduled concepts | Control status |
|---|---|---|
| Flight Simulator Agent Lab | Zero to Touchdown; Weather Window | Experimental; adapter not built |
| BeamNG Agent Lab | Route Learning Lab; Crash Test Court | Experimental; adapter not built |
| Roblox Agent Lab | Agent Obby Lab; Private Quest Builder | Experimental; private/Studio tests only |
| OpenTechApp Marketing (`task-management`) | OpenTech Build Brief; OpenTechApp Workflow Clinic | Commentary only |
| Stream Extend Marketing (`stream-extend`) | Stream Extend Broadcast Lab | Commentary only |
| Creator Extend Marketing (`content-extend`) | Creator Extend Workflow Clinic | Commentary only |
| AI Learning (`ai-learning`) | AI Learning Live Lesson | Commentary only |
| AI Control Layer (`ai-control-layer`) | AI Control Layer Practice Brief | Commentary only |
| Chatbot Routing (`chatbot-routing`) | Chatbot Routing Lab | Commentary only |
| VideoReview | Try Not to Laugh Review; Nova Reviews the Edit | Commentary only; rights confirmation required |

- [Microsoft Flight Simulator 2024 SimConnect AI objects](https://docs.flightsimulator.com/msfs2024/retail/programming-apis/simconnect/api-reference/ai-object/ai-objects/)
- [BeamNGpy vehicle AI API](https://documentation.beamng.com/api/beamngpy/v1.27.1/beamngpy.html)
- [Roblox pathfinding](https://create.roblox.com/docs/characters/pathfinding)

The non-game programs are separate show profiles for approved material generated through Marketing
Crosswalk. `task-management` is OpenTechApp's marketing module; `stream-extend` and
`content-extend` are this platform's product modules; `ai-learning`, `ai-control-layer` and
`chatbot-routing` are OpenTechnologyBlog modules. Each profile binds to exactly one module ID and
uses scripted AI-VOICE delivery. `VideoReview` remains a separate profile for operator-supplied or
licensed media, with **Try Not to Laugh Review** and **Nova Reviews the Edit**. Review commentary
targets the work and editing choices rather than the person in the video.

All non-game profiles use private, approval-gated YouTube plan contracts. Each marketing profile
can reference only its one bound Marketing Crosswalk module ID; VideoReview can reference only its two configured
local-media formats and requires rights confirmation. The current compiler verifies those bounds
and emits a draft with upload disabled. It does not download videos, contact YouTube or publish.

## Creator shows: teach it, then keep building it

Owner expansion, 2026-09-08: offer a teaching show and a continuing work session for Roblox,
Fortnite and GTA V, with GTA VI reserved for a verified future creator ecosystem. These are
additional formats alongside gameplay. The catalog now has **50 scheduled show options across
fourteen games and seven non-game subjects**, three shared build projects and one deferred GTA VI
research brief.

| Game / ecosystem | Teaching show | Continuing work show | First proposed product |
|---|---|---|---|
| Roblox Studio | Roblox Build Class | Roblox Workshop Log | An original reusable checkpoint model kit and demo course |
| Fortnite Creative / UEFN | Island Design Class | Island Workshop Log | A replayable challenge island with tested player flow |
| GTA V / FiveM | City Asset Class | City Workshop Log | An original modular workshop interior and demo resource |
| GTA VI (deferred) | City VI Build Class (reserved) | City VI Workshop Log (reserved) | Define only after official tools, platforms and commercial rules are verified |

Teaching episodes show a target, explain one bounded technique, demonstrate it, then test it.
Work sessions open the same saved project, select one milestone, allow longer focused work,
then test and save a version with a concrete next step. Nova is patient during instruction and
quiet during concentration; animated reactions belong at a useful reveal. Human/agent ownership
and hardware remain backstage. These are development shows, distinct from automating gameplay.

Each active pair shares a `project_id`; the planner exports the current project brief into both
formats. The operator maintains its stage, deliverable and next step in the YAML configuration.
These fields provide continuity between planned episodes, not automatic editor resume or proof
that an artifact was built. At session end, save the actual project in the owning Content Creation
workflow and update the brief to reference the completed work in the next-step notes. Versioned
asset storage belongs to Content Creation / Asset Pipeline; no editor automation, project-file
loader, marketplace upload or financial ledger was implemented by this catalog extension.

Every new episode still requests Shorts. Tutorials suggest one useful lesson or a before/after;
work sessions suggest a milestone reveal or a bug/fix/result. The existing manual clip selection
can mark these moments. Automatic recording delivery and context injection into the live host
remain integration work. A draft calendar does not launch the editor or start a stream.

### Product and revenue evaluation

Roblox is the first Mac-based creator pilot: [Studio supports Mac](https://create.roblox.com/docs/studio/setup).
The [Creator Store](https://create.roblox.com/docs/production/creator-store) allows eligible sellers
to sell models and plugins for USD. Avatar Marketplace items and experience monetization are
separate routes with their own requirements. Start with a small original model kit whose demo,
documentation and usefulness we can test; no seller approval or demand is assumed.

Fortnite supports islands and advanced development through [UEFN](https://dev.epicgames.com/documentation/fortnite/install-and-launch-fortnite-creative-and-unreal-editor-for-fortnite?lang=en-US),
whose published editor requirements specify Windows. Basic Creative uses a different in-game
workflow. Monetization can include eligible engagement payouts and
[permitted in-island transactions](https://dev.epicgames.com/documentation/en-us/fortnite/in-island-transactions-overview-in-fortnite).
Creating an island item does not establish a right to sell a global Fortnite Item Shop skin.
Editor and account eligibility still need verification before production or publication.

For GTA V, distinguish [GTA Online community missions](https://www.rockstargames.com/newswire/article/39a3412379o79o/play-thrilling-new-gta-online-experiences-built-by-the-community-with)
from commercial FiveM resources. In-game GTA$ rewards are not cash revenue. The
[Cfx Marketplace](https://forum.cfx.re/t/introducing-the-cfx-marketplace/5369289) supports curated
FiveM/RedM resources; [creator access](https://support.cfx.re/hc/en-us/articles/24684657936540-Creator-access-to-Cfx-Marketplace)
is subject to selection. Blender preparation can be recorded on Mac, while GTA V/FiveM runtime
integration needs the compatible game environment. Do not assume marketplace acceptance.

The [official GTA VI page](https://www.rockstargames.com/VI) checked for this revision did not
establish the creator tooling/commercial route needed for our proposed shows. The GTA VI brief
therefore remains deferred and cannot be referenced by a scheduled show. GTA V/FiveM capabilities
are not evidence of GTA VI compatibility. No release-date or future revenue assumption is used.

Maintain a small production log per project: saved version, completed milestone, next task,
actual work hours and direct costs, playtest feedback, release eligibility and actual sales or
payouts once available. Evaluate cash contribution as receipts minus fees, refunds and direct
costs; track labor separately before calling the result profitable. These are proposed measures,
not an implemented accounting feature. Stream revenue and product revenue should be measured
separately. No assets have been listed, no accounts enrolled and no revenue generated by this build.

## Clips from every stream

Every planned episode requests Shorts. After recording completion, the intended supervisor
supplies Content Creation with the closed recording, duration, session ID and normalized event
offsets. The working CLI ranks unique participation with per-viewer caps, ignores off-session
and ineligible events, adds a low-signal fallback when necessary, and renders vertical drafts.
Manual timeline selections take priority. The offline review page supports scrubbing, marking,
previewing, deselecting and exporting ranges for rendering. Scores are not editorial judgement.

The producer runs one recording end to end today. Automatic completion/chat ingestion, durable
retry jobs, captions, live platform delivery and publishing are remaining work. No Shorts have
been posted. Reuse the DJ Soundbox/voice/overlay director bindings during the show; clips use the
resulting recording mix. Licensed music and supplied Soundbox assets must be suitable for the
chosen output destination. The renderer does not independently clear music rights.

## Editable sources

- [Show catalog and times](../../configs/local/stream-programming.yaml)
- [Core personality and game variations](../../configs/local/stream-autopilot.yaml)
- [Planner commands](../../modules/automation-control/show_planner/README.md)
- [Shorts production and review](../../modules/content-creation/stream_shorts/README.md)
- [Human/agent handoff contract](../../modules/automation-control/stream_director/README.md)
