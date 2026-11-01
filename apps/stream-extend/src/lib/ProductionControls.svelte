<script lang="ts">
  import { onMount } from 'svelte';
  type Runtime = {
    ok: boolean; error?: string; session_id: string; broadcast_control_enabled: boolean; avatar_enabled: boolean;
    policy: { broadcast_start_authorized: boolean; gameplay_enabled: boolean; local_run_authorized: boolean; mode: string };
    status?: { lifecycle: string; revision: number; ready: boolean; resume_required: boolean; last_error: string | null;
      checks: { id: string; status: string; detail: string }[] };
    worker_states: Record<string, string>;
  };
  let { invoke }: { invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T> } = $props();
  let runtime: Runtime | null = $state(null);
  let error = $state('');
  let busy = $state(false);
  let stopping = $state(false);
  let polling = $state(false);
  let serial = 0;
  let disposed = false;
  let connected = $state(true);
  function observe(value: Runtime) {
    if (value.status && (!runtime?.status || value.status.revision >= runtime.status.revision)) runtime = value;
  }
  async function refresh() {
    if (polling || !connected) return;
    polling = true;
    const version = serial;
    try { const value = await invoke<Runtime>('autopilot_production_status'); if (!disposed && connected && version === serial) observe(value); }
    catch (value) { if (!disposed) error = String(value); }
    finally { polling = false; }
  }
  async function action(name: string) {
    if ((name === 'stop' || name === 'emergency_stop') && stopping) return;
    if (name === 'stop' || name === 'emergency_stop') stopping = true;
    const request = ++serial;
    busy = true; error = ''; connected = true;
    try {
      let sourceProfileId: string | null = null, contentProfileId: string | null = null;
      if (name === 'run') {
        sourceProfileId = (await invoke<{profile_id:string}>('plugin:social-manager|selection', {kind:'stream'})).profile_id;
        contentProfileId = (await invoke<{profile_id:string}>('plugin:social-manager|selection', {kind:'content'})).profile_id;
      }
      const result = await invoke<Runtime>('autopilot_production_action', { action: name, operationId: crypto.randomUUID(), sourceProfileId, contentProfileId });
      if (disposed || request !== serial) return;
      observe(result);
      if (!result.ok) error = result.error === 'busy' ? 'Another action is still running. Recheck or use Emergency stop.' : 'The runtime rejected this action. Review state and prerequisites.';
    } catch (value) { if (!disposed && request === serial) error = String(value); }
    finally { if (name === 'stop' || name === 'emergency_stop') stopping = false; if (request === serial) busy = false; }
  }
  async function disconnect() {
    const request = ++serial;
    busy = true; error = '';
    try { await invoke('autopilot_production_disconnect'); connected = false; runtime = null; }
    catch (value) { if (!disposed) error = String(value); }
    finally { if (request === serial) busy = false; }
  }
  async function prepareGame() {
    busy = true; error = '';
    try { const result = await invoke<{installed:boolean}>('autopilot_prepare_game'); if (!result.installed) error = 'Optional game package is not ready.'; }
    catch (value) { error = String(value); }
    finally { busy = false; }
  }
  onMount(() => {
    disposed = false; void refresh();
    const timer = setInterval(() => { void refresh(); }, 1500);
    return () => { disposed = true; clearInterval(timer); };
  });
  let lifecycle = $derived.by(() => { const value = runtime as Runtime | null; return value?.status?.lifecycle ?? 'unavailable'; });
</script>

<section aria-label="Production runtime controls">
  <h3>Local production runtime</h3>
  <p>Owns the configured local pipeline. Rehearsal state is separate. Live start and gameplay stay locked unless the operator configuration explicitly enables them.</p>
  {#if error}<p role="alert" class="error">{error}</p>{/if}
  {#if runtime}
    <p><strong>{runtime.session_id} · {lifecycle}</strong></p>
    <p>Live start: {runtime.policy?.broadcast_start_authorized ? 'Authorized in local policy' : 'Locked'} · Gameplay: {runtime.policy?.gameplay_enabled ? 'Enabled in local policy' : 'Disabled'}</p>
    {#if runtime.status?.last_error}<p class="error">{runtime.status.last_error}</p>{/if}
    {#each runtime.status?.checks ?? [] as check}<p><strong>{check.id}: {check.status}</strong> · {check.detail}</p>{/each}
    {#if Object.keys(runtime.worker_states ?? {}).length}<p>Workers: {Object.entries(runtime.worker_states).map(([name, status]) => `${name}: ${status}`).join(' · ')}</p>{/if}
  {/if}
  <div class="actions">
    <button disabled={busy} onclick={() => action('preflight')}>Check production readiness</button>
    <button disabled={busy || !runtime?.status?.ready || !['preflight','preview','degraded'].includes(lifecycle)} onclick={() => action('preview')}>Start local preview</button>
    <button disabled={busy || lifecycle !== 'preview' || !!runtime?.status?.resume_required || !(runtime?.policy?.local_run_authorized || (runtime?.policy?.broadcast_start_authorized && runtime?.broadcast_control_enabled))} onclick={() => action('run')}>{runtime?.broadcast_control_enabled ? 'Run authorized broadcast' : 'Run authorized local session'}</button>
    <button disabled={busy || !['preview','running'].includes(lifecycle)} onclick={() => action('pause')}>Pause output</button>
    <button disabled={busy || lifecycle !== 'paused'} onclick={() => action('resume')}>Resume to preview</button>
    <button disabled={!runtime || stopping} onclick={() => action('stop')}>Stop runtime</button>
    <button class="emergency" disabled={stopping} onclick={() => action('emergency_stop')}>Emergency stop</button>
    <button disabled={polling} onclick={() => { connected = true; void refresh(); }}>Recheck state</button>
    <button disabled={busy} onclick={() => action('reconcile')}>Verify OBS is inactive</button>
    <button disabled={busy || !runtime} onclick={disconnect}>Close production owner</button>
  </div>
  <details><summary>Optional private-world game setup</summary><p>Requires Node.js 22+ and an explicitly permitted private test world. Preparing the pinned SDK starts no game client. Stop the runtime before preparing dependencies.</p><button disabled={busy || !['stopped','degraded','unavailable'].includes(lifecycle)} onclick={prepareGame}>Prepare optional Minecraft package</button></details>
  <div class="actions" aria-label="Owned avatar cues">
    {#each ['wave','nod','shrug','look_left','look_right','happy','surprised','neutral'] as cue}
      <button disabled={busy || !runtime?.avatar_enabled || !['preview','running'].includes(lifecycle)} onclick={() => action('cue_' + cue)}>{cue.replaceAll('_',' ')}</button>
    {/each}
  </div>
  <p class="note">Cue requests use the configured owned model; queue acknowledgement does not prove visible motion.</p>
  <p class="note">Connection/policy changes apply after closing the production owner. OBS recordings use the shared Creator inbox. Preview can run local model/voice workers after readiness passes. It is an explicit operator action. A green check is not audible, visible, gameplay or performance acceptance.</p>
</section>
<style>
section {background:#1a1a1a;border:1px solid #333;border-radius:12px;padding:1.25rem;}
h3 {margin-top:0;} p {color:#bbb;line-height:1.5;}
.actions {display:flex;flex-wrap:wrap;gap:.6rem;}
button {background:#24242c;color:#eee;border:1px solid #666;border-radius:7px;padding:.65rem .85rem;cursor:pointer;}
button:disabled {opacity:.5;cursor:default;} .emergency {border-color:#ff8c8c;color:#ffbcbc;} .error {color:#ff8c8c;} .note {font-size:.8rem;}
</style>
