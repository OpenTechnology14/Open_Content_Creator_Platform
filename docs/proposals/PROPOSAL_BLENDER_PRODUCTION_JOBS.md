# Proposal: Blender production-job lifecycle

**Queue row:** P-061
**Agent model / effort:** `gpt-6.1-sol` / `xhigh` — Native Blender job ownership, cancellation and restart recovery
Model assignment: [proposal queue policy](../PROPOSALS.md#agent-model-selection).
**Status:** In progress — owner requested continuing Sol implementation; [the queue](../PROPOSALS.md) is authoritative.
**Owner:** Owner + agent
**Date:** 2026-09-09
**Roadmap layer:** Content Creation
**Evidence level:** Verified current state; proposed implementation

## 1. Executive summary

**Implementation continuation, 2026-10-08:** use explicit scene selection and local-only PNG
still outputs as the conservative first job mode; no upload is implied. The job contract can
also accept names selected through Blender checkboxes later. Existing P-063 already added a
packaged synchronous batch script/planner; this replaces its unbounded all-scene rendering
with immutable attempt directories and observed lifecycle state. Native ownership/cancellation,
restart reporting and retry are implemented against fixed bundled code, not caller scripts.

Turn the Blender addon's documented batch-render stub into a bounded local production-job
lifecycle. A creator can choose eligible scenes, render them sequentially, see progress, cancel,
retry failed scenes and hand successful outputs to the existing asset pipeline. Creator Extend
shows observed Blender process and artifact state rather than optimistic completion messages.

## 2. Verified current state

- `CE_OT_BatchRender.execute()` reports that a batch started but contains only a TODO; no scene
  iteration, rendering or upload occurs.
- The single-output MinIO upload operator and ComfyUI handoff operator contain real code.
- `apps/creator-extend/src-tauri/src/blender.rs` can detect/open Blender and run one Python script,
  but has no job schema, process registry, progress, cancellation, retry or result history.
- The acceptance checklist correctly marks batch rendering blocked.

## 3. Problem, goals, and non-goals

Creators cannot rely on the advertised batch button or manage a long render from Creator Extend.
The goal is an honest, recoverable local job path with immutable manifests and explicit per-scene
results. This proposal does not add a render farm, Kubernetes, automatic marketplace publishing,
arbitrary remote scripts, or a new storage client.

## 4. User paths and states

First run verifies Blender, the project and output directory. Submission snapshots eligible scene
names and render settings into a job manifest. The job moves through queued, running, cancelling,
cancelled, complete or failed with per-scene progress. A missing dependency fails before start.
Invalid projects and paths are rejected. Retry creates a new attempt for failed scenes. Restart
recovers the saved job as interrupted until artifacts and processes are reconciled.

## 5. Architecture and data flow

Blender and rendering remain local. Creator Extend launches a fixed bundled script with argument
arrays, never a shell or caller-supplied script path. The script writes an atomic local manifest;
successful outputs use the existing MinIO/S3 contract. Credentials remain in Blender preferences
or the OS credential store and never enter manifests. Remote approval may request a known job
operation later, but cannot submit arbitrary code or paths.

## 6. Direct injection map

| Location | Surface | Before | Proposed change | Verification |
|---|---|---|---|---|
| `plugins/blender-addon/operators/__init__.py` | `CE_OT_BatchRender` | Optimistic stub | Validate selection and submit/observe a real local job | Blender operator acceptance |
| `modules/content-creation/blender/` | Production runner | README only | Add fixed batch script, schema and atomic manifest writer | Python contract tests + Blender live run |
| `apps/creator-extend/src-tauri/src/blender.rs` | Process control | Open/run one script | Add bounded job owner, status, cancel, retry and recovery | Rust process contracts |
| `apps/creator-extend/src-tauri/src/lib.rs` | Tauri commands | No job commands | Register typed job operations | Command allowlist tests |
| `apps/creator-extend/src/routes/+page.svelte` | Production UI | No Blender job view | Show submission, progress, per-scene results and recovery | Svelte + native UI acceptance |
| `modules/content-creation/setup/` | Setup/readiness | Stub disclosure | Add exact dependency and live verification steps | Setup tests and manual Blender run |

## 7. Contracts and compatibility

The versioned job manifest includes job/attempt IDs, canonical project and output roots, selected
scene names, timestamps, per-scene state, artifact metadata and upload state. IDs and counts are
bounded. Existing open, single-upload and ComfyUI operators remain compatible. Outputs never
overwrite an existing attempt. Only canonical paths under operator-approved roots are accepted.

## 8. Security, privacy, accessibility, and observability

No arbitrary command, script or environment injection is accepted. Logs redact credentials and
bound the amount of Blender output retained in the UI. Progress and terminal states are keyboard and screen-reader
accessible. Record job duration, scene counts, failure class and upload outcome without project
contents. Local project files and renders remain local unless upload is explicitly enabled.

## 9. Test and pressure matrix

| ID | Scenario | Expected result | Level | Release gate |
|---|---|---|---|---|
| B1 | Missing Blender or invalid project | Preflight fails; no process starts | Automated contract | Phase 1 |
| B2 | Two eligible scenes | Each renders once and manifest completes | Real Blender | Phase 1 |
| B3 | One scene fails | Other result remains; job reports partial failure | Contract + live | Phase 1 |
| B4 | Cancel during render | Process receives bounded termination and job does not claim complete | Rust/live | Phase 2 |
| B5 | Retry failed scene | New attempt preserves earlier artifacts | Contract + live | Phase 2 |
| B6 | App restart during job | Recovered state is interrupted or reconciled from real process/artifacts | Rust/native | Phase 2 |
| B7 | Upload enabled | Every successful artifact reaches configured bucket once | Live MinIO | Phase 3 |
| B8 | Path/script injection attempt | Request is rejected before process launch | Automated security | Every phase |

## 10. Delivery plan

1. Define the job/manifest contract and fixed Blender batch runner.
2. Replace the addon stub with real sequential scene rendering and per-scene results.
3. Add Creator Extend process ownership, progress, cancellation, retry and restart recovery.
4. Add optional asset-pipeline handoff and retained output history.
5. Run native macOS and Windows Blender acceptance before changing capability status.

## 11. Rollout and rollback

Keep the feature behind a local readiness check. On rollback, hide job submission while retaining
read-only manifests and the existing single-render operators. No project or output is deleted.

## 12. Risks and unresolved decisions

| Item | Impact | Decision owner |
|---|---|---|
| Scene eligibility marker versus explicit selection UI | Defines stable job input | Owner + UX |
| Blender versions supported on macOS/Windows | Affects scripting and packaging | Implementation |
| Cancellation strategy per render engine | Determines recovery guarantees | Implementation |
| Default upload policy and bucket | Affects storage cost and privacy | Owner |

## 13. Documentation updates

### Implementation verification — 2026-10-09

- Fixed worker now performs explicit, bounded PNG still jobs with unique attempt directories,
  atomic per-scene state, preserved source settings and successful-artifact hashes/dimensions.
- Native owner provides start/status/list/cancel/retry, one owned job per app session, bounded
  logs and timeout. Restart never claims/kills a persisted PID; interrupted retry needs operator
  confirmation. Project changes and tampered/missing artifacts reject reuse.
- Creator UI adds scene checkboxes and observed progress/cancel/retry under the existing tool
  workspace. Addon stub replaced with a modal owned job and no implicit upload.
- Ten Python cases and five Rust process contracts passed; Svelte check reports zero errors
  or warnings and frontend/native debug bundle builds pass (one pre-existing unused run_script warning).
- Real Blender 5.2.1 LTS on arm64/16 GiB Mac: two selected scenes rendered to verified 64×64
  PNGs; a no-camera scene failed while a subsequent successful output was retained. The actual
  native owner smoke also completed, validated both checksums and returned success in 1.79s.
- Legacy scene-label path escape reproduced using the previous script in an isolated temporary
  fixture; numeric output filenames now prevent that escape. Initial real native smoke caught
  Blender's Zstandard-compressed saved-file header; supported compressed signatures now pass.
- Artifacts: ignored `output/blender-lifecycle.fL11DI/`; logs `/tmp/hcp-blender-native-live.log`
  and `/tmp/hcp-blender-partial.log`. No user project, account, stream or existing output was altered.

The Mac is locked, so native UI acceptance could not proceed. First mode supports PNG stills,
not animation; optional batch asset-pipeline upload and full physical Windows/native/addon UI
acceptance remain open. This is implementation progress, not promotion of Content Creation.
Final required staged `make test` reached 100%, exit 0 (`/tmp/hcp-blender-offline-final.log`),
all ordinary Creator native suites passed, and Ruff/Svelte/build/generated-doc/diff checks passed.
The real native-owned job test is opt-in and passed separately; default CI does not claim
that Blender is installed or that physical/native UI acceptance was performed.

**Hosted verification, 2026-10-09:** CI `37885607341` at `dd17563` passed generated docs,
blocking lint/offline/live acceptance and both desktop build/native-contract jobs. Native
smoke `37885607245` passed both macOS/Windows rehearsals. This verifies the implemented
local still mode; it does not close the locked-Mac GUI, physical Windows, animation or
optional batch upload gates. The remaining work is explicitly retained rather than marked Done.

**Retry verification follow-up, 2026-10-09:** six ordinary Rust contracts passed (one
real-Blender test remains opt-in). The new contract proves that changed source bytes reject
retry before creating an attempt, completed scenes are excluded from the child command, and
the parent manifest/output remain byte-for-byte unchanged after cancelling the retry. The
expanded real Blender smoke passed in 4.34s: two-scene success, a partial failure with a retained
PNG, and a new attempt containing only the failed no-camera scene. That scene correctly failed
again; the successful parent PNG was preserved. Logs: `/tmp/hcp-blender-retry-live.log`.
These checks strengthen B3/B5 evidence; they do not substitute for native UI or Windows acceptance.

The addon monitor also reproduced three exceptions before the fix: deleted log file,
malformed JSON and a non-object manifest. Regression cases now pass: unavailable logs do not
abandon process observation, unreadable terminal manifests report failure and release the timer,
and damaged cancellation manifests are retained rather than replaced with invented state.
The focused addon/worker run passed 22 cases; targeted Ruff passed. Native Blender UI acceptance
is still required for the modal operator itself.
Required `make test` reached 100%, exit 0 (`/tmp/hcp-blender-retry-offline-final.log`).
Creator Svelte check returned zero errors/warnings; frontend build and native debug `.app`
bundle passed (`/tmp/hcp-blender-retry-bundle.log`). Generated documentation freshness,
eight generated-doc contracts, Rust formatting, blocking module/script Ruff and diff checks passed.

Update the Content Creation README/setup guides, Blender addon docs, Creator Extend help,
`docs/AUDIT.md`, module matrices, verification matrix, acceptance checklist and queue evidence as
phases are implemented.
