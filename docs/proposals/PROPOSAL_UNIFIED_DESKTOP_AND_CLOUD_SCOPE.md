# Proposal: One desktop app for Stream Extend and Creator Extend

**Queue row:** `P-072`
**Agent model / effort:** `gpt-6.1-sol` / `high` — Desktop consolidation, migration contracts and staged cloud scope
Model assignment: [queue assignment](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — Testing; private combined desktop includes OBS observation/scenes/mute and recovery; managed recording is fenced on unresolved atomic Stop safety. Remaining workflow parity and final native acceptance are open; migration, public release and replacement retain gates. State is authoritative in [the queue](../PROPOSALS.md).

### Round3 acceptance and normal integration — 2026-11-06

**Kind:** proposal remainder / documentation reconciliation, including **P072-R3-01**, the
nonblocking P3 lane wording finding. **Model:** `codex / gpt-6.1-sol / high`, inherited from
the canonical P-072 assignment for evidence/lane/approval consistency; same sole writer, no override.

Independent round3 **approved the bounded R2 repair and R1 containment** at exact source
`abaf6a49e34c97c9d38e59ef07beb37126b2b8e6`. The parent independently confirmed all eight hosted
checks passed for that head, marked PR94 ready and normally merged it as
`aa24e8bf46e0442e8faadc74ad997e7e9e1ba893` (private development evidence; not distributed)
at **2026-11-07T01:39:24Z** (November 6 local). The full independent record is retained privately
as `artifacts/p072-review-r3-20261106/REVIEW.md`; no old CI/review result is attributed to this
subsequent docs-only checkpoint.

| Finding | Current disposition |
|---|---|
| P072-R1-01 | **Unresolved; containment accepted and integrated.** Native managed Start/destructive Stop remain unavailable. Source-only ABI research proposes an upstream dependency; it is not an accepted runtime implementation or atomic/native proof. |
| P072-R1-02–05 | **Bounded repairs accepted** at cb9 by round2, retained by round3 and integrated through PR94. Full/native feature acceptance remains open. |
| P072-R2-01 | **Accepted** by independent round3 at abaf6a4 and integrated in aa24e8b. Observation-bound endpoint/context admission and safe UI recovery are the accepted scope. |
| P072-R3-01 | **Wording corrected in this docs checkpoint, pending docs review.** CT-R15's state now names the R1-01 atomic-contract block, remaining Shorts desktop adapter and actual native repeat. No recording capability is enabled to match prose. |

P-072 stays **Testing, not Done**. P067 Accepted §18/exact ORCH assignments, CT-A01 bounded
resolution and CT-D09 OpenTechnologyApp selection remain. Independent ORCH04 export source is
not integrated by this change. Real OBS/playable output, native GUI/vault/CSP, Windows, migration,
resources, rollback, convergence and release gates (including PL-D10–13 and ST-D07) remain open.
The private `P072-ATOMIC-OBS-CONTRACT-v1.md` source study is now complete as research; its proposed
ABI/patch/IPC route still needs independent engineering review, implementation and native proof.
No plugin, Go Live, account, credential migration or release work is included here.

The dated pre-review checkpoints and briefs below remain historical evidence. Their pending or
unaccepted wording is superseded only for the repair dispositions stated above; their NOT RUN
native/output/acceptance limits remain. Next is parent review of this narrow docs reconciliation
and the separate private ABI route, with no repeat owner continuation question.

**This docs-only checkpoint:** base `aa24e8bf46e0442e8faadc74ad997e7e9e1ba893`;
prepared Python `-B -m pytest tests/docs -q -o addopts='' -p no:cacheprovider
-p scripts.testing.no_skips` — **1,021 passed**, including model, link, lane and decision checks.
Blocking Ruff 0.6.4 on `modules/ scripts/ tests/docs`, generated-doc check, proposal report
(`lane_missing=[]`, `lane_extra=[]`), whitespace and conflict-marker checks pass. CT-R15 changes
only its state cell; CT-A01/CT-D09, P067/ORCH and all other queue rows are unchanged. Runtime/test
delta against the actual main base is empty; runtime tree-object SHA256 remains
`f704ca6296c7e36fc7534c09591a115d7708d83d0417853366574e38e9f6c5fd`.
**NOT RUN here:** product/native/full offline builds/tests, GUI/output/vault/CSP/Windows/migration
and release acceptance; this proportional documentation pass does not repeat unchanged runtime
suites or claim old CI as new-head evidence. The new docs PR records its exact commit and checks.

### Round-2 review repair — P072-R2-01 — 2026-11-06

**Kind:** bug / Security + UI / P2. **Model:** `codex / gpt-6.1-sol / high`, inherited from the canonical P-072 queue for native endpoint/context admission and safe recovery. Same writer/branch, current clean source `cb76111be24dc2e0ee7c3b3faeb21ba7d3da4494`; no override, HF or spend. Independent round2 reviewed frozen `cb9d22412dc3948bc2860349a22fbfbe9ce045d8` and returned **REQUEST CHANGES**. The subsequent cb76111 normal docs merge preserves PR96 Accepted §18/ORCH model table and CT decisions; its runtime tree is identical to cb9.

Round2 **accepted R1-02–05 repairs** and **R1-01 containment only**. R1-01 remains unresolved/unavailable; native managed Start/destructive Stop fences stay. This acceptance does not complete P-072 or real/native output criteria. Prior dated pending-review entries remain historical.

| Finding | Evidence / disposition |
|---|---|
| P072-R2-01 | Audio/scene observed on A at `0:idle`, endpoint save changes native context to `1:idle`; old `session_id=null` passes generation admission and mutates B. Reviewer executed actual trusted handler bodies against two fake WebSocket endpoints; both assertions fail. Browser failed status after saving port 4456 leaves old mute usable with no expected context. **Accepted at abaf6a4 by round3; integrated in aa24e8b:** required observation-bound context and generation, checked under the native mutation lock before lazy settings/vault/network resolution; unique controller-lifetime epoch prevents reconstructed/prior-instance idle keys. Idle context invalidates before settings/credential writes (including ambiguous failure), while safe pinned settings preserve it. UI clears idle observations around relevant saves, pauses idle reads during save, rejects stale completion/action, and requires fresh observations; no mutation retry. Pinned safety and prior repairs retained. |

**Historical R2 handoff, superseded by round3 above:** scope was this bounded finding only. Private pinned-OBS ABI study was saved at `P072-ATOMIC-OBS-CONTRACT-v1.md` and paused; no plugin/Go Live/social/export changes. Parent created fresh exact-head round3 carrying R1/R2 and the docs merge; no owner continuation permission was needed.

#### Historical R2 pre-review verification checkpoint

**Runtime/test commit:** `d28ab8d7053d7dc2f200d33ab20f065409a0ac3a`, parent
`cb76111be24dc2e0ee7c3b3faeb21ba7d3da4494`. Same T3 worktree/branch, verified
`codex / gpt-6.1-sol / high`; no dependency, identity, plugin or legacy-runtime changes.
Evidence is retained privately under `artifacts/p072-r2-repair-20261106` in the installed
project notes. At this historical checkpoint it was **implemented, awaiting independent round3**;
round3 acceptance/integration is recorded above, without overall feature acceptance or Done.

- **Fail before fix:** `endpoint-review.py` executed the cb76111 trusted mute/scene handler bodies
  against two fake OBS sockets: both regressions failed, mutating B after observing A; logs
  `endpoint-repro.log` and `before-run.log`. `browser-before.json` records the enabled old mute
  sending `sessionId:null` without an expected context after port 4456 save/status failure.
- **Temporary reverts / mutations:** 18 valid detections, restored source verified byte-for-byte:
  5 Rust behavioral guards, 11 Node behavioral guards, and 2 compiled native pre-write/admission
  assertions. Native context removal independently fails mute and scene replacement regressions;
  generation, controller lifetime, pinned preservation, observation binding, save/read fencing,
  failure invalidation and public-settings reconciliation also fail when reverted. Compiler errors,
  locator/setup failures and timeouts are excluded. Runners/summaries and each failing assertion
  are retained privately; source hashes and restored passing suites are recorded there.
- `CARGO_TARGET_DIR="$PWD/apps/extend/src-tauri/target" cargo test --offline --locked --manifest-path
  apps/extend/src-tauri/Cargo.toml` — **24 passed**. Same target/flags with the Stream manifest —
  **17 unit + 52 protocol/controller passed**, 1 existing packaged-owner case ignored. The 52
  retain R1 containment/held-read/autoload/abandon coverage and add stale/missing/lifetime contexts,
  same-name A/B, delayed reads/commands, credential/pack rotation and corrupt-settings pinned mute.
- Same locked/offline Creator manifest suite — **44 passed**, 2 existing real Blender/ComfyUI cases
  ignored. Selected shared crates via combined manifest `-p recording-library -p local-settings
  -p tauri-plugin-social-manager` — **3 / 2 / 5 passed**. No ignored live case is claimed as passed.
- `npm --prefix apps/extend test` — **29 passed**; all three apps' `npm run check` — **0 errors,
  0 warnings**; all three frontend builds pass. Combined private bundle built with
  `npm --prefix apps/extend run tauri build -- --debug --bundles app -- --locked`;
  executable SHA256 `2ae7f9ad6c820ae23e7ab7b9797796a01660eee87867f40b8ae6d3dc138fd554`.
  Production build scan finds no fixture markers. Existing unused candidate-import/test warnings
  remain; they are not a new managed-recording capability.
- Existing prepared Python environment: no-skip `pytest tests/desktop_apps -q -o addopts=''
  -p no:cacheprovider -p scripts.testing.no_skips` — **24 passed**; full `make test` — **exit 0,
  100%**. Its four collection-skip locations and 15 case skips cover missing FastAPI/asyncpg,
  absent sibling source paths and intentional ComfyUI stubs; one hcp-alerts scaffold xfail remains.
  These do not prove relay/backend/live security. Blocking Ruff 0.6.4, generated/model/lane/docs
  checks pass: **1,045 no-skip docs/desktop tests** (model/lane/link/security declarations),
  `generate_docs.py --check` matches, `make proposal-report ARGS='--check --summary'` reports no
  missing/extra lane IDs; Ruff and `git diff --check` pass. No unresolved conflict markers.
- Rendered T3 synthetic fixture: actual audio/scene handlers send their observation's required
  context; pending save and lost save response plus failed status leave no old controls; fresh B
  restores actions with B's context. Ambiguous save re-reads public preferences, so navigation
  preserves B; unreadable preferences enter existing Retry while pinned safety stays mounted.
  Same-host synthetic credential rotation, released old held audio/scene reads, pinned reload
  with corrupt preferences and independent held-inspection mute pass. At **320×736**, scroll
  width is 320 and Tab/Enter operates the observed mute. No real credential or output is used.
- **NOT RUN:** final native built-in-display smoke: automation returned `cgWindowNotFound` twice;
  bundle-ID selection is ambiguous across three checkouts. Only this task's launched process was
  stopped. Build success is not native GUI acceptance. Real OBS/plugin/atomic generation, playable
  output, Windows, OS-vault/CSP GUI, migration/rollback, accounts, cloud and public release remain
  open. Hosted checks/review are not inherited from older heads.

**Historical round3 brief (completed at abaf6a4; retained below):** P-072 / P072-R1-01–05 + P072-R2-01, **Sol / high**, inherited from the
canonical queue for sensitive native/context safety. Parent creates a new independent round3
task on the exact repair/evidence head, carrying the original R1 and round2 reports/responses.
Verify R2 required observation-bound command fields, lock-before-settings/vault/network admission,
zero B effects for old/omitted/null/reconstructed context, pre-write ambiguity invalidation, fresh
B positive path, delayed read/command ordering, same-host credentials/pack changes and pinned
corrupt-settings safety. Recheck preserved R1-02–05 acceptance and R1-01 containment without enabling
recording; inspect cb76111 docs integration preserves accepted P067 §18/ORCH models/CT decisions.
No plugin, Go Live, exports or source changes in that review; report finite architectural objections
and exact-head CI/NOT RUN. Parent owns review/integration; private ABI study remains pending.

### Recovery authority — 2026-11-06

**Model-label clarification (`P072-MODEL-LABELS-20261106-V1`):** Owner: "Are the work blocks labeled by which model to use?  That should be built into proposal queue already". P-072 / P072-R1-01–05 inherits **gpt-6.1-sol / high** from the [canonical queue assignment](../PROPOSALS.md#agent-model-selection): sensitive native ownership, cross-app controller and safety regressions. Native Codex configuration is verified; no override or recommended Terra/Luna child is selected. Subsequent briefs and review handoffs must state proposal/child ID, model, effort and scope rationale or explicit inheritance. No second registry.

Owner exact instruction: "Did you use T3 for this?  Use T3 to drive this all to completion"
(`P072-COMPLETION-20261106-V1`). The existing coordinator drives review, bounded repair, normal
integration, sequential accepted desktop slices and available acceptance without continuation
permission. This writer's current scope remains P072-R1-01–05 on PR94, not integration or another
feature slice. PL-D10–13, ST-D07 and all release/account/provider/migration gates persist. No new
writer, review delegation or watcher is created here. Surviving edits were inspected on the same
branch at `f7074ab166f0ccb3960a695c85dde01543beb1e2`; `/tmp` evidence/backups were unavailable.
The interrupted audio-inspection lock mutation was present and must be restored; prior mutation
counts and pre-interruption green runs are not evidence of the recovered tree. All five repair
dispositions below remain **unaccepted pending fresh independent review**.

### Review repair v7.1 — 2026-11-01

Owner v7 directs the existing coordinator through review → repair → integration → the next desktop
slice → acceptance without repeat continuation prompts. This sole writer continues on the same
branch/PR94; no new agent, thread, schedule, provider spend or backlog work. Actual model verified
`codex/gpt-6.1-sol/high`; accepted workflow `07f5d729`, with upstream `b70913d` drift unchanged.
Independent review of `f7074ab166f0ccb3960a695c85dde01543beb1e2` returned **REQUEST CHANGES**.
The earlier green tests did not cover these defects; acceptance is not granted by those runs.

| Finding | Kind / bug group / severity | Reproduced evidence and repair disposition |
|---|---|---|
| P072-R1-01 | bug / Security / P1 | Retained ownership boolean lets Stop claim an external replacement, including after uncertain Stop. Reproduced before fix: replacement was stopped and uncertain Stop was sent twice. Continuous witness candidate improves prior replacement/loss/unknown-outcome handling but deterministic after-admission replacement still destroys external output. **Unresolved; containment accepted at `cb9d224` by round2, native managed Start/destructive Stop fenced.** OBS-side atomic-generation contract required. |
| P072-R1-02 | bug / Security + UI / P1 | Pinned status/audio consult corrupt preferences; successful Start ID is discarded before a failed observation. Reproduced corrupt-load/failed-observation identity loss. Implemented lazy pinned resolution, immediate Start reservation receipt, request/context fencing; accepted at `cb9d224` by round2; full feature/native acceptance remains open. |
| P072-R1-03 | bug / UI / P2 | Slow inspection disables safety UI and holds the native controller/cache lock across reads. Reproduced held native mutex and disabled browser controls. Implemented short snapshots, independent read/control sockets, direct per-input mute and separate UI read activity; accepted at `cb9d224` by round2; full feature/native acceptance remains open. |
| P072-R1-04 | bug / UI / P2 | Fresh Start → Library has no automatic audio enumeration/mute. Fresh fixture reproduced zero audio calls/mute. Implemented automatic connection/session audio refresh, one read in flight, stale-context rejection; accepted at `cb9d224` by round2; full feature/native acceptance remains open. |
| P072-R1-05 | bug / Other / P2 | Permanently missing finalized file traps pending handoff; recovery rejects it forever. Reproduced permanent missing-file recovery rejection. Added explicit generation-fenced finalized/inactive abandonment; no second Stop/file mutation; accepted at `cb9d224` by round2; full feature/native acceptance remains open. |

P072-NAV-01/02 remain unchanged. This pass adds no Go Live, creative, cloud, account or migration
functionality. The current bundle identity stays preview. The coordinator generates the next
independent review for the new head; no additional owner permission is needed for these repairs.

### OBS-side completion contract required

**P072-R1-01 is unresolved.** `StopRecord` has no expected output/session field in installed
`obws 0.15.0` (`requests/recording.rs`, `client/recording.rs`). The official
[protocol](https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md#stoprecord),
[record handler](https://github.com/obsproject/obs-websocket/blob/master/src/requesthandler/RequestHandler_Record.cpp)
and [frontend API](https://github.com/obsproject/obs-studio/blob/master/frontend/OBSStudioAPI.cpp)
corroborate a current-output Stop and queued frontend operation. These upstream master sources
were read on 2026-11-06; they are not certification of installed OBS 32.2.2 internals.

Deterministic trace: candidate Start acknowledges/witnesses STARTED → same-socket status confirms
active → fake server receives Stop but holds execution → another controller stops original and
starts replacement → held Stop executes on replacement → app rejects mismatched lifecycle but
`recording_active=false`: replacement already destroyed. The regression failed with
“parameterless StopRecord destroyed the replacement after its admission barrier”. An event
subscription or timecode alone cannot close this gap. Reconnect and unknown mutation outcomes
continue to revoke ownership, never authorize replay.

Native Start is rejected before settings/vault/network access and again by the controller.
Native Stop validates generation and permits **only already-finalized inbox retry**; it sends no
StopRecord for an active/uncertain pin. No race waiver/configuration switch exists. Runtime status
sets `managed_recording_available=false`; UI does not offer a new managed start/destructive Stop
and tells existing pins to finish in OBS then recover inactive. Candidate transport Start/Stop
methods are test-only on the combined controller; candidate tests do not prove product availability.
Observation, scenes, mute, Content readiness/import, inactive recovery and finalized abandonment
remain independent. The original legacy live functions and their existing guard contract are unchanged.

Viable next design (engineering proposal, **not implemented or accepted**):

- An OBS-side vendor ABI returns a random server-epoch plus recording-generation capability only
  for a successful owned Start. It refuses external/pre-existing output and never adopts a PID.
- `StopOwned(epoch, generation, operation_id)` checks the current generation **at execution on the
  OBS output/frontend serialization boundary**, then stops exactly that output or returns stale
  without side effects. A check followed by queuing parameterless StopRecording is insufficient.
  Retain/refcount the exact output or serialize frontend generation validation and stop together;
  prove stop/restart on the same reused output object cannot bypass generation checks.
- Lifecycle changes, splits, output replacement, plugin/OBS restart and observation loss invalidate
  capabilities. Idempotent operation receipts distinguish pre-execution rejection, finalized path,
  and unknown outcomes. Re-query a receipt; never replay a mutation against “currently active”.
- Reuse `plugins/obs-plugin` only after source/ABI review against pinned OBS/obs-websocket versions
  and supported Mac/Windows architectures. No plugin installation or implementation in this pass.
  Require authenticated local vendor calls, per-owner capabilities, strict schemas/bounds, no secret
  logging or public listener, no generic script/command endpoint, trusted-native IPC and CSP denial.
- Prove interleavings with fake and real OBS-side tests: replacement before check, between check and
  queued execution, after execution, stale/duplicate receipts, disconnect/restart/lag, split, stop
  failure and unknown outcomes; zero external Stop and zero wrong-profile/path attribution.
  Packaging must verify artifact/source hashes, plugin/version handshake, absence/incompatible-plugin
  admission denial, installation/upgrade/uninstall/rollback, and native ABI on each claimed OS.
  Only then run isolated synthetic real recording → playable picture/audio → exact owned Stop →
  shared Library attribution/navigation/recovery on built-in MacBook display; Windows remains separate.

The parent owns the next engineering route under existing completion authority. No owner safety
waiver or duplicate recorder is requested. `P-067-ORCH-03` (future Sol/high override in accepted
PR96/7731fc3 §18) must reuse this controller boundary. ORCH01 may read interfaces; this repair does
not broaden into Go Live or the new orchestration implementation. Preserve PR96's canonical changes
when integrating; this branch changes only its existing P-072 records, not P-067's queue state.

### Recovered repair verification — 2026-11-06

**Source commit:** `1e5b689723a2bbe7154905e55a9dd080ead8913e`; review baseline
`f7074ab166f0ccb3960a695c85dde01543beb1e2`; preserved integration base
`ab2bc473030bbfbb35e8c40a1d13f2cd6a844fd5` / main
`a19f9b32e78ead7a8d57ff039f592139681e988f`. Same isolated branch and PR94, no reset/rebase.
Native configuration `codex/gpt-6.1-sol/high`. R1-01 is **unresolved/contained**, not repaired
managed-recording capability; R1-02–05 are **implemented/unaccepted pending independent review**.

- `CARGO_TARGET_DIR="$PWD/apps/extend/src-tauri/target" cargo test --locked --manifest-path
  apps/extend/src-tauri/Cargo.toml` — **24 passed**. Includes actual corrupt preference JSON with
  pinned lazy resolution; disabled idle pack/vault admission and independent real fake-HTTP Content
  readiness remain tested. Native origin/window rejection and unsafe preference guards pass.
- The same target with `cargo test --locked --manifest-path apps/stream-extend/src-tauri/Cargo.toml`
  — **17 unit + 45 protocol/controller passed**, existing packaged Python-owner test ignored.
  The 45 include runtime no-network Start denial and no-Stop replacement protection. Other recording
  transport cases call explicit **test-only candidate** methods; they do not claim product availability.
- Locked Creator suite — **44 passed**, existing real-Blender and selected-ComfyUI cases ignored.
  Shared suites through the combined manifest with `-p local-settings -p recording-library
  -p tauri-plugin-social-manager -p tauri-plugin-module-setup -p relay-client` — **2/3/5/23/5 passed**.
  Locked standalone `apps/shared/setup-engine/Cargo.toml` — **7 passed** using its existing ignored
  lock. An initial attempt to select setup-engine via `-p` was rejected because it is not a workspace
  member; standalone locked verification replaces it. No existing package versions were upgraded.
  OBS's events feature requires `futures-util` and locked optional `tokio-stream 0.1.19`.
- Each of `apps/extend`, `apps/stream-extend`, `apps/creator-extend`: `npm run check` — **0 errors,
  0 warnings**; `npm run build` — exit 0. Combined `npm test` — **18 passed**, including fresh audio,
  failed status/receipt identity, before/during-Start old status, held inspection, one read in flight,
  duplicate mutation, reload before preferences and disabled idle observation. An initial fixture
  DTO type omission was corrected; final checks/build pass. Production build contains no fixture
  call-log/banner/native-pin/synthetic-session markers.
- `make test` with the existing prepared Python environment — **100%, exit 0** (15 skip markers,
  one expected-failure marker; not live acceptance). `ruff 0.6.4 check modules/ scripts/` — clean.
  `python3 -m pytest -p scripts.testing.no_skips tests/desktop_apps -q` — **24 passed, zero skips**.
  No-skip `tests/docs tests/desktop_apps` also passes. Generated-doc check, proposal/lane report
  (zero missing/extra IDs) and `git diff --check` pass. Private release hygiene guard: zero failures,
  existing two owner-set contact placeholders remain pending; not release approval.
- An extra no-skip docs/design/native run initially failed on six optional sibling-source observations.
  Read-only environment pointers verified five; Job-Hunter's pinned `8f9b4f2` is absent from the
  available checkout, so that one observation is **NOT RUN**, not passed. No foreign fetch/edit or
  token adoption. Ordinary docs/design run passes with the declared skips; the required native
  admission lane is independently no-skip. Aggregate `make verify` is only planned with `--list`,
  not claimed executed; separate cloud/backend service CI lanes are not rerun locally for this slice.

**Regression/revert evidence:** [protocol tests](../../apps/stream-extend/src-tauri/tests/obs_contract.rs),
[client tests](../../apps/extend/tests/production-client.test.js), native unit tests and desktop
admission contracts are committed. Local logs/runners are retained beside this worktree in
`p072-repair-evidence-20261106` (private evidence, not a repository dependency).

| Finding | Executable failing counterfactual / temporary revert | Restored result |
|---|---|---|
| R1-01 | Reused the `f7074ab` adapter body with only test type adaptation: external replacement is stopped; uncertain Stop is sent twice. New deterministic after-admission replacement also fails against the witness candidate. Removing native Start/Stop fences fails the runtime regressions. | Runtime Start sends zero requests; destructive Stop sends zero StopRecord. Candidate continuity does not close the architectural gap. |
| R1-02 | Eager load before pin fails corrupt-load regression; dropping Start receipt or status epochs fails client identity cases. Reload bootstrap failed before its fix and fails again when reverted. | Pinned access, failed observation, receipt/epoch and reload tests pass; idle admission stays native-gated. |
| R1-03 | Restoring held native inspection lock fails the deterministic held-read safety test; making inspection use the UI mutation flag fails the client test. | Held fake audio waits on explicit synchronization while per-input mute and candidate Stop dispatch on separate sockets; stale read rejected. Runtime Stop remains fenced. |
| R1-04 | Removing automatic audio calls fails fresh connection/Start regression; removing single-flight guard fails bounded-read test. | Fresh fixture Start → Media Library has one automatic audio call without manual inspection; mute visible. |
| R1-05 | Restoring unconditional pending rejection fails missing-file abandonment. Removing generation/finalized/inactive guards fails their cases. | Runtime pending retry never sends another Stop; inactive explicit abandonment preserves original profile note, releases preferences/new session reservation, rejects stale generation and leaves manual import validation intact. |

**Mutation accounting:** 28 failing executable revert/mutation runs, including repeat checks after
containment; all source restored in `finally`, then suites/bundle rerun. Do not count the old
missing-comma compiler error, early recovery compiler-invalid attempts, a duplicate-test timeout,
or two surviving isolated termination mutations (other loss guards still revoked). The duplicate
case was changed to resolve both promises and assert actual dispatch count, then caught the guard
removal. The broader executable termination-revocation mutation was caught. Machine-readable
summaries and per-run logs distinguish every excluded result; no compiler error is a caught guard.

**Browser/native:** final fresh synthetic T3 fixture passes Start receipt + failed status, automatic
safety audio after Start → Library, held scene/audio reads with dispatched mute/Stop, missing-file
handoff with exactly one Stop and keyboard abandonment, and reload with corrupt preferences +
pinned inactive recovery using the right generation and zero Stop. At **320×736**, abandonment
and recovery work by Enter and no horizontal overflow is observed. Native unavailable recording
fixture offers no managed Start/Stop. This is IPC mocking, not real output acceptance.

`npm --prefix apps/extend run tauri build -- --debug --bundles app -- --locked` — private Mac app
built and reopened on the built-in Retina display. Unknown status/audio are honest, managed Start
is absent, blocked/manual guidance is visible, and status remains across collapsed Production →
Media Library navigation. Existing profile selection/ledger only observed; no profiles, secrets or
media were changed/imported. Binary SHA-256:
`bd9896273b64632d5fab5f6130a3e4310509c1141b274db1f94b2d592d49ed54`.
One unused candidate-export warning remains; no build failure. App and test server/tab closed.

**NOT RUN:** real OBS outputs/atomic-generation plugin/encoder/playable picture/audio/handoff,
real native recovery with output, Windows/clean-host/signing/vault persistence/migration, actual
CSP enforcement/crafted native origin GUI probes, real relay/account/publish/live/provider work,
resource/convergence/rollback and public release. Existing ignored tests remain ignored. No feature
acceptance, module promotion or Done. U-01–U-13 remain exact open evidence; U-10–U-12 cloud stays out.

**Next independent review brief:** P-072 / P072-R1-01–05, `gpt-6.1-sol / high` inherited from the
canonical queue for adversarial native/controller/security review. Parent creates a **new** round-2
`delegate_task` for the final PR head; original REQUEST CHANGES at `f7074ab` remains evidence.
Read this five-finding table, source commit and exact current PR head. Review containment of R1-01
(no managed Start/destructive Stop or fallback), and R1-02–05's pin/reload/unknown-state, read/mutation
concurrency, auto audio, generation and finalized inactive abandonment. Reproduce the committed
regressions and inspect source, not green counts alone. Return each finding's disposition and finite
architectural objections; never accept managed recording from the witness candidate. No source edits,
new worker, real OBS output or owner race waiver. After review the parent drives normal gated
integration and the OBS-side engineering route/independent desktop work under existing authority.

### Owner v6 desktop authorization and recording-first slice — 2026-11-01

**Kind:** feature (existing P-072); **State:** implementation authorized. The owner explicitly
authorized completing the combined desktop product beyond navigation-only preview before the
convergence checks finish. Actual release/replacement, paid providers, live account publishing or
streaming, and credential/account migrations retain their gates. This supersedes the earlier
preview-only development limit, not final acceptance. **Agent:** `codex` / `gpt-6.1-sol` / `high`,
verified in the task's native T3 configuration. HF/OpenCode is not used: disabled and unsuitable
for sensitive ownership orchestration. Sole implementation worker reports to the installed coordinator.

This bounded slice implements local recording, scene switching and per-input mute through the
existing Stream OBS adapter, with a native root controller, pinned source/content profile IDs,
connection and in-memory ownership, shared inbox registration, and persistent visible safety controls.
Go Live transport is deliberately deferred to the next controller slice: the legacy live-start
failure/cleanup path needs separate regression evidence before reuse. No live account is exercised.
Unconfirmed recording starts require explicit OBS inspection and inactive-output recovery; they never
adopt an externally observed recording. Restart never restores ownership or adopts a PID.

Source base is `ab2bc473030bbfbb35e8c40a1d13f2cd6a844fd5`, one sidebar commit above
`a19f9b32e78ead7a8d57ff039f592139681e988f`. The clean isolated task branch was moved from
`5d3e87e8017bf38aa710e2a423f83d45c1197bb5` only after native binding/configuration inspection.
The installed guide is read from the prepared coordinator checkout because absent here. Its accepted
workflow reference checks as upstream-drift (`07f5d729` versus `b70913d`); root work-type/entry-gate
links at `9495bfb6` remain unavailable. Foreign references are not repaired by this feature.

Refreshed registrations at this base: **31 Stream + 42 Creator command entries**, 15 shared
names / 58 distinct commands; combined base has 15 entries, extended to 24 by this slice (including explicit finalized abandonment).
Autopilot nested registrations count as entries. This supersedes the historical phase-0
27/42 count below without rewriting its dated evidence. Source-present does not mean accepted:

| Accepted legacy workflow / source | Existing evidence and limits | Combined state / remaining or blocked |
|---|---|---|
| Shared module selection/install/retry/guides — [setup plugin](../../apps/shared/setup-wizard/src/lib.rs) | P-003/P-063 Mac setup evidence; physical Windows/capture remains open | Combined shared setup present; native/clean-host acceptance remains U-01/U-02 |
| Saved connections and readiness — [Stream registry](../../apps/stream-extend/src-tauri/src/lib.rs), [Creator registry](../../apps/creator-extend/src-tauri/src/lib.rs), [local settings](../../apps/shared/local-settings/src/lib.rs) | P-003 isolated public/vault contracts; provider/device readiness needs actual runs | Combined isolated preferences/vault and independent pack readiness present; R1-02 pins safety access through corrupt preferences; no migration |
| Optional setup sync — same native registries and [setup engine](../../apps/shared/setup-engine/src/lib.rs) | P-003 loopback contract; hosted sync separate | Combined sync explicitly unavailable; cloud authorization still separate |
| Stream/Content profile selection and remembered routing — [social manager](../../apps/shared/social-manager/src/lib.rs) | P-065 synthetic profile persistence; account/provider acceptance open | Combined separate selections present; native recording snapshots their real IDs; no account migration |
| OBS status and existing-scene switching — [OBS adapter](../../apps/stream-extend/src-tauri/src/obs.rs) | P-055/P-063 fake protocol; picture/audio/native scene acceptance open | Combined real status/scenes present; R1-03 independent inspection sockets; source editing still missing |
| Managed Go Live + Record / ordered Stop / handoff — same adapter and [recording library](../../apps/shared/recording-library/src/lib.rs) | P-065 ownership/request order; ST-R05/ST-R06 real handoff remains open | Combined Go Live missing; managed local Start/Stop fenced on P072-R1-01; not managed-live parity |
| Local recording / input mute — [continuous local owner](../../apps/stream-extend/src-tauri/src/obs_local_recording.rs), [root controller](../../apps/extend/src-tauri/src/production.rs) | Fake lifecycle and safety cases; no actual encoder/media quality acceptance | Status/scenes/mute operational; managed local Start/Stop blocked, witness candidate test-only. R1-04 auto-loads audio; atomic proof then real U-04/ST-T16 remain open |
| Grafana/API/n8n/NodeCG service links — [Stream page](../../apps/stream-extend/src/routes/+page.svelte) | Source-present links; not proof of embedded service/overlay operation | Combined configured service-link parity missing; no new service introduced |
| Autopilot rehearsal/status — [autopilot](../../apps/stream-extend/src-tauri/src/autopilot.rs) | P-056 bounded source/rehearsal evidence | Combined adapter missing; no unrelated gameplay/autonomy work |
| Production host/game/rig control — [native production owner](../../apps/stream-extend/src-tauri/src/autopilot_control.rs) | P-056 guarded local owner; actual game/rig/live bindings remain open | Combined adapter missing; original session/off-air/stale-event guards unchanged |
| Voice/personality authoring/review/scripted Q&A — [voice studio](../../apps/stream-extend/src-tauri/src/voice_studio.rs) | P-066 native authoring and local audio evidence; audible OBS/account binding open | Combined adapter missing; no paid provider or voice activation |
| Remote discovery/approval/correlated result — [relay client](../../apps/shared/relay-client/src/lib.rs) | P-058 loopback; hosted two-device ST-R14 open | Combined remote missing/denied; U-08 later, no new remote permission |
| Account/OAuth/private provider actions — [social bridge](../../apps/shared/social-manager/src/lib.rs) | P-062 source routes; actual sign-in/destination acceptance open | Combined profile selection only; OAuth/publish not granted |
| Workflow catalog/preflight — [ComfyUI adapter](../../apps/creator-extend/src-tauri/src/comfyui.rs) | P-054/P-057/P-063 source and historical GPU evidence; per-target gates open | Combined catalog/readiness present; operational preflight/queue adapter missing |
| Workflow inputs/upload/queue/history/output preview — [workflow inputs](../../apps/creator-extend/src-tauri/src/workflow_inputs.rs), same ComfyUI adapter | Existing fake contracts and historical local output; native target acceptance remains | Combined operational creative jobs missing; not implemented in this repair |
| Media import/list/reveal/archive/status — [shared inbox](../../apps/shared/ui/RecordingLibrary.svelte) and recording library | P-065 synthetic Mac import/reveal; Start editing/Published are metadata only | Combined Content-gated import/list/reveal/archive present; editing/published updates denied. R1-05 explicit manual-import abandonment does not claim registration |
| Blender launch/planning/owned render jobs/cancel/retry — [Blender jobs](../../apps/creator-extend/src-tauri/src/blender_jobs.rs) | P-061 Mac picker/two-scene evidence; recovery/Windows remain open | Combined operational adapter missing; no job/process guard changes |
| Krita fixed launch/scripts/addon archive/tool checks — [Krita adapter](../../apps/creator-extend/src-tauri/src/krita.rs), [tool runtime](../../apps/creator-extend/src-tauri/src/tool_runtime.rs) | P-057 fixed adapters; live DCC acceptance separate | Combined adapter missing; no caller-supplied script or executable path |
| Posture analysis — [posture adapter](../../apps/creator-extend/src-tauri/src/posture.rs) | P-057 native source; input quality/physical acceptance separate | Combined adapter missing; optional capability must remain independent |
| Recording → reviewed Shorts draft / generated asset → overlay — [local Shorts](../../modules/content-creation/stream_shorts/README.md), P-072 U-09 | P-056 local CLI/synthetic output exists; cross-workspace acceptance not complete | Combined Shorts/overlay adapters missing; no metadata-only editing claim |
| Packaging/upgrade/rollback — P-072 U-01/U-03/U-06/U-07/U-13 | Private unsigned Mac build is not clean-host/signing/migration acceptance | Bundle identity remains preview; actual replacement/release still gated |
| Cloud U-10–U-12 / unrelated Pending/Deferred scope | Proposed candidates, not accepted legacy desktop parity | Out of scope; no implementation or provider spend |

This is the single current workflow inventory. The dated phase-0 tables below preserve historical
source evidence only; neither table nor native registrations grant acceptance or backlog authority.

PR #93 overlaps configuration/branding/setup documentation and #92 social catalog/content. Neither
is merged or overwritten here; `com.hybridcreator.extend.preview` remains the bundle identifier.

#### Recording-first checkpoint verification — 2026-11-01

**Runtime source commit:** `804a395236046f092f825d62567cb8cf574f2e19`; integration base
`ab2bc473030bbfbb35e8c40a1d13f2cd6a844fd5`; upstream main checked as
`a19f9b32e78ead7a8d57ff039f592139681e988f`. The following evidence is independent of the
sidebar's earlier runs. This is a working local-recording slice, not completed P-072 parity.

- `npm --prefix apps/extend run check` — 0 errors/warnings; `npm --prefix apps/extend test` —
  8 passed; `npm --prefix apps/extend run build` — exit 0. Both legacy apps independently passed
  `npm run check` (0 errors/warnings) and `npm run build`. Production assets contain none of the
  browser-fixture/session/call-log markers.
- `cargo test --locked --manifest-path apps/extend/src-tauri/Cargo.toml` — 22 passed. Includes
  foreign window/origin rejection, unsafe pack/host/port/password changes, and both locked-vault
  and unreachable-loopback OBS leaving a real fake-HTTP Content readiness path usable.
- `cargo test --locked --manifest-path apps/stream-extend/src-tauri/Cargo.toml` — 17 unit +
  29 protocol/controller tests passed; one packaged Python-owner test ignored by its existing gate.
  Ten new combined cases cover actual local start/Stop, scenes/input mute, external outputs,
  actual saved-profile attribution, pinned reconnect after cache loss, failed/unconfirmed start,
  failed Stop/retry, lost Stop response/manual import, inbox retry without another Stop, duplicate
  concurrent calls, stale generations, restart non-adoption and legacy external-recording ownership.
- `cargo test --locked --manifest-path apps/creator-extend/src-tauri/Cargo.toml` — 44 passed;
  real-Blender and operator-selected-ComfyUI tests remain ignored. No live test is reported passed.
- Locked shared suites used the combined manifest with `-p local-settings -p recording-library
  -p tauri-plugin-social-manager -p tauri-plugin-module-setup -p relay-client`: respectively
  2 / 3 / 5 / 23 / 5 passed. `cargo test --locked --manifest-path apps/shared/setup-engine/Cargo.toml`
  — 7 passed using the existing ignored setup-engine lock. A standalone shared-plugin invocation
  without a lock was rejected by `--locked`; rerouted to the application's existing lock, without
  changing dependencies or manifests. All Rust suites share the task's app target cache.
- **23 guard mutations caught, source restored:** trusted window/origin; Stream pack, host, port
  and credential changes; session generation and duplicate start; external-output checks in both
  controller and adapter; pinned reconnect; pending-inbox retry; owned/pending/active-output recovery;
  adapter duplicate/unowned/externally-owned recording Stop; observed scene/audio input; one-shot
  start/Stop; inactive Stop; native pack admission. Rust mutations fail executable tests; the wrapper
  pack mutation fails the no-skips desktop admission contract. The pin mutation initially survived
  because an already-cached connection masked redirection; clearing the cache makes it fail, and
  the restored test passes. No compiler failure was counted as a caught mutation.
- `python3 -m pytest tests/desktop_apps -q -p scripts.testing.no_skips` — 24 passed; the focused
  desktop + docs run also exits 0 under `scripts.testing.no_skips`. `make test` — required offline
  suite reaches 100%, exit 0. The first post-commit run detected a stale desktop radius observation:
  the check counts tracked files, so the new component entered its inventory only after commit.
  Updated only the hub's two observed declaration counts (no proposed/approved design value changed)
  and reran the suite. `ruff check modules/ scripts/`, generated-doc check,
  `make proposal-report ARGS='--check --summary'` (no missing/extra lane IDs), public-release hygiene
  (0 failures; 2 existing owner-set placeholders) and `git diff --check` pass.
- Explicit synthetic browser fixture: start local recording, load scenes/audio, navigate directly
  Stream → Content with correct profile options, collapse Production/Studio, open Help, mute and Stop
  using the same session generation. Stop/mute stay usable and in view. At 320×736 there is no
  horizontal overflow and both controls remain usable. This fixture invokes no real native actions.
  Regression assertion `assertContentProfile` failed with the keyed-remount fix removed, then passed
  restored; the original Stream options incorrectly remained under the Content selector.
- `npm --prefix apps/extend run tauri build -- --debug --bundles app -- --locked` — private unsigned
  Mac app built. Opened that task bundle and moved it through Window → Built-in Retina Display.
  Native main-window ACL admits preferences/navigation/catalog; local status strip remains visible
  while scrolling Studio, OBS unavailable is sanitized, Start stays disabled, and direct navigation
  correctly shows Main Stream then Main Content without editing either selection. No native recording,
  scene switch, mute, install, import, render, upload, publish or broadcast action was invoked.

**NOT RUN / remaining:** full aggregate `make verify` (its 46-command plan was inspected; 17 checks
listed not-run), hosted CI, Docker/service acceptance, real OBS encoder/file/picture/audio and Stop
stress, private playable-media handoff, actual vault unlock/failure recovery, native Windows,
clean-host/signing/public distribution, migration/relay/two-device and full U-01–U-13 convergence.
U-10–U-12 cloud remains out of scope. Native foreign-origin IPC/CSP enforcement still needs the
manual U-07 pass; executable origin-policy and configured ACL tests do not certify that runtime.
Closing/restarting the app loses ownership by design; control any surviving output in OBS and
import manually. Do not stop/restart OBS recording independently inside an owned session.

**Next completion brief:** first independently review this diff and repeat U-04 with synthetic,
playable local OBS output and real source/content profile handoff. Then extend the root controller
with the existing live-session start/Stop only after regression/mutation tests for uncertain stream
start and failed recording rollback prove safety ownership is retained. Keep generation/connection
pins and root safety commands, audit original live/off-air guards, and preserve the live-account gate.
Transport the remaining accepted creative adapters in separate bounded slices; do not activate
unrelated Pending/Deferred features. No new owner choice blocks this local slice. Existing PL-D10–
PL-D13 and release/account decisions remain at their canonical gates; no duplicate alignment question.

### Owner-approved sidebar slice — 2026-11-01

**Kind:** feature (existing P-072); **State:** implementation authorized by “Start building?”
after agreement on the navigation and expandable controls. **Agent:** `gpt-6.1-sol` / `high`,
retaining P-072's assignment for configuration-driven Svelte navigation and capability isolation.
The installed coordinator retains this bounded assignment; no additional worker or timer is created.
The referenced work-type/entry-gate files at the root instructions' library pin were unavailable;
this explicitly labelled feature row records the work without inventing additional authority.

Owner decisions **P072-NAV-01** and **P072-NAV-02** supersede the earlier visible
Home/Stream/Create/Library/Settings grouping with these feature sections:

- **Workspace:** Home, Media Library, Jobs & Activity, Automations.
- **Production:** Live & Recording, Scenes & Sources, Audio & Soundboard, Overlays & Avatars.
- **Studio:** Clips & Video, Images & Thumbnails, 3D & Environments, Sports Analysis.
- **Pinned utilities:** Profiles & Accounts, Setup & Settings, Help & Diagnostics.

Workspace, Production and Studio expand/collapse independently. Feature links open a page;
section shortcuts also expand the destination and bring it into view. Everyday controls remain
visible and advanced configuration expands in place. Collapsing either navigation or configuration
must not stop jobs, change profiles/accounts, disable a capability or hide live safety controls.
The preview has no broadcast controller, so this slice does not introduce an imitation live strip.
MyFeed supplies layout/interaction references; exact branding and drafted hub tokens remain unapproved.

Implementation scope: the existing private preview frontend and navigation configuration,
accessible disclosure/section targeting and presentation-state persistence. Reuse existing native
page IDs and admission, isolated preferences, setup/profile and recording contracts. Unimplemented
features are explicitly unavailable; no new operational native commands, credential migration,
stream controller, render/export implementation or replacement release is included. Library access
continues to require the Content pack until native shared-library admission is separately migrated.

**Verification — 2026-11-01:** P-072 private-shell-preview row in the verification matrix:

- `npm --prefix apps/extend run check` (0 errors/warnings), `npm --prefix apps/extend test`
  (8 passed); five navigation/admission guard mutations each made the Node suite fail, then restored.
- Stream Extend and Creator Extend each passed `npm run check` and `npm run build`.
- `cargo test --locked --manifest-path apps/extend/src-tauri/Cargo.toml`: 20 passed.
  Both legacy app locked Rust suites passed; their opt-in real-service/Blender tests remain ignored.
- Locked shared crate suites: recording-library 3, local-settings 2, social-manager 4,
  module-setup 23, relay-client 5 and setup-engine 7 passed. Legacy/shared suites reused a common
  `CARGO_TARGET_DIR`; native source, permissions and commands were not changed.
- `make test`: offline suite exit 0; `ruff check modules/ scripts/`, generated-doc check,
  proposal report and `git diff --check` passed. The CI-derived `make verify ARGS=--list` plan
  was inspected; full aggregate `make verify`, Docker/Compose, separate service security lanes,
  hosted CI and live acceptance were not run for this frontend slice.
- Explicit synthetic browser fixture: section expansion/focus, keyboard group toggling,
  remembered folding after reload, Stream-only hiding Studio/library, rejection of a disabled
  deep link, and no horizontal overflow at 320/736px. The fixture uses test-only official Tauri
  IPC mocks; production build contents were checked for absence of fixture markers.
- `npm --prefix apps/extend run tauri build -- --debug --bundles app -- --locked`: private Mac
  app built. Actual native UI on the built-in Retina display: both groups and utilities render;
  Stream-only/Create-only/both admission, advanced-connections shortcut expansion/focus and
  restart restoration of collapsed Production/Studio verified. No install, secret edit, profile
  change, media import, broadcast, render, upload or publish action was taken.

Full parity, migration, clean-host/native Windows, live broadcast safety and public distribution
remain open. This is a navigation implementation in the private preview, not the completed merger.

**Owner:** OpenTechnology14 + agent
**Date:** 2026-10-04
**Roadmap layer(s):** Existing product surfaces; Creator Experience, Content Creation, Realtime AI, Automation / Control, Social Management, Backend / API, Storage / Data, Infrastructure and Observability. No new top-level module.
**Evidence level:** Current source inspected; desktop consolidation is partially implemented under v6 authorization and cloud expansion remains Proposed. Historical acceptance is attributed to its existing proposal, not rerun here.

The owner explicitly wants the apps combined to make distribution to other people easier. This
records that direction and a phased implementation contract. The initial 2026-10-04 task created
the proposal. On 2026-10-12 the owner explicitly authorized the private preview before convergence
checks finish; the preview now exists at `apps/extend/`. Cloud phases remain candidate scope.

The assigned model/effort is offered by this host's execution controls. This drafting interface
does not expose a control to change or independently verify its active model; the assignment above
must be selected and recorded when implementation starts. No historical model execution is claimed.

## 1. Executive summary

**Private-preview authorization and implementation — 2026-10-12:** after requesting continuation
until the two Accepted proposals reach Testing, the owner explicitly answered **"Build the private
preview first"** to the five-gate timing question. The [roadmap exception](../architecture/deviations.md#2026-10-12--private-combined-shell-preview-before-convergence)
authorizes a preview alongside the legacy apps; full parity, migration, public release, commercial
changes, cloud phases and legacy replacement remain gated. Model assignment remains Sol/high;
no model dispatch or independently verified executor identity is inferred from that metadata.

[Extend Preview](../../apps/extend/README.md) is now a real Tauri/Svelte application: guided task
folders and compact layout; persisted Stream/Create/both choices; one shared setup environment;
separate profile selections; the shared locked recording inbox; read-only OBS/ComfyUI readiness
and bundled workflow catalog. Native pack checks reject disabled-domain operations. Invalid
connection drafts preserve saved settings; OBS secret updates use a separate preview vault identity.
No legacy settings/tokens are migrated. The v6 recording-first slice adds native local recording,
scene and input-mute commands; broadcast/render/remote/publishing commands remain absent. Editing/published status changes are denied, including
crafted invokes, and the inbox hides those metadata-only actions in preview mode.

New configuration is `configs/ui/combined-navigation.json`, `extend-preview-defaults.json` and
`configs/setup/extend-preview.json`. The original OBS/ComfyUI modules are included as source
adapters, not independently rewritten; the queue-status timeout repair under P-001 therefore also
applies here. A locked OBS vault yields blocked Stream observations while Create remains usable.
The preview grants no OAuth/remote/publishing plugin permissions and configures a local CSP.
Native GUI/CSP/credential-store enforcement is still an acceptance run, not inferred from builds.

**Built and checked:** 20 Rust unit/adapter tests, four Node navigation tests, native admission/
permission-surface Python checks and frontend check/build pass; an ARM64 Mac `.app` and `.dmg`
are produced by the locked debug bundle command. Both legacy app Rust and frontend checks/builds
are rerun because the shared recording component gained a backwards-compatible preview mode.
CI now includes the preview in the existing desktop matrix. These are private debug artifacts;
Windows/clean-host/signing, native UI/voice/video, restart/vault and public migration are not proved.

**Testing handoff:** U-01/U-02/U-07 apply to the private preview: first opening with prerequisites
absent, pack/layout persistence and keyboard/narrow-window navigation, selected-tool install/retry,
synthetic local import/reveal and profile separation, denied crafted invokes/remote origins and
vault failure recovery. The recording/streaming/export/remote parity journeys U-03–U-09 and public
rollback U-13 remain later gates. The v6 slice adds a global owned-local-recording Stop/status strip and observed-input mute;
Go Live remains in Stream Extend pending its controller recovery slice and real acceptance.

Ship **one local desktop application**, with **Stream** and **Create** workspaces, one setup flow,
one recording/asset library and one settings/account area. A new user downloads one installer for
their OS, opens it without a developer toolchain or cloud account, and selects Stream, Create, or
both. Shared dependencies are installed once, and additional capabilities can be enabled later.
The product name, application identifier, pricing and store listing are separate release decisions.

This is feasible because both apps already use Tauri 2, Svelte 5 and several shared Rust/UI
packages. It is still substantial integration work: putting the two dashboards in one window does
not resolve settings conflicts, recording ownership, permissions, relay identity or resource use.
The smallest useful preview combines setup, navigation, profiles and recording handoff; replacement
of the existing downloads requires parity for all currently accepted workflows.

**Cloud recommendation:** desktop first, then an optional browser companion for status, planning
and review, followed by explicitly approved remote actions and selected batch jobs. A full browser
replacement is a separate, much larger product: the present UI calls native Rust commands for local
files, credentials, processes and OBS/ComfyUI connections. Reusing visual components does not make
those commands available in a normal browser. This conclusion follows from the current code and
[Tauri's native core/WebView process model](https://v2.tauri.app/concept/process-model/).

## 2. Verified current state

| Evidence inspected | What exists / what it means |
|---|---|
| Both `apps/*/package.json` and `src-tauri/tauri.conf.json` | Matching Svelte/Tauri stacks; separate bundles `com.streamextend.app` and `com.creatorextend.app`. Both currently set `app.security.csp` to null. Combining them requires a permission and content-policy review. |
| `apps/stream-extend/src/routes/+page.svelte` and `apps/creator-extend/src/routes/+page.svelte` | Separate pages and lifecycle polling with direct Tauri `invoke` calls. Both import shared setup, profile, social and remote components; Creator also imports `RecordingLibrary.svelte`. |
| Both `src-tauri/src/lib.rs`, `connection_settings.rs`; `apps/shared/local-settings/src/lib.rs` | Each app registers its own `get_config`/`set_config` and remote/setup commands. Connection files live under the shared OS local-data `HybridCreatorPlatform/connections` directory but are keyed by application identifier. OS-vault entries also use product-qualified keys. |
| `apps/shared/recording-library/` and `apps/shared/social-manager/` | Locked shared recording metadata and separate Stream/Content profile selections already exist. Media is referenced by local path, not copied into the other app. Preserve these contracts. |
| `apps/shared/setup-wizard/`, `setup-engine/`, `ui/`; `configs/setup/stream-extend.json`, `creator-extend.json` | Shared setup/readiness infrastructure exists, with product-specific manifests. This is the consolidation base; no second installer engine is needed. |
| `apps/shared/relay-client/src/lib.rs`, `control.rs`; `cloud/relay-api/app/routers/relay.py` | Product-specific discovery/action validation exists. The server accepts only `StreamExtend` and `CreatorExtend` presence identities today. A new product string would be rejected; a combined shell is a protocol migration too. |
| `cloud/relay-api/app/routers/sync.py`, `metrics.py`, `notifications.py` | Tenant-scoped sync and metrics routes exist. Sync is generic versioned JSON, not application-aware conflict resolution. APNs/FCM delivery helpers still have TODO implementations. These files do not prove a ready hosted companion. |
| `.github/workflows/desktop-installers.yml` | The installer matrix builds both app names and identifies outputs as unsigned private prereleases. One installer does not by itself solve public signing or clean-machine setup. |
| [Audit](../AUDIT.md), P-003/P-058/P-063/P-065 in [the queue](../PROPOSALS.md) | Some native Mac and loopback paths have recorded evidence; clean-host, physical media, Windows, real-account and hosted/two-device acceptance remain open for relevant paths. Consolidation must not convert those gaps into claims of completion. |

The [roadmap convergence rule](../architecture/roadmap.md#future-convergence-path) originally
delayed even proposal work until five acceptance gates passed. The owner's explicit request is a
**planning-only timing exception**, recorded in [deviations](../architecture/deviations.md).
The gates remain required before implementation replaces the two delivery surfaces. Product
branding/pricing and unrelated Pending/Deferred work receive no approval through this proposal.

## 3. Problem, goals, and non-goals

### Phase 0 source inventory and gate review — 2026-10-12

The owner requested work on P-072 and P-001. This pass advances the authorized baseline/contract
phase. It does not mark the five convergence gates passed or authorize a combined binary.
Source anchor: checkout `718240e42c61715873724ac92309773a2541c688`, plus existing unrelated
uncommitted documentation/testing work. The runtime files inspected below were unchanged in
that starting worktree. The P-072 assignment remains `gpt-6.1-sol` / `high`; no model dispatch or
historical executor identity is inferred from that assignment.

#### Current workflow coverage

Both apps expose six navigation views. Each dashboard contains additional task controls; those
controls must be included in parity even when they are not independent navigation entries.
“Source present” below means an implemented path is registered, not full native acceptance.

| Current surface / workflow | Source and evidence owner | State and consolidation requirement |
|---|---|---|
| Both: Module setup, selected tools, installs/retry, guides, capture/audio checks | Shared [ModuleSetup](../../apps/shared/ui/ModuleSetup.svelte), [setup-wizard](../../apps/shared/setup-wizard/README.md); P-003/P-063 | Source present; native Mac evidence recorded; clean physical Windows/capture acceptance open. Reuse the installer/environment locks and manifest resources once. |
| Both: Connections, save/restart, readiness/retry, optional setup sync | Both `connection_settings.rs`/`lib.rs`, shared [local-settings](../../apps/shared/local-settings/README.md), [setup-engine](../../apps/shared/setup-engine/README.md); P-003 | Source present, shared persistence contract but different settings DTOs and probe implementations. Preserve capability-specific readiness; do not merge conflicting endpoints silently. |
| Both: Remote control, discovery, request, approve/deny, correlated result | Both `relay.rs`, shared [relay-client](../../apps/shared/relay-client/README.md); P-058 | Loopback evidence exists; successful hosted action on two real devices remains open (ST-R14). Preserve product allowlists until negotiated migration is separately built. |
| Both: Social and Stream/Content profile switchers | Shared [social-manager](../../apps/shared/social-manager/README.md), `ProfileSwitcher.svelte`, `SocialManagement.svelte`; P-062/P-065 | Source present; real-provider routes/sign-in/private actions remain open. Separate profile selections must survive workspace switches; no publishing is authorized by this inventory. |
| Stream: Dashboard scene selection and observed OBS status | [Stream page](../../apps/stream-extend/src/routes/+page.svelte), `obs.rs`; P-055/P-063 | Real command implementation and fake protocol tests; current local server is unreachable. Native picture/audio and scene-change acceptance still required. |
| Stream: Grafana, Platform API, n8n and NodeCG service links | Stream dashboard Services section | Four external links exist; they use fixed local addresses rather than saved endpoint values. Include configured link routing in the future parity review; a link is not an embedded service or accepted overlay workflow. |
| Stream: managed stream/recording start, stop and handoff | Stream `lib.rs`/`obs.rs`, shared [recording-library](../../apps/shared/recording-library/README.md); P-065 | Ownership/order contracts exist; full real-profile handoff ST-R05 is open. Keep the session controller alive across navigation; never adopt a pre-existing recording as owned. |
| Stream: Automated streaming and Personalities authoring | `Autopilot.svelte`, `autopilot.rs`, `voice_studio.rs`; P-056/P-066 | Rehearsal/authoring paths built; live production/game/account/avatar bindings and audible OBS acceptance open. Preserve live/off-air guards and fixed worker boundaries. |
| Creator: Dashboard workflow catalog, preflight, input/image upload, queue, history and preview | [Creator page](../../apps/creator-extend/src/routes/+page.svelte), `WorkflowInputs.svelte`, `comfyui.rs`, `workflow_inputs.rs`; P-054/P-057/P-063 | Source present; historical local GPU/output evidence recorded; each target/workflow needs its stated acceptance. Current local ComfyUI endpoint is unreachable. |
| Creator: Recordings import/list, profile attribution, reveal/archive/status | Shared `RecordingLibrary.svelte`/recording library; P-065 | Source present; synthetic Mac import/reveal evidence recorded. **Start editing only writes `editing` status; Mark published only writes metadata.** Neither invokes rendering/upload. Real handoff and accounts remain open. |
| Creator: Blender launch, render planning/start/status/list/cancel/retry | Creator `lib.rs`, `blender.rs`, `blender_jobs.rs`, `tool_runtime.rs`; P-061 | Production-job source exists; full native two-scene failure/cancel/recovery acceptance remains open. Preserve manifest/job IDs and existing worker ownership. |
| Creator: Krita launch, packaged scripts, addon archive and tool checks | Creator `krita.rs`/`tool_runtime.rs`; P-057 | Fixed tool adapters exist; live DCC workflow acceptance remains separate. Do not broaden script/executable selection while transporting this page. |
| Creator: Posture Screen analysis | Creator `posture.rs`/`posture_analyze`, Sports Analytics module; P-057 | Native adapter present; physical/input-quality acceptance remains separate. Enabling this optional task must not require it for recording/clip work. |
| Planned combined Home, clip adapter, global live strip and admission policy | P-072 §5 | Proposed only. No combined shell or native recording-to-Shorts adapter exists. Reuse the Content Creation CLI after implementation authorization; status changes cannot satisfy U-09. |

#### Native command and migration map

Inspection of each `generate_handler!` registration found **27 Stream commands, 42 Creator
commands, 15 shared names and 54 distinct names**, excluding the two shared plugin namespaces.
Identical names do not imply identical arguments, validation or result types.

| Group | Registered commands / boundary |
|---|---|
| Shared names (15) | `get_config`, `set_config`; `remote_get_settings`, `remote_save_settings`, `remote_connect`, `remote_disconnect`, `remote_status`, `remote_approve`, `remote_deny`, `remote_request`; `setup_last_readiness`, `setup_refresh_readiness`, `setup_sync_settings`, `setup_save_sync_settings`, `setup_sync_now` |
| Stream OBS (9) | `obs_status`, `obs_connection_diagnostic`, `obs_recording_test`, `obs_scenes`, `obs_switch_scene`, `obs_stream_status`, `obs_toggle_stream`, `obs_start_stream_session`, `obs_stop_stream_session` |
| Stream workers (3) | `autopilot::autopilot_status`, `autopilot::autopilot_rehearse`, `voice_studio_request` |
| Creator workflows (11) | `comfyui_status`, `comfyui_preflight`, `comfyui_workflows`, `comfyui_load_workflow`, `comfyui_workflow_inputs`, `comfyui_upload_target`, `comfyui_queue_configured`, `comfyui_upload_image`, `comfyui_queue`, `comfyui_prompt_status`, `comfyui_output_preview` |
| Creator recording inbox (4) | `recordings_list`, `recordings_import`, `recordings_update`, `recordings_reveal` |
| Creator Blender jobs (7) | `blender_open`, `blender_batch_render`, `blender_job_start`, `blender_job_status`, `blender_job_list`, `blender_job_cancel`, `blender_job_retry` |
| Creator tools (5) | `krita_open`, `krita_run_script`, `creator_tool_status`, `creator_tool_archive_blender_addon`, `posture_analyze` |
| Shared plugins (separate from counts) | `plugin:module-setup` selection/install/check/capture/audio contracts and `plugin:social-manager` catalog/profile/account/publishing contracts. Retain their own native validation and permissions. |

| State / privilege | Conflict or migration policy to implement after approval |
|---|---|
| Shared `comfyui_url` and `api_url` in two app-qualified files | Show both values in import review; require a choice when different. Do not pick the most recently modified file as an implicit winner. |
| Stream-only OBS host/port, vault `obs-password`, Grafana URL | Import only into Stream capability settings; verify vault access with the chosen new identity; retain original namespace for rollback. |
| Creator-only MinIO endpoint/vault keys and Blender/Krita paths | Import into Content capability settings; missing credentials require reconnecting; never serialize them into previews or backups. |
| Remote tokens, stable device IDs, auto-connect and product identity | Keep public settings separate from vault entries. Explicit adoption/re-pairing, v1/v2 negotiation and session shutdown must precede identity migration. |
| Readiness observations, setup selection and shared environments | Reuse the shared installer/environment roots; capability evidence expires normally. Imported selection does not prove a running service or physical acceptance. |
| Recording ledger, social catalog and distinct selections | Reuse locked shared stores without copying video or rewriting their schemas in the first slice. Pin the active session destination independently of Content selection. |
| Stream OBS cache/session and Creator render runtime | Create one owner for each domain; navigation must not mount a second controller or discard an owned session. Legacy/unified concurrent writers require admission checks. |
| Declared capabilities | Both declare `module-setup:default` and `social-manager:default` for `main`; Creator additionally declares `core:default` and `dialog:default`. Both CSP values are null. Audit a minimum combined grant set and content policy; copying the union is not a completed security review. |

#### Measured baseline and remaining measurements

This workstation reports **macOS 26.6.2, ARM64**. Four existing local DMGs were hashed in place
without launching or rebuilding them. These measurements identify those files only: their build
commits, signatures, install time and clean-host provenance were not established in this pass.

| Existing file | Bytes | SHA-256 |
|---|---:|---|
| Stream `target/release/bundle/dmg/Stream Extend_0.1.0_aarch64.dmg` | 7,130,199 | `0eda08c5603d710275cc56cf3ce1729f84bb6c57a51b827cf18394d4bbd26b2c` |
| Creator `target/release/bundle/dmg/Creator Extend_0.1.0_aarch64.dmg` | 7,116,763 | `992717c27d4a93f2dc2036646983ce564ab749521c57e8102c6f4e065a927da7` |
| Stream `target/debug/bundle/dmg/Stream Extend_0.1.0_aarch64.dmg` | 17,380,392 | `c2e5e8124ebdac40606f1aacd4ffbc7542ba4aa6beea5fff34deafe370fd7e87` |
| Creator `target/debug/bundle/dmg/Creator Extend_0.1.0_aarch64.dmg` | 17,370,859 | `a10931ed78f1090d6a05e0bff60c45e9e96c1f73bbd8dd961b8d7d7361b0f062` |

Release DMGs total 14,246,962 bytes; this is the sum of two existing compressed downloads,
not a forecast of combined size. Do not compare debug bytes with future release bytes.
The existing private installer workflow targets Windows x64; local files above are macOS ARM64.
Neither establishes the owner-approved public support matrix (PL-D02/PL-D10).

Startup and resource measurement is still open. For each fresh artifact/target, record hash and
build commit, clean-host prerequisites/network state, install actions/time, launch-to-usable-setup
time (five cold trials), idle process count/RSS after 60 seconds, then task actions/time to a
verified stream recording and content output. Repeat Stream-only, Create-only and both selections
on the same machine/settings. Before contention tests, PL-D10 must select numerical limits for
startup, RAM, package size, stop/mute latency and OBS rendering/encoding lag. No unmeasured budget
is silently treated as passed; this inventory is not a finished performance baseline.

#### Five convergence gates: none closed by this pass

| Roadmap gate | Current evidence / next proof |
|---|---|
| 1. Both desktop journeys accepted | Partial: builds, synthetic/loopback and some Mac workflows recorded. ST-R05 and CT-R01/CT-R15 still require full physical/account/output evidence. |
| 2. Shared contracts without product forks | Partial: shared crates/components exist, but connection DTOs, native probes/controllers and relay product identity differ. The command/migration map above identifies the contracts to reconcile and test. |
| 3. Three real cross-product workflows | Open: recording → reviewed MP4 (CT-R15), generated graphic → visible OBS overlay (ST-T17), and recording → selected Content account → approved private upload (CT-R16). CLI/synthetic output is not these full journeys. |
| 4. Real two-device relay/approval | Open: ST-R14 is still required. One-machine loopback does not close it. |
| 5. Packaging improves first run/switching | Open: concept interactions exist; no combined artifact or comparative clean-host task measurement. PL-D10 baseline/budgets and native single-pack evidence are required. |

Recommended next execution order: restore the local OBS baseline (ST-R01), finish the existing
Stream/Content acceptance journeys, obtain two-device approval evidence, then review PL-D10 and
PL-D13 against this inventory. Public identity/commercial/cloud decisions remain later, separate
gates. Source/planning progress does not close P-072 or its native acceptance rows.

**Verification:** required `make test` reached 100%, exit 0
(`/tmp/hcp-accepted-final.log`); generated documentation is synchronized; proposal/lane report
has zero missing/extra IDs; Ruff and `git diff --check` pass. Source command counts and all four
local DMG byte/hash observations were read directly. Startup/resource benchmarks, native
convergence workflows and two-device acceptance were not run. Native OBS inspection was
attempted but the UI tool reported the Mac locked; manual unlock is required to continue.

**Actors:** a new recipient installing the software; a creator who streams and edits; an existing
user upgrading either/both apps; later, an invited reviewer using a browser; the operator supporting
installations and optional hosting.

**Goals:** one download choice per supported OS/architecture, one installation and app launch,
zero cloud sign-ins for local features, one shared setup history, and zero app switches to move a
finished stream recording into the content workflow. Keep independent Stream and Content account
selections visible so a workspace switch never silently changes a live destination.

Measure clean-host time/actions to the setup window, time/actions to first verified stream and
content output, package/download size, idle RAM, cold start and background processes. Compare
Stream-only, Create-only and combined selections with today's separate-app baselines. At Phase 0,
record hardware and numerical performance budgets before evaluating the merged build. No speed or
size improvement is claimed without that comparison.

**Non-goals:** implementing unfinished module features merely because their tabs move; renaming
every public surface; deciding new commercial terms; bundling all models/DCC tools in the installer;
merging module implementations; requiring Docker for the initial window; introducing Kubernetes or
distributed workers; moving live capture/inference into the cloud; building a new browser editor or
mobile app in the desktop consolidation phase.

## 4. User paths and states

| Path | Proposed behavior and recovery |
|---|---|
| First run | Open guided Home with no OBS, Python, Docker, models or cloud credentials. Choose Stream, Create or both; follow only the next required setup step, inspect optional installs and skip any unavailable step. Preserve P-063's bundled guides and restart recovery. |
| Normal streaming → creation | Run an owned OBS session, stop and finalize its recording, then open that same library item in Create. Carry source profile, content profile and provenance; do not auto-publish or duplicate the media. |
| Stream-only / Create-only | Show the chosen workspace first; keep the other discoverable through capabilities/settings. Lazy-load its UI and start no unused runtime merely because the app contains its code. |
| Missing dependency / service failure | Report the affected capability, offer its setup/retry path, and keep the rest of the app usable. Missing ComfyUI must not block OBS control; an OBS failure must not block content browsing. |
| Invalid input | Native handlers reject invalid endpoints, paths, unsupported schemas and unknown actions before side effects. Show a field-specific correction; preserve the last valid state. |
| Local offline / cloud outage | Installed local capabilities continue. Cloud status is unavailable/stale with a timestamp. A workstation that is asleep or offline cannot execute remote actions; never show a queued action as completed. |
| Retry | Deduplicate migration steps, installs and remote request IDs. Inspect known job status before resubmitting after a timeout; do not repeat stream toggles, uploads or paid renders blindly. |
| Cancel / disable capability | Cancel only the owned job. Ask the operator to stop/drain an active stream or render before disabling its workspace. Preserve external OBS recordings and shared dependencies used by other modules. |
| Upgrade from one/both apps | Preview detected settings and conflicts; copy into the new namespace atomically, retain originals, reuse shared module environments/library, and migrate secrets through the OS vault. Missing secrets require reconnecting, not plaintext export. |
| Relaunch after crash | Recover journaled migration/setup steps, reconcile external job/session state, keep unknown outcomes explicit, and leave stale remote approvals expired. Never infer recording ownership from “OBS is recording.” |
| Later browser use | Show desktop availability, last-seen time and capabilities. Read-only viewing requires a scoped account; remote execution still requires target-side approval. Review an uploaded proxy, not a workstation path. |

## 5. Architecture and data flow

### Beginner navigation direction — owner refinement, 2026-10-05

The owner wants one app that a beginner can understand, with few controls on the main pages
and module groups/folders exposing additional tools through navigation and configuration.
The owner named MYFeed and OpenTechApp as references. This refines P-072's authorized planning;
the combined shell and all proposed UI below remain implementation-gated.

**Source comparison (code inspection, not a new usability study):**

| Reference inspected | Useful pattern | Carry into the combined app |
|---|---|---|
| MYFeed working checkout based on `b2ff1c2` (the inspected UI includes uncommitted changes): `src/App.tsx`, `src/components/FeedReader.tsx`, `SettingsPage.tsx`, `SettingsContent.tsx` | A clear reading view, separate Customize mode, named sidebar entries, Connections and grouped app settings; workspace details expand inside Settings | Everyday work stays on the workspace page; setup/customization opens in context or Settings. Keep labels for beginners and remember the selected workspace |
| OpenTechnologyApp `752b972`: `src/components/Sidebar.tsx`, `sidebar/SidebarRail.tsx`, `SidebarDrawerToolbar.tsx`, `SidebarFolderTree.tsx`, `SidebarProjectNavigation.tsx` | Persistent quick-access rail; drawer for navigation; expandable folders and project sections; Settings remains grouped management even where quick shortcuts exist | Shallow navigation groups and optional compact rail; don't duplicate the same toolbar across rail, drawer and content |
| Current Extend apps: both `src/routes/+page.svelte`, shared `ModuleSetup.svelte`, `RecordingLibrary.svelte` | Six peer tabs per app, a flat module chooser, technical prerequisite/endpoint controls and an existing recording inbox | Preserve native safety/readiness, profile routes and shared data; reorganize discovery around tasks and progressively disclose configuration |

The directory named `OpenTechApp` contains marketing SVG illustrations; the working application
reference is the separate `OpenTechnologyApp` checkout. Reference repositories are read-only:
no code, workspace data, account information or credentials are copied into this platform.

**Current strengths:** shared setup, local operation, recording handoff and a working Shorts CLI
provide useful building blocks. **Current friction for a beginner:** module/package names,
service endpoints, optional ComfyUI/Docker prerequisites and automation compete with the first
recording task. Combining binaries alone does not resolve that learning path.

#### Recommended default: labelled folders and a guided Home

Use five navigation entries: **Home**, **Stream**, **Create**, **Library**, **Settings**. Home is
a page; the other entries expand to shallow task pages. Help remains easy to find. Keep one
group plus one leaf level in the default hierarchy; arbitrary user-defined nesting is a later
usability decision, not part of the first preview. These are UI groups, not new roadmap modules,
filesystem folders, authorization roles or reasons to duplicate module code.

| Navigation | Task pages / controls | Configuration belongs in |
|---|---|---|
| Home | One current next step; at most three prominent task actions, with one primary: Check setup, Practice recording, Make a clip. Completed setup changes the primary action; unrelated missing tools create no global red dashboard | Contextual guided setup, with an explicit link to the same Settings page |
| Stream | Preview & sound, Scenes; enabled Soundboard/overlays and optional Host/avatar/automation pages | Stream customization; camera/mic/account routing, OBS endpoints, encoder details and hotkey bindings in Settings/context panels |
| Create | Make a clip first; enabled image/thumbnail, Blender/scene-asset and sports-analysis pages | Per-job editing controls stay with the job; model/node/provider configuration belongs in Settings |
| Library | Recordings and exported clips, with source/content profile and processing state visible | Storage location, retention and optional backups in Settings; browsing local recordings never requires Docker/cloud |
| Settings | Guided setup; Profiles & accounts; Enabled tools; Advanced connections, services and diagnostics | The full catalog and technical configuration live here, grouped and searchable in the later implementation, rather than as top-level workspace buttons |

Recommend **Guided folders** for first use. **Compact rail** is an optional presentation for
someone already familiar with the tasks: a short labelled/accessible rail opens the same folder
tree. Both layouts expose the same capabilities and readiness rules. Keep layout preference
separate from feature enablement; a hidden navigation item does not revoke or grant permissions.
Settings must allow discovering and enabling optional tools without requiring a second installer.

#### Module groups for discovery, not backend boundaries

| Enabled-tools group | Existing modules surfaced or depended on |
|---|---|
| Streaming basics | `creator-experience`, `audio-production`, `soundboard` |
| Looks, overlays and avatars | `realtime-ai`, `broadcast-graphics`, `character-avatar` |
| Hosts and automation | `ai-agents`, `automation-control` |
| Clips and creative editing | `content-creation`, `image-editing` |
| Sports and motion | `sports-analytics` |
| Landscape and city assets | `nature-generation`, `cityscape-generation` — learned tiers retain their Pending gates |
| Accounts and promotion | `social-management`; `marketing-crosswalk` is identified as a repository CLI, not a shipped desktop page |
| Shared foundations and diagnostics | `storage-data`, `asset-pipeline`, `model-registry`, `backend-api`, `observability`, `infrastructure` |

Every module appears once in the discovery mapping; shared services are dependency-resolved
from selected capabilities. Basic OBS control/local recording and CPU clip work must not require
enabling Docker, generative AI, a cloud account, avatars or unattended automation. Dependency
checks remain installed/running/connected/verified, with the module's real evidence and status.
Navigation visibility never promotes a scaffolded capability or authorizes a Pending proposal.

#### Beginner task and live-safety contract

The first path is **choose streaming/creation goals → picture and microphone checks → short
off-air recording → review → make a clip**. Ask for only the inputs used by the next step;
show advanced values behind labelled configuration sections, with plain-language recovery for a
missing microphone, unavailable OBS or interrupted job. Account sign-in is needed for an external
broadcast, not for a local practice recording. Beginner and advanced presentation share the same
native validation and explicit final account/destination review.

When live, preserve an always-visible session strip across Home, Create, Library and Settings:
live destination/profile, recording ownership/state, microphone mute, Mark moment and End stream.
Critical stop/mute and failure/approval notices are never buried in collapsed folders, an overflow
menu or Advanced mode. Stream and Content profile selections remain separate; changing a Create
view does not change the pinned live destination or stop the owned recording. Mark moment is a
proposed marker action requiring its own real event/time mapping; it is not present today.

The primary cross-workspace product journey is the existing recording inbox into an actual
review/trim/export adapter for `stream_shorts`. Today's Start editing changes metadata only;
the combined app must not claim editing from that flag. Preserve the local original, reviewable
intervals, source/profile provenance and approved content destination. Heavy exports remain
deferred during live work by the resource policy; reviewing a cut never auto-publishes it.

#### Proposed UI injection and acceptance

Add proposed `configs/ui/combined-navigation.json` for stable group/page IDs, user labels,
module/capability mapping and default presentation. Proposed shared `Navigation.svelte` and
`Home.svelte`, plus `apps/extend/src/routes/+layout.svelte`, consume it through the existing
typed desktop adapter/session manager. Existing settings/setup/recording components provide the
underlying contracts; the clip page adapts the existing Content Creation CLI after that slice
is authorized. No new native command is authorized by a navigation configuration.

Extend U-01/U-02/U-07/U-09 with: first-run novice task completion and recovery without exposing
all modules; no more than three prominent Home task actions; single-pack operation without
unrelated readiness warnings; keyboard/touch folder access and usable labels at narrow widths;
enabled-tool discovery and disabled/planned states; navigation changes during a live session
preserving the pinned route, recording and visible stop/mute controls; and a real recording
becoming a reviewed cut and verified MP4, rather than an editing-status change.
The existing ST-T14/ST-T16 and CT-R15 lane items own those native/user acceptance repeats.
Usability is not proven by this source comparison or the isolated concept preview.

Planning verification is recorded at the end of §9 after the local documentation checks.

### Desktop shape

Propose `apps/extend/` as an internal source path, not an approved public brand. Build one Tauri
core and shell with workspace components extracted from the two current pages. Keep OBS, ComfyUI,
Blender, Krita, FFmpeg and speech/avatar workers in their existing local execution boundaries;
the shell orchestrates them. Do not run heavy work on the UI thread or promise that a shared core
cannot crash. Preserve direct OBS access and independent module CLIs as recovery paths.

Shared Home, Library and Settings surround Stream/Create workspaces. Profiles remain visible in
workspace context and managed in Settings; enabled Remote controls and setup use grouped navigation,
with critical approval/status notices available across pages.
An app-owned session manager retains streaming, recording and job state across navigation;
component unmounting cannot stop an active stream, reset ownership or leak polling listeners.
Commands belong to domains (`stream`, `content`, `settings`, `remote`) behind a shared typed
frontend adapter, with native validation independent of UI visibility.

```text
Packaged desktop UI → native validated commands → existing local tools/modules
                              ↓
                  shared settings, profiles, library, readiness

Optional browser → authenticated cloud API/relay → approved local command
                      ↓                              ↓
              opted-in metadata/proxies        workstation execution

Optional batch submission → private asset storage → one approved batch executor
                                                   → reviewed output
```

Live capture/rendering remains local. Local-first does not mean offline streaming to an external
platform; it means the app's core operation has no dependency on our cloud service.

### Cloud feature scope

Difficulty is a relative engineering assessment, not an estimate of elapsed time or a claim that
deployment is complete. Hosting existing APIs privately is less work than operating a public
multi-tenant product. A cloud-hosted download page can distribute the desktop immediately without
turning the software into a cloud runtime.

| Feature | Execution/data location | Suggested stage | Difficulty / main remaining work |
|---|---|---|---|
| Downloads, guides, release notes, workflow catalog metadata | Web hosting; local installer/runtime | Alongside desktop release | Low relative to runtime migration; artifact integrity, signing, support and truthful readiness still required. |
| Readiness, job status, last-seen and stream metrics dashboard | Optional sanitized metadata in cloud; probes on desktop | C1 companion MVP | Moderate: authenticated web UI, tenant scope, stale-state semantics, retention and hosted acceptance. |
| Content calendar, episode plans, scripts and publishing drafts | Local by default; opted-in documents in cloud | C1 | Moderate: document IDs, version conflicts, permissions and actual persisted plans. Scheduling a draft must not launch a local show. |
| Selected preset/workflow/profile sync | Cloud metadata; machine-specific endpoints stay local | C2 | Moderate: allowlisted fields and conflict UI. Never sync tokens, private file paths or hardware mappings as portable settings. |
| Recording/asset review and comments | Explicitly uploaded thumbnails/proxies in private object storage | C2 | Moderate–high: resumable uploads, access control, codecs, quotas, deletion and review links. Large recordings make upload/storage/egress a real cost. |
| Notifications | Local notifications first; cloud delivery after opt-in | C2 | Moderate: provider implementations/credentials, consent, delivery receipts and duplicate suppression; current push helpers are unfinished. |
| Remote scene/workflow controls | Cloud relays bounded messages; desktop approves and executes | C2 | High: capability-aware protocol, identity migration, revocation and real two-device acceptance. No public OBS/ComfyUI port. |
| Social review/approval and scheduled publishing | Drafts can be web-based; execution initially stays with local approved adapters | C2 review, C3 hosted publishing | High for unattended publishing: provider OAuth, server-side token custody, account routing, retry/idempotency and separate exact-job authorization. It will not run while the desktop sleeps unless a hosted adapter is built. |
| Backups of selected assets/project metadata | Private object storage, opt-in from desktop | C2 | Moderate–high: restore tests, checksums, retention, quotas and deletion; exclude credentials and licensed model weights by default. |
| Transcription, captions, Shorts exports, grading and other file jobs | Existing local path first; uploaded inputs processed in a cloud job | C3 | High: durable jobs, cancellation, deterministic manifests, privacy, cost caps and output download. Reuse module APIs/CLIs. |
| ComfyUI batch generation and headless Blender rendering | Opt-in GPU/CPU burst executor with explicit assets/models | C3 | High: hardware/model compatibility, model rights, reproducible tool versions, transfer time and spend limits. One executor first; no worker fleet. |
| OBS capture, live audio routing, soundboard, realtime effects/CV, game input, avatar playback | Creator workstation | Desktop only in this proposal | A full cloud substitute would require media transport, device/input/audio redesign and a different latency/reliability contract. |
| Interactive Krita/Blender/DaVinci editing | Installed desktop tools | Desktop only in this proposal | Remote desktop or a new web editor would be another product; do not promise feature parity from hosting the current Svelte UI. |

**C1 excludes:** remote execution, media upload, publishing, team collaboration, GPU provisioning
and billing. Start with one authenticated user/tenant; isolation tests still precede any external
accounts. C2/C3 need separately accepted queue items and updated operating-cost estimates. The
current product spec's prices and cloud feature list are assumptions, not a budget for this scope.

## 6. Direct injection map

All new paths/symbols below are Proposed. Existing modules keep their own ownership and setup docs.

| Location | Symbol/route/component | Before | Proposed change | Example | Verification |
|---|---|---|---|---|---|
| Both `apps/*/src/routes/+page.svelte`; new `apps/extend/src/routes/+page.svelte` | `activeView`, lifecycle polling, shared UI imports | Two root pages | Extract Stream/Create views, one navigation shell and session manager | Switch to Library during a live session | Navigation/unmount tests and native active-session pass |
| Both `src-tauri/src/lib.rs`; new `apps/extend/src-tauri/src/lib.rs` | `run`, `get_config`, `set_config`, `obs_start_stream_session`, `recordings_list`, `comfyui_queue_configured` | Separate registrations with overlapping names | One registration per domain; adapt existing handlers without changing their safety contracts | Domain-specific settings DTOs under one shell | Both app contract suites plus merged command tests |
| `apps/shared/ui/`; proposed `apps/shared/api-client/` | Shared components; new `DesktopServices` interface | Components invoke native commands directly | Isolate desktop transport from view models; any future browser adapter returns explicit unavailable capabilities | `stream.startSession` and `content.queueWorkflow` | Type checks; no native import in browser build |
| `configs/setup/`; `apps/shared/setup-engine/`, `setup-wizard/` | Product manifests, `SetupEngine::new` | Separate product selections/evidence | Versioned union manifest, per-capability selection, reuse setup locking; invalidate old observations when necessary | `enabled_packs: ["Stream", "Content"]` | Select/skip/retry/restart plus stale-evidence tests |
| Both `connection_settings.rs`; `apps/shared/local-settings/`; new `apps/extend/src-tauri/src/migration.rs` | `ConnectionPersistence`, `LocalSettings`, `OsCredentials` | Product-qualified files/secrets | Idempotent migration journal, conflict preview, separate original backups | Two different ComfyUI endpoints remain unresolved until selected | Crash/failure injection and real OS-vault migration |
| `apps/shared/recording-library/`, `social-manager/`; Stream session handlers | `RecordingLibrary`, `ActiveSelection`, session ownership | Shared files already in use | Reuse ledger and independent profile selections; unify display only | Finalized path opens in Create with source profile intact | P-065 contracts and playable recording acceptance |
| `apps/shared/relay-client/src/lib.rs`, `control.rs`; `cloud/relay-api/app/routers/relay.py`; `apps/shared/ui/RemoteControl.svelte` | `Product`, `DevicePresence`, `validate_command`, `_validate_relay_message` | Product enum/filter and action lists | Versioned capability discovery and server/client negotiation; retain bounded action validation and local approval | New peer advertises OBS and Comfy capabilities | Legacy/new relay matrix, isolation, denial, expiry and two-device action |
| Both `src-tauri/capabilities/`, `tauri.conf.json`, `build.rs`; new shell equivalents | IPC/plugin grants, CSP, resources, bundle ID | Separate privileges/resources | Audit minimum grants per surface; no wildcard union; bundle required guides/templates and enforce tested CSP | Only native UI may invoke local tool commands | Permission negatives, resource checks, packaged runtime pass |
| `.github/workflows/desktop-installers.yml`, `.github/workflows/ci.yml`; `tests/desktop_apps/` | Build matrix and installer contracts | Two product artifacts | Add combined prerelease target, retain legacy checks until retirement | One installer per supported OS/arch | Clean-host install, upgrade, rollback and signatures |
| `cloud/relay-api/app/routers/sync.py`, `metrics.py`, `notifications.py`; future companion UI path selected in C1 | Existing routers; new sanitized view contracts | API building blocks, unfinished push delivery | C1/C2 follow-ups expose only reviewed schemas; do not publish generic native commands | Versioned status DTO with observation time | Hosted tenant/auth/staleness tests before release |

## 7. Contracts and examples

### Local workspace configuration and migration

Example new non-secret shell document; values are illustrative:

```json
{
  "schema_version": 1,
  "enabled_packs": ["Stream", "Content"],
  "active_workspace": "stream",
  "cloud_enabled": false,
  "background_jobs_during_live": "defer",
  "migration": {
    "version": 1,
    "sources": ["com.streamextend.app", "com.creatorextend.app"],
    "state": "needs_review"
  }
}
```

Retain independent profile selections in the existing social contract. Reuse the shared recording
ledger without changing its schema in the first consolidation slice. Snapshot only metadata,
not media. No secret appears in migration previews, backups, logs or browser DTOs.

Migration states: `not_started → needs_review → applying → verified`; any failure becomes
`recoverable_error`. Validate source schema and current session state first. Missing one legacy
app is normal; unsupported/newer schemas block only import. Merge non-conflicting values, require
an explicit choice for conflicting endpoints/accounts, verify new OS-vault entries before marking
success, and retain old entries through rollback support. Interrupted work resumes by journal ID.
The migration must not run while legacy apps are writing settings or controlling a session.

Representative errors: `DEPENDENCY_MISSING`, `SETTINGS_CONFLICT`, `MIGRATION_INCOMPLETE`,
`CAPABILITY_DISABLED`, `LIVE_SESSION_BUSY`, `REMOTE_OFFLINE`, `PROTOCOL_UNSUPPORTED`,
`APPROVAL_EXPIRED`, `JOB_OUTCOME_UNKNOWN`. Native commands enforce these regardless of selected tab.

### Relay compatibility

Proposed version-2 discovery, **not accepted by today's protocol**:

```json
{
  "protocol_version": 2,
  "device_id": "paired-workstation-id",
  "capabilities": ["obs-control", "comfy-workflows"],
  "observed_at": "2026-10-04T12:00:00Z"
}
```

Capability presence supports discovery, not authorization. The authenticated session binds device
and tenant; the workstation revalidates readiness, action, profile/account, request expiry and local
approval immediately before execution. Preserve existing payload/message/queue bounds. Do not add
a new `Product` value without coordinated client/server rollout and a protocol negotiation test.
Unsupported peers receive an upgrade-required state; never silently widen either legacy app's
allowlist. Remote capability migration must pass before the combined app replaces either product.

New-device identity adoption or re-pairing must be explicit; do not reuse two legacy device IDs
concurrently or overwrite their tokens. Old peers retain their v1 discovery/control during the
compatibility window, with no implication that they can discover a v2 combined device.

### Cloud boundaries

Use opaque asset/job IDs, observed timestamps, revision checks and scoped tenant authorization in
cloud contracts. Local path references stay local. An uploaded proxy has separate consent, size,
checksum, retention and access policy; deleting a cloud proxy never deletes its local original.
Cloud batch manifests pin input hashes, workflow/tool/model versions, output destination and maximum
spend. Timeout yields an unknown/pending outcome until reconciled, not an automatic duplicate job.
Full HTTP/job schemas and storage migrations belong to separately accepted C1–C3 proposals.

## 8. Security, privacy, accessibility, and observability

- Keep secrets in the OS vault; treat bundled UI, external web content, local services and cloud
  sessions as different trust boundaries. Loading a cloud page into the desktop does not grant it
  native privileges. Tauri warns that overlapping window capabilities combine permissions; audit
  the merged grants explicitly. [Tauri capabilities](https://v2.tauri.app/security/capabilities/).
- Cloud sync is opt-in and field-allowlisted. Do not send recordings, prompts, account tokens or
  machine paths by default. Cloud retention/deletion and backup expiry must be stated before C1/C2
  release; public sharing links, if later added, expire and can be revoked.
- Private self-hosting uses Tailscale; hosted public endpoints require TLS and an authenticated
  application boundary. Keep OBS, ComfyUI, databases, admin views and local control ports private.
  Tenant checks apply to every asset/job/document ID; a storage prefix alone is not access control.
- Preserve per-action remote approval and social publishing gates. Revocation blocks new actions;
  stale approvals cannot replay after restart. No arbitrary shell or filesystem API is exposed.
- Use keyboard-accessible workspace switching, predictable focus, readable busy/error states and
  screen-reader labels. Always show the active profile and whether a destination is local/cloud.
- Record redacted migration version/results, readiness age, startup timing, owned job IDs and
  command outcomes locally. Cloud metrics are opt-in. Never log bearer tokens, full media paths or
  sensitive prompt content. Alert on repeated migration failures and unknown remote/job outcomes.

## 9. Test and pressure matrix

These are required future implementation checks; none is claimed as completed by writing this doc.

### Conditional acceptance-run consolidation (2026-11-07)

**Record:** `P072-ACCEPTANCE-20261107` — owner steering on acceptance testing, within existing
P-072; `gpt-6.1-sol` / `high` remains the assigned model/effort. No override or new proposal.

**Owner verbatim:** “Noticed stream-only and create-only testing.  We should look to just drop those once we confirm testing works for all features”

**State: recorded, conditional; not executed.** No tests, test selections or acceptance runs are
removed by this documentation change. The combined desktop has not yet verified every supported
Stream and Create workflow on each applicable platform; P-072 remains Testing. The comparison
below identifies coverage to reconcile, not evidence that those runs have passed.

**Answered owner direction:** retire the separate full Stream-only and Create-only acceptance
runs once the combined desktop proves all supported Stream and Create workflows, including the
cross-workspace journeys, on their applicable platforms. This concerns test runs; removing
user-facing modes, selectable packs or legacy apps is outside this decision. It consolidates
existing acceptance obligations, adds no release gate and requires no repeat owner approval.
**Question:** Should duplicate full single-mode acceptance runs retire once combined coverage is verified?

Before removing duplication, compare each single-mode run with the existing §3 feature inventory,
its module/proposal evidence and U-01 through U-09 below. Include controls that are not separate
navigation entries. For each supported workflow and applicable OS/architecture, retain the
artifact/build identity, prerequisites, actual result/output and evidence location; identify any
behavior or failure/recovery case exercised only by the single-mode run. Move that distinct
coverage into the combined journey or retain its focused check. Unproved, fenced or unavailable
workflows remain explicitly open; source presence, mocks, builds or a pass on another platform
cannot supply missing native/output evidence. Only demonstrated duplicate full runs retire in
ordinary test maintenance, with their replacement evidence recorded here and in the verification
matrix. Do not delete unique coverage merely because the combined app opens.

| Existing acceptance ID | Distinct behavior to preserve when comparing full runs |
|---|---|
| U-01 | Clean-host/offline first opening and usable setup on applicable platforms, including missing dependencies, skip and retry. |
| U-02 | Initial pack selection, enabling the other pack later, selection persistence across restarts, no duplicate installation and no unwanted background service startup. Retain focused checks while packs remain selectable. |
| U-03 | Neither/either/both legacy import paths, settings/profile identity, schema conflicts, corrupt state, locked vault, disk full and interrupted-write recovery. |
| U-04 | Stream controls and owned live/recording session safety while navigating between workspaces; external/pre-existing output and failed or uncertain start/Stop behavior; correct playable handoff and attribution. |
| U-05 | Supported Creator jobs during OBS work, resource contention and worker failure; responsive safety controls and unaffected modules. |
| U-06 | Setup/job cancel, retry and restart, shared locks, coexisting legacy apps and protection against duplicate controllers or destructive cleanup. |
| U-07 | Disabled capability enforcement in native invokes as well as UI visibility, crafted calls and untrusted/remote origins. Retain focused pack-denial checks while packs remain selectable. |
| U-08 | Applicable relay/device combinations, tenant/device/profile scope, stale or duplicate approval rejection and one correlated execution. |
| U-09 | All three real cross-workspace journeys: recording to reviewed Shorts; generated graphic to visible OBS overlay; recording through the selected Content profile to an approved private publishing test. Existing account/action decisions still apply. |

Inventory coverage includes the supported shared setup/connections/profile/relay paths, Stream
OBS/service/automation/audio controls, and Create workflow inputs/queue/history/preview, library,
Blender, Krita and optional analysis paths listed in §3. Link each applicable feature to actual
combined-desktop evidence rather than treating the U-ID table as a substitute for feature parity.

**Source inspection for this direction:** existing
[navigation tests](../../apps/extend/tests/navigation.test.js) distinguish pack visibility,
safe navigation after changing packs and enabled destinations;
[native preview tests](../../apps/extend/src-tauri/src/lib.rs) include Create-only observation
without OBS/vault access; [preview contracts](../../tests/desktop_apps/test_private_preview.py)
retain native pack admission. These demonstrate why focused selection/isolation checks are not
duplicate full journeys. They are not fresh native acceptance results. Restart persistence and
absence of unwanted service startup still need the applicable U-02 runtime evidence.

The earlier single-pack startup/resource comparisons remain useful focused configuration checks.
Once full-run equivalence is established, retain selecting/enabling a pack, restart persistence,
disabled capability denial and service-start isolation checks; do not rerun every Stream/Create
workflow separately solely to repeat proven combined coverage.

**Documentation verification — 2026-11-07:** Docs only row: 1,021 documentation tests passed
with no skips; generated-doc check, blocking Ruff, proposal model/lane report and diff checks
passed. Generation produced no registry changes. Runtime, tests, CI selection, queue status and
P-072 model assignment are unchanged. Full product/native acceptance and coverage equivalence
were not run by this documentation pass; no acceptance run is retired.

### macOS platform evidence (2026-11-07)

**State:** recorded macOS command/output evidence; combined UI coverage is **partial**.
P-072 remains Testing and `gpt-6.1-sol` / `high`; this documentation checkpoint does not
enable managed recording, close U-04/U-09 or accept PR97's runtime changes.

The owner supplied private evidence bundle `mac-equivalence-20261107-P6PeLk`, report
`REPORT.md` dated **2026-11-07T15:52:23-05:00**, observed host **arm64 macOS 27.2,
build 26B123**. Report SHA-256:
`9ac371b76ce662b4984b72f8155bd9c8dbc6ddcfe022654b275e8b1d4c6e6039`.
The existing host/dependencies are not clean-machine installation or a new support-matrix claim.

**Source attribution:** native-rehearsal commands and exports use PR97 exact
`0d2af40d20590a68935a6585bc4c9d57ad036962`. Combined desktop checks use `2f8de22`;
its `apps/extend` tree `21a90d716073673c4e1147dc90f28d0eca03bf0c` matches main
`f801fc4d66a665d7840ea5f34a134d76d9a306e7`. Source comparison across apps and
Creator Experience has no delta between those desktop revisions. The export and desktop branches
have not thereby been integrated end to end. Existing Python 3.12.13 and locked offline Rust
manifests were used; audio/soundboard setup had a fresh scoped module data directory.

| Recorded scope | Observed evidence and limit |
|---|---|
| PR97 macOS native-rehearsal job commands | All commands passed locally; **420 Python tests passed** (`native-python.log`, 97.14 seconds), same test paths and diagnostics plugin as the hosted job. This is local Mac execution, not Windows callback/ABI proof. |
| Shared setup and diagnostics | **7 setup-engine Rust tests passed** (`setup-rust.log`); plan, capture scan, module install/doctor and autopilot doctor exited zero. Capture scan establishes discovery only. |
| Native voice and synthetic Shorts | **11 smoke steps passed** (`autopilot/report.json`), including speech, clip review and rendering. OBS, gameplay, live chat and publication flags remain false. |
| Combined desktop contracts | **29 Node and 24 Rust tests passed** (`app-js.log`, `app-rust.log`). Stream adapter/controller: **69 passed, one existing ignored case** (`stream-rust.log`). Managed Start still rejects as unavailable before sending an OBS request. |
| Rendered Stream/Create/Both comparison | Headless Chrome on macOS with synthetic Tauri IPC: expected navigation, selections after reload, profile attribution, selected Stream controls and Content Library/catalog; Profiles at 320/736/1100 pixels (`workspace-check.log`). Create-only allows the status bootstrap for native-session recovery, with no other production commands. This is partial automated U-02 evidence, not native WebView restart, every feature or background-service acceptance. |
| Real local export files | A finalized 12-second synthetic picture/audio source went through the real stdio worker. Input before/after hashes agree; all three output hashes match. Separate FFmpeg validation decoded video and audio to EOF with fatal-error checking (`playback.json`, `exports/evidence.json`). No in-app Library export button or recording Start/Stop was used. |

| Preset | Dimensions / duration | Bytes | SHA-256 |
|---|---|---:|---|
| youtube-longform-v1 | 640 × 360 / 12.01 seconds | 1,093,754 | `77cbc28d4f77716929f9a4588585992aac942e182297a8c29567faad808d5ebc` |
| youtube-shorts-v1 | 720 × 1280 / 8.0 seconds | 832,044 | `96b49d07c7b07eea3dff4517e6abf64e929c3bedb01c9ab0d29735a53f3e70e1` |
| tiktok-local-v1 | 720 × 1280 / 8.0 seconds | 832,044 | `96b49d07c7b07eea3dff4517e6abf64e929c3bedb01c9ab0d29735a53f3e70e1` |

The coordinator inspected the supplied logs/JSON, verified the stored output hashes and desktop
tree comparison, and recorded their provenance without a duplicate product run. The files remain
private evidence; none is added to Git. Decoding is not subjective picture/listening acceptance.
The initial browser assumption of zero Create-only production calls was corrected to permit only
the session-recovery status bootstrap; the report retains this exclusion rather than claiming an
OBS-free native acceptance run.

**Still open:** PR97 Windows rehearsal at the same head is **cancelled**, and round-five
independent Astra review is **outstanding** after a quota failure without a verdict. These Mac
results do not replace either gate. Managed Start/destructive Stop remain unavailable pending
atomic ownership proof. U-04 in-app owned recording to playable output with correct Content
attribution, U-09 cross-workspace journeys, native Library export/playback, clean hosts, native
stress, migration, two-device/account and release acceptance remain unverified. Trusted native
launcher/helper certification is unchanged. No full test lane is retired under the conditional
direction above, and no fixture output authorizes re-enablement.

**Documentation-only validation:** 1,021 no-skip docs tests, Ruff, generated-doc, model/lane
and diff checks passed. Only the proposal, verification matrix and audit log change; no product
run, media decode, test selection, queue/model assignment or runtime code is changed by this pass.

### Supported recording API assessment (2026-11-07)

**Record:** P072-U04-SUPPORTED-API-20261107. **Blocked on an external supported
ownership contract; U-04 is not accepted.** Owner: “Complete these with T3”. This
bounded assessment retains P-072's `gpt-6.1-sol` / `high` assignment and the existing
writers. It does not resume the provider-rejected upstream proof, reproduce defects,
or authorize an alternative recorder, manual recording or a mock as U-04 evidence.

The installed application is **OBS 32.2.2**, bundle build `31845296735`. The official
[latest release](https://github.com/obsproject/obs-studio/releases/tag/33.0.1) is
**33.0.1**, published 2026-10-29. The coordinator inspected released public declarations
and protocol definitions for both versions; no OBS process, recording, output, setting,
credential or plugin was changed. The update was assessed, not installed.

| Supported surface | Verified contract and limit |
|---|---|
| 32.2.2 release WebSocket revision `1ef34bf48110c2a18184e50e41cd0b1a855e2147` | [Published protocol](https://github.com/obsproject/obs-websocket/blob/1ef34bf48110c2a18184e50e41cd0b1a855e2147/docs/generated/protocol.json): StartRecord and StopRecord have no request fields. StopRecord returns a path after stopping, not an ownership condition. |
| Released 33.0.1 bundled WebSocket revision `e28f84975984340e84fc4879cfc05741cc0afde1` | [Published protocol](https://github.com/obsproject/obs-websocket/blob/e28f84975984340e84fc4879cfc05741cc0afde1/docs/generated/protocol.json) retains the same recording request fields. StopOutput accepts an output name, with no expected recording generation or owner. GetRecordStatus reports activity, pause, duration and bytes; it does not issue an ownership token. |
| Public frontend and output APIs | Both released frontend headers declare parameterless recording start/stop and an accessor for the current output. The [frontend reference](https://docs.obsproject.com/reference-frontend-api) describes an output reference; the [output reference](https://docs.obsproject.com/reference-outputs) describes Stop on an output object. Neither documents a conditional stop for an expected recording activation or an exclusive reservation of the existing frontend recording lifecycle. |
| Vendor request bridge | CallVendorRequest transports a vendor-defined request; its presence does not supply a supported ownership implementation. No new vendor contract or plugin is claimed. |

**Conclusion (inference from these public contracts):** updating to the current stable
release does not provide the missing supported ownership condition for this adapter.
Object/name identity and a prior status observation do not document exclusive ownership
of a particular recording activation. The existing managed Start/destructive Stop fence
therefore remains unchanged. The existing static trusted-command/admission compatibility
check passed; no race reproduction, mutation, live output or rejected source proof ran.

**Exact external dependency and next safe action:** obtain a released, documented OBS-side
operation that binds Start to an owned recording activation and conditionally stops only
that activation, rejects stale ownership before effects, and yields its finalized output
identity. A supported exclusive lifecycle contract could satisfy the same requirement.
Reassess an actual supported release/vendor contract when available, then implement and
independently review its adapter before running isolated app-operated synthetic recording
→ Stop → playable picture/audio → correct Stream/Content Library attribution with unrelated
output preserved. This is an engineering dependency, not a request for an owner waiver.
No public upstream message is sent by this checkpoint.

Private evidence bundle `p072-supported-api-assessment-20261107` retains the installed
version, exact released headers/protocols, selected fields and SHA-256 manifest. Existing
PR100 macOS evidence remains reusable but does not complete this journey. PR97 Windows
diagnosis continues independently in the original Sol/high writer; its independent export
review remains Astra/xhigh on the final repaired head. Account/release decisions and the
conditional acceptance-run consolidation record above remain unchanged.

### Existing acceptance scenarios

| ID | Scenario | Expected result | Test level | Release gate |
|---|---|---|---|---|
| U-01 | Clean macOS/Windows, no developer tools or optional dependencies, no network | Installer opens usable setup; missing steps can be skipped and retried | Native clean-host | Preview and replacement |
| U-02 | Stream-only, Create-only, both; enable second pack later | No duplicate install or unrelated background processes; persisted selection | Rust/UI + native | Preview |
| U-03 | Import neither, either or both legacy apps; conflicting/corrupt/newer schema; locked vault; disk full; kill mid-write | No original loss, no secret leak, explicit conflicts, repeatable recovery | Fixtures/fault injection + real vault on both OSes | Upgrade |
| U-04 | Live stream while switching workspace; recording pre-exists or stream start fails | Session retained; only owned recording stopped; playable handoff without duplicate bytes | Existing fake-OBS tests + real picture/audio recording | Replacement |
| U-05 | Long ComfyUI/Blender job during OBS; low disk/memory; worker crash | Default defers new heavy batch jobs during live work; responsive Stop controls; unaffected modules continue | Stress/native, measured against Phase 0 budgets | Replacement |
| U-06 | Cancel/retry/restart setup and jobs; two legacy apps still installed | Shared locks work; no double controller, partial migration or destructive cleanup | Integration/native | Replacement |
| U-07 | Disabled capability, crafted invoke, untrusted preview or remote origin | Native validation denies unauthorized operation; no expanded wildcard privileges | Rust/security/UI | Preview and replacement |
| U-08 | Legacy/new relay combinations, wrong tenant/device, spoofed capabilities, duplicate or stale approval | Fail closed; correct correlated result; explicit unsupported state; approved action runs once | Loopback + hosted real two-device | Replacement for remote parity |
| U-09 | Three cross-workspace journeys | (1) recording → reviewed Shorts draft; (2) generated graphic → OBS overlay; (3) recording → Content profile → approved private publishing test | Real workflow evidence, dependencies in their existing proposals | Roadmap convergence |
| U-10 | Expired cloud session, desktop asleep, reconnect, stale status, conflicting document edits | Local operation continues; browser shows actual availability; no silent overwrite or queued-as-complete result | API/UI + hosted | C1/C2 only |
| U-11 | Proxy upload interrupted; quota exceeded; wrong-tenant download; delete/restore | Bounded resume, authorization, correct retention and original preserved | Integration/storage | C2 only |
| U-12 | Batch executor lost, duplicate submit, cost ceiling, cancellation, model/version mismatch | Durable outcome, no duplicate charge/work, hard admission budget, verifiable artifact | Job contracts + real small batch | C3 only |
| U-13 | Install combined update, then rollback; uninstall either legacy app | Shared environments, settings and recordings survive; incompatible state is not silently restored | Native both OSes | Public release |

Use the existing [verification matrix](../agent/VERIFICATION-MATRIX.md) row **Docs only** for this change, plus an explicit check that the queue and detailed
proposal carry the same model/effort/rationale. Future implementation inherits the rows for
P-003 settings/readiness, P-063 launch/setup, P-065 recordings/profiles, P-058 remote control and
Creator workflow inputs, plus each affected module's [acceptance checklist](../../tests/ACCEPTANCE-CHECKLIST.md).

Required implementation commands include `make test`; `npm run check` and `npm run build` in
each retained app and the new shell; `cargo test --locked --manifest-path <crate>/Cargo.toml` for
the affected apps/shared crates; and Python Ruff for any Python changes. Record actual counts,
native artifact hashes/OS and workflow outputs. A build or empty window does not satisfy U-04/U-09.

**Proposal verification — 2026-10-04:** the initial shared-checkout drafting pass recorded
19,849 documentation tests and a successful offline suite. That checkout also contained unrelated
uncommitted work. The publishable branch is based on `origin/main` at `1072ec6` and carries only
P-072 and its required documentation/index updates. On that isolated branch,
`PATH="$PWD/.venv-stream-autopilot/bin:$PATH" make test`
reached **100%, exit 0**. An explicit check resolved **192 local links/fragments across eight
changed documents**, including this new proposal, and verified matching model assignments, all
13 template sections and well-formed lane tables. `git diff --check` passed.
No merged binary, cloud deployment, native migration or performance benchmark was run.

**Beginner navigation planning verification — 2026-10-05:** inspected MYFeed's working UI
(based on `b2ff1c2`, with uncommitted changes) and clean OpenTechnologyApp `752b972`; reference
directories remained read-only. Produced an isolated two-layout concept using sample state,
with no native commands, workspace/provider APIs, camera access or external actions. Browser
checks passed guided setup → recording → cut review, interval updates, enabled-tool navigation,
live stop/mute across Create/Settings, safe state restoration, variant/drawer interactions and
1100/736/360/320px widths; screenshots were visually inspected. Existing UI/lane ownership and
all 21 module mappings were checked. Documentation/queue verification results are recorded
in the P-072 row after the local offline run. No combined application or beginner usability
acceptance is claimed; implementation gates, account routes and module statuses remain unchanged.

## 10. Delivery plan

| Phase | Deliverable / owner | Dependencies and gate |
|---|---|---|
| 0 — Baseline and contract | Owner + agent inventory every currently exposed workflow as verified/partial/planned, measure install/startup costs, map settings/commands/permissions and decide support targets | Planning is authorized now. Track unresolved live evidence under P-003/P-057/P-058/P-062/P-063/P-065 and release work under P-001. Record the five roadmap gates with links to evidence before approving the implementation slice; no assumption they already pass. |
| 1 — Shared shell preview | Agent implements one setup/navigation/profile/library shell and transports the two workspace views; owner evaluates simpler first run | Gate review and queue authorization for implementation; preserve old apps. Acceptance: U-01/U-02/U-07 plus both existing app checks. |
| 2 — Parity and migration | Agent resolves command/settings/relay identities, credential migration, session lifecycle, capability admission and resource policy | Owner-chosen bundle identity, rollback contract, real OS-vault/device access. Pass U-03–U-09; do not hide missing capabilities to claim parity. |
| 3 — Distributable desktop | Release owner produces signed platform artifacts, one download/install guide, migration notes, support diagnostics and a tested update path | P-001/P-063 release prerequisites; native clean-machine install and U-13. Retire old downloads only after the compatibility period and owner release decision. |
| C1 — Optional web companion | Separate proposal: authenticated status/metrics and opted-in planning/drafts | Stable desktop DTO/adapter contract, hosting/auth/tenant acceptance, retention and budget. No runtime migration prerequisite for desktop shipping. |
| C2 — Sync, review and remote actions | Separate proposals: conflict-safe sync, proxies/comments/backups, real notifications and approved remote actions | C1 plus provider/storage/two-device evidence, permission model and per-feature opt-in. |
| C3 — Cloud batch and publishing | Separate proposals for bounded rendering/transcription/export and any server-side publishing | Working single-node module path, provider/token/model rights review, durable job/cancel semantics, quotas and measured cost. |

Relative scope: shared shell is **medium**; production migration/distribution is **large**; a
companion is **medium-to-large**; public batch/publishing services are **large**; complete cloud
replacement is **very large and excluded**. These are planning judgments, not time commitments.
Re-estimate after Phase 0; consolidation must not wait for optional cloud features.

## 11. Rollout and rollback

Start as an opt-in combined preview beside the two existing installers. Use capability flags,
retain shared schemas initially, and reject concurrent legacy/unified control of an owned session.
App updates occur outside active broadcasts/renders; rollback never blindly kills an external job.
Keep legacy installers and original settings/vault entries for at least one explicitly documented
stable-release compatibility window. Preview support duration is set before broad distribution.

Rollback triggers include lost profiles/credentials, recording ownership regressions, setup failure,
remote privilege expansion or measured stream instability. Disable the affected capability/preview,
reconcile active jobs, then reopen the legacy app against its preserved settings. Do not overwrite
newer shared library/profile data with a stale backup; require reviewed reconciliation if a shared
schema ever changes. Uninstalling any shell must leave shared environments and user media intact.
Do not implement unattended bidirectional migration between old and new app settings.

## 12. Risks and unresolved decisions

| Item | Impact | Mitigation / decision owner | Due |
|---|---|---|---|
| One UI becomes crowded | Distribution simplifies but daily use becomes harder | Stream/Create workspaces, capability selection, progressive setup; owner tests both single-purpose journeys | Phase 1 |
| Larger installer and dependency footprint | More downloads and failed first-run installs | Bundle shared shell/resources once; optional tools/models on demand; measure size/actions | Phase 1 |
| Settings, secrets and device migration | Lost connections or wrong remote target | Journaled import, conflict preview, native vault migration, explicit pairing, rollback tests | Before Phase 2 |
| Broader failure/permission boundary | A Creator error affects live control or exposes native actions | Domain validation, least privilege, independent workers, timeouts and session manager; document residual shared-core risk | Phase 2 |
| GPU/CPU/disk contention | Render jobs cause dropped frames or broken recordings | Default defer new heavy batch jobs during live sessions; preflight already-running jobs before stream start; measured budgets | Phase 2 |
| Wrong profile/account after switching | Content posted or streamed to the wrong destination | Persist separate Stream/Content selections and pin live-session destination; explicit final action review | Phase 2 |
| Unfinished features mistaken for parity | “One app” becomes an accidental whole-platform rewrite | Inventory accepted versus planned paths, keep statuses/evidence and existing proposal ownership | Phase 0 onward |
| Public distribution still difficult | Unsigned apps or hidden prerequisites undermine handoff | Signing/notarization as applicable, clean-machine proof, one guide and bounded diagnostics | Phase 3 |
| Name, bundle ID, existing purchases and store listings | Broken upgrades, marketing or entitlements | Owner chooses brand and upgrade policy; coordinate P-023 and unresolved licensing decisions; no price change here | Identity before Phase 2; commercial terms before Phase 3 |
| Cloud transfer, GPU and support costs | Large bills or slower results than local execution | Measure representative jobs; per-tenant quotas, hard budgets, explicit upload and batch opt-in | Before C2/C3 acceptance |
| Cloud credentials, media and team isolation | New operational/security responsibility | Separate threat review, scoped auth, private objects, deletion/restore tests and provider-specific token custody | Before each cloud release |
| Delivery scope and dates | Consolidation stalls behind optional features | Desktop replaces two downloads independently of C1–C3; estimate from Phase 0 inventory | Phase 0 |

## 13. Documentation updates

This proposal change adds the queue row, this contract, the planning exception, pointers in
the roadmap/product spec, and P-072 owner-decision/manual-run entries in `docs/todo/`. Current app names, module statuses and runtime claims remain factual.
Proposal documents are indexed by the queue under the existing documentation-index convention.

When implementation ships, update `README.md`, `AGENTS.md`/`CLAUDE.md` product/path descriptions,
`docs/architecture/product-spec.md`, `roadmap.md`, `docs/PROJECT_CROSSWALK.md`,
`docs/AUDIT.md`, `docs/agent/VERIFICATION-MATRIX.md`, `SUBFEATURE-CHECKLIST.md`,
`tests/ACCEPTANCE-CHECKLIST.md`, affected module setup guides and
`modules/infrastructure/setup/desktop-setup.md`. Preserve `Content`/`Stream` module labels as
capability labels; changing packaging does not create new roadmap layers.

Update installer/build instructions, migration/rollback support, plugin integration references and
marketing subjects/anchors in the same release. Run `marketing-crosswalk validate`/`selftest` for
those claim changes. New configs/services need their module-item/config documentation, Compose and
`.env.example` entries as applicable. Cloud proposals must revise the product spec's cloud scope
and pricing assumptions explicitly instead of treating its historical cost figures as verified.

### Native preview and final Testing handoff — 2026-10-12

The final Mac debug bundle opened through the native UI tool and was moved to the built-in
Retina display before testing. Stream-only hides Create/Library; Create-only hides Stream; both
restore all task folders. Distinct Main Stream/Main Content profile kinds, the shared existing
inbox and bundled catalog render. Missing OBS/ComfyUI produce only relevant blocked observations.
A file-scheme endpoint is rejected and the prior valid address remains saved; valid recovery
works. Keyboard selection changes layout; quit/reopen restores compact layout and selected packs.
Shared setup loads without a cloud account/Docker, with zero selected installs; no install, account,
media edit or broadcast action was run. New library edit/publish and setup sync/record controls
are hidden/denied in preview. Screenshots exposed primary-hover and embedded setup contrast
issues; both are repaired and the rebuilt native layout visually checked. Workflow engineering
notes are collapsed behind friendly task names.

20 locked Rust tests, four Node tests, Python admission/permission checks and all three frontend
checks/builds pass. Legacy/shared crates pass; the CI-derived local verifier accounts for 47
commands (30 PASS, 17 NOT RUN), exit 0. Required `make test` reaches 100%, exit 0. Preserve the
private artifact/hash report under `output/release-evidence/p072-private-preview-2026-10-12/`;
source is an uncommitted worktree, not a signed/tagged release.

U-01/U-02/U-07 still need clean hosts, narrow widths/complete keyboard recovery, vault write/lock,
crafted/foreign-origin denial and synthetic import/reveal on this preview, plus Windows. Existing
legacy shared-inbox display is not new import/reveal acceptance. Real workflows, two devices,
parity/session controls, migration, budgets and public replacement remain gated. This closed
private build slice qualifies for Testing with remaining features/delivery; P-072 is not Done.
