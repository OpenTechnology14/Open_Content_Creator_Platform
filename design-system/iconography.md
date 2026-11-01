# Iconography

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory.** Labels (Verified, Sourced, Proposed, Blocked) are defined in the
> [README](README.md#evidence-labels).

## What exists (Verified, 2026-10-21)

| Consumer | Icons | Library and version |
|---|---|---|
| OpenTechnologyApp | 130 distinct icons imported | `lucide-react` ^0.577.0 |
| OpenTechnologyBlog | 21 | `lucide-react` ^0.576.0 |
| MyFeed | 39 | `lucide-react` ^0.577.0 |
| Stream Extend, Creator Extend, Extend shell | none: no icon library and no inline SVG; text glyphs (`✓`, `!`) and an emoji appear in the page markup | — |
| Job Hunter admin | none found: the page has no `<svg`; icon use is not otherwise surveyed | — |

Counts are from a one-off scan of the import lines on 2026-10-21 and are approximate; re-run before relying on them.

**There is no shared size scale.** The App sets sizes with numeric `size` props, mostly 10 to 16 (12, 13 and 11 are the most
common); the Blog uses Tailwind height classes, mostly `h-4` (16px); MyFeed uses numeric sizes from 13 to 19. Stroke is the
library default of 2 almost everywhere; the App sets 2.5 on a minority of icons. The library's own defaults, read from the
installed package, are a 24×24 grid, `strokeWidth` 2 and round line caps.

## Where icons live

| Asset | Location | Notes |
|---|---|---|
| Platform logo | `docs/assets/logo.svg` | 60×60 viewBox; declared canonical in `modules/social-management/catalog.yaml` and used by the root README |
| Brand marks served by the apps | `modules/social-management/assets/brands/` | four fixed marks (hybrid platform, Stream Extend, Creator Extend, OpenTechApp), compiled into both desktop apps |
| Desktop app icons | `apps/<app>/src-tauri/icons/` and `apps/<app>/icon-source.png` | **Placeholders.** The 1024×1024 sources come from `scripts/setup/generate_placeholder_icons.py`: a flat product-color square with the product's first letter, which its own docstring calls "not real branding" and says exists to unblock `tauri icon` (the full set is generated from a 1024×1024 source). `catalog.yaml` still labels these PNGs canonical. Real brand assets: **Blocked (D-7)** |
| UI icons in web consumers | imported from `lucide-react` inline | no icon files are committed |
| Channel art | produced by hand per account | specs below |

Channel-art specs (Sourced, `docs/guides/production-setup/STREAM_EXTEND_PRODUCTION_SETUP.md` §3.6): profile picture 256×256 PNG,
square; banner 1200×480 (Twitch) or 2560×1440 with a 1546×423 safe area (YouTube); panels 320×100; watermark 150×150 transparent.
**The 32-pixel rule:** a profile picture is seen at 32px far more often than full size, so shrink it to 32px and look; a face or
one bold glyph survives, a detailed scene does not. A thumbnail gets the same test at 200px wide. One palette and one typeface
across every artifact of an account.

## Rules

**Set and stroke**
- **Verified** — All three web consumers use one library, Lucide. **Proposed** — it is the hub's UI icon set for web surfaces.
- **Proposed** — Use the library's default stroke (2) so icons keep their weight relative to text. A deliberate local override
  (the App's 2.5) is recorded in that consumer's pointer doc. Do not mix strokes within one view.
- **Blocked (D-7)** — Whether the desktop apps adopt the set or keep text glyphs.

**Size scale (Proposed, awaiting owner review)**
- 16px for inline and control icons (the one size all three web consumers use, and the Blog's button primitive sizes its child
  icons to 16px by default), 20px for prominent controls, 24px (the library's native grid) for standalone and empty-state icons. Sizes that are not on the scale are a finding, not a style.
- The App's 10 to 14px icons are a divergence to resolve under D-7, not a precedent.
- An icon-only control still has a hit target of at least 24×24 CSS px (WCAG 2.5.8) and 44px on touch surfaces, as the App's rail
  uses (`OpenTechnologyApp:docs/proposals/PROPOSAL_UI_REDESIGN_HAMBURGER_AND_VIEW_TOGGLE.md`).

**Metaphors (Verified in the App's rail; the rule is Proposed)**
- One meaning per glyph across the ecosystem: Home, Menu, Search, Settings, Theme, Language, Support, Notifications, Chatbot,
  Sign out, and "…" (more) for overflow. The App's rail is the only place these are documented.
- A destructive terminal action (Sign out) is last, and confirms inline.
- **Sourced** — Never convey meaning by color alone: pair color with an icon or text (`OpenTechnologyApp:CLAUDE.md` §
  Accessibility conventions). An icon that carries meaning is not decoration.

**Accessibility**
- **Sourced** — Every interactive element has an accessible name. An icon-only button needs an `aria-label` or visually hidden
  text. **Proposed** — A decorative icon is hidden from assistive technology (`aria-hidden`).
- **Proposed** — Do not use emoji as icons: they render differently per operating system and cannot be recolored. (Verified:
  one emoji appears as an icon in a Creator Extend panel today.)

## Licensing

- **Verified** — `lucide-react` is licensed ISC, with portions MIT from Feather (read from the installed package's LICENSE file,
  versions 0.576.0 and 0.577.0).
- **Verified** — The repository's root `LICENSE` is MIT (added by P-075, `docs/THIRD_PARTY_PROVENANCE.md`; the owner confirms
  it at `OSS-D01`) and covers the repository's own code. Whether it also states the hub's license is part of D-9. None of the
  three web consumers declares a `license` field in `package.json`; Job Hunter is MIT.
- **Blocked (D-9)** — No repository records the license of any font family used (Space Grotesk, JetBrains Mono, DM Sans, Inter).
  Confirm each at its source and record it with the third-party notices before any public release.
- **Blocked (D-9)** — The brand marks were authored in this repository, generated as placeholders, or copied from the owner
  workspace (per `modules/social-management/catalog.yaml` and the generator above). No file states a license for them.
- **Proposed** — A new icon source needs: a license that permits redistribution inside a desktop installer; an entry in the
  third-party notices; and a decision recorded in a design proposal. Icons generated by an image model are not used without an
  owner decision, because their rights are not established (the same position the repository takes on training corpora).
