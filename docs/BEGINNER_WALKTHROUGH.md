# First private recording — narration, glossary and recovery FAQ

> **Status:** Reviewable draft · **Last reviewed:** 2026-10-08 · **Owner:** OpenTechnology14

**Enforcement: reference.** P-071 T1/T2 source material. This is a spoken-script/transcript
draft, not captured footage or an approved publication. No source screen or hardware test is
invented. Narration timing is an estimate until rehearsal. The current parent task completed
the integrated source review; no Terra execution is claimed.

Sources: [beginner website](public/index.html#start), [capture setup](../modules/creator-experience/setup/manual.md),
[audio setup](../modules/audio-production/setup/manual.md), and [Shorts boundaries](../modules/content-creation/stream_shorts/README.md).
Keep the setup guides authoritative; this artifact teaches one small task.

## Recording storyboard and transcript

Target: someone who has never streamed. Outcome: one saved private recording they have
watched and heard. Requires OBS, a harmless window to capture, disk space and optionally a mic.
No streaming account, Docker, AI model, external capture card or cloud service is required for
this window-capture exercise. OS/version-specific labels and permissions need rehearsal.

### 1 — Opening and starting state

**Screen cue:** OBS open, off air, with no personal desktop information visible. Show the
Sources and Audio Mixer areas. Capture state: not demonstrated yet.

**Narration:**

Today we'll make a short private recording and watch it back. You don't need a streaming
account for this. The goal is simple: save a file that contains the picture and sound you
intended. Once that works, you're in a much better position to add a camera, effects or a
live audience.

OBS is the program that captures your picture and sound. We'll use it directly for this
practice run. The platform adds controls and workflows around it, but the first useful
check is whether OBS can save a recording you can actually watch.

Before we start, close any private messages or notifications that could appear in the test
window. Use something harmless, such as a sample document. We're preparing a private test,
and the Start Streaming button is a separate action we don't need for this exercise.

**Screenshot caption / alt text:** OBS before the test, with Sources and Audio Mixer visible;
the recording and streaming controls are idle.

### 2 — Choose the picture

**Screen cue:** Show the current scene, then Sources → add. Select the capture option for
the test window. Confirm the preview. Capture state: not demonstrated yet.

**Narration:**

A scene is a layout. A source is one thing inside that layout, such as a window or camera.
Think of the scene as a small stage and the sources as the things you place on it.

In Sources, use the add control and choose the capture option for your test window.
The exact options depend on your operating system. Choose the window you meant to show,
then look at the preview before doing anything else.

You should see the sample window, with no private desktop material around it. If the
picture is black, pause here. Confirm that you selected the correct source and check your
operating system's screen-recording permission. After changing one setting, look at the
preview again. Adding effects won't fix a source that isn't capturing the right picture.

**Screenshot caption / alt text:** A sample window appears in the OBS preview after its
capture source has been selected.

### 3 — Check the sound

**Screen cue:** Speak one sentence and show the intended microphone meter. Check mute.
Use headphones. Capture state: not demonstrated yet.

**Narration:**

If you want narration, speak into the microphone and watch its meter in the Audio Mixer.
A moving meter tells you OBS is receiving something. It doesn't yet prove that the saved
recording will contain the sound you want; we'll check the actual file in a moment.

Make sure the intended source isn't muted. If you want application or game audio, check
that source separately. Try to capture each device once. Capturing the same sound twice
can create an echo, and speakers feeding back into the microphone can do the same thing.

Headphones make this easier. Keep the setup small for the first test. More audio buses,
voice effects and virtual cables can wait until a simple recording sounds right.

**Screenshot caption / alt text:** The intended microphone meter responds to speech and
its mute control is off; unrelated sources are not part of this test.

### 4 — Record, stop and inspect

**Screen cue:** Settings → Output, show a sample recording folder without a private path.
Start Recording, speak a sentence, move the test window, then Stop Recording after about
20 seconds. Open the new file in a player. Capture state: not demonstrated yet.

**Narration:**

Choose a recording folder you can find again. Check that you have free disk space, then
press Start Recording. Speak a sentence and move something in the test window so the
recording contains an obvious picture-and-sound check. After about twenty seconds, press
Stop Recording.

Now open the actual saved file. Listen to the sentence and watch the movement. Does the
picture show what you intended? Is the speech understandable? Does the sound match what
you see? This replay is the useful proof. A preview or moving meter alone isn't enough.

If the file is silent or doubled, change one audio setting and make another short test.
If the file is missing, check the selected folder and disk space. Keep the original when
converting recording formats. OBS can remux MKV to MP4 when the next tool needs MP4; check
the converted file before relying on it.

You now have a clear starting point: a private recording you've watched and heard. Next,
choose one moment you want to turn into a clip. The current local Shorts tool has a review
and command-line render path; the full desktop inbox-to-editor handoff is still being
connected. We'll keep that distinction clear as the combined app develops.

**Screenshot caption / alt text:** The saved recording plays in a local player, showing the
sample window and its intended audio. This caption must accompany real capture, not a mockup.

## Beginner glossary

| Term | Plain-language meaning | Example |
|---|---|---|
| Scene | A layout containing the things viewers see or hear | A game view with a small camera in the corner |
| Source | One picture or sound input inside a scene | A window, camera or microphone |
| Capture | Bringing an input into the recording program | Showing a selected window in OBS |
| Preview | A view of what the program is preparing to show | Checking a camera's framing before recording |
| Audio meter | A moving indicator of incoming sound level | A microphone meter moves when you speak |
| Mute | Stop a selected sound source from being heard | Mute an unused microphone source |
| Monitoring | Listening to an audio source while working | Headphones let you hear the selected source |
| Recording | A saved picture-and-sound file | A private twenty-second test |
| Stream | Sending a broadcast to a live destination | Going live requires additional account and destination checks |
| Remux | Change the container around encoded media | Convert an OBS MKV recording to MP4 without a new edit |
| Profile | A saved set of settings or identity choices | Stream and Content profiles keep separate selections |
| Inbox | A list of recordings available for later work | Creator Extend's Recordings view |
| Clip | A selected part of a longer recording | One thirty-second moment |
| Render / export | Produce the output file from an editing plan | The Shorts CLI writes a reviewed interval as MP4 |
| Optional setup | A tool needed for an extra capability | AI effects are optional for a basic OBS window recording |

## Recovery FAQ

| Symptom | Next action | Expected result | Reference / escalation |
|---|---|---|---|
| Black window preview | Confirm the chosen source/window and OS capture permission; retry one change at a time | The intended window appears before recording | Capture setup; report OS/version and source type if still blank |
| Camera missing | Confirm the device connection and camera permission; close another app using it, then retry | The intended camera becomes selectable | Capture setup; do not install unrelated AI tools to fix device discovery |
| Silent recording | Play the saved file, then check the intended microphone/device and mute setting | A second short recording contains the intended sound | Audio setup; include the source and observed meter behavior |
| Echo or doubled audio | Use headphones and check that each device is captured once | The new recording has one audible path | Audio setup; advanced routing remains a separate task |
| Missing recording file | Check the selected output folder, disk space and OBS error message | A new file appears after Stop Recording | Capture setup; preserve error details without sharing secrets |
| MP4 required but recording is MKV | Remux a copy, then play and inspect it | The MP4 contains the same picture and sound | Capture setup; retain the original until verification |
| Many missing optional tools | Return to the task-specific prerequisites before installing more | Basic recording can proceed without irrelevant tools | Beginner site; current prototypes expose more setup than the planned shell |
| Start editing did not open an editor | Check the current inbox/Shorts instructions | You understand the existing metadata marker and CLI review/render path | Shorts reference; the desktop adapter remains implementation work |

## Rehearsal and publication record

- Timed rehearsal, OS/build and source labels: pending.
- Captured screenshot/video paths and device evidence: pending.
- Captions/transcript alignment and keyboard-only review: pending capture.
- Operator/factual review and publication destination: pending; no upload is authorized here.
- Engineering companion: canonical source links above, verification matrix and release audit.

The text can be read as a transcript without watching footage. Any future image needs the
specified alt text, and any concept image must remain labelled Concept. A rehearsal finding
updates the canonical setup guide first, then this artifact and the public-site copy.
