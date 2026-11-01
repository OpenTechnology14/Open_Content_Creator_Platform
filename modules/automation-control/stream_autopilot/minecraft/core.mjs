import { isIP } from 'node:net';
const keys = ['schema_version','enabled','permission_confirmed','permission_statement','world_id','host','port','username','game_version','task'];
export function validate(config) {
  if (!config || typeof config !== 'object' || Object.keys(config).length !== keys.length || keys.some(key => !(key in config))) throw Error('invalid_configuration');
  if (config.schema_version !== 1 || typeof config.enabled !== 'boolean' || typeof config.permission_confirmed !== 'boolean') throw Error('invalid_configuration');
  if (typeof config.permission_statement !== 'string' || config.permission_statement.length > 500 || !/^[a-zA-Z0-9_-]{1,64}$/.test(config.world_id)) throw Error('invalid_permission');
  const ip = config.host === 'localhost' ? '127.0.0.1' : config.host;
  const octets = typeof ip === 'string' ? ip.split('.').map(Number) : [];
  const privateHost = ip === '::1' || (isIP(ip) === 4 && (octets[0] === 127 || octets[0] === 10 || (octets[0] === 192 && octets[1] === 168) || (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31)));
  if (!privateHost || !Number.isInteger(config.port) || config.port < 1 || config.port > 65535) throw Error('private_server_required');
  if (!/^hcp_[a-zA-Z0-9_]{1,12}$/.test(config.username)) throw Error('dedicated_bot_identity_required');
  if (config.game_version !== null && (typeof config.game_version !== 'string' || !/^\d+\.\d+(\.\d+)?$/.test(config.game_version))) throw Error('invalid_version');
  if (!config.task || Object.keys(config.task).sort().join(',') !== 'action,duration_ms' || !['forward','back','jump'].includes(config.task.action) || !Number.isInteger(config.task.duration_ms) || config.task.duration_ms < 50 || config.task.duration_ms > 1000) throw Error('bounded_task_required');
  if (config.enabled && (!config.permission_confirmed || config.permission_statement.trim().length < 10 || config.world_id === 'unbound')) throw Error('permission_required');
  return { ...config, host:ip };
}
export class Controller {
  constructor(config, factory) { this.config=validate(config); this.factory=factory; this.bot=null; this.epoch=0; this.hold=null; this.connected=false; }
  async connect() {
    if (!this.config.enabled || !this.config.permission_confirmed) throw Error('permission_required');
    if (this.bot) throw Error('already_connected');
    this.bot=this.factory({host:this.config.host,port:this.config.port,username:this.config.username,auth:'offline',version:this.config.game_version||false,respawn:false,logErrors:false,hideErrors:true});
    await new Promise((resolve,reject) => {
      const timer=setTimeout(()=>{this.close();reject(Error('spawn_timeout'));},10000);
      this.bot.once('spawn',()=>{clearTimeout(timer);this.connected=true;resolve();});
      this.bot.on('error',()=>{clearTimeout(timer);this.release(this.epoch+1);reject(Error('connection_failed'));});
      this.bot.on('end',()=>{clearTimeout(timer);this.connected=false;this.release(this.epoch+1);reject(Error('connection_closed'));});
    });
    return this.observe();
  }
  observe() {
    if (!this.connected || !this.bot?.entity?.position) throw Error('not_connected');
    const {x,y,z}=this.bot.entity.position;
    if (![x,y,z,this.bot.health].every(Number.isFinite)) throw Error('invalid_observation');
    return {world_id:this.config.world_id,position:{x,y,z},health:this.bot.health};
  }
  release(epoch) {
    if (!Number.isInteger(epoch) || epoch < this.epoch) throw Error('stale_epoch');
    this.epoch=epoch;
    if (this.hold) { clearTimeout(this.hold.timer); this.hold.finish({ok:false,error:'interrupted',epoch:this.hold.epoch,released:true}); this.hold=null; }
    if (this.bot) this.bot.clearControlStates();
    return {ok:true,epoch,released:true};
  }
  async perform(epoch) {
    if (!Number.isInteger(epoch) || epoch <= this.epoch || this.hold) throw Error('stale_or_busy');
    const before=this.observe(); this.epoch=epoch;
    this.bot.clearControlStates(); this.bot.setControlState(this.config.task.action,true);
    return new Promise(resolve=>{
      this.hold={epoch,finish:resolve,timer:setTimeout(()=>{
        this.hold=null; this.bot.clearControlStates();
        try {
          const after=this.observe();
          const delta=Math.hypot(after.position.x-before.position.x,after.position.y-before.position.y,after.position.z-before.position.z);
          resolve({ok:delta>0.01,epoch,released:true,before,after,distance:delta,error:delta>0.01?null:'no_movement_observed'});
        } catch { resolve({ok:false,epoch,released:true,error:'observation_failed'}); }
      },this.config.task.duration_ms)};
    });
  }
  close() { this.release(this.epoch+1); if(this.bot) this.bot.quit('operator stop');this.bot=null;this.connected=false; }
}
