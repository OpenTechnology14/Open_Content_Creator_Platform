<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { open as openDialog } from '@tauri-apps/plugin-dialog';
  import ModuleSetup from '../../../shared/ui/ModuleSetup.svelte';
  import ProfileSwitcher from '../../../shared/ui/ProfileSwitcher.svelte';
  import RecordingLibrary from '../../../shared/ui/RecordingLibrary.svelte';
  import navigation from '../../../../configs/ui/combined-navigation.json';
  import defaults from '../../../../configs/ui/extend-preview-defaults.json';
  import { visibleGroups, navigationTarget, disclosureState, withPacks, homeActions } from '$lib/navigation.js';
  import FeatureSidebar from '$lib/FeatureSidebar.svelte';
  import ProductionControls from '$lib/ProductionControls.svelte';
  import type { NavigationGroup, NavigationItem } from '$lib/navigation.js';

  type Preferences = typeof defaults;
  type Readiness = { capabilities: { capability_id: string; label: string; status: string; summary: string }[] };
  type Workflow = { name: string; category: string; description?: string };
  let productionControls: { beginConnectionChange(): void; endConnectionChange(): void } | undefined;
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
  const sidebarGroups: NavigationGroup[] = navigation.sidebar_groups;
  const groups = $derived(visibleGroups(sidebarGroups, preferences.enabled_packs));
  const destinations: NavigationItem[] = [...sidebarGroups.flatMap(group => group.items), ...navigation.utilities, ...navigation.shortcuts];
  let activeId = $state('home');
  let expanded = $state<Record<string, boolean>>({});
  const storageKey = 'extend-preview:sidebar-groups:v1';
  const title = $derived(destinations.find(item => item.id === activeId)?.label ?? 'Home');
  const actionLabels: Record<string, string> = { settings: 'Check setup', stream: 'View stream readiness', library: 'Browse recordings' };
  const workflowLabels: Record<string, { label: string; purpose: string }> = navigation.workflow_labels;
  onMount(() => {
    let stored: string | null = null;
    try { stored = localStorage.getItem(storageKey); } catch { /* Private storage can be unavailable. */ }
    expanded = disclosureState(stored, navigation.sidebar_groups.map(group => group.id));
    const onHashChange = () => { if (ready) void followHash(); };
    window.addEventListener('hashchange', onHashChange);
    void load();
    return () => window.removeEventListener('hashchange', onHashChange);
  });

  function toggleGroup(id: string, open: boolean) {
    if (expanded[id] === open) return;
    expanded = { ...expanded, [id]: open };
    try { localStorage.setItem(storageKey, JSON.stringify(expanded)); } catch { /* Navigation remains usable. */ }
  }
  async function reveal(section: string) {
    await tick();
    const target = document.getElementById(section);
    if (!target) return;
    if (target instanceof HTMLDetailsElement) target.open = true;
    target.focus({ preventScroll: true });
    target.scrollIntoView({ block: 'start', behavior: 'instant' });
  }
  async function navigate(id: string) {
    if (!ready || busy) return;
    const target = navigationTarget(destinations, navigation.pages, id, preferences.enabled_packs);
    if (!target) return;
    if (target.page !== preferences.active_page && !await visit(target.page!)) return;
    activeId = target.id;
    const group = groups.find(group => group.items.some(item => item.id === id));
    if (group) toggleGroup(group.id, true);
    history.replaceState(null, '', `#${id}`);
    await reveal(target.section!);
  }
  async function followHash() {
    const id = window.location.hash.slice(1);
    if (navigationTarget(destinations, navigation.pages, id, preferences.enabled_packs)) await navigate(id);
    else {
      activeId = navigation.pages.find(page => page.id === preferences.active_page)?.feature ?? 'home';
      history.replaceState(null, '', `#${activeId}`);
    }
  }

  async function load() {
    try {
      preferences = await invoke<Preferences>('preview_preferences');
      draftHost = preferences.obs_host; draftPort = preferences.obs_port; draftComfyUrl = preferences.comfyui_url;
      if (!preferences.enabled_packs.includes('stream')) setupKind = 'creator';
      ready = true;
      readiness = await invoke<Readiness | null>('setup_last_readiness');
      if (preferences.active_page === 'create') workflows = await invoke<Workflow[]>('preview_workflows');
      await followHash();
    } catch (cause) { error = String(cause); }
  }
  async function save(next: Preferences) {
    busy = true; error = ''; notice = '';
    const connectionChange=next.obs_host!==preferences.obs_host || next.obs_port!==preferences.obs_port || JSON.stringify(next.enabled_packs)!==JSON.stringify(preferences.enabled_packs);
    if(connectionChange) productionControls?.beginConnectionChange();
    try { preferences = await invoke<Preferences>('preview_save_preferences', { preferences: next }); return true; }
    catch (cause) {
      error = String(cause);
      if(connectionChange) {
        // The write may have applied before its response failed. Reconcile
        // public settings so later navigation cannot overwrite B with stale A.
        try { preferences = await invoke<Preferences>('preview_preferences'); }
        catch { ready = false; } // Existing Retry reload; pinned safety stays mounted.
      }
      return false;
    }
    finally { if(connectionChange) productionControls?.endConnectionChange(); busy = false; }
  }
  async function visit(page: string) {
    if (await save({ ...preferences, active_page: page })) {
      if (page === 'create') {
        try { workflows = await invoke<Workflow[]>('preview_workflows'); }
        catch (cause) { error = String(cause); }
      }
      return true;
    }
    return false;
  }
  async function choose(packs: string[]) {
    if (await save(withPacks(preferences, packs))) {
      setupKind = packs.includes('stream') ? 'stream' : 'creator';
      readiness = null;
      activeId = 'home';
      toggleGroup('workspace', true);
      history.replaceState(null, '', '#home');
      notice = 'Workspace choice saved. Shared setup is installed once.';
      await reveal('workspace-overview');
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
    productionControls?.beginConnectionChange();
    try { await invoke('preview_set_obs_password', { password }); password = ''; notice = 'OBS password saved in the OS credential manager.'; }
    catch (cause) { error = String(cause); }
    finally { productionControls?.endConnectionChange(); busy = false; }
  }
</script>

<svelte:head><title>Extend Preview</title><meta name="description" content="Private Stream and Create workspace preview" /></svelte:head>
<div class:compact={preferences.layout === 'compact'} class="shell">
  <aside aria-label="Workspace navigation">
    <a class="brand" href="#home" onclick={(event) => { event.preventDefault(); void navigate('home'); }}>Extend <span>Preview</span></a>
    <FeatureSidebar {groups} utilities={navigation.utilities} shortcuts={navigation.shortcuts} {expanded} {activeId}
      enabled={ready && !busy} settingsActive={preferences.active_page === 'settings'} onNavigate={(id) => { void navigate(id); }} onToggle={toggleGroup} />
    <p class="private">Private preview<br />Local tools and recordings</p>
  </aside>
  <main>
    <header><p class="eyebrow">YOUR WORKSPACE</p><h1>{title}</h1></header>
    <ProductionControls bind:this={productionControls} id="production-controls" {invoke} enabled={ready && preferences.enabled_packs.includes('stream')} showTasks={preferences.active_page === 'stream'} />
    {#if error}<p class="error" role="alert">{error}</p>{/if}
    {#if notice}<p class="notice" role="status">{notice}</p>{/if}
    {#if !ready}<p role="status">Opening your local workspace…</p><button onclick={load}>Retry</button>
    {:else if preferences.active_page === 'home'}
      <section class="intro" id="workspace-overview" tabindex="-1"><h2>Stream and create, in one place.</h2><p>Choose the workspaces you need, then check setup. You can add the other workspace later.</p>
        <div class="choices" aria-label="Enabled workspaces">
          <button aria-pressed={preferences.enabled_packs.length === 1 && preferences.enabled_packs.includes('stream')} disabled={busy} onclick={() => choose(['stream'])}>Stream</button>
          <button aria-pressed={preferences.enabled_packs.length === 1 && preferences.enabled_packs.includes('content')} disabled={busy} onclick={() => choose(['content'])}>Create</button>
          <button aria-pressed={preferences.enabled_packs.length === 2} disabled={busy} onclick={() => choose(['stream', 'content'])}>Both</button>
        </div>
        <div class="actions">{#each homeActions(preferences.enabled_packs) as page, index}<button class:primary={index === 0} disabled={busy} onclick={() => navigate(page === 'settings' ? 'setup' : page === 'stream' ? 'live-recording' : 'media-library')}>{actionLabels[page]}</button>{/each}</div>
      </section>
      <p class="scope">This preview brings setup, profiles, readiness and the recording inbox together. Observe OBS, switch existing scenes and mute inputs in Production. Record and finish output in OBS, then import it into Media Library. Continue editing, live streaming and publishing in the existing Extend apps.</p>
    {:else if preferences.active_page === 'stream' || preferences.active_page === 'create'}
      {#key preferences.active_page}<ProfileSwitcher {invoke} kind={preferences.active_page === 'stream' ? 'stream' : 'content'} />{/key}
      <section class="task" id={preferences.active_page === 'stream' ? 'stream-readiness' : 'creative-readiness'} tabindex="-1"><h2>{preferences.active_page === 'stream' ? 'Your streaming setup' : 'Your creative workspace'}</h2>
        <p>{preferences.active_page === 'stream' ? 'Use the OBS controls above for scene switching and input mute. Record and finish output in OBS, then import it into Media Library. Live streaming stays in Stream Extend.' : 'Browse the bundled workflows and shared recording inbox. Run editing and export jobs in Creator Extend during this preview.'}</p>
        <button class="primary" disabled={busy} onclick={checkReadiness}>{busy ? 'Checking…' : 'Check readiness'}</button>
        {#if readiness}{#each readiness.capabilities.filter(item => item.capability_id === (preferences.active_page === 'stream' ? 'obs-control' : 'comfy-workflows')) as item}<p role="status"><strong>{item.label}: {item.status}</strong> · {item.summary}</p>{/each}{/if}
      </section>
      {#if preferences.active_page === 'create'}<section class="task" id="workflow-catalog" tabindex="-1"><h2>Images & thumbnails</h2><p>Select and run workflows in Creator Extend during this preview.</p><div class="catalog">{#each workflows as workflow}<article><strong>{workflowLabels[workflow.name]?.label ?? workflow.name}</strong><small>{workflow.category}</small><p>{workflowLabels[workflow.name]?.purpose ?? 'Bundled local workflow'}</p>{#if workflow.description}<details><summary>Technical notes</summary><p>{workflow.description}</p></details>{/if}</article>{/each}</div></section>{/if}
    {:else if preferences.active_page === 'library'}
      <section id="recording-library" tabindex="-1" aria-label="Media library"><RecordingLibrary {invoke} {openDialog} preview={true} /></section>
    {:else if preferences.active_page === 'settings'}
      <section class="task" id="profiles" tabindex="-1"><h2>Profiles & accounts</h2><p>Keep a separate profile for each workflow. Account connections remain in the existing apps during this preview.</p>
        {#if preferences.enabled_packs.includes('stream')}<ProfileSwitcher {invoke} kind="stream" />{/if}
        {#if preferences.enabled_packs.includes('content')}<ProfileSwitcher {invoke} kind="content" />{/if}
      </section>
      <section class="task" id="workspace-layout" tabindex="-1"><h2>Workspaces and layout</h2><div class="choices"><button disabled={busy} onclick={() => choose(['stream'])}>Stream only</button><button disabled={busy} onclick={() => choose(['content'])}>Create only</button><button disabled={busy} onclick={() => choose(['stream', 'content'])}>Both</button></div>
        <label>Navigation layout<select value={preferences.layout} onchange={(event) => save({ ...preferences, layout: event.currentTarget.value })}><option value="guided">Guided folders</option><option value="compact">Compact navigation</option></select></label>
      </section>
      <section class="task" id="guided-setup" tabindex="-1"><h2>Guided setup</h2>
        {#if preferences.enabled_packs.length === 2}<div class="choices"><button aria-pressed={setupKind === 'stream'} onclick={() => setupKind = 'stream'}>Stream tools</button><button aria-pressed={setupKind === 'creator'} onclick={() => setupKind = 'creator'}>Create tools</button></div>{/if}
        <div class="setup-content"><ModuleSetup {invoke} productKind={setupKind} preview={true} onReadiness={(value) => readiness = value} /></div>
      </section>
      <details class="task" id="connections" tabindex="-1"><summary>Advanced connections</summary><p>Preview connections are saved separately. Existing app settings and credentials are not imported.</p>
        {#if preferences.enabled_packs.includes('stream')}<label>OBS host<input bind:value={draftHost} /></label><label>OBS port<input type="number" min="1" max="65535" bind:value={draftPort} /></label><label>OBS password<input type="password" bind:value={password} autocomplete="off" /></label><button disabled={busy || !password} onclick={savePassword}>Save password</button>{/if}
        {#if preferences.enabled_packs.includes('content')}<label>ComfyUI address<input bind:value={draftComfyUrl} /></label>{/if}
        <button disabled={busy} onclick={async () => { if (await save({ ...preferences, obs_host: draftHost, obs_port: draftPort, comfyui_url: draftComfyUrl })) notice = 'Preview connections saved.'; }}>Save connections</button>
      </details>
      <details class="task" id="discover-tools" tabindex="-1"><summary>Discover tools</summary><p>These groups help you find the existing modules. A listed tool is not a claim that every feature is complete.</p>{#each navigation.groups as group}<details><summary>{group.label}</summary><ul>{#each group.modules as name}<li>{name}</li>{/each}</ul></details>{/each}</details>
      <details class="task" id="help" tabindex="-1"><summary>Help & diagnostics</summary><p>Start with Guided setup to check installed tools. Check readiness on the production or studio page before opening the existing app. Connections are saved separately for this preview.</p><p>Features marked Later are not available here yet. Collapsing navigation only changes what is displayed.</p></details>
    {/if}
  </main>
</div>

<style>
  :global(body) { margin: 0; background: #f6f5f1; color: #252b29; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  :global(*) { box-sizing: border-box; }
  .shell { min-height: 100vh; display: grid; grid-template-columns: 220px minmax(0,1fr); }
  aside { display: flex; flex-direction: column; gap: 20px; position: sticky; top: 0; height: 100dvh; overflow: hidden; padding: 30px 20px; background: #eeeee8; border-right: 1px solid #dedfd7; }
  .brand { color: #233e35; text-decoration: none; font-size: 24px; font-weight: 700; display: grid; }
  .brand span, .eyebrow { font-size: 11px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; }
  .private { margin-top: 0; font-size: 12px; color: #747b72; line-height: 1.7; }
  main { width: 100%; max-width: 1100px; padding: 45px 50px; min-width: 0; }
  h1 { margin: 7px 0 30px; font-size: 34px; letter-spacing: -.04em; } h2 { font-size: 22px; letter-spacing: -.025em; }
  p { line-height: 1.7; color: #586158; } .eyebrow { color: #687c6c; }
  .intro, .task { background: #fffefa; padding: 25px; border: 1px solid #dedfd7; border-radius: 14px; margin: 20px 0; }
  .intro { padding: 35px; } .choices, .actions { display: flex; gap: 10px; flex-wrap: wrap; margin: 22px 0; }
  .setup-content { background: #16151d; border-radius: 12px; padding: 20px; margin-top: 20px; }
  .setup-content :global(.module-grid) { grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr)); }
  .setup-content :global(.selected-modules) { grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }
  .setup-content :global(.capture-checks), .setup-content :global(.device-fields) { grid-template-columns: repeat(auto-fit, minmax(min(100%, 250px), 1fr)); }
  button { border: 1px solid #cbd2c7; border-radius: 8px; padding: 11px 15px; color: #284837; background: #fffefa; font: inherit; cursor: pointer; }
  button:hover { background: #e7eee5; } button:disabled { opacity: .5; cursor: default; } .primary, button[aria-pressed='true'] { background: #2b5d44; color: white; border-color: #2b5d44; }
  .primary:hover, button[aria-pressed='true']:hover { background: #204e37; color: white; }
  button:focus-visible, a:focus-visible, summary:focus-visible, input:focus-visible, select:focus-visible { outline: 3px solid #c69045; outline-offset: 3px; }
  label { display: grid; gap: 8px; max-width: 420px; margin: 15px 0; } input, select { background: white; border: 1px solid #cbd2c7; padding: 11px; border-radius: 7px; font: inherit; width: 100%; }
  .error { color: #9d3434; } .notice { color: #2b5d44; } .scope { max-width: 700px; font-size: 14px; }
  [tabindex="-1"] { scroll-margin-top: 24px; }
  summary { cursor: pointer; padding: 12px 0; font-weight: 600; } .catalog { display: grid; gap: 12px; } article { border-top: 1px solid #dedfd7; padding-top: 15px; } article small { display: block; color: #687c6c; }
  .compact { grid-template-columns: 150px minmax(0,1fr); } .compact aside { padding-inline: 15px; } .compact .brand { font-size: 20px; }
  @media (max-width: 760px) { .shell, .compact { grid-template-columns: 1fr; } aside { position: static; height: auto; overflow: visible; padding: 15px; border-right: 0; border-bottom: 1px solid #dedfd7; } .brand { font-size: 20px; display: inline-block; } .brand span { margin-left: 10px; } .private { display: none; } main { padding: 25px 18px; } .intro, .task { padding: 20px; } h1 { font-size: 29px; } }
</style>
