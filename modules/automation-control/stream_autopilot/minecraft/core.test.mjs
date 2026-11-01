import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {validate,Controller} from './core.mjs';
const config=()=>({schema_version:1,enabled:true,permission_confirmed:true,permission_statement:'Owned disposable test world permits this bot.',world_id:'fixture',host:'127.0.0.1',port:25565,username:'hcp_fixture',game_version:null,task:{action:'forward',duration_ms:50}});
class Bot extends EventEmitter {constructor(){super();this.health=20;this.entity={position:{x:0,y:1,z:0}};this.controls={};queueMicrotask(()=>this.emit('spawn'));}clearControlStates(){this.controls={};}setControlState(key,value){this.controls[key]=value;this.entity.position.x+=1;}quit(){this.emit('end');}}
test('permission and private target required before any client factory',async()=>{
  assert.throws(()=>validate({...config(),host:'8.8.8.8'}));
  assert.throws(()=>validate({...config(),permission_confirmed:false}));
  const controller=new Controller({...config(),enabled:false},()=>assert.fail('connected'));
  await assert.rejects(()=>controller.connect());
});
test('bounded task observes progress and releases controls',async()=>{
  let bot;const controller=new Controller(config(),options=>{assert.equal(options.auth,'offline');return bot=new Bot();});
  await controller.connect();const result=await controller.perform(1);
  assert.equal(result.ok,true);assert.equal(result.distance,1);assert.deepEqual(bot.controls,{});controller.close();
});
test('release supersedes active task and rejects stale epochs',async()=>{
  let bot;const controller=new Controller(config(),()=>bot=new Bot());await controller.connect();
  const task=controller.perform(1);const released=controller.release(2);
  assert.equal(released.released,true);assert.equal((await task).error,'interrupted');assert.deepEqual(bot.controls,{});
  await assert.rejects(()=>controller.perform(1));controller.close();
});
test('no movement is never claimed task completion',async()=>{
  const controller=new Controller(config(),()=>{const bot=new Bot();bot.setControlState=()=>{};return bot;});await controller.connect();
  assert.equal((await controller.perform(1)).error,'no_movement_observed');controller.close();
});
