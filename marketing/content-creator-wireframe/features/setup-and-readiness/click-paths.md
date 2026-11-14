# Setup and readiness — click paths

> **Evidence:** read from the code on `main`. The apps were not launched, so treat each step as **Inferred** until
> someone follows it once. Every link below is re-checked against the code by `tests/docs/test_wireframe_refs.py`.

Both desktop apps open on **Module setup**: [`activeView = $state('setup')`](../../../../apps/creator-extend/src/routes/+page.svelte#L7)
in Creator Extend and [`activeView = $state('setup')`](../../../../apps/stream-extend/src/routes/+page.svelte#L7) in Stream Extend. It is
one shared panel, [Module setup](../../../../apps/shared/ui/ModuleSetup.svelte#L404), mounted with
[`productKind="creator"`](../../../../apps/creator-extend/src/routes/+page.svelte#L462) or
[`productKind="stream"`](../../../../apps/stream-extend/src/routes/+page.svelte#L202). There are no URL routes: a "page"
here is a tab.

## Path 1 — Choose the tools you need

1. Open either app. It lands on **Module setup**, headed [Choose the tools you need](../../../../apps/shared/ui/ModuleSetup.svelte#L407):
   [Choose modules individually or start with a profile](../../../../apps/shared/ui/ModuleSetup.svelte#L408).
   Your selections are saved on this device.

   *Caption:* Module setup on first launch, headed Choose the tools you need, with the starter-profile buttons and module grid.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-01.png]
2. Click a starter profile, [`Add {title(id)}`](../../../../apps/shared/ui/ModuleSetup.svelte#L416). There is one button per
   profile in the catalog; it adds that profile's modules to what you already chose.
3. Or tick modules one by one in the grid under [`Modules · {selected.length} chosen`](../../../../apps/shared/ui/ModuleSetup.svelte#L420).
   A module that another one needs is ticked for you and marked
   [Required dependency](../../../../apps/shared/ui/ModuleSetup.svelte#L426); it cannot be unticked while its dependent stays chosen.

   *Caption:* The module grid with several modules ticked and one marked Required dependency.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-02.png]
4. Each module's line says what is left to do: [Python dependencies + manual setup](../../../../apps/shared/ui/ModuleSetup.svelte#L426)
   or [Manual setup](../../../../apps/shared/ui/ModuleSetup.svelte#L426).
5. The choice is saved by [`choose`](../../../../apps/shared/ui/ModuleSetup.svelte#L146).

## Path 2 — Install the prerequisites

1. Under the grid, the [Python 3.12](../../../../apps/shared/ui/ModuleSetup.svelte#L434) card says whether Python is installed and
   where. If it is missing, [Install Python 3.12](../../../../apps/shared/ui/ModuleSetup.svelte#L440) is offered when the app can
   install it; [Recheck Python](../../../../apps/shared/ui/ModuleSetup.svelte#L442) re-reads the state.

   *Caption:* The Python 3.12 card showing Python is missing, with Install Python 3.12 offered.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-03.png]
2. [FFmpeg](../../../../apps/shared/ui/ModuleSetup.svelte#L449) gets the same treatment, with
   [Recheck FFmpeg](../../../../apps/shared/ui/ModuleSetup.svelte#L457).
3. [OBS Studio](../../../../apps/shared/ui/ModuleSetup.svelte#L464): [Open OBS Studio](../../../../apps/shared/ui/ModuleSetup.svelte#L483),
   [Recheck OBS](../../../../apps/shared/ui/ModuleSetup.svelte#L485), [Test WebSocket](../../../../apps/shared/ui/ModuleSetup.svelte#L487)
   and, outside the preview, [Run OBS recording test (3s)](../../../../apps/shared/ui/ModuleSetup.svelte#L490). A collapsed
   [`Preview {obsPlan.name}`](../../../../apps/shared/ui/ModuleSetup.svelte#L474) shows the scene collection the app would import.

   *Caption:* The OBS Studio card with Open OBS Studio, Recheck OBS and Test WebSocket.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-04.png]
4. [Docker-backed local services](../../../../apps/shared/ui/ModuleSetup.svelte#L498): [Open Docker Desktop](../../../../apps/shared/ui/ModuleSetup.svelte#L519),
   [Recheck Docker](../../../../apps/shared/ui/ModuleSetup.svelte#L521), [Start selected local services](../../../../apps/shared/ui/ModuleSetup.svelte#L523),
   then [Initialize data & workflows](../../../../apps/shared/ui/ModuleSetup.svelte#L525) once Postgres, MinIO or n8n are in the plan.
5. How installs happen is stated on the page: [winget on Windows or an existing Homebrew on macOS](../../../../apps/shared/ui/ModuleSetup.svelte#L535),
   and [they do not create cloud resources](../../../../apps/shared/ui/ModuleSetup.svelte#L535).

## Path 3 — Install the Python modules and check readiness

1. [Install selected Python dependencies](../../../../apps/shared/ui/ModuleSetup.svelte#L532) is enabled once modules are chosen and
   Python is found. It [downloads Python packages into shared local environments](../../../../apps/shared/ui/ModuleSetup.svelte#L535).
2. Progress shows under [Installation progress](../../../../apps/shared/ui/ModuleSetup.svelte#L603); a
   [Local installation log](../../../../apps/shared/ui/ModuleSetup.svelte#L634) block gives the log path.

   *Caption:* The Installation progress panel while Python dependencies install, with the local log path.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-05.png]
3. Click [Check readiness](../../../../apps/shared/ui/ModuleSetup.svelte#L533). The
   [Capability readiness](../../../../apps/shared/ui/ModuleSetup.svelte#L538) list fills in: each capability shows its label, a status
   word such as [Action required](../../../../apps/shared/ui/ModuleSetup.svelte#L400), and a summary. With nothing recorded it says
   [No service evidence has been recorded. Run Check readiness.](../../../../apps/shared/ui/ModuleSetup.svelte#L543)
   [Verification evidence](../../../../apps/shared/ui/ModuleSetup.svelte#L544) expands to the individual checks.

   *Caption:* Capability readiness after Check readiness, showing a mix of passed and action-required statuses.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-06.png]
4. Other tabs read the same snapshot. Creator Extend unlocks ComfyUI workflows from the `comfy-workflows` capability
   ([`canRunWorkflows`](../../../../apps/creator-extend/src/routes/+page.svelte#L57)); Stream Extend unlocks OBS control from `obs-control`
   ([`canObsControl`](../../../../apps/stream-extend/src/routes/+page.svelte#L46)). Until then they say
   [Workflow controls are locked until the current ComfyUI and committed-catalog checks pass](../../../../apps/creator-extend/src/routes/+page.svelte#L572)
   and [OBS controls are locked until the current WebSocket and scene checks pass](../../../../apps/stream-extend/src/routes/+page.svelte#L243).

## Path 4 — Point the app at your services (Connections)

1. Click [Connections](../../../../apps/creator-extend/src/routes/+page.svelte#L455) in Creator Extend or
   [Connections](../../../../apps/stream-extend/src/routes/+page.svelte#L195) in Stream Extend.
2. Creator Extend shows [Connection settings](../../../../apps/creator-extend/src/routes/+page.svelte#L465): the
   [ComfyUI URL](../../../../apps/creator-extend/src/routes/+page.svelte#L470), the MinIO endpoint and keys (keys go to the operating
   system credential manager and are [never displayed after saving](../../../../apps/creator-extend/src/routes/+page.svelte#L466)),
   Blender and Krita paths that default to [Auto-detect](../../../../apps/creator-extend/src/routes/+page.svelte#L476), and the Platform API URL.
   Then [Save settings](../../../../apps/creator-extend/src/routes/+page.svelte#L481) or
   [Save and test ComfyUI](../../../../apps/creator-extend/src/routes/+page.svelte#L482).

   *Caption:* Creator Extend Connection settings with the ComfyUI URL field and the two save buttons.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-07.png]
3. Stream Extend shows [Connection settings](../../../../apps/stream-extend/src/routes/+page.svelte#L205): the
   [OBS host](../../../../apps/stream-extend/src/routes/+page.svelte#L210), [OBS WebSocket port](../../../../apps/stream-extend/src/routes/+page.svelte#L211),
   a [New OBS password](../../../../apps/stream-extend/src/routes/+page.svelte#L212) (stored in the credential manager), and the ComfyUI,
   Grafana and Platform API URLs. Then [Save settings](../../../../apps/stream-extend/src/routes/+page.svelte#L219) or
   [Save and test OBS](../../../../apps/stream-extend/src/routes/+page.svelte#L220). The result reads
   [Saved and connected to OBS.](../../../../apps/stream-extend/src/routes/+page.svelte#L106) or
   [Saved. OBS did not answer yet; check OBS WebSocket settings and retry.](../../../../apps/stream-extend/src/routes/+page.svelte#L107)

   *Caption:* Stream Extend Connection settings with Save and test OBS and its result message.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-08.png]
4. The header shows live status: [`ComfyUI {comfyConnected ? 'Connected' : 'Disconnected'}`](../../../../apps/creator-extend/src/routes/+page.svelte#L445)
   and [`OBS {obsConnected ? 'Connected' : obsConnecting ? 'Connecting…' : 'Disconnected'}`](../../../../apps/stream-extend/src/routes/+page.svelte#L187),
   the latter refreshed every two seconds by [`setInterval(refreshStatus, 2000)`](../../../../apps/stream-extend/src/routes/+page.svelte#L60).

## Path 5 — Find your capture hardware

1. In Module setup find [Capture hardware](../../../../apps/shared/ui/ModuleSetup.svelte#L553) and click
   [Scan capture hardware](../../../../apps/shared/ui/ModuleSetup.svelte#L554). It looks for cameras, capture cards and audio inputs
   [without opening a recording stream](../../../../apps/shared/ui/ModuleSetup.svelte#L553).
2. The result is stamped with the scan time and ends [Ready for OBS setup](../../../../apps/shared/ui/ModuleSetup.svelte#L557) or Action required.

   *Caption:* The capture hardware scan result, stamped with the scan time and ending Ready for OBS setup.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-09.png]
3. Choose the inputs, then [Save capture choices](../../../../apps/shared/ui/ModuleSetup.svelte#L579) and
   [Test selected capture (3s)](../../../../apps/shared/ui/ModuleSetup.svelte#L580). The
   [Capture test result](../../../../apps/shared/ui/ModuleSetup.svelte#L583) reports detected, signal, recording and accepted stages.

   *Caption:* The capture test result showing the detected, signal, recording and accepted stages.
   [screenshot: marketing/content-creator-wireframe/screenshots/setup-and-readiness/step-10.png]
