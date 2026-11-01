<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { open as openDialog } from '@tauri-apps/plugin-dialog';
  import ModuleSetup from '../../../shared/ui/ModuleSetup.svelte';
  import ProfileSwitcher from '../../../shared/ui/ProfileSwitcher.svelte';
  import RecordingLibrary from '../../../shared/ui/RecordingLibrary.svelte';
  import navigation from '../../../../configs/ui/combined-navigation.json';
  import defaults from '../../../../configs/ui/extend-preview-defaults.json';
  import { visiblePages, withPacks, homeActions } from '$lib/navigation.js';

  type Preferences = typeof defaults;
  type Readiness = { capabilities: { capability_id: string; label: string; status: string; summary: string }[] };
  type Workflow = { name: string; category: string; description?: string };
  let preferences = $state<Preferences>({ ...defaults });
  let draftHost = $state(defaults.obs_host);
  let draftPort = $state(defaults.obs_port);
  let draftComfyUrl = $state(defaults.comfyui_url);
  let ready = $state(false);
  let busy = $state(false);
  let error = $state('');
  let notice = $state('');
  let password = $state('');
  let readiness = $state<Readiness | null>(null);
  let workflows = $state<Workflow[]>([]);
  let setupKind = $state<'stream' | 'creator'>('stream');
  const pages = $derived(visiblePages(navigation.pages, preferences.enabled_packs));
  const title = $derived(navigation.pages.find(page => page.id === preferences.active_page)?.label ?? 'Home');
  const actionLabels: Record<string, string> = { settings: 'Check setup', stream: 'View stream readiness', library: 'Browse recordings' };
  const taskLabels: Record<string, string> = { stream: 'Setup and readiness', create: 'Workflow catalog', library: 'Recordings', settings: 'Setup and tools' };
  const workflowLabels: Record<string, { label: string; purpose: string }> = navigation.workflow_labels;
  onMount(() => { void load(); });

  async function load() {
    try {
      preferences = await invoke<Preferences>('preview_preferences');
      draftHost = preferences.obs_host; draftPort = preferences.obs_port; draftComfyUrl = preferences.comfyui_url;
      if (!preferences.enabled_packs.includes('stream')) setupKind = 'creator';
      ready = true;
      readiness = await invoke<Readiness | null>('setup_last_readiness');
      if (preferences.active_page === 'create') workflows = await invoke<Workflow[]>('preview_workflows');
    } catch (cause) { error = String(cause); }
  }
  async function save(next: Preferences) {
    busy = true; error = ''; notice = '';
    try { preferences = await invoke<Preferences>('preview_save_preferences', { preferences: next }); return true; }
    catch (cause) { error = String(cause); return false; }
    finally { busy = false; }
  }
  async function visit(page: string) {
    if (await save({ ...preferences, active_page: page })) {
      if (page === 'create') {
        try { workflows = await invoke<Workflow[]>('preview_workflows'); }
        catch (cause) { error = String(cause); }
      }
    }
  }
  async function choose(packs: string[]) {
    if (await save(withPacks(preferences, packs))) {
      setupKind = packs.includes('stream') ? 'stream' : 'creator';
      readiness = null;
      notice = 'Workspace choice saved. Shared setup is installed once.';
    }
  }
  async function checkReadiness() {
    busy = true; error = '';
    try { readiness = await invoke<Readiness>('setup_refresh_readiness'); }
    catch (cause) { error = String(cause); }
    finally { busy = false; }
  }
  async function savePassword() {
    busy = true; error = '';
    try { await invoke('preview_set_obs_password', { password }); password = ''; notice = 'OBS password saved in the OS credential manager.'; }
    catch (cause) { error = String(cause); }
    finally { busy = false; }
  }
</script>

<svelte:head><title>Extend Preview</title><meta name="description" content="Private Stream and Create workspace preview" /></svelte:head>
<div class:compact={preferences.layout === 'compact'} class="shell">
  <aside aria-label="Workspace navigation">
    <a class="brand" href="#home" onclick={(event) => { event.preventDefault(); void visit('home'); }}>Extend <span>Preview</span></a>
    <nav>
      {#each pages as page}
        {#if page.id === 'home'}<button aria-current={preferences.active_page === page.id ? 'page' : undefined} disabled={!ready || busy} onclick={() => visit(page.id)}>{page.label}</button>
        {:else}<details class:current={preferences.active_page === page.id} open={preferences.active_page === page.id}><summary>{page.label}</summary><button aria-current={preferences.active_page === page.id ? 'page' : undefined} disabled={!ready || busy} onclick={() => visit(page.id)}>{taskLabels[page.id]}</button></details>{/if}
      {/each}
    </nav>
    <p class="private">Private preview<br />Local tools and recordings</p>
  </aside>
  <main>
    <header><p class="eyebrow">YOUR WORKSPACE</p><h1>{title}</h1></header>
    {#if error}<p class="error" role="alert">{error}</p>{/if}
    {#if notice}<p class="notice" role="status">{notice}</p>{/if}
    {#if !ready}<p role="status">Opening your local workspace…</p><button onclick={load}>Retry</button>
    {:else if preferences.active_page === 'home'}
      <section class="intro"><h2>Stream and create, in one place.</h2><p>Choose the workspaces you need, then check setup. You can add the other workspace later.</p>
        <div class="choices" aria-label="Enabled workspaces">
          <button aria-pressed={preferences.enabled_packs.length === 1 && preferences.enabled_packs.includes('stream')} disabled={busy} onclick={() => choose(['stream'])}>Stream</button>
          <button aria-pressed={preferences.enabled_packs.length === 1 && preferences.enabled_packs.includes('content')} disabled={busy} onclick={() => choose(['content'])}>Create</button>
          <button aria-pressed={preferences.enabled_packs.length === 2} disabled={busy} onclick={() => choose(['stream', 'content'])}>Both</button>
        </div>
        <div class="actions">{#each homeActions(preferences.enabled_packs) as page, index}<button class:primary={index === 0} disabled={busy} onclick={() => visit(page)}>{actionLabels[page]}</button>{/each}</div>
      </section>
      <p class="scope">This preview brings setup, profiles, readiness and the recording inbox together. Continue recording, editing and publishing in the existing Extend apps.</p>
    {:else if preferences.active_page === 'stream' || preferences.active_page === 'create'}
      <ProfileSwitcher {invoke} kind={preferences.active_page === 'stream' ? 'stream' : 'content'} />
      <section class="task"><h2>{preferences.active_page === 'stream' ? 'Your streaming setup' : 'Your creative workspace'}</h2>
        <p>{preferences.active_page === 'stream' ? 'Check OBS before continuing in Stream Extend. This preview will not start, stop or interrupt a broadcast.' : 'Browse the bundled workflows and shared recording inbox. Run editing and export jobs in Creator Extend during this preview.'}</p>
        <button class="primary" disabled={busy} onclick={checkReadiness}>{busy ? 'Checking…' : 'Check readiness'}</button>
        {#if readiness}{#each readiness.capabilities.filter(item => item.capability_id === (preferences.active_page === 'stream' ? 'obs-control' : 'comfy-workflows')) as item}<p role="status"><strong>{item.label}: {item.status}</strong> · {item.summary}</p>{/each}{/if}
      </section>
      {#if preferences.active_page === 'create'}<section class="task"><h2>Workflow catalog</h2><p>Select and run workflows in Creator Extend during this preview.</p><div class="catalog">{#each workflows as workflow}<article><strong>{workflowLabels[workflow.name]?.label ?? workflow.name}</strong><small>{workflow.category}</small><p>{workflowLabels[workflow.name]?.purpose ?? 'Bundled local workflow'}</p>{#if workflow.description}<details><summary>Technical notes</summary><p>{workflow.description}</p></details>{/if}</article>{/each}</div></section>{/if}
    {:else if preferences.active_page === 'library'}
      <RecordingLibrary {invoke} {openDialog} preview={true} />
    {:else if preferences.active_page === 'settings'}
      <section class="task"><h2>Workspaces and layout</h2><div class="choices"><button disabled={busy} onclick={() => choose(['stream'])}>Stream only</button><button disabled={busy} onclick={() => choose(['content'])}>Create only</button><button disabled={busy} onclick={() => choose(['stream', 'content'])}>Both</button></div>
        <label>Navigation layout<select value={preferences.layout} onchange={(event) => save({ ...preferences, layout: event.currentTarget.value })}><option value="guided">Guided folders</option><option value="compact">Compact navigation</option></select></label>
      </section>
      <section class="task"><h2>Guided setup</h2>
        {#if preferences.enabled_packs.length === 2}<div class="choices"><button aria-pressed={setupKind === 'stream'} onclick={() => setupKind = 'stream'}>Stream tools</button><button aria-pressed={setupKind === 'creator'} onclick={() => setupKind = 'creator'}>Create tools</button></div>{/if}
        <div class="setup-content"><ModuleSetup {invoke} productKind={setupKind} preview={true} onReadiness={(value) => readiness = value} /></div>
      </section>
      <details class="task"><summary>Connections</summary><p>Preview connections are saved separately. Existing app settings and credentials are not imported.</p>
        {#if preferences.enabled_packs.includes('stream')}<label>OBS host<input bind:value={draftHost} /></label><label>OBS port<input type="number" min="1" max="65535" bind:value={draftPort} /></label><label>OBS password<input type="password" bind:value={password} autocomplete="off" /></label><button disabled={busy || !password} onclick={savePassword}>Save password</button>{/if}
        {#if preferences.enabled_packs.includes('content')}<label>ComfyUI address<input bind:value={draftComfyUrl} /></label>{/if}
        <button disabled={busy} onclick={async () => { if (await save({ ...preferences, obs_host: draftHost, obs_port: draftPort, comfyui_url: draftComfyUrl })) notice = 'Preview connections saved.'; }}>Save connections</button>
      </details>
      <section class="task"><h2>Discover tools</h2><p>These groups help you find the existing modules. A listed tool is not a claim that every feature is complete.</p>{#each navigation.groups as group}<details><summary>{group.label}</summary><ul>{#each group.modules as name}<li>{name}</li>{/each}</ul></details>{/each}</section>
    {/if}
  </main>
</div>

<style>
  :global(body) { margin: 0; background: #f6f5f1; color: #252b29; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  :global(*) { box-sizing: border-box; }
  .shell { min-height: 100vh; display: grid; grid-template-columns: 220px minmax(0,1fr); }
  aside { padding: 30px 20px; background: #eeeee8; border-right: 1px solid #dedfd7; }
  .brand { color: #233e35; text-decoration: none; font-size: 24px; font-weight: 700; display: grid; }
  .brand span, .eyebrow { font-size: 11px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; }
  nav { display: grid; gap: 7px; margin-top: 35px; } nav button { text-align: left; width: 100%; background: transparent; border-color: transparent; }
  nav button[aria-current='page'] { background: #dde7df; color: #234a38; font-weight: 650; }
  nav details { border-radius: 8px; } nav details.current > summary { color: #234a38; font-weight: 700; } nav summary { padding: 11px 8px; font-weight: 500; } nav details button { font-size: 13px; padding-left: 15px; }
  .private { margin-top: 55px; font-size: 12px; color: #747b72; line-height: 1.7; }
  main { width: 100%; max-width: 1100px; padding: 45px 50px; min-width: 0; }
  h1 { margin: 7px 0 30px; font-size: 34px; letter-spacing: -.04em; } h2 { font-size: 22px; letter-spacing: -.025em; }
  p { line-height: 1.7; color: #586158; } .eyebrow { color: #687c6c; }
  .intro, .task { background: #fffefa; padding: 25px; border: 1px solid #dedfd7; border-radius: 14px; margin: 20px 0; }
  .intro { padding: 35px; } .choices, .actions { display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0; }
  .setup-content { background: #16151d; border-radius: 12px; padding: 20px; margin-top: 20px; }
  button { border: 1px solid #cbd2c7; border-radius: 8px; padding: 11px 15px; color: #284837; background: #fffefa; font: inherit; cursor: pointer; }
  button:hover { background: #e7eee5; } button:disabled { opacity: .5; cursor: default; } .primary, button[aria-pressed='true'] { background: #2b5d44; color: white; border-color: #2b5d44; }
  .primary:hover, button[aria-pressed='true']:hover { background: #204e37; color: white; }
  button:focus-visible, a:focus-visible, summary:focus-visible, input:focus-visible, select:focus-visible { outline: 3px solid #c69045; outline-offset: 3px; }
  label { display: grid; gap: 8px; max-width: 420px; margin: 15px 0; } input, select { background: white; border: 1px solid #cbd2c7; padding: 11px; border-radius: 7px; font: inherit; width: 100%; }
  .error { color: #9d3434; } .notice { color: #2b5d44; } .scope { max-width: 700px; font-size: 14px; }
  summary { cursor: pointer; padding: 12px 0; font-weight: 600; } .catalog { display: grid; gap: 12px; } article { border-top: 1px solid #dedfd7; padding-top: 15px; } article small { display: block; color: #687c6c; }
  .compact { grid-template-columns: 150px minmax(0,1fr); } .compact aside { padding-inline: 15px; } .compact .brand { font-size: 20px; }
  @media (max-width: 760px) { .shell, .compact { grid-template-columns: 1fr; } aside { padding: 15px; border-right: 0; border-bottom: 1px solid #dedfd7; } .brand { font-size: 20px; display: inline-block; } .brand span { margin-left: 10px; } nav { display: flex; flex-wrap: wrap; margin-top: 15px; } nav button { width: auto; } .private { display: none; } main { padding: 25px 18px; } .intro, .task { padding: 20px; } h1 { font-size: 29px; } }
</style>
