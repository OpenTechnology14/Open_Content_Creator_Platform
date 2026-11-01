<script lang="ts">
  import { onMount } from 'svelte';

  type Invoke = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  type Settings = {
    mode: 'local' | 'hosted' | 'self-hosted'; enabled: boolean;
    self_hosted_url: string | null; hosted_token_set: boolean;
    self_hosted_token_set: boolean; device_id: string; device_name: string;
  };
  type Pending = { id: string; source_device_id: string; target: string; action: string; summary: string };
  type Outgoing = { id: string; target_device_id: string; action: string; status: string; message: string };
  type Device = { device_id: string; device_name: string; product: 'StreamExtend' | 'CreatorExtend' };
  type Runtime = { status: string; last_error: string | null; subscription_tier: string | null; pending: Pending[]; outgoing: Outgoing[]; devices: Device[] };
  type Props = { invoke: Invoke; hostedLabel: string; actionDescription: string; kind: 'stream' | 'creator' };

  let { invoke, hostedLabel, actionDescription, kind }: Props = $props();
  let settings: Settings = $state({
    mode: 'local', enabled: false, self_hosted_url: null,
    hosted_token_set: false, self_hosted_token_set: false,
    device_id: '', device_name: '',
  });
  let runtime: Runtime = $state({ status: 'disconnected', last_error: null, subscription_tier: null, pending: [], outgoing: [], devices: [] });
  let token = $state('');
  let clearToken = $state(false);
  let busy = $state(false);
  let message = $state('');
  let error = $state('');
  let targetDeviceId = $state('');
  let sceneName = $state('Gameplay');
  let workflowPath = $state('');

  onMount(() => {
    void load();
    const interval = setInterval(refresh, 1500);
    return () => clearInterval(interval);
  });

  function tokenIsSet() {
    return settings.mode === 'hosted' ? settings.hosted_token_set : settings.self_hosted_token_set;
  }

  async function load() {
    try {
      settings = await invoke<Settings>('remote_get_settings');
      await refresh();
    } catch (cause) { error = String(cause); }
  }

  async function refresh() {
    try {
      runtime = await invoke<Runtime>('remote_status');
      if (targetDeviceId && !runtime.devices.some((device) => device.device_id === targetDeviceId)) {
        targetDeviceId = '';
      }
    }
    catch (cause) { error = String(cause); }
  }

  async function save() {
    busy = true; error = ''; message = '';
    try {
      settings = await invoke<Settings>('remote_save_settings', { settings: {
        mode: settings.mode,
        enabled: settings.enabled,
        self_hosted_url: settings.self_hosted_url || null,
        access_token: token || null,
        clear_access_token: clearToken,
        device_name: settings.device_name,
      }});
      token = ''; clearToken = false;
      message = 'Remote settings saved. Relay credentials stay in the operating system credential manager.';
      await refresh();
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function connect() {
    busy = true; error = ''; message = '';
    try {
      runtime = await invoke<Runtime>('remote_connect');
      message = 'Connection started. Authentication status will update here.';
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function disconnect() {
    busy = true;
    try { runtime = await invoke<Runtime>('remote_disconnect'); message = 'Remote control disconnected.'; }
    catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function decide(id: string, approve: boolean) {
    error = ''; message = '';
    try {
      if (approve) await invoke('remote_approve', { id });
      else await invoke('remote_deny', { id });
      message = approve ? 'Approved action completed and the result was returned.' : 'Request denied.';
      await refresh();
    } catch (cause) { error = String(cause); await refresh(); }
  }

  async function request(target: string, action: string, payload: Record<string, unknown>) {
    error = ''; message = '';
    try {
      const id = await invoke<string>('remote_request', { targetDeviceId, target, action, payload });
      message = `Request ${id} sent. It must be approved on the target device.`;
    } catch (cause) { error = String(cause); }
  }
</script>

<section class="remote" aria-label="Remote control">
  <div class="heading">
    <div><h2>Remote control</h2><p>Control this workstation through an authenticated relay. Media and game processing remain local.</p></div>
    <span class:connected={runtime.status === 'connected'}>{runtime.status}</span>
  </div>

  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if message}<p class="success" role="status">{message}</p>{/if}
  {#if runtime.last_error && runtime.status !== 'connected'}<p class="hint">Last relay message: {runtime.last_error}</p>{/if}

  <div class="grid">
    <fieldset>
      <legend>Relay mode</legend>
      <label class="check"><input type="radio" bind:group={settings.mode} value="local" /> Local only</label>
      <label class="check"><input type="radio" bind:group={settings.mode} value="hosted" /> {hostedLabel}</label>
      <label class="check"><input type="radio" bind:group={settings.mode} value="self-hosted" /> Self-hosted relay</label>
    </fieldset>
    <label>Device name <input bind:value={settings.device_name} maxlength="80" autocomplete="off" /></label>
    {#if settings.mode === 'self-hosted'}
      <label>Relay URL <input type="url" bind:value={settings.self_hosted_url} placeholder="https://relay.example.com" /></label>
    {/if}
    {#if settings.mode !== 'local'}
      <label>New relay access token
        <input type="password" bind:value={token} autocomplete="new-password" placeholder={tokenIsSet() ? 'Saved in system credentials' : 'Required'} disabled={clearToken} />
      </label>
      <label class="check"><input type="checkbox" bind:checked={clearToken} disabled={!tokenIsSet() || !!token} /> Clear saved token</label>
      <label class="check"><input type="checkbox" bind:checked={settings.enabled} /> Enable remote requests on startup</label>
    {/if}
  </div>
  <p class="device">Device ID: <code>{settings.device_id || 'created on first save'}</code></p>
  <div class="actions">
    <button disabled={busy} onclick={save}>{busy ? 'Working…' : 'Save settings'}</button>
    {#if settings.mode !== 'local' && settings.enabled && runtime.status !== 'connected' && runtime.status !== 'connecting'}
      <button disabled={busy} onclick={connect}>Connect now</button>
    {/if}
    {#if runtime.status === 'connected' || runtime.status === 'connecting' || runtime.status === 'reconnecting'}
      <button class="secondary" disabled={busy} onclick={disconnect}>Disconnect</button>
    {/if}
  </div>

  <div class="controller">
    <h3>Control another device</h3>
    <p>Connected devices on this account appear automatically. The target still approves every request before it runs.</p>
    <div class="grid">
      <label>Target device
        <select bind:value={targetDeviceId} disabled={runtime.status !== 'connected'}>
          <option value="">{runtime.devices.length ? 'Choose a connected device' : 'Waiting for another device'}</option>
          {#each runtime.devices as device (device.device_id)}
            <option value={device.device_id}>{device.device_name} · {device.device_id.slice(0, 8)}</option>
          {/each}
        </select>
      </label>
      {#if kind === 'stream'}
        <label>OBS scene <input bind:value={sceneName} maxlength="128" /></label>
      {:else}
        <label>Committed workflow path <input bind:value={workflowPath} maxlength="512" placeholder="modules/.../workflow.json" /></label>
      {/if}
    </div>
    <div class="actions">
      {#if kind === 'stream'}
        <button disabled={runtime.status !== 'connected' || !targetDeviceId || !sceneName} onclick={() => request('obs', 'switch_scene', { scene: sceneName })}>Request scene change</button>
        <button class="danger" disabled={runtime.status !== 'connected' || !targetDeviceId} onclick={() => request('obs', 'toggle_stream', {})}>Request start or stop stream</button>
      {:else}
        <button disabled={runtime.status !== 'connected' || !targetDeviceId || !workflowPath} onclick={() => request('comfyui', 'queue_workflow', { workflow_path: workflowPath })}>Request workflow run</button>
      {/if}
    </div>
  </div>

  <div class="approval">
    <h3>Pending approvals <small>{runtime.pending.length}</small></h3>
    <p>{actionDescription} Each request waits here until it is approved on this device.</p>
    {#if runtime.pending.length === 0}
      <p class="empty">No remote requests are waiting.</p>
    {:else}
      {#each runtime.pending as request (request.id)}
        <article>
          <div><strong>{request.summary}</strong><small>From {request.source_device_id} · {request.target}/{request.action} · {request.id}</small></div>
          <div class="actions"><button onclick={() => decide(request.id, true)}>Approve and run</button><button class="danger" onclick={() => decide(request.id, false)}>Deny</button></div>
        </article>
      {/each}
    {/if}
  </div>
  {#if runtime.outgoing.length}
    <div class="approval">
      <h3>Sent requests</h3>
      {#each runtime.outgoing.slice().reverse() as request (request.id)}
        <article>
          <div><strong>{request.action} · {request.status}</strong><small>To {request.target_device_id} · {request.message}</small></div>
        </article>
      {/each}
    </div>
  {/if}
</section>

<style>
  .remote { max-width: 850px; background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem; }
  .heading { display: flex; justify-content: space-between; gap: 1rem; align-items: start; }
  h2 { color: #ff6b35; margin: 0; } h3 { margin-bottom: .25rem; } p { color: #aaa; }
  .heading span { text-transform: capitalize; padding: .3rem .8rem; border-radius: 1rem; background: #2a2a2a; color: #aaa; }
  .heading span.connected { background: #193a24; color: #71d28d; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin: 1.25rem 0; }
  label { display: grid; gap: .4rem; color: #ccc; font-size: .88rem; }
  label.check { display: flex; flex-direction: row; align-items: center; align-self: end; }
  input:not([type="checkbox"]):not([type="radio"]), select { padding: .65rem; border: 1px solid #494955; border-radius: 6px; background: #15151b; color: #f1eef6; font: inherit; }
  fieldset { border: 1px solid #494955; border-radius: 6px; display: grid; gap: .45rem; } legend { color: #ccc; font-size: .88rem; }
  .actions { display: flex; gap: .6rem; flex-wrap: wrap; }
  button { padding: .55rem 1rem; border: 1px solid #ff6b35; border-radius: 8px; background: transparent; color: #ff9a74; cursor: pointer; }
  button:hover { background: #ff6b35; color: white; } button:disabled { opacity: .5; cursor: wait; }
  button.secondary { border-color: #777; color: #bbb; } button.danger { border-color: #dd5c5c; color: #ff8d8d; }
  .device { font-size: .8rem; } code { user-select: all; }
  .approval { border-top: 1px solid #333; margin-top: 1.5rem; padding-top: 1rem; }
  .controller { border-top: 1px solid #333; margin-top: 1.5rem; padding-top: 1rem; }
  .approval h3 small { color: #999; font-weight: normal; }
  article { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 1rem; background: #222; border-radius: 8px; margin-top: .7rem; }
  article div:first-child { display: grid; gap: .35rem; } article small { color: #888; overflow-wrap: anywhere; }
  .empty, .hint { color: #888; } .error { color: #ff8585; } .success { color: #a4d9b1; }
</style>
