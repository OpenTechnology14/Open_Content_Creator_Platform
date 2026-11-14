/** Shared presentation rules; native admission independently validates every request. */
/** @template {{id:string,label:string,pack?:string}} T
 * @param {T[]} pages @param {string[]} packs */
export function visiblePages(pages, packs) {
  return pages.filter((page) => !page.pack || packs.includes(page.pack));
}

/** @template T @param {T} preferences @param {string[]} packs */
export function withPacks(preferences, packs) {
  return { ...preferences, enabled_packs: [...packs], active_page: 'home' };
}

/** @param {string[]} packs */
export function homeActions(packs) {
  return ['settings', ...(packs.includes('stream') ? ['stream'] : []), ...(packs.includes('content') ? ['library'] : [])];
}

/** @typedef {{id:string, label:string, pack?:string, page?:string, section?:string, available?:boolean}} NavigationItem */
/** @typedef {{id:string, label:string, items:NavigationItem[]}} NavigationGroup */

/** @param {NavigationGroup[]} groups @param {string[]} packs */
export function visibleGroups(groups, packs) {
  return groups.map(group => ({ ...group, items: visiblePages(group.items, packs) }))
    .filter(group => group.items.length > 0);
}

/** Resolve only bundled, enabled destinations. A URL never grants a pack or native permission.
 * @param {NavigationItem[]} items @param {{id:string,label:string,pack?:string}[]} pages
 * @param {string} id @param {string[]} packs
 */
export function navigationTarget(items, pages, id, packs) {
  const item = visiblePages(items, packs).find(item => item.id === id);
  if (!item || item.available === false || !item.page || !item.section) return null;
  return visiblePages(pages, packs).some(page => page.id === item.page) ? item : null;
}

/** Only known booleans are restored; presentation storage never contains endpoints or secrets.
 * @param {string|null} stored @param {string[]} ids
 * @returns {Record<string,boolean>}
 */
export function disclosureState(stored, ids) {
  try {
    const value = JSON.parse(stored ?? '{}');
    return Object.fromEntries(ids.map(id => [id, typeof value?.[id] === 'boolean' ? value[id] : id === 'workspace']));
  } catch {
    return Object.fromEntries(ids.map(id => [id, id === 'workspace']));
  }
}
