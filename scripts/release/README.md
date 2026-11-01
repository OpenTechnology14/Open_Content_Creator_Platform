# Public source snapshot

Export from a committed private revision into a **new** directory outside the checkout:

```bash
python3 scripts/release/public_snapshot.py --source . --ref HEAD \
  --policy /path/to/private-export-policy.json --destination /path/to/new-public-snapshot
```

The policy is private JSON with `private_repo`, `public_repo`, a nonempty `deny_patterns`
array of reviewed regular expressions for personal identifiers, and optional literal
`replacements`. Keep actual personal identifiers outside the public repository. The private
edition maintains its policy under `private/release/`. The command exports only committed Git
blobs, excluding `private/`, accepted local workflow-installation references and history-specific
secret-scan suppressions. It never copies `.git`, local state, ignored files, PRs, issues, Actions
logs or branches. It rejects credential-like filenames, symlinks, submodules and files over 5 MB.

Wrap private-only document sections in paired `<!-- private-only:start -->` and
`<!-- private-only:end -->` comments, each on its own line. Those sections are removed, and own-repository PR/issue/run
links become explicit unavailable private evidence. Remaining own-repository URLs point to
the public repository; historical blob refs still need a source-link review before publication.
Internal application IDs/data directories are not product display names; retain them unless
an actual migration is implemented and accepted.

The JSON output contains exported paths/hashes and counts, never source text or the private
deny list. It is an inventory, **not a claim that source is free of every possible secret**.
The exporter adds a public-edition notice and ignores `/private/` in the exported `.gitignore`.
Before publishing:

1. Inspect the exported tree, public README, imagery, licenses, manifests and external links.
2. Regenerate derived documentation in the exported tree; run applicable checks there.
3. Run `gitleaks dir --redact --no-banner --report-format json` with its report outside the
   candidate. Review every finding privately; do not copy history-specific suppressions.
4. Inspect exported personal names, emails, home paths, hostnames and binary metadata. Verify
   the private matrix and deployment/install records are absent. Recheck after any edit.
5. Initialize fresh Git history with a project noreply identity. Never mirror/fork the private
   repository or add its Git objects to the public candidate. Scan that fresh history too.
6. Publish only the reviewed commit to the intended new repository. Check visibility, author
   metadata and that no old PRs/issues/runs were copied. Keep the original repository private.

Source publication is distinct from a production release. Existing optional dependency
licenses and native/provider/security acceptance limits still apply. Tests for exporter
boundaries are in `tests/release/test_public_snapshot.py`; full validation uses `make test`.
