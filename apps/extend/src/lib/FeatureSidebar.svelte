<script lang="ts">
  import type { NavigationGroup, NavigationItem } from './navigation.js';

  let { groups, utilities, shortcuts, expanded, activeId, enabled, settingsActive, onNavigate, onToggle }:
    { groups: NavigationGroup[]; utilities: NavigationItem[]; shortcuts: NavigationItem[];
      expanded: Record<string, boolean>; activeId: string; enabled: boolean; settingsActive: boolean;
      onNavigate: (id: string) => void; onToggle: (id: string, open: boolean) => void } = $props();
</script>

<nav aria-label="Features" class="features">
  {#each groups as group (group.id)}
    <details open={expanded[group.id] !== false} ontoggle={(event) => onToggle(group.id, event.currentTarget.open)}>
      <summary>{group.label}</summary>
      <div class="items">
        {#each group.items as item (item.id)}
          <button disabled={!enabled || item.available === false} aria-current={activeId === item.id ? 'page' : undefined}
            title={item.available === false ? 'Not available in this preview' : undefined} onclick={() => onNavigate(item.id)}>
            <span>{item.label}</span>{#if item.available === false}<small>Later</small>{/if}
          </button>
        {/each}
      </div>
    </details>
  {/each}
</nav>
<nav aria-label="Workspace utilities" class="utilities">
  {#each utilities as item (item.id)}
    <button disabled={!enabled} aria-current={activeId === item.id ? 'page' : undefined} onclick={() => onNavigate(item.id)}>{item.label}</button>
    {#if item.id === 'setup' && settingsActive}
      <div class="shortcuts" aria-label="Settings sections">
        {#each shortcuts as shortcut}
          <button disabled={!enabled} aria-current={activeId === shortcut.id ? 'location' : undefined} onclick={() => onNavigate(shortcut.id)}>{shortcut.label}</button>
        {/each}
      </div>
    {/if}
  {/each}
</nav>

<style>
  nav { display: grid; gap: 8px; }
  .features { flex: 1; min-height: 100px; overflow-y: auto; align-content: start; padding: 4px; margin: 12px -4px 0; }
  .utilities { flex-shrink: 0; margin-top: auto; padding-top: 16px; border-top: 1px solid #dedfd7; }
  details { padding-bottom: 8px; }
  summary { cursor: pointer; color: #586158; padding: 10px 4px; font-size: 12px; font-weight: 700; letter-spacing: .06em; }
  .items { display: grid; gap: 3px; margin-top: 4px; }
  button { display: flex; align-items: center; justify-content: space-between; gap: 6px; width: 100%; text-align: left; background: transparent; color: #284837; border: 1px solid transparent; border-radius: 8px; padding: 10px; font: inherit; font-size: 14px; cursor: pointer; }
  button:hover:enabled { background: #e7eee5; }
  button[aria-current] { background: #dde7df; color: #234a38; font-weight: 650; }
  button:disabled { color: #747b72; cursor: default; }
  small { font-size: 10px; font-weight: 500; color: #586158; border: 1px solid #cbd2c7; border-radius: 4px; padding: 2px 4px; }
  button span { min-width: 0; overflow-wrap: anywhere; }
  .shortcuts { display: grid; padding-left: 12px; border-left: 1px solid #cbd2c7; margin-left: 10px; }
  .shortcuts button { font-size: 12px; }
  button:focus-visible, summary:focus-visible { outline: 3px solid #c69045; outline-offset: 3px; }
  @media (max-width: 760px) { .features { margin-top: 18px; max-height: 40dvh; } .utilities { margin-top: 16px; padding-top: 16px; } }
</style>
