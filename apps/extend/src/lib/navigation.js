/** Shared presentation rules; native admission independently validates every request. */
/** @param {{id:string,label:string,pack?:string}[]} pages @param {string[]} packs */
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
