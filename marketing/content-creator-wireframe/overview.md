# Content Creator — the whole app at once

> **Evidence:** composed from the per-feature click paths in this set, which are read from the code on `main`. The apps were not
> launched. This file is a view over the feature folders, not a second source of truth: when a feature changes, update its own folder and
> then refresh the one line here.

## The three apps and their tabs

| App | Opens on | Tabs | Where its features sit |
|---|---|---|---|
| **Stream Extend** | [Module setup](../../apps/stream-extend/src/routes/+page.svelte#L194) | [Module setup](../../apps/stream-extend/src/routes/+page.svelte#L194), [Connections](../../apps/stream-extend/src/routes/+page.svelte#L195), [Remote control](../../apps/stream-extend/src/routes/+page.svelte#L196), [Social](../../apps/stream-extend/src/routes/+page.svelte#L197), [Automated streaming](../../apps/stream-extend/src/routes/+page.svelte#L198), [Dashboard](../../apps/stream-extend/src/routes/+page.svelte#L199) | OBS control on the Dashboard; the AI host and Personalities on Automated streaming |
| **Creator Extend** | [Module setup](../../apps/creator-extend/src/routes/+page.svelte#L454) | [Module setup](../../apps/creator-extend/src/routes/+page.svelte#L454), [Connections](../../apps/creator-extend/src/routes/+page.svelte#L455), [Remote control](../../apps/creator-extend/src/routes/+page.svelte#L456), [Social](../../apps/creator-extend/src/routes/+page.svelte#L457), [Recordings](../../apps/creator-extend/src/routes/+page.svelte#L458), [Dashboard](../../apps/creator-extend/src/routes/+page.svelte#L459) | Creative tools, ComfyUI workflows and the Posture Screen on the Dashboard; the recording inbox on Recordings |
| **Extend** (combined, private preview) | the home page, [Stream and create, in one place.](../../apps/extend/src/routes/+page.svelte#L162) | a left [Workspace navigation](../../apps/extend/src/routes/+page.svelte#L149) with Home, Stream, Create, Library and Settings | A read-only shell: it reads setup state, lists the bundled workflows and holds the [Media library](../../apps/extend/src/routes/+page.svelte#L180); running jobs still happens in the two apps |

Both main apps carry the same shared tabs, so those are described once, in
[setup and readiness](features/setup-and-readiness/click-paths.md): [Module setup](../../apps/shared/ui/ModuleSetup.svelte#L404) and
Connections. The Recordings tab is the same component in Creator Extend and, with fewer buttons, in the combined preview
([`preview={true}`](../../apps/extend/src/routes/+page.svelte#L180)).

## The path from first run to a finished piece of content

1. Open either app and work through [setup and readiness](features/setup-and-readiness/click-paths.md): choose tools, install prerequisites, check readiness, connect services.
2. In Creator Extend, [preflight and run a ComfyUI workflow](features/comfyui-workflows/click-paths.md) and read the output history.
3. In Creator Extend, [plan and render Blender stills](features/blender-stills/click-paths.md) as an owned local job.
4. In Stream Extend, [switch scenes, go live and record](features/stream-control-and-recording/click-paths.md); stopping sends the file to Creator Extend.
5. In Creator Extend's Recordings tab, [work the recording through its states](features/stream-control-and-recording/click-paths.md) from ready to published.
6. In Stream Extend's Automated streaming tab, [rehearse the lifecycle and start the local runtime](features/automated-streaming/click-paths.md).
7. In the same tab, [draft, audition and approve a personality](features/personalities-and-voice/click-paths.md) before it is used.
8. Separately, [analyze a photo with the Posture Screen](features/posture-screen/click-paths.md) as a sports-analytics example.

## Feature index

| Feature | Folder | In one line |
|---|---|---|
| Setup and readiness | [`features/setup-and-readiness/`](features/setup-and-readiness/click-paths.md) | Choose tools, install prerequisites, check readiness, connect services, scan capture hardware. |
| ComfyUI workflows | [`features/comfyui-workflows/`](features/comfyui-workflows/click-paths.md) | Preflight a bundled workflow, set its inputs, run it, read the output history. |
| Blender stills and creative tools | [`features/blender-stills/`](features/blender-stills/click-paths.md) | Open Blender or Krita, plan a batch render, render stills as an owned job, prepare the add-on. |
| OBS control and the recording handoff | [`features/stream-control-and-recording/`](features/stream-control-and-recording/click-paths.md) | Switch scenes, go live and record, then find the file in Creator Extend's inbox. |
| Automated streaming | [`features/automated-streaming/`](features/automated-streaming/click-paths.md) | Rehearse the lifecycle, start the local production runtime, cue the avatar. |
| Personalities: prompt and voice preview | [`features/personalities-and-voice/`](features/personalities-and-voice/click-paths.md) | Draft a persona with a local model, audition and approve it, map hotkeys, run a scripted show. |
| Posture Screen | [`features/posture-screen/`](features/posture-screen/click-paths.md) | Analyze a photo for body alignment with a local pose model. |

## Built is not accepted

Everything above is *built*: it exists in the code and is reachable from the apps. None of it has been accepted on a real account or
live stream, and the platform has not yet created an external stream, post or upload (`ST-R15` in the
[run lanes](../../docs/todo/README.md)). What may be said publicly about each feature follows its status in
[MARKETING.md](../../MARKETING.md) and [docs/AUDIT.md](../../docs/AUDIT.md); the AI parts are inventoried, with what each needs, in
[docs/AI_ACTIONS_INVENTORY.md](../../docs/AI_ACTIONS_INVENTORY.md). Screenshots of the real app are placeholders for now; see the README.

## Not covered in this first pass

These exist in the apps and follow the same pattern; they are listed so nothing is silently dropped.

- **Remote control** tab: [`RemoteControl`](../../apps/creator-extend/src/routes/+page.svelte#L486) in Creator Extend and
  [`RemoteControl`](../../apps/stream-extend/src/routes/+page.svelte#L224) in Stream Extend, from
  [Remote control](../../apps/shared/ui/RemoteControl.svelte#L114).
- **Social** tab: [`SocialManagement`](../../apps/creator-extend/src/routes/+page.svelte#L488) /
  [`SocialManagement`](../../apps/stream-extend/src/routes/+page.svelte#L226), from
  [Social Management](../../apps/shared/ui/SocialManagement.svelte#L164).
- **Profile switcher** in each header: [`ProfileSwitcher`](../../apps/stream-extend/src/routes/+page.svelte#L183).
- **Audio routing** inside Module setup: [Audio routing](../../apps/shared/ui/AudioSetup.svelte#L25).
- **The combined preview's own settings**: [Profiles & accounts](../../apps/extend/src/routes/+page.svelte#L182),
  [Workspaces and layout](../../apps/extend/src/routes/+page.svelte#L186) and [Guided setup](../../apps/extend/src/routes/+page.svelte#L189).
- **Commands with no screen** (`comfyui_queue`, `comfyui_load_workflow`, `krita_run_script`) are in the AI actions inventory, not here.
- **Outside the apps:** the OBS plugin, the Blender add-on once installed in Blender, the Krita panels, and the command-line sports tools.
