# Daily show planner

**Labels:** Stream · P-056 · Local, draft-only scheduling.

The catalog in [stream-programming.yaml](../../../configs/local/stream-programming.yaml)
contains 50 concepts across fourteen games and seven non-game subjects, plus a deferred GTA VI
project brief. Nova's identity comes from the AI Agents host config. The six marketing subjects
are direct bindings to registered Marketing Crosswalk module IDs; they are show profiles, not new
Nova identities.
The same show can be played by a human or an eligible agent. Hardware and input ownership are
backstage configuration; they never select the show name, voice, avatar, or catchphrases.

From the repository root with Python 3.11+:

```bash
.venv-stream-autopilot/bin/pip install -r modules/automation-control/show_planner/requirements.txt
PYTHONPATH=modules/automation-control .venv-stream-autopilot/bin/python -m show_planner --start 2026-09-08 --days 28
PYTHONPATH=modules/automation-control .venv-stream-autopilot/bin/python -m show_planner --start 2026-09-08 --days 28 --daily-slots 2
```

The working draft has Tuesday/Saturday Minecraft flagships at 19:00 America/New_York;
other games rotate on the remaining days. A second daily slot at 13:00 is opt-in. These are
editable programming assumptions. The primary lineup remains unchanged when slot two is added.
All fourteen games and all seven non-game subjects occur in the first 28 daily episodes. Every episode
requests Shorts production.
Intervals are timezone-aware; overlapping episodes and ambiguous/nonexistent DST times fail.

Output is a JSON planning artifact with `launch_enabled: false`. There is no timer, automatic
OBS start, account provisioning, recording-completion listener, or upload. A future supervisor
must resolve readiness, game eligibility, destination ownership and recording completion before
turning a draft episode into a live session. DigitalOcean adds no required service or dependency.

## Stream profiles and scoped YouTube handoff

Ten explicit profiles cover experimental controller labs for Microsoft Flight Simulator 2024,
BeamNG.drive and private Roblox experiences, six module-specific scripted marketing programs, and
`VideoReview`. `experimental` means the show is suitable for adapter evaluation; it does not
enable input control. The flight, driving and Roblox controller adapters still need bounded
implementation and live acceptance before an agent may play.

Every profile declares `audio_policy`. Game profiles are `gaming-reactive`; marketing profiles
must be `opentech-scripted` or `technical-scripted`; `VideoReview` is `review-scripted`. The
persona → profile → module → target → social-account chain and the checklist for adding one are in
[streaming personality audio routing](../../../docs/architecture/stream-personality-audio-routing.md#how-personalities-are-organized).

Each scripted marketing profile accepts exactly one registered Marketing Crosswalk module ID:
`task-management` for OpenTechApp, `stream-extend` and `content-extend` for this platform, and
`ai-learning`, `ai-control-layer` and `chatbot-routing` for OpenTechnologyBlog. `VideoReview`
accepts operator-selected local media for the try-not-to-laugh and general review formats and
requires an explicit rights confirmation. All non-game profiles generate private, approval-gated
YouTube handoff plans. The compiler accepts an existing local media file, never a URL, shell
command or arbitrary marketing source:

```bash
PYTHONPATH=modules/automation-control .venv-stream-autopilot/bin/python \
  -m show_planner.youtube \
  --profile opentech-marketing \
  --source task-management \
  --source-artifact /absolute/path/to/hybrid-creator-platform/modules/marketing-crosswalk/out/task-management--extend_platform--stream-script.md \
  --media /absolute/path/to/approved-demo.mp4 \
  --title "OpenTechApp workflow demo"
```

Generate the outline first with the Crosswalk's
[`stream-script` workflow](../../marketing-crosswalk/README.md#scripted-marketing-shows), then
complete/review it and record the episode manually. The result records the bound persona and audio
policy, destination channel environment-variable name, private visibility and approval state,
with `upload_enabled: false`. It neither contacts YouTube nor publishes anything.
An upload adapter and account acceptance remain later work.

## Teaching and continuing build sessions

Six creator shows pair `tutorial` and `workshop` formats for Roblox, Fortnite and GTA V/FiveM.
Each pair references one entry in `projects`. Update the project stage and next step in the
configuration after saving actual work. Calendar episodes include `format`, `project_id` and a
snapshot `project_brief`, so an eventual supervisor can pass consistent context to either show.
Legacy gameplay-only catalogs still load without these fields. Unknown/wrong-game references,
duplicate project IDs and scheduled references to deferred projects are rejected.

The first rotation entries retain broad subject coverage; the creator shows and remaining variants
follow. Two Minecraft flagship days remain in place. All fourteen games and all seven non-game
subjects occur in the default first 28 days; additional creator variants remain reachable later
in the rotation. This is programming metadata,
not readiness approval. The active projects start at `idea`; editors, assets and seller accounts
remain unconfigured. The GTA VI brief is deferred and has no active shows or persona.

Content Creation owns editor workflows and saved asset versions. This planner does not import
editor code or claim to resume a project, earn revenue, submit a marketplace listing, or inject
the brief into the current live host. Host game prompts now describe calmer teaching/workshop
delivery when that context is supplied. See the [creator show plan](../../../docs/proposals/STREAM_AUTOPILOT_SHOW_BIBLE.md#creator-shows-teach-it-then-keep-building-it).

Install the declared `tzdata` dependency on Windows: its standard library does not ship an IANA timezone database. The shared [Windows/Mac test runner](../../ai-agents/stream_host/WINDOWS_TEST.md) installs it automatically.
