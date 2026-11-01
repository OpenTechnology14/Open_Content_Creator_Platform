<script lang="ts">
  import AudioSetup from './AudioSetup.svelte';
  type Module = { requirements: string[]; depends_on: string[]; remaining: string };
  type Check = { name: string; status: string; detail: string };
  type Report = { checked_at: number; modules: { id: string; checks: Check[] }[] };
  export type ReadinessSnapshot = {
    schema_version: number; manifest_version: string; product: string; machine_id: string;
    setup_run_id: string; generated_at: string;
    checks: { check_id: string; status: string; summary: string; evidence: Record<string, unknown> }[];
    capabilities: { capability_id: string; label: string; status: string; summary: string; required_checks: string[] }[];
  };
  type SyncSettings = { enabled: boolean; base_url: string; project_id: string; machine_id: string; api_key_set: boolean };
  type SyncReport = { attempted: number; accepted: number; duplicates: number; failures: string[] };
  type Job = { id: string; kind?: string; status: string; package?: string; verified?: boolean; log_path?: string; services?: string[]; service_states?: Record<string, string>; steps?: Record<string, string>; credentials_saved?: boolean; report?: { modules: { id: string; dependencies: string }[] } };
  type PythonStatus = { installed: boolean; path?: string; bootstrap_available: boolean; detail: string };
  type FfmpegStatus = { installed: boolean; path?: string; version?: string; bootstrap_available: boolean; detail: string };
  type ObsSystemStatus = { state: string; installed: boolean; path?: string; running: boolean; default_websocket_reachable: boolean; bootstrap_available: boolean; detail: string };
  type ObsScenePlan = { asset_version: string; name: string; scenes: string[]; apply_available: boolean; detail: string };
  type ObsConnectionStatus = { state: string; detail: string; host: string; port: number; obs_version?: string; websocket_version?: string };
  type ObsRecordingReport = { accepted: boolean; duration_seconds: number; bytes: number; file_name?: string; detail: string };
  type DockerPlan = { asset_version: string; modules: string[]; services: string[]; detail: string };
  type DockerStatus = {
    state: string; installed: boolean; desktop_installed: boolean; desktop_running: boolean;
    desktop_path?: string; cli_available: boolean; daemon_ready: boolean; compose_ready: boolean;
    docker_version?: string; engine_version?: string; compose_version?: string;
    wsl_state: string; wsl_detail: string; bootstrap_available: boolean; start_available: boolean;
    services_ready: boolean; service_states: Record<string, string>; detail: string;
  };
  type CaptureDevice = { id: string; name: string; kind: 'video' | 'audio'; backend: string };
  type CaptureReport = {
    checked_at: number; status: string; scope: string;
    obs: { found: boolean; detail: string }; ffmpeg: { found: boolean; detail: string };
    video_devices: CaptureDevice[]; audio_devices: CaptureDevice[];
    windows_pnp_devices: { name: string; class: string; status: string }[];
    recommendations: string[];
  };
  type CaptureTestReport = {
    checked_at: number; status: string; scope: string; error?: string;
    stages: { detected: boolean; signal: boolean; recorded: boolean; accepted: boolean };
    video_stream?: boolean; audio_stream?: boolean; frames_observed?: number;
    duration_observed_seconds?: number; recording_bytes?: number;
  };
  let { invoke, onReadiness, productKind, preview = false }: {
    invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
    onReadiness: (snapshot: ReadinessSnapshot | null) => void;
    productKind: 'stream' | 'creator';
    preview?: boolean;
  } = $props();
  let catalog: { modules: Record<string, Module>; profiles: Record<string, string[]> } | null = $state(null);
  let selected: string[] = $state([]);
  let saving = $state(false);
  let loading = $state(true);
  let busy = $state(false);
  let error = $state('');
  let notice = $state('');
  let guide = $state('');
  let guideTitle = $state('');
  let report: Report | null = $state(null);
  let readiness: ReadinessSnapshot | null = $state(null);
  let syncSettings: SyncSettings | null = $state(null);
  let syncBusy = $state(false);
  let newApiKey = $state('');
  let clearApiKey = $state(false);
  let job: Job | null = $state(null);
  let pythonStatus: PythonStatus | null = $state(null);
  let pythonBusy = $state(false);
  let ffmpegStatus: FfmpegStatus | null = $state(null);
  let ffmpegBusy = $state(false);
  let obsSystem: ObsSystemStatus | null = $state(null);
  let obsPlan: ObsScenePlan | null = $state(null);
  let obsConnection: ObsConnectionStatus | null = $state(null);
  let obsRecording: ObsRecordingReport | null = $state(null);
  let obsBusy = $state(false);
  let dockerPlan: DockerPlan | null = $state(null);
  let dockerStatus: DockerStatus | null = $state(null);
  let dockerBusy = $state(false);
  let captureReport: CaptureReport | null = $state(null);
  let captureTestReport: CaptureTestReport | null = $state(null);
  let captureVideoId = $state('');
  let captureAudioId = $state('');
  let captureBusy = $state(false);
  let disposed = false;
  let polling = false;
  const command = (name: string) => `plugin:module-setup|${name}`;
  const title = (name: string) => name.split('-').map(word => word[0].toUpperCase() + word.slice(1)).join(' ');
  const failure = (value: unknown) => typeof value === 'object' && value && 'message' in value ? String(value.message) : String(value);
  const isInstalling = (value: Job | null) => value?.status === 'running' || value?.status === 'starting';
  let installing = $derived(isInstalling(job));
  let resolved = $derived.by(() => {
    if (!catalog) return [] as string[];
    const result = new Set<string>();
    const visit = (id: string) => {
      if (result.has(id) || !catalog?.modules[id]) return;
      result.add(id);
      catalog.modules[id].depends_on.forEach(visit);
    };
    selected.forEach(visit);
    return [...result];
  });

  $effect(() => {
    const bridge = invoke;
    disposed = false;
    void load(bridge);
    const timer = setInterval(() => { if (job && (installing || job.status === 'unobserved')) void poll(job.id); }, 1500);
    return () => { disposed = true; clearInterval(timer); };
  });

  async function load(bridge: typeof invoke) {
    try {
      const [value, savedPython, savedFfmpeg, savedObs, savedObsPlan, savedReadiness, savedSync] = await Promise.all([
        bridge<{
          catalog: NonNullable<typeof catalog>; selected: string[]; last_job?: string;
          capture_video_id?: string; capture_audio_id?: string; capture_report?: CaptureReport;
          capture_test_report?: CaptureTestReport;
        }>(command('snapshot')),
        bridge<PythonStatus>(command('python_status')),
        bridge<FfmpegStatus>(command('ffmpeg_status')),
        bridge<ObsSystemStatus>(command('obs_status')),
        bridge<ObsScenePlan>(command('obs_scene_plan')),
        bridge<ReadinessSnapshot | null>('setup_last_readiness'),
        bridge<SyncSettings>('setup_sync_settings'),
      ]);
      if (disposed) return;
      catalog = value.catalog; selected = value.selected;
      captureVideoId = value.capture_video_id ?? '';
      captureAudioId = value.capture_audio_id ?? '';
      captureReport = value.capture_report ?? null;
      captureTestReport = value.capture_test_report ?? null;
      pythonStatus = savedPython;
      ffmpegStatus = savedFfmpeg;
      obsSystem = savedObs;
      obsPlan = savedObsPlan;
      readiness = savedReadiness;
      syncSettings = savedSync;
      onReadiness(savedReadiness);
      [dockerPlan, dockerStatus] = await Promise.all([
        bridge<DockerPlan>(command('docker_plan'), { selected: value.selected }),
        bridge<DockerStatus>(command('docker_status'), { selected: value.selected }),
      ]);
      if (disposed) return;
      if (value.last_job) await poll(value.last_job);
    } catch (e) { error = failure(e); }
    finally { loading = false; }
  }
  async function choose(next: string[]) {
    saving = true; error = ''; notice = ''; report = null;
    try {
      await invoke(command('save_selection'), { selected: next });
      selected = next; notice = 'Module choices saved on this device.';
      await refreshDocker(next);
    } catch (e) { error = failure(e); }
    finally { saving = false; }
  }
  async function poll(id: string) {
    if (polling) return;
    polling = true;
    try {
      const value = await invoke<Job>(command('job_status'), { id });
      if (!disposed) {
        const changed = job?.status !== value.status;
        job = value;
        if (changed && value.kind === 'python_bootstrap' && ['finished', 'failed'].includes(value.status)) await refreshPython();
        if (changed && value.kind === 'ffmpeg_bootstrap' && ['finished', 'failed'].includes(value.status)) await refreshFfmpeg();
        if (changed && value.kind === 'obs_bootstrap' && ['finished', 'failed'].includes(value.status)) await refreshObs();
        if (changed && ['docker_bootstrap', 'docker_services'].includes(value.kind ?? '') && ['finished', 'failed'].includes(value.status)) await refreshDocker();
      }
    }
    catch (e) { error = failure(e); }
    finally { polling = false; }
  }
  async function install() {
    busy = true; error = ''; notice = ''; report = null;
    try {
      const id = await invoke<string>(command('start_install'), { selected });
      job = { id, status: 'starting' };
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { busy = false; }
  }
  async function refreshPython() {
    pythonBusy = true;
    try { pythonStatus = await invoke<PythonStatus>(command('python_status')); }
    catch (e) { error = failure(e); }
    finally { pythonBusy = false; }
  }
  async function bootstrapPython() {
    pythonBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_python_bootstrap'));
      job = { id, kind: 'python_bootstrap', status: 'starting', package: 'Python 3.12' };
      notice = 'Python installation started. You can keep using the app while it runs.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { pythonBusy = false; }
  }
  async function refreshFfmpeg() {
    ffmpegBusy = true;
    try { ffmpegStatus = await invoke<FfmpegStatus>(command('ffmpeg_status')); }
    catch (e) { error = failure(e); }
    finally { ffmpegBusy = false; }
  }
  async function bootstrapFfmpeg() {
    ffmpegBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_ffmpeg_bootstrap'));
      job = { id, kind: 'ffmpeg_bootstrap', status: 'starting', package: 'FFmpeg' };
      notice = 'FFmpeg installation started. You can keep using the app while it runs.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { ffmpegBusy = false; }
  }
  async function refreshObs(testConnection = false) {
    obsBusy = true; error = '';
    try {
      obsSystem = await invoke<ObsSystemStatus>(command('obs_status'));
      if (testConnection && productKind === 'stream' && obsSystem.running) {
        obsConnection = await invoke<ObsConnectionStatus>('obs_connection_diagnostic');
      } else if (!obsSystem.running) {
        obsConnection = null;
      }
    } catch (e) { error = failure(e); }
    finally { obsBusy = false; }
  }
  async function bootstrapObs() {
    obsBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_obs_bootstrap'));
      job = { id, kind: 'obs_bootstrap', status: 'starting', package: 'OBS Studio' };
      notice = 'OBS installation started. You can keep using the app while it runs.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { obsBusy = false; }
  }
  async function openObs() {
    obsBusy = true; error = ''; notice = '';
    try {
      obsSystem = await invoke<ObsSystemStatus>(command('launch_obs'));
      notice = obsSystem.running ? 'OBS Studio opened. Finish its first-run prompts, then test the connection.' : 'OBS launch was requested; recheck after its first-run prompts.';
    } catch (e) { error = failure(e); }
    finally { obsBusy = false; }
  }
  async function testObsRecording() {
    obsBusy = true; error = ''; notice = ''; obsRecording = null;
    try {
      obsRecording = await invoke<ObsRecordingReport>('obs_recording_test');
      notice = obsRecording.accepted ? 'OBS created and finalized a local test recording.' : 'OBS recording acceptance needs attention.';
    } catch (e) { error = failure(e); }
    finally { obsBusy = false; }
  }
  async function refreshDocker(next = selected) {
    dockerBusy = true; error = '';
    try {
      [dockerPlan, dockerStatus] = await Promise.all([
        invoke<DockerPlan>(command('docker_plan'), { selected: next }),
        invoke<DockerStatus>(command('docker_status'), { selected: next }),
      ]);
    } catch (e) { error = failure(e); }
    finally { dockerBusy = false; }
  }
  async function bootstrapDocker() {
    dockerBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_docker_bootstrap'));
      job = { id, kind: 'docker_bootstrap', status: 'starting', package: 'Docker Desktop' };
      notice = 'Docker Desktop installation started. Elevation, licence or restart handoffs may still appear.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { dockerBusy = false; }
  }
  async function openDocker() {
    dockerBusy = true; error = ''; notice = '';
    try {
      dockerStatus = await invoke<DockerStatus>(command('launch_docker_desktop'), { selected });
      notice = dockerStatus.daemon_ready ? 'Docker Desktop opened and its daemon is ready.' : 'Docker Desktop opened. Finish its first-run prompts, then recheck.';
    } catch (e) { error = failure(e); }
    finally { dockerBusy = false; }
  }
  async function startDockerServices() {
    dockerBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_docker_services'), { selected });
      job = { id, kind: 'docker_services', status: 'starting', services: dockerPlan?.services ?? [] };
      notice = 'Selected local services are starting. First use may download images and build dependencies.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { dockerBusy = false; }
  }
  async function initializeLocalServices() {
    dockerBusy = true; error = ''; notice = '';
    try {
      const id = await invoke<string>(command('start_local_service_bootstrap'), { selected });
      job = { id, kind: 'local_service_bootstrap', status: 'starting', services: dockerPlan?.services ?? [] };
      notice = 'Database migrations, storage buckets and selected workflows are being initialized.';
      await poll(id);
    } catch (e) { error = failure(e); }
    finally { dockerBusy = false; }
  }
  async function copyLocalCredential(kind: string) {
    error = ''; notice = '';
    try {
      const result = await invoke<{ copied: boolean; label: string }>(command('copy_local_credential'), { kind });
      notice = `${result.label} copied to the system clipboard.`;
    } catch (e) { error = failure(e); }
  }
  function dockerStateLabel(state: string) {
    return ({ missing: 'Not installed', desktop_stopped: 'Desktop stopped', daemon_unreachable: 'Daemon unavailable', compose_unavailable: 'Compose unavailable', wsl_missing: 'WSL unavailable', wsl_update_required: 'WSL update required', virtualization_unavailable: 'Virtualization unavailable', reboot_required: 'Restart required', ready: 'Engine ready' } as Record<string,string>)[state] ?? state;
  }
  function jobHeading(value: Job) {
    const name = value.kind === 'python_bootstrap' ? 'Python 3.12' : value.kind === 'ffmpeg_bootstrap' ? 'FFmpeg' : value.kind === 'obs_bootstrap' ? 'OBS Studio' : value.kind === 'docker_bootstrap' ? 'Docker Desktop' : value.kind === 'docker_services' ? 'selected local services' : value.kind === 'local_service_bootstrap' ? 'local data and workflows' : 'dependencies';
    if (isInstalling(value)) return value.kind === 'docker_services' ? 'Starting selected local services…' : value.kind === 'local_service_bootstrap' ? 'Initializing local data and workflows…' : `Installing ${name}…`;
    if (value.status === 'finished') return value.kind === 'module_dependencies' || !value.kind ? 'Dependency install finished — check readiness next' : value.kind === 'docker_services' ? 'Selected local services are ready' : value.kind === 'local_service_bootstrap' ? 'Local data and workflows are ready' : `${name} installed and verified`;
    if (value.status === 'unobserved') return `${name[0].toUpperCase()}${name.slice(1)} installation needs a recheck`;
    return `${name[0].toUpperCase()}${name.slice(1)} installation did not finish successfully`;
  }
  async function check() {
    busy = true; error = ''; report = null; notice = '';
    const [dependencies, live] = await Promise.allSettled([
      invoke<Report>(command('check'), { selected }),
      invoke<ReadinessSnapshot>('setup_refresh_readiness'),
    ]);
    if (disposed) return;
    if (dependencies.status === 'fulfilled') report = dependencies.value;
    else error = failure(dependencies.reason);
    if (live.status === 'fulfilled') {
      readiness = live.value;
      onReadiness(live.value);
      if (syncSettings?.enabled) await synchronize();
    } else error = [error, failure(live.reason)].filter(Boolean).join(' · ');
    busy = false;
  }
  async function saveSyncSettings() {
    if (!syncSettings) return;
    syncBusy = true; error = ''; notice = '';
    try {
      syncSettings = await invoke<SyncSettings>('setup_save_sync_settings', { settings: {
        enabled: syncSettings.enabled,
        base_url: syncSettings.base_url,
        project_id: syncSettings.project_id,
        machine_id: syncSettings.machine_id,
        api_key: newApiKey || null,
        clear_api_key: clearApiKey,
      }});
      newApiKey = ''; clearApiKey = false;
      notice = 'OpenTechnology synchronization settings saved on this device.';
    } catch (e) { error = failure(e); }
    finally { syncBusy = false; }
  }
  async function synchronize() {
    syncBusy = true; error = ''; notice = '';
    try {
      const result = await invoke<SyncReport>('setup_sync_now');
      if (result.failures.length) {
        error = `${result.accepted}/${result.attempted} readiness observations accepted. ${result.failures.join(' · ')}`;
      } else {
        notice = `${result.accepted} readiness observation${result.accepted === 1 ? '' : 's'} synchronized${result.duplicates ? ` (${result.duplicates} already received)` : ''}.`;
      }
    } catch (e) { error = failure(e); }
    finally { syncBusy = false; }
  }
  async function showGuide(module: string) {
    try { guide = await invoke<string>(command('manual'), { module }); guideTitle = title(module); }
    catch (e) { error = failure(e); }
  }
  async function scanCapture() {
    captureBusy = true; error = ''; notice = '';
    try {
      captureReport = await invoke<CaptureReport>(command('capture_scan'));
      if (!captureReport.video_devices.some(device => device.id === captureVideoId)) captureVideoId = '';
      if (!captureReport.audio_devices.some(device => device.id === captureAudioId)) captureAudioId = '';
    } catch (e) { error = failure(e); }
    finally { captureBusy = false; }
  }
  async function saveCapture() {
    captureBusy = true; error = ''; notice = '';
    try {
      await invoke(command('save_capture_selection'), {
        videoId: captureVideoId || null,
        audioId: captureAudioId || null,
      });
      notice = 'Capture-device choices saved on this computer.';
    } catch (e) { error = failure(e); }
    finally { captureBusy = false; }
  }
  async function testCapture() {
    if (!captureVideoId) return;
    captureBusy = true; error = ''; notice = ''; captureTestReport = null;
    try {
      captureTestReport = await invoke<CaptureTestReport>(command('capture_test'), {
        videoId: captureVideoId,
        audioId: captureAudioId || null,
      });
      notice = captureTestReport.status === 'accepted'
        ? 'Capture test recorded a valid local sample.'
        : 'Capture test needs attention. Review the stages below.';
    } catch (e) { error = failure(e); }
    finally { captureBusy = false; }
  }
  function label(status: string) {
    return ({ passed: 'Check passed', missing: 'Action required', not_found: 'Not found', failed: 'Check failed', installed: 'Dependencies installed', manual_only: 'Manual setup', installing: 'Installing dependencies', connected: 'Connected', authentication_failed: 'Credentials rejected', websocket_unreachable: 'Unavailable', handshake_failed: 'Handshake failed', incompatible: 'Version mismatch' } as Record<string,string>)[status] ?? status;
  }
</script>

<section class="setup" aria-label="Module setup">
  <div class="intro">
    <p class="eyebrow">SET UP YOUR WORKSPACE</p>
    <h2>Choose the tools you need</h2>
    <p>Choose modules individually or start with a profile. Your selections are saved on this device. Other modules can be added later.</p>
  </div>
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if notice}<p class="notice" role="status">{notice}</p>{/if}
  {#if loading}<p role="status">Loading module catalog…</p>
  {:else if catalog}
    <div class="profiles" aria-label="Starter profiles">
      {#each Object.entries(catalog.profiles) as [id, modules]}
        <button disabled={busy || saving || installing} onclick={() => choose([...new Set([...selected, ...modules])])}>Add {title(id)}</button>
      {/each}
    </div>
    <fieldset disabled={busy || saving || installing}>
      <legend>Modules · {selected.length} chosen{resolved.length > selected.length ? ` + ${resolved.length - selected.length} required` : ''}</legend>
      <div class="module-grid">
        {#each Object.entries(catalog.modules) as [id, module]}
          <label class:chosen={resolved.includes(id)}>
            <input type="checkbox" checked={resolved.includes(id)} disabled={resolved.includes(id) && !selected.includes(id)}
              onchange={(event) => choose(event.currentTarget.checked ? [...selected, id] : selected.filter(value => value !== id))} />
            <span>{title(id)}<small>{resolved.includes(id) && !selected.includes(id) ? 'Required dependency' : module.requirements.length ? 'Python dependencies + manual setup' : 'Manual setup'}</small></span>
          </label>
        {/each}
      </div>
    </fieldset>
    {#if pythonStatus}
      <section class="prerequisite" aria-label="Python prerequisite">
        <div>
          <h3>Python 3.12</h3>
          <p class:passed={pythonStatus.installed}>{pythonStatus.detail}</p>
          {#if pythonStatus.path}<p class="scope">{pythonStatus.path}</p>{/if}
        </div>
        <div class="capture-actions">
          {#if !pythonStatus.installed}
            <button class="primary" disabled={pythonBusy || installing || !pythonStatus.bootstrap_available} onclick={bootstrapPython}>{pythonBusy ? 'Checking…' : 'Install Python 3.12'}</button>
          {/if}
          <button disabled={pythonBusy || installing} onclick={refreshPython}>Recheck Python</button>
        </div>
      </section>
    {/if}
    {#if ffmpegStatus}
      <section class="prerequisite" aria-label="FFmpeg prerequisite">
        <div>
          <h3>FFmpeg</h3>
          <p class:passed={ffmpegStatus.installed}>{ffmpegStatus.detail}</p>
          {#if ffmpegStatus.path}<p class="scope">{ffmpegStatus.path}{ffmpegStatus.version ? ` · ${ffmpegStatus.version}` : ''}</p>{/if}
        </div>
        <div class="capture-actions">
          {#if !ffmpegStatus.installed}
            <button class="primary" disabled={ffmpegBusy || installing || !ffmpegStatus.bootstrap_available} onclick={bootstrapFfmpeg}>{ffmpegBusy ? 'Checking…' : 'Install FFmpeg'}</button>
          {/if}
          <button disabled={ffmpegBusy || installing} onclick={refreshFfmpeg}>Recheck FFmpeg</button>
        </div>
      </section>
    {/if}
    {#if obsSystem && obsPlan}
      <section class="prerequisite" aria-label="OBS onboarding">
        <div>
          <h3>OBS Studio</h3>
          <p class:passed={obsSystem.running}>{obsSystem.detail}</p>
          {#if obsSystem.path}<p class="scope">{obsSystem.path}</p>{/if}
          {#if obsConnection}
            <p class:passed={obsConnection.state === 'connected'}><strong>WebSocket: {label(obsConnection.state)}</strong><br />{obsConnection.detail}</p>
          {/if}
          {#if obsRecording}
            <p class:passed={obsRecording.accepted}><strong>Recording acceptance: {obsRecording.accepted ? 'Passed' : 'Action required'}</strong><br />{obsRecording.detail}{obsRecording.file_name ? ` · ${obsRecording.file_name}` : ''}{obsRecording.bytes ? ` · ${obsRecording.bytes} bytes` : ''}</p>
          {/if}
          <details>
            <summary>Preview {obsPlan.name} · {obsPlan.scenes.length} scenes</summary>
            <p>{obsPlan.scenes.join(' · ')}</p>
            <p class="scope">Asset {obsPlan.asset_version}. {obsPlan.detail}</p>
          </details>
        </div>
        <div class="capture-actions">
          {#if !obsSystem.installed}
            <button class="primary" disabled={obsBusy || installing || !obsSystem.bootstrap_available} onclick={bootstrapObs}>{obsBusy ? 'Checking…' : 'Install OBS Studio'}</button>
          {:else if !obsSystem.running}
            <button class="primary" disabled={obsBusy || installing} onclick={openObs}>{obsBusy ? 'Opening…' : 'Open OBS Studio'}</button>
          {/if}
          <button disabled={obsBusy || installing} onclick={() => refreshObs(false)}>Recheck OBS</button>
          {#if productKind === 'stream' && obsSystem.running}
            <button disabled={obsBusy || installing} onclick={() => refreshObs(true)}>Test WebSocket</button>
          {/if}
          {#if productKind === 'stream' && obsConnection?.state === 'connected'}
            {#if !preview}<button disabled={obsBusy || installing} onclick={testObsRecording}>{obsBusy ? 'Recording…' : 'Run OBS recording test (3s)'}</button>{/if}
          {/if}
        </div>
      </section>
    {/if}
    {#if dockerStatus && dockerPlan}
      <section class="prerequisite" aria-label="Docker setup">
        <div>
          <h3>Docker-backed local services</h3>
          <p class:passed={dockerStatus.daemon_ready && dockerStatus.compose_ready}><strong>{dockerStateLabel(dockerStatus.state)}</strong><br />{dockerStatus.detail}</p>
          {#if dockerStatus.desktop_path}<p class="scope">{dockerStatus.desktop_path}</p>{/if}
          {#if dockerStatus.wsl_state !== 'not_applicable'}
            <p class:passed={dockerStatus.wsl_state === 'ready'}><strong>WSL: {dockerStateLabel(dockerStatus.wsl_state)}</strong><br />{dockerStatus.wsl_detail}</p>
          {/if}
          <details>
            <summary>Preview selected service plan · {dockerPlan.services.length} services</summary>
            {#if dockerPlan.services.length}
              <ol>{#each dockerPlan.services as service}<li><strong>{service}</strong> · {dockerStatus.service_states[service] ?? 'not started'}</li>{/each}</ol>
            {:else}<p>No selected module needs a container.</p>{/if}
            <p class="scope">Asset {dockerPlan.asset_version}. {dockerPlan.detail}</p>
          </details>
          {#if dockerStatus.docker_version || dockerStatus.engine_version || dockerStatus.compose_version}
            <p class="scope">{[dockerStatus.docker_version, dockerStatus.engine_version ? `Engine ${dockerStatus.engine_version}` : '', dockerStatus.compose_version ? `Compose ${dockerStatus.compose_version}` : ''].filter(Boolean).join(' · ')}</p>
          {/if}
        </div>
        <div class="capture-actions">
          {#if !dockerStatus.desktop_installed && !dockerStatus.daemon_ready}
            <button class="primary" disabled={dockerBusy || installing || !dockerStatus.bootstrap_available} onclick={bootstrapDocker}>{dockerBusy ? 'Checking…' : 'Install Docker Desktop'}</button>
          {:else if dockerStatus.desktop_installed && !dockerStatus.daemon_ready}
            <button class="primary" disabled={dockerBusy || installing} onclick={openDocker}>{dockerBusy ? 'Opening…' : 'Open Docker Desktop'}</button>
          {/if}
          <button disabled={dockerBusy || installing} onclick={() => refreshDocker()}>Recheck Docker</button>
          {#if dockerPlan.services.length}
            <button disabled={dockerBusy || installing || !dockerStatus.start_available || dockerStatus.services_ready} onclick={startDockerServices}>{dockerBusy ? 'Starting…' : dockerStatus.services_ready ? 'Selected services ready' : 'Start selected local services'}</button>
            {#if dockerPlan.services.some(service => ['postgres', 'minio', 'n8n'].includes(service))}
              <button class="primary" disabled={dockerBusy || installing || !dockerStatus.services_ready} onclick={initializeLocalServices}>{dockerBusy ? 'Working…' : 'Initialize data & workflows'}</button>
            {/if}
          {/if}
        </div>
      </section>
    {/if}
    <div class="actions">
      <button class="primary" disabled={!selected.length || busy || saving || installing || !pythonStatus?.installed} onclick={install}>Install selected Python dependencies</button>
      <button disabled={!selected.length || busy || saving || installing} onclick={check}>{busy ? 'Working…' : 'Check readiness'}</button>
    </div>
    <p class="scope">Installation downloads Python packages into shared local environments. Fixed prerequisite actions can install Python, FFmpeg, OBS and Docker Desktop through winget on Windows or an existing Homebrew on macOS. Docker service startup and initialization use the bundled local Compose project and selected module plan; they do not create cloud resources. Drivers, models and live acceptance remain separate.</p>
    <section class="readiness" aria-label="Capability readiness">
      <div class="capture-heading">
        <div><h3>Capability readiness</h3><p>Versioned contract {readiness?.schema_version ?? 1}. Operational controls unlock only from current native evidence.</p></div>
        <span class="contract">Manifest {readiness?.manifest_version ?? '2026.09.1'}</span>
      </div>
      {#each readiness?.capabilities ?? [] as capability}
        <p class:passed={capability.status === 'ready'}><strong>{capability.label}: {label(capability.status)}</strong><br />{capability.summary}</p>
      {:else}<p class="muted">No service evidence has been recorded. Run Check readiness.</p>{/each}
      {#if readiness}<details><summary>Verification evidence ({readiness.checks.length})</summary>
        {#each readiness.checks as item}<p><strong>{item.check_id}: {label(item.status)}</strong><br />{item.summary}</p>{/each}
      </details>{/if}
    </section>
    {#if resolved.includes('audio-production') || resolved.includes('soundboard')}
      <AudioSetup {invoke} onGuide={showGuide} disabled={installing} />
    {/if}
    <section class="capture" aria-label="Capture hardware setup">
      <div class="capture-heading">
        <div><h3>Capture hardware</h3><p>Find local cameras, capture cards and audio inputs without opening a recording stream.</p></div>
        <button disabled={captureBusy || installing} onclick={scanCapture}>{captureBusy ? 'Scanning…' : 'Scan capture hardware'}</button>
      </div>
      {#if captureReport}
        <p class="timestamp">Scanned {new Date(captureReport.checked_at * 1000).toLocaleString()} · {captureReport.status === 'ready_for_obs_setup' ? 'Ready for OBS setup' : 'Action required'}</p>
        <div class="capture-checks">
          <p class:passed={captureReport.obs.found}><strong>OBS Studio: {captureReport.obs.found ? 'Found' : 'Not found'}</strong><br />{captureReport.obs.detail}</p>
          <p class:passed={captureReport.ffmpeg.found}><strong>FFmpeg device names: {captureReport.ffmpeg.found ? 'Available' : 'Not found'}</strong><br />{captureReport.ffmpeg.detail}</p>
        </div>
        <div class="device-fields">
          <label>
            <span>Video device<small>Camera or HDMI capture-card video</small></span>
            <select bind:value={captureVideoId}>
              <option value="">Choose after scanning</option>
              {#each captureReport.video_devices as device}<option value={device.id}>{device.name} · {device.backend}</option>{/each}
            </select>
          </label>
          <label>
            <span>Game audio device<small>Capture-card audio, if exposed separately</small></span>
            <select bind:value={captureAudioId}>
              <option value="">No separate audio device</option>
              {#each captureReport.audio_devices as device}<option value={device.id}>{device.name} · {device.backend}</option>{/each}
            </select>
          </label>
        </div>
        <div class="capture-actions">
          <button disabled={captureBusy || !captureVideoId} onclick={saveCapture}>Save capture choices</button>
          <button disabled={captureBusy || !captureVideoId} onclick={testCapture}>{captureBusy ? 'Testing…' : 'Test selected capture (3s)'}</button>
        </div>
        {#if captureTestReport}
          <section class="capture-test" aria-label="Capture test result">
            <h4>Capture acceptance: {captureTestReport.status === 'accepted' ? 'Passed' : captureTestReport.status === 'signal' ? 'Signal found; recording failed' : 'Action required'}</h4>
            <p>Detected: {captureTestReport.stages.detected ? 'yes' : 'no'} · Signal: {captureTestReport.stages.signal ? 'yes' : 'no'} · Recording: {captureTestReport.stages.recorded ? 'yes' : 'no'} · Accepted: {captureTestReport.stages.accepted ? 'yes' : 'no'}</p>
            {#if captureTestReport.frames_observed !== undefined}<p>{captureTestReport.frames_observed} frames observed{captureTestReport.duration_observed_seconds ? ` over ${captureTestReport.duration_observed_seconds.toFixed(2)}s` : ''} · Video stream: {captureTestReport.video_stream ? 'yes' : 'no'} · Audio stream: {captureTestReport.audio_stream ? 'yes' : 'no'}</p>{/if}
            {#if captureTestReport.error}<p class="error">{captureTestReport.error}</p>{/if}
            <p class="scope">{captureTestReport.scope}</p>
          </section>
        {/if}
        {#if captureReport.windows_pnp_devices.length}
          <details><summary>Windows driver inventory ({captureReport.windows_pnp_devices.length})</summary>
            {#each captureReport.windows_pnp_devices as device}<p>{device.name} · {device.class} · {device.status}</p>{/each}
          </details>
        {/if}
        <ol>{#each captureReport.recommendations as item}<li>{item}</li>{/each}</ol>
        <p class="scope">{captureReport.scope}</p>
      {:else}
        <p class="muted">No scan has been run on this computer. Windows also checks present Camera, Image and Media drivers.</p>
      {/if}
    </section>
    {#if job}
      <section class="job" aria-label="Installation progress" aria-live="polite">
        <h3>{jobHeading(job)}</h3>
        {#if job.status === 'unobserved'}<p>The app closed before it observed completion. Installation may still be running; check readiness and review the log before retrying.</p>{/if}
        {#if job.status === 'failed'}<p>Review the log and retry. Another app may already be installing into the shared environments.</p>{/if}
        {#if job.kind === 'python_bootstrap' && job.status === 'unobserved'}<p>The package manager may still be running. Recheck Python before retrying.</p>{/if}
        {#if job.kind === 'ffmpeg_bootstrap' && job.status === 'unobserved'}<p>The package manager may still be running. Recheck FFmpeg before retrying.</p>{/if}
        {#if job.kind === 'ffmpeg_bootstrap' && job.status === 'finished'}<p>Scan capture hardware again to refresh the device report with the installed FFmpeg helper.</p>{/if}
        {#if job.kind === 'obs_bootstrap' && job.status === 'unobserved'}<p>The package manager may still be running. Recheck OBS before retrying.</p>{/if}
        {#if job.kind === 'docker_bootstrap' && job.status === 'unobserved'}<p>Docker Desktop setup may still be running or waiting for elevation/restart. Recheck Docker before retrying.</p>{/if}
        {#if job.kind === 'docker_services' && job.status === 'unobserved'}<p>Compose may still be pulling, building or starting services. Recheck Docker and review the local log before retrying.</p>{/if}
        {#if job.kind === 'local_service_bootstrap' && job.status === 'unobserved'}<p>A fixed initialization helper may still be running. Review the local log before retrying; every step is safe to run again.</p>{/if}
        {#each job.report?.modules ?? [] as item}<p>{title(item.id)}: {label(item.dependencies)}</p>{/each}
        {#each Object.entries(job.service_states ?? {}) as [service, state]}<p>{service}: {state}</p>{/each}
        {#each Object.entries(job.steps ?? {}) as [step, state]}<p>{label(step)}: {label(state)}</p>{/each}
        {#if job.kind === 'local_service_bootstrap' && job.status === 'finished'}
          <p>{job.credentials_saved ? 'Local service credentials were saved to the operating system credential manager. Creator Extend will reuse the MinIO keys after restart.' : 'The services are initialized. Use the copy actions below to complete UI sign-in.'}</p>
          <div class="capture-actions">
            <button onclick={() => copyLocalCredential('minio_access_key')}>Copy MinIO user</button>
            <button onclick={() => copyLocalCredential('minio_secret_key')}>Copy MinIO password</button>
            {#if job.services?.includes('n8n')}
              <button onclick={() => copyLocalCredential('n8n_user')}>Copy n8n user</button>
              <button onclick={() => copyLocalCredential('n8n_password')}>Copy n8n password</button>
            {/if}
            {#if job.services?.includes('grafana')}
              <button onclick={() => copyLocalCredential('grafana_password')}>Copy Grafana password</button>
            {/if}
            {#if job.services?.includes('fastapi')}
              <button onclick={() => copyLocalCredential('hcp_api_key')}>Copy local API key</button>
            {/if}
          </div>
        {/if}
        {#if job.log_path}<details><summary>Local installation log</summary><code>{job.log_path}</code></details>{/if}
      </section>
    {/if}
    {#if syncSettings && !preview}
      <section class="sync" aria-label="OpenTechnology readiness synchronization">
        <h3>OpenTechnology synchronization</h3>
        <p>Optionally send sanitized readiness observations over an outbound HTTPS connection. Local credentials and paths are never included.</p>
        <div class="device-fields">
          <label><span>OpenTechnology URL</span><input type="url" bind:value={syncSettings.base_url} placeholder="https://tasks.example.com" /></label>
          <label><span>Project ID</span><input bind:value={syncSettings.project_id} autocomplete="off" /></label>
          <label><span>Machine ID<small>Must match the setup item in OpenTechnology</small></span><input bind:value={syncSettings.machine_id} autocomplete="off" /></label>
          <label><span>New API key</span><input type="password" bind:value={newApiKey} autocomplete="new-password" placeholder={syncSettings.api_key_set ? 'Saved in system credentials' : 'Required when enabled'} disabled={clearApiKey} /></label>
        </div>
        <label class="inline"><input type="checkbox" bind:checked={syncSettings.enabled} /> Sync after readiness checks</label>
        <label class="inline"><input type="checkbox" bind:checked={clearApiKey} disabled={!syncSettings.api_key_set || !!newApiKey} /> Clear saved API key</label>
        <div class="actions">
          <button disabled={syncBusy} onclick={saveSyncSettings}>{syncBusy ? 'Working…' : 'Save synchronization settings'}</button>
          <button disabled={syncBusy || !syncSettings.enabled || !readiness} onclick={synchronize}>Sync readiness now</button>
        </div>
      </section>
    {/if}
    {#if report}<p class="timestamp">Checked {new Date(report.checked_at * 1000).toLocaleString()}. Recheck after changing installations or configuration.</p>{/if}
    <div class="selected-modules">
      {#each resolved as id}
        {@const item = catalog.modules[id]}
        {@const result = report?.modules.find(module => module.id === id)}
        <article>
          <h3>{title(id)}</h3>
          {#each result?.checks ?? [] as check}
            <p class:passed={check.status === 'passed'}><strong>{check.name}: {label(check.status)}</strong><br />{check.detail}</p>
          {:else}<p class="muted">{report ? 'No automatic dependency check is available for this selection.' : 'Not checked in this session.'}</p>{/each}
          <p class="remaining"><strong>Still to verify</strong><br />{item.remaining}</p>
          <button onclick={() => showGuide(id)}>Read {title(id)} setup guide</button>
        </article>
      {:else}<p class="empty">Select a module or starter profile to see its setup steps.</p>{/each}
    </div>
    {#if guide}<section class="guide"><h3>{guideTitle} setup guide</h3><p>Repository paths and module commands in this guide may require the full source checkout.</p><button onclick={() => guide = ''}>Close guide</button><pre>{guide}</pre></section>{/if}
  {/if}
</section>

<style>
  .setup { color: #e9e9f0; font-family: inherit; }
  .intro { max-width: 780px; margin-bottom: 1.5rem; }
  .eyebrow { color: #bdadff; font-size: .75rem; letter-spacing: .1em; }
  h2 { color: #e9e9f0; font-size: 1.65rem; margin: .3rem 0; }
  h3 { margin: 0 0 .7rem; }
  p { line-height: 1.5; }
  .profiles, .actions { display: flex; flex-wrap: wrap; gap: .6rem; margin: 1rem 0; }
  fieldset { margin: 0; padding: 1rem; border: 1px solid #494955; border-radius: 10px; }
  legend { padding: 0 .5rem; }
  .module-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .5rem; }
  label { display: flex; gap: .65rem; align-items: flex-start; padding: .7rem; border: 1px solid #393943; border-radius: 7px; background: #1c1c23; }
  label.chosen { border-color: #a08bdc; background: #292236; }
  input { margin-top: .25rem; accent-color: #b89ef5; }
  small { display: block; color: #bcb8c9; font-size: .72rem; margin-top: .25rem; }
  button { padding: .6rem .8rem; border: 1px solid #9d89ce; border-radius: 7px; background: #272031; color: #f4efff; cursor: pointer; font: inherit; font-size: .85rem; }
  button.primary { background: #61429c; }
  button:disabled { opacity: .5; cursor: default; }
  .scope, .timestamp, .muted { color: #bbb8c7; font-size: .85rem; }
  .selected-modules { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem; }
  article, .job, .guide, .capture, .readiness, .sync, .prerequisite { background: #1d1d25; border: 1px solid #42424f; border-radius: 10px; padding: 1rem; margin-top: .7rem; }
  .prerequisite { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem; }
  .prerequisite p { margin: .25rem 0; }
  article p, .job p { font-size: .85rem; }
  .capture-heading { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: 1rem; }
  .capture-heading p { margin: 0; color: #bbb8c7; font-size: .85rem; }
  .capture-actions { display: flex; flex-wrap: wrap; gap: .6rem; margin: .8rem 0; }
  .capture-test { border-left: 3px solid #7c4dff; padding-left: .8rem; margin-top: .8rem; }
  .capture-checks, .device-fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: .7rem; margin: .8rem 0; }
  .device-fields label { display: grid; gap: .5rem; }
  select { width: 100%; padding: .55rem; border: 1px solid #5a5665; border-radius: 6px; background: #15151b; color: #f4efff; font: inherit; }
  input:not([type="checkbox"]) { width: 100%; box-sizing: border-box; padding: .55rem; border: 1px solid #5a5665; border-radius: 6px; background: #15151b; color: #f4efff; font: inherit; }
  .inline { display: inline-flex; align-items: center; gap: .45rem; margin: .3rem 1rem .3rem 0; padding: 0; border: 0; background: transparent; }
  .contract { color: #c8b7ee; font-size: .78rem; }
  ol { padding-left: 1.25rem; color: #d1ceda; font-size: .85rem; line-height: 1.5; }
  .remaining { border-top: 1px solid #42424f; padding-top: .75rem; }
  .passed, .notice { color: #a4d9b1; }
  .error { padding: .8rem; border: 1px solid #b66565; background: #382323; color: #ffcccc; border-radius: 8px; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.5; font-size: .8rem; }
  code { overflow-wrap: anywhere; }
  :focus-visible { outline: 2px solid #c6b2f2; outline-offset: 3px; }
</style>
