# Posture Screen — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Where it lives: **Creator Extend → Dashboard → [Posture Screen](../../../../apps/creator-extend/src/routes/+page.svelte#L681)**, the
smallest of the built features and the one that shows the sports-analytics side of the platform. A local MediaPipe Pose model finds body
landmarks in a photo you pick. Nothing is uploaded: the analysis runs on your machine.

## Path 1 — Analyze a photo

1. Click [Dashboard](../../../../apps/creator-extend/src/routes/+page.svelte#L459) and find [Posture Screen](../../../../apps/creator-extend/src/routes/+page.svelte#L681):
   [Upload a front, side, or back photo to check body alignment.](../../../../apps/creator-extend/src/routes/+page.svelte#L682)
2. Choose the view with the radio buttons: [Front](../../../../apps/creator-extend/src/routes/+page.svelte#L687),
   [Side](../../../../apps/creator-extend/src/routes/+page.svelte#L691) or [Back](../../../../apps/creator-extend/src/routes/+page.svelte#L695).

   *Caption:* The Posture Screen panel with the Front, Side and Back choices and the Upload Photo button.
   [screenshot: marketing/content-creator-wireframe/screenshots/posture-screen/step-01.png]
3. Click [Upload Photo](../../../../apps/creator-extend/src/routes/+page.svelte#L700). The file dialog offers only
   [`extensions: ['png', 'jpg', 'jpeg']`](../../../../apps/creator-extend/src/routes/+page.svelte#L382); while it works the button reads
   [Analyzing…](../../../../apps/creator-extend/src/routes/+page.svelte#L700).
4. The app calls [`posture_analyze`](../../../../apps/creator-extend/src/routes/+page.svelte#L391) with the image path and the view. In Rust that is
   [`posture_analyze`](../../../../apps/creator-extend/src-tauri/src/lib.rs#L579), which runs the sports-analytics Python tool.

## Path 2 — Read the result

1. The photo appears with a purple dot on each landmark the model is at least 30% sure of
   ([`if (kp.v < 0.3) continue;`](../../../../apps/creator-extend/src/routes/+page.svelte#L416), drawn by
   [`drawPostureOverlay`](../../../../apps/creator-extend/src/routes/+page.svelte#L406)).

   *Caption:* An analyzed photo with a purple dot on each detected landmark.
   [screenshot: marketing/content-creator-wireframe/screenshots/posture-screen/step-02.png]
2. Below it a list of metrics, one row per measurement with underscores shown as spaces
   ([`key.replace(/_/g, ' ')`](../../../../apps/creator-extend/src/routes/+page.svelte#L723)). Front and back views measure
   [`shoulder_tilt_deg`](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L99) and
   [`hip_tilt_deg`](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L100); the side view measures
   [`forward_head_deg`](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L128) and
   [`trunk_lean_deg`](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L129).
3. Flags appear as a list with a severity ([`flag-{flag.severity}`](../../../../apps/creator-extend/src/routes/+page.svelte#L732)). The labels the tool can raise include
   [shoulders uneven](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L103),
   [hips uneven](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L106),
   [trunk shifted laterally](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L109),
   [forward head posture](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L132) and
   [trunk leaning off vertical](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L135).

   *Caption:* The metric rows and the flag list for the chosen view.
   [screenshot: marketing/content-creator-wireframe/screenshots/posture-screen/step-03.png]
4. With nothing to flag: [No alignment issues flagged.](../../../../apps/creator-extend/src/routes/+page.svelte#L736)

   *Caption:* The panel showing No alignment issues flagged.
   [screenshot: marketing/content-creator-wireframe/screenshots/posture-screen/step-04.png]

## Path 3 — When it does not work

1. If no person is found: [No person detected in photo.](../../../../apps/creator-extend/src/routes/+page.svelte#L397) Any other failure prints the error text
   under the button ([`posture-error`](../../../../apps/creator-extend/src/routes/+page.svelte#L704)).

   *Caption:* The panel showing No person detected in photo.
   [screenshot: marketing/content-creator-wireframe/screenshots/posture-screen/step-05.png]
2. If the Python dependencies are missing, run **Check packaged actions** in Creative Tools and use
   [Set up Posture Screen dependencies in Module setup](../../../../apps/creator-extend/src/routes/+page.svelte#L510)
   (see the [Blender and creative tools](../blender-stills/click-paths.md) path 2 and [setup](../setup-and-readiness/click-paths.md) path 3).

## What this feature does not do

It is a screening aid, not a diagnosis: the flags compare angles against fixed thresholds
(such as [`SHOULDER_TILT_WARN_DEG`](../../../../modules/sports-analytics/pose-estimation/posture_screen.py#L103)), and the photo's framing decides how well it
works. The golf tracer and swing analysis in the same module are command-line tools with no screen. See the
[AI actions inventory](../../../../docs/AI_ACTIONS_INVENTORY.md).
