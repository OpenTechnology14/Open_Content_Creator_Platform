<script lang="ts">
  import { onMount } from 'svelte';

  type Invoke = <T>(command: string, args?: Record<string, unknown>) => Promise<T>;
  type OpenDialog = (options: Record<string, unknown>) => Promise<string | string[] | null>;
  type Profile = { id: string; display_name: string; kind: string };
  type Selection = { profile_id: string };
  type Recording = {
    id: string; file_path: string; file_name: string; bytes: number; created_at_unix: number;
    source_profile_id: string | null; content_profile_id: string | null;
    origin: 'stream-session' | 'manual-import'; status: 'ready' | 'editing' | 'published' | 'archived';
    available: boolean;
  };
  let { invoke, openDialog, preview = false }: { invoke: Invoke; openDialog: OpenDialog; preview?: boolean } = $props();
  let recordings: Recording[] = $state([]);
  let profiles: Profile[] = $state([]);
  let activeContentProfile = $state('');
  let busy = $state(false);
  let showArchived = $state(false);
  let error = $state('');
  let message = $state('');
  let visible = $derived(recordings.filter((item) => showArchived || item.status !== 'archived'));
  const socialCommand = (name: string) => `plugin:social-manager|${name}`;

  onMount(() => {
    void load();
    const interval = setInterval(() => void refresh(), 4000);
    return () => clearInterval(interval);
  });

  async function load() {
    busy = true; error = '';
    try {
      const snapshot = await invoke<{ catalog: { profiles: Profile[] } }>(socialCommand('snapshot'));
      profiles = snapshot.catalog.profiles.filter((item) => item.kind === 'content' || item.kind === 'hybrid');
      const active = await invoke<Selection>(socialCommand('selection'), { kind: 'content' });
      activeContentProfile = active.profile_id;
      await refresh();
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function refresh() {
    try { recordings = await invoke<Recording[]>('recordings_list'); }
    catch (cause) { error = String(cause); }
  }

  async function importRecording() {
    error = ''; message = '';
    const selected = await openDialog({
      multiple: false,
      title: 'Add a recording to Creator Extend',
      filters: [{ name: 'Video recordings', extensions: ['mkv', 'mp4', 'mov', 'webm', 'm4v', 'avi', 'ts'] }],
    });
    if (!selected || Array.isArray(selected)) return;
    busy = true;
    try {
      const recording = await invoke<Recording>('recordings_import', {
        path: selected, contentProfileId: activeContentProfile || null,
      });
      message = `${recording.file_name} is ready in the recording inbox.`;
      await refresh();
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function updateRecording(
    recording: Recording,
    status = recording.status,
    contentProfileId: string | null = recording.content_profile_id,
  ) {
    error = ''; message = ''; busy = true;
    try {
      const updated = await invoke<Recording>('recordings_update', {
        id: recording.id, status, contentProfileId,
      });
      recordings = recordings.map((item) => item.id === updated.id ? updated : item);
      message = `${updated.file_name} updated.`;
    } catch (cause) { error = String(cause); }
    finally { busy = false; }
  }

  async function reveal(recording: Recording) {
    error = ''; message = '';
    try { await invoke('recordings_reveal', { id: recording.id }); }
    catch (cause) { error = String(cause); }
  }

  function size(bytes: number) {
    if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
    if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
</script>

<section class="library" aria-label="Recording inbox">
  <div class="heading">
    <div><p class="eyebrow">STREAM EXTEND → CREATOR EXTEND</p><h2>Recording inbox</h2></div>
    <span>{recordings.filter((item) => item.status !== 'archived').length} active</span>
  </div>
  <p>Managed Stream Extend sessions arrive here as soon as OBS finalizes the local file. The video stays in its original folder and is never uploaded automatically.</p>
  {#if preview}<p>Use Creator Extend to edit or publish a recording during this preview.</p>{/if}
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if message}<p class="success" role="status">{message}</p>{/if}
  <div class="toolbar">
    <button disabled={busy} onclick={importRecording}>{busy ? 'Working…' : 'Add existing recording'}</button>
    <button class="secondary" disabled={busy} onclick={refresh}>Refresh</button>
    <label><input type="checkbox" bind:checked={showArchived} /> Show archived</label>
  </div>
  {#if !busy && visible.length === 0}<p class="empty">No recordings yet. Start a managed live session in Stream Extend or add an existing local video.</p>{/if}
  <div class="records">
    {#each visible as recording (recording.id)}
      <article class:missing={!recording.available}>
        <div class="record-title">
          <div><strong>{recording.file_name}</strong><small>{size(recording.bytes)} · {new Date(recording.created_at_unix * 1000).toLocaleString()}</small></div>
          <span class={`status ${recording.status}`}>{recording.status}</span>
        </div>
        <div class="route">
          <span>From <strong>{recording.source_profile_id ?? (recording.origin === 'manual-import' ? 'Manual import' : 'Unknown stream profile')}</strong></span>
          <label>Content profile
            <select
              value={recording.content_profile_id ?? ''}
              disabled={busy}
              onchange={(event) => updateRecording(recording, recording.status, event.currentTarget.value || null)}
            >
              <option value="">Unassigned</option>
              {#each profiles as profile}<option value={profile.id}>{profile.display_name}</option>{/each}
            </select>
          </label>
        </div>
        {#if !recording.available}<p class="warning">The original file moved or was deleted. Locate it and add it again.</p>{/if}
        <div class="actions">
          {#if !preview}<button disabled={busy || !recording.available} onclick={() => updateRecording(recording, 'editing')}>Start editing</button>{/if}
          <button class="secondary" disabled={busy || !recording.available} onclick={() => reveal(recording)}>Show in folder</button>
          {#if recording.status !== 'ready'}<button class="secondary" disabled={busy} onclick={() => updateRecording(recording, 'ready')}>Mark ready</button>{/if}
          {#if !preview && recording.status !== 'published'}<button class="secondary" disabled={busy} onclick={() => updateRecording(recording, 'published')}>Mark published</button>{/if}
          {#if recording.status !== 'archived'}<button class="quiet" disabled={busy} onclick={() => updateRecording(recording, 'archived')}>Archive</button>{/if}
        </div>
      </article>
    {/each}
  </div>
</section>

<style>
  .library { max-width: 920px; background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem; }
  .heading, .record-title, .route, .toolbar, .actions { display: flex; align-items: center; gap: .8rem; }
  .heading, .record-title, .route { justify-content: space-between; }
  h2 { color: #ff6b35; margin: .15rem 0 0; } p { color: #aaa; }
  .eyebrow { color: #8ea2ff; font-size: .72rem; font-weight: 800; letter-spacing: .12em; margin: 0; }
  .heading > span, .status { padding: .3rem .7rem; border-radius: 1rem; background: #292932; color: #c7c7d1; font-size: .76rem; }
  .status.ready { background: #193a24; color: #71d28d; } .status.editing { background: #223452; color: #87b8ff; }
  .status.published { background: #3b2f14; color: #f1cb66; } .status.archived { color: #999; }
  .toolbar, .actions { flex-wrap: wrap; margin: 1rem 0; }
  .toolbar label { margin-left: auto; color: #bbb; font-size: .86rem; }
  .records { display: grid; gap: .9rem; }
  article { background: #141419; border: 1px solid #34343d; border-radius: 10px; padding: 1rem; }
  article.missing { border-color: #744949; }
  .record-title > div { display: grid; gap: .2rem; min-width: 0; }
  strong { overflow-wrap: anywhere; } small { color: #858593; }
  .route { margin: .9rem 0; align-items: end; color: #999; font-size: .84rem; }
  .route label { display: grid; gap: .3rem; min-width: 220px; }
  select { padding: .5rem; border: 1px solid #494955; border-radius: 7px; background: #15151b; color: #f1eef6; }
  button { padding: .55rem .9rem; border: 1px solid #ff6b35; border-radius: 8px; background: transparent; color: #ff9a74; cursor: pointer; }
  button:hover { background: #ff6b35; color: white; } button:disabled { opacity: .45; cursor: not-allowed; }
  button.secondary { border-color: #60606d; color: #c2c2cb; } button.quiet { border-color: transparent; color: #999; }
  .error, .warning { color: #ff8d8d; } .success { color: #a4d9b1; } .empty { padding: 1.2rem 0; }
  @media (max-width: 640px) { .route { align-items: stretch; flex-direction: column; } .route label { min-width: 0; } }
</style>
