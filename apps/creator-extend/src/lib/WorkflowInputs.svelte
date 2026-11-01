<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { onMount, onDestroy } from 'svelte';

  type Field = { node_id: string; input: string; label: string; kind: string; value: string | number };
  let { workflowPath, workflowName, connected, onQueued, onClose }: {
    workflowPath: string; workflowName: string; connected: boolean;
    onQueued: (path: string, promptId: string) => void; onClose: () => void;
  } = $props();
  let fields: Field[] = $state([]);
  let loading = $state(true);
  let busy = $state(false);
  let error = $state('');
  let destination = $state('');
  let uploadStatus = $state('');
  let disposed = false;
  onDestroy(() => { disposed = true; });
  onMount(() => { void load(); });

  async function load() {
    try {
      const [inputs, target] = await Promise.all([
        invoke<Field[]>('comfyui_workflow_inputs', { workflowPath }),
        invoke<string>('comfyui_upload_target'),
      ]);
      if (disposed) return;
      fields = inputs;
      destination = target;
    } catch (e: any) {
      error = e?.message ?? String(e);
    } finally {
      loading = false;
    }
  }

  function setValue(index: number, value: string) {
    fields = fields.map((field, i) => i === index ? { ...field, value } : field);
  }

  async function upload(index: number, file?: File) {
    if (!file) return;
    error = '';
    uploadStatus = '';
    if (file.size > 10 * 1024 * 1024 || file.size === 0) {
      error = 'Choose an image up to 10 MiB.';
      return;
    }
    busy = true;
    try {
      const bytes = Array.from(new Uint8Array(await file.arrayBuffer()));
      const reference = await invoke<string>('comfyui_upload_image', { bytes });
      if (disposed) return;
      setValue(index, reference);
      uploadStatus = `Uploaded ${file.name}. It will be used for ${fields[index].label}.`;
    } catch (e: any) {
      error = e?.message ?? String(e);
    } finally {
      busy = false;
    }
  }

  async function run() {
    error = '';
    busy = true;
    try {
      const edits = fields.map((field) => {
        let value: string | number = field.value;
        if (field.kind === 'seed') {
          const text = String(value);
          const number = Number(text);
          if (!/^\d+$/.test(text) || !Number.isSafeInteger(number) || number < 0) {
            throw new Error('Seeds must be whole numbers from 0 to 9007199254740991.');
          }
          value = number;
        }
        return { node_id: field.node_id, input: field.input, value };
      });
      const promptId = await invoke<string>('comfyui_queue_configured', { workflowPath, edits });
      if (!disposed) onQueued(workflowPath, promptId);
    } catch (e: any) {
      error = e?.message ?? String(e);
    } finally {
      busy = false;
    }
  }
</script>

<section class="input-editor" aria-label="Workflow inputs">
  <h3>Configure {workflowName}</h3>
  <p>Changes apply to this run. Your saved workflow stays unchanged.</p>
  {#if loading}
    <p role="status">Loading inputs…</p>
  {:else}
    {#if destination}
      <p class="destination">Images upload to your configured ComfyUI server at <strong>{destination}</strong> and remain there after closing this editor. Uploading does not start a job.</p>
    {/if}
    {#each fields as field, index}
      <div class="field">
        <label for={`workflow-input-${index}`}>{field.label}</label>
        {#if field.kind === 'text'}
          <textarea id={`workflow-input-${index}`} rows="3" value={field.value}
            disabled={busy} oninput={(event) => setValue(index, event.currentTarget.value)}></textarea>
        {:else if field.kind === 'seed'}
          <input id={`workflow-input-${index}`} type="text" inputmode="numeric" value={field.value}
            disabled={busy} oninput={(event) => setValue(index, event.currentTarget.value)} />
        {:else}
          <input id={`workflow-input-${index}`} type="text" value={field.value} disabled={busy}
            placeholder="Image already in ComfyUI's input folder"
            oninput={(event) => setValue(index, event.currentTarget.value)} />
          <label class="upload">Upload an image or mask (PNG, JPEG, WebP; up to 10 MiB)
            <input type="file" accept="image/png,image/jpeg,image/webp" disabled={busy || !connected || !destination}
              onchange={(event) => { const file = event.currentTarget.files?.[0]; event.currentTarget.value = ''; void upload(index, file); }} />
          </label>
        {/if}
      </div>
    {:else}
      {#if !error}<p>This workflow has no supported image, prompt or seed fields.</p>{/if}
    {/each}
  {/if}
  {#if uploadStatus}<p role="status">{uploadStatus}</p>{/if}
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  {#if !connected}<p>Connect ComfyUI before uploading an image or running this workflow.</p>{/if}
  <div class="actions">
    <button onclick={run} disabled={busy || loading || !connected || !destination}>{busy ? 'Working…' : 'Run with these inputs'}</button>
    <button onclick={onClose} disabled={busy}>Close</button>
  </div>
</section>

<style>
  .input-editor { margin-top: 1rem; padding: 1rem; border: 1px solid #8d70e8; border-radius: 10px; background: #202025; }
  h3 { margin: 0 0 .5rem; }
  p, .upload { font-size: .85rem; line-height: 1.5; color: #c4c4cf; }
  .destination { overflow-wrap: anywhere; }
  .field { display: grid; gap: .4rem; margin: 1rem 0; }
  label { font-size: .85rem; }
  textarea, input[type="text"] { box-sizing: border-box; width: 100%; color: #eee; background: #111; border: 1px solid #666; border-radius: 5px; padding: .6rem; font: inherit; }
  textarea { resize: vertical; }
  input[type="file"] { display: block; max-width: 100%; margin-top: .4rem; }
  .error { color: #ffaaaa; }
  .actions { display: flex; gap: .75rem; flex-wrap: wrap; }
  button { border: 1px solid #a68ae9; border-radius: 6px; padding: .6rem; background: #30204f; color: #eee; cursor: pointer; }
  button:disabled { opacity: .55; cursor: default; }
  :focus-visible { outline: 2px solid #c6adff; outline-offset: 3px; }
</style>
