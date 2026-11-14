/** @typedef {{session_id:string|null,context_id:string,managed_recording_available?:boolean,connected:boolean,stream_active:boolean|null,recording_active:boolean|null,owned:boolean,recovery_required:boolean,handoff_pending:boolean,source_profile_id:string|null,content_profile_id:string|null}} Status */
/** @typedef {{name:string,muted:boolean,context_id:string,session_id:string|null}} AudioInput */
/** @typedef {{name:string,is_current:boolean,context_id:string,session_id:string|null}} Scene */
/** @typedef {{status:Status|null,inputs:AudioInput[],scenes:Scene[],working:boolean,inspecting:boolean,audioLoading:boolean,unknown:boolean,error:string,notice:string}} View */
/** @typedef {(command:string,args?:Record<string,unknown>)=>Promise<unknown>} Invoke */
/** @returns {View} */
export function initialProductionView() { return {status:null,inputs:[],scenes:[],working:false,inspecting:false,audioLoading:false,unknown:true,error:'',notice:''}; }

export class ProductionClient {
  /** @param {Invoke} invoke @param {(view:View)=>void} changed */
  constructor(invoke, changed) {
    this.invoke=invoke; this.changed=changed; this.view=initialProductionView();
    this.enabled=false; this.alive=true; this.checking=false; this.epoch=0;
    this.audioContext=''; this.sceneContext=''; this.audioFailed=false; this.connectionChanges=0; this.refreshAfterChange=false;
  }
  emit() { if(this.alive) this.changed({...this.view,inputs:[...this.view.inputs],scenes:[...this.view.scenes]}); }
  /** @param {boolean} enabled */
  setEnabled(enabled) {
    const changed=this.enabled!==enabled; this.enabled=enabled;
    if(!enabled && !this.view.status?.session_id && (changed || this.view.status)) this.invalidateIdleObservations();
  }
  invalidateIdleObservations() {
    if(this.view.status?.session_id) return;
    this.epoch++; this.view.status=null; this.view.inputs=[]; this.view.scenes=[];
    this.audioContext=''; this.sceneContext=''; this.view.unknown=true; this.emit();
  }
  beginConnectionChange() {
    this.connectionChanges++; this.invalidateIdleObservations();
  }
  endConnectionChange() {
    this.connectionChanges=Math.max(0,this.connectionChanges-1);
    if(!this.connectionChanges) { this.invalidateIdleObservations(); this.refreshAfterChange=true; void this.refresh(); }
  }
  close() { this.alive=false; this.epoch++; }
  get context() { return this.view.status?.context_id ?? ''; }
  async refresh() {
    if(!this.alive || this.checking || (this.connectionChanges && !this.view.status?.session_id)) return;
    // Probe the native pin even before preferences load (including webview reload).
    // Idle admission remains enforced by the native pack/settings/vault gate.
    const epoch=this.epoch;
    this.refreshAfterChange=false; this.checking=true;
    try {
      const status=/** @type {Status} */(await this.invoke('production_status'));
      if(!this.alive || epoch!==this.epoch) return;
      if(!this.enabled && !status.session_id) return;
      if(this.context!==status.context_id) { this.view.inputs=[]; this.view.scenes=[]; this.audioContext=''; this.sceneContext=''; }
      this.view.status=status; this.view.unknown=!status.connected;
      // Audio belongs to safety, independent of the task page/manual inspection.
      if(status.connected || status.session_id) void this.refreshAudio();
    } catch { if(this.alive && epoch===this.epoch) this.view.unknown=true; }
    finally {
      this.checking=false; this.emit();
      // One replacement read after an invalidated in-flight observation; no
      // accumulating poll queue and no automatic mutation retry.
      if(this.alive && this.refreshAfterChange && !this.view.working && !this.connectionChanges) void this.refresh();
    }
  }
  async refreshAudio() {
    if(!this.alive || this.view.audioLoading || !this.context || (this.connectionChanges && !this.view.status?.session_id)) return;
    const epoch=this.epoch, context=this.context;
    this.view.audioLoading=true; this.emit();
    try {
      const result=/** @type {{context_id:string,session_id:string|null,value:AudioInput[]}} */(await this.invoke('production_audio_inputs'));
      if(this.alive && epoch===this.epoch && context===this.context && result.context_id===context) {
        this.view.inputs=result.value.map(input=>({...input,context_id:result.context_id,session_id:result.session_id ?? null})); this.audioContext=context; this.audioFailed=false;
      }
    } catch { if(epoch===this.epoch && context===this.context) { this.view.inputs=[]; this.audioFailed=true; } }
    finally {
      this.view.audioLoading=false; this.emit();
      // At most one read in flight. A context change queues one replacement,
      // never an accumulating request per poll/navigation event.
      if(this.alive && this.context && (context!==this.context || epoch!==this.epoch)) void this.refreshAudio();
    }
  }
  async inspect() {
    if(!this.alive || this.view.inspecting || (this.connectionChanges && !this.view.status?.session_id)) return;
    const epoch=this.epoch, context=this.context;
    this.view.inspecting=true; this.emit();
    void this.refreshAudio();
    try {
      const result=/** @type {{context_id:string,session_id:string|null,value:Scene[]}} */(await this.invoke('production_scenes'));
      if(this.alive && epoch===this.epoch && context===this.context && result.context_id===context) {
        this.view.scenes=result.value.map(scene=>({...scene,context_id:result.context_id,session_id:result.session_id ?? null})); this.sceneContext=context;
      }
    } catch { if(epoch===this.epoch) this.view.error='Scene inspection unavailable. Safety controls remain available.'; }
    finally { this.view.inspecting=false; this.emit(); }
  }
  /** @param {AudioInput} input */
  setMute(input) {
    return this.act('production_set_mute',{inputName:input.name,muted:!input.muted,sessionId:input.session_id,expectedContextId:input.context_id});
  }
  /** @param {Scene} scene */
  switchScene(scene) {
    return this.act('production_switch_scene',{sceneName:scene.name,sessionId:scene.session_id,expectedContextId:scene.context_id});
  }
  /** @param {string} command @param {Record<string,unknown>} [args] */
  async act(command,args) {
    if(!this.alive || this.view.working) return;
    const observedContext=command==='production_set_mute'?this.audioContext:command==='production_switch_scene'?this.sceneContext:null;
    if(observedContext!==null && (!observedContext || args?.expectedContextId!==observedContext || (this.connectionChanges && !this.view.status?.session_id))) return;
    this.view.working=true; this.view.error=''; this.view.notice='';
    const epoch=++this.epoch; this.emit();
    try {
      const result=await this.invoke(command,args);
      if(!this.alive || epoch!==this.epoch) return;
      this.epoch++; // invalidate reads admitted while the mutation was in flight
      if(command==='production_start_recording') {
        const receipt=/** @type {{session_id:string,context_id:string,confirmed:boolean,source_profile_id:string,content_profile_id:string}} */(result);
        // The reservation is retained before any observation. Never invent
        // inactive/ready output state from an RPC receipt or failed read.
        this.view.status={session_id:receipt.session_id,context_id:receipt.context_id,managed_recording_available:this.view.status?.managed_recording_available ?? false,connected:false,stream_active:null,recording_active:null,owned:receipt.confirmed,recovery_required:!receipt.confirmed,handoff_pending:false,source_profile_id:receipt.source_profile_id,content_profile_id:receipt.content_profile_id};
        this.view.unknown=true; this.view.inputs=[]; this.view.scenes=[]; this.audioContext=''; this.sceneContext='';
        this.emit(); void this.refreshAudio();
      } else if(command==='production_set_mute') {
        const updated=/** @type {AudioInput[]} */(result).map(input=>({...input,context_id:String(args?.expectedContextId),session_id:/** @type {string|null} */(args?.sessionId ?? null)}));
        for(const input of updated) { const index=this.view.inputs.findIndex(i=>i.name===input.name); if(index<0) this.view.inputs.push(input); else this.view.inputs[index]=input; }
      } else if(command==='production_switch_scene') this.view.scenes=/** @type {Scene[]} */(result).map(scene=>({...scene,context_id:String(args?.expectedContextId),session_id:/** @type {string|null} */(args?.sessionId ?? null)}));
      else {
        this.view.notice=typeof result==='string'?result:'OBS recovery completed; no recording was imported.';
        // Stop/abandon/recover acknowledged completion of this generation.
        this.view.status=null; this.view.inputs=[]; this.view.scenes=[]; this.audioContext=''; this.sceneContext='';
      }
    } catch {
      if(epoch===this.epoch) {
        this.view.error='OBS did not confirm the action. Refresh status. If continuity is lost, control the output in OBS and recover only when inactive.';
        this.view.unknown=true;
        if(observedContext!==null && !this.view.status?.session_id) this.invalidateIdleObservations();
      }
    } finally { this.view.working=false; this.emit(); await this.refresh(); }
  }
}
