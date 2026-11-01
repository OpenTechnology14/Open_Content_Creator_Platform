<script lang="ts">
  import ModuleSetup from '../../../shared/ui/ModuleSetup.svelte';
  import ProfileSwitcher from '../../../shared/ui/ProfileSwitcher.svelte';
  import RecordingLibrary from '../../../shared/ui/RecordingLibrary.svelte';
  import RemoteControl from '../../../shared/ui/RemoteControl.svelte';
  import SocialManagement from '../../../shared/ui/SocialManagement.svelte';
  let activeView = $state('setup');
  import { invoke, convertFileSrc } from '@tauri-apps/api/core';
  import { open as openExternal } from '@tauri-apps/plugin-shell';
  import { open as openDialog } from '@tauri-apps/plugin-dialog';
  import { onMount } from 'svelte';
  import WorkflowInputs from '$lib/WorkflowInputs.svelte';
  type ReadinessSnapshot = { capabilities: { capability_id: string; status: string; summary: string }[] };
  type PromptOutput = { node_id: string; filename: string; subfolder: string; folder_type: string };
  type OutputPreview = { data_url: string; media_type: string };
  type WorkflowRun = { status: string; message?: string };
  type ToolCheck = {
    id: string; label: string; packaged: boolean; interpreter: string | null;
    ready: boolean; detail: string;
  };
  type WorkflowPreflight = {
    connected: boolean; compatible: boolean; gpu_name: string | null;
    vram_total_mb: number | null; vram_free_mb: number | null;
    missing_nodes: string[]; missing_models: string[]; checked_models: string[];
    unchecked_models: string[]; summary: string;
  };
  type HistoryEntry = {
    promptId: string; workflowPath: string; workflowName: string; finishedAt: string;
    status: 'success' | 'error'; message?: string;
    previews: (OutputPreview & { filename: string })[];
  };
  let editingWorkflow: { path: string; name: string } | null = $state(null);

  // State
  let comfyConnected = $state(false);
  let comfyGpu = $state('');
  let comfyVram = $state('');
  let queueCount = $state(0);
  let workflows: any[] = $state([]);
  type ConnectionConfig = {
    comfyui_url: string; minio_endpoint: string; minio_access_key_set: boolean;
    minio_secret_key_set: boolean; blender_path: string | null; krita_path: string | null; api_url: string;
  };
  let connectionConfig: ConnectionConfig = $state({
    comfyui_url: 'http://localhost:8188', minio_endpoint: 'http://localhost:9000',
    minio_access_key_set: false, minio_secret_key_set: false,
    blender_path: null, krita_path: null, api_url: 'http://localhost:8000',
  });
  let newMinioAccessKey = $state('');
  let newMinioSecretKey = $state('');
  let clearMinioAccessKey = $state(false);
  let clearMinioSecretKey = $state(false);
  let settingsBusy = $state(false);
  let settingsMessage = $state('');
  let settingsError = $state('');
  let readiness = $state<ReadinessSnapshot | null>(null);
  let canRunWorkflows = $derived(readiness?.capabilities.some(item => item.capability_id === 'comfy-workflows' && item.status === 'ready') ?? false);

  // workflow path -> { status: 'queueing' | 'pending' | 'success' | 'error', message?: string }
  let workflowRuns: Record<string, WorkflowRun> = $state({});
  let workflowPreflights: Record<string, WorkflowPreflight> = $state({});
  let workflowPreflightBusy: Record<string, boolean> = $state({});
  let outputHistory: HistoryEntry[] = $state([]);
  let toolChecks: ToolCheck[] = $state([]);
  let toolCheckBusy = $state(false);
  let blenderJobBusy = $state(false);
  let blenderJobPlan = $state('');
  let blenderJobError = $state('');
  let blenderJobProject = $state<string | null>(null);
  let blenderJobOutput = $state<string | null>(null);
  let blenderScenes = $state<string[]>([]);
  let blenderSelection = $state<string[]>([]);
  let blenderJobs = $state<any[]>([]);
  let blenderActiveJob = $state<string | null>(null);
  let blenderPollBusy = false;
  let blenderAddonBusy = $state(false);
  let blenderAddonPath = $state('');
  let blenderAddonError = $state('');

  // Filters
  let categoryFilter = $state('all');

  onMount(() => {
    void loadConnectionSettings();
    void loadReadiness();
    refreshWorkflows();
    refreshStatus();
    refreshToolChecks();
    void refreshBlenderJobs();
    const interval = setInterval(refreshStatus, 3000);
    const jobInterval = setInterval(pollBlenderJob, 1000);
    return () => { clearInterval(interval); clearInterval(jobInterval); };
  });

  async function loadConnectionSettings() {
    try { connectionConfig = await invoke<ConnectionConfig>('get_config'); }
    catch (e) { settingsError = String(e); }
  }

  async function loadReadiness() {
    try { readiness = await invoke<ReadinessSnapshot | null>('setup_last_readiness'); }
    catch (e) { console.error('Readiness load failed:', e); }
  }

  function updateReadiness(value: ReadinessSnapshot | null) { readiness = value; }

  async function saveConnectionSettings(testAfterSave = false) {
    settingsBusy = true; settingsMessage = ''; settingsError = '';
    try {
      connectionConfig = await invoke<ConnectionConfig>('set_config', { config: {
        comfyui_url: connectionConfig.comfyui_url,
        minio_endpoint: connectionConfig.minio_endpoint,
        minio_access_key: newMinioAccessKey || null,
        minio_secret_key: newMinioSecretKey || null,
        clear_minio_access_key: clearMinioAccessKey,
        clear_minio_secret_key: clearMinioSecretKey,
        blender_path: connectionConfig.blender_path || null,
        krita_path: connectionConfig.krita_path || null,
        api_url: connectionConfig.api_url,
      }});
      newMinioAccessKey = ''; newMinioSecretKey = '';
      clearMinioAccessKey = false; clearMinioSecretKey = false;
      workflowPreflights = {};
      settingsMessage = 'Connection settings saved on this device.';
      await refreshStatus();
      if (testAfterSave) {
        const result = await invoke<ReadinessSnapshot>('setup_refresh_readiness');
        updateReadiness(result);
        settingsMessage = result.capabilities.some(item => item.capability_id === 'comfy-workflows' && item.status === 'ready')
          ? 'Saved and connected to ComfyUI.'
          : 'Saved. ComfyUI did not answer yet; start it and retry.';
      }
    } catch (e) { settingsError = String(e); }
    finally { settingsBusy = false; }
  }

  async function refreshWorkflows() {
    // The app's own committed, GPU-verified workflow files — not ComfyUI's
    // userdata, and not gated on ComfyUI actually being connected: this is
    // a local file listing, independent of the live service's state.
    try {
      workflows = (await invoke('comfyui_workflows')) as any[];
    } catch (e) {
      console.error('Failed to list workflows:', e);
    }
  }

  async function refreshStatus() {
    try {
      const status = await invoke('comfyui_status');
      const s = status as any;
      comfyConnected = s.connected;
      comfyGpu = s.gpu_name || '';
      comfyVram = s.vram_free_mb ? `${s.vram_free_mb}/${s.vram_total_mb} MB` : '';
      queueCount = s.queue_remaining;
    } catch (e) {
      console.error('Status refresh failed:', e);
    }
  }

  async function preflightWorkflow(workflowPath: string) {
    workflowPreflightBusy = { ...workflowPreflightBusy, [workflowPath]: true };
    try {
      const preflight = await invoke<WorkflowPreflight>('comfyui_preflight', { workflowPath });
      workflowPreflights = { ...workflowPreflights, [workflowPath]: preflight };
      comfyConnected = preflight.connected;
      if (preflight.gpu_name) comfyGpu = preflight.gpu_name;
      if (preflight.vram_total_mb !== null && preflight.vram_free_mb !== null) {
        comfyVram = `${preflight.vram_free_mb}/${preflight.vram_total_mb} MB`;
      }
    } catch (e) {
      workflowPreflights = {
        ...workflowPreflights,
        [workflowPath]: {
          connected: false, compatible: false, gpu_name: null, vram_total_mb: null, vram_free_mb: null,
          missing_nodes: [], missing_models: [], checked_models: [], unchecked_models: [],
          summary: `Preflight could not complete: ${String(e)}`,
        },
      };
    } finally {
      workflowPreflightBusy = { ...workflowPreflightBusy, [workflowPath]: false };
    }
  }

  function workflowQueued(workflowPath: string, promptId: string) {
    workflowRuns = { ...workflowRuns, [workflowPath]: { status: 'pending' } };
    editingWorkflow = null;
    pollPromptStatus(workflowPath, promptId);
    void refreshStatus();
  }

  async function loadOutputPreviews(outputs: PromptOutput[]) {
    const previews: (OutputPreview & { filename: string })[] = [];
    for (const output of outputs.slice(0, 4)) {
      try {
        const preview = await invoke<OutputPreview>('comfyui_output_preview', { output });
        previews.push({ ...preview, filename: output.filename });
      } catch (e) {
        console.error('Output preview unavailable:', e);
      }
    }
    return previews;
  }

  function retainHistory(entry: HistoryEntry) {
    outputHistory = [entry, ...outputHistory.filter(item => item.promptId !== entry.promptId)].slice(0, 20);
  }

  function pollPromptStatus(workflowPath: string, promptId: string) {
    const interval = setInterval(async () => {
      try {
        const status = await invoke<{ completed: boolean; success: boolean; error?: string; outputs: PromptOutput[] }>('comfyui_prompt_status', { promptId });
        if (!status.completed) return;
        clearInterval(interval);
        const previews = status.success ? await loadOutputPreviews(status.outputs) : [];
        const workflowName = workflows.find((item: any) => item.path === workflowPath)?.name ?? workflowPath;
        workflowRuns = {
          ...workflowRuns,
          [workflowPath]: status.success
            ? { status: 'success' }
            : { status: 'error', message: status.error ?? 'ComfyUI reported a failed prompt' },
        };
        retainHistory({
          promptId, workflowPath, workflowName, finishedAt: new Date().toISOString(),
          status: status.success ? 'success' : 'error', message: status.error, previews,
        });
        await refreshStatus();
      } catch (e: any) {
        clearInterval(interval);
        const message = e?.message ?? String(e);
        workflowRuns = { ...workflowRuns, [workflowPath]: { status: 'error', message } };
        retainHistory({
          promptId, workflowPath,
          workflowName: workflows.find((item: any) => item.path === workflowPath)?.name ?? workflowPath,
          finishedAt: new Date().toISOString(), status: 'error', message, previews: [],
        });
      }
    }, 1500);
  }

  async function openBlender() {
    try {
      await invoke('blender_open', { projectPath: null });
    } catch (e) {
      console.error('Blender launch failed:', e);
    }
  }

  async function openKrita() {
    try {
      await invoke('krita_open', { filePath: null });
    } catch (e) {
      console.error('Krita launch failed:', e);
    }
  }

  async function refreshToolChecks() {
    try {
      toolChecks = await invoke<ToolCheck[]>('creator_tool_status');
    } catch (e) {
      console.error('Creator tool check failed:', e);
    }
  }

  async function checkCreatorTools() {
    toolCheckBusy = true;
    try {
      toolChecks = await invoke<ToolCheck[]>('creator_tool_status');
    } catch (e) {
      console.error('Creator tool check failed:', e);
    } finally {
      toolCheckBusy = false;
    }
  }

  async function planBlenderRender() {
    const project = await openDialog({
      multiple: false,
      filters: [{ name: 'Blender project', extensions: ['blend'] }],
    });
    if (!project || Array.isArray(project)) return;
    const output = await openDialog({ directory: true, multiple: false });
    if (!output || Array.isArray(output)) return;
    blenderJobBusy = true;
    blenderJobError = '';
    blenderJobPlan = '';
    blenderScenes = [];
    blenderSelection = [];
    blenderJobProject = project as string;
    blenderJobOutput = output as string;
    try {
      blenderJobPlan = await invoke<string>('blender_batch_render', {
        projectPath: project,
        outputPath: output,
        dryRun: true,
      });
      const line = blenderJobPlan.split('\n').find(line => line.startsWith('HCP_JOB '));
      if (!line) throw new Error('Blender returned no verified scene inventory.');
      const plan = JSON.parse(line.slice(8));
      blenderScenes = plan.available_scenes ?? [];
    } catch (e) {
      blenderJobError = String(e);
    } finally {
      blenderJobBusy = false;
    }
  }

  async function renderBlenderJob() {
    if (!blenderJobProject || !blenderJobOutput || !blenderSelection.length) return;
    if (!window.confirm('Render the selected scenes as local PNG stills in a new attempt folder? This can use CPU/GPU resources; run this as an off-air batch task. No upload occurs.')) return;
    blenderJobBusy = true;
    blenderJobError = '';
    try {
      blenderActiveJob = await invoke<string>('blender_job_start', {
        projectPath: blenderJobProject,
        outputPath: blenderJobOutput,
        scenes: blenderSelection,
      });
      await refreshBlenderJobs();
    } catch (e) {
      blenderJobError = String(e);
    } finally {
      blenderJobBusy = false;
    }
  }

  async function refreshBlenderJobs() {
    try {
      blenderJobs = await invoke<any[]>('blender_job_list');
      blenderActiveJob = blenderJobs.find(job => job.process_owned)?.job_id ?? null;
    } catch (e) { blenderJobError = String(e); }
  }

  async function pollBlenderJob() {
    if (!blenderActiveJob || blenderPollBusy) return;
    blenderPollBusy = true;
    try {
      const job = await invoke<any>('blender_job_status', { jobId: blenderActiveJob });
      blenderJobs = [job, ...blenderJobs.filter(item => item.job_id !== job.job_id)];
      if (!job.process_owned) blenderActiveJob = null;
    } catch (e) { blenderJobError = String(e); }
    finally { blenderPollBusy = false; }
  }

  async function cancelBlenderJob(jobId: string) {
    try { await invoke('blender_job_cancel', { jobId }); await pollBlenderJob(); }
    catch (e) { blenderJobError = String(e); }
  }

  async function retryBlenderJob(jobId: string) {
    const interrupted = blenderJobs.find(job => job.job_id === jobId)?.status === 'interrupted';
    const message = interrupted ? 'This app cannot claim the old worker. Confirm you have stopped it before retrying unfinished scenes into a new attempt folder.' : 'Retry only unfinished scenes as a new local attempt? Previous outputs are preserved.';
    if (!window.confirm(message)) return;
    try { blenderActiveJob = await invoke<string>('blender_job_retry', { jobId, interruptedConfirmed: interrupted }); await refreshBlenderJobs(); }
    catch (e) { blenderJobError = String(e); }
  }

  async function prepareBlenderAddon() {
    blenderAddonBusy = true;
    blenderAddonError = '';
    try {
      blenderAddonPath = await invoke<string>('creator_tool_archive_blender_addon');
    } catch (e) {
      blenderAddonError = String(e);
    } finally {
      blenderAddonBusy = false;
    }
  }

  // Posture Screen
  let postureView = $state<'front' | 'side' | 'back'>('front');
  let postureImageSrc = $state('');
  let postureResult: any = $state(null);
  let postureLoading = $state(false);
  let postureError = $state('');
  let postureCanvas: HTMLCanvasElement | undefined = $state();
  let postureImg: HTMLImageElement | undefined = $state();

  async function pickPostureImage() {
    const selected = await openDialog({
      multiple: false,
      filters: [{ name: 'Image', extensions: ['png', 'jpg', 'jpeg'] }],
    });
    if (!selected || Array.isArray(selected)) return;

    postureError = '';
    postureResult = null;
    postureImageSrc = convertFileSrc(selected as string);
    postureLoading = true;
    try {
      const result = await invoke('posture_analyze', {
        imagePath: selected,
        view: postureView,
      });
      postureResult = result as any;
      if (!postureResult.ok) {
        postureError = postureResult.error || 'No person detected in photo.';
      }
    } catch (e) {
      postureError = String(e);
    } finally {
      postureLoading = false;
    }
  }

  function drawPostureOverlay() {
    if (!postureCanvas || !postureImg || !postureResult?.ok) return;
    const ctx = postureCanvas.getContext('2d');
    if (!ctx) return;
    const w = postureImg.clientWidth;
    const h = postureImg.clientHeight;
    postureCanvas.width = w;
    postureCanvas.height = h;
    ctx.clearRect(0, 0, w, h);
    for (const kp of postureResult.keypoints as any[]) {
      if (kp.v < 0.3) continue;
      ctx.beginPath();
      ctx.arc(kp.x * w, kp.y * h, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#7c4dff';
      ctx.fill();
    }
  }

  $effect(() => {
    postureResult;
    drawPostureOverlay();
  });

  const categories = ['all', 'inpaint', 'upscale', 'stylize', 'segment', 'video', 'realtime', 'general'];

  let filteredWorkflows = $derived(
    categoryFilter === 'all'
      ? workflows
      : workflows.filter((w: any) => w.category === categoryFilter)
  );

</script>

<main>
  <header>
    <h1>Creator Extend</h1>
    <ProfileSwitcher {invoke} kind="content" />
    <div class="status-bar">
      <span class="indicator" class:connected={comfyConnected}>
        ComfyUI {comfyConnected ? 'Connected' : 'Disconnected'}
      </span>
      {#if comfyGpu}
        <span class="gpu-info">{comfyGpu} &middot; VRAM {comfyVram}</span>
      {/if}
    </div>
  </header>

  <nav class="workspace-tabs" aria-label="Workspace view">
    <button aria-pressed={activeView === 'setup'} onclick={() => activeView = 'setup'}>Module setup</button>
    <button aria-pressed={activeView === 'connections'} onclick={() => activeView = 'connections'}>Connections</button>
    <button aria-pressed={activeView === 'remote'} onclick={() => activeView = 'remote'}>Remote control</button>
    <button aria-pressed={activeView === 'social'} onclick={() => activeView = 'social'}>Social</button>
    <button aria-pressed={activeView === 'recordings'} onclick={() => activeView = 'recordings'}>Recordings</button>
    <button aria-pressed={activeView === 'dashboard'} onclick={() => activeView = 'dashboard'}>Dashboard</button>
  </nav>
  {#if activeView === 'setup'}
    <ModuleSetup {invoke} onReadiness={updateReadiness} productKind="creator" />
  {:else if activeView === 'connections'}
    <section class="panel settings" aria-label="Connection settings">
      <h2>Connection settings</h2>
      <p>Endpoints and app paths are stored locally. MinIO keys use the operating system credential manager and are never displayed after saving.</p>
      {#if settingsError}<p class="error" role="alert">{settingsError}</p>{/if}
      {#if settingsMessage}<p class="settings-success" role="status">{settingsMessage}</p>{/if}
      <div class="settings-grid">
        <label>ComfyUI URL <input type="url" bind:value={connectionConfig.comfyui_url} /></label>
        <label>MinIO endpoint <input type="url" bind:value={connectionConfig.minio_endpoint} /></label>
        <label>New MinIO access key <input type="password" bind:value={newMinioAccessKey} autocomplete="new-password" placeholder={connectionConfig.minio_access_key_set ? 'Saved in system credentials' : 'Optional'} disabled={clearMinioAccessKey} /></label>
        <label>New MinIO secret key <input type="password" bind:value={newMinioSecretKey} autocomplete="new-password" placeholder={connectionConfig.minio_secret_key_set ? 'Saved in system credentials' : 'Optional'} disabled={clearMinioSecretKey} /></label>
        <label class="check"><input type="checkbox" bind:checked={clearMinioAccessKey} disabled={!connectionConfig.minio_access_key_set || !!newMinioAccessKey} /> Clear saved access key</label>
        <label class="check"><input type="checkbox" bind:checked={clearMinioSecretKey} disabled={!connectionConfig.minio_secret_key_set || !!newMinioSecretKey} /> Clear saved secret key</label>
        <label>Blender executable path <input bind:value={connectionConfig.blender_path} placeholder="Auto-detect" /></label>
        <label>Krita executable path <input bind:value={connectionConfig.krita_path} placeholder="Auto-detect" /></label>
        <label>Platform API URL <input type="url" bind:value={connectionConfig.api_url} /></label>
      </div>
      <div class="settings-actions">
        <button disabled={settingsBusy} onclick={() => saveConnectionSettings(false)}>{settingsBusy ? 'Saving…' : 'Save settings'}</button>
        <button disabled={settingsBusy} onclick={() => saveConnectionSettings(true)}>Save and test ComfyUI</button>
      </div>
    </section>
  {:else if activeView === 'remote'}
    <RemoteControl {invoke} kind="creator" hostedLabel="Creator Extend Cloud (subscription)" actionDescription="Approved committed ComfyUI workflows can be queued remotely." />
  {:else if activeView === 'social'}
    <SocialManagement {invoke} {openExternal} preferredKind="content" />
  {:else if activeView === 'recordings'}
    <RecordingLibrary {invoke} {openDialog} />
  {:else}
  <div class="dashboard">
    <!-- App Launchers -->
    <section class="panel launchers">
      <h2>Creative Tools</h2>
      <p class="hint">The package checks below run each bundled script with <code>--help</code>. They do not touch project files or start a service.</p>
      <button class="check-tools" disabled={toolCheckBusy} onclick={checkCreatorTools}>
        {toolCheckBusy ? 'Checking packaged actions…' : 'Check packaged actions'}
      </button>
      {#if toolChecks.length > 0}
        <div class="tool-check-list" aria-label="Creator tool readiness">
          {#each toolChecks as check}
            <div class="tool-check" class:tool-check-ready={check.ready}>
              <span>{check.ready ? '✓' : '!'}</span>
              <span><strong>{check.label}</strong> — {check.detail}</span>
            </div>
          {/each}
        </div>
        {#if toolChecks.some(check => check.id === 'posture-screen' && !check.ready)}
          <button class="setup-tool" onclick={() => activeView = 'setup'}>Set up Posture Screen dependencies in Module setup</button>
        {/if}
      {/if}
      <div class="tool-grid">
        <button class="tool-card" onclick={openBlender}>
          <span class="tool-icon">🎬</span>
          <span class="tool-name">Blender</span>
          <span class="tool-desc">3D + Motion Graphics</span>
        </button>
        <button class="tool-card" onclick={openKrita}>
          <span class="tool-icon">🎨</span>
          <span class="tool-name">Krita</span>
          <span class="tool-desc">AI Image Editing</span>
        </button>
        <button class="tool-card" onclick={checkCreatorTools}>
          <span class="tool-icon">⬆️</span>
          <span class="tool-name">Batch Upscale package</span>
          <span class="tool-desc">Check ComfyUI + SDXL action</span>
        </button>
        <button class="tool-card" onclick={checkCreatorTools}>
          <span class="tool-icon">🖌️</span>
          <span class="tool-name">Style Transfer package</span>
          <span class="tool-desc">Check IPAdapter action</span>
        </button>
      </div>
      <button class="check-tools" disabled={blenderJobBusy} onclick={planBlenderRender}>
        {blenderJobBusy ? 'Planning Blender render…' : 'Plan Blender batch render'}
      </button>
      {#if blenderJobPlan && blenderJobProject && blenderJobOutput}
        <fieldset><legend>Select up to 16 scenes for local PNG stills</legend>
          {#each blenderScenes as scene}
            <label><input type="checkbox" checked={blenderSelection.includes(scene)} onchange={(event) => blenderSelection = event.currentTarget.checked ? [...blenderSelection, scene] : blenderSelection.filter(name => name !== scene)} /> {scene}</label>
          {/each}
        </fieldset>
        <button class="render-tools" disabled={blenderJobBusy || !!blenderActiveJob || !blenderSelection.length || blenderSelection.length > 16} onclick={renderBlenderJob}>
          {blenderJobBusy ? 'Starting Blender job…' : 'Render selected scenes'}
        </button>
      {/if}
      {#if blenderJobError}<p class="posture-error" role="alert">{blenderJobError}</p>{/if}
      {#if blenderJobPlan}<pre class="tool-plan">{blenderJobPlan}</pre>{/if}
      {#each blenderJobs as job (job.job_id)}
        <div class="tool-plan" aria-live="polite">
          <strong>Blender job {job.job_id.slice(0, 8)}: {job.status}</strong>
          {#each job.scenes ?? [] as scene}<p>{scene.name}: {scene.status}{scene.error ? ` (${scene.error})` : ''}</p>{/each}
          {#if job.output}<p>Local outputs: {job.output}</p>{/if}
          {#if job.error}<p role="alert">{job.error}</p>{/if}
          {#if job.process_owned}<button onclick={() => cancelBlenderJob(job.job_id)}>Cancel owned job</button>
          {:else if ['failed', 'cancelled', 'interrupted'].includes(job.status)}<button disabled={!!blenderActiveJob} onclick={() => retryBlenderJob(job.job_id)}>Retry unfinished scenes</button>{/if}
        </div>
      {/each}
      <button class="check-tools" disabled={blenderAddonBusy} onclick={prepareBlenderAddon}>
        {blenderAddonBusy ? 'Preparing Blender addon…' : 'Prepare Blender addon package'}
      </button>
      {#if blenderAddonError}<p class="posture-error" role="alert">{blenderAddonError}</p>{/if}
      {#if blenderAddonPath}<p class="tool-path">Install this ZIP from Blender Add-ons → Install: <code>{blenderAddonPath}</code></p>{/if}
    </section>

    <!-- ComfyUI Workflows -->
    <section class="panel">
      <h2>ComfyUI Workflows</h2>

      {#if !canRunWorkflows}
        <p class="hint">Workflow controls are locked until the current ComfyUI and committed-catalog checks pass. Open Module setup and run Check readiness.</p>
      {:else}
        <p class="hint">Run preflight on a workflow before Configure. It checks the live node and fixed model inventory, then reports VRAM without estimating output quality.</p>
      {/if}

      <div class="category-tabs">
        {#each categories as cat}
          <button
            class="tab"
            class:active={categoryFilter === cat}
            onclick={() => categoryFilter = cat}
          >
            {cat}
          </button>
        {/each}
      </div>

      {#if queueCount > 0}
        <p class="queue-status">Queue: {queueCount} pending</p>
      {/if}

      <div class="workflow-list">
        {#each filteredWorkflows as wf}
          {@const run = workflowRuns[wf.path]}
          {@const preflight = workflowPreflights[wf.path]}
          <div class="workflow-item">
            <div class="wf-info">
              <span class="wf-name">{wf.name}</span>
              <span class="wf-category">{wf.category}</span>
              {#if run}
                <span class="wf-run-status wf-run-{run.status}">
                  {run.status === 'queueing' ? 'Queueing…'
                    : run.status === 'pending' ? 'Running…'
                    : run.status === 'success' ? '✓ Done'
                  : `✗ ${run.message ?? 'Failed'}`}
                </span>
              {/if}
              {#if preflight}
                <span class:preflight-ready={preflight.compatible} class:preflight-blocked={!preflight.compatible} class="preflight-summary">
                  {preflight.compatible ? '✓ ' : '⚠ '}{preflight.summary}
                </span>
                {#if preflight.checked_models.length}
                  <span class="preflight-detail">Models found: {preflight.checked_models.join(', ')}</span>
                {/if}
                {#if preflight.gpu_name || preflight.vram_total_mb !== null}
                  <span class="preflight-detail">{preflight.gpu_name ?? 'GPU'} · VRAM {preflight.vram_free_mb ?? 'unknown'}/{preflight.vram_total_mb ?? 'unknown'} MB</span>
                {/if}
              {/if}
            </div>
            <button
              onclick={() => preflightWorkflow(wf.path)}
              disabled={!canRunWorkflows || editingWorkflow !== null || workflowPreflightBusy[wf.path]}
            >
              {workflowPreflightBusy[wf.path] ? 'Checking…' : preflight ? 'Recheck' : 'Preflight'}
            </button>
            <button
              onclick={() => editingWorkflow = { path: wf.path, name: wf.name }}
              disabled={!canRunWorkflows || !preflight?.compatible || editingWorkflow !== null || run?.status === 'queueing' || run?.status === 'pending'}
            >
              Configure
            </button>
          </div>
        {:else}
          <p class="hint">No workflows found{categoryFilter !== 'all' ? ` in "${categoryFilter}"` : ''}</p>
        {/each}
      </div>
      {#if editingWorkflow}
        {#key editingWorkflow.path}
          <WorkflowInputs workflowPath={editingWorkflow.path} workflowName={editingWorkflow.name}
            connected={comfyConnected} onQueued={workflowQueued} onClose={() => editingWorkflow = null} />
        {/key}
      {/if}
    </section>

    <section class="panel">
      <div class="history-heading">
        <div>
          <h2>Output history</h2>
          <p>Completed jobs from this app session. Up to four bounded previews are loaded from the configured ComfyUI server.</p>
        </div>
        {#if outputHistory.length}<button onclick={() => outputHistory = []}>Clear history</button>{/if}
      </div>
      {#each outputHistory as entry}
        <article class="history-entry">
          <div><strong>{entry.workflowName}</strong> · <span class:history-error={entry.status === 'error'}>{entry.status}</span></div>
          <small>{new Date(entry.finishedAt).toLocaleString()} · Prompt {entry.promptId}</small>
          {#if entry.message}<p class="history-error">{entry.message}</p>{/if}
          {#if entry.previews.length}
            <div class="preview-grid">
              {#each entry.previews as preview}
                {#if preview.media_type.startsWith('video/')}
                  <!-- svelte-ignore a11y_media_has_caption -->
                  <video controls preload="metadata" src={preview.data_url} aria-label={`Output ${preview.filename}`}></video>
                {:else}
                  <img src={preview.data_url} alt={`Output ${preview.filename}`} />
                {/if}
              {/each}
            </div>
          {:else if entry.status === 'success'}
            <p class="hint">The workflow completed without a supported image or video preview.</p>
          {/if}
        </article>
      {:else}
        <p class="hint">Run a configured workflow to see its completion and output here.</p>
      {/each}
    </section>

    <!-- Posture Screen -->
    <section class="panel posture-panel">
      <h2>Posture Screen</h2>
      <p class="hint">Upload a front, side, or back photo to check body alignment.</p>

      <div class="relay-options view-select">
        <label>
          <input type="radio" bind:group={postureView} value="front" />
          Front
        </label>
        <label>
          <input type="radio" bind:group={postureView} value="side" />
          Side
        </label>
        <label>
          <input type="radio" bind:group={postureView} value="back" />
          Back
        </label>
      </div>

      <button onclick={pickPostureImage} disabled={postureLoading}>
        {postureLoading ? 'Analyzing…' : 'Upload Photo'}
      </button>

      {#if postureError}
        <p class="posture-error">{postureError}</p>
      {/if}

      {#if postureImageSrc}
        <div class="posture-image-wrap">
          <img
            bind:this={postureImg}
            src={postureImageSrc}
            alt="Uploaded for posture analysis"
            onload={drawPostureOverlay}
          />
          <canvas bind:this={postureCanvas}></canvas>
        </div>
      {/if}

      {#if postureResult?.ok}
        <div class="posture-metrics">
          {#each Object.entries(postureResult.metrics) as [key, value]}
            <div class="metric-row">
              <span class="metric-key">{key.replace(/_/g, ' ')}</span>
              <span class="metric-value">{value}</span>
            </div>
          {/each}
        </div>

        {#if postureResult.flags.length}
          <ul class="flag-list">
            {#each postureResult.flags as flag}
              <li class="flag-{flag.severity}">{flag.label} ({flag.value})</li>
            {/each}
          </ul>
        {:else}
          <p class="hint">No alignment issues flagged.</p>
        {/if}
      {/if}
    </section>

  </div>
  {/if}
</main>

<style>
  .workspace-tabs { display: flex; gap: .7rem; margin-bottom: 1.5rem; }
  .workspace-tabs button[aria-pressed="true"] { background: #61429c; color: white; }
  .settings { max-width: 760px; }
  .settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin: 1.25rem 0; }
  .settings-grid label { display: grid; gap: .4rem; color: #c9c5d2; font-size: .85rem; }
  .settings-grid label.check { display: flex; align-items: center; align-self: end; }
  .settings-grid input:not([type="checkbox"]) { padding: .65rem; border: 1px solid #494955; border-radius: 6px; background: #15151b; color: #f1eef6; font: inherit; }
  .settings-actions { display: flex; gap: .7rem; flex-wrap: wrap; }
  .settings-success { color: #a4d9b1; }
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f0f;
    color: #e0e0e0;
  }

  main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 1.5rem;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    border-bottom: 1px solid #333;
    padding-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  h1 { color: #7c4dff; margin: 0; }
  h2 { color: #7c4dff; margin-top: 0; }

  .status-bar { display: flex; gap: 1rem; align-items: center; }

  .indicator {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    background: #2a2a2a;
    color: #888;
  }
  .indicator.connected { background: #1a3a1a; color: #4caf50; }

  .gpu-info { font-size: 0.8rem; color: #888; }

  .dashboard {
    display: grid;
    grid-template-columns: 1fr 1fr;
    align-items: start;
    gap: 1.5rem;
  }

  .panel {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .launchers { grid-column: 1 / -1; }

  .check-tools { margin: 0.25rem 0 0.75rem; }
  .render-tools { margin: 0 0 0.75rem; border-color: #e39b43; color: #e39b43; }
  .setup-tool { margin: 0 0 1rem; }
  .tool-plan {
    margin: 0.5rem 0 0;
    padding: 0.75rem;
    max-height: 10rem;
    overflow: auto;
    background: #111;
    border-radius: 6px;
    color: #b6b1c1;
    font-size: 0.75rem;
    white-space: pre-wrap;
  }
  .tool-path { margin: 0 0 0.75rem; color: #b6b1c1; font-size: 0.8rem; overflow-wrap: anywhere; }
  .tool-check-list { display: grid; gap: 0.35rem; margin: 0 0 1rem; }
  .tool-check {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    padding: 0.45rem 0.6rem;
    border-radius: 6px;
    background: #3a2f1a;
    color: #f0bd76;
    font-size: 0.8rem;
  }
  .tool-check-ready { background: #1a3a1a; color: #a4d9b1; }
  .tool-check strong { color: inherit; }

  .tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 1rem;
  }

  .tool-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.25rem;
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    color: #e0e0e0;
  }

  .tool-card:hover { border-color: #7c4dff; background: #2a2a3a; }
  .tool-icon { font-size: 2rem; }
  .tool-name { font-weight: 600; }
  .tool-desc { font-size: 0.8rem; color: #888; }

  .category-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .tab {
    padding: 0.3rem 0.75rem;
    border: 1px solid #444;
    border-radius: 16px;
    background: #2a2a2a;
    color: #ccc;
    cursor: pointer;
    font-size: 0.85rem;
    text-transform: capitalize;
  }

  .tab:hover { border-color: #7c4dff; }
  .tab.active { background: #7c4dff; color: white; border-color: #7c4dff; }

  .queue-status {
    color: #ff9800;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
  }

  .workflow-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .workflow-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #2a2a2a;
    border-radius: 8px;
  }

  .wf-name { font-weight: 500; }
  .wf-category {
    font-size: 0.75rem;
    color: #888;
    margin-left: 0.5rem;
    padding: 0.15rem 0.5rem;
    background: #333;
    border-radius: 8px;
  }

  .wf-run-status {
    display: block;
    font-size: 0.75rem;
    margin-top: 0.25rem;
  }
  .wf-run-queueing, .wf-run-pending { color: #7c4dff; }
  .preflight-summary, .preflight-detail { display: block; font-size: .8rem; line-height: 1.35; }
  .preflight-ready { color: #a4d9b1; }
  .preflight-blocked { color: #f0bd76; }
  .preflight-detail { color: #b6b1c1; }
  .wf-run-success { color: #4caf50; }
  .wf-run-error { color: #f44336; }

  .history-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
  .history-heading h2 { margin-bottom: 0.25rem; }
  .history-heading p { margin: 0; color: #aaa; font-size: 0.85rem; }
  .history-entry { margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid #444; }
  .history-entry small { color: #aaa; overflow-wrap: anywhere; }
  .history-error { color: #f44336; }
  .preview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; }
  .preview-grid img, .preview-grid video { width: 100%; max-height: 320px; object-fit: contain; border-radius: 6px; background: #111; }

  .relay-options {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0;
  }

  .hint { color: #888; font-size: 0.9rem; }

  .view-select { flex-direction: row; margin-bottom: 1rem; }

  .posture-error {
    color: #f44336;
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }

  .posture-image-wrap {
    position: relative;
    display: inline-block;
    max-width: 100%;
    margin: 0.5rem 0;
  }

  .posture-image-wrap img {
    display: block;
    max-width: 100%;
    border-radius: 8px;
  }

  .posture-image-wrap canvas {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
  }

  .posture-metrics {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin: 1rem 0;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0.6rem;
    background: #2a2a2a;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .metric-key { color: #ccc; text-transform: capitalize; }
  .metric-value { color: #7c4dff; font-weight: 600; }

  .flag-list {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .flag-list li {
    padding: 0.4rem 0.6rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .flag-warning { background: #3a2f1a; color: #ff9800; }
  .flag-flag { background: #3a1a1a; color: #f44336; }

  button {
    padding: 0.4rem 1rem;
    border: 1px solid #7c4dff;
    border-radius: 8px;
    background: transparent;
    color: #7c4dff;
    cursor: pointer;
    font-size: 0.85rem;
  }
  button:hover { background: #7c4dff; color: white; }
</style>
