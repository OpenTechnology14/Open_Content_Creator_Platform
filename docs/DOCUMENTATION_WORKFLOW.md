# Essential document workflow

> **Status:** Living · **Last reviewed:** 2026-09-30 · **Owner:** OpenTechnology14

**Enforcement: reference.** This guide applies the existing [doc update rules](agent/DOC-UPDATE-MATRIX.md)
and [verification requirements](agent/VERIFICATION-MATRIX.md). The [documentation index](README.md)
remains the full catalog; the [project crosswalk](PROJECT_CROSSWALK.md) connects it to implementation.
Neither this guide nor the project crosswalk currently has an automatic regeneration command.

## Essential documents by decision

Update these existing documents in place rather than starting another competing status report.

| Decision or handoff | Document to maintain | Inputs and refresh trigger |
|---|---|---|
| Product scope and module boundary | [Roadmap](architecture/roadmap.md), [product spec](architecture/product-spec.md) | Accepted architecture/product decisions; record ordering exceptions in [deviations](architecture/deviations.md) |
| Navigate from a product to its implementation | [Project crosswalk](PROJECT_CROSSWALK.md) | Module labels, shared app packages and proposal relationships; refresh when those change |
| Authorize and track work | [Proposal queue](PROPOSALS.md) and [proposal template](proposals/TEMPLATE_PROPOSAL.md) | Owner request, concrete scope and acceptance criteria; record verification before closing |
| Install and operate a capability | Module-owned setup guides, reached through the [module index](../modules/README.md) | Real commands/configuration; update after walking setup and discovering drift |
| Decide whether a capability works | [Audit](AUDIT.md), [subfeature checklist](agent/SUBFEATURE-CHECKLIST.md), [acceptance checklist](../tests/ACCEPTANCE-CHECKLIST.md) | Dated commands, outputs and live/manual artifacts; a build alone cannot promote capability status |
| Validate a complete creator journey | [Use cases](../tests/USE-CASES.md) | Actual cross-module handoffs, failure/recovery results and remaining manual steps |
| Prepare a release | [Release checklist](OPEN_SOURCE_RELEASE_CHECKLIST.md), [repository alignment](REPOSITORY_ALIGNMENT.md) | Licensing decision, accepted capabilities, canonical commit, export/build evidence and rollback |
| Produce marketing drafts | [Marketing registry and generator](../modules/marketing-crosswalk/README.md) | Registered consumers, source anchors, subject evidence and supported asset templates |

## Preparing or refreshing a document

Canonical queue, lane-index, module-status, matrix-rule and CLAUDE instruction edits must be
followed by `python3 scripts/testing/generate_docs.py --write`, diff review and `--check`.
The generated data is derived; readable sources remain authoritative.

1. Start with the owning source in the table. Check the proposal state and dated evidence before
   turning planned behavior into a claim. Keep historical verification dated.
2. Update the existing document, or add a new one only when it answers a distinct question.
   Include its purpose, source links, review date and whether it is guidance or a requirement.
3. Link every new document from the [index](README.md); proposal documents instead need a queue
   row. Apply the relevant [doc update matrix](agent/DOC-UPDATE-MATRIX.md) rules in the same change.
4. From the repository root, run `make test` and `git diff --check`. Inspect links in newly created
   files explicitly: the existing relative-link test selects tracked Markdown, so an untracked
   file can be omitted even when the suite passes. Check heading fragments as well as file paths.
5. Record the commands, exit codes, results and unrun checks in the owning proposal. Documentation
   verification proves the reference structure; live capability acceptance still needs its own
   evidence. Only then close the documentation work.

## Marketing drafts and coverage

The marketing crosswalk is distinct from the project crosswalk. Its canonical
[consumer registry](../modules/marketing-crosswalk/crosswalk/modules.yml) chooses which products
or learning modules receive content. It does not automatically onboard every platform module.
This platform's own go-to-market plan is the root [MARKETING.md](../MARKETING.md), registered as a
`marketing_playbook` doc in the same `targets.yml`; its repeated tables are checked by
`tests/marketing_crosswalk/test_playbook.py`.

Prerequisites are Python and the module's declared dependencies, plus the local target checkouts
configured in [targets.yml](../modules/marketing-crosswalk/crosswalk/targets.yml).
That file names `OPENTECHAPP_REPO_PATH`, `OTBLOG_REPO_PATH` and `HCP_REPO_PATH` overrides.
Validation reads the entire registry, so selecting one consumer does not bypass missing or
drifting evidence in another target.

Run from the marketing module directory:

```bash
cd modules/marketing-crosswalk
python3 -m generator.cli validate
python3 -m generator.cli selftest
python3 -m generator.cli coverage --module stream-extend
python3 -m generator.cli coverage --module content-extend
python3 -m generator.cli generate --module stream-extend --asset guide-page --dry-run
```

Require successful validation before generating deliverable drafts. The `coverage` command emits
a report to stdout; `selftest` renders in memory. Use explicit `--dry-run` for preview: the current
[CLI implementation](../modules/marketing-crosswalk/generator/cli.py) writes files when it is
omitted, despite older module prose describing dry-run as the default.

For a local draft after a successful preview:

```bash
python3 -m generator.cli generate --module stream-extend --asset guide-page
```

Output goes to the module's ignored `out/` directory. `--out` selects a different local directory;
`--apply` writes into the target checkout's configured draft directory. Existing filenames can be
overwritten, so preserve any hand-edited draft separately before rerunning. None of these commands
publishes content. Review status evidence, naming, claims, links and required screenshots/metrics
before moving a draft to its destination.

Blocked shipped claims and discovery-only consumers are expected boundaries. Fix stale evidence
at its source; do not use `--force` to produce evidence-backed deliverables. A successful template
render does not establish that the product capability or lesson has shipped.
