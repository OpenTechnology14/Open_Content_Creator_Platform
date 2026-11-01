<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  type Phrase = { reaction: string; text: string };
  type Persona = { display_name: string; audio_policy: string; game_id: string; voice_id: string; catchphrases: Record<string, string[]> };
  type Revision = { id: string; persona_id: string; parent_revision_id: string | null; prompt: string; phrases: Phrase[]; voice: string | null; model: string; status: string; error: string; phrase_origin: string; assets: { file: string; duration_seconds: number }[]; feedback: { text: string; at: string }[] };
  type Snapshot = { personas: Record<string, Persona>; revisions: Record<string, Revision>; production: Record<string, { revision_id: string }>; library_path: string; busy_revision: string | null; model: string; revision_id?: string; manifest?: string; script: { state: string; cursor?: number; segments?: string[]; persona_id?: string; answer?: string; error?: string } };
  let { invoke, sessionPersona = '' }: { invoke: <T>(command: string, args?: Record<string, unknown>) => Promise<T>; sessionPersona?: string } = $props();
  let data: Snapshot | null = $state(null);
  let personaId = $state('');
  let revisionId = $state('');
  let prompt = $state('');
  let voice = $state('');
  let model = $state('');
  let phrases: Phrase[] = $state([]);
  let feedback = $state('');
  let error = $state('');
  let busy = $state(false);
  let reviewed = $state(false);
  let isolated = $state(false);
  let obsTested = $state(false);
  let bindings: Record<string, string> = $state({});
  let stopHotkey = $state('');
  let exportPath = $state('');
  let scriptText = $state('');
  let sources = $state('');
  let scriptReviewed = $state(false);
  let routeConfirmed = $state(false);
  let question = $state('');
  let answer = $state('');
  let answerReviewed = $state(false);
  let audio: HTMLAudioElement | null = null;
  let timer: ReturnType<typeof setInterval>;
  let polling = false;
  let audioUrl = '';
  let playing = $state(false);
  let disposed = false;
  let persona = $derived((data as Snapshot | null)?.personas[personaId]);
  let revision = $derived((data as Snapshot | null)?.revisions[revisionId]);
  let gaming = $derived(persona?.audio_policy === 'gaming-reactive');
  let dirty = $derived(!!revision && (prompt !== revision.prompt || voice !== (revision.voice || '') || model !== revision.model || JSON.stringify(phrases) !== JSON.stringify(revision.phrases)));
  let scriptMatches = $derived((data as Snapshot | null)?.script.persona_id === personaId);
  const api = <T,>(request: Record<string, unknown>) => invoke<T>('voice_studio_request', { request });

  function stopAudio() {
    audio?.pause(); audio = null; playing = false;
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    audioUrl = '';
  }
  function chooseRevision(id: string) {
    stopAudio(); revisionId = id; reviewed = false; obsTested = false; bindings = {};
    const item = data?.revisions[id];
    prompt = item?.prompt || ''; voice = item?.voice || ''; model = item?.model || data?.model || '';
    phrases = item ? item.phrases.map(p => ({ ...p })) : [];
  }
  function choosePersona() {
    chooseRevision(''); answer = ''; answerReviewed = false; scriptReviewed = false; routeConfirmed = false;
  }
  async function command(action: string, extra: Record<string, unknown> = {}) {
    busy = true; error = '';
    try {
      const next = await api<Snapshot>({ action, revision_id: revisionId, persona_id: personaId, ...extra });
      if (disposed) return;
      data = next;
      personaId ||= (next.personas[sessionPersona] ? sessionPersona : Object.keys(next.personas)[0]) || '';
      if (next.revision_id) chooseRevision(next.revision_id);
      if (next.manifest) exportPath = next.manifest;
    } catch (value) { error = String(value); }
    finally { busy = false; }
  }
  async function poll() {
    if (busy || polling || disposed) return;
    polling = true;
    try {
      if (playing) {
        const stream = await invoke<{ active: boolean }>('obs_stream_status');
        if (stream.active) { stopAudio(); error = 'Draft audition stopped: OBS is on air.'; }
      }
      const next = await api<Snapshot>({ action: 'status' });
      if (disposed) return;
      if (next.script.state === 'answer_review' && data?.script.state !== 'answer_review') {
        answer = next.script.answer || ''; answerReviewed = false;
      }
      const refreshRendered = revision?.status === 'generating' && next.revisions[revisionId]?.status !== 'generating';
      data = next;
      if (refreshRendered) chooseRevision(revisionId);
    } catch (value) { stopAudio(); error = String(value); }
    finally { polling = false; }
  }
  async function saveRevision() {
    await command(revision ? 'revise' : 'create', {
      prompt, voice: voice || null, model, phrases, feedback,
    });
  }
  async function audition(index: number) {
    stopAudio(); error = ''; busy = true;
    try {
      const result = await api<{ audio: string; mime: string }>({ action: 'audio', revision_id: revisionId, asset_index: index, monitor_confirmed: isolated });
      if (disposed) return;
      const bytes = Uint8Array.from(atob(result.audio), c => c.charCodeAt(0));
      audioUrl = URL.createObjectURL(new Blob([bytes], { type: result.mime }));
      audio = new Audio(audioUrl); audio.onended = stopAudio; audio.onerror = stopAudio;
      await audio.play(); playing = true;
    } catch (value) { stopAudio(); error = String(value); }
    finally { busy = false; }
  }
  onMount(() => { void command('status'); timer = setInterval(() => void poll(), 1500); });
  onDestroy(() => { disposed = true; clearInterval(timer); stopAudio(); void api({ action: 'script_stop' }).catch(() => {}); });
</script>

<section class="studio" aria-label="Personalities — Prompt and Voice Preview">
  <header><p class="eyebrow">Personalities</p><h2>Prompt & Voice Preview</h2><p>Generate, audition, review, and improve locally. Nothing is approved or put on air automatically.</p></header>
  {#if error}<p role="alert" class="error">{error}</p>{/if}
  {#if !data}
    <p>Install Automation / Control in Module setup to use the local studio.</p>
    <button disabled={busy} onclick={() => command('status')}>Load personalities</button>
  {:else}
    <label>Personality<select bind:value={personaId} onchange={choosePersona} disabled={busy}>
      {#each Object.entries(data.personas) as [id, p]}<option value={id}>{p.display_name} / {id} · {p.game_id} · {p.audio_policy}</option>{/each}
    </select></label>
    {#if sessionPersona}<p>Autopilot session personality: {sessionPersona}. Authoring another personality does not switch the on-air session.</p><button disabled={busy} onclick={() => { personaId = sessionPersona; choosePersona(); }}>Use session personality</button>{/if}
    <p class="policy">{persona?.game_id} · {persona?.voice_id} · {gaming ? 'Saved reactions → Soundboard; live voice only as configured fallback.' : 'Script + reviewed Q&A → AI-VOICE. Soundboard disabled.'}</p>
    {#if gaming}
      <div class="row">
        <label>Saved revision<select value={revisionId} onchange={(event) => chooseRevision(event.currentTarget.value)} disabled={busy}>
          <option value="">New draft</option>
          {#each Object.values(data.revisions).filter(r => r.persona_id === personaId).reverse() as r}<option value={r.id}>{r.id.slice(0, 8)} · {r.status}{data.production[personaId]?.revision_id === r.id ? ' · selected' : ''}</option>{/each}
        </select></label>
        <button disabled={busy} onclick={() => command('create', { model })}>Generate personality prompt</button>
      </div>
      <label>Local Ollama model (required for AI phrase generation)<input bind:value={model} disabled={revision?.status === 'generating'} placeholder="Installed model name" maxlength="120" /></label>
      <label>Installed OS voice (blank = configured/default)<input bind:value={voice} disabled={revision?.status === 'generating'} maxlength="120" /></label>
      {#if revision}
        <label>Reviewable authoring prompt<textarea bind:value={prompt} disabled={revision.status === 'generating'} rows="10" maxlength="16000"></textarea></label>
        <h3>Phrase candidates</h3>
        {#each phrases as phrase, index}
          <div class="row"><label>Reaction {index + 1}<select bind:value={phrase.reaction} disabled={revision.status === 'generating'}>{#each Object.keys(persona?.catchphrases || {}) as reaction}<option>{reaction}</option>{/each}</select></label><label>Spoken text<input bind:value={phrase.text} disabled={revision.status === 'generating'} maxlength="280" /></label></div>
        {/each}
        <label>Revision feedback / improvement request<textarea bind:value={feedback} rows="2" maxlength="2000"></textarea></label>
        <div class="actions">
          <button disabled={busy} onclick={saveRevision}>Save as new revision</button>
          <button disabled={busy || !feedback.trim()} onclick={() => command('feedback', { feedback })}>Record feedback</button>
          <button disabled={busy || dirty || revision.status !== 'draft' || !!data.busy_revision} onclick={() => command('preview', { generate: false })}>Render saved phrases</button>
          <button disabled={busy || dirty || revision.status !== 'draft' || !!data.busy_revision || !model.trim()} onclick={() => command('preview', { generate: true })}>Generate AI phrases + audio</button>
          {#if revision.status === 'generating'}<button onclick={() => command('cancel')}>Cancel preview</button>{/if}
        </div>
        {#if dirty}<p>Unsaved edits: save a new revision before rendering or approving.</p>{/if}
        <p role="status">Revision {revision.id.slice(0, 8)}: {revision.status} · {revision.phrase_origin}. {revision.error}</p>
        <label class="check"><input type="checkbox" bind:checked={isolated} />Audition output is isolated from the program mix. OBS must be connected and off air.</label>
        {#each revision.assets as asset, index}
          <div class="asset"><p>{revision.phrases[index]?.text}<br /><small>{asset.duration_seconds.toFixed(2)}s · {data.library_path}/{asset.file}</small></p><button disabled={busy || !isolated} onclick={() => audition(index)}>Audition {index + 1}</button></div>
        {/each}
        {#if playing}<button onclick={stopAudio}>Stop audition</button>{/if}
        <label class="check"><input type="checkbox" bind:checked={reviewed} />I reviewed this exact prompt, phrases, voice, and every audio sample.</label>
        <button disabled={busy || dirty || !reviewed || revision.status !== 'ready'} onclick={() => command('approve', { acceptance_confirmed: reviewed })}>Approve revision</button>
        <button disabled={busy || !['draft', 'ready', 'failed', 'canceled'].includes(revision.status)} onclick={() => command('reject')}>Reject revision (keep history)</button>
        {#if revision.status === 'approved'}
          <h3>Production selection · next worker/session start</h3>
          <p>Import the WAV paths above into OBS Soundbox. Test each clip and Stop All, then enter their exact registered hotkey names. This does not start a stream or update a running director.</p>
          {#each revision.assets as _, index}<label>Clip {index + 1} hotkey<input bind:value={bindings[String(index)]} maxlength="200" /></label>{/each}
          <label>Stop All hotkey<input bind:value={stopHotkey} maxlength="200" /></label>
          <label class="check"><input type="checkbox" bind:checked={obsTested} />I tested the clip-to-hotkey mapping, levels, and emergency stop in OBS.</label>
          <div class="actions"><button disabled={busy || dirty || !obsTested} onclick={() => command('activate', { bindings, stop_hotkey: stopHotkey, acceptance_confirmed: obsTested })}>Select approved revision</button><button disabled={busy} onclick={() => command('disable')}>Disable saved phrases</button><button disabled={busy} onclick={() => command('export')}>Export runtime manifest</button></div>
        {/if}
        {#if exportPath}<p>Manifest: {exportPath}</p>{/if}
        <details><summary>Revision history & feedback</summary><p>Parent: {revision.parent_revision_id || 'original'}. To roll back, select an earlier approved revision and re-confirm its OBS bindings.</p>{#each revision.feedback as item}<p>{item.at}: {item.text}</p>{/each}
          {#if revision.parent_revision_id && data.revisions[revision.parent_revision_id]}
            <h3>Previous prompt</h3><pre>{data.revisions[revision.parent_revision_id].prompt}</pre>
            {#each data.revisions[revision.parent_revision_id].phrases as phrase}<p>{phrase.reaction}: {phrase.text}</p>{/each}
          {/if}
        </details>
      {/if}
    {:else}
      <h3>Scripted show · operator-controlled playback</h3>
      <p>One paragraph per speech segment (maximum 500 characters). Pause finishes the current segment; Stop cancels immediately. Keep other host/speech workers stopped to avoid overlapping voices.</p>
      <label>Reviewed script<textarea bind:value={scriptText} rows="8"></textarea></label>
      <label>Episode brief / permitted source material<textarea bind:value={sources} rows="5" maxlength="20000"></textarea></label>
      <div class="row"><label>Local Ollama model for Q&A<input bind:value={model} maxlength="120" /></label><label>Installed voice (blank = persona default)<input bind:value={voice} maxlength="120" /></label></div>
      <label class="check"><input type="checkbox" bind:checked={scriptReviewed} />I approve the script and source material.</label>
      <button disabled={busy || !scriptReviewed} onclick={() => command('script_load', { segments: scriptText.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean), sources, voice: voice || null, model, acceptance_confirmed: scriptReviewed })}>Load approved script</button>
      <label class="check"><input type="checkbox" bind:checked={routeConfirmed} />OS speech output is routed to the intended AI-VOICE bus; no competing speech worker is running.</label>
      <p role="status">{data.script.state} · next segment {(data.script.cursor || 0) + 1}/{data.script.segments?.length || 0} · {data.script.error || ''}</p>
      <div class="actions"><button disabled={busy || !scriptMatches || !routeConfirmed} onclick={() => command('script_resume', { monitor_confirmed: routeConfirmed })}>Play / resume</button><button disabled={busy || !scriptMatches || data.script.state !== 'playing'} onclick={() => command('script_pause')}>Pause at next boundary</button><button disabled={busy} onclick={() => command('script_stop')}>Stop voice now</button></div>
      <label>One audience question per pause<input bind:value={question} maxlength="500" /></label>
      <button disabled={busy || !scriptMatches || !question.trim()} onclick={() => command('script_question', { question })}>Draft source-grounded answer</button>
      {#if scriptMatches && data.script.state === 'answer_review'}
        <label>Answer to review / edit<textarea bind:value={answer} rows="3" maxlength="500" oninput={() => answerReviewed = false}></textarea></label>
        <label class="check"><input type="checkbox" bind:checked={answerReviewed} />I checked this answer against the episode sources.</label>
        <button disabled={busy || !answerReviewed || !routeConfirmed} onclick={() => command('script_answer', { answer, acceptance_confirmed: answerReviewed, monitor_confirmed: routeConfirmed })}>Speak approved answer</button>
      {/if}
      <p>The script resumes only when you choose Play / resume. Unknown or failed answers defer to the episode brief; generated text never controls OBS or Soundboard.</p>
    {/if}
    <p class="note">Local library: {data.library_path}. AI authoring uses your installed Ollama model; audio uses the installed OS voice, not a cloned voice or an “Astra” speech model.</p>
  {/if}
</section>

<style>
  pre { white-space: pre-wrap; overflow-wrap: anywhere; }
  .studio { display: grid; gap: .85rem; border-top: 1px solid #494955; padding-top: 1.5rem; margin-top: 1rem; color: #eee; }
  h2, h3, p { margin: 0; } header p, .note, small { color: #aaa; } .eyebrow { color: #ff8b61; text-transform: uppercase; font-size: .75rem; letter-spacing: .12em; }
  label { display: grid; gap: .4rem; font-size: .85rem; } input, select, textarea { box-sizing: border-box; width: 100%; padding: .65rem; color: #eee; background: #15151a; border: 1px solid #494955; border-radius: 7px; font: inherit; } textarea { resize: vertical; }
  .check { display: flex; align-items: flex-start; } .check input { width: auto; }
  .row { display: flex; gap: 1rem; align-items: end; flex-wrap: wrap; } .row label { flex: 1; min-width: 200px; }
  .actions { display: flex; flex-wrap: wrap; gap: .6rem; } button { padding: .6rem 1rem; border: 1px solid #ff6b35; border-radius: 8px; background: transparent; color: #ff8b61; cursor: pointer; } button:disabled { opacity: .45; cursor: default; }
  .asset { padding: .8rem; border: 1px solid #333; border-radius: 8px; display: flex; justify-content: space-between; gap: 1rem; } .asset p, .note { overflow-wrap: anywhere; } .error { color: #ff8c8c; } .policy { padding: .8rem; background: #22232b; border-radius: 8px; } summary { cursor: pointer; } details p { margin-top: .5rem; }
</style>
