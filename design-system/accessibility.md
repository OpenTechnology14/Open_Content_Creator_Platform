# Accessibility

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory until approved.** Labels (Verified, Sourced, Proposed, Blocked) are defined in the
> [README](README.md#evidence-labels). Standards references (WCAG, the WAI-ARIA Authoring Practices) are external; the
> repository does not vendor them, so they are cited by number.

## Baseline

**WCAG Level AA** is the baseline. That is the owner's direction for this hub (relayed 2026-10-21), and it matches what the
App already states: contrast "must meet WCAG AA: 4.5:1 for body text, 3:1 for large text and UI controls"
(`OpenTechnologyApp:CLAUDE.md` § Accessibility conventions). Neither says which version.

**Proposed (D-6):** cite **WCAG 2.2** Level AA, which includes everything in 2.1 AA and adds, among others, focus-not-obscured (2.4.11)
and minimum target size (2.5.8). Focus Appearance (2.4.13) is Level AAA in 2.2 and is **not** part of the baseline; this hub's
focus-indicator contrast comes from Non-text Contrast (1.4.11) instead.

| Need | Success criterion | Hub rule | Evidence |
|---|---|---|---|
| Text contrast | 1.4.3 (AA): 4.5:1, or 3:1 for large text (18pt, or 14pt bold) | every text pairing in `contrast.pairs` | **Sourced** (App), **Verified** (computed below) |
| Control and graphic contrast | 1.4.11 (AA): 3:1 for UI components, their states and graphical objects | borders that identify a control, focus indicators, icons that carry meaning | **Sourced** (App: 3:1 for UI controls) |
| Not color alone | 1.4.1 (A) | pair color with text, an icon or a pattern | **Sourced** (App) |
| Keyboard | 2.1.1 (A), 2.1.2 (A) | everything operable by keyboard, no trap except a modal | **Sourced** (App, P-072) |
| Focus visible | 2.4.7 (AA), 2.4.11 (AA, 2.2) | a visible indicator that sticky UI does not cover | **Proposed** |
| Target size | 2.5.8 (AA, 2.2): 24×24 CSS px | 24px floor; 44px on touch surfaces | **Sourced** (App rail uses 44px) |
| Names and roles | 4.1.2 (A) | semantic HTML first; ARIA only where HTML falls short | **Sourced** (App) |
| Labels and errors | 3.3.1 (A), 3.3.2 (A), 3.3.3 (AA) | label every input; name the field and the fix | **Sourced** (App), **Proposed** (3.3.x) |
| Status messages | 4.1.3 (AA) | `aria-live` for content that appears without a page load | **Sourced** (App) |
| Consistent naming | 3.2.3, 3.2.4 (AA) | one glyph, one meaning (see [`iconography.md`](iconography.md)) | **Proposed** |
| Motion and flashing | 2.2.2 (A), 2.3.1 (A) | no content that flashes more than three times a second; moving content can be paused | **Proposed** |
| Reflow and zoom | 1.4.4, 1.4.10 (AA) | usable at 200% zoom and a 320 CSS px width | **Proposed**; P-072 already requires narrow-window navigation |

## Color-contrast rules

1. A new or changed color token declares every foreground/background pairing it enters in `contrast.pairs` and passes, or is
   recorded in `contrast.known_failures` with a decision. A test recomputes every ratio; nothing here is estimated.
2. Text uses 4.5:1. Large text, control boundaries, focus indicators and meaningful icons use 3:1.
3. Disabled controls are exempt from the contrast criteria but must stay recognizable and say why they are disabled.
4. Logos and brand marks are exempt from 1.4.3; they are not interface text.
5. The state of a control (hover, active, selected) is checked as its own pairing. Verified failure: Stream Extend's hover
   state is white on its orange.

### Computed results for the proposed set

The proposed defaults are the Blog's values. These pairings fall short of the requirement (`tokens.yaml`
`contrast.known_failures`, all awaiting decision D-5). The ratios are exact to two decimals and re-computed by a test.

| Pairing | Theme | Ratio | Needs |
|---|---|---|---|
| `text.muted` on `surface.subtle` | light | 4.24 | 4.5 |
| `text.muted` on `surface.subtle` | dark | 4.30 | 4.5 |
| `brand.primary-contrast` on `brand.primary` | light | 4.43 | 4.5 |
| `brand.primary-contrast` on `brand.primary` | dark | 3.66 | 4.5 |
| `brand.primary` as link text on `surface.base` | light | 4.12 | 4.5 |
| `brand.accent-contrast` on `brand.accent` | light | 2.57 | 4.5 |
| `brand.accent-contrast` on `brand.accent` | dark | 1.97 | 4.5 |
| `brand.accent` as an icon or border on `surface.base` | light | 2.40 | 3.0 |
| `status.danger-contrast` on `status.danger` | light | 3.78 | 4.5 |
| `border.input` on `surface.base` | light | 1.25 | 3.0 |
| `border.input` on `surface.base` | dark | 1.31 | 3.0 |

Passing, for the record: body text on the page and on cards in both themes, muted text on the page and on cards, the focus
ring in both themes, and the dark-theme danger label.

### Observed failures in the consumers

Verified from the consumers' own values (`tokens.yaml` `contrast.observed_pairs`):

| Where | Ratio | Needs |
|---|---|---|
| OpenTechnologyApp primary button, light | 3.97 | 4.5 |
| OpenTechnologyApp primary button, dark | 3.03 | 4.5 |
| Stream Extend outline button on hover (white on orange) | 2.84 | 4.5 |
| Creator Extend heading and button text on a panel (purple on near-black) | 3.62 | 4.5 |
| Extend shell focus outline | 2.57 | 3.0 |

These are findings, not rules. Fixing them is a consumer change that waits for the colors to be decided (D-1, D-5).

## Keyboard patterns

Sourced rows come from the App's conventions and P-072; the arrow-key behavior is the W3C WAI-ARIA Authoring Practices pattern
for each widget (external).

| Pattern | Keys | Source |
|---|---|---|
| Button | Enter or Space activates | **Sourced** (App) |
| Link | Enter | HTML semantics |
| Dialog | Tab cycles inside the dialog; Escape closes; focus returns to the trigger | **Sourced** (App: trap and restore), APG |
| Tabs | Left and Right move between tabs; Tab moves into the panel | APG; the App's `tabs` primitive |
| Menu or dropdown | Arrow keys move; Escape closes and returns focus | APG |
| Toggle button | Enter or Space; `aria-pressed` exposes state | **Verified** in Creator Extend and the Extend shell |
| Current navigation item | Tab to reach; `aria-current="page"` exposes it | **Verified** in the Extend shell |
| Disclosure group | Enter or Space on the `summary` | **Verified** (Extend shell `details`) |
| Workspace switching | keyboard-accessible, with predictable focus and screen-reader labels | **Sourced** (P-072 §8) |

## Focus management

- **Verified** — Focus indicators in this repository's desktop pages are three different colors and two widths: Creator Extend's
  inputs `2px #c6adff`, the shared setup panel `2px #c6b2f2`, the Extend shell `3px #c69045` with a 3px offset. Stream Extend's
  own files declare none and rely on the browser default. No desktop page removes the outline.
- **Verified** — MyFeed draws `2px solid var(--primary)` on buttons and links. The shadcn consumers draw a ring from `--ring`.
- **Proposed** — One token, `focus.ring`, a 2px indicator with an offset, at 3:1 or better against the surface it sits on.
  Removing the browser outline is acceptable only where a visible replacement exists.
- **Sourced** — A modal traps focus while open and restores focus to its trigger when it closes (App). The primitive does this.
- **Proposed** — When a view changes, focus goes to the view's heading; after a failed submit, to the first invalid field;
  sticky headers never cover the focused element (2.4.11).

## Motion

- **Verified** — Only MyFeed honors `prefers-reduced-motion` (a global switch-off of animation and transition). The Blog, the App
  and the three desktop pages do not.
- **Proposed** — Honor `prefers-reduced-motion` everywhere; it is not a WCAG AA requirement (2.3.3 is AAA), it is good practice.
- **Proposed** — Overlays and stream effects never flash more than three times per second (2.3.1). This matters more here than
  in a typical app because overlays sit on live video.

## Live regions and forms

- **Verified** — The desktop pages use inline `role="alert"` text (15 lines) and `aria-live="polite"` (2), plus `role="status"`
  for loading text.
- **Sourced** — Every input has an associated label; placeholder text is never the only label; dynamic content that appears
  without a page load goes in an `aria-live` region; images have descriptive `alt` text, and decorative images use `alt=""`
  (App).

## Testing

- **Verified** — OpenTechnologyApp and OpenTechnologyBlog run the Storybook accessibility addon. The desktop apps and MyFeed have
  no automated accessibility tooling.
- **Verified** — This hub tests contrast numerically (`tests/design_system/`). It does not test anything it cannot compute.
- **Sourced** — A design change is checked in light and dark and at mobile width, and the changed controls are walked with the
  keyboard (`OpenTechnologyApp:.claude/skills/design/SKILL.md` § Verify a design change).
- **Blocked** — No record exists of a screen-reader pass on any consumer.

## Known gaps

- **Captions.** Live captions and transcription are deferred in `docs/architecture/future.md`, with the trigger "an accessibility
  ask from a viewer, or an auto-clipper that needs a transcript." Published streams and videos have no caption policy in this repo.
- **Tabs semantics.** Creator Extend switches views with `aria-pressed` buttons rather than the tabs pattern.
- **No shared focus style** in the desktop pages (see above).
- **Contrast.** The failures above.
