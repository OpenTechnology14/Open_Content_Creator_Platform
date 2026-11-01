# Design system hub

> **Status:** drafted — awaiting owner review · **Last reviewed:** 2026-10-21 · **Owner:** OpenTechnology14
> **Enforcement: advisory until approved.** Nothing in this folder is owner-approved. Read the
> [adoption rule](#adoption-rule) before acting on any value.

The ecosystem's design-system hub. This repository (`hybrid-creator-platform`) is the hub; every other
repository keeps a **pointer doc** plus its own local overrides, never a copy. It is the same pattern the
[marketing crosswalk](../modules/marketing-crosswalk/README.md) uses for module discovery, for the same
reason: two copies of a source of truth drift.

Provenance of the layout: the owner chose this repository as the hub (Option B plus an add-on from the design-system
options, relayed 2026-10-21). The options document itself was not available to the agent that built this folder, so
the layout follows the deliverable list in the request and the pointer docs downstream sessions had already written:
`OpenTechnologyBlog:docs/design/DESIGN-SYSTEM-POINTER.md` (merged in the Blog on 2026-10-21) and a draft in Ironfall.

## What is here

| File | Holds |
|---|---|
| [`tokens.yaml`](tokens.yaml) | Machine-readable tokens: color, type, space, radius, shadow, motion. Each token has a hub default and the **verbatim value every consumer uses today**, plus computed contrast results and the open decisions |
| [`components.md`](components.md) | The component spec layer: buttons, cards, modals, forms, badges, navigation, feedback, overlays. Usage rules and anti-patterns; no implementation code |
| [`voice-and-tone.md`](voice-and-tone.md) | Per-profile voice, encoded as **registers**, never as the names of real people |
| [`iconography.md`](iconography.md) | Icon-set rules, where icons live, licensing |
| [`accessibility.md`](accessibility.md) | The WCAG AA baseline, contrast rules, keyboard patterns, focus management |
| [`crosswalk/consumers.md`](crosswalk/consumers.md) | The downstream repositories and the pointer-doc path each is expected to keep |
| [`proposals/TEMPLATE.md`](proposals/TEMPLATE.md) | The template for design artifacts (mockup, data flow, interaction notes, open questions, decision gates) |

## Evidence labels

Every statement in this folder carries one of three labels, so a reader can tell what exists from what is wanted.
They extend the repository's evidence vocabulary ([`docs/PROPOSAL_CREATION_SOP.md`](../docs/PROPOSAL_CREATION_SOP.md)).

| Label | Meaning |
|---|---|
| **Verified** | Observed verbatim in a named source (file and revision), or computed from observed values. Tests re-read in-repo sources on every run |
| **Sourced** | A rule an existing ecosystem document already states, cited. The citation is the evidence; adopting it as a hub rule is still a draft |
| **Proposed** | The hub's draft. No source or owner approval stands behind it |
| **Blocked** | Cannot be filled in without an owner decision ([`tokens.yaml`](tokens.yaml) `decisions`, D-1 to D-9) |

A token's `status` is `drafted` (everything today), `approved` (set only by the owner, with `approved_by` and
`approved_on`) or `deprecated`.

## Adoption rule

**A consumer implements a token or rule only once it is `approved`.** `drafted` content documents what exists and what
the hub proposes. It is not an instruction: no consumer should change its implemented values because of this folder,
and no agent should treat a drafted value as a requirement. A pointer doc that says "the hub wins" means *the approved hub*.

## Where the ecosystem stands

All of this is Verified, and the numbers live in [`tokens.yaml`](tokens.yaml), not here:

- **There is no single visual identity yet.** The consumers disagree on `brand.primary`: three web consumers use three
  different blues, the platform's canonical logo and both desktop apps use orange and purple on near-black, the Extend
  shell preview uses green, and Job Hunter's admin has its own blue. Typefaces disagree too.
- **Only some consumers have tokens.** The App, Blog and MyFeed define CSS custom properties with light and dark
  values; the App and Blog share shadcn's variable names. The three desktop pages define none and hard-code hex values.
- **One name means two things.** shadcn's `--accent` is a brand teal in the Blog and a subtle highlight tint in the App
  and MyFeed. The hub separates the roles (`brand.accent`, `surface.highlight`).
- **The proposed set does not pass WCAG AA everywhere.** Several pairings fall short, including white text on the
  proposed primary. They are computed and listed rather than quietly adjusted; see [`accessibility.md`](accessibility.md).

## Owner decisions

The authoritative text is `decisions` in [`tokens.yaml`](tokens.yaml); a test keeps the IDs below in sync with it.

| ID | Question |
|---|---|
| D-1 | Which palette is the ecosystem's brand? **Question:** Use the Blog's palette as the ecosystem brand, as the hub proposes? |
| D-2 | Do the desktop apps converge on hub tokens, or keep per-product accents? **Question:** Move the desktop apps onto the hub's tokens, or let each keep its own accent? |
| D-3 | One typeface for the ecosystem, or one per surface? **Question:** Use one typeface across the whole ecosystem rather than one per surface? |
| D-4 | Which success, warning and info colors does the ecosystem use? **Question:** Define one set of success, warning and info colors in the hub for every product to use? |
| D-5 | The proposed set fails WCAG AA in several pairings: adjust values or accept exceptions? **Question:** Adjust the failing colors to pass WCAG AA, or accept them as documented exceptions? |
| D-6 | Is the baseline WCAG 2.2 AA or 2.1 AA? **Question:** Set the accessibility baseline at WCAG 2.2 AA rather than 2.1 AA? |
| D-7 | Do the desktop apps adopt an icon set, and what is the size scale? **Question:** Should the desktop apps adopt a shared icon set and size scale? |
| D-8 | Which tokens apply to engine UI (Ironfall, AnimalHouse)? **Question:** Apply the hub's typography and color tokens to the game engines' UI, leaving their world art alone? |
| D-9 | What are the hub's and the fonts' licenses? **Question:** Will the hub follow the repository's MIT license, and will you record each font's license? |

How the hub's defaults were chosen: a **Proposed** default in `tokens.yaml` is the OpenTechnologyBlog value (or a Tailwind
default the Blog inherits and does not override) wherever the Blog defines the role, because the Blog is the only consumer with a
complete, documented semantic set (both themes, a brand accent, shadows, radius and motion) and its pointer doc already names it
the interim reference. Where the Blog has no value the default is `null` and names the blocking decision. The exception is the two
product accents, which are verified identical in the platform logo and the desktop apps. That is a selection rule, stated so it
can be reversed, not a judgment that the Blog's look is right. Answer D-1 and the defaults are re-derived from the chosen source.

## Policy: add a token, or reuse one (Proposed)

**Reuse when**

- an existing role already fits: a card background is `surface.raised`, not a new "card-bg";
- the difference is a **state** (hover, active, disabled, selected): derive it by rule in the component spec, and mint a
  token only if the derivation cannot meet contrast;
- the value differs only per consumer: record it as a local override in that consumer's pointer doc, not as a hub token;
- it is data-visualization color. The App's rule is hex literals only for data visualization, and theme variables
  everywhere else (`OpenTechnologyApp:CLAUDE.md` § shadcn/ui conventions).

**Add when all of these hold**

1. The **role recurs**: two consumers need it, or one does and no existing token can express it.
2. It is a **role, not a value**: `category.role[.variant]`, lowercase, dots between levels and hyphens within one
   (`surface.raised`, `brand.primary-contrast`). Never a value name such as `blue-500`.
3. It has **light and dark** values, or states why it has one.
4. Every foreground/background pairing it enters is added to `contrast.pairs` and passes, or is recorded in
   `contrast.known_failures` with a decision.
5. It records `observed` values for every consumer that already has an equivalent, and `maps_to` where a shadcn
   variable exists, so convergence is mechanical.
6. It lands as a pull request (with a design proposal if it changes how more than one consumer looks), as `drafted`.

## Policy: deprecation (Proposed)

Nothing is approved yet, so nothing can be deprecated; the policy starts with the first approval.

- Never change what an approved token **means**. Add a new token and deprecate the old one.
- Deprecating sets `status: deprecated` with `replaced_by`, `deprecated_on` and `remove_not_before`; the value stays.
- A deprecated token is removed only after every consumer's pointer doc records that it no longer uses it
  ([`crosswalk/consumers.md`](crosswalk/consumers.md)), and the removal is its own pull request.
- Consumers see a deprecation in their pointer's "Verified against" revision going stale, not as a surprise break.

## Voice and tone

Voice is documented as **registers**: young/energetic/expressive (Games), young/energetic/Latin-accented (Reactions),
deep/warm/measured/narrative (the OpenTechnology family). It is registers, not names: the real people the owner once cited
as inspiration are selection references only and never appear in a prompt, a voice name, a config comment, marketing copy
or this folder (`docs/proposals/PROPOSAL_AI_WALKTHROUGH_MASCOT_SYSTEM.md` §7.3). See
[`voice-and-tone.md`](voice-and-tone.md).

## Design proposals: the `proposals/` convention

A design proposal is a **design artifact** — a mockup, a data flow, interaction notes — that needs a review record. It is
not the work queue: authorization still comes from a row in [`docs/PROPOSALS.md`](../docs/PROPOSALS.md), and a design
proposal names the row (or the consumer's local proposal) it supports.

- Write one when a change adds, changes or deprecates a hub token, adds a component pattern, or changes how more than one
  consumer looks. A single-consumer change that touches no hub token needs no hub proposal; it goes in that consumer's own
  `docs/design/proposals/`.
- Copy [`proposals/TEMPLATE.md`](proposals/TEMPLATE.md) to `design-system/proposals/<YYYY-MM-DD>-<short-name>.md`.
- Status runs Draft → Under review → Accepted, Rejected or Superseded. Accepted does not mean approved tokens: token
  approval is recorded in `tokens.yaml`.
- Prefer Mermaid and SVG: both are text, so they diff and review. A raster image is allowed when it is small; nothing over
  5 MB is committed (`CLAUDE.md` §10).
- The Blog and Ironfall each keep a local variant of the template. The hub's is canonical; a local variant may drop sections
  but should not rename them.

## How this folder is checked

`tests/design_system/` fails when: `tokens.yaml` loses a required token or claims approval it does not have; a recorded
value is no longer in its source (in-repo sources every run; sibling repositories when their checkout is supplied through
`OPENTECHAPP_REPO_PATH`, `OTBLOG_REPO_PATH`, `MYFEED_REPO_PATH` or `JOB_HUNTER_REPO_PATH`); a contrast number does not
recompute; a decision ID drifts between the README and `tokens.yaml`; the consumers list and the registry row disagree; or a
real person's name appears in any file here.

The folder is registered in the marketing crosswalk as the `design-system` row (`kind: design-system-hub`) so a session can
find it by name ([`modules/marketing-crosswalk/crosswalk/modules.yml`](../modules/marketing-crosswalk/crosswalk/modules.yml)).
Agent instructions point here from `CLAUDE.md` §15, mirrored into `AGENTS.md`.

## Sources

Revisions are recorded in `sources` in [`tokens.yaml`](tokens.yaml). In summary: `OpenTechnologyBlog` `src/app/globals.css`
and `src/app/layout.tsx`; `OpenTechnologyApp` `src/index.css`, `tailwind.config.js` and `CLAUDE.md`; `MyFeed`
`src/styles.css`; `Job-Hunter` `admin/static/index.html`; this repository's three desktop pages, shared Svelte components,
broadcast overlays and brand marks; the production-setup guides and the Stream Autopilot proposals for voice and accounts.
