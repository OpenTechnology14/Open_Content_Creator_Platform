# marketing-crosswalk — automated setup

**Labels:** `Content` · Manual path: [manual.md](manual.md)

This module *is* automation — a CLI, not a service. Setup is one dependency install.

```bash
cd modules/marketing-crosswalk
pip install -r requirements.txt     # pyyaml only
python3 -m generator.cli validate
```

No container, no port, no Compose service, no Make target. It reads the configured local git checkouts and
writes markdown.

## Commands

| Command | Purpose |
|---|---|
| `validate` | Marketing-doc anchors and status claims still hold in the target repo |
| `coverage` | Per-subject render/blocked counts and content-ledger gaps |
| `selftest` | Renders every template in memory; writes nothing |
| `generate` | Renders drafts to `out/`, or `--apply` to the target repo's draft dir |

## Target resolution

Targets and environment overrides are declared in `../crosswalk/targets.yml`.
The registry currently reads this platform, OpenTechnologyApp and OpenTechnologyBlog.
Use `OPENTECHAPP_REPO_PATH`, `OTBLOG_REPO_PATH` and `HCP_REPO_PATH` for their respective
checkouts. Selecting a module does not bypass validation of other registered targets.

## Not automated

Publishing. `--apply` writes drafts to a draft directory and never edits a marketing doc in place;
moving a draft into `MARKETING.md` is a human decision. Every draft carries a checklist of what
the generator could not know.
