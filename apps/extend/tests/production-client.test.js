import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { ProductionClient } from '../src/lib/production-client.js';

function deferred() {
  /** @type {(value:unknown)=>void} */ let resolve=()=>{};
  const promise=new Promise(r=>{resolve=r;});
  return {promise,resolve};
}
const idle={session_id:null,context_id:'idle',connected:true,stream_active:false,recording_active:false,owned:false,recovery_required:false,handoff_pending:false,source_profile_id:null,content_profile_id:null};
const receipt={session_id:'one',context_id:'one',confirmed:true,source_profile_id:'stream-main',content_profile_id:'content-main'};
/** @param {Record<string,(args?:Record<string,unknown>)=>unknown>} [overrides] */
function harness(overrides={}) {
  /** @type {string[]} */ const calls=[];
  /** @type {ProductionClient} */
  const client=new ProductionClient(async(command,args)=>{
    calls.push(command);
    if(overrides[command]) return overrides[command](args);
    if(command==='production_status') return {...idle};
    if(command==='production_start_recording') return {...receipt};
    if(command==='production_audio_inputs') return {context_id:client.context,session_id:client.view.status?.session_id ?? null,value:[{name:'Mic',muted:false}]};
    if(command==='production_scenes') return {context_id:client.context,session_id:client.view.status?.session_id ?? null,value:[]};
    if(command==='production_set_mute') return [{name:'Mic',muted:true}];
    return 'completed';
  },()=>{});
  client.setEnabled(true);
  return {client,calls};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));

test('R1-02 successful start retains generation and unknown output through failed status',async()=>{
  const {client}=harness({production_status:()=>Promise.reject(new Error('unavailable'))});
  await client.act('production_start_recording'); await flush();
  assert.equal(client.view.status?.session_id,'one'); assert.equal(client.view.status?.owned,true);
  assert.equal(client.view.status?.recording_active,null); assert.equal(client.view.unknown,true);
  assert.equal(client.view.inputs[0].name,'Mic');
});
test('R1-02 unknown Start receipt preserves recoverable identity without claiming ownership',async()=>{
  const {client}=harness({production_start_recording:()=>({...receipt,confirmed:false}),production_status:()=>Promise.reject(new Error('unavailable'))});
  await client.act('production_start_recording');
  assert.equal(client.view.status?.session_id,'one'); assert.equal(client.view.status?.owned,false);
  assert.equal(client.view.status?.recovery_required,true); assert.equal(client.view.unknown,true);
});
test('R1-02 old status completion cannot overwrite a newer reservation',async()=>{
  const old=deferred();const {client}=harness({production_status:()=>old.promise});
  const refresh=client.refresh();await client.act('production_start_recording');
  old.resolve({...idle});await refresh;
  assert.equal(client.view.status?.session_id,'one');
});
test('R1-02 status admitted during Start is discarded after its receipt',async()=>{
  const old=deferred(), start=deferred();const {client}=harness({production_start_recording:()=>start.promise,production_status:()=>old.promise});
  const mutation=client.act('production_start_recording');const refresh=client.refresh();
  start.resolve(receipt);await mutation;old.resolve(idle);await refresh;
  assert.equal(client.view.status?.session_id,'one');
});
test('R1-03 held inspection does not disable safety or queue its mutation',async()=>{
  const scenes=deferred(),audio=deferred();const {client,calls}=harness({production_scenes:()=>scenes.promise,production_audio_inputs:()=>audio.promise});
  client.view.status={...idle,session_id:'one',context_id:'one',owned:true};
  client.view.inputs=[{name:'Mic',muted:false,context_id:'one',session_id:'one'}];client.audioContext='one';
  const inspect=client.inspect();assert.equal(client.view.inspecting,true);assert.equal(client.view.working,false);
  await client.act('production_set_mute',{inputName:'Mic',muted:true,sessionId:'one',expectedContextId:'one'});
  assert.ok(calls.includes('production_set_mute'));assert.equal(client.view.working,false);
  scenes.resolve({context_id:'one',value:[]});audio.resolve({context_id:'one',value:[]});await inspect;
});
test('R1-04 fresh connection and fresh Start load safety audio without inspection',async()=>{
  const {client,calls}=harness();await client.refresh();await flush();
  assert.ok(calls.includes('production_audio_inputs'));assert.equal(client.view.inputs[0].name,'Mic');
  calls.length=0;await client.act('production_start_recording');await flush();
  assert.ok(calls.includes('production_audio_inputs'));assert.ok(!calls.includes('production_scenes'));
});
test('R1-03/04 one audio read in flight, stale completion ignored and one new-context refresh',async()=>{
  const pending=deferred(), fresh=deferred();let requests=0;
  const {client}=harness({production_audio_inputs:()=>{requests++;return requests===1?pending.promise:fresh.promise;},production_status:()=>Promise.reject(new Error('unavailable'))});
  client.view.status={...idle};void client.refreshAudio();
  await client.act('production_start_recording');void client.refreshAudio();void client.refreshAudio();
  assert.equal(requests,1);pending.resolve({context_id:'idle',value:[{name:'old',muted:false}]});await flush();
  assert.equal(requests,2);assert.deepEqual(client.view.inputs,[]);
  fresh.resolve({context_id:'one',value:[{name:'new',muted:false}]});await flush();
  assert.deepEqual(client.view.inputs,[{name:'new',muted:false,context_id:'one',session_id:null}]);
});
test('duplicate mutation is rejected while its own RPC is pending',async()=>{
  const pending=deferred();const {client,calls}=harness({production_start_recording:()=>pending.promise});
  const first=client.act('production_start_recording');const duplicate=client.act('production_start_recording');
  const dispatched=calls.filter(c=>c==='production_start_recording').length;
  pending.resolve(receipt);await Promise.all([first,duplicate]);
  assert.equal(dispatched,1);
});

test('R1-02 reload recovers the native pinned generation before preferences are available',async()=>{
  const {client,calls}=harness({production_status:()=>({...idle,...receipt,owned:true,recording_active:true})});
  client.setEnabled(false);await client.refresh();await flush();
  assert.equal(client.view.status?.session_id,'one');assert.equal(client.view.status?.owned,true);
  assert.ok(calls.includes('production_audio_inputs'));
});
test('R1-02 disabled idle observation never enables idle controls or audio',async()=>{
  const {client,calls}=harness();client.setEnabled(false);await client.refresh();await flush();
  assert.equal(client.view.status,null);assert.deepEqual(client.view.inputs,[]);
  assert.ok(!calls.includes('production_audio_inputs'));
});


test('R2-01 actions carry their actual audio and scene observation keys, never latest status',async()=>{
  for(const kind of ['audio','scene']) {
    /** @type {Record<string,unknown>[]} */ const calls=[];
    const {client}=harness({production_set_mute:a=>{calls.push(a ?? {});return [];},production_switch_scene:a=>{calls.push(a ?? {});return [];},production_scenes:()=>({context_id:'idle',session_id:null,value:[{name:'Main',is_current:true}]})});
    await client.refresh();await flush();await client.inspect();
    const input=client.view.inputs[0],scene=client.view.scenes[0];
    client.view.status={...idle,context_id:'new-status'};
    if(kind==='audio') await client.setMute(input);else await client.switchScene(scene);
    assert.equal(calls.length,1);assert.equal(calls[0].expectedContextId,'idle');assert.equal(calls[0].sessionId,null);
  }
});
test('R2-01 pending/failed settings save clears idle controls and never reuses A for same-named B',async()=>{
  let current='A',failed=false;
  /** @type {Record<string,unknown>[]} */ const args=[];let statusCalls=0;
  const {client}=harness({production_status:()=>{statusCalls++;if(failed)throw Error('offline');return {...idle,context_id:current};},production_audio_inputs:()=>({context_id:current,session_id:null,value:[{name:'Mic',muted:false}]}),production_set_mute:a=>{args.push(a ?? {});return [{name:'Mic',muted:true}];}});
  await client.refresh();await flush();const old=client.view.inputs[0];
  const before=statusCalls;client.beginConnectionChange();current='B';failed=true;
  await client.refresh();await client.setMute(old);
  assert.equal(statusCalls,before);assert.deepEqual(client.view.inputs,[]);assert.equal(args.length,0);
  client.endConnectionChange();await flush();assert.deepEqual(client.view.inputs,[]);
  await client.setMute(old);assert.equal(args.length,0);
  failed=false;await client.refresh();await flush();await client.setMute(old);assert.equal(args.length,0);
  await client.setMute(client.view.inputs[0]);assert.equal(args[0].expectedContextId,'B');
});
test('R2-01 held old audio/scenes cannot repopulate controls after rotation and failed status',async()=>{
  const audio=deferred(),scenes=deferred();let failed=false;
  const {client}=harness({production_status:()=>{if(failed)throw Error('offline');return {...idle};},production_audio_inputs:()=>audio.promise,production_scenes:()=>scenes.promise});
  await client.refresh();const inspection=client.inspect();
  failed=true;client.beginConnectionChange();client.endConnectionChange();
  audio.resolve({context_id:'idle',session_id:null,value:[{name:'old',muted:false}]});scenes.resolve({context_id:'idle',session_id:null,value:[{name:'old',is_current:true}]});await inspection;await flush();
  assert.deepEqual(client.view.inputs,[]);assert.deepEqual(client.view.scenes,[]);
});
test('R2-01 connection completion waits out an older status before learning the new context',async()=>{
  const old=deferred();let requests=0;
  const {client}=harness({production_status:()=>++requests===1?old.promise:{...idle,context_id:'B'}});
  const refresh=client.refresh();client.beginConnectionChange();client.endConnectionChange();old.resolve({...idle,context_id:'A'});await refresh;await flush();
  assert.equal(client.context,'B');assert.equal(client.view.inputs[0].context_id,'B');assert.equal(requests,2);
});
test('R2-01 credential/pack invalidation preserves pinned safety through corrupt preference status',async()=>{
  /** @type {Record<string,unknown>[]} */ const args=[];const {client}=harness({production_status:()=>Promise.reject(Error('corrupt prefs')),production_set_mute:a=>{args.push(a ?? {});return [{name:'Mic',muted:true}];}});
  client.view.status={...idle,...receipt,owned:true};await client.refreshAudio();
  const input=client.view.inputs[0];client.beginConnectionChange();client.endConnectionChange();
  assert.equal(client.view.inputs[0],input);await client.setMute(input);
  assert.equal(args[0].expectedContextId,'one');assert.equal(args[0].sessionId,'one');
});

test('R2-01 a rejected idle mutation clears its old observation and never retries after failed status',async()=>{
  let failed=false,mutations=0;
  const {client}=harness({production_status:()=>{if(failed)throw Error('offline');return {...idle};},production_set_mute:()=>{mutations++;throw Error('stale context');}});
  await client.refresh();await flush();const old=client.view.inputs[0];failed=true;
  await client.setMute(old);assert.deepEqual(client.view.inputs,[]);assert.equal(client.view.status,null);
  await client.setMute(old);assert.equal(mutations,1);
});
test('R2-01 malformed client context never dispatches even when names match',async()=>{
  const {client,calls}=harness();await client.refresh();await flush();calls.length=0;
  for(const expectedContextId of [undefined,null,'','other']) await client.act('production_set_mute',{inputName:'Mic',muted:true,sessionId:null,expectedContextId});
  assert.ok(!calls.includes('production_set_mute'));
});

test('R2-01 a save rejected before native context changes still replaces its invalidated held audio read',async()=>{
  const old=deferred();let reads=0;
  const {client}=harness({production_audio_inputs:()=>++reads===1?old.promise:{context_id:'idle',session_id:null,value:[{name:'fresh',muted:false}]}});
  await client.refresh();client.beginConnectionChange();client.endConnectionChange();await flush();
  old.resolve({context_id:'idle',session_id:null,value:[{name:'old',muted:false}]});await flush();
  assert.equal(reads,2);assert.equal(client.view.inputs[0].name,'fresh');
});

test('R2-01 unchanged disabled presentation cannot cancel native-pin bootstrap',async()=>{
  const pending=deferred();const {client}=harness({production_status:()=>pending.promise});
  client.setEnabled(false);const read=client.refresh();client.setEnabled(false);
  pending.resolve({...idle,...receipt,owned:true});await read;
  assert.equal(client.view.status?.session_id,'one');
});

// Execute the actual Svelte save body with a synthetic public-settings facade;
// browser checks separately prove the mounted component's lifecycle hooks.
async function savedPreferencesAfterLostResponse(readFails=false) {
  const page=readFileSync(new URL('../src/routes/+page.svelte',import.meta.url),'utf8');
  const body=page.split('  async function save(next: Preferences) {')[1].split('  async function visit')[0].replaceAll('invoke<Preferences>','invoke');
  const run=new (Object.getPrototypeOf(async()=>{}).constructor)('invoke',`let preferences={obs_host:'A',obs_port:4455,enabled_packs:['stream']};let busy=false,error='',notice='',ready=true;const hooks=[];const productionControls={beginConnectionChange:()=>hooks.push('begin'),endConnectionChange:()=>hooks.push('end')};async function save(next) {${body}return {result:await save({obs_host:'B',obs_port:4456,enabled_packs:['stream']}),preferences,ready,hooks};`);
  /** @type {string[]} */ const commands=[];
  const state=await run(async (/** @type {string} */ command)=>{commands.push(command);if(command==='preview_save_preferences')throw Error('lost response');if(readFails)throw Error('bad preferences');return {obs_host:'B',obs_port:4456,enabled_packs:['stream']};});
  return {...state,commands};
}
test('R2-01 ambiguous save reconciles native public preferences before later navigation can overwrite B',async()=>{
  const state=await savedPreferencesAfterLostResponse();
  assert.deepEqual(state.commands,['preview_save_preferences','preview_preferences']);assert.equal(state.result,false);assert.equal(state.preferences.obs_port,4456);assert.equal(state.ready,true);assert.deepEqual(state.hooks,['begin','end']);
});
test('R2-01 unreadable settings after ambiguous save block navigation but keep the safety component mounted',async()=>{
  const state=await savedPreferencesAfterLostResponse(true);assert.equal(state.ready,false);assert.deepEqual(state.hooks,['begin','end']);
});
