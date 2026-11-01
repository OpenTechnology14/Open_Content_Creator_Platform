---
name: code-creation
description: Rules for writing code in the Open Content Creator Platform - adding or changing anything under modules/, apps/, plugins/ or scripts/; language conventions; the Blender still-job lifecycle (blender_jobs.rs, the Blender addon, the fixed batch worker); and test discipline (fail-before-fix, mutation checks, the verification matrix). Use before creating a module or a check, before touching process, path or credential handling, and before claiming a change works.
when_to_use: "Examples: 'add a module', 'fix this bug in modules/…', 'change the Blender job code', 'does this need a test?', 'is it safe to say this works?'. Load before writing or editing code under modules/, apps/, plugins/ or scripts/."
---

# Code creation

If this skill and a cited doc disagree, **the doc wins** - fix the skill. It summarises; it does not
replace `CLAUDE.md` (mirrored for other tools as `AGENTS.md`), `docs/agent/VERIFICATION-MATRIX.md`
or the owning proposal.

**Register first.** Before Step 1, register the task with its one Kind (`CLAUDE.md` section 17, the entry gate). A bug fix, a feature slice and a tests-only wave are different Kinds; work with no row does not start.

## Step 1 - place the work before writing it

1. Name the **roadmap layer** (`docs/architecture/roadmap.md`) and put code in that `modules/<layer>/`.
   If the request contradicts the roadmap's layering or order, surface the conflict and ask; if it
   proceeds, record it in `docs/architecture/deviations.md` (`DM-DEVIATION`).
2. Read the module's `README.md` and `setup/manual.md` for its scope. If the feature exceeds it, flag it.
3. **Module work is proposal work.** Find or add the row in `docs/PROPOSALS.md` first
   (`docs/PROPOSAL_CREATION_SOP.md` § "Module work is proposal work"). The row names an agent model,
   reasoning effort and rationale; an assignment does not authorise Pending or Deferred work.
4. Inspect `git status`, open PRs and worktrees for overlapping work (`.claude/commands/pre-merge.md`
   does the same). Preserve unrelated work: if the checkout holds uncommitted changes you did not
   make, use a separate worktree and never clean up what you did not create.

## Step 2 - boundaries that do not bend (`CLAUDE.md` §2, §10)

- **Local-first.** OBS, webcam, realtime inference and overlays never depend on a network round trip.
- **Modules are independent.** `sports-analytics` must not import `realtime-ai`; shared data goes
  through `backend-api`. A broken module must not break another.
- **Configuration over code.** Local-versus-DigitalOcean differences live in `configs/`. No hardcoded
  `localhost` in module code - use compose service names or environment variables.
- **No Kubernetes, service mesh or distributed workers** before `docs/architecture/k8s-decision.md`'s
  four conditions hold. **No public exposure** without an auth layer. **No binary over 5 MB** or model
  weights in git (MinIO / DO Spaces).
- A new environment variable goes in `.env.example` in the same commit; secrets never in git.

## Step 3 - adding a module (the checklist `DM-MODULE` enforces)

| Needed | Where |
|---|---|
| Proposal row | `docs/PROPOSALS.md` |
| Roadmap layer + deviation entry | `docs/architecture/roadmap.md`, `docs/architecture/deviations.md` |
| Labels `Content` / `Stream` / both | `CLAUDE.md` §4 and §11, `modules/README.md` |
| `setup/manual.md` **and** `setup/automated.md` | the module; if nothing is automated, say so plainly |
| Matrix rows | `docs/agent/MODULE-MATRIX.md`, `MODULE-ITEM-MATRIX.md`, `SUBFEATURE-CHECKLIST.md` |
| Status row (`scaffolded` until evidenced) | `CLAUDE.md` §11 |

A **registry row** in `modules/marketing-crosswalk` is *not* a new module - see the `docs` skill.
Then run `python3 scripts/testing/generate_docs.py --write` and `--check` (`DM-CONTEXT`).

## Step 4 - conventions (`CLAUDE.md` §6)

- **Python 3.11+**: `ruff`, type hints on public functions, async FastAPI, pydantic v2 request/response
  models, `loguru`, no prints on production paths.
- **TypeScript**: ESM only, Prettier defaults. **Bash**: `set -euo pipefail`, quote every expansion,
  a `--help` flag, and it must parse under macOS bash 3.2 (no `mapfile`).
- **Commits**: Conventional Commits with the module as scope, e.g. `feat(sports-analytics): ...`.
- Offline by default: tests take no service, network or GPU. Live work is marked `live` and excluded
  from `make test`.

## The Blender still-job lifecycle (P-061)

Read `docs/proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md` before touching any of these files.

| Piece | File |
|---|---|
| Native owner (start, status, list, cancel, retry) | `apps/creator-extend/src-tauri/src/blender_jobs.rs`, `blender.rs` |
| Fixed bundled worker | `modules/content-creation/blender/scripts/batch_render.py` |
| Addon operator (modal, owned job) | `plugins/blender-addon/operators/__init__.py` |
| Contracts | `apps/creator-extend/src-tauri/tests/blender_jobs_contract.rs`, `tests/content_creation/test_blender_jobs.py`, `tests/blender_addon/test_batch_lifecycle.py` |

The rules the code and tests already enforce - break none of them:

1. **Fixed script, argument arrays.** Launch the bundled worker with an argument array: never a shell,
   never a caller-supplied script, path or environment. Only canonical paths under operator-approved
   roots are accepted. An invalid project path, an empty selection or a traversing job ID is rejected
   before the job library is even created; a missing Blender executable fails the job *without* spawning
   a process or rendering output, and the failed job stays listed.
2. **First mode is explicit scene selection and local PNG stills.** No implicit upload; credentials never
   enter a manifest.
3. **Immutable attempts.** Every attempt gets a fresh directory; earlier artifacts are never overwritten.
   Output filenames are numeric so a scene label cannot escape the output path. Manifests are written
   atomically, per scene, and successful artifacts record a hash and dimensions.
4. **Ownership is observed, not assumed.** One owned job per app session, bounded logs, a timeout, and a
   bounded termination on cancel. **Persisted metadata never authorises killing a PID.** After a restart a
   saved job reads as `interrupted`, and retrying it needs operator confirmation.
5. **Retry is conservative.** Changed project bytes, tampered or missing artifacts reject reuse; retry
   re-runs only failed scenes; cancelling a retry leaves the parent manifest byte-for-byte unchanged.
6. **The monitor survives damaged state.** A deleted log, malformed JSON or a non-object manifest must not
   abandon observation: an unreadable terminal manifest reports failure and releases the timer, and a
   damaged cancellation manifest is retained rather than replaced with invented state.
7. **Never report optimistic completion.** Status is what the process and artifacts show. The real-Blender
   smoke is opt-in (`#[ignore]`), so default CI never claims Blender is installed, and a headless pass does
   not promote the capability: native GUI and physical Windows acceptance stay separate.

## Test discipline (`CLAUDE.md` §9, `docs/agent/VERIFICATION-MATRIX.md`)

- **Bug fix = a test that fails before and passes after.** Reproduce locally first. Prove the test by
  reverting the fix and watching it fail. A test written after the fact that never saw the bug proves nothing.
- **Mutation-check every new guard.** Break each rule once, confirm a test fails, restore. Name tests for
  the behaviour they pin (`missing_dependency_fails_without_process_or_rendered_output`), not the function.
- **Look the change up in the matrix** and run that row: `make test` is the required offline suite;
  `ruff check modules/ scripts/` is blocking; `make verify` runs the recognised CI gates and lists every
  NOT RUN check (`make verify ARGS=--list` shows the plan); `python3 scripts/testing/generate_docs.py --check`
  guards generated docs. Security contracts also run with `-p scripts.testing.no_skips`.
- **Report the row and its result**, and what you could not run and why. "Tested" is not a verification.
- **No fix-until-green** (`CLAUDE.md` §13). If a draft needs more than small corrections, discard it and
  write it directly; iterating toward a passing test is how wrong code acquires a green check.
- **CI can be unavailable.** Check why before saying a PR is red: a job that fails in seconds with zero
  steps and a spending-limit annotation is the account billing block, not your change. Say so; do not
  merge on it, and do not describe a local run as green CI.

## Paths that need the full bar with any model or tool (`CLAUDE.md` §13)

`apps/*/src-tauri/**`, `modules/character-avatar/**`, `configs/local/**` where credentials are involved,
cross-app orchestration (the shared `recording-library`, `local-settings`, `social-manager` crates), and
streaming or gameplay pipeline changes. A wrong capability file or a dropped stale-event guard compiles,
passes tests and fails silently. Do not hand these to a cheap first-draft pass.

## Sources

`CLAUDE.md` §2, §4, §6, §9, §10, §13 - `docs/PROPOSAL_CREATION_SOP.md` - `docs/agent/VERIFICATION-MATRIX.md`
- `docs/agent/DOC-UPDATE-MATRIX.md` - `docs/proposals/PROPOSAL_BLENDER_PRODUCTION_JOBS.md` (§ Implementation
verification) - `scripts/testing/README.md`.
