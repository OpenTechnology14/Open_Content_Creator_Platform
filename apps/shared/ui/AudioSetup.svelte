<script lang="ts">
  type AudioReport = {
    checked_at: number; platform: string; capability_status: string; scope: string;
    checks: { name: string; status: string; path: string | null; detail: string }[];
    guidance: string; reference: { path: string; contents: string }; acceptance: string[];
  };
  let { invoke, onGuide, disabled = false }: {
    invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
    onGuide: (module: string) => Promise<void>;
    disabled?: boolean;
  } = $props();
  let report: AudioReport | null = $state(null);
  let busy = $state(false);
  let error = $state('');
  async function scan() {
    busy = true; error = ''; report = null;
    try { report = await invoke<AudioReport>('plugin:module-setup|audio_setup_status'); }
    catch (value) { error = String(value); }
    finally { busy = false; }
  }
</script>

<section aria-label="Audio routing setup">
  <div class="heading">
    <div><h3>Audio routing</h3><p>Check routing tools and review the configuration for this computer.</p></div>
    <button disabled={busy || disabled} onclick={scan}>{busy ? 'Checking…' : 'Check audio routing tools'}</button>
  </div>
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if report}
    <p class="scope">Checked {new Date(report.checked_at * 1000).toLocaleString()} · Audio operation not verified</p>
    {#each report.checks as check}
      <p><strong>{check.name}: {check.status === 'found' ? 'Found' : 'Not found in standard locations'}</strong><br />{check.detail}</p>
      {#if check.path}<p class="path">{check.path}</p>{/if}
    {/each}
    <p>{report.guidance}</p>
    <details><summary>Bundled routing reference</summary><p class="path">{report.reference.path}</p><pre>{report.reference.contents}</pre></details>
    <h4>Verify off-air in OBS</h4>
    <ol>{#each report.acceptance as step}<li>{step}</li>{/each}</ol>
    <p class="scope">{report.scope}</p>
  {:else}
    <p>Routing tools are optional when OBS captures sources directly. A tool check cannot verify levels, mix-minus or hotkeys.</p>
  {/if}
  <div class="guides">
    <button disabled={disabled} onclick={() => onGuide('audio-production')}>Read audio setup guide</button>
    <button disabled={disabled} onclick={() => onGuide('soundboard')}>Read soundboard and hotkey guide</button>
  </div>
</section>

<style>
  section { margin-top: 1.2rem; padding: 1rem; border: 1px solid #354057; border-radius: 10px; }
  .heading { display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
  h3 { margin: 0 0 .4rem; } p, li { line-height: 1.5; } li { margin: .5rem 0; }
  button { background: #26334b; color: #e8edf5; border: 1px solid #52617b; border-radius: 6px; padding: .55rem .85rem; cursor: pointer; }
  button:disabled { opacity: .55; cursor: wait; } .guides { display: flex; gap: .6rem; flex-wrap: wrap; }
  .scope, .path { color: #aebbd1; font-size: .85rem; } .path { overflow-wrap: anywhere; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 22rem; overflow: auto; background: #101824; padding: .8rem; }
  .error { color: #ffb5b5; }
</style>
