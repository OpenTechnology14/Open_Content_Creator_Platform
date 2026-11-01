# Components

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory.** This is the specification layer: usage rules and anti-patterns, with **no implementation
> code**. Each consumer builds these in its own stack. Labels (Verified, Sourced, Proposed, Blocked) are defined in the
> [README](README.md#evidence-labels).

## Inventory (Verified, 2026-10-21)

What each consumer actually ships. A blank cell means nothing was found, not that nothing is wanted.

| Family | OpenTechnologyApp | OpenTechnologyBlog | MyFeed | Desktop apps and shell (this repo) |
|---|---|---|---|---|
| Button | `button` primitive (variant, size) | `button` primitive | `.button` class | a styled `button` per page: outline with accent border and text (Stream, Creator); filled `.primary` (Extend shell) |
| Card / panel | `card` | page components | CSS cards | `.panel`: raised surface, 1px border, 12px radius, 1.5rem padding |
| Modal / overlay | `dialog` | — | `.modal` family and `ConnectionModal` | none: no `<dialog>` and no `role="dialog"` in any desktop page |
| Form | `input`, `label`, `select` | `input`, `select`, `textarea` | `.field` | native `label`, `input`, `select` with page CSS |
| Badge / status | `badge` | `badge` | — | `.indicator` pill and status chips |
| Tabs / navigation | `tabs`, sidebar rail, hamburger popout | `Header`, `dropdown-menu` | `.sidebar`, `.nav-item` | `nav` of `aria-pressed` buttons (Creator); `aside` of `aria-current` buttons and `details` groups (Extend shell) |
| Feedback | toasts (by rule), `aria-live` regions | `sonner` toasts, `tooltip` | `.toast` | inline `role="alert"` text (15 uses) and `aria-live="polite"` (2) |
| Broadcast graphics | — | — | — | NodeCG `hcp-starter`: lower third, scoreboard, sponsor rotator |

Sources: `src/components/ui/` in the App (avatar, badge, button, card, dialog, input, label, select, separator, tabs) and
the Blog (badge, button, dropdown-menu, input, select, sonner, textarea, tooltip); class names in MyFeed's
`src/styles.css`; the desktop Svelte pages under `apps/`.

## Rules that apply to every family

- **Sourced** — Theme colors come from variables, never hex literals, except for data-visualization colors where semantic
  tokens do not apply. Primitives are never edited; they are wrapped. Right primitive for the job. (`OpenTechnologyApp:CLAUDE.md`
  § shadcn/ui conventions)
- **Sourced** — Accessibility is part of the component, not a later pass; see [`accessibility.md`](accessibility.md).
- **Sourced** — Status shows **observed** state, never optimistic state. The shared setup UI does not mark a module ready
  because a selection or install succeeded, and controls backed by a declared capability stay locked until current native
  evidence passes (`apps/shared/ui/README.md`). The Blender job UI shows observed process and artifact state rather than
  optimistic completion messages (`docs/proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md` §1).
- **Sourced** — Always show the active profile and whether a destination is local or cloud (`docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md` §8).
- **Proposed** — Component rules name tokens by role (`surface.raised`, `brand.primary`), never by value.

## Buttons

**Verified.** The App and Blog use a variant-and-size primitive. Stream Extend and Creator Extend style a plain `button`
per page: transparent fill, accent border and text, accent fill with white text on hover. The Extend shell has a filled
`.primary` button, `aria-pressed` toggle buttons, and `button:disabled` at half opacity.

**Rules**
- **Sourced** — Use the primitive with the correct `variant` and `size`; do not style a raw `<button>`. When a button wraps a
  link, the primitive's `asChild` form keeps one element in the tab order. (`OpenTechnologyApp:CLAUDE.md`)
- **Sourced** — Every interactive element is keyboard-focusable and operable with Enter or Space.
- **Sourced** — A destructive terminal action goes last in its group and asks for a two-step inline confirmation, with a busy
  state and a failure notice (the App's Sign out, `OpenTechnologyApp:docs/proposals/PROPOSAL_UI_REDESIGN_HAMBURGER_AND_VIEW_TOGGLE.md`, Revision 5).
- **Sourced** — A control whose capability is not verified is locked, with the reason visible, not hidden.
- **Proposed** — One primary action per region. A busy button stays in place, is disabled, and says in text what is happening.
- **Proposed** — Hit target at least 24×24 CSS px (WCAG 2.5.8); 44px on touch surfaces, as the App's rail uses.

**Anti-patterns**
- An outline button whose hover fill fails contrast. Verified: Stream Extend's hover state is white on its orange, 2.84:1
  (`tokens.yaml` `contrast.observed_pairs`).
- A raw styled `<button>` where a primitive exists; `alert()` or `console.log` as user feedback.
- Conveying state by color alone (an active tab differing only in fill).
- Disabling a button with no stated reason.

## Cards and panels

**Verified.** The desktop apps separate surfaces with a 1px border and no shadow. The Blog uses a card shadow
(`shadow.card`, `shadow.card-hover`); the App defines three elevations; MyFeed has one shadow variable.

**Rules**
- **Proposed** — A card groups content; it is not a button. If the whole card is clickable it is one link or button with one
  accessible name, not a container of nested interactive elements.
- **Proposed** — Use `surface.raised` for the card and `radius.lg` for its corners. Separate with a border or a shadow, not
  both; which one is the identity's choice (decision D-1).

**Anti-patterns:** cards nested inside cards; `surface.raised` as the page background; a decorative card with no content role.

## Modals, sheets and popovers

**Verified.** The App uses `dialog`; MyFeed has a modal family and `ConnectionModal`; the desktop apps have none.

**Rules**
- **Sourced** — Prefer the dialog primitive over a custom modal, a sheet over a custom drawer, a popover over a custom dropdown.
  A modal traps focus while open and restores focus to its trigger on close; the primitive does this, so do not replace it with
  a custom `div`. (`OpenTechnologyApp:CLAUDE.md`)
- **Proposed** — Escape closes; the title labels the dialog; the first focusable control or the title takes focus on open.
- **Proposed** — A lightweight destructive confirmation is inline (see Buttons); an irreversible one with consequences is a dialog.

**Anti-patterns:** a custom `div` modal; focus lost on close; stacked modals; a modal for content that could be inline.

## Forms

**Verified.** Extend shell: each `label` wraps its input in a grid with an 8px gap and a 420px maximum width; inputs have a
7px radius and a 1px border. MyFeed styles a `.field`.

**Rules**
- **Sourced** — Every input has an associated `<label>` (`htmlFor` or `aria-label`); placeholder text is never the only label.
  Forms the user submits are controlled forms built with a schema validator. Inline errors appear in an `aria-live` region.
  (`OpenTechnologyApp:CLAUDE.md`)
- **Sourced** — Secret fields are write-only: an API key never re-enters the component after saving; only an "is set" flag
  returns (`apps/shared/ui/README.md`).
- **Proposed** — An error names the field and how to fix it (WCAG 3.3.1, 3.3.3). A required field is marked in text, not color.

**Anti-patterns:** placeholder as label; color-only error; a toast for a field error; echoing a stored secret back into a field.

## Badges and status indicators

**Verified.** The App and Blog have a `badge` primitive. The desktop apps use an `.indicator` pill (12px radius) whose
connected state is green text on a dark green fill, and status chips in the shared components.

**Rules**
- **Sourced** — Never convey information through color alone; pair color with text, an icon or a pattern (the App's priority
  indicators use both color and an icon). (`OpenTechnologyApp:CLAUDE.md`)
- **Sourced** — A "ready" or "connected" badge reflects evidence, not intent (see the cross-cutting rule above).
- **Blocked (D-4)** — The success, warning and info colors: no web consumer defines them and the desktop apps disagree.

**Anti-patterns:** a green "ready" for an unverified state; a color-only badge; a badge that behaves like a button.

## Navigation patterns

**Verified.** Three patterns exist:
- *Rail and popout* (App). Order: Home, Menu, Data/Automations, Search, Settings, Theme, Language, Support, Notifications,
  Chatbot, Sign out. Below the `md` breakpoint the later items collapse into a "…" overflow menu; the rail's items are 44px
  touch targets.
- *Toggle-button view tabs* (Creator Extend): a `nav` labelled "Workspace view" of buttons using `aria-pressed`.
- *Sidebar with current page* (Extend shell): an `aside` labelled "Workspace navigation" of buttons using `aria-current="page"`
  and `details` groups, collapsing to one column at 760px.
- Both desktop apps also keep a **profile switcher** in the header, visible from every view, with routing remembered per profile
  (`docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §6.1).

**Rules**
- **Sourced** — The rail is for quick access and Settings is for grouped management; both may exist (the owner's decision
  after testing the alternative, recorded in the App's UI redesign proposal, Revision 5). Do not show a destination twice.
- **Sourced** — Workspace switching is keyboard-accessible, focus is predictable, busy and error states are readable, and
  screen-reader labels exist (`docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md` §8).
- **Proposed** — `aria-current="page"` marks the current destination in navigation; `aria-pressed` is for toggles. View
  switching that swaps panels on one page uses the tabs pattern. Creator Extend's `aria-pressed` buttons are a divergence to
  resolve, not a rule.

**Anti-patterns:** hiding the active profile; two navigation systems reaching the same destination with different labels;
navigation that moves focus unpredictably; an overflow menu that is always collapsed.

## Feedback and loading

**Rules**
- **Sourced** — Toasts, never `alert()` or `console.log`, for user-facing messages. `aria-live` for content that appears without
  a page load. A skeleton that matches the real content shape for loading. (`OpenTechnologyApp:CLAUDE.md`)
- **Sourced** — Busy and error states are readable (P-072 §8).
- **Proposed** — An empty state says what to do next.

**Anti-patterns:** a spinner with no text on a long operation; an error that disappears before it can be read; layout shift
when content arrives.

## Broadcast overlays

**Verified.** The NodeCG `hcp-starter` bundle ships a lower third, a scoreboard and a sponsor rotator on a 1920×1080 browser
source, with transparent backgrounds and white text.

**Rules**
- **Sourced** — Overlays must render at 60 fps inside OBS; avoid heavy WebGL for ordinary lower thirds because it competes
  with the encoder. For 3D or particles, pre-render a transparent video
  (`modules/broadcast-graphics/nodecg/bundles/hcp-starter/README.md`).
- **Sourced** — One palette and one typeface across all of an account's artifacts and all of its games; per-game overlay variants
  are fine, per-game branding is not (`docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §3.6).
- **Proposed** — Nothing in an overlay flashes more than three times per second (WCAG 2.3.1).

## Across the folder: what not to do

- Do not add a component to the hub that no consumer ships; a pattern enters the inventory when it exists or when a design
  proposal carries it.
- Do not copy token values into this file. Name the role.
- Do not edit a vendor primitive to restyle it; wrap it, or propose a token.
