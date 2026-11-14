<script lang="ts">
  import { onMount } from 'svelte';
  type Invoke = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  import { ProductionClient, initialProductionView } from './production-client.js';
  let { id, invoke, enabled, showTasks }: { id: string; invoke: Invoke; enabled: boolean; showTasks: boolean } = $props();
  let view = $state(initialProductionView());
  let client: ProductionClient | null = null;
  let armed = $state(false);
  const status = $derived(view.status);
  const hasSession = $derived(Boolean(status?.session_id));
  const output = (value: boolean | null | undefined) => value == null ? 'unknown' : value ? 'active' : 'inactive';
  $effect(() => { const selected = enabled; client?.setEnabled(selected); });
  onMount(() => {
    client = new ProductionClient(invoke, next => view = next);
    client.setEnabled(enabled);
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => { if(alive) await client?.refresh(); if(alive) timer=setTimeout(poll,2500); };
    void poll();
    return () => { alive=false; clearTimeout(timer); client?.close(); };
  });
  export function beginConnectionChange() { client?.beginConnectionChange(); }
  export function endConnectionChange() { client?.endConnectionChange(); }
  async function act(command: string, args?: Record<string,unknown>) { await client?.act(command,args); if(command==='production_start_recording') armed=false; }
</script>

{#if enabled || hasSession}
  <section {id} tabindex="-1" class="production" aria-label="OBS production controls">
    <div class="safety" aria-label="OBS status and safety controls">
      <div role="status"><strong>OBS {view.unknown ? 'status unavailable' : status?.connected ? 'connected' : 'not checked'}</strong>
        <span>Stream: {view.unknown ? 'unknown' : output(status?.stream_active)} · Recording: {view.unknown ? 'unknown' : output(status?.recording_active)}</span>
        {#if hasSession}<span>Source: {status?.source_profile_id} → Content: {status?.content_profile_id}</span>{/if}
        {#if status?.recording_active && !status?.owned && !hasSession}<span>External recording · control it in OBS</span>{/if}
      </div>
      {#if hasSession && !status?.recovery_required && (status?.handoff_pending || status?.managed_recording_available)}
        <button class="stop" disabled={view.working} onclick={() => act('production_stop_recording', { sessionId: status?.session_id })}>{status?.handoff_pending ? 'Retry inbox handoff' : 'Stop owned recording'}</button>
      {/if}
      {#if status?.recovery_required}<p>Recording continuity is unproven. Inspect and stop the output in OBS, then recover when inactive. No external recording will be attributed.</p><button disabled={view.working} onclick={() => act('production_recover', { sessionId: status?.session_id })}>Recover after OBS is inactive</button>{/if}
      {#if hasSession && !status?.managed_recording_available && !status?.handoff_pending}<p>Managed Stop is unavailable. Finish the output in OBS; refresh and recover only after it is inactive.</p>{/if}
      <button disabled={view.working} onclick={() => client?.refresh()}>Refresh OBS status</button>
    </div>
    {#if view.inputs.length}<div class="audio" aria-label="OBS input mute controls">{#each view.inputs as input}<button disabled={view.working} aria-pressed={input.muted} onclick={() => client?.setMute(input)}>{input.muted ? 'Unmute' : 'Mute'} {input.name}</button>{/each}</div>{/if}
    {#if !view.inputs.length}<p role="status">Audio status {view.audioLoading ? 'loading' : 'unknown or unavailable'}. <button onclick={() => client?.refreshAudio()}>Refresh safety audio</button></p>{/if}
    {#if status?.handoff_pending}<p>OBS finalized the recording, but inbox registration is pending. Retry, or leave it for validated manual import. No file will be deleted or changed.</p><button disabled={view.working} onclick={() => act('production_abandon_handoff', { sessionId: status?.session_id })}>Leave handoff for manual import</button>{/if}
    {#if showTasks}
      <h2>Local recording</h2><p>Record and finish output in OBS, then import the finished file into Media Library. Scene switching and input mute below affect OBS directly.</p>
      {#if status?.managed_recording_available}<p>The Stream source and Content destination profiles are pinned at start. Profile changes apply to the next recording.</p>{/if}
      {#if !hasSession && status?.managed_recording_available}<label><input type="checkbox" bind:checked={armed} /> I have checked the scene, audio and recording folder in OBS.</label><button disabled={view.working || !armed || !status?.connected || status?.stream_active !== false || status?.recording_active !== false} onclick={() => act('production_start_recording')}>Start local recording</button>{/if}
      {#if !status?.managed_recording_available}<p>Managed recording is unavailable in this build. Start and finish recordings in OBS, then import the file into Media Library. Existing output is never adopted.</p>{/if}
      <h2>Scenes & sources</h2><p>Switch an existing program scene. Source editing and soundboard playback remain in Stream Extend.</p>
      <button disabled={view.inspecting} onclick={() => client?.inspect()}>Load scenes and audio inputs</button>
      <div class="scenes">{#each view.scenes as scene}<button disabled={view.working} aria-pressed={scene.is_current} onclick={() => client?.switchScene(scene)}>{scene.name}{scene.is_current ? ' · current' : ''}</button>{/each}</div>
    {/if}
    {#if view.error}<p class="error" role="alert">{view.error}</p>{/if}
    {#if view.notice}<p role="status">{view.notice}</p>{/if}
  </section>
{/if}

<style>
  .production { position: sticky; top: 0; z-index: 2; padding: 16px; margin-bottom: 20px; background: #fffefa; border: 1px solid #cbd2c7; border-radius: 12px; max-height: 75dvh; overflow-y: auto; }
  .safety, .audio, .scenes { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
  .safety { position: sticky; top: -16px; background: #fffefa; z-index: 1; padding-block: 4px; }
  .safety > div { flex: 1; min-width: min(100%, 200px); } span { display: block; font-size: 13px; overflow-wrap: anywhere; }
  button { background: #fffefa; color: #284837; border: 1px solid #cbd2c7; border-radius: 8px; padding: 10px 12px; font: inherit; cursor: pointer; overflow-wrap: anywhere; max-width: 100%; }
  button:disabled { opacity: .5; cursor: default; } button[aria-pressed='true'] { background: #2b5d44; color: white; }
  button.stop { background: #9d3434; color: white; border-color: #9d3434; }
  button:focus-visible, input:focus-visible { outline: 3px solid #c69045; outline-offset: 3px; }
  label { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; } .audio, .scenes { margin-top: 12px; }
  h2 { font-size: 19px; } p { font-size: 14px; line-height: 1.5; } .error { color: #9d3434; }
</style>
