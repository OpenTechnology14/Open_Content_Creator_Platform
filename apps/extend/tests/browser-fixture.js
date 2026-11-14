import { mockIPC } from '@tauri-apps/api/mocks';
import defaults from '../../../configs/ui/extend-preview-defaults.json';
import * as fixtureChecks from './browser-production-check.js';

if (typeof window !== 'undefined') {
  let preferences = JSON.parse(sessionStorage.getItem('extend-fixture-preferences') ?? JSON.stringify(defaults));
  /** @type {{session_id:string|null, context_id:string, managed_recording_available:boolean, connected:boolean, stream_active:boolean, recording_active:boolean, owned:boolean, recovery_required:boolean, handoff_pending:boolean, source_profile_id:string|null, content_profile_id:string|null}} */
  let production = { session_id: null, context_id: 'idle', managed_recording_available: true, connected: true, stream_active: false, recording_active: false, owned: false, recovery_required: false, handoff_pending: false, source_profile_id: null, content_profile_id: null };
  production = JSON.parse(sessionStorage.getItem('extend-fixture-native-pin') ?? JSON.stringify(production));
  let revision=0;
  let muted = false;
  let scene = 'Main Scene';
  /** @type {{command:string,args:Record<string,unknown>}[]} */
  const callLog = [];
  const control = { failStatus: false, failStatusAfterStart: false, failStatusAfterSave: false, failSaveAfterApply: false, holdSave: false, releaseSave: () => {}, holdAudio: false, holdScenes: false, unconfirmedStart: false, failHandoff: false, endOutput: () => { production.recording_active = false; production.stream_active = false; }, releaseScenes: () => {}, releaseAudio: () => {} };
  Object.assign(window, { fixtureCallLog: callLog, fixtureChecks, fixtureControl: control });
  mockIPC((command, args = {}) => {
    const values = /** @type {Record<string, unknown>} */ (args);
    callLog.push({ command, args: command==='preview_set_obs_password'?{provided:true}:values });
    switch (command) {
      case 'production_status': if (control.failStatus) return Promise.reject(new Error('synthetic observation failure')); return { ...production };
      case 'production_start_recording':
        production = { ...production, session_id: 'synthetic-session', context_id: 'synthetic-session', recording_active: true, owned: true, source_profile_id: 'test-stream', content_profile_id: 'test-content' };
        if (control.failStatusAfterStart) control.failStatus = true;
        if (control.unconfirmedStart) production = { ...production, owned: false, recovery_required: true };
        return { ...production, confirmed: !control.unconfirmedStart };
      case 'production_stop_recording':
        if (control.failHandoff) { production = { ...production, owned: false, recording_active: false, handoff_pending: true }; return Promise.reject(new Error('synthetic absent finalized file')); }
        production = { ...production, session_id: null, context_id: 'idle-after', recording_active: false, owned: false };
        return 'Synthetic recording handed off';
      case 'production_scenes': {
        const result={context_id:production.context_id,session_id:production.session_id,value:[{name:scene,is_current:true},{name:'Starting Soon',is_current:false}]};
        if(control.holdScenes) return new Promise(resolve=>{control.releaseScenes=()=>resolve(result);});
        return result;
      }
      case 'production_abandon_handoff':
        if (!production.handoff_pending || production.recording_active || production.stream_active) return Promise.reject(new Error('not safely finalized'));
        production = { ...production, session_id: null, context_id: 'abandoned', owned: false, handoff_pending: false, recovery_required: false };
        return 'Inbox handoff abandoned. No file was registered, deleted or changed. Import manually with the original profiles.';
      case 'production_recover':
        if (production.recording_active || production.stream_active) return Promise.reject(new Error('outputs still active'));
        production = { ...production, session_id: null, context_id: 'recovered', recording_active: false, owned: false, recovery_required: false }; return null;
      case 'production_switch_scene':
        if(typeof values.expectedContextId!=='string' || values.expectedContextId!==production.context_id || values.sessionId!==production.session_id) return Promise.reject(new Error('stale observation'));
        scene = String(values.sceneName); return [{ name: scene, is_current: true }];
      case 'production_audio_inputs': {
        const result={context_id:production.context_id,session_id:production.session_id,value:[{name:'Synthetic Mic',muted}]};
        if(control.holdAudio) return new Promise(resolve=>{control.releaseAudio=()=>resolve(result);});
        return result;
      }
      case 'production_set_mute':
        if(typeof values.expectedContextId!=='string' || values.expectedContextId!==production.context_id || values.sessionId!==production.session_id) return Promise.reject(new Error('stale observation'));
        muted = Boolean(values.muted); return [{ name: 'Synthetic Mic', muted }];
      case 'preview_preferences': if(sessionStorage.getItem('extend-fixture-corrupt-preferences')==='true') return Promise.reject(new Error('Synthetic invalid preferences')); return preferences;
      case 'preview_save_preferences': {
        const next=/** @type {typeof defaults} */(values.preferences);
        const changed=preferences.obs_host!==next.obs_host || preferences.obs_port!==next.obs_port || JSON.stringify(preferences.enabled_packs)!==JSON.stringify(next.enabled_packs);
        const apply=()=>{
          if(production.session_id && (preferences.obs_host!==next.obs_host || preferences.obs_port!==next.obs_port || !next.enabled_packs.includes('stream'))) throw Error('pinned connection');
          if(changed && !production.session_id) production={...production,context_id:`fixture-${++revision}:idle`};
          preferences=next;sessionStorage.setItem('extend-fixture-preferences',JSON.stringify(preferences));
          if(control.failStatusAfterSave) control.failStatus=true;
          if(control.failSaveAfterApply) throw Error('synthetic lost save response');
          return preferences;
        };
        if(control.holdSave) return new Promise((resolve,reject)=>{control.releaseSave=()=>{try{resolve(apply());}catch(e){reject(e);}};});
        return apply();
      }
      case 'preview_set_obs_password':
        if(production.session_id) return Promise.reject(new Error('pinned connection'));
        production={...production,context_id:`fixture-${++revision}:idle`};
        if(control.failStatusAfterSave) control.failStatus=true;
        if(control.failSaveAfterApply) return Promise.reject(new Error('synthetic lost credential response'));
        return null;
      case 'setup_last_readiness': return null;
      case 'preview_workflows': return [{ name: 'inpaint-fill-v1', category: 'Synthetic catalog', description: 'Test-only workflow description.' }];
      case 'plugin:social-manager|snapshot': return { catalog: { profiles: [
        { id: 'test-stream', display_name: 'Synthetic Stream', kind: 'stream' },
        { id: 'test-content', display_name: 'Synthetic Content', kind: 'content' },
      ] } };
      case 'plugin:social-manager|selection': return { kind: values.kind, profile_id: `test-${values.kind}`, provider_id: 'synthetic', connection_id: null };
      case 'plugin:module-setup|snapshot': return { catalog: { modules: {}, profiles: {} }, selected: [] };
      case 'plugin:module-setup|python_status':
      case 'plugin:module-setup|ffmpeg_status':
      case 'plugin:module-setup|obs_status': return { installed: false, bootstrap_available: false, detail: 'Synthetic unavailable tool.' };
      case 'plugin:module-setup|obs_scene_plan': return { scenes: [], apply_available: false, detail: 'Synthetic plan.' };
      case 'setup_sync_settings': return { enabled: false, api_key_set: false };
      case 'plugin:module-setup|docker_plan': return { modules: [], services: [], detail: 'Synthetic plan.' };
      case 'plugin:module-setup|docker_status': return { state: 'missing', services_ready: false, service_states: {}, detail: 'Synthetic unavailable tool.' };
      case 'recordings_list': return [];
      default: throw new Error(`No native operation in browser fixture: ${command}`);
    }
  });
}
