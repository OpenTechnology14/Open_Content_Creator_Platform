# Consumers

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-24 · **Owner:** OpenTechnology14
> **Enforcement: advisory.** Labels (Verified, Sourced, Proposed, Blocked) are defined in the
> [README](../README.md#evidence-labels). Pointer states were re-verified on 2026-10-24 against each repository's default branch
> (GitHub API) and AnimalHouse's local folder; re-check before relying on them.

The downstream repositories that mirror this hub. Each keeps a **pointer doc** — the hub is canonical, the consumer keeps a
pointer and its local overrides, and token values are never copied (two copies drift). This is the same pattern as
`MARKETING_CROSSWALK_POINTER.md`. The machine-readable copy of this list is the `consumers` key of the `design-system` row in
[`modules.yml`](../../modules/marketing-crosswalk/crosswalk/modules.yml); a test keeps the two in step.

## The list

| Consumer | Repository (visibility) | Surface and styling source (Verified) | Expected pointer doc | Pointer state |
|---|---|---|---|---|
| OpenTechnologyApp | `OpenTechnology14/OpenTechnologyApp` (private) | web app; shadcn/ui on Tailwind 3; `src/index.css`, `tailwind.config.js` | `OpenTechnologyApp:docs/design/DESIGN-SYSTEM-POINTER.md` | **absent** on main; its `docs/design/` already holds the build-prompting digest |
| OpenTechnologyBlog | `OpenTechnology14/OpenTechnologyBlog` (private) | web; shadcn-style on Tailwind 4; `src/app/globals.css` | `OpenTechnologyBlog:docs/design/DESIGN-SYSTEM-POINTER.md` | **present** (merged 2026-10-21, #65; revised 2026-10-23, #69), written before the hub existed, so its hub-file table says "not found" |
| MyFeed | `OpenTechnology14/MyFeed` (private) | web; React and Vite with plain CSS; `src/styles.css` | `MyFeed:docs/design/DESIGN-SYSTEM-POINTER.md` | **present** (merged 2026-10-22, #13) and **hub-pending**: it says the hub does not exist yet, so every path in it is a forward reference. Its docs sit in `docs/` and `docs/readable/` |
| Job Hunter | `OpenTechnology14/Job-Hunter` (**public**, MIT) | a single admin HTML page with its own custom properties; `admin/static/index.html` | `Job-Hunter:docs/design/DESIGN-SYSTEM-POINTER.md` | **present** (merged 2026-10-23 as #4 in the repository that is now the private archive `job-hunter-archive`; carried into the re-created public repository's first commit `0fd2fca` on 2026-10-27), verified against hub `54266fc`; it states that the repository is public and the hub private |
| Ironfall | `OpenTechnology14/Ironfall` (private) | Unreal Engine 5.8 game; engine UI, no web tokens; world art direction locked | `Ironfall:Docs/design/DESIGN-SYSTEM-POINTER.md` | **present** (merged 2026-10-21, #43), no longer a local draft |
| AnimalHouse | local project; not a git repository, no remote | Unreal Engine 5.8 prototype; engine UI | `AnimalHouse:Docs/design/DESIGN-SYSTEM-POINTER.md` | **present** as an uncommitted local file (written 2026-10-21, "proposed crosswalk; source directory does not yet exist"); AnimalHouse is not a git repository, so nothing is committed or reviewed |
| Gist | `OpenTechnology14/Gist` (private) | mobile-first web app; React 18 and Vite 5; no tokens, no stylesheet: 266 inline `style={{…}}` objects with hex values in `src/GroceryAppV3_Web.jsx`; Space Grotesk loaded from Google Fonts | `Gist:docs/design/DESIGN-SYSTEM-POINTER.md` | **present** (merged 2026-10-23, #1), verified against hub `54266fc`; it records that Gist is not yet in this list, which this row closes. Gist's values are not yet recorded under `observed` in [`tokens.yaml`](../tokens.yaml) |

**In-repo consumers need no pointer**: Stream Extend, Creator Extend, the Extend shell preview, the shared Svelte components and
the NodeCG overlays live in this repository. Their current values are recorded under `observed` in [`tokens.yaml`](../tokens.yaml),
and what they should converge on is decision D-2.

## The convention, and where it came from

The expected path, in every repository, is `<repo>:docs/design/DESIGN-SYSTEM-POINTER.md` (`Docs/design/` in the repos that capitalize it). **Verified on 2026-10-24:** the Blog,
MyFeed, Job Hunter, Ironfall and Gist have that file on their default branches and AnimalHouse has it as a local file; only the App
does not, and it already has a `docs/design/` directory. **Proposed:** the same path everywhere, so a session in any repo finds it without searching. Each
consumer's local design-proposal template, where one exists, sits beside it at `<repo>:docs/design/proposals/TEMPLATE.md`.

Two constraints on the list:
- **Job Hunter is public and this hub is private.** Its pointer may name the hub and state the rule; it must not quote hub
  content, and outside readers cannot open the hub. Until the hub is published, that pointer can only carry local overrides.
- **Ironfall and AnimalHouse have no web tokens to match.** Which hub categories apply to engine UI is decision D-8. Ironfall's draft
  applies typography, menu color and semantic feedback and excludes world art, costume and animation; that draft is a consumer
  proposal, not a hub rule.

## What a pointer doc contains (Verified in the Blog's and Ironfall's merged pointers)

1. A status banner: status, last-reviewed date, and the revision it was **verified against** (hub revision, and the consumer's own).
2. One sentence naming the hub path and stating that the hub is canonical, the pointer holds only local overrides, and **values are not
   copied**. It says the hub wins only when the hub's token is `approved` (the [adoption rule](../README.md#adoption-rule)).
3. **Hub status**: which hub files it relies on and when they were last checked.
4. **Tokens that apply, and tokens that do not**, by category and with the reason. (Ironfall's draft has both tables; the Blog's has
   a local-overrides table.)
5. **Local overrides**: area, behavior, rationale, in a table. An override with no recorded rationale is a finding.
6. **Register**: which of the [three registers](../voice-and-tone.md) the consumer sits in, and any copy that differs.
7. **Proposals**: where the consumer's local design proposals live.

## Keeping it in step

- A hub change that renames a file, token or section a pointer cites is a change to the consumers: update the table above first.
- A pointer is re-verified when the hub revision it cites is no longer current; the stale revision is the signal, not a break.
- Adding a consumer means a row here, an entry under `consumers` in the registry row, and a pointer-doc path. The test fails if
  the two lists disagree.
