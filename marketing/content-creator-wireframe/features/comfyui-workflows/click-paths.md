# ComfyUI workflows — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Creator Extend → Dashboard → [ComfyUI Workflows](../../../../apps/creator-extend/src/routes/+page.svelte#L569)**,
with the input editor [`Configure {workflowName}`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L89). It needs a running
ComfyUI that you start yourself; the app connects to it. See [setup and readiness](../setup-and-readiness/click-paths.md) for the
connection and the readiness check that unlocks this panel.

## Path 1 — Open the workflow list and pick a category

1. Click [Dashboard](../../../../apps/creator-extend/src/routes/+page.svelte#L459), then find
   [ComfyUI Workflows](../../../../apps/creator-extend/src/routes/+page.svelte#L569).
2. Until setup passes, the panel says
   [Workflow controls are locked until the current ComfyUI and committed-catalog checks pass](../../../../apps/creator-extend/src/routes/+page.svelte#L572).
   Once it does: [Run preflight on a workflow before Configure](../../../../apps/creator-extend/src/routes/+page.svelte#L574).

   *Caption:* The ComfyUI Workflows panel locked, with the message to run Check readiness first.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-01.png]
3. The list comes from [`comfyui_workflows`](../../../../apps/creator-extend/src/routes/+page.svelte#L142) (the workflows bundled with the app).
   Pick a category tab: [`const categories = ['all', 'inpaint', 'upscale', 'stylize', 'segment', 'video', 'realtime', 'general']`](../../../../apps/creator-extend/src/routes/+page.svelte#L429).
   An empty category reads [No workflows found](../../../../apps/creator-extend/src/routes/+page.svelte#L635).

   *Caption:* The workflow list with category tabs, each row showing a name, category and Preflight button.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-02.png]
4. If ComfyUI already has jobs waiting, the panel says
   [`Queue: {queueCount} pending`](../../../../apps/creator-extend/src/routes/+page.svelte#L590).

## Path 2 — Preflight a workflow

1. On a workflow row click [Preflight](../../../../apps/creator-extend/src/routes/+page.svelte#L625); once it has run the button reads
   [Recheck](../../../../apps/creator-extend/src/routes/+page.svelte#L625).
2. The app asks the live ComfyUI whether it has the nodes and models the workflow needs:
   [`comfyui_preflight`](../../../../apps/creator-extend/src/routes/+page.svelte#L164).
3. The row shows a ✓ or ⚠ summary ([`preflight.summary`](../../../../apps/creator-extend/src/routes/+page.svelte#L611)), the
   [Models found](../../../../apps/creator-extend/src/routes/+page.svelte#L614), and the GPU with free and total
   [VRAM](../../../../apps/creator-extend/src/routes/+page.svelte#L617). The header indicator picks up the same figures
   ([`comfyVram`](../../../../apps/creator-extend/src/routes/+page.svelte#L169)).

   *Caption:* A workflow row after preflight, showing the ready summary, models found and GPU with free VRAM.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-03.png]
4. If the check itself cannot finish the row says
   [Preflight could not complete](../../../../apps/creator-extend/src/routes/+page.svelte#L177).

   *Caption:* A workflow row whose preflight could not complete, showing the error summary.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-04.png]
5. [Configure](../../../../apps/creator-extend/src/routes/+page.svelte#L631) stays disabled until preflight reports the workflow
   compatible ([`!preflight?.compatible`](../../../../apps/creator-extend/src/routes/+page.svelte#L629)).

## Path 3 — Configure the inputs, and upload an image if the workflow needs one

1. Click [Configure](../../../../apps/creator-extend/src/routes/+page.svelte#L631). An editor opens under the list:
   [`Configure {workflowName}`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L89), with
   [Your saved workflow stays unchanged](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L90).

   *Caption:* The Configure editor open under the list, showing the prompt, seed and image fields.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-05.png]
2. It loads the editable fields ([`comfyui_workflow_inputs`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L23)) and where
   uploads go ([`comfyui_upload_target`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L24)). A field is a text prompt, a
   seed ([Seeds must be whole numbers from 0 to 9007199254740991.](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L72)),
   or the name of an image or mask.
3. For an image or mask, type the name of a file that is already there
   ([Image already in ComfyUI's input folder](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L108)) or choose
   [Upload an image or mask (PNG, JPEG, WebP; up to 10 MiB)](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L110).
   The upload calls [`comfyui_upload_image`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L51) and confirms with
   [`Uploaded ${file.name}`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L54).

   *Caption:* An image field with the upload control, and the upload confirmation after choosing a file.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-06.png]
4. The editor says where files go: [Images upload to your configured ComfyUI server at](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L95),
   and that [Uploading does not start a job](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L95).
5. With ComfyUI disconnected it says
   [Connect ComfyUI before uploading an image or running this workflow.](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L122)
   [Close](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L125) leaves without running anything.

## Path 4 — Run it and watch the status

1. Click [Run with these inputs](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L124). It queues the job with
   [`comfyui_queue_configured`](../../../../apps/creator-extend/src/lib/WorkflowInputs.svelte#L78).
2. The editor closes ([`workflowQueued`](../../../../apps/creator-extend/src/routes/+page.svelte#L185)) and the row's badge follows the job:
   [Queueing…](../../../../apps/creator-extend/src/routes/+page.svelte#L603), [Running…](../../../../apps/creator-extend/src/routes/+page.svelte#L604),
   then [✓ Done](../../../../apps/creator-extend/src/routes/+page.svelte#L605).

   *Caption:* The workflow row badge reading Running while the job executes.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-07.png]
3. The app asks ComfyUI for the job's state ([`comfyui_prompt_status`](../../../../apps/creator-extend/src/routes/+page.svelte#L212)) every
   [1500](../../../../apps/creator-extend/src/routes/+page.svelte#L238) milliseconds until it completes.
4. A failure shows on the row as [`✗ ${run.message ?? 'Failed'}`](../../../../apps/creator-extend/src/routes/+page.svelte#L606).

## Path 5 — Read the output history

1. Scroll to [Output history](../../../../apps/creator-extend/src/routes/+page.svelte#L649). It says
   [Up to four bounded previews](../../../../apps/creator-extend/src/routes/+page.svelte#L650) are loaded from the ComfyUI server.
2. Each finished job is an entry with the workflow name, the status, the time and
   [`Prompt {entry.promptId}`](../../../../apps/creator-extend/src/routes/+page.svelte#L657). At most four previews are fetched per job
   ([`outputs.slice(0, 4)`](../../../../apps/creator-extend/src/routes/+page.svelte#L194), via
   [`comfyui_output_preview`](../../../../apps/creator-extend/src/routes/+page.svelte#L196)). If none is an image or video it says
   [The workflow completed without a supported image or video preview.](../../../../apps/creator-extend/src/routes/+page.svelte#L671)

   *Caption:* The Output history with a finished entry and its image preview.
   [screenshot: marketing/content-creator-wireframe/screenshots/comfyui-workflows/step-08.png]
3. The history keeps the latest twenty entries ([`.slice(0, 20)`](../../../../apps/creator-extend/src/routes/+page.svelte#L206)).
   [Clear history](../../../../apps/creator-extend/src/routes/+page.svelte#L652) empties it. Before anything has run:
   [Run a configured workflow to see its completion and output here.](../../../../apps/creator-extend/src/routes/+page.svelte#L675)

## What this feature does not do (so a conversation does not promise it)

The app queues the workflow and shows the result ComfyUI returns; it does not install ComfyUI or its models, and preflight
[reports VRAM without estimating output quality](../../../../apps/creator-extend/src/routes/+page.svelte#L574). The three realtime
workflows and the eight image and video workflows are bundled; the remaining realtime ones are not built
(see the [AI actions inventory](../../../../docs/AI_ACTIONS_INVENTORY.md)).
