# Generated agent registries

> **Status:** Living · **Last reviewed:** 2026-10-08 · **Owner:** OpenTechnology14

**Enforcement: required.** Files in this directory are generated from canonical readable
sources. Edit the source and regenerate; do not hand-edit JSON snapshots.

```bash
python3 scripts/testing/generate_docs.py --write
python3 scripts/testing/generate_docs.py --check
```

`documentation.json` derives proposal IDs/states/model assignments, unfinished lane coverage,
module labels/statuses and documentation-update rules. Source hashes use normalized text;
It also generates the explicit module-owned proposal-reference block in PROJECT_CROSSWALK.md;
manual conceptual mappings remain readable source. Module README/setup edits must regenerate it.
there is no wall-clock timestamp that changes on each run. The same command generates
`AGENTS.md` from `CLAUDE.md`, changing only agent self-identification. Optional Claude
review-workflow restrictions remain identical in both instruction files.

The offline suite and CI reject stale snapshots or agent instructions. The snapshot establishes
consistency with the source, not whether a claim is true. Module promotion, live acceptance,
source-rule review and owner authorization retain their existing evidence requirements.
The readable matrix remains advisory for semantic document-review triggers. Its `## Path triggers` table is carried into
`documentation.json` as a `paths` list per rule, which `scripts/testing/doc_advisory.py` reads; a rule with an empty list is a
judgement the script cannot make.
