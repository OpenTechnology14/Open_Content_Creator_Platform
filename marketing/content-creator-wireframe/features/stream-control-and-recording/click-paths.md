# OBS control and the recording handoff — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Stream Extend → Dashboard → [OBS Control](../../../../apps/stream-extend/src/routes/+page.svelte#L233)**, and the
other half of the handoff, **Creator Extend → [Recordings](../../../../apps/creator-extend/src/routes/+page.svelte#L458)**. It needs OBS
running with its WebSocket server on; the app connects to it. See [setup and readiness](../setup-and-readiness/click-paths.md) for the
connection and the check that unlocks these controls.

## Path 1 — See that OBS is connected

1. The header always shows the state:
   [`OBS {obsConnected ? 'Connected' : obsConnecting ? 'Connecting…' : 'Disconnected'}`](../../../../apps/stream-extend/src/routes/+page.svelte#L187),
   refreshed every two seconds ([`refreshStatus`](../../../../apps/stream-extend/src/routes/+page.svelte#L113), which asks
   [`obs_status`](../../../../apps/stream-extend/src/routes/+page.svelte#L116)).

   *Caption:* The Stream Extend header showing the OBS connection indicator.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-01.png]
2. Click [Dashboard](../../../../apps/stream-extend/src/routes/+page.svelte#L199). Until the readiness check passes the panel says
   [OBS controls are locked until the current WebSocket and scene checks pass](../../../../apps/stream-extend/src/routes/+page.svelte#L243).

## Path 2 — Switch scenes

1. Under [Scenes](../../../../apps/stream-extend/src/routes/+page.svelte#L246) there is one button per OBS scene, read with
   [`obs_scenes`](../../../../apps/stream-extend/src/routes/+page.svelte#L120); the current scene is highlighted
   ([`class:active={scene.is_current}`](../../../../apps/stream-extend/src/routes/+page.svelte#L250)).

   *Caption:* The OBS Control panel listing the scenes with the current one highlighted.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-02.png]
2. Click a scene. The app calls [`obs_switch_scene`](../../../../apps/stream-extend/src/routes/+page.svelte#L141) and redraws the list from OBS's answer.
   A failure shows in red above the panel ([`obs-error`](../../../../apps/stream-extend/src/routes/+page.svelte#L236)).

## Path 3 — Go live and record

1. Click [Go Live + Record](../../../../apps/stream-extend/src/routes/+page.svelte#L266). It is disabled while a request is running, and
   when OBS control is locked.

   *Caption:* The OBS Control panel with the Go Live + Record button before it is clicked.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-03.png]
2. Before it starts, the app reads which stream profile and which content profile are selected
   ([`plugin:social-manager|selection`](../../../../apps/stream-extend/src/routes/+page.svelte#L160)) so the recording can be filed against them. If profile routing is unavailable it logs
   [Profile routing unavailable; starting the local session without profile metadata.](../../../../apps/stream-extend/src/routes/+page.svelte#L163) and still starts.
3. It then calls [`obs_start_stream_session`](../../../../apps/stream-extend/src/routes/+page.svelte#L165), which owns the recording.
4. While live the panel shows [`{streamStats.kbitsPerSec.toFixed(0)} kbps`](../../../../apps/stream-extend/src/routes/+page.svelte#L272),
   [`Skipped: {streamStats.skippedFrames}/{streamStats.totalFrames}`](../../../../apps/stream-extend/src/routes/+page.svelte#L273) and either
   [Recording for Creator Extend](../../../../apps/stream-extend/src/routes/+page.svelte#L274) or
   [External recording not owned](../../../../apps/stream-extend/src/routes/+page.svelte#L274).

   *Caption:* The live state showing bitrate, skipped frames and the Recording for Creator Extend line.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-04.png]

## Path 4 — Stop and send the recording to Creator Extend

1. The same button now reads [Stop + Send to Creator](../../../../apps/stream-extend/src/routes/+page.svelte#L266). Click it.

   *Caption:* The same button reading Stop + Send to Creator while a session is active.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-05.png]
2. The app calls [`obs_stop_stream_session`](../../../../apps/stream-extend/src/routes/+page.svelte#L155) and shows the result's detail in a status line
   ([`recording-message`](../../../../apps/stream-extend/src/routes/+page.svelte#L239)).

## Path 5 — Find the recording in Creator Extend

1. In Creator Extend click [Recordings](../../../../apps/creator-extend/src/routes/+page.svelte#L458). The inbox is headed
   [STREAM EXTEND → CREATOR EXTEND](../../../../apps/shared/ui/RecordingLibrary.svelte#L98) and
   [Recording inbox](../../../../apps/shared/ui/RecordingLibrary.svelte#L98).

   *Caption:* The Creator Extend Recording inbox listing a new recording with its source profile.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-06.png]
2. It says [Managed Stream Extend sessions arrive here as soon as OBS finalizes the local file.](../../../../apps/shared/ui/RecordingLibrary.svelte#L101)
   and that the video [is never uploaded automatically](../../../../apps/shared/ui/RecordingLibrary.svelte#L101). The list refreshes itself
   ([`setInterval(() => void refresh(), 4000)`](../../../../apps/shared/ui/RecordingLibrary.svelte#L27)).
3. Each recording shows its name, size and time, a status pill, and where it came from
   ([`From`](../../../../apps/shared/ui/RecordingLibrary.svelte#L119): the stream profile, Manual import, or an unknown stream profile). A
   [Content profile](../../../../apps/shared/ui/RecordingLibrary.svelte#L120) menu files it under one of your content profiles, or
   [Unassigned](../../../../apps/shared/ui/RecordingLibrary.svelte#L126).
4. If the file was moved the card says
   [The original file moved or was deleted. Locate it and add it again.](../../../../apps/shared/ui/RecordingLibrary.svelte#L131)

## Path 6 — Work a recording through its states

1. [Start editing](../../../../apps/shared/ui/RecordingLibrary.svelte#L133) marks it as being edited; [Show in folder](../../../../apps/shared/ui/RecordingLibrary.svelte#L134)
   reveals the file ([`recordings_reveal`](../../../../apps/shared/ui/RecordingLibrary.svelte#L85)).

   *Caption:* A recording card with the Start editing, Show in folder, Mark ready and Archive actions.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-07.png]
2. [Mark ready](../../../../apps/shared/ui/RecordingLibrary.svelte#L135), [Mark published](../../../../apps/shared/ui/RecordingLibrary.svelte#L136) and
   [Archive](../../../../apps/shared/ui/RecordingLibrary.svelte#L137) move it between `ready`, `editing`, `published` and `archived`
   ([`status: 'ready' | 'editing' | 'published' | 'archived'`](../../../../apps/shared/ui/RecordingLibrary.svelte#L11)). The status is a label you keep;
   nothing is published by it.
3. Archived recordings are hidden until you tick [Show archived](../../../../apps/shared/ui/RecordingLibrary.svelte#L108).

## Path 7 — Add a recording that did not come from Stream Extend

1. Click [Add existing recording](../../../../apps/shared/ui/RecordingLibrary.svelte#L106). A file dialog titled
   [Add a recording to Creator Extend](../../../../apps/shared/ui/RecordingLibrary.svelte#L52) offers
   [`['mkv', 'mp4', 'mov', 'webm', 'm4v', 'avi', 'ts']`](../../../../apps/shared/ui/RecordingLibrary.svelte#L53).

   *Caption:* The file dialog titled Add a recording to Creator Extend, filtered to video files.
   [screenshot: marketing/content-creator-wireframe/screenshots/stream-control-and-recording/step-08.png]
2. The app registers it ([`recordings_import`](../../../../apps/shared/ui/RecordingLibrary.svelte#L58)) and says
   [is ready in the recording inbox.](../../../../apps/shared/ui/RecordingLibrary.svelte#L61) The video stays where it was.
3. With nothing yet, the inbox says [No recordings yet.](../../../../apps/shared/ui/RecordingLibrary.svelte#L110)

## What this feature does not do

Nothing here has been run against a real live stream: the platform has not yet created an external stream, post or upload
(`ST-R15` in the [run lanes](../../../../docs/todo/README.md)). The button's name says what OBS is asked to do; whether a stream
reaches an audience depends on the stream key and destination configured in OBS itself. The inbox never uploads.
