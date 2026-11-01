# Open Content Creator Platform — Marketing Playbook

A go-to-market plan for the two desktop products this repository builds — **Stream Extend** and
**Creator Extend** — and for the Nova-hosted marketing shows that present them. It keeps the section
numbering of [OpenTechnologyApp's MARKETING.md](https://github.com/OpenTechnology14/OpenTechnologyApp/blob/main/MARKETING.md),
so "§3a" or "§4" in the crosswalk's [asset catalogue](modules/marketing-crosswalk/crosswalk/assets.yml)
means the same step in both, but the audiences, claims and evidence are this repository's own.

> **North-star:** reach the people who already juggle a dozen free tools — OBS plugins, ComfyUI,
> Blender, Krita — and want one local-first control surface. Lead with the problem they have, and let
> every claim stand on what this repository can evidence. Never promise ahead of `status`.

> **How this file is wired — it is a crosswalk artifact, not a floating document.**
> - [`targets.yml`](modules/marketing-crosswalk/crosswalk/targets.yml) registers it as the
>   `marketing_playbook` doc of the `hybrid-creator-platform` target, so
>   `python3 -m generator.cli validate` fails if a heading below is renamed.
> - The `stream-extend` and `content-extend` rows in
>   [`modules.yml`](modules/marketing-crosswalk/crosswalk/modules.yml) list it as `files.marketing_doc`.
> - Every numbered section opens with a **Registry:** line naming the registered modules it depends on.
> - [`test_playbook.py`](tests/marketing_crosswalk/test_playbook.py) checks those lines, §1's shipped
>   list, §2's ICP tables, §3g's persona chain and §4's engine order against the YAML and configs.
>
> The registry stays the source of truth. Where a table below repeats registry data, the registry wins
> and this file is the one to fix — the test is what makes the duplication safe.

**Status rule (applies to every section).** Claims follow `status`, not ambition. The
[README](README.md) is explicit that local-first is the design target, that implementation and
operating-system acceptance are incomplete, and that paid remote features are product plans.
[`docs/AUDIT.md`](docs/AUDIT.md) is the repository's verdict on what is real. A `scaffolded` subject can
only be given roadmap-level copy; assets that assert "it works today" are blocked for it by the
generator (§4).

---

## 1. Positioning

**Registry:** `stream-extend` · `content-extend` — identity in
[`products.yml`](modules/marketing-crosswalk/crosswalk/products.yml); rows in
[`modules.yml`](modules/marketing-crosswalk/crosswalk/modules.yml).

**Taglines and one-liners** (transcribed from `products.yml` — change them there first):

| Product | Tagline | One-liner |
|---|---|---|
| Stream Extend | One dashboard for OBS, AI effects, overlays, and agents | Wraps OBS, realtime AI effects, broadcast graphics, audio routing, and AI agents into one dashboard you can drive from any device — without a subscription for local features. |
| Creator Extend | One pipeline for ComfyUI, Blender, Krita, and your own photo library | Wraps ComfyUI, Blender, Krita, sports CV, and generation trained on your own photographs into one pipeline — running on your GPU, with no subscription for local features. |

**The wedge (why someone switches):**

- *Stream Extend* — one dashboard instead of a plugin per capability; everything works locally with no
  subscription, and cloud adds only remote access, push, sync and multi-user.
- *Creator Extend* — one pipeline instead of four apps that do not talk to each other; trained on your
  photographs, on your GPU, so the corpus never leaves the workstation.
- *Hold the price line.* `products.yml` also carries "$20 one-time" as a third wedge for each product,
  but pricing, purchases and naming remain release decisions
  ([product-spec](docs/architecture/product-spec.md)). Do not publish a price.

**What you may claim today — and nothing more.**
**Shipped subjects (checked by tests):** `asset-pipeline`, `model-registry`, `storage-data`.
Every other subject in both rows is `scaffolded`: describe it as planned or in setup, never as working.
Run `python3 -m generator.cli coverage --module stream-extend` (or `content-extend`) from
`modules/marketing-crosswalk` to see exactly which assets are blocked.

**Naming is unsettled.** Every marketing surface and `products.yml` say *Creator Extend*;
[`REPOSITORY_ALIGNMENT.md`](docs/REPOSITORY_ALIGNMENT.md) names the product *ContentExtend* and requires an
approved proposal to rename. The generator stamps guide and comparison pages for it "Do not publish under
either name". Treat all external Creator Extend copy as draft until that resolves.

**Competitors** (comparison-table rows stay `_TODO: verify_` until checked): Stream Extend — Streamlabs,
StreamElements, OBS alone, vMix, NVIDIA Broadcast. Creator Extend — Adobe Creative Cloud, Photoshop
Generative Fill, Firefly, Topaz, manual export/import.

---

## 2. Who to target (ICPs, in priority order)

**Registry:** `stream-extend` ([subjects](modules/marketing-crosswalk/crosswalk/subjects/stream-extend.yml),
`icps:`) · `content-extend` ([subjects](modules/marketing-crosswalk/crosswalk/subjects/content-extend.yml),
`icps:`). These are *not* OpenTechnologyApp's agencies and MSPs: they describe who buys a streaming
dashboard and a local content pipeline.

**Stream Extend**

| # | ICP | Who | Why they switch | Where they hang out |
|---|---|---|---|---|
| 1 | `live-streamer` | Twitch / YouTube streamers running OBS solo | A different plugin per effect, each with its own install and GPU quirks, and no shared control surface | r/Twitch, r/streaming, r/obs, X streaming community |
| 2 | `esports-broadcast` | Small esports / league broadcast operators | Scoreboards and lower-thirds are hand-built per event; nothing is reusable and nothing is driven from live data | r/esports, r/nodecg, Discord broadcast servers |
| 3 | `vtuber` | VTubers and PNGTubers | Avatar tooling is Windows-only and disconnected from the scene switcher and agent that should drive it | r/VirtualYoutubers, r/PNGTubers, X VTuber community |
| 4 | `technical-creator` | Self-hosting / homelab creators who run their own stack | They already run Docker and want the creator stack observable and automatable, not a black box | r/selfhosted, r/homelab, r/devops, Hacker News |

**Creator Extend**

| # | ICP | Who | Why they switch | Where they hang out |
|---|---|---|---|---|
| 1 | `content-creator` | YouTube / shorts creators with a render pipeline | ComfyUI, Blender, and Krita each run in isolation; moving an asset between them is manual every single time | r/NewTubers, r/comfyui, r/StableDiffusion, r/blender |
| 2 | `photographer` | Photographers with a library they want to look consistent | A per-image edit does not scale, and cloud AI tools want the library uploaded before they will touch it | r/photography, r/postprocessing, r/AskPhotography |
| 3 | `technical-creator` | Self-hosting creators who run their own stack | They already run Docker and want the creative stack observable and automatable, not a black box | r/selfhosted, r/homelab, Hacker News |
| 4 | `sports-coach` | Golf / sports coaches and small athletic programs | Shot tracing and swing analysis are locked behind $2k+ hardware or per-athlete SaaS | r/golf, r/golfsimulator, coaching forums |

Pick **one ICP per product per month** and write for that person; the rank-1 rows are the default.
A streamer and a photographer need different words, and `technical-creator` is reached from both products.

---

## 3. Channel playbook

**Registry:** `stream-extend` · `content-extend` — channel labels live in each subjects file's
`channels:` block; each subject lists the channels it may use.

The channel *machine* — answer first and link second, saved searches and alerts, build-in-public,
comparison pages, one-time sends — is shared with OpenTechnologyApp's playbook. The audiences are not,
so subreddits, examples and claims below are this repository's own.

### 3a. Reddit — value-first, 9:1 rule

**Registry:** `stream-extend` · `content-extend` (channel key `reddit`)

- **Where:** §2's "Where they hang out" column is the subreddit list. Read each sub's self-promotion
  rules first.
- **Alerts:** set up F5Bot (free) from the `keywords:` of the subjects you are about to discuss — the
  first keyword is primary (for example `obs scene collection template` for `creator-experience`). When
  one fires, answer the question first; mention the project last, and only if it helps.
- **Rule:** nine helpful replies for every one mention. No drive-by link drops, no copy-pasted comments,
  never the same link in several subs in a day, and say you build it.
- **Draft with the crosswalk:** `comment-ammo` and `blog-brief` are roadmap-level and available for every
  subject. `reddit-post` asserts that the subject works today, so it is blocked until the subject is
  `shipped` (§4).

### 3b. X — saved searches + build-in-public

**Registry:** `stream-extend` · `content-extend` (channel key `x_twitter`)

- **Saved searches** for the communities in §2 and the subjects' `keywords:`; reply with a tip first and a
  soft mention second, same rule as Reddit.
- **Build-in-public:** this project builds in the open — the showcase streams (§3g), the proposal queue and
  the audit supply honest material. Post what shipped, what is still `scaffolded`, and what a run proved.
  Clips come from Creator Extend, as in the [AI Learning Series stream format](docs/learning/README.md).
- **Draft with the crosswalk:** `x-thread` (roadmap-level).

### 3c. LinkedIn — business-value angle

**Registry:** `stream-extend` · `content-extend` (channel key `linkedin`)

- The business-value angle suits the operator-facing audiences (`esports-broadcast`, `technical-creator`)
  more than solo streamers or photographers. Only subjects that list `linkedin` in their `channels:` get a
  post — `coverage` shows which.
- `linkedin-post` asserts that the subject works today, so it follows the same `shipped` gate as
  `reddit-post` (§4).

### 3d. SEO guide and comparison pages — setup docs as content

**Registry:** `stream-extend` · `content-extend` (channel key `seo`; planned pages in each subject's
`coverage:`)

- **Guides as content.** Each module's `setup/` docs double as website copy —
  [product-spec](docs/architecture/product-spec.md) § "Marketing: Guides as Content" holds the planned URL
  table (streamextend.com and creatorextend.com guides). The table is a plan: this file does not assert
  that any page is live. The local [documentation website](docs/public/index.html) is source, not a
  deployed service.
- **Comparison pages** use the competitor lists in §1 and an honest table. `comparison-page` is
  `shipped`-gated, and Creator Extend pages also wait on the naming decision.
- **Gaps are visible.** A module with no planned page is a `false` cell in its subject's `coverage:` —
  `coverage` reports it as a gap rather than hiding it.

### 3e. Directories & launches — gated, nothing submitted

**Registry:** `stream-extend` · `content-extend`

No directory or launch submission has been made from this repository, and none is claimed. Preconditions
that are documented as open:

| Precondition | Where it is recorded |
|---|---|
| Product name (Creator Extend vs ContentExtend) | [`REPOSITORY_ALIGNMENT.md`](docs/REPOSITORY_ALIGNMENT.md) |
| Root license (not selected or issued) | [README § Source code](README.md#source-code), [release checklist](docs/OPEN_SOURCE_RELEASE_CHECKLIST.md) |
| Pricing and purchase flow | [product-spec](docs/architecture/product-spec.md); purchase routes return 501 ([GAP_AUDIT](docs/GAP_AUDIT.md)) |
| Clean-machine install proof | [product-spec](docs/architecture/product-spec.md) § first launch and assisted setup |

There is deliberately no directory-listing asset in [`assets.yml`](modules/marketing-crosswalk/crosswalk/assets.yml)
and no paste-ready listing copy here. When the preconditions clear, start from the `products.yml` tagline and
one-liner and build a tracker like OpenTechnologyApp's — without copying its rows.

### 3f. Direct email — no list exists here

**Registry:** `stream-extend` · `content-extend`

Nothing in this repository sends email and no email list for these products exists. The crosswalk has a
`lead-email-angle` asset, but it is declared for neither product module. Any send is an owner decision; if
one is made, follow OpenTechnologyApp's one-send-no-drip policy.

### 3g. Live streams — Nova marketing shows

**Registry:** `stream-extend` · `content-extend` (and `ai-learning` for the series; every registered module
has its own chain in the [personality map](docs/architecture/stream-personality-audio-routing.md))

This channel is specific to this repository. One on-air identity, **Nova**, presents each module through a
persona, a show profile and a scripted audio policy:

| Registry module | Show profile | Nova persona | Show | Audio policy |
|---|---|---|---|---|
| `stream-extend` | `marketing-stream-extend` | `nova-stream-extend` | `stream-extend-showcase` | `opentech-scripted` |
| `content-extend` | `marketing-content-extend` | `nova-content-extend` | `content-extend-workflow` | `opentech-scripted` |

- **Scripts are outlines for human completion** (`stream-script`): a draft opening, source evidence and
  explicit TODOs. They are not approved narration and start nothing.
- **Nothing runs on its own.** Both profiles keep uploads disabled and approval required; scripted personas
  use AI-VOICE only and the Soundboard is for gaming-reactive personalities.
- Build-in-public material (§3b) and clips for the other channels come out of these shows.

---

## 4. Content engine (make one thing become five)

**Registry:** `stream-extend` · `content-extend` (assets are declared per subject; catalogue in
[`assets.yml`](modules/marketing-crosswalk/crosswalk/assets.yml)); the generator is the
[`marketing-crosswalk`](modules/marketing-crosswalk/README.md) module.

**Engine order:** `blog-brief` → `reddit-post` → `x-thread` → `linkedin-post` → `comment-ammo`

| Step | Asset | Claim level | Channel | What it is |
|---|---|---|---|---|
| 1 | `blog-brief` | roadmap | §3d | Outline and target keywords for the post that feeds the other four |
| 2 | `reddit-post` | shipped | §3a | "Show & tell" post, value-first, 9:1 |
| 3 | `x-thread` | roadmap | §3b | Key points plus a screenshot, or a build-in-public thread |
| 4 | `linkedin-post` | shipped | §3c | The business-value angle |
| 5 | `comment-ammo` | roadmap | §3a | The alert reply that answers first and links second |

Beyond the five: `guide-page` (§3d), `comparison-page` (§3d), `stream-script` (§3g), `walkthrough-brief`
and `matrix-row`. Claim levels follow the subject: *roadmap* assets are safe at any status, *shipped*
assets need `status: shipped` and show as `BLOCKED` in `coverage` otherwise.

```bash
cd modules/marketing-crosswalk
python3 -m generator.cli validate                      # anchors and status claims still hold
python3 -m generator.cli coverage --module stream-extend
python3 -m generator.cli generate --module stream-extend --subject creator-experience --asset blog-brief --dry-run
python3 -m generator.cli generate --module stream-extend --subject creator-experience --asset blog-brief
```

Drafts land in `modules/marketing-crosswalk/out/`. `--apply` writes into this target's draft directory
instead and never edits a hand-written doc in place: a human moves a reviewed draft into the README or
product-spec. A draft is not approved copy.

---

## 5. Realistic weekly cadence

**Registry:** `stream-extend` · `content-extend` · `ai-learning` (the one series with its own stream format)

The owner sets the time budget; this section only orders the work. The machine steps (`validate`,
`coverage`, `generate`) take minutes — the real cost is review and approval.

- **Daily:** check F5Bot alerts (§3a); answer one to three threads, value first.
- **Two or three times a week:** one X reply-with-value and one build-in-public post (§3b), sourced from
  what the last stream or run actually proved.
- **Weekly:** run `validate` and `coverage` for both product modules and clear any drift before
  generating. Complete and approve the next `stream-script` for the week's marketing show (§3g).
- **Every one to two weeks:** one guide or blog page (§3d), then repurpose it through the engine (§4).
- **When a module's row in `CLAUDE.md` §11 changes status:** update the subject's `status` and
  `status_evidence` together; blocked assets unblock by themselves.
- **Broadcast slots** come from [`configs/local/stream-programming.yaml`](configs/local/stream-programming.yaml).
  Marketing shows are rotation entries (`stream-extend-showcase`, `content-extend-workflow`, and
  `ai-learning-lesson` for the series), not flagship nights.

---

## 6. Funnel & metrics (track what can actually be measured)

**Registry:** `stream-extend` · `content-extend` · `ai-learning`

Be exact about what is instrumented. As of 2026-10-20 **none of the funnel is**: there is no signup or
download tracking in this repository, this file does not assert that any site is live, and the paid tiers
cannot be bought — the relay's purchase and subscription routes return `501` ([GAP_AUDIT](docs/GAP_AUDIT.md)).
A conversion number would be invented. What can be measured, in the order to watch it:

1. **Claim coverage** — `coverage --module <name>`: how many assets for the rank-1 ICP's subjects are
   unblocked versus `BLOCKED`. A rising unblocked count means statuses are being earned, not argued.
2. **Registry freshness** — `validate` green, and the age of each row's `last_verified`. A stale row is a
   claim nobody re-read.
3. **Activation, once there is something to install** — [product-spec](docs/architecture/product-spec.md)
   defines it: time and user actions to the first usable window, measured separately from the first
   verified broadcast or content output. A source build or CI rehearsal does not prove clean-machine
   installation.
4. **Lessons aired** — the `ai-learning` row counts `lessons_aired`; today it is 0.

Attribution (`?ref=` links, "where did you hear about us") is an owner decision that waits for a live
landing page and a purchase flow. Do not build tracking for a funnel that cannot convert yet.

---

## 7. First 30 days (do these in order)

**Registry:** `stream-extend` · `content-extend` · `ai-learning`

Items marked *(owner)* need a decision or an account only a person can provide.

1. [ ] Run `validate`, then `coverage` for both product modules; keep the blocked-claims list as the
   month's baseline.
2. [ ] *(owner)* Decide the Creator Extend / ContentExtend name. Until then every Creator Extend guide or
   comparison draft is stamped do-not-publish (§1).
3. [ ] *(owner)* Settle the license and the pricing and purchase questions before any listing (§3e).
4. [ ] Pick **one ICP per product** for the month — rank 1 in §2 (`live-streamer`, `content-creator`)
   unless the owner redirects.
5. [ ] Generate roadmap-level drafts (`blog-brief`, `comment-ammo`, `x-thread`, `walkthrough-brief`) for a
   subject that serves each ICP and has a planned guide page: `creator-experience` for Stream,
   `content-creation` for Creator.
6. [ ] Complete and approve one `stream-script` per product before its showcase show (§3g); confirm uploads
   stay disabled.
7. [ ] *(owner)* Create the F5Bot account and alerts from the chosen subjects' `keywords:` (§3a).
8. [ ] Answer one to three alert threads a day, value first, all month.
9. [ ] Publish nothing that says `shipped` for a `scaffolded` subject. When evidence changes, update
   `status` and `status_evidence` together and re-run `validate`.
10. [ ] Review §6's measurable items; keep what moved the unblocked count and drop what did not.

---

## 8. Mistakes to avoid

**Registry:** `stream-extend` · `content-extend`

- **Claiming ahead of status.** `scaffolded` means the directory, README and config exist — not that it
  works. Roadmap-level copy only (§4).
- **Presenting plans as products.** One-click setup, mobile control and the paid tiers are plans or
  targets in the README; the purchase routes return 501 today.
- **Talking to every ICP at once.** One per product per month.
- **Mixing audiences.** Stream Extend's ICPs are not Creator Extend's, and neither is OpenTechnologyApp's
  agencies and MSPs.
- **Publishing under an unresolved name** (§1).
- **Reaction clips on scripted shows.** Scripted personas are AI-VOICE only (§3g).
- **Launching to no one.** No directory or launch (§3e) before the preconditions clear and a few people are
  lined up to try it on a clean machine.
- **Letting this file float.** If a table here disagrees with the YAML, the YAML wins and this file is wrong;
  run `pytest tests/marketing_crosswalk/test_playbook.py` after any registry change.
- **Treating counts as evidence.** Registry `counts` are hand-transcribed navigation aids
  ([schema](modules/marketing-crosswalk/crosswalk/schema.md)); a public claim needs a subject's
  `status_evidence`.

---

*Last verified 2026-10-20 against the `stream-extend` and `content-extend` rows and subjects files,
`products.yml`, `assets.yml` and `configs/local/stream-programming.yaml`. OpenTechnologyApp's playbook is
the skeleton reference, not a source of claims about this platform.*
