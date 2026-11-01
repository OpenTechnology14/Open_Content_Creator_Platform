<script lang="ts">
  import { onMount } from 'svelte';

  type Invoke = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  type Profile = { id: string; display_name: string; kind: string };
  type Selection = {
    kind: 'stream' | 'content'; profile_id: string; brand_id: string;
    provider_id: string; capability: string; connection_id: string | null;
  };
  let { invoke, kind }: { invoke: Invoke; kind: 'stream' | 'content' } = $props();
  let profiles: Profile[] = $state([]);
  let selection: Selection | null = $state(null);
  let busy = $state(true);
  let error = $state('');
  const command = (name: string) => `plugin:social-manager|${name}`;

  onMount(() => {
    const listener = (event: Event) => {
      const value = (event as CustomEvent<Selection>).detail;
      if (value?.kind === kind) selection = value;
    };
    window.addEventListener('hcp-profile-selection', listener);
    void load();
    return () => window.removeEventListener('hcp-profile-selection', listener);
  });

  async function load() {
    busy = true; error = '';
    try {
      const value = await invoke<{ catalog: { profiles: Profile[] } }>(command('snapshot'));
      profiles = value.catalog.profiles.filter((item) => item.kind === kind || item.kind === 'hybrid');
      selection = await invoke<Selection>(command('selection'), { kind });
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function activate(profile: string) {
    busy = true; error = '';
    try {
      selection = await invoke<Selection>(command('activate_profile'), { kind, profile });
      window.dispatchEvent(new CustomEvent('hcp-profile-selection', { detail: selection }));
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }
</script>

<div class="switcher" aria-label={`${kind} profile workspace`}>
  <span>Active profile</span>
  <select
    value={selection?.profile_id ?? ''}
    disabled={busy || profiles.length === 0}
    onchange={(event) => activate(event.currentTarget.value)}
    aria-label={`Active ${kind} profile`}
  >
    {#each profiles as profile}<option value={profile.id}>{profile.display_name}</option>{/each}
  </select>
  {#if selection}<small>{selection.provider_id} · {selection.connection_id ? 'account routed' : 'no account selected'}</small>{/if}
  {#if error}<small class="error">Profile unavailable</small>{/if}
</div>

<style>
  .switcher { display: grid; grid-template-columns: auto minmax(150px, 220px); gap: .22rem .55rem; align-items: center; }
  span { color: #999; font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
  select { min-width: 0; padding: .42rem .55rem; border: 1px solid #494955; border-radius: 7px; background: #17171d; color: #f1eef6; }
  small { grid-column: 2; color: #858593; font-size: .68rem; }
  .error { color: #ff8d8d; }
</style>
