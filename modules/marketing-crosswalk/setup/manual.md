# marketing-crosswalk — manual setup

**Labels:** `Content` · Automated path: [automated.md](automated.md)

Generates marketing content for the consumer modules registered in `crosswalk/modules.yml`. The
first is OpenTechApp's task-management module.

## Prerequisites

- Python 3.9+ with `pyyaml`
- Local checkouts of the registered targets: this platform, OpenTechnologyApp and
  OpenTechnologyBlog. Validation checks all registered targets, even for a single-module draft.

```bash
cd modules/marketing-crosswalk
pip install -r requirements.txt
```

## Point it at the target

Resolution order:

```bash
python3 -m generator.cli --target-path /path/to/OpenTechnologyApp validate
# or
export OPENTECHAPP_REPO_PATH=/path/to/OpenTechnologyApp
# or place the checkout at ../OpenTechnologyApp relative to this repo
```

Set `OTBLOG_REPO_PATH` for OpenTechnologyBlog if it is not at the sibling default path.
`HCP_REPO_PATH` overrides this platform's evidence checkout. See `crosswalk/targets.yml`
from the module root for the full mapping.

## Run

```bash
python3 -m generator.cli validate     # start here
python3 -m generator.cli coverage --module task-management
python3 -m generator.cli generate --module task-management --subject pm_requests --dry-run
```

Use `--asset walkthrough-brief` for a demonstration plan. Omit `--dry-run` to write into
ignored `out/`; repeated filenames are overwritten. Generation does not publish anything.

## Onboarding another module

This is the separate per-module step:

1. Add a row to `crosswalk/modules.yml` naming its `target` and `subjects` file.
2. Add `crosswalk/subjects/<module>.yml`. Every subject needs a `status` **and** a
   `status_evidence` file + text that exists in the target repo.
3. New target repo? Add it to `crosswalk/targets.yml` with the exact heading text of every anchor.
4. `validate`, then `coverage --module <name>`, then `generate --dry-run`.

Full detail in [the module README](../README.md) and [crosswalk/schema.md](../crosswalk/schema.md).

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `python3 -m generator.cli validate` — anchors and status claims
- `python3 -m generator.cli selftest` — every template renders
- `python3 -m ruff check generator/`

**Manual — nothing automates these:**

- [ ] `generate --dry-run` lists drafts without writing
- [ ] A generated draft's claims read correctly to a human — the tool checks status, not tone

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.
## Troubleshooting

- **"target repository not found"** — set `--target-path` or `$OPENTECHAPP_REPO_PATH`.
- **"anchor heading not found"** — a heading was reworded in the target repo. Update the anchor in
  `crosswalk/targets.yml` to the new text.
- **"status … cites … — evidence text is no longer present"** — the line backing a status claim
  changed. Re-read that file and update `status` and `status_evidence` together.
