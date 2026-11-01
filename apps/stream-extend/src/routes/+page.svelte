<script lang="ts">
  import ModuleSetup from '../../../shared/ui/ModuleSetup.svelte';
  import ProfileSwitcher from '../../../shared/ui/ProfileSwitcher.svelte';
  import RemoteControl from '../../../shared/ui/RemoteControl.svelte';
  import SocialManagement from '../../../shared/ui/SocialManagement.svelte';
  import Autopilot from '../lib/Autopilot.svelte';
  let activeView = $state('setup');
  import { invoke } from '@tauri-apps/api/core';
  import { open as openExternal } from '@tauri-apps/plugin-shell';
  import { onMount } from 'svelte';
  import { listen } from '@tauri-apps/api/event';

  type SceneInfo = { name: string; index: number; is_current: boolean };
  type ReadinessSnapshot = { capabilities: { capability_id: string; status: string; summary: string }[] };
  type ConnectionConfig = {
    obs_host: string; obs_port: number; obs_password_set: boolean;
    comfyui_url: string; grafana_url: string; api_url: string;
  };
  type ActiveSelection = { profile_id: string };
  type StreamSessionReport = {
    stream_active: boolean; recording_active: boolean; recording_owned: boolean;
    detail: string; handoff: { file_name: string } | null;
  };

  // State
  let obsConnected = $state(false);
  let obsConnecting = $state(false);
  let obsError = $state('');
  let autopilotStopMessage = $state('');
  let autopilotStopping = $state(false);
  let scenes: SceneInfo[] = $state([]);
  let streaming = $state(false);
  let sessionBusy = $state(false);
  let recordingOwned = $state(false);
  let recordingMessage = $state('');
  let connectionConfig: ConnectionConfig = $state({
    obs_host: 'localhost', obs_port: 4455, obs_password_set: false,
    comfyui_url: 'http://localhost:8188', grafana_url: 'http://localhost:3000', api_url: 'http://localhost:8000',
  });
  let newObsPassword = $state('');
  let clearObsPassword = $state(false);
  let settingsBusy = $state(false);
  let settingsMessage = $state('');
  let settingsError = $state('');
  let readiness = $state<ReadinessSnapshot | null>(null);
  let canObsControl = $derived(readiness?.capabilities.some(item => item.capability_id === 'obs-control' && item.status === 'ready') ?? false);

  // Stats
  let streamStats = $state({
    kbitsPerSec: 0,
    skippedFrames: 0,
    totalFrames: 0,
  });

  onMount(() => {
    void loadConnectionSettings();
    void loadReadiness();
    refreshStatus();
    // Poll every 2 seconds
    const interval = setInterval(refreshStatus, 2000);
    const stopListener = listen<string>('autopilot-shutdown-error', event => { autopilotStopMessage = 'Quit paused: ' + event.payload; });
    return () => { clearInterval(interval); void stopListener.then(unlisten => unlisten()); };
  });

  async function stopAutopilot() {
    if (autopilotStopping) return;
    autopilotStopping = true;
    try {
      const result = await invoke<{ ok: boolean; status?: { lifecycle: string } }>('autopilot_production_action', { action: 'emergency_stop', operationId: crypto.randomUUID(), sourceProfileId: null, contentProfileId: null });
      autopilotStopMessage = result.ok && result.status?.lifecycle === 'stopped' ? 'Owned AI runtime stopped.' : 'Stop is not confirmed. Open Automated streaming and check local effects.';
    } catch (value) { autopilotStopMessage = String(value); }
    finally { autopilotStopping = false; }
  }

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
        obs_host: connectionConfig.obs_host,
        obs_port: Number(connectionConfig.obs_port),
        obs_password: newObsPassword || null,
        clear_obs_password: clearObsPassword,
        comfyui_url: connectionConfig.comfyui_url,
        grafana_url: connectionConfig.grafana_url,
        api_url: connectionConfig.api_url,
      }});
      newObsPassword = ''; clearObsPassword = false;
      settingsMessage = 'Connection settings saved on this device.';
      await refreshStatus();
      if (testAfterSave) {
        const result = await invoke<ReadinessSnapshot>('setup_refresh_readiness');
        updateReadiness(result);
        settingsMessage = result.capabilities.some(item => item.capability_id === 'obs-control' && item.status === 'ready')
          ? 'Saved and connected to OBS.'
          : 'Saved. OBS did not answer yet; check OBS WebSocket settings and retry.';
      }
    } catch (e) { settingsError = String(e); }
    finally { settingsBusy = false; }
  }

  async function refreshStatus() {
    obsConnecting = true;
    try {
      const status = await invoke('obs_status');
      obsConnected = (status as any).connected;

      if (obsConnected) {
        const sceneList = await invoke('obs_scenes');
        scenes = sceneList as SceneInfo[];

        const streamStatus = await invoke('obs_stream_status');
        streaming = (streamStatus as any).active;
        streamStats = {
          kbitsPerSec: (streamStatus as any).kbits_per_sec || 0,
          skippedFrames: (streamStatus as any).skipped_frames || 0,
          totalFrames: (streamStatus as any).total_frames || 0,
        };
      }
    } catch (e) {
      console.error('Status refresh failed:', e);
    } finally {
      obsConnecting = false;
    }
  }

  async function switchScene(name: string) {
    obsError = '';
    try {
      scenes = (await invoke('obs_switch_scene', { sceneName: name })) as SceneInfo[];
    } catch (e: any) {
      obsError = e?.message ?? String(e);
      console.error('Scene switch failed:', e);
    }
  }

  async function toggleStream() {
    obsError = '';
    recordingMessage = '';
    sessionBusy = true;
    try {
      let result: StreamSessionReport;
      if (streaming) {
        result = await invoke<StreamSessionReport>('obs_stop_stream_session');
      } else {
        let sourceProfileId: string | null = null;
        let contentProfileId: string | null = null;
        try {
          sourceProfileId = (await invoke<ActiveSelection>('plugin:social-manager|selection', { kind: 'stream' })).profile_id;
          contentProfileId = (await invoke<ActiveSelection>('plugin:social-manager|selection', { kind: 'content' })).profile_id;
        } catch (cause) {
          console.warn('Profile routing unavailable; starting the local session without profile metadata.', cause);
        }
        result = await invoke<StreamSessionReport>('obs_start_stream_session', { sourceProfileId, contentProfileId });
      }
      streaming = result.stream_active;
      recordingOwned = result.recording_owned && result.stream_active;
      recordingMessage = result.detail;
    } catch (e: any) {
      obsError = e?.message ?? String(e);
      console.error('Toggle stream failed:', e);
    } finally {
      sessionBusy = false;
    }
  }

</script>

<main>
  <header>
    <h1>Stream Extend</h1>
    <ProfileSwitcher {invoke} kind="stream" />
    <button class="btn" disabled={autopilotStopping} onclick={stopAutopilot}>Emergency stop runtime</button>
    <div class="status-bar">
      <span class="indicator" class:connected={obsConnected}>
        OBS {obsConnected ? 'Connected' : obsConnecting ? 'Connecting…' : 'Disconnected'}
      </span>
    </div>
  </header>
  {#if autopilotStopMessage}<p role="status">{autopilotStopMessage}</p>{/if}

  <nav class="workspace-tabs" aria-label="Workspace view">
    <button aria-pressed={activeView === 'setup'} onclick={() => activeView = 'setup'}>Module setup</button>
    <button aria-pressed={activeView === 'connections'} onclick={() => activeView = 'connections'}>Connections</button>
    <button aria-pressed={activeView === 'remote'} onclick={() => activeView = 'remote'}>Remote control</button>
    <button aria-pressed={activeView === 'social'} onclick={() => activeView = 'social'}>Social</button>
    <button aria-pressed={activeView === 'autopilot'} onclick={() => activeView = 'autopilot'}>Automated streaming</button>
    <button aria-pressed={activeView === 'dashboard'} onclick={() => activeView = 'dashboard'}>Dashboard</button>
  </nav>
  {#if activeView === 'setup'}
    <ModuleSetup {invoke} onReadiness={updateReadiness} productKind="stream" />
  {:else if activeView === 'connections'}
    <section class="panel settings" aria-label="Connection settings">
      <h2>Connection settings</h2>
      <p>Endpoints are stored locally. The OBS password is stored in the operating system credential manager and is never displayed after saving.</p>
      {#if settingsError}<p class="obs-error" role="alert">{settingsError}</p>{/if}
      {#if settingsMessage}<p class="settings-success" role="status">{settingsMessage}</p>{/if}
      <div class="settings-grid">
        <label>OBS host <input bind:value={connectionConfig.obs_host} autocomplete="off" /></label>
        <label>OBS WebSocket port <input type="number" min="1" max="65535" bind:value={connectionConfig.obs_port} /></label>
        <label>New OBS password <input type="password" bind:value={newObsPassword} autocomplete="new-password" placeholder={connectionConfig.obs_password_set ? 'Saved in system credentials' : 'Optional'} disabled={clearObsPassword} /></label>
        <label class="check"><input type="checkbox" bind:checked={clearObsPassword} disabled={!connectionConfig.obs_password_set || !!newObsPassword} /> Clear saved OBS password</label>
        <label>ComfyUI URL <input type="url" bind:value={connectionConfig.comfyui_url} /></label>
        <label>Grafana URL <input type="url" bind:value={connectionConfig.grafana_url} /></label>
        <label>Platform API URL <input type="url" bind:value={connectionConfig.api_url} /></label>
      </div>
      <div class="settings-actions">
        <button disabled={settingsBusy} onclick={() => saveConnectionSettings(false)}>{settingsBusy ? 'Saving…' : 'Save settings'}</button>
        <button disabled={settingsBusy} onclick={() => saveConnectionSettings(true)}>Save and test OBS</button>
      </div>
    </section>
  {:else if activeView === 'remote'}
    <RemoteControl {invoke} kind="stream" hostedLabel="Stream Extend Cloud (subscription)" actionDescription="OBS scene changes and stream start or stop are supported." />
  {:else if activeView === 'social'}
    <SocialManagement {invoke} {openExternal} preferredKind="stream" />
  {:else if activeView === 'autopilot'}
    <Autopilot {invoke} />
  {:else}
  <div class="dashboard">
    <!-- OBS Control Panel -->
    <section class="panel">
      <h2>OBS Control</h2>

      {#if obsError}
        <p class="obs-error">{obsError}</p>
      {/if}
      {#if recordingMessage}
        <p class="recording-message" role="status">{recordingMessage}</p>
      {/if}

      {#if !canObsControl && !streaming}
        <p class="hint">OBS controls are locked until the current WebSocket and scene checks pass. Open Module setup and run Check readiness.</p>
      {:else}
        <div class="scenes">
          <h3>Scenes</h3>
          {#each scenes as scene}
            <button
              class="scene-btn"
              class:active={scene.is_current}
              disabled={!canObsControl}
              onclick={() => switchScene(scene.name)}
            >
              {scene.name}
            </button>
          {/each}
        </div>

        <div class="stream-control">
          <button
            class="stream-btn"
            class:live={streaming}
            disabled={sessionBusy || (!streaming && !canObsControl)}
            onclick={toggleStream}
          >
            {sessionBusy ? 'Working…' : streaming ? '⬛ Stop + Send to Creator' : '🔴 Go Live + Record'}
          </button>
        </div>

        {#if streaming}
          <div class="stats">
            <span>{streamStats.kbitsPerSec.toFixed(0)} kbps</span>
            <span>Skipped: {streamStats.skippedFrames}/{streamStats.totalFrames}</span>
            <span>{recordingOwned ? 'Recording for Creator Extend' : 'External recording not owned'}</span>
          </div>
        {/if}
      {/if}
    </section>

    <!-- Quick Links -->
    <section class="panel">
      <h2>Services</h2>
      <div class="service-links">
        <a href="http://localhost:3000" target="_blank">Grafana Dashboards</a>
        <a href="http://localhost:8000/docs" target="_blank">Platform API</a>
        <a href="http://localhost:5678" target="_blank">n8n Automation</a>
        <a href="http://localhost:9091" target="_blank">NodeCG Overlays</a>
      </div>
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
  }

  h1 { color: #ff6b35; margin: 0; }
  h2 { color: #ff6b35; margin-top: 0; }

  .status-bar {
    display: flex;
    gap: 1rem;
  }

  .indicator {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.85rem;
    background: #2a2a2a;
    color: #888;
  }

  .indicator.connected {
    background: #1a3a1a;
    color: #4caf50;
  }

  .dashboard {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .panel {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .panel:first-child {
    grid-column: 1 / -1;
  }

  .scenes {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .scene-btn {
    padding: 0.5rem 1rem;
    border: 1px solid #444;
    border-radius: 8px;
    background: #2a2a2a;
    color: #e0e0e0;
    cursor: pointer;
    transition: all 0.2s;
  }

  .scene-btn:hover { border-color: #ff6b35; }
  .scene-btn.active { background: #ff6b35; color: white; border-color: #ff6b35; }

  .stream-btn {
    padding: 0.75rem 2rem;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    cursor: pointer;
    background: #333;
    color: white;
    transition: all 0.2s;
  }

  .stream-btn.live { background: #d32f2f; }
  .stream-btn:hover { opacity: 0.9; }

  .stats {
    display: flex;
    gap: 1.5rem;
    margin-top: 0.75rem;
    font-size: 0.85rem;
    color: #888;
  }

  .service-links {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .service-links a {
    color: #6db3f2;
    text-decoration: none;
    padding: 0.5rem;
    border-radius: 6px;
    transition: background 0.2s;
  }

  .service-links a:hover {
    background: #2a2a2a;
  }

  .hint {
    color: #888;
    font-size: 0.9rem;
  }

  .obs-error {
    color: #f44336;
    font-size: 0.85rem;
    margin: 0.5rem 0;
  }

  .recording-message { color: #a4d9b1; font-size: .88rem; }

  button {
    padding: 0.5rem 1.5rem;
    border: 1px solid #ff6b35;
    border-radius: 8px;
    background: transparent;
    color: #ff6b35;
    cursor: pointer;
    font-size: 0.9rem;
  }

  button:hover {
    background: #ff6b35;
    color: white;
  }
</style>
