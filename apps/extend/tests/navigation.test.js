import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { visiblePages, visibleGroups, navigationTarget, disclosureState, withPacks, homeActions } from '../src/lib/navigation.js';

/** @type {{pages:{id:string,label:string,pack?:string}[],groups:{modules:string[]}[], sidebar_groups:import('../src/lib/navigation.js').NavigationGroup[], utilities:import('../src/lib/navigation.js').NavigationItem[], shortcuts:import('../src/lib/navigation.js').NavigationItem[]}} */
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

const destinations = [...navigation.sidebar_groups.flatMap(group => group.items), ...navigation.utilities, ...navigation.shortcuts];

test('feature groups follow the agreed order and omit disabled packs', () => {
  assert.deepEqual(visibleGroups(navigation.sidebar_groups, ['stream', 'content']).map(group => group.label), ['Workspace', 'Production', 'Studio']);
  assert.deepEqual(visibleGroups(navigation.sidebar_groups, ['stream']).map(group => group.id), ['workspace', 'production']);
  assert.deepEqual(visibleGroups(navigation.sidebar_groups, ['content']).map(group => group.id), ['workspace', 'studio']);
  assert.deepEqual(navigation.utilities.map(item => item.id), ['profiles', 'setup', 'help']);
});

test('section links resolve only enabled native pages and available features', () => {
  assert.equal(navigationTarget(destinations, navigation.pages, 'connections', ['stream'])?.section, 'connections');
  for (const id of ['media-library', 'images', 'clips', 'unknown', '__proto__']) {
    assert.equal(navigationTarget(destinations, navigation.pages, id, ['stream']), null);
  }
  assert.equal(navigationTarget(destinations, navigation.pages, 'live-recording', ['content']), null);
  assert.equal(navigationTarget([{ id: 'crafted', label: 'Crafted', page: 'create', section: 'workflow-catalog' }], navigation.pages, 'crafted', ['stream']), null);
  assert.equal(navigationTarget([{ id: 'future', label: 'Future', available: false, page: 'home', section: 'workspace-overview' }], navigation.pages, 'future', ['stream']), null);
  assert.equal(navigationTarget([{ id: 'partial', label: 'Partial', page: 'home' }], navigation.pages, 'partial', ['stream']), null);
});

test('presentation state recovers from corrupted storage and ignores unrelated values', () => {
  assert.deepEqual(disclosureState('{broken', ['workspace', 'production']), { workspace: true, production: false });
  assert.deepEqual(disclosureState('null', ['workspace']), { workspace: true });
  assert.deepEqual(disclosureState('{"workspace":false,"production":"false","password":"discard"}', ['workspace', 'production']), { workspace: false, production: false });
  assert.deepEqual(disclosureState('{"production":true}', ['workspace', 'production', 'studio']), { workspace: true, production: true, studio: false });
});

test('every available destination targets a real section and keeps a unique feature identity', () => {
  const source = readFileSync(new URL('../src/routes/+page.svelte', import.meta.url), 'utf8');
  assert.equal(new Set(destinations.map(item => item.id)).size, destinations.length);
  for (const item of destinations.filter(item => item.available !== false)) {
    assert.ok(navigationTarget(destinations, navigation.pages, item.id, ['stream', 'content']));
    assert.ok(item.section && source.includes(item.section), `${item.id} target ${item.section} exists`);
  }
});
