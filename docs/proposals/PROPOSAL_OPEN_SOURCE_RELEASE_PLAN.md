# Proposal: Open-source release plan — what is done now, and what needs the owner

> Copied from [`TEMPLATE_PROPOSAL.md`](TEMPLATE_PROPOSAL.md). **Numbers live in the queue, not in the
> filename.** This is the release-preparation counterpart to [P-002](PROPOSAL_OPEN_SOURCE_READINESS_AND_OPENTECH_COMPANION.md)
> (license, distribution and the optional companion) and [P-001](PROPOSAL_RELEASE_GAP_CLOSURE.md) (release
> engineering). It does not replace either: it lists every step to a publishable repository, does the ones that
> need no decision, and turns the rest into gates.

**Queue row:** `P-075`
**Agent model / effort:** `gpt-6.1-sol` / `high` — Release hygiene across licenses, history exposure and public-facing documents; legal conclusions stay with the owner
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `In progress` — on 2026-10-23 the owner directed that the steps needing no decision be executed in one pull request; the gates in §12.1 await the owner. State is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md), not here
**Owner:** OpenTechnology14 + agent
**Date:** 2026-10-23
**Roadmap layer(s):** None — release engineering and documentation; no new module
**Evidence level:** *Verified* for this repository at `41b54e6`: the tracked tree and every commit on every ref (166 commits, 13 remote branches). License data was read on 2026-10-23 from PyPI metadata, `cargo metadata` over the three desktop apps, the npm lockfiles, GitHub's license API and the model cards named in §2.5. **Not legal advice:** every license conclusion below is a flag for the owner, not a determination. *Proposed* for everything from §6 on

## 1. Executive summary

### Owner-directed repository split — 2026-11-01

**Work registration:** P-075 / public-snapshot-and-rename; Kind: proposal remainder;
state: private rename applied; sanitized source export under verification. Assignment: inherited Sol/high for release hygiene;
credential boundaries receive capable review; no model-switch or worker-dispatch claim.

Owner instructed that the existing repository remain private, that a second repository
receive this code with personal information and prior PR exposure removed, and that both
products be named **Open Content Creator Platform**. Confirmed GitHub names:
`Open_Content_Creator_Platform` (existing) and `Open_Content_Creator_Platform`
(new public source snapshot). This explicitly selects OSS-D06's clean-history route and
authorizes the repository creation/rename/public source copy. It does not approve production
readiness, claim all sixteen historical release choices answered, or authorize merging
unrelated PRs. Preserve the existing MIT/third-party notices in the source snapshot.

Scope: isolated continuation of the P-062 branch, display-name and repository-link updates,
private account matrix under P-062, a repeatable export that excludes private state and Git
history, personal-data/secret checks, and a clean public initial commit with a project
noreply author. Prior PRs, issues, Actions logs and WIP branches stay in the private repository.
No fork/mirror, copied PR archive, model weights or generated app binaries are published.
Existing local data directories, vault keys and native application IDs retain compatibility.
T3 startup uses the installed guide because this branch lacks its unmerged adoption docs;
the existing coordinator remains authoritative. The accepted AgentWorkflows reference
matches its local source; upstream has drifted and is not silently adopted.

Verification: inspect source/export manifests, secret scan with redacted findings, reject
private paths and private history, test exporter failure boundaries and run applicable offline
checks. Confirm both GitHub names/visibility, public author metadata and absent copied PRs
after publication. Runtime/native/provider acceptance remains independent of this source copy.


**Top line: the repository can be made ready to publish, but an agent cannot finish it alone.** This change does the
14 steps that need no decision (§10.1). **16 gates remain** (`OSS-D01` to `D16`, §12.1). Four of them decide whether
publishing is safe at all: the license and holder line, the history policy, the copyleft dependencies, and the two
contact channels. The visibility flip itself is the owner's action and is not taken here. **No live credential was
found in the working tree or in any commit.**

What the work found, in the order it matters:

1. **History is the largest exposure, and a clean tree does not fix it.** All 166 commits carry one personal e-mail
   address as author. The two private registry rows removed here remain in the history of the pull request that added
   them. Absolute local paths remain in the history of four documents, 13 remote branches carry unmerged work, and
   the 83 pull requests and the Actions logs become public with a visibility flip of this repository. Only a fresh
   repository with one reviewed snapshot avoids all of it (OSS-D06).
2. **The root license is absent and the manifests contradict the owner's direction.** Nine first-party Rust manifests
   declare `BSL-1.1`, which the owner dropped on 2026-10-05. MIT is recommended and applied (OSS-D01).
3. **Three Python libraries the code imports are copyleft, and one bundles a binary.** Ultralytics is AGPL-3.0,
   pyvirtualcam is GPL-2.0, obsws-python is GPL-3.0-only, and imageio-ffmpeg ships an FFmpeg executable. Services
   pulled by the compose files add more: MinIO, Grafana and Loki are AGPL-3.0, n8n uses its Sustainable Use License,
   and the floating `redis:7-alpine` tag resolves to a release under a non-OSI license. Four recommended models are
   non-commercial (§2.5).
4. **The two private rows are removed.** The registry flags exactly two rows `visibility: private`; both are gone with
   their subject files and the private target. A public subject on an overlapping topic was left untouched, as the
   owner decided on 2026-10-21.
5. **Governance files already existed.** `CONTRIBUTING.md`, `SECURITY.md` and `CODE_OF_CONDUCT.md` were present and
   are rewritten for a public reader; the conduct file now carries the Contributor Covenant 2.1 text.
6. **One defect surfaced from the license walk.** The Windows-only VoiceMeeter requirement named a package that does
   not exist on PyPI, so a clean install of that exporter would fail. It is fixed with a test.
7. **The two apps are not combined.** There are two shipping desktop apps, a third private preview shell, and a shared
   component library; the README now says so (§2.7).

| The request asked for | Where it is |
|---|---|
| Private-rows removal and a sweep for private-system references | S01, S02; §2.3 |
| License audit and dependency walk in the Ironfall provenance pattern | S04, S05; §2.5; `docs/THIRD_PARTY_PROVENANCE.md` |
| Secrets scan | S03; §2.4 |
| README overhaul, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` | S06 to S09 |
| Release-checklist completion | S10; §2.2 |
| Steps done now versus decision gates `OSS-D01…` | §10.1 and §12.1 |
| The UI question | §2.7 |

## 2. Verified current state

### 2.1 Method

| Evidence | How it was gathered |
|---|---|
| Secret scanning | `gitleaks` 8.30.1 over all refs and the tree, redacted; plus a keyword scan of every added line in `git log --all -p` (177,047 lines), with each candidate classified and its value masked |
| Python licenses | PyPI JSON metadata for the exact pinned version of each distinct package in every `requirements*.txt` |
| Rust licenses | `cargo metadata --locked` for the three desktop apps |
| Node licenses | the `license` field of every `package-lock.json` entry |
| Services and tools | GitHub's license API per repository; Redis from `redis.io/legal/licenses`; n8n and AITuberKit from their LICENSE files |
| Models | the model card or OpenModelDB page of each model named in the docs |
| History exposure | `git shortlog`, `git branch -r`, `git log --all -G` for the private-system terms, and `gh` counts for pull requests, issues and runs |

### 2.2 The release checklist

[`../OPEN_SOURCE_RELEASE_CHECKLIST.md`](../OPEN_SOURCE_RELEASE_CHECKLIST.md) has 23 boxes. Six were already ticked. The
checklist's own rule applies throughout: **no P0 legal box is ticked on an agent's say-so.**

| # | Box | Before | After this change |
|---|---|---|---|
| 1 | Root `LICENSE` exists and matches every manifest | open | Prepared (MIT, nine manifests corrected); **unticked until the owner signs off** (OSS-D01, D02) |
| 2 | "Open source" is legally accurate | open | README states the license and its exceptions; unticked pending OSS-D01, D07 to D09 |
| 3 | `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` exist | ticked | Still ticked; contents rewritten; contacts are OSS-D04 |
| 4 | Third-party notices and dependency licenses reviewed | open | Walk done and ledgered (S05); **owner review of the flags** (OSS-D07 to D10) |
| 5 | Branding and screenshots hold no personal or customer data | open | Evidence: no screenshot is tracked; icons are generated placeholders; the marks are first-party. Unticked pending OSS-D02 |
| 6 | Clean clone installs and builds on every claimed OS | open | Not doable here; P-001 and the supported-OS decision |
| 7 | CI enforces lint, test and build | ticked | unchanged |
| 8 | A complete creator journey passes | ticked | unchanged |
| 9 | Release-scope placeholder paths implemented or flagged | open | Open; P-001 and P-003 |
| 10 | `.env.example` covers every variable | ticked | unchanged |
| 11 | Production config refuses weak secrets | ticked | unchanged |
| 12 | Database, Redis and metrics ports not public by default | ticked | unchanged |
| 13 | CORS and WebSocket origins follow the trust boundary | open | Open: both legacy desktop apps still set a null CSP (OSS-D12; P-001) |
| 14 | Working tree and full history pass secret scanning | open | Scan run (§2.4); four reviewed fixtures; unticked until OSS-D05 |
| 15 | Route and command authorization decisions complete | open | Open; P-001 |
| 16 | Uploads, paths, launches and sync keys validated and limited | open | Open; P-001 |
| 17 | Data-flow document | open | **Not started.** `AUDIT.md` recommends it; estimate one small PR |
| 18 | Vulnerability-reporting contact and response policy published | open | Policy rewritten; the contact channel is OSS-D04 |
| 19 | No `visibility: private` row in the published tree | open | **Done and ticked** (S01); a test now holds it |
| 20 | Version, changelog, compatibility matrix, SBOM, checksums, rollback | open | OSS-D15 |
| 21 | Artifacts reproducibly tied to the tag | open | OSS-D15 |
| 22 | Backup, restore and outage scenarios pass | open | Open; P-001 live acceptance |
| 23 | Known limitations in plain language | open | README "Status" section; release notes under OSS-D15 |

### 2.3 Private rows and private-system references

- The registry flagged exactly two rows `visibility: private`, each with a subject file, plus one `private-local` target.
  All five are removed. `rg 'visibility: private' modules/marketing-crosswalk` now finds nothing in the data files.
- A search of the tracked tree for spreadsheet, script and board identifiers, tenant or host names, ticket-system
  links and internal process names found **none of those categories**. What remained was generic wording about the
  private rows (rules in three skills, a digest line, a schema note and a consumers-list paragraph), which went with
  them, and an exclusion list in P-067 that names the category, not a specific.
- **Absolute local paths** naming the owner's operating-system account and two sibling repositories appeared on 12
  lines in four documents. They are replaced with generic placeholders.
- A public subject covering the same topics stays, by the owner's decision of 2026-10-21 (OSS-D16).
- **History is unchanged by this.** Five commits on `main` touch the sweep terms: the private rows (#80), the skill and
  digest wording (#81), the P-067 exclusion list (#49), the original public subject (#5) and a hygiene rule in P-074 (#83). Removing a row from the tree does not remove it from those commits.

### 2.4 Secrets

| Scan | Result |
|---|---|
| Working tree, `gitleaks` | 1 finding: a fixed mock OBS challenge string in a test |
| All refs, `gitleaks` (160 commits scanned) | 3 findings: a JWT-shaped string and a private-key header in a walkthrough-lint test, both **only on the unmerged branch of PR #65**; and the same mock challenge |
| Keyword scan of 177,047 added lines | 2,028 lines matched; 1,549 prose, 268 short values, 94 identifiers, 92 placeholders or test markers, **25 candidates** (16 distinct). All 16 are placeholders, fixtures, a token URL, a design-token file name or code that computes a hash |
| Known token formats | 11 hits, all in the same branch-only test: an AWS documentation example key, `sk-` and `xoxb-` test strings, a fake JWT and PEM headers |
| Tracked key or environment files | none; only the two `.env.example` files, whose values are placeholders |

**No live credential was found.** The four findings are fixtures and are recorded by fingerprint in `.gitleaksignore`
so that a future scan is quiet; the checklist box stays open until the owner signs them off (OSS-D05). The release
evidence collector's earlier run reached the same count.

### 2.5 Licenses

**Linked or imported by this repository's code, Python:**

| Package | Used by | License (source) | Flag |
|---|---|---|---|
| `ultralytics` 8.3.0 | `modules/sports-analytics/` (golf tracer, pose estimation) | AGPL-3.0-or-later (PyPI) | **AGPL** |
| `pyvirtualcam` 0.11.1 | `modules/realtime-ai/` (AR filters, ComfyUI webcam bridge), `modules/sports-analytics/` (NDI output) | GPL-2.0 (PyPI) | **GPL** |
| `obsws-python` 1.8.0 | `modules/observability/source-health-exporter/`, `scripts/setup/test_obs_websocket.py` | GPL-3.0-only (PyPI) | **GPL** |
| `imageio-ffmpeg` 0.6.0 | `modules/content-creation/stream_shorts/`, two setup scripts | BSD-2-Clause wrapper; the wheels ship an FFmpeg executable and the package page does not state its license | **Review: bundled binary** |

The other 31 distinct Python packages are MIT, BSD, Apache-2.0 or ISC. Rust: 614 third-party crates, all
permissive except five MPL-2.0 crates (`cssparser`, `cssparser-macros`, `dtoa-short`, `option-ext`, `selectors`), one
CDLA-Permissive-2.0 data crate and `r-efi`, whose license offers MIT or Apache-2.0 beside an LGPL option. Node: four
lockfiles, 467 entries, all MIT, Apache-2.0, ISC, BSD, CC0 or 0BSD; the three desktop apps' are build tooling only.

**Services the compose files pull or build:**

| Service | Where | License (source) | Flag |
|---|---|---|---|
| MinIO server and `mc` | built from pinned sources by `modules/storage-data/minio/Dockerfile` | AGPL-3.0 (GitHub) | **AGPL.** Built locally; CI pushes only the FastAPI image |
| Grafana, Loki | `docker-compose.yml`, `:latest` tags | AGPL-3.0 (GitHub) | **AGPL**; promtail was not separately checked |
| n8n | `docker-compose.yml`, two services | Sustainable Use License, with an Enterprise License for `.ee.` files (its LICENSE.md) | **Not OSI; use restrictions** |
| Redis | `docker-compose.yml`, `cloud/docker-compose.relay.yml`, `redis:7-alpine` | BSD-3-Clause to 7.2.x; RSALv2 or SSPLv1 from 7.4; AGPLv3 added at 8 (redis.io) | **Floating tag crosses the boundary** |

**Plugins that link or import a GPL host:** `plugins/obs-plugin/` links libobs (OBS Studio is GPL-2.0 per GitHub);
`plugins/blender-addon/` declares `MIT` in its `bl_info`; `plugins/krita-integration/` scripts Krita (GPL-3.0).
Plugins that use a host's API are commonly treated as covered by the host's license; MIT source is GPL-compatible,
but a distributed plugin binary follows the host's terms. Flag for review (OSS-D09). `plugins/LICENSE` is MIT.

**Models the docs recommend (none is committed):**

| Model | License (source) | Flag |
|---|---|---|
| SDXL Turbo | `sai-nc-community` (model card) | **NC** |
| FLUX.1 Fill [dev] | `flux-1-dev-non-commercial-license`; outputs usable commercially per the card | **NC (model)** |
| RMBG-1.4 | `bria-rmbg-1.4`, a non-commercial Creative Commons license (model card) | **NC** |
| 4x-UltraSharp | CC-BY-NC-SA-4.0 (OpenModelDB) | **NC and SA** |
| YOLOv8 weights | the Ultralytics terms; AGPL-3.0 for the library | **AGPL** (weights not separately checked) |
| SDXL base, SD 1.5, LCM-LoRA, ControlNets, IP-Adapter, SAM and variants, inpainting checkpoints, SDXL VAE | not recorded in the repository and not verified here | needs registry entries |

`modules/model-registry/registry.yml` is deliberately empty because no weight has been downloaded and checksummed.

**External tools the docs integrate with, not bundled:** OBS Studio GPL-2.0; ComfyUI, DeepFaceLive, Krita and the Krita
AI Diffusion plugin GPL-3.0; Deep-Live-Cam AGPL-3.0; AITuberKit under a custom license that offers a non-commercial
license or a commercial one; NodeCG, Ollama MIT; Prometheus Apache-2.0; VTube Studio, VoiceMeeter and DaVinci Resolve
proprietary.

**Assets:** eight soundboard files, each recorded in `modules/soundboard/sounds/manifest.yaml` as CC0 1.0 with its
source. Icons are generated placeholders. The logo and four brand marks are first-party.

### 2.6 What a visibility flip publishes

| Surface | State | Consequence |
|---|---|---|
| Commits | 166, one author identity with a personal e-mail | Permanent once public |
| Refs | `main` and 12 other branches, several with unmerged work | All visible unless pruned |
| Pull requests | 83, no issues | Titles, bodies and comments become public |
| Actions | at least 100 runs | Logs become public |
| Repository metadata | no description, no topics, no license | A visitor sees an unlabelled repository |
| Links | README and docs link to 8 sibling repositories, seven of them private | Dead links for readers (OSS-D11) |

### 2.7 First impression: are the two UIs one?

**No.** Today there are two separate shipping desktop apps, one private preview shell that is the consolidation
vehicle, and a shared component folder. [P-072](PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md) already records the owner's
direction to ship one app and the five convergence gates; none is closed.

| Surface | Entry point | Identity |
|---|---|---|
| Stream Extend | `apps/stream-extend/src/routes/+page.svelte` (451 lines) and `src/lib/` | `Stream Extend`, `com.streamextend.app`, dev port 5173 |
| Creator Extend | `apps/creator-extend/src/routes/+page.svelte` (1,023 lines) and `src/lib/WorkflowInputs.svelte` | `Creator Extend`, `com.creatorextend.app`, port 5174 |
| Extend Preview (combined) | `apps/extend/src/routes/+page.svelte` (160 lines), `configs/ui/combined-navigation.json` | `Extend Preview`, `com.hybridcreator.extend.preview`, port 5175, macOS bundles only |
| Shared | `apps/shared/ui/*.svelte`, imported by relative path | one setup panel, profile switcher, recording library, remote control, social management |

The preview already offers a Stream or Create workspace choice, one shared setup, separate profile selections, the
shared recording inbox and a read-only readiness view, with a strict CSP. It has no native broadcast, render, remote
or publishing commands, migrates no settings, and imports none of the other two apps' screens. The two legacy apps
have no CSP (the checklist's box 13). For a contributor, `apps/` therefore shows three apps with a confusing name
(`extend` beside `stream-extend` and `creator-extend`). The README explains the layout; a new consolidation proposal
is not needed, because P-072 is that proposal. What the owner decides for the public face is OSS-D12.

## 3. Problem, goals, and non-goals

**Problem.** The repository is described as intended for open source but has no license, manifests that say BSL, a
README written for the owner, copyleft dependencies nobody has ledgered, and a history that cannot be cleaned by
editing the tree.

**Goals.**

- Every step that needs no decision is done and tested, with the checklist updated to say what each box now rests on.
- Every step that needs a decision is a numbered gate with options and a recommendation.
- A guard stops the same mistakes returning: a private row, a local path, a manifest that disagrees with `LICENSE`.
- A reader of the README learns what the project is, what state it is in, how to build it and where to contribute,
  without a claim ahead of the evidence in [`../AUDIT.md`](../AUDIT.md).

**Non-goals.**

- **No visibility change, tag, release, history rewrite or repository setting.** Those are the owner's (§11).
- No legal determination, and no relicensing of a third party's work.
- No change to a module's behaviour, except the corrected requirement name in S11.
- No engineering item that P-001 owns: clean-clone builds on each OS, placeholder paths, CORS and CSP, authorization,
  upload limits, backup and restore.
- No change to the two public subjects, the design-system hub or the registry's other rows.

## 4. User paths and states

| Path | Today | After this change |
|---|---|---|
| A visitor opens the repository | A README for the owner, pricing tables and links to private repositories | A short README: what it is, status, install, quickstart, contribute, license |
| A contributor wants to help | `CONTRIBUTING.md` says contributions should not be solicited | A public guide; contribution terms are inbound equals outbound under the root license until OSS-D03 |
| A reporter finds a vulnerability | "Contact the maintainer through the repository host" | Same path, stated plainly; the channel is OSS-D04 |
| Someone reports a conduct concern | A short custom text | Contributor Covenant 2.1; the contact carries `OWNER-SET` until OSS-D04 |
| An agent adds a private row | Allowed by the registry | A test fails |
| The owner flips visibility | Nothing prevents it | `public_release_guard.py --release` lists what is still unset |
| A user installs an optional integration | No notice of its license | The ledger and `THIRD_PARTY_NOTICES.md` name it |

## 5. Architecture and data flow

Everything stays in the repository: Markdown, YAML, one standard-library script and its tests. No service, network
call, secret or OAuth scope is added.

| Layer | Holds | After this change |
|---|---|---|
| `LICENSE`, manifests | The grant and its metadata | MIT at the root; first-party manifests agree |
| `docs/THIRD_PARTY_PROVENANCE.md` | One row per third-party component, with license, flag and use | New; the Ironfall pattern |
| `THIRD_PARTY_NOTICES.md` | Attributions a license requires | New |
| `docs/PRODUCT_OVERVIEW.md` | The product and commercial content the old README carried | New; nothing deleted |
| `scripts/testing/public_release_guard.py` | Hygiene checks and the owner-pending list | New |
| `modules/marketing-crosswalk/` | The registry | Two private rows and one private target fewer |

## 6. Direct injection map

| Location | Before | Change | Verification |
|---|---|---|---|
| `modules/marketing-crosswalk/crosswalk/modules.yml`, `targets.yml`, two subject files | Two private rows, one private target | Removed | `test_discovery_modules.py`, guard test |
| `tests/marketing_crosswalk/test_discovery_modules.py`, `tests/design_system/test_hub_structure.py` | Named the private rows | Rewritten around "no private row ships" | offline suite |
| Schema notes, three skills, the digest, the consumers list | Explained the private rows | Reworded or removed | docs and design-system tests |
| Four documents | Absolute local paths | Generic placeholders | guard |
| `LICENSE`; ten `Cargo.toml`; six `package.json` | No root license; `BSL-1.1` in nine | MIT | guard |
| `docs/THIRD_PARTY_PROVENANCE.md`, `THIRD_PARTY_NOTICES.md`, `.gitleaksignore` | None | New | docs tests |
| `README.md`, `docs/PRODUCT_OVERVIEW.md` | 534-line product README | Public README; old content relocated | link and index tests |
| `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` | Internal wording | Public wording; Contributor Covenant 2.1 | link tests |
| `modules/observability/source-health-exporter/requirements.txt` | A package that does not exist | The real package name | new test |
| `scripts/testing/public_release_guard.py` and its test | None | New | offline suite |
| `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md` | 23 boxes, 6 ticked | Dispositions, one box ticked, sign-off rows | read |
| `docs/PROPOSALS.md`, `docs/todo/README.md`, `docs/README.md`, registry | No P-075 | Rows and index entries | `proposal_report.py --check` |

## 7. Contracts and examples

**License.** MIT, text unmodified, holder line `Open Content Creator Platform contributors` and year `2026` as the default
until OSS-D02. The existing `plugins/LICENSE` is unchanged and says `2024 Open Content Creator Platform`; the two holder
lines should be made one by the owner.

**Provenance row** (the Ironfall columns, adapted from packs to software):

| Component | Source | Version | License (SPDX) | Use | Flag | Redistributed here? | Attributed? | Notes |
|---|---|---|---|---|---|---|---|---|

The Ironfall policy rejects NC, SA, GPL and AGPL because it ships a commercial game. This repository's policy is
looser and stated in the ledger: **a flagged component may be recommended or imported only with its license named,
and never bundled into a hosted paid feature without an owner decision.**

**Owner-pending marker.** An unset value that only the owner can supply is written `OWNER-SET` in the public file
that needs it. `public_release_guard.py` reports every occurrence, and `--release` makes them fail.

**Guard CLI.** `python3 scripts/testing/public_release_guard.py [--release] [--root PATH]`. Hygiene checks always run
and must pass: no `visibility: private` in the registry data; no absolute home path in a tracked text file; a root
`LICENSE` whose SPDX id equals the `license` of every first-party manifest that declares one; no tracked `.env`,
key or certificate file. `--release` also fails on any `OWNER-SET`. Exit code 1 on failure.

**README outline.** Value proposition; status in one honest paragraph; what is in the repository, including the
three apps; install from source; quickstart; documentation; the design-system hub and the crosswalk registry;
contributing; license and its exceptions. Pricing, subscription, self-hosting and the module feature tables move to
`docs/PRODUCT_OVERVIEW.md`.

## 8. Security, privacy, accessibility, and observability

- **Security.** No new network path or scope. The guard reads tracked files only. `.gitleaksignore` holds four
  fingerprints with the reason beside each; it silences nothing else.
- **Privacy.** The personal e-mail in history is not printed anywhere in this change. No new text names the private
  tooling, a person's e-mail, an account name or a local path.
- **Accessibility.** Markdown with ordered headings and plain tables; the README keeps the logo's alt text.
- **Observability.** The guard names each offending file and line; the checklist records evidence beside each box.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| T-01 | A private row is added to the registry | `test_no_private_row_ships` and the guard fail | auto, mutation | this PR |
| T-02 | An absolute `/Users/<name>/` path is added to a tracked doc | the guard fails and names the line | auto, mutation | this PR |
| T-03 | A manifest says `BSL-1.1` or any license other than the root's | the guard fails | auto, mutation | this PR |
| T-04 | A `.env` or `*.pem` file is tracked | the guard fails | auto | this PR |
| T-05 | `OWNER-SET` appears in a public file | listed in default mode; fails with `--release` | auto | this PR |
| T-06 | The VoiceMeeter requirement names a package that does not exist | a test pins the correct distribution name | auto, mutation | this PR |
| T-07 | Rules for a private row on a synthetic crosswalk | the loader still refuses to generate for it | auto | this PR |
| T-08 | Links, index entries and queue-to-lane map | docs integrity and `proposal_report.py --check` pass | auto | this PR |
| T-09 | `make test`, `ruff`, `generate_docs.py --check` | green; result recorded | auto | this PR |
| T-10 | A fresh scan after the owner's history decision | `gitleaks` over the published history reports no finding or only the four signed fixtures | manual | OSS-D06 |
| T-11 | A clean clone builds on each claimed OS | per P-001 | live | OSS-D15 |

## 10. Delivery plan

### 10.1 Steps — what can be done now and what cannot

| Step | What | State | Gate |
|---|---|---|---|
| S01 | Remove the two private rows, their subject files and the private target; reword what existed for them; add a guard | **Done in this change** | — |
| S02 | Sweep for private-system references; replace local paths in four documents | **Done** | history: OSS-D06 |
| S03 | Scan the tree and every ref for secrets; record; fingerprint the four fixtures | **Done** | sign-off: OSS-D05 |
| S04 | Record the license choice; add `LICENSE`; correct nine `BSL-1.1` manifests, add the field to the tenth, and set it in six `package.json` | **Done** (MIT) | confirm: OSS-D01, D02, D03 |
| S05 | Walk dependencies; ledger them in the Ironfall pattern; add notices | **Done** | flags: OSS-D07 to D10 |
| S06 | Rewrite the README for a public reader; relocate the old content | **Done** | OSS-D11, D12, D13 |
| S07 | Rewrite `CONTRIBUTING.md` | **Done** | OSS-D03 |
| S08 | Replace `CODE_OF_CONDUCT.md` with Contributor Covenant 2.1 | **Done**, contact `OWNER-SET` | OSS-D04 |
| S09 | Refresh `SECURITY.md`, correcting its stale limitations list | **Done** | OSS-D04 |
| S10 | Walk the 23-box checklist; tick box 19; add sign-off rows | **Done** | see §2.2 |
| S11 | Correct the VoiceMeeter requirement name | **Done** | — |
| S12 | Add the public-release guard and its tests | **Done** | — |
| S13 | Queue row, lane row, generated registry, docs index | **Done** | — |
| S14 | Answer the UI question and state it in the README | **Done** (§2.7) | OSS-D12 |
| S15 | Data-flow document (checklist box 17) | Not started | none; one small PR |
| S16 | History and refs policy | Owner decision, then owner action | OSS-D06 |
| S17 | Repository settings, description, topics, visibility | Owner action | OSS-D14 |
| S18 | First tag, changelog, SBOM, signing | Owner action | OSS-D15 |
| S19 | Clean-clone builds, placeholder paths, CORS and CSP, authorization, uploads, backup and restore | Tracked by P-001 | P-001 |

### 10.2 Phases

| Phase | Contents | Evidence |
|---|---|---|
| 0 — this change | S01 to S14 | T-01 to T-09 |
| 1 — owner decisions | OSS-D01 to D16 answered | the answers recorded in §12.1 |
| 2 — history and settings | S16, S17 | T-10 |
| 3 — first release | S18, S19 | T-11 and the signed checklist |

Out of scope throughout: any code change that is not a dependency-name correction.

## 11. Rollout and rollback

- **Rollout of this change.** One pull request, no flag. The edits are documentation, metadata, one removed registry
  fixture and one new script; the registry loader is unchanged.
- **Rollback of this change.** `git revert` the squash commit; run `generate_docs.py --write`.
- **The flip.** Making a repository public is reversible in name only: clones, forks and caches persist. Treat it as
  irreversible. That is why S16 comes before S17.
- **Support response.** None until the repository is public; then the contact channels in OSS-D04 apply.

## 12. Risks and unresolved decisions

### 12.1 Decision gates

The recommended answer is the owner's default to accept, not an agent's. An unanswered gate means the repository stays
private and the status quo holds. Reply `OSS-D01–D16 accept as recommended`, or list exceptions.

| Gate | Question | Options | Recommended | If unanswered |
|---|---|---|---|---|
| `OSS-D01` | Which root license? **Question:** Use the MIT license for the repository's own code? | MIT / Apache-2.0 / none | **MIT.** Simplest, GPL-compatible, and the owner's existing public repository is MIT. Apache-2.0 adds a patent grant but is not compatible with GPL-2.0-only hosts | The MIT file stays; do not publish |
| `OSS-D02` | Copyright holder line, and are the product names and marks yours to license? **Question:** Is the project name the right copyright holder, and are the product names and marks yours to license? | the project-name line as written / a legal name / the brand | A legal name if one exists; else keep the line. Make `plugins/LICENSE` match | Line as written |
| `OSS-D03` | Contribution terms? **Question:** Accept contributions on the same MIT terms, with no CLA or sign-off requirement? | inbound equals outbound / DCO sign-off / CLA | Inbound equals outbound; MIT already permits proprietary derivatives, so a CLA buys little and deters drive-by changes | Inbound equals outbound |
| `OSS-D04` | Contact for conduct reports, and for vulnerability reports? **Question:** Will you set up a project mailbox and turn on private vulnerability reporting for conduct and security reports? | a project mailbox / enable GitHub private vulnerability reporting / both | Both, and use no personal address | The conduct file carries `OWNER-SET`; `--release` fails |
| `OSS-D05` | Sign off the four reviewed fixture findings as non-secrets? **Question:** Accept the four reviewed secret-scan findings as test fixtures, not real secrets? | accept / remove the fixtures | Accept; the fingerprints are in `.gitleaksignore` | Checklist box 14 stays open |
| `OSS-D06` | History and refs: what is published? **Question:** Publish a new repository with one clean snapshot commit, and keep this one private as the archive? | (a) flip this repository / (b) a new repository with one reviewed snapshot commit and a noreply author / (c) rewrite history here, then flip | **(b).** It alone removes the personal e-mail, the private rows in history, the local paths, 12 WIP branches, 83 pull requests and the run logs. Keep this repository private as the archive | Do not flip |
| `OSS-D07` | The four copyleft or bundled-binary Python dependencies? **Question:** Make the copyleft and bundled-binary Python libraries optional extras with license notices, instead of required dependencies? | keep as optional user-installed extras with a license notice / replace / relicense the module / buy a commercial license | Per library: replace `obsws-python` with the in-repo OBS WebSocket client or make it optional; make `pyvirtualcam` and `ultralytics` optional extras with notices and evaluate a permissive detector; document `imageio-ffmpeg`'s bundled binary or use the system FFmpeg | Ledger flags stay; nothing changes |
| `OSS-D08` | Service images and pins? **Question:** Pin Redis to 7.2.x or switch to Valkey, and keep the AGPL services as user-run, never pushing modified images? | pin Redis to 7.2.x or use Valkey (BSD-3-Clause) / keep floating; document the AGPL services and n8n's limits | Pin Redis; keep MinIO, Grafana and Loki as user-run services and never push modified images; note that a hosted paid cloud raises AGPL network-use questions | Floating tags stay |
| `OSS-D09` | Plugin licensing? **Question:** Relicense the OBS, Blender and Krita plugins to match their host programs' GPL terms, after legal review? | keep `plugins/` MIT / relicense the OBS plugin to GPL-2.0-or-later and the Blender and Krita pieces to GPL-3.0-or-later | Relicense to the hosts' terms; legal review first | Stay MIT; flag stays |
| `OSS-D10` | Non-commercial models? **Question:** Mark the four non-commercial models in the docs and keep them out of any paid feature? | add a license column and mark the four NC rows / swap for permissive models / also fill the registry (needs downloads and checksums) | Mark them now, keep NC models out of any paid feature, fill the registry as weights are downloaded | Docs unchanged |
| `OSS-D11` | Links to private sibling repositories? **Question:** Replace links to the private sibling repositories with plain text in public-facing docs? | publish them / unlink to plain text / leave | Plain text in public-facing docs; leave historical proposals | Left; the README avoids them |
| `OSS-D12` | The apps in the public tree, and the null CSP? **Question:** Publish both desktop apps in the public tree, with the combined-app preview labelled and a content security policy set first? | publish both apps and keep `apps/extend` labelled preview / hold `apps/extend` back / wait for the combined app; set a CSP in both legacy apps before a public alpha | Publish both, label the preview, fix the CSP first | Unchanged |
| `OSS-D13` | Pricing and subscription text? **Question:** Trim the pricing and subscription text to what is true today? | keep public / trim to what is true today / remove | Trim: prices and tiers are plans until a store listing exists | Stays in `docs/PRODUCT_OVERVIEW.md` |
| `OSS-D14` | Repository settings at the flip? **Question:** Turn on all the listed repository safeguards at the flip, and add a description? | private vulnerability reporting, secret scanning and push protection, Dependabot, branch protection, code owners, issue and PR templates, description and topics | All of them; also a description, which is empty today | Owner action |
| `OSS-D15` | What is the first release? **Question:** Make the first release source-only, as an architecture preview, with no installers? | source-only architecture preview / a tagged alpha with installers | Source-only: `AUDIT.md` calls the repository an architecture preview until the P0 gates close | None |
| `OSS-D16` | Do the two public subjects stay? **Question:** Keep the two public subjects, as decided on 2026-10-21? | keep / remove | Keep, as decided on 2026-10-21 | Stay |

The lane index carries these as one row, `PL-D16`, not sixteen: its platform table is already past the size at which
FD-25 says to give it its own document.

### 12.2 Risks

| Item | Impact | Mitigation / decision owner | Due |
|---|---|---|---|
| The flip exposes history | Personal e-mail, private rows, local paths and 83 PRs become public and permanent | OSS-D06 (b); this change does not rewrite history — owner | before S17 |
| An agent's license reading is wrong | A mislabelled flag | Every row cites its source; the conclusions are flags, and OSS-D07 to D09 call for legal review — owner | before S17 |
| MIT with AGPL or GPL optional integrations | A user who bundles them inherits their terms | The ledger and notices name each; OSS-D07 — owner | before S17 |
| The placeholder contact ships | A conduct file with no way to report | `--release` fails on `OWNER-SET`; OSS-D04 — owner | before S17 |
| Concurrent edits | The owner's checkout has uncommitted edits to several files this change touches | Built in a clean worktree off `main`; expect a manual merge there — owner | on merge |
| FD-25 trigger | The platform table is already past its guideline | One umbrella row; the owner decides FD-25 separately — owner | at acceptance |

## 13. Documentation updates

**This change:** `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`,
`docs/PROPOSALS.md`, `docs/todo/README.md`, `docs/README.md` (index entries), `docs/PRODUCT_OVERVIEW.md` and
`docs/THIRD_PARTY_PROVENANCE.md` (new), `THIRD_PARTY_NOTICES.md` and `LICENSE` (new), the crosswalk schema notes and
the skills and digest that described the private rows, four documents with local paths, and
`docs/agent-registries/documentation.json` (regenerated). Rules fired: `DM-PROPOSAL-OPEN`, `DM-PROPOSAL-MODEL`,
`DM-DOCS-INDEX`, `DM-CONTEXT` if `CLAUDE.md` changes.

**Follow-ups after the gates:** `docs/todo/README.md` resolved rows; the model docs' license column (OSS-D10); the
data-flow document (S15).


## 14. Repository-split verification checkpoint — 2026-11-01

- Existing repository renamed to `Open_Content_Creator_Platform`; GitHub reports
  PRIVATE and the shared Git remote now uses its new URL. Prior PRs/history are retained there.
- New `Open_Content_Creator_Platform` repository created privately for staging; Actions disabled
  while the source candidate is inspected. Publication remains a separate recorded step below.
- Display-name updates preserve app identifiers, the OS-vault service key and local state paths.
  Old repository names remain only where required by literal historical source evidence.
- P-062's private matrix has 17 identity rows and 17 access rows spanning all 15 providers.
  No real account fields or passwords were filled. Public export excludes the whole private tree.
- Export tests: 18 passed. Thirteen export guards were independently disabled; every mutation
  was caught, and the original source restored. An accidentally overlapping verification run
  observed the intentional mutation; the subsequent isolated run passed all 1,114 focused
  release/docs/crosswalk checks. No mutation is retained.
- Full private `make test`: exit 0, with three existing live/environment skip markers.
  Ruff, generated-doc checks and diff checks passed. Crosswalk validation confirmed 107 anchors
  and 55 status claims against clean App main and Blog main; 286 template pairs rendered.
  Six stale local README anchors were reconciled to the current headings during this work.
- Image metadata reviewed for 52 PNGs, three ICNS and three ICOs; only generated icons and
  a test fixture are tracked, with no unexpected text metadata. Public secret/tree/history
  scans and final publication evidence are recorded after the candidate checks.

No application installers, private logs, account metadata or historical PR archives are part
of the public source copy. Hosted CI, native acceptance, actual account sign-in and the
unresolved production-release gates are not claimed by these source/documentation checks.
