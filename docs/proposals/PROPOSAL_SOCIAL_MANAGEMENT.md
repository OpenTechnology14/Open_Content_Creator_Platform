# Proposal: Social profile and account management

**Queue row:** `P-062`  
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — OAuth, OS credentials, account selection and publishing gates
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** `Code complete — external acceptance open` — state is authoritative in [`../PROPOSALS.md`](../PROPOSALS.md)  
**Owner:** OpenTechnology14 + agent  
**Date:** 2026-09-10  
**Roadmap layer:** Social Management  
**Evidence level:** Local contract verified; provider acceptance pending

## 1. Executive summary

Add one shared `Content` + `Stream` module that binds a named creator profile and approved brand
logo to platform accounts. It exposes a reusable profile/provider dropdown, keeps OAuth tokens in
the operating-system credential manager, verifies the returned account, and requires an approved
job plus its exact ID before a post, upload, or live destination can be created.
Five starter profiles ship in Git; validated custom profiles live in private local state and join
the same dropdown without replacing the starters.

## 2. Verified current state

`configs/local/stream-programming.yaml` already defines OpenTechMarketing, Video Review, and three
agent-game profiles. Automation Control can compile a private YouTube draft, but deliberately sets
`upload_enabled: false`; it owns no reusable platform identity, OAuth tokens, or publishing adapter.
Marketing Crosswalk generates source material and does not own external account credentials.

## 3. Problem, goals, and boundaries

Creators need to select the same profile, logo, and connected account for both live shows and
generated content. The module must make provider capability differences visible, support multiple
accounts without placing tokens in repository or public state, and retain a manual review boundary.

The first adapter set is YouTube account verification, video upload, and live preparation; Twitch
account verification and live ingest lookup; X account verification and text posting; and Discord
channel selection plus announcement posting. TikTok, Instagram, Facebook, LinkedIn, Bluesky,
Mastodon, Kick, Rumble, Trovo, DLive, and Restream appear in the catalog with honest
registration-required or planned states. Discord Go Live remains a manual client screen-share flow
and is not presented as an OBS ingest destination. Completing the other developer reviews and
adapters stays open. Marketing generation remains in `marketing-crosswalk`; OBS control stays in
`automation-control` and `creator-experience`.

## 4. User paths and states

1. Run the loopback profile picker and choose a profile, logo, platform, and purpose.
2. If the provider is available and its client environment variables exist, complete OAuth in the
   provider's own page. The callback rejects wrong or expired state.
3. The module verifies the provider account, writes the token to Keychain/Credential Manager, and
   persists only redacted account metadata.
4. A caller builds a private-by-default job. External execution requires `approved: true` and the
   exact job ID as confirmation.
5. Expired access tokens refresh through the provider and update only the vault. Disconnecting deletes
   both the vault entry and public metadata. Reconnect UI, scheduling, and account health alerts are
   subsequent slices.

Missing developer registration disables Connect and links to provider setup. Network and provider
errors leave existing connections intact and do not claim success.

## 5. Architecture and data flow

The committed catalog and logos are local. OAuth opens in the system browser and returns to a
loopback-only callback. Client registration values come from environment variables; access and
refresh tokens go to the OS credential manager under `HybridCreatorPlatform.social`. The public
connection file is atomic, mode `0600` on Unix, and contains identity/scopes/timestamps only.

Automation Control and Content Creation consume public profile/job contracts. The live ingest
destination is returned only to the caller and must be passed directly to OBS; stream keys are not
persisted or logged. Provider API traffic is the only cloud dependency.

## 6. Direct injection map

| Location | Change | Verification |
|---|---|---|
| `modules/social-management/catalog.yaml` | Profiles, logos, providers, capabilities | Catalog/reference tests |
| `social_management/oauth.py` | OAuth state, PKCE, scoped authorization | State/expiry/permission tests |
| `social_management/connections.py` | Token exchange and provider identity verification | Mock-provider tests |
| `social_management/vault.py` | OS-vault tokens and redacted atomic state | Secret-absence/mode tests |
| `social_management/jobs.py` | Approved publishing and live adapters | Approval and request-shape tests |
| `social_management/ui.py` | Loopback profile/brand/provider dropdown | Contract and Mac UI acceptance |
| `apps/shared/social-manager` | Fixed Tauri bridge, compiled catalog/logos, loopback service launcher | Rust tests + desktop builds |
| `apps/shared/ui/SocialManagement.svelte` | Shared Stream/Creator native picker and redacted account list | Svelte checks + Mac UI acceptance |
| `apps/shared/ui/ProfileSwitcher.svelte` | Persistent Stream/Content workspace and per-profile account route (P-065) | Rust persistence + Svelte checks |

## 7. Contracts

Catalog schema version 1 defines `brands`, `providers`, and `profiles`. Connection records contain
no credential. Publish jobs carry profile, provider, connection, brand, capability, content,
visibility, AI-generated marker, approval, and creation time. Unknown fields and cross-references
fail validation.

## 8. Security, privacy, accessibility, and observability

The UI binds only to loopback, labels every selector, exposes provider readiness, and announces
status changes. OAuth sessions expire after ten minutes and use PKCE where supported. Tokens,
authorization headers, stream keys, and upload URLs must never enter logs, Git, job files, or public
connection state. Public publishing remains a human approval action even when content is generated
automatically.

## 9. Test and pressure matrix

| Scenario | Expected result | Evidence |
|---|---|---|
| Load profiles/logos | Every reference resolves | Offline test passed |
| Wrong/expired OAuth state | Rejected, session retained | Offline test passed |
| Token storage | Secret only in injected vault | Offline test passed |
| Unapproved post | No provider request | Offline test passed |
| Exact approved X post | One correctly scoped request | Offline test passed |
| Exact approved Discord post | OAuth webhook request with mentions disabled | Offline test passed |
| Twitch live handoff | Account-bound key returned, not stored | Offline test passed |
| Real provider connect/post/live | Correct account and remote result | Manual, pending credentials |

## 10. Delivery plan

Phase 1 is the catalog, dropdown UI, four provider adapters, credential separation, approval gate,
tests, and module/setup documentation. The desktop portion of Phase 2 now wires the shared picker,
bundled logo previews, service startup, browser consent launch, and redacted account list into both
Tauri apps. P-065 adds always-visible active workspaces, restores each profile's last
brand/provider/capability/account route, and adds reconnect plus confirmation-gated disconnect;
remote account-health probing remains open. Phase 3 adds approved providers after developer
registration, scheduling, analytics, and the future mobile review surface.

## 11. Rollout and rollback

Nothing connects until the user runs the module and supplies provider app credentials. Removing the
module does not affect stream planning. Rollback deletes its local public state and corresponding OS
credential entries; remote posts are outside local rollback and therefore keep the approval gate.

## 12. Risks and unresolved decisions

Provider review, quotas, channel eligibility, and API pricing can block individual capabilities.
Each remains a per-provider state rather than a platform-wide failure. Final account ownership,
profile naming, and default publication visibility are owner acceptance items.

## 13. Documentation updates

Update the roadmap, deviations ledger, module index/setup order, both agent module matrices,
subfeature checklist, acceptance/use-case coverage, environment example, root context files, setup
catalog, and proposal queue.

## 14. Channel portfolio and AgentWorkflows controls — 2026-10-31

**Work registration:** P-062 / channel-portfolio; Kind: proposal remainder; state: local editorial slice verified; adoption/provider acceptance open.
**Verified against:** main `a19f9b3`, 2026-10-31. **Assignment:** retain Sol/xhigh above;
the current client does not expose a model switch, so this records the assignment rather
than certifying execution. HF considered: source-summary drafts may fit later, but account
routing and approval transitions need capable review; availability unverified, no dispatch.

**Owner request:** build social account management connected to Agent reporting and the
AgentWorkflows repository; one OpenTechnology YouTube channel for all project walkthroughs,
a separate AI-produced content channel using Blog concepts with owner concept approval,
and one or more gaming channels. The owner clarified that the other repository is
AgentWorkflows, not OpenTechnologyApp. This authorizes the local implementation and workflow
connection; the existing final publishing gate remains in force. Channel creation, real
OAuth consent and public uploads are not performed by this slice.

### Scope and first slice

Extend this existing module, with configuration-owned channel purposes and a private local
editorial queue. AgentWorkflows supplies the idea-generation/review/reporting procedure;
the platform owns account bindings and durable decisions. Blog and registered marketing
modules supply evidence, Content Creation renders media, and existing Social publishing
owns remote actions. No second coordinator or duplicated marketing registry.

| Channel purpose | Initial routing | Editorial scope |
|---|---|---|
| OpenTechnology | Existing OpenTechMarketing profile | All eligible project walkthroughs, grouped by project/playlist |
| AI content | Existing Main Content profile | Original explainers, experiments and stories inspired by selected Blog sources |
| Gaming | Existing Main Stream profile; configurable additional channels | Existing gaming shows, sessions and highlights; no new gameplay autonomy |

These are logical channel definitions, not created or connected YouTube accounts. A binding
must select an existing verified YouTube connection with the matching social profile; separate
logical channels must not accidentally share the same remote YouTube channel.

### Contracts and injection map

| Proposed location/surface | Change | Verification |
|---|---|---|
| `configs/local/social-channels.yaml` (new) | Versioned purpose/profile/source configuration, no credentials | Catalog references and duplicate rejection |
| `social_management/editorial.py` (new) | SQLite queue, source references, revision-bound decisions, binding checks and report | Persistence, stale decisions, routing, concurrent update and edit invalidation contracts |
| `social_management/editorial_cli.py` (new); existing CLI | Agent-operated channel, concept, decision, brief and report commands | Real CLI round trip, error and restart tests |
| Module README/setup | Platform adapter for AgentWorkflows; exact commands and limitations | Docs/link checks, generated registry |
| AgentWorkflows public workflow/template/package | Generic content idea → review → production handoff → reporting procedure | Its package verifier and unit suite; synthetic examples only |

Concept schema version 1 records channel, title, audience, hook, original contribution,
outline, format, source repository/revision/path, and source/rights notes. New and edited
concepts await approval; approve/reject/revise decisions require the exact concept ID and
current revision, an actor label and the owner's decision text. Changes invalidate approval.
SQLite transactions serialize mutations and retain a separate event history. Approval grants
a production brief for that revision only; it never constructs an approved PublishJob.
Reports expose editorial state and connection readiness without tokens or account IDs.
No new service, HTTP endpoint, paid model call or scheduler is introduced.

### User paths, failure and recovery

First run lists unbound configured channels and an empty private queue. An agent reads
selected Blog/marketing sources, submits a bounded set of concepts and presents short cards.
The owner approves, rejects or asks for revisions. An approved concept produces a versioned
production brief for the existing content pipeline. Missing OAuth blocks account-bound work,
not concept drafting. Unknown channels, invalid inputs, stale revisions and mismatched
connections fail without changing state. Offline drafting/review/reporting remain usable.
Retry with the current revision after reading back the record; repeated stale decisions
do not apply twice. Reject/revise cancels editorial permission, not an already running
renderer; the facilitator separately uses that renderer's existing cancellation controls.
Restart reads committed state; an unreadable database reports an error rather than reset.

### Approval and acceptance boundaries

CT-D19 remains pending: approve concepts then review finished videos (existing gate), or
explicitly authorize an automatic publishing policy. Unanswered means no policy change.
Gaming channel count/names can be configured later; one initial gaming channel is an agent
recommendation, not a decision to merge existing identities. Real account bindings retain
ST-D03 and existing P-062 live acceptance. Walkthrough runtime remains P-067, whose open
PR #65 must not be duplicated. Discovery-only marketing modules remain ineligible until
their own promotion requirements pass.

For growth, evaluate ideas by audience, hook, originality and production effort; measure
views, watch time and subscribers only from observed results. No analytics collector or
growth result is claimed. YouTube's [monetization policy](https://support.google.com/youtube/answer/1311392)
requires original, authentic content; its [video contract](https://developers.google.com/youtube/data/reference/rest/v3/videos)
supports disclosure of realistic altered/synthetic media. Recheck these at publishing time.

### Verification and rollback

Required: Python-in-a-module matrix row (`make test`, Ruff and real CLI input); focused
editorial persistence/approval/routing tests; documentation parity; AgentWorkflows build,
verification and tests. Native apps/provider adapters are unchanged, and their existing
live/macOS/Windows acceptance is not newly claimed. Record actual results below after execution.
Rollback removes the CLI integration/config and workflow reference; retain the private
database/history for export. No remote content is created, removed or rolled back.

**Next implementation brief v1:** build the bounded interfaces above on the isolated task
branches, preserve existing profile/OAuth/publish contracts, validate with synthetic state,
then generate a review/acceptance brief from the actual diff. No worker dispatch implied.


### Channel-portfolio verification — 2026-10-31

- **Verified:** `python -m pytest tests/social_management -q`: 31 passed, including
  simultaneous revision decisions, restart/history, stale approval, edit revocation,
  configuration changes, pause, invalid inputs, binding separation and report escaping.
- **Verified:** malformed channel YAML initially raised a parser traceback; a new regression
  test failed before the fix and passes with a concise error and no created state.
- **Verified:** all 20 explicit ValueError guards in the new editorial/CLI files were
  independently disabled; every mutation made the focused suite fail. Original sources
  were restored before subsequent verification.
- **Verified:** `make test` with the prepared CI-dependency Python environment reached
  100%, exit 0. Three existing skip markers remained; no live/provider acceptance claimed.
  The first run found CT-D19's missing required Question marker; it was corrected and the
  full suite rerun successfully.
- **Verified:** `python -m ruff check modules/ scripts/ tests/social_management`,
  `python3 scripts/testing/generate_docs.py --check`,
  `python3 scripts/testing/proposal_report.py --check --summary` and `git diff --check` passed.
- **Verified:** separate-process CLI submit → explicit synthetic approval → brief → edit →
  stale-decision rejection → history succeeded in temporary state. Brief publication
  permission stayed false. No provider/model call occurred.
- **Verified:** the private local adapter invoked the real CLI from its configured working
  directory and read three channels and three Blog-inspired concepts, all awaiting approval.
  Every channel remains unbound; the concepts are agent suggestions, not owner decisions.
- **Verified:** companion AgentWorkflows `scripts/build.py`, `scripts/verify.py` (111 local
  links) and 14 packaging unit tests passed. Private reporting verifier passed 10 projects,
  849 source records, 501 snapshots and 695 local links. Source/runtime provenance is intact.
- **Not run/built:** real channel creation/OAuth/provider actions, native/Windows acceptance,
  automatic renderer invocation, live analytics and unattended publishing. Existing desktop
  controls and provider adapters were not modified. Public workflow/installed-reporting
  adoption remains a release step; writing task-branch files is not coordinator delivery.

**Next review/acceptance brief v2:** inspect this concrete local diff and the companion
workflow/reporting changes, preserving the existing coordinator and foreign worktrees.
Present the saved concepts from current private state; apply only actual owner answers
with exact revisions, then prepare the existing production pipeline's bounded brief.
Keep CT-D19 pending and existing publication approval. Recheck media/voice/source-rights
prerequisites before production; no paid fallback, provider action or merge inferred.
HF source-summary drafting may be considered with one attempt/capable review; availability
remains unverified. Return evidence and the next real owner choice, not a new backlog.

## 15. Owner account preparation — 2026-11-01

**Work registration:** P-062 / account-setup-guide; Kind: proposal remainder; state: documentation verified; owner account checks pending.
**Assignment:** inherited Sol/xhigh; documentation of credential and provider boundaries
retains capable review. No client model switch or worker dispatch claimed.

**Owner request:** create user setup steps for accounts, including apps not implemented,
password management and agent access, so accounts can be tested and signed into again.
Scope: one canonical all-provider setup guide, a blank private-readiness template, links
from setup/editorial and private reporting, and corrections to misleading setup wording.
No account creation, sign-in, credential access, provider action or adapter implementation.
Account preparation does not answer CT-D19 or change the final publishing gate.

**Source finding:** Trovo's official March 26 announcement ended live streaming on
June 30, 2026. Its existing catalog row is stale for live onboarding; document recovery-only
handling and retain the explicit service blocker. No provider status is promoted by this work.
See the [official notice](https://support.trovo.live/category/8/article/2394).

**Delivered:** [account setup guide](../../modules/social-management/setup/accounts.md) and
[blank private checklist](../../modules/social-management/setup/account-readiness.template.md),
linked from module/manual/editorial setup and private reporting. A blank private note was
created outside Git without filling any account result. The guide distinguishes browser
sign-in, cached app metadata, OAuth consent, actual acceptance and assistant tool permissions.
Existing setup wording now describes process-environment injection, YouTube Data API live
resources and Twitch's potentially public testing correctly.

**Verified — 2026-11-01:** `python -m pytest tests/docs -q -o addopts=''`: 1,026 passed;
`python3 scripts/testing/generate_docs.py --check` and
`python3 scripts/testing/proposal_report.py --check --summary` passed. An explicit catalog
coverage/local-link check found all 15 providers in guide and template and 31 valid local
links/anchors in the initial check; the final check passed all 33 including delivery links. Private reporting's
`python3 scripts/verify.py` passed 695 local links and preserved source/runtime provenance.
`git diff --check` passed. Applied the owner documentation-only verification exception:
no full runtime/native suite, real sign-in, secret inspection, provider action or acceptance
claim. Module/adapter status is unchanged.

**Next acceptance brief v3:** read this guide and current private account readiness, retain
P-062 ownership and existing coordinator, guide the owner through the first incomplete step
for their selected account, and record observed label/date/device/results only. Owner enters
credentials and consent; recheck provider/adapter availability before connection. Preserve
unanswered CT-D19, the separate final publishing gate and all pending live/Windows acceptance.
No external test, spend, runtime change or dispatch is inferred from this documentation task.

## 16. Private account matrix — 2026-11-01

**Work registration:** P-062 / private-account-matrix; Kind: proposal remainder;
state: private matrix delivered and checked; inherited Sol/xhigh. Owner requested a matrix to store
account information and potentially passwords, alongside a private/public repository split.

Deliver an editable private account matrix with all provider/destination rows, identity and
sign-in fields, recovery/MFA readiness, password-manager references, app scopes and agent
access boundaries. Use the password manager/OS vault for secret values; a private Git repo
does not make plaintext passwords appropriate. The matrix itself is excluded from the public
export, including later filled account metadata. No credentials are read or invented and
no account is marked ready without observed evidence. This is a private repository document,
not a new desktop matrix editor or password vault.


Matrix verification: 17 account identity rows and 17 security/access rows cover all 15 catalog
providers. All actual values/results remain blank or not checked. P-075 owns exclusion and
public-export verification. The private matrix is linked from the private README and account
setup guide; those marked private-only links are removed during public export.
