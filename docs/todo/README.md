# Owner decisions and runs — lane index

> **Status:** Living · **Last reviewed:** 2026-10-04 · **Owner:** OpenTechnology14

**Enforcement: required for intake, reference for everything else.** One rule binds: a proposal
that opens an owner decision, or a run only a person or hardware can do, adds its row here in the
same change — see [intake](#intake--the-one-required-rule). The rest of this directory is a reading aid.

[`../PROPOSALS.md`](../PROPOSALS.md) owns **state and authorization**. A proposal owns its
**rationale and contract**. This directory owns one thing: **what is waiting on a person** — the
owner decisions and the live or manual runs that no agent can finish alone — pulled out of the
proposals that raised them so they can be read in one place instead of in a dozen documents.

The queue now groups acceptance-heavy work under [Testing](../PROPOSALS.md#testing).
Those rows remain In progress and retain the same owner handoffs here.

It is a **derived index, not a second queue.** It never authorizes work, never sets rank and never
replaces a proposal row. When a row here disagrees with its source proposal, **the source wins** —
fix the row. The pattern is OpenTechnologyApp's *Operator action handoffs* section in its
`PRIORITY.md`: owner-run actions, each naming its canonical proposal, kept out of the implementation
backlog so they are neither lost nor mistaken for engineering work.

## The lanes

| Lane | Doc | Holds | Does not hold |
|---|---|---|---|
| **Content create** | [CONTENT_CREATE_TODO.md](CONTENT_CREATE_TODO.md) | Decisions and runs about **producing non-live content** — narration and voice, the pet, walkthrough and reactive clips, clips and thumbnails, publishing, the AI Learning Series, marketing drafts, the generation modules | Anything that needs OBS, a live account or capture hardware |
| **Stream** | [STREAM_DECISIONS_AND_TODO.md](STREAM_DECISIONS_AND_TODO.md) | Decisions, **live runs and testing** about streaming — accounts and handles, capture hardware, games, autonomy permission, live acceptance, performance gates, native Windows acceptance, the kill switch | Turning a finished recording into content |
| **Platform and release** | *no doc yet* — [the short table below](#platform-and-release-decisions-no-lane-doc-yet) | License, supported OS matrix, API trust model, naming, infrastructure images | — |

### Which lane?

Classify by what the run **exercises**, not by which proposal raised it.

- It exercises the **live path** — OBS, a real account, capture hardware, a real audience → **Stream**.
- It **produces or transforms a non-live artifact** — audio, image, clip, post, draft → **Content**.
- It needs both → **two rows, one per lane**, linked through their *Needs* column. Never one row in
  two lanes: a duplicated item is the second backlog this directory exists to prevent.

## Row format

| Prefix | Lane | Kind |
|---|---|---|
| `CT-A##` / `ST-A##` | content / stream | **Awaiting acceptance** — a `Pending` proposal waiting for the owner to accept, amend or defer it |
| `CT-D##` / `ST-D##` / `PL-D##` | content / stream / platform | **Decision** — one question, with the answer that applies if nobody answers |
| `CT-R##` / `ST-R##` | content / stream | **Run** — a one-off thing a person or hardware must do |
| `ST-T##` | stream | **Test** — a repeatable check, as opposed to a one-off run |

- **IDs are never reused or renumbered.** A resolved row moves to its doc's *Resolved* log and keeps its ID.
- **One row per item**, on one line, so two sessions adding rows rarely conflict.
- **Every open decision row ends its explanation with `**Question:** <one short sentence>`.** The full explanation stays; the
  question is additive — plain English, answerable yes or no where it can be, no identifiers, because the row already names its
  source. Answered rows move to the *Resolved* log and need none.
  `tests/docs/test_decision_questions.py` enforces it.
- **Every row names its canonical proposal** and the section that raised it.
- **Order is "unblocks the most else first"** — not by size, and not by proposal number.

**State:** `open` · `ready` (nothing stops you starting) · `blocked by <ID>` · `in flight` (another
branch or session has it — verify before starting) · `decided <date>` / `done <date>` · `dropped <date>`.

**Proof marker** on runs and tests — the same vocabulary as
[`../../tests/ACCEPTANCE-CHECKLIST.md`](../../tests/ACCEPTANCE-CHECKLIST.md), with *live* extended to
hardware and real accounts:

| Marker | Meaning |
|---|---|
| **auto** | Proven by `make test`, offline, with no human |
| **manual** | Needs a human; the steps are written down |
| **live** | Needs a running service, real hardware or a real account |
| **blocked** | Cannot be proven yet; the row names what is missing |

Rules for runs that touch a real account: **the owner performs the sign-in.** An agent continues
from an already-authenticated session and never types a password, key or token into a form;
credentials stay in environment variables and the OS credential manager, never in a row.

## Intake — the one required rule

When a proposal is written, or an existing one changes, and it contains an **owner decision** or a
**run only a person or hardware can do**:

1. Add **one row per item** to the matching lane doc **in the same change**, naming the proposal and
   section as its canonical parent.
2. If the proposal is `Pending`, add or update its **Awaiting acceptance** row.
3. When an item is answered or finished, **record the answer or the evidence in the source
   proposal first**, then move the row to the lane's *Resolved* log with the date. Never delete a row
   while its source still shows the question open.
4. When a queue row moves to `Done`, its rows here must already be resolved —
   `DM-PROPOSAL-DONE` in [`../agent/DOC-UPDATE-MATRIX.md`](../agent/DOC-UPDATE-MATRIX.md) fires on it,
   and `DM-PROPOSAL-OPEN` fires on the way in.

Nothing checks this automatically yet. That is a named weakness, tracked as `FD-21` in
[`../FUTURE_DOCS.md`](../FUTURE_DOCS.md): a check that diffs open queue rows against the map below
is cheap once the queue's sections match its states.

## Queue to lane map

Every non-`Done` queue row on `origin/main` as of 2026-10-04, and where its waiting items live.
*Both* means the proposal has items in two lanes.

| Proposal | State | Lane | Waiting items |
|---|---|---|---|
| P-001 Release gap closure | In progress — Testing; release gates open | Platform | PL-D01/PL-D02 open; PL-D03/PL-D04 resolved in source; real-hardware OBS evidence is ST-R01 |
| P-002 Open-source readiness | Pending | Platform | PL-D05, PL-D06 |
| P-003 Setup readiness contract | Code complete — external acceptance open | Stream | ST-R17, ST-T11 |
| P-004 Content asset generation | Pending | Content | CT-A03, CT-D14 |
| P-005 Standalone workflow and template testing | In progress — Testing, runner built | Both + Platform | Physical/live gates follow P-003/P-055/P-057/P-061; connected/mobile gates follow P-002/P-058/P-072 |
| P-019 `captions` | Deferred | — | Trigger recorded in [`../architecture/future.md`](../architecture/future.md) |
| P-020 Kubernetes | Deferred | — | Trigger recorded in the proposal row |
| P-021 `licensing` | Deferred | Platform | Follows PL-D01 |
| P-022 `video-generation` | Deferred | — | Trigger recorded in the proposal row |
| P-023 ContentExtend rename | Deferred | Both | CT-D12, PL-D07 |
| P-027 `creator-experience` | Partially done | Stream | ST-R16 (OBS profile export) |
| P-028 `realtime-ai` | Partially done | Content | CT-R13 (GPU verification of six workflows) |
| P-032 Setup timeline reorganisation | Pending | Platform | PL-D09 |
| P-055 OBS commands, real-hardware half | Code done, hardware acceptance open | Stream | ST-R01 |
| P-056 Stream Autopilot | In progress — Testing; bounded build ready | Stream | ST-D06, ST-D09–ST-D14, ST-R10–ST-R12, ST-T07–ST-T09 |
| P-057 Creator workflow inputs | Code complete — native Windows open | Content | CT-R12 (needs ST-D07) |
| P-058 Desktop remote control | Code complete — external acceptance open | Stream | ST-R14, ST-T12 |
| P-059 Nature learned tiers | Pending | Content | CT-A04, CT-D15, CT-D16 |
| P-060 Cityscape learned tiers | Pending | Content | CT-A05, CT-D15, CT-D16 |
| P-061 Blender production jobs | In progress | Content | CT-D17, CT-D18 |
| P-062 Social profile and account management | Code complete — external acceptance open | Both | Accounts: ST-D01, ST-D05, ST-R02, ST-R15. Private upload: CT-R01 |
| P-063 Open apps first / in-app setup | In progress | Both | ST-R17, ST-T11; clean-host Docker acceptance |
| P-064 AI Learning Series | In progress | Both | Airing: ST-R09. Everything else: CT-D11, CT-D13, CT-R09–CT-R11, CT-R14 |
| P-065 Recording handoff and profile workspaces | Code complete — external acceptance open | Both | Stream side: ST-R05, ST-R06. Content side: CT-R01 |
| P-066 Astra reaction audio | In progress — build authorized, release gates open | Stream | ST-D18, ST-R13, ST-T11 |
| P-067 Nova profile registry, walkthrough, mascot | Pending | Both | Content: CT-A01, CT-D01–CT-D03, CT-D07–CT-D10. Stream: ST-D03, ST-D16, ST-D17 |
| P-068 Local TTS stack for Nova | Pending | Content | CT-A02, CT-D04–CT-D06, CT-R02–CT-R04 |
| P-072 Unified desktop and optional cloud scope | In progress — Testing; private preview built | Both + Platform | PL-D10–PL-D14; Stream: ST-R18, ST-T14–ST-T17; Content: CT-R15–CT-R19 |
| P-074 Redesign from the OpenTechnologyApp pattern | In progress | Platform | PL-D15 (partly answered 2026-10-24) |
| P-075 Open-source release plan | In progress | Platform | PL-D16 (`OSS-D01` is `PL-D01`) |

`P-008` and `P-009` are standing practices, not work. `P-069` and `P-070` are `Done`, and a `Done` row carries no lane row.

## Platform and release decisions (no lane doc yet)

These are neither content nor stream. They are listed here so no owner decision is invisible, and so
the question *"does this need its own lane doc?"* has evidence behind it.

| ID | Decision | Source | Blocks | Default if unanswered | State |
|---|---|---|---|---|---|
| PL-D01 | Root license and accurate public wording **Question:** Confirm MIT as the repository's root license? | P-001 §4 (`D-01`) | Public release; accepting outside contributions | Keep private; do not call it open source | open — the only gate on public release. **P-075 recommends MIT and has prepared the root `LICENSE`; the owner confirms at `OSS-D01`** |
| PL-D02 | Supported alpha OS matrix **Question:** Make macOS and Ubuntu the supported operating systems for the alpha? | P-001 §4 (`D-02`) | The release workflow | macOS + Ubuntu as candidates, both unverified | open |
| PL-D05 | Does P-002 stay, or fold into P-001 and retire? **Question:** Fold the open-source readiness proposal into the release gap-closure proposal, and retire it? | P-002 queue row | Accepting either | None stated | open |
| PL-D06 | OpenTech queue/project identifiers and template schema; retention limit for unsent integration events **Question:** Will you provide the OpenTech queue and project identifiers and template schema, and set a retention limit for unsent events? | P-002 §12 | P-002 acceptance | None stated | open |
| PL-D07 | ContentExtend vs Creator Extend naming **Question:** Which name should published copy use: Creator Extend or ContentExtend? | P-023 (Deferred); also CT-D12 | Naming in any published copy | Preserve both names, as [`../PROJECT_CROSSWALK.md`](../PROJECT_CROSSWALK.md) does | open — needs re-acceptance |
| PL-D08 | MinIO source-build distribution | P-001/P-063; checksum-pinned server/client sources | Fresh source builds and bucket/lifecycle bootstrap | Existing MinIO/S3 contract preserved | **Resolved on PR #67** — CI run 37876242044 passed both builds and two live acceptance tests; main awaits merge |
| PL-D09 | Accept, or retire, the docs scaffold P-032 (setup timeline) **Question:** Accept the setup-timeline reorganisation, or retire it? | P-032 queue row. P-005, the other scaffold this row once named, was accepted and has been In progress since 2026-10-09 (queue), so it no longer waits here | Nothing downstream | Leave `Pending` | open |
| PL-D10 | Confirm supported OS/architecture targets and numerical startup/resource budgets from the separate-app baselines **Question:** Keep the current OS and architecture targets for the combined app, and set startup and resource budgets only after measuring? | [P-072 §3/§10](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#3-problem-goals-and-non-goals) | Combined-shell implementation and measurable acceptance | Preserve existing targets; make no performance improvement claim until measured | open — 2026-10-12 source inventory, installer byte/hash observations and measurement procedure recorded in §3; startup/resource/clean-host measurements remain open |
| PL-D11 | Choose combined product name, bundle identity and device migration policy, coordinated with P-023 **Question:** Pick the combined app's name and bundle identity now, or keep today's public names for the time being? | [P-072 §7/§12](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#7-contracts-and-examples) | Credential/settings migration and packaging | Internal path `apps/extend/` only; preserve current public names and identities | open — before Phase 2 |
| PL-D12 | Decide purchase/upgrade terms, store listing and stable-release rollback/support window **Question:** Set purchase and upgrade terms and a support window now, or defer them with no commercial change? | [P-072 §11/§12](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#11-rollout-and-rollback) | Public distribution and legacy retirement | No commercial change; keep old installers and credentials | open — before Phase 3 |
| PL-D13 | Review all five convergence gates and authorize the implementation slice; later approve public replacement after native/signing evidence **Question:** After reviewing the five convergence gates, do you authorize the next implementation slice of the combined app? | [P-072 §10](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#10-delivery-plan) | Implementation and retirement of separate apps | Planning only; existing downloads remain | open — 2026-10-12 §3 maps all five gates to current evidence and existing lane runs; none is closed by planning **Private preview authorized 2026-10-12** by explicit owner answer; preview built beside legacy apps. Five convergence conditions still gate full parity/migration/public replacement. |
| PL-D14 | Select any cloud stage for a separate proposal, including retention, privacy, quotas and operating budget **Question:** Keep cloud features off for now, and take up any cloud stage in a separate proposal later? | [P-072 §5/§10/§12](../proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#cloud-feature-scope) | C1–C3 implementation | Cloud disabled; desktop consolidation proceeds independently | open — optional follow-up |
| PL-D15 | Accept, amend or defer P-074 and answer its ten gates (`HYB-REDESIGN-D01` to `D10`): queue format, `docs/readable/`, contribution workflow, `security` skill, skill matrix, doc-update advisory, header coverage, template fields, PR template **Question:** Accept the recommended answer on each remaining gate of the redesign audit, listing any exceptions? | [P-074 §12.1](../proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md#121-decision-gates) | Every phase of P-074 | Stays `Pending`; nothing built; status quo on every gate | open — **partly answered 2026-10-24** (D01, D07 and D09; D04, D05 and D08 in part): see [§12.1a](../proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md#121a-owner-direction--2026-10-24). Still the owner's: D02, D03, D06, D10 and the rest of D04, D05 and D08. On 2026-10-26 the `security` skill (not path-bound) and eight status headers shipped; what is left is the `paths:` binding and four documents with no recorded review ([§12.1b](../proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md#121b-owner-direction--2026-10-26)). One row here rather than ten, so the table does not outgrow FD-25 |
| PL-D16 | Answer the sixteen open-source release gates (`OSS-D01` to `D16`): license and holder line, contribution terms, contact channels, secret-scan sign-off, history and refs policy, copyleft and non-commercial components, service pins, sibling-repo links, the apps in the public tree, commercial text, repository settings, first release. **`OSS-D01` is `PL-D01`** **Question:** Accept the recommended answer on each of the sixteen open-source release gates, listing any exceptions? | [P-075 §12.1](../proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md#121-decision-gates) | Publishing the repository; `PL-D01`; P-002 acceptance | Stays private; the MIT file stays in the tree | open — recommended answers are in §12.1; one row here rather than sixteen, for the same FD-25 reason as `PL-D15` |

**Decision for the owner:** if this table grows past about ten live rows, give it its own lane doc
(`PLATFORM_DECISIONS.md`, same format). It is deliberately not built until the evidence says so. **Question:** The platform table is now past that size: give it its own lane document?

### Resolved platform engineering decisions

The source proposal records the reconciliation first. These decisions no longer wait on an
unmade architecture choice; their separate release/native review gates remain open.

| ID | Decision | Source | Unblocked | Previous default | Resolution |
|---|---|---|---|---|---|
| PL-D03 | Local API trust model and API-key storage | P-001 §4 (`D-03`) | Mutating API exposure | Bind local only; require a configured key | **Resolved in source, confirmed 2026-10-12** — P-001 §4 records the API route ledger/auth tests and shared OS-vault desktop settings. Native/real-token acceptance remains separate. |
| PL-D04 | OBS WebSocket client: maintained crate vs internal protocol | P-001 §4 (`D-04`) | The OBS work package | Maintained v5 crate | **Resolved in source, confirmed 2026-10-12** — P-001 §4 records P-055's `obws::Client` implementation and protocol tests; dependency-license review remains release work. |

## How this grows

You will keep adding proposal work, so the structure is built to take it.

- **Adding work** is one row, on one line, in the right lane — never a new document.
- **A lane doc over about 60 open rows splits by sub-lane** into a second file in this directory,
  leaving a pointer row behind. Split by what is being exercised (for example, Stream Autopilot
  versus accounts and platforms), not alphabetically.
- **Resolved logs keep their last 25 entries.** Older ones move to a dated archive file in this
  directory. The rows are history, not clutter, so they are moved, not deleted.
- **A third lane** is added the same way the first two were: one new doc, one row in the lanes table.
- **The queue itself is not reordered by this directory.** Section placement inside `PROPOSALS.md`
  is a separate hygiene pass ([`../proposals/PROPOSAL_DOCUMENT_GAPS.md`](../proposals/PROPOSAL_DOCUMENT_GAPS.md) §10, phase 2).

## Related

- [`../PROPOSALS.md`](../PROPOSALS.md) — state and authorization; [`../PROPOSAL_CREATION_SOP.md`](../PROPOSAL_CREATION_SOP.md) — form and evidence.
- [`../FUTURE_DOCS.md`](../FUTURE_DOCS.md) — documents that do not exist yet, each with a state and a trigger.
- [`../proposals/PROPOSAL_DOCUMENT_GAPS.md`](../proposals/PROPOSAL_DOCUMENT_GAPS.md) — why these lanes exist and what else is proposed (P-071).
- [`../DOCUMENTATION_WORKFLOW.md`](../DOCUMENTATION_WORKFLOW.md) — how to prepare or refresh any document.
- [`../agent/VERIFICATION-MATRIX.md`](../agent/VERIFICATION-MATRIX.md) — what proves a change works.
