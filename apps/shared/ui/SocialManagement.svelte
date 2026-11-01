<script lang="ts">
  import { onMount } from 'svelte';

  type Invoke = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  type Brand = { id: string; display_name: string; logo_path: string };
  type Provider = { id: string; display_name: string; connection_status: 'available' | 'registration-required' | 'planned'; notes?: string[] };
  type Destination = { provider_id: string; capabilities: string[]; account_label: string };
  type Profile = { id: string; display_name: string; kind: string; brand_ids: string[]; default_brand_id: string; destinations: Destination[] };
  type Catalog = { brands: Brand[]; providers: Provider[]; profiles: Profile[] };
  type Connection = { id: string; profile_id: string; provider_id: string; account_name: string; verified_at: string };
  type ActiveSelection = {
    kind: 'stream' | 'content'; profile_id: string; brand_id: string;
    provider_id: string; capability: string; connection_id: string | null;
  };

  let { invoke, openExternal, preferredKind }: {
    invoke: Invoke; openExternal: (url: string) => Promise<void>; preferredKind: 'stream' | 'content';
  } = $props();
  let catalog: Catalog | null = $state(null);
  let logos: Record<string, string> = $state({});
  let profileId = $state('');
  let brandId = $state('');
  let providerId = $state('');
  let capability = $state('');
  let connectionId: string | null = $state(null);
  let serviceRunning = $state(false);
  let busy = $state(true);
  let error = $state('');
  let message = $state('');
  let connections: Connection[] = $state([]);
  const command = (name: string) => `plugin:social-manager|${name}`;
  let profile = $derived.by((): Profile | null => catalog ? catalog.profiles.find((item: Profile) => item.id === profileId) ?? null : null);
  let destination = $derived.by((): Destination | null => profile ? profile.destinations.find((item: Destination) => item.provider_id === providerId) ?? null : null);
  let provider = $derived.by((): Provider | null => catalog ? catalog.providers.find((item: Provider) => item.id === providerId) ?? null : null);
  let brand = $derived.by((): Brand | null => catalog ? catalog.brands.find((item: Brand) => item.id === brandId) ?? null : null);
  let compatibleProfiles = $derived.by((): Profile[] => catalog
    ? catalog.profiles.filter((item: Profile) => item.kind === preferredKind || item.kind === 'hybrid')
    : []);
  let connectable = $derived(serviceRunning && provider?.connection_status === 'available' && !!capability);
  let visibleConnections = $derived(connections.filter((item) => item.profile_id === profileId));
  let routeConnections = $derived(visibleConnections.filter((item) => item.provider_id === providerId));
  let selectedConnection = $derived(routeConnections.find((item) => item.id === connectionId) ?? null);

  onMount(() => { void load(); });

  function applySelection(value: ActiveSelection) {
    profileId = value.profile_id;
    brandId = value.brand_id;
    providerId = value.provider_id;
    capability = value.capability;
    connectionId = value.connection_id;
  }

  async function chooseProfile(id: string) {
    busy = true; error = ''; message = '';
    try {
      const value = await invoke<ActiveSelection>(command('activate_profile'), {
        kind: preferredKind, profile: id,
      });
      applySelection(value);
      message = `${catalog?.profiles.find((item) => item.id === id)?.display_name ?? id} is now active.`;
      window.dispatchEvent(new CustomEvent('hcp-profile-selection', { detail: value }));
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function chooseBrand(id: string) {
    brandId = id;
    await persistSelection();
  }

  async function chooseProvider(id: string) {
    providerId = id;
    const selected = profile?.destinations.find((item: Destination) => item.provider_id === id);
    capability = selected?.capabilities.find((item: string) => item !== 'account-read') ?? '';
    connectionId = connections.find((item) => item.profile_id === profileId && item.provider_id === id)?.id ?? null;
    await persistSelection();
  }

  async function chooseCapability(value: string) {
    capability = value;
    await persistSelection();
  }

  async function chooseConnection(value: string) {
    connectionId = value || null;
    await persistSelection();
  }

  async function persistSelection() {
    if (!profileId || !brandId || !providerId || !capability) return;
    try {
      const value = await invoke<ActiveSelection>(command('save_selection'), { selection: {
        kind: preferredKind,
        profile_id: profileId,
        brand_id: brandId,
        provider_id: providerId,
        capability,
        connection_id: connectionId,
      }});
      applySelection(value);
      window.dispatchEvent(new CustomEvent('hcp-profile-selection', { detail: value }));
      message = 'Profile route saved for fast switching.';
    } catch (cause) { error = String(cause); }
  }

  async function load() {
    busy = true; error = ''; message = '';
    try {
      const value = await invoke<{ catalog: Catalog; logos: Record<string, string> }>(command('snapshot'));
      catalog = value.catalog;
      logos = value.logos;
      const saved = await invoke<ActiveSelection>(command('selection'), { kind: preferredKind });
      applySelection(saved);
      const service = await invoke<{ running: boolean; url: string }>(command('start'));
      serviceRunning = service.running;
      if (serviceRunning) await refreshConnections();
    } catch (cause) {
      error = String(cause);
    } finally { busy = false; }
  }

  async function refreshConnections() {
    try {
      const value = await invoke<{ connections: Connection[] }>(command('connections'));
      connections = value.connections;
      if (connectionId && !connections.some((item) => item.id === connectionId && item.profile_id === profileId && item.provider_id === providerId)) {
        connectionId = null;
        await persistSelection();
      }
    } catch (cause) { error = String(cause); }
  }

  async function connect() {
    busy = true; error = ''; message = '';
    try {
      const authorizationUrl = await invoke<string>(command('authorize'), {
        profile: profileId, provider: providerId, capability,
      });
      await openExternal(authorizationUrl);
      message = 'Finish consent in your browser, then return here and refresh connected accounts.';
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function disconnectAccount() {
    if (!selectedConnection) return;
    if (!window.confirm(`Disconnect ${selectedConnection.account_name} from ${profile?.display_name}?`)) return;
    busy = true; error = ''; message = '';
    try {
      await invoke(command('disconnect'), { connection: selectedConnection.id });
      const name = selectedConnection.account_name;
      connectionId = null;
      await persistSelection();
      await refreshConnections();
      message = `${name} was disconnected and its saved credential was removed.`;
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }
</script>

<section class="social" aria-label="Social management">
  <div class="heading">
    <div><p class="eyebrow">SHARED PROFILE DIRECTORY</p><h2>Social Management</h2></div>
    <span class:connected={serviceRunning}>{serviceRunning ? 'Local service ready' : 'Setup required'}</span>
  </div>
  <p>Choose the show identity, logo, destination, and permission. Both apps use the same local profiles and connected accounts.</p>
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if message}<p class="success" role="status">{message}</p>{/if}
  {#if busy && !catalog}<p role="status">Loading Social Management…</p>{/if}
  {#if catalog && profile}
    <div class="quick-profiles" aria-label="Quick profile switching">
      {#each compatibleProfiles as item}
        <button class:active={item.id === profileId} disabled={busy} onclick={() => chooseProfile(item.id)}>{item.display_name}</button>
      {/each}
    </div>
    <div class="picker">
      <label>Profile
        <select value={profileId} onchange={(event) => chooseProfile(event.currentTarget.value)}>
          {#each compatibleProfiles as item}<option value={item.id}>{item.display_name} · {item.kind}</option>{/each}
        </select>
      </label>
      <label>Brand and logo
        <span class="brand-row">
          {#if brand}<img src={logos[brand.logo_path]} alt={`${brand.display_name} logo`} />{/if}
          <select value={brandId} onchange={(event) => chooseBrand(event.currentTarget.value)}>
            {#each catalog.brands.filter((item) => profile?.brand_ids.includes(item.id)) as item}<option value={item.id}>{item.display_name}</option>{/each}
          </select>
        </span>
      </label>
      <label>Destination
        <select value={providerId} onchange={(event) => chooseProvider(event.currentTarget.value)}>
          {#each profile.destinations as item}
            {@const platform = catalog.providers.find((candidate) => candidate.id === item.provider_id)}
            <option value={item.provider_id}>{platform?.display_name} · {platform?.connection_status}</option>
          {/each}
        </select>
      </label>
      <label>Connection purpose
        <select value={capability} onchange={(event) => chooseCapability(event.currentTarget.value)}>
          {#each destination?.capabilities.filter((item: string) => item !== 'account-read') ?? [] as item}<option value={item}>{item}</option>{/each}
        </select>
      </label>
      <label>Active connected account
        <select value={connectionId ?? ''} onchange={(event) => chooseConnection(event.currentTarget.value)}>
          <option value="">No account selected</option>
          {#each routeConnections as item}<option value={item.id}>{item.account_name}</option>{/each}
        </select>
      </label>
    </div>
    {#if provider}
      <div class="provider-card">
        <div>
          <strong>{provider.display_name}</strong>
          <small>{selectedConnection ? `Posting route: ${selectedConnection.account_name}` : destination?.account_label}</small>
        </div>
        <span class:available={provider.connection_status === 'available'}>{provider.connection_status}</span>
      </div>
      {#if provider.id === 'discord'}
        <p class="hint">Discord connects an announcement channel for approved posts. Discord Go Live still uses screen sharing in the Discord desktop client.</p>
      {:else if provider.connection_status !== 'available'}
        <p class="hint">This destination is tracked in the catalog. Connection stays disabled until its account and publishing or ingest adapter is implemented and verified.</p>
      {/if}
    {/if}
    <div class="actions">
      <button disabled={!connectable || busy} onclick={connect}>{busy ? 'Working…' : `${selectedConnection ? 'Reconnect' : 'Connect'} ${provider?.display_name ?? 'account'}`}</button>
      <button class="secondary" disabled={!serviceRunning || busy} onclick={refreshConnections}>Refresh connected accounts</button>
      {#if selectedConnection}<button class="danger" disabled={busy} onclick={disconnectAccount}>Disconnect {selectedConnection.account_name}</button>{/if}
    </div>
    <div class="accounts">
      <h3>Connected accounts <small>{visibleConnections.length}</small></h3>
      {#if visibleConnections.length === 0}<p class="empty">No accounts are connected to this profile on this device.</p>{/if}
      {#each visibleConnections as item (item.id)}
        <article><strong>{catalog.providers.find((candidate) => candidate.id === item.provider_id)?.display_name}</strong><span>{item.account_name}</span><small>{item.id}</small></article>
      {/each}
    </div>
  {/if}
</section>

<style>
  .social { max-width: 880px; background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem; }
  .heading { display: flex; justify-content: space-between; gap: 1rem; align-items: start; }
  h2 { color: #ff6b35; margin: .15rem 0 0; } h3 { margin-bottom: .5rem; } p { color: #aaa; }
  .eyebrow { color: #8ea2ff; font-size: .72rem; font-weight: 800; letter-spacing: .12em; margin: 0; }
  .heading > span, .provider-card > span { padding: .3rem .75rem; border-radius: 1rem; background: #302626; color: #e89b9b; font-size: .78rem; }
  .heading > span.connected, .provider-card > span.available { background: #193a24; color: #71d28d; }
  .picker { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin: 1.25rem 0; }
  .quick-profiles { display: flex; gap: .55rem; flex-wrap: wrap; margin-top: 1rem; }
  .quick-profiles button { border-color: #555568; color: #c8c8d2; }
  .quick-profiles button.active { border-color: #ff6b35; background: #ff6b35; color: white; }
  label { display: grid; gap: .45rem; color: #ccc; font-size: .88rem; }
  select { min-width: 0; width: 100%; padding: .68rem; border: 1px solid #494955; border-radius: 7px; background: #15151b; color: #f1eef6; font: inherit; }
  .brand-row { display: grid; grid-template-columns: 54px 1fr; gap: .7rem; align-items: center; }
  img { width: 46px; height: 46px; object-fit: contain; background: white; border-radius: 10px; padding: 4px; }
  .provider-card { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .85rem 1rem; background: #141419; border: 1px solid #34343d; border-radius: 9px; }
  .provider-card div, article { display: grid; gap: .2rem; } small { color: #858593; }
  .actions { display: flex; gap: .7rem; flex-wrap: wrap; margin: 1rem 0; }
  button { padding: .6rem 1rem; border: 1px solid #ff6b35; border-radius: 8px; background: transparent; color: #ff9a74; cursor: pointer; }
  button:hover { background: #ff6b35; color: white; } button:disabled { opacity: .45; cursor: not-allowed; }
  button.secondary { border-color: #6b6b77; color: #b8b8c2; }
  button.danger { border-color: #a34f4f; color: #f0a0a0; }
  .accounts { border-top: 1px solid #333; margin-top: 1.25rem; padding-top: .5rem; }
  article { padding: .7rem 0; border-bottom: 1px solid #292930; grid-template-columns: 120px 1fr; }
  article small { grid-column: 2; overflow-wrap: anywhere; }
  .error { color: #ff8d8d; } .success { color: #a4d9b1; } .hint, .empty { font-size: .88rem; }
</style>
