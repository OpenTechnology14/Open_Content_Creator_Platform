import fs from 'node:fs';
import readline from 'node:readline';
import {validate,Controller} from './core.mjs';
const configPath=process.argv[process.argv.indexOf('--config')+1];
const output=value=>process.stdout.write(JSON.stringify(value)+'\n');
let controller;
try {
  if (!process.argv.includes('--config') || fs.statSync(configPath).size>65536) throw Error('invalid_configuration');
  const config=validate(JSON.parse(fs.readFileSync(configPath,'utf8')));
  if (Number(process.versions.node.split('.')[0]) < 22) throw Error('node_22_required');
  if (!config.enabled && !process.argv.includes('--dependency-check')) { output({valid:false,reason:'adapter_disabled'}); process.exit(0); }
  const imported=await import('mineflayer');
  const mineflayer=imported.default||imported;
  if(process.argv.includes('--dependency-check')) {output({valid:typeof mineflayer.createBot==='function',connected:false});process.exit(0);}
  if(process.argv.includes('--validate')) {output({valid:true,world_id:config.world_id,connected:false});process.exit(0);}
  if(!process.argv.includes('--stdio')) throw Error('invalid_mode');
  controller=new Controller(config,options=>mineflayer.createBot(options));
  const input=readline.createInterface({input:process.stdin});
  const allowed=new Set(['connect','observe','task','release','close']);
  let pending=false;
  input.on('line',async line=>{
    let request={};
    try {
      if(Buffer.byteLength(line)>4096) { controller.close(); input.close(); throw Error('frame_too_large'); }
      request=JSON.parse(line);
      if(Object.keys(request).sort().join(',')!=='action,epoch,operation_id' || typeof request.operation_id!=='string' || !/^[a-zA-Z0-9_-]{1,64}$/.test(request.operation_id) || !Number.isInteger(request.epoch) || request.epoch<0 || request.epoch>1000000000 || !allowed.has(request.action)) throw Error('invalid_request');
      if(pending && !['release','close'].includes(request.action)) throw Error('busy');
      let result;
      if(request.action==='release') result=controller.release(request.epoch);
      else if(request.action==='close'){controller.close();result={ok:true,released:true,epoch:request.epoch};input.close();}
      else {
        pending=true;
        try { result=request.action==='connect'?{ok:true,observation:await controller.connect()}:request.action==='observe'?{ok:true,observation:controller.observe()}:await controller.perform(request.epoch); }
        finally {pending=false;}
      }
      output({...result,operation_id:request.operation_id,epoch:result.epoch??request.epoch});
    } catch(error) { output({operation_id:typeof request.operation_id==='string'?request.operation_id:null,ok:false,error:['permission_required','stale_epoch','stale_or_busy','busy'].includes(error.message)?error.message:'adapter_error'}); }
  });
  input.on('close',()=>{controller.close();});
  process.on('SIGTERM',()=>{controller.close();process.exit(0);});
  process.on('SIGINT',()=>{controller.close();process.exit(0);});
} catch {output({valid:false,reason:'adapter_unavailable_or_invalid_configuration'});process.exitCode=1;}
