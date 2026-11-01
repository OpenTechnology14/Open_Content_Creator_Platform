# Local verification and proposal reporting

Run from the repository root after installing the CI-pinned Python tooling and desktop
dependencies. Python uses the interpreter on PATH; put the prepared virtual environment first.

```bash
make verify ARGS=--list
make verify
make verify ARGS=--python-only
make proposal-report ARGS='--check --summary'
```

The verifier reads `.github/workflows/ci.yml` using YAML, expands the retained app and private-preview matrix entries,
and classifies every run command. It executes recognized local checks in CI order, preserves
the existing `.env`, and uses `.env.example` explicitly for Compose rendering. Installation
steps, service-starting acceptance and missing executables appear as NOT RUN. The report is
local coverage, not CI or release acceptance.

A failed/timed-out gate gives exit 1 after later checks finish. Invalid YAML, unrecognized
commands, unsafe directories or fewer than 15 eligible gates give exit 2 before execution.
`--timeout` bounds each check (default 1800 seconds). On timeout the process tree is stopped.
Adding a recognized check to CI automatically adds it to this run; a new command shape
requires explicit review in the classifier. Setup actions remain handled by the environment.

`python3 scripts/testing/doc_advisory.py` lists the documentation-update rules your change fires, from the files it touches
(working tree against `origin/main`; `--base REF` for another ref). It reads the `## Path triggers` table of
`docs/agent/DOC-UPDATE-MATRIX.md` through `docs/agent-registries/documentation.json`, advises only and always exits 0. It maps paths,
not meaning, so the judgement rules without a path row stay on the author. CI does not run it.

The proposal report emits derived JSON to stdout; it does not maintain a second hand-edited
queue. It distinguishes completion, standing practices and unfinished states, includes model
assignments, rejects duplicate/malformed/unassigned rows, and compares unfinished IDs with
the lane index. `--check` exits 1 on lane discrepancies; invalid queue input exits 2.
Status text and owner instructions remain authoritative, including explicit prerequisites.

Canonical documentation generation:

```bash
python3 scripts/testing/generate_docs.py --write
python3 scripts/testing/generate_docs.py --check
```

The explicit write command updates only AGENTS.md and the generated documentation registry.
Check mode is read-only and fails on full-file or source-data drift. Inspect generated diffs.

## Private release evidence (P-001 WP-7)

Inspect the plan in any checkout; collect evidence only from a clean repository root with no
local `.env`. Prepare CI-pinned Python tooling and native dependencies separately. Use a fresh
clone of the reviewed commit, rather than copying a workstation directory and its credentials.

```bash
python3 scripts/testing/release_check.py --list
python3 scripts/testing/release_check.py --checkout /path/to/clean-clone --output /path/to/new-evidence
python3 scripts/testing/release_check.py --checkout /path/to/clean-clone --output /path/to/python-evidence --python-only
```

The collector reuses the verifier's reviewed CI command allowlist. It does not install packages,
start services, build container images, publish artifacts or change source files. Desktop
checks/builds may write ignored build outputs. Every unavailable, live or out-of-scope command is
recorded as `NOT RUN`. Unknown CI command shapes reject the plan. Each executable check has a
bounded timeout; failures do not hide later checks. Tool stdout/stderr is discarded, so the bundle
cannot include test logs containing credentials or media paths. Rerun a failed command directly
in the clean checkout for local diagnostics.

`evidence.json` records commit/tree IDs, collector hash, OS/architecture, check exit codes and
durations, source stability, and separate unverified release gates. `SHA256SUMS.txt` hashes the
report and any explicitly supplied installer (`--artifact /path/to/installer.dmg`, repeatable).
Installers are hashed in place, never copied. Their names and bytes are public artifact metadata;
use distributable filenames. Supplied hashes do not establish which source built an installer.
Output must be a new directory outside the checkout; existing evidence is never overwritten.

Exit 0 means all executable checks passed and the source stayed clean; skipped checks are still
unverified. Exit 1 means a check failed/timed out or source changed; exit 2 rejects inputs or the
CI plan. **Every bundle has `release_ready=false`.** Licensing/governance, target selection,
full-history secret scanning, SBOM/license review, signing/provenance, native/live acceptance and
rollback remain separate release prerequisites. Keep this evidence private until those reviews.

On-demand audit/pre-merge instructions live in `.claude/commands/`; the capped evidence log
is [docs/AUDIT_LOG.md](../../docs/AUDIT_LOG.md). P-071 owns these tools.

## Required security lanes

Install `cloud/relay-api/requirements.txt` and `modules/backend-api/fastapi/requirements.txt` in
separate environments with pytest/PyYAML. Their HTTP dependency pins differ. Required security
CI runs `-p scripts.testing.no_skips`; selected security tests cannot silently skip on missing
dependencies. The live relay suite owns an ephemeral Postgres cluster/container and never tears
down the default creator stack. See `cloud/README.md` for upgrade and live-test prerequisites.

```bash
make verify ARGS='--relay-python /path/to/relay/bin/python --backend-python /path/to/backend/bin/python'
```

Interpreter overrides apply only to the two reviewed Python security jobs and preserve their
arguments. They do not install tooling or enable live tests. Default offline/claim checks use
the invoking interpreter. Docker, physical/native, account/provider and public release evidence
remain explicitly NOT RUN until their separate acceptance succeeds.
