# Personalities: prompt and voice preview — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Stream Extend → [Automated streaming](../../../../apps/stream-extend/src/routes/+page.svelte#L198) → scroll to
[Personalities](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L111)**. It writes a persona's prompt and
catchphrases with a local Ollama model, turns the phrases into audio with an installed operating-system voice, and walks a person through reviewing
them. The panel's own promise: [Nothing is approved or put on air automatically.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L111)

## Path 1 — Load the personalities and pick one

1. Click [Load personalities](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L115).
2. Choose one in the [Personality](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L117) menu.

   *Caption:* The Personalities panel with the Personality menu after Load personalities.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-01.png]
3. If the session already has a personality the panel says
   [Authoring another personality does not switch the on-air session.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L120)

## Path 2 — Generate a reviewable prompt

1. Type the name of an installed model in
   [Local Ollama model (required for AI phrase generation)](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L130), and optionally an
   [Installed OS voice (blank = configured/default)](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L131).
2. Click [Generate personality prompt](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L128).
3. A [Reviewable authoring prompt](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L133) appears in an editable box, with
   [Phrase candidates](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L134), each assigned to one of the persona's reactions
   ([`Reaction {index + 1}`](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L136)).

   *Caption:* The generated Reviewable authoring prompt with the Phrase candidates list.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-02.png]

## Path 3 — Edit, save a revision, record feedback

1. Edit the prompt and the phrases. Add a note in
   [Revision feedback / improvement request](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L138).
2. [Save as new revision](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L140) keeps the earlier one;
   [Record feedback](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L141) stores the note.

   *Caption:* The revision controls: Save as new revision, Record feedback and the Saved revision menu.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-03.png]
3. Switch between revisions with [Saved revision](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L124).

## Path 4 — Render the phrases to audio

1. [Render saved phrases](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L142) makes audio from the text you saved.
   [Generate AI phrases + audio](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L143) first asks the local model for new phrases
   (it needs a model name).

   *Caption:* The audio clips rendered from the saved phrases, with durations and file paths.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-04.png]
2. While it works, [Cancel preview](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L144) stops it.

## Path 5 — Audition, review and approve

1. Tick [Audition output is isolated from the program mix. OBS must be connected and off air.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L148)
   The audition buttons stay disabled until you do.

   *Caption:* The audition checkbox and the Audition buttons, with the OBS-off-air condition stated.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-05.png]
2. Click [`Audition {index + 1}`](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L150) for each clip; [Stop audition](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L152)
   ends playback.
3. Tick [I reviewed this exact prompt, phrases, voice, and every audio sample.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L153)
   Then [Approve revision](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L154), or
   [Reject revision (keep history)](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L155).

   *Caption:* The review checkbox with Approve revision and Reject revision (keep history).
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-06.png]

## Path 6 — Map the clips to hotkeys and select the revision for production

1. Under [Production selection · next worker/session start](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L157), import the WAV files into OBS
   Soundbox as the text says, then enter each [Clip {index + 1} hotkey](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L159) and the
   [Stop All hotkey](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L160).

   *Caption:* The Production selection form with a hotkey field per clip and the Stop All hotkey.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-07.png]
2. Tick [I tested the clip-to-hotkey mapping, levels, and emergency stop in OBS.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L161)
3. Click [Select approved revision](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L162). It
   [does not start a stream or update a running director](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L158): the choice applies at the next
   worker or session start. Beside it: [Disable saved phrases](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L162) and
   [Export runtime manifest](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L162).
4. [Revision history & feedback](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L165) shows the parent revision and how to roll back.

## Path 7 — Run a scripted show with audience questions

1. Open [Scripted show · operator-controlled playback](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L173). Paste a
   [Reviewed script](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L175) and the
   [Episode brief / permitted source material](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L176), name a model for Q&A, and tick
   [I approve the script and source material.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L178)

   *Caption:* The Scripted show section with the script and episode brief boxes and the approval checkbox.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-08.png]
2. Click [Load approved script](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L179). Confirm that
   [OS speech output is routed to the intended AI-VOICE bus; no competing speech worker is running.](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L180)
3. [Play / resume](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L182) starts it; [Pause at next boundary](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L182)
   waits for the end of the current segment; [Stop voice now](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L182) cuts it off.
4. At a pause, type [One audience question per pause](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L183) and click
   [Draft source-grounded answer](../../../../apps/stream-extend/src/lib/PersonalityVoicePreview.svelte#L184). The answer is a draft built from your episode brief; you
   decide whether it is spoken.

   *Caption:* A drafted source-grounded answer to an audience question at a pause.
   [screenshot: marketing/content-creator-wireframe/screenshots/personalities-and-voice/step-09.png]

## What this feature does not do (so a conversation does not promise it)

The prompt and phrases are drafted by a local model you run; nothing leaves the machine, and nothing is approved for you. A real prompt and
real audio have not yet been approved by the owner (`P-066`), and the reaction audio has not been proven in OBS or on Windows. A local text-to-speech
stack with a provider choice is proposed, not built (`P-068`). See the [AI actions inventory](../../../../docs/AI_ACTIONS_INVENTORY.md).
