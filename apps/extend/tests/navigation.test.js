import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { visiblePages, withPacks, homeActions } from '../src/lib/navigation.js';

/** @type {{pages:{id:string,label:string,pack?:string}[],groups:{modules:string[]}[]}} */
const navigation = JSON.parse(readFileSync(new URL('../../../configs/ui/combined-navigation.json', import.meta.url), 'utf8'));

test('single-pack navigation omits unrelated tasks and remains discoverable through settings', () => {
  assert.deepEqual(visiblePages(navigation.pages, ['stream']).map(page => page.id), ['home', 'stream', 'settings']);
  assert.deepEqual(visiblePages(navigation.pages, ['content']).map(page => page.id), ['home', 'create', 'library', 'settings']);
});
test('changing packs leaves source settings intact and restores a safe page', () => {
  const before = { active_page: 'library', enabled_packs: ['content'], obs_host: 'obs.test' };
  const after = withPacks(before, ['stream']);
  assert.equal(after.active_page, 'home');
  assert.equal(before.active_page, 'library');
  assert.equal(after.obs_host, before.obs_host);
});
test('Home has at most three relevant task actions with setup first', () => {
  for (const packs of [['stream'], ['content'], ['stream', 'content']]) {
    const actions = homeActions(packs);
    assert.equal(actions[0], 'settings'); assert.ok(actions.length <= 3);
    for (const action of actions) assert.ok(visiblePages(navigation.pages, packs).some(page => page.id === action));
  }
});
test('tool discovery covers all modules exactly once', () => {
  const modules = navigation.groups.flatMap(group => group.modules);
  assert.equal(modules.length, 21); assert.equal(new Set(modules).size, 21);
});
