# Blender stills and creative tools — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Creator Extend → Dashboard → [Creative Tools](../../../../apps/creator-extend/src/routes/+page.svelte#L495)**.
The still-render job is an owned local process with a lifecycle (plan, render, watch, cancel, retry); it renders PNG stills only and
uploads nothing. The Blender and Krita executables come from [Connections](../setup-and-readiness/click-paths.md) (blank means auto-detect).

## Path 1 — Open Blender or Krita

1. Click [Dashboard](../../../../apps/creator-extend/src/routes/+page.svelte#L459). The Creative Tools panel shows a grid of cards:
   [3D + Motion Graphics](../../../../apps/creator-extend/src/routes/+page.svelte#L517) (Blender) and
   [AI Image Editing](../../../../apps/creator-extend/src/routes/+page.svelte#L522) (Krita).

   *Caption:* The Creative Tools panel with the Blender, Krita and package-check cards.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-01.png]
2. Click a card. Blender opens through [`blender_open`](../../../../apps/creator-extend/src/routes/+page.svelte#L243) and Krita through
   [`krita_open`](../../../../apps/creator-extend/src/routes/+page.svelte#L251). Nothing is passed: they open empty. A failure is logged,
   not shown on the card.

## Path 2 — Check that the packaged actions are ready

1. Click [Check packaged actions](../../../../apps/creator-extend/src/routes/+page.svelte#L498). The panel's hint begins
   [The package checks below run each bundled script with](../../../../apps/creator-extend/src/routes/+page.svelte#L496) `--help`; the checks do not touch project files
   or start a service.
2. The app asks for each tool's status ([`creator_tool_status`](../../../../apps/creator-extend/src/routes/+page.svelte#L268)) and lists one line per
   tool under [Creator tool readiness](../../../../apps/creator-extend/src/routes/+page.svelte#L501), ticked or flagged.

   *Caption:* The Creator tool readiness list after Check packaged actions, one ticked or flagged line per tool.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-02.png]
3. The two package cards, [Check ComfyUI + SDXL action](../../../../apps/creator-extend/src/routes/+page.svelte#L527) and
   [Check IPAdapter action](../../../../apps/creator-extend/src/routes/+page.svelte#L532), run the same check.
4. If the Posture Screen's dependencies are missing, a shortcut appears:
   [Set up Posture Screen dependencies in Module setup](../../../../apps/creator-extend/src/routes/+page.svelte#L510).

## Path 3 — Plan a batch render

1. Click [Plan Blender batch render](../../../../apps/creator-extend/src/routes/+page.svelte#L536).
2. Choose a project in the file dialog, which only offers [`extensions: ['blend']`](../../../../apps/creator-extend/src/routes/+page.svelte#L279), then choose an
   output folder ([`directory: true`](../../../../apps/creator-extend/src/routes/+page.svelte#L282)).
3. The app runs Blender as a dry run ([`blender_batch_render`](../../../../apps/creator-extend/src/routes/+page.svelte#L292),
   [`dryRun: true`](../../../../apps/creator-extend/src/routes/+page.svelte#L295)) and reads the scene list from the line that starts
   [`HCP_JOB `](../../../../apps/creator-extend/src/routes/+page.svelte#L297). If there is none it stops with
   [Blender returned no verified scene inventory.](../../../../apps/creator-extend/src/routes/+page.svelte#L298)

   *Caption:* The Blender batch render plan shown after the dry run, with the scene checkbox list.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-03.png]
4. The raw plan is shown in a preformatted block under the button ([`tool-plan`](../../../../apps/creator-extend/src/routes/+page.svelte#L549)).

## Path 4 — Choose scenes and render

1. A checkbox list appears under the legend [Select up to 16 scenes for local PNG stills](../../../../apps/creator-extend/src/routes/+page.svelte#L539).
2. Click [Render selected scenes](../../../../apps/creator-extend/src/routes/+page.svelte#L545). It stays disabled with no scene ticked or more than sixteen
   ([`blenderSelection.length > 16`](../../../../apps/creator-extend/src/routes/+page.svelte#L544)).
3. A confirmation asks you to approve it:
   [Render the selected scenes as local PNG stills in a new attempt folder?](../../../../apps/creator-extend/src/routes/+page.svelte#L310) It also says to run it
   [as an off-air batch task](../../../../apps/creator-extend/src/routes/+page.svelte#L310) and that [No upload occurs](../../../../apps/creator-extend/src/routes/+page.svelte#L310).

   *Caption:* The confirmation dialog asking to render the selected scenes as local PNG stills.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-04.png]
4. On OK the app starts the job ([`blender_job_start`](../../../../apps/creator-extend/src/routes/+page.svelte#L314)) and refreshes the job list
   ([`blender_job_list`](../../../../apps/creator-extend/src/routes/+page.svelte#L329)).

## Path 5 — Watch the job, cancel it, or retry what did not finish

1. Each job shows [`Blender job {job.job_id.slice(0, 8)}: {job.status}`](../../../../apps/creator-extend/src/routes/+page.svelte#L552), a line per scene with its status
   and any error, and [Local outputs](../../../../apps/creator-extend/src/routes/+page.svelte#L554). The app asks for the job's state every second
   ([`setInterval(pollBlenderJob, 1000)`](../../../../apps/creator-extend/src/routes/+page.svelte#L91), [`blender_job_status`](../../../../apps/creator-extend/src/routes/+page.svelte#L338)).

   *Caption:* A Blender job card with per-scene statuses, local outputs and the Cancel owned job button.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-05.png]
2. While this app owns the worker process, [Cancel owned job](../../../../apps/creator-extend/src/routes/+page.svelte#L556) stops it
   ([`blender_job_cancel`](../../../../apps/creator-extend/src/routes/+page.svelte#L346)).
3. After a failed, cancelled or interrupted job, [Retry unfinished scenes](../../../../apps/creator-extend/src/routes/+page.svelte#L557) is offered. It confirms
   with [Retry only unfinished scenes as a new local attempt? Previous outputs are preserved.](../../../../apps/creator-extend/src/routes/+page.svelte#L352),
   or, for an interrupted job, asks you to confirm you have stopped the old worker
   ([`This app cannot claim the old worker`](../../../../apps/creator-extend/src/routes/+page.svelte#L352)), then calls
   [`blender_job_retry`](../../../../apps/creator-extend/src/routes/+page.svelte#L354).

   *Caption:* A failed or cancelled job card offering Retry unfinished scenes.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-06.png]

## Path 6 — Prepare the Blender add-on

1. Click [Prepare Blender addon package](../../../../apps/creator-extend/src/routes/+page.svelte#L561). The app builds a ZIP
   ([`creator_tool_archive_blender_addon`](../../../../apps/creator-extend/src/routes/+page.svelte#L362)).
2. The page prints where it is and what to do next:
   [Install this ZIP from Blender Add-ons → Install](../../../../apps/creator-extend/src/routes/+page.svelte#L564).

   *Caption:* The Prepare Blender addon package result giving the ZIP path and the install instruction.
   [screenshot: marketing/content-creator-wireframe/screenshots/blender-stills/step-07.png]

## What this feature does not do

It renders **stills** from a project you choose, locally. It does not render animation, upload anywhere, or run on a schedule; the
confirmation says so. For where this sits in the proposal queue see the [AI actions inventory](../../../../docs/AI_ACTIONS_INVENTORY.md)
(it is not an AI action) and `P-061` in [`docs/PROPOSALS.md`](../../../../docs/PROPOSALS.md).
