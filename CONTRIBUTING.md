# Contributing to Open Content Creator Platform

Thank you for wanting to help. This guide covers how to propose a change, what to run before you open a pull request,
and what a good description says. By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

The project is **pre-release** (see the status note in the [README](README.md)). Small, well-tested changes are the
easiest to review. For anything large, open an issue first so we can agree on the shape before you write it.

## Ways to help

- **Report a bug** with the steps to reproduce it, using synthetic data. Never paste a token, a stream key or a private
  recording. For a security problem, follow [`SECURITY.md`](SECURITY.md) instead of opening an issue.
- **Improve the documentation.** A wrong or missing step in a `setup/manual.md` is a real bug.
- **Add or extend a module.** The module is the unit of contribution (below).
- **Test on a platform we have not verified.** Hardware-dependent changes need a repeatable evidence record when a
  deterministic fixture is not possible; say what you ran and on what.

## How the project is organised

- **Pick the layer first.** Every module belongs to a layer in [`docs/architecture/roadmap.md`](docs/architecture/roadmap.md)
  and lives in `modules/<name>/`. Keep a change inside its module boundary; modules must run on their own.
- **Read the working rules.** [`CLAUDE.md`](CLAUDE.md) §2 (principles), §4 (modules and labels) and §9 (how to add a feature
  or fix a bug) are the contract. [`AGENTS.md`](AGENTS.md) is the same guidance for AI coding tools.
- **A new module needs a proposal.** Cross-module, setup, cloud, privacy or public-API changes start from a proposal, using
  [`docs/PROPOSAL_CREATION_SOP.md`](docs/PROPOSAL_CREATION_SOP.md). The maintainer accepts proposals; a row in
  [`docs/PROPOSALS.md`](docs/PROPOSALS.md) marked Pending is not permission to start.

## Set up

Install Node.js 22, stable Rust and Python 3.11 or newer; the [README](README.md#install-from-source) has the steps, and
[`modules/infrastructure/setup/desktop-setup.md`](modules/infrastructure/setup/desktop-setup.md) covers the desktop apps.
Docker is needed only for the service stack and the acceptance harness.

## Before you open a change

1. Choose the layer and keep the change inside its `modules/<layer>` folder.
2. Do not add secrets, recordings, model weights, private creator assets or binaries over 5 MB. Weights belong in
   object storage, with an entry in [`modules/model-registry`](modules/model-registry/README.md).
3. Put configuration in environment or config files and update `.env.example` in the same change.
4. Add tests for success, failure and recovery. If the harness you need does not exist, say so in the pull request rather than
   claiming coverage.
5. Fix a bug test-first: write a test that fails, then the fix, and confirm the test fails again if you revert the fix.

## Checks

Run the ones that cover what you changed:

```bash
make test                                   # the offline suite; about a minute, needs no service
make verify ARGS=--list                     # every CI-derived check, and which this machine cannot run
ruff check modules/ scripts/                # blocking in CI
python3 scripts/testing/generate_docs.py --check   # generated documents are current
python3 scripts/testing/public_release_guard.py    # no private row, local path or license mismatch
python3 scripts/testing/doc_advisory.py            # which doc-update rules this change fires (advisory)
make test-acceptance                        # the creator-journey harness; needs Docker
docker compose -f docker-compose.yml config -q
```

For a desktop app change also run its frontend check and Rust tests, for example
`npm --prefix apps/stream-extend run check` and `cargo test --locked --manifest-path apps/stream-extend/src-tauri/Cargo.toml`.
[`docs/GAP_AUDIT.md`](docs/GAP_AUDIT.md) tracks what is still genuinely open; a failing check you did not cause belongs
there, not in your pull request.

## Change quality

- Type the public Python functions and use Pydantic v2 models for API bodies.
- Use ESM for TypeScript, and quote Bash expansions; scripts start with `set -euo pipefail`.
- Preserve offline, local operation for the core creator workflows.
- Never put a cloud call in the realtime video or audio path.
- Keep Kubernetes out of scope until the roadmap permits it.

## Commits and pull requests

Use [Conventional Commits](https://www.conventionalcommits.org/) with the module as the scope, for example
`feat(sports-analytics): add club detector`. A pull request description should state:

- the **user outcome** and the **layer** it touches;
- the **exact verification** you ran, and what you could not run;
- the **privacy and security impact**, and any configuration or documentation change;
- how to **roll it back**.

Label a scaffold or a proposal as one; never describe it as finished.

## Licensing of contributions

This repository is under the [MIT License](LICENSE). By submitting a contribution you agree that it is licensed under the
same terms, unless the directory you change carries its own license (for example [`plugins/`](plugins/LICENSE)). There is no
contributor license agreement. The maintainer may later ask for a sign-off on each commit; if so, this file will say so.

## AI-assisted contributions

Much of this repository is written with AI coding tools, under the rules in [`AGENTS.md`](AGENTS.md). Contributions made
with them are welcome on the same terms: you are responsible for what you submit, it must pass the same checks, and it must
not contain material you have no right to contribute. Do not paste output that reproduces someone else's copyrighted work.
