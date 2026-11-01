<script lang="ts">
  import { onMount } from 'svelte';
  import ProductionControls from './ProductionControls.svelte';
  import PersonalityVoicePreview from './PersonalityVoicePreview.svelte';

  type Policy = {
    persona_id: string;
    game_id: string;
    mode: 'cohost' | 'autonomous';
    enabled: boolean;
    broadcast_start_authorized: boolean;
    gameplay_enabled: boolean;
  };
  type Status = {
    valid: boolean;
    max_concurrent_running: number;
    sessions: Record<string, Policy>;
  };
  type Rehearsal = {
    rehearsal: boolean;
    broadcast_started: boolean;
    driver_actions: string[];
    status: { lifecycle: string; last_error: string | null };
  };

  let { invoke }: { invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T> } = $props();
  let status: Status | null = $state(null);
  let result: Rehearsal | null = $state(null);
  let selected = $state('');
  let busy = $state(false);
  let error = $state('');

  onMount(() => { void load(); });

  async function load() {
    busy = true; error = '';
    try {
      status = await invoke<Status>('autopilot_status');
      selected = selected || Object.keys(status.sessions).find((id) => status?.sessions[id].enabled) || '';
    } catch (value) { error = String(value); }
    finally { busy = false; }
  }

  async function rehearse() {
    busy = true; error = ''; result = null;
    try { result = await invoke<Rehearsal>('autopilot_rehearse', { sessionId: selected }); }
    catch (value) { error = String(value); }
    finally { busy = false; }
  }

  let policy = $derived.by((): Policy | null => {
    const current = status as Status | null;
    return current && selected ? current.sessions[selected] ?? null : null;
  });
</script>

<section class="autopilot" aria-label="Automated streaming">
  <div class="heading">
    <div>
      <p class="eyebrow">Stream Autopilot</p>
      <h2>Automated streaming</h2>
      <p>Validate session policy and exercise pause, recovery and stop controls before connecting live services.</p>
    </div>
    <span class="stage">Lifecycle foundation</span>
  </div>

  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if !status}
    <div class="empty">
      <p>{busy ? 'Loading Autopilot policy…' : 'Autopilot policy is unavailable.'}</p>
      {#if !busy}<button onclick={load}>Retry</button>{/if}
    </div>
  {:else}
    <div class="grid">
      <article>
        <h3>Session</h3>
        <label>
          Show runtime
          <select bind:value={selected} disabled={busy}>
            {#each Object.entries(status.sessions) as [id, item]}
              <option value={id} disabled={!item.enabled}>{id} · {item.game_id}</option>
            {/each}
          </select>
        </label>
        {#if policy}
          <dl>
            <div><dt>Persona</dt><dd>{policy.persona_id}</dd></div>
            <div><dt>Mode</dt><dd>{policy.mode}</dd></div>
            <div><dt>Live start</dt><dd>{policy.broadcast_start_authorized ? 'Authorized' : 'Locked'}</dd></div>
            <div><dt>Game adapter</dt><dd>{policy.gameplay_enabled ? 'Enabled' : 'Disabled'}</dd></div>
          </dl>
        {/if}
      </article>

      <article>
        <h3>Safe lifecycle rehearsal</h3>
        <p>Runs preflight → preview → pause → resume → stop with local durable state.</p>
        <button class="primary" disabled={busy || !selected} onclick={rehearse}>
          {busy ? 'Running…' : 'Run lifecycle rehearsal'}
        </button>
        <p class="note">This rehearsal never starts OBS streaming, gameplay, a model, voice, avatar, or chat.</p>
      </article>
    </div>

    {#if result}
      <div class="result" role="status">
        <div><strong>Rehearsal complete</strong><span>{result.status.lifecycle}</span></div>
        <p>{result.driver_actions.join(' → ')}</p>
        <p>Broadcast started: {result.broadcast_started ? 'yes' : 'no'}</p>
      </div>
    {/if}

    <div class="next">
      <strong>Live integration still required</strong>
      <p>The production driver must bind the model, voice, avatar, OBS/Soundbox and an eligible game adapter before the Run control can be enabled.</p>
    </div>
  {/if}
</section>

<ProductionControls {invoke} />

<PersonalityVoicePreview {invoke} sessionPersona={policy?.persona_id || ''} />

<style>
  .autopilot { display: grid; gap: 1rem; }
  .heading { display: flex; justify-content: space-between; gap: 2rem; align-items: flex-start; }
  .heading h2 { margin: .1rem 0 .35rem; }
  .heading p { margin: 0; color: #aaa; max-width: 720px; }
  .eyebrow { color: #ff8b61 !important; font-size: .75rem; text-transform: uppercase; letter-spacing: .14em; font-weight: 700; }
  .stage { border: 1px solid #675538; color: #f7cc78; border-radius: 999px; padding: .35rem .7rem; white-space: nowrap; font-size: .78rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
  article, .result, .next, .empty { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.25rem; }
  article h3 { margin-top: 0; color: #f1eef6; }
  article p, .next p { color: #aaa; }
  label { display: grid; gap: .45rem; color: #c9c5d2; font-size: .85rem; }
  select { padding: .7rem; border: 1px solid #494955; border-radius: 7px; background: #111117; color: #f1eef6; }
  dl { margin: 1rem 0 0; display: grid; gap: .6rem; }
  dl div { display: flex; justify-content: space-between; gap: 1rem; border-bottom: 1px solid #2d2d34; padding-bottom: .45rem; }
  dt { color: #999; } dd { margin: 0; color: #f1eef6; }
  button { padding: .6rem 1rem; border: 1px solid #ff6b35; border-radius: 8px; background: transparent; color: #ff8b61; cursor: pointer; }
  button.primary { background: #ff6b35; color: white; }
  button:disabled { opacity: .5; cursor: default; }
  .note { font-size: .8rem; }
  .result { border-color: #315e43; background: #15231b; }
  .result div { display: flex; justify-content: space-between; }
  .result span { color: #99d5aa; text-transform: capitalize; }
  .result p { margin: .5rem 0 0; color: #b8c8bc; }
  .next { border-style: dashed; }
  .next p { margin-bottom: 0; }
  .error { color: #ff8c8c; }
  @media (max-width: 640px) { .heading { display: grid; } }
</style>
