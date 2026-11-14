# Automated streaming — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Stream Extend → [Automated streaming](../../../../apps/stream-extend/src/routes/+page.svelte#L198)**, which mounts the
[`<Autopilot {invoke} />`](../../../../apps/stream-extend/src/routes/+page.svelte#L228) panel. Below its rehearsal section it mounts
[`<ProductionControls {invoke} />`](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L120) (the local production runtime) and the
[Personalities](../personalities-and-voice/click-paths.md) panel. The runtime starts local worker processes: the AI host (answers through a
local Ollama model), a director, speech, an avatar controller and, only with credentials, chat.

## Path 1 — Open the tab and read the session policy

1. Click [Automated streaming](../../../../apps/stream-extend/src/routes/+page.svelte#L198). The panel is headed
   [Automated streaming](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L61) with
   [Validate session policy and exercise pause, recovery and stop controls before connecting live services.](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L62)

   *Caption:* The Automated streaming tab with the policy introduction and the Session menu.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-01.png]
2. If the policy cannot be read it says [Autopilot policy is unavailable.](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L70)
   with a [Retry](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L71) button.
3. Under [Session](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L76) pick one of the configured sessions; each option shows its id and
   game ([`{id} · {item.game_id}`](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L81)) and is greyed out if it is not enabled.

## Path 2 — Rehearse the whole lifecycle without going live

1. Under [Safe lifecycle rehearsal](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L96) click
   [Run lifecycle rehearsal](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L99). It
   runs: [Runs preflight → preview → pause → resume → stop with local durable state.](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L97).
2. The page promises
   [This rehearsal never starts OBS streaming, gameplay, a model, voice, avatar, or chat.](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L101)
3. The result reads [Rehearsal complete](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L107) with the lifecycle state, the sequence of driver
   actions, and [`Broadcast started: {result.broadcast_started ? 'yes' : 'no'}`](../../../../apps/stream-extend/src/lib/Autopilot.svelte#L109).

   *Caption:* The Rehearsal complete result with the driver actions and Broadcast started: no.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-02.png]

## Path 3 — Check readiness and start a local preview

1. Under [Local production runtime](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L70) click
   [Check production readiness](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L81). The panel lists each check with its status and the
   state of each worker ([`Workers:`](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L78)). It refreshes itself every
   [1500](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L63) milliseconds.

   *Caption:* The Local production runtime panel after Check production readiness, with check statuses and worker states.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-03.png]
2. The policy is printed plainly:
   [`Live start: {runtime.policy?.broadcast_start_authorized ? 'Authorized in local policy' : 'Locked'}`](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L75). The panel says
   [Live start and gameplay stay locked unless the operator configuration explicitly enables them.](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L71)

   *Caption:* The policy line showing live start Locked and gameplay Disabled.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-04.png]
3. Once the checks pass, [Start local preview](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L82) is enabled. It starts the workers in preview.

## Path 4 — Run, pause, resume and stop

1. In preview, [Run authorized local session](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L83) is enabled only if the local policy authorizes
   a local run. When broadcast control is enabled the same button reads
   [Run authorized broadcast](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L83), and only if the policy authorizes broadcast.

   *Caption:* The runtime in preview with Run authorized local session, Pause output and Stop runtime enabled.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-05.png]
2. [Pause output](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L84) and [Resume to preview](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L85)
   move between running and paused; resuming returns to preview, not to the air.
3. [Stop runtime](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L86) ends it; [Emergency stop](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L87)
   does so without waiting. The header carries the same action at all times:
   [Emergency stop runtime](../../../../apps/stream-extend/src/routes/+page.svelte#L184), which answers
   [Owned AI runtime stopped.](../../../../apps/stream-extend/src/routes/+page.svelte#L70) or says the stop is not confirmed.
4. [Verify OBS is inactive](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L89) reconciles with OBS;
   [Recheck state](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L88) re-reads the runtime;
   [Close production owner](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L90) releases the runtime.

## Path 5 — Cue the avatar

1. In preview or running, the buttons under [Owned avatar cues](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L93) make the avatar react:
   [`['wave','nod','shrug','look_left','look_right','happy','surprised','neutral']`](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L94).
   They stay disabled unless [`runtime?.avatar_enabled`](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L95) is on.

   *Caption:* The Owned avatar cues buttons enabled while the runtime is in preview.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-06.png]

## Path 6 — Prepare the optional private-world game session

1. Open [Optional private-world game setup](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L92). It
   [Requires Node.js 22+ and an explicitly permitted private test world.](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L92)

   *Caption:* The Optional private-world game setup section expanded, showing its Node.js requirement.
   [screenshot: marketing/content-creator-wireframe/screenshots/automated-streaming/step-07.png]
2. Click [Prepare optional Minecraft package](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L92) while the runtime is stopped. It calls
   [`autopilot_prepare_game`](../../../../apps/stream-extend/src-tauri/src/autopilot_control.rs#L533), which installs the pinned game SDK and
   [starts no game client](../../../../apps/stream-extend/src/lib/ProductionControls.svelte#L92).

## What this feature does not do (so a conversation does not promise it)

The AI host has never spoken to a real audience: its live acceptance rows (`ST-R10`, `ST-R11`) are blocked on accounts and dry runs, and no
external stream has ever been created (`ST-R15`), see the [run lanes](../../../../docs/todo/README.md) and the
[AI actions inventory](../../../../docs/AI_ACTIONS_INVENTORY.md). Live start and gameplay are off unless an operator enables them in local
configuration. Playing games beyond the first bounded adapter is proposed, not built (`P-056`).
