# Open-Source Release Checklist

> **Status:** Living · **Last reviewed:** 2026-10-23 · **Owner:** OpenTechnology14

## Current verdict

**Owner direction, 2026-10-05:** open-source distribution is intended. GitHub currently reports
this repository private with no detected license, and the checkout has no root `LICENSE`.
The former BSL/paid-source description is no longer the intended release policy. Select the
actual license and copyright holder, review dependencies and release scope, and reconcile
manifests/marketing before changing visibility. JobHunter's public MIT release is a reference,
not evidence that these gates have passed here. [Review and delivery plan](PUBLIC_DOCS_AND_MARKETING_REVIEW.md).

**NO-GO for an open-source production release.** A clearly labeled architecture preview may be published after secret and legal review. A public alpha requires all P0 boxes.

**Engineering refresh, 2026-10-12 (P-001):** the historical notes below are updated where
committed implementation/evidence resolves their specific finding. Private
[release evidence collection](../scripts/testing/README.md#private-release-evidence-p-001-wp-7)
now exists and was exercised against a fresh clone at `718240e`; generated docs, Ruff and the
offline suite passed. It deliberately retains `release_ready=false`. Native/Docker checks,
supported-target approval, legal/security reviews, SBOM/signing, live acceptance and rollback
remain separate. The root license is still absent. This is engineering reconciliation, not
public-release approval.

**Release preparation, 2026-10-23 ([P-075](proposals/PROPOSAL_OPEN_SOURCE_RELEASE_PLAN.md)):** every step that needs no
decision was done in one change — the private registry rows removed, a root MIT `LICENSE` added and the nine `BSL-1.1`
manifests corrected, the third-party dependencies walked and ledgered
([`THIRD_PARTY_PROVENANCE.md`](THIRD_PARTY_PROVENANCE.md)), the tree and every commit scanned for secrets, and the README,
`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` and `SECURITY.md` rewritten for a public reader. Sixteen decisions (`OSS-D01` to
`D16`, `PL-D16`) remain the owner's. **The verdict is unchanged: NO-GO for a production release, and no visibility change
has been made.** An architecture preview becomes publishable once the gates that decide safety are answered: the license
and holder line, the history policy, the copyleft dependencies and the contact channels.

**Verdict itself unchanged as of 2026-09-02** — 4 boxes below newly check off on real evidence
(`P-046`), but every remaining unchecked P0 legal item (root `LICENSE`, third-party notice review,
branding review) is exactly as open as before, and any one of them alone keeps this a NO-GO.

## P0 legal and governance

- [ ] Root `LICENSE` exists and matches every README/package manifest. *(2026-10-23, `P-075`: MIT `LICENSE` added; nine
  `BSL-1.1` Cargo manifests corrected, the tenth and six `package.json` files set, and
  `scripts/testing/public_release_guard.py` now fails on a mismatch. **Unticked: a legal box needs the owner's sign-off
  (`OSS-D01` license, `OSS-D02` holder line and marks), not an agent's.**)*
- [ ] The term “open source” is legally accurate; BSL projects are described as source-available before conversion.
  *(2026-10-23, `P-075`: the README states MIT, the plugins' own license and that optional integrations carry other terms.
  Unticked pending `OSS-D01` and the copyleft decisions `OSS-D07` to `D09`.)*
- [x] `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` exist. *(2026-09-02, `P-046`: all
  three present at root with real content — 95 lines combined, not stubs; `SECURITY.md` names a
  reporting path and response-time targets)* *(2026-10-23, `P-075`: all three rewritten for a public reader, the conduct file
  is the Contributor Covenant 2.1; the contact for each is an `OWNER-SET` placeholder until `OSS-D04`.)*
- [ ] Third-party notices and dependency licenses are reviewed. *(2026-10-23, `P-075`: every Python, Rust and Node
  dependency, the services, plugin hosts, models and tools were walked and ledgered in
  [`THIRD_PARTY_PROVENANCE.md`](THIRD_PARTY_PROVENANCE.md); [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) carries the
  notices that apply today. **Unticked: the flags await the owner (`OSS-D07` to `D10`)**, and the full per-package notice
  text is a release artifact, `OSS-D15`.)*
- [ ] Branding and screenshots contain no personal/customer data. *(2026-10-23, `P-075`: no screenshot is tracked, the
  README's hero image is a commented placeholder, the desktop icons are generated placeholders and the logo and four brand
  marks are first-party. Absolute local paths naming a personal account were removed from four documents. Unticked pending
  `OSS-D02`: whether the product names and marks are yours to license.)*

## P0 engineering

- [ ] Clean clone installs and builds on every claimed supported OS. *(2026-10-23, `P-075`: not doable without a host per
  OS; tracked by P-001 and the supported-OS decision `PL-D02`. The license walk found one install defect, a Windows-only
  requirement naming a package that does not exist on PyPI, fixed with a test.)*
- [x] CI enforces lint, test, and build failures. *(2026-10-12 reconciliation: P-049 made
  Ruff blocking; `.github/workflows/ci.yml` runs unconditional pytest and both apps' frontend
  check/build and locked Rust check/test commands. Private installer builds have their own
  workflow. Fresh clone generated-doc/Ruff/offline checks passed; this checkbox describes
  enforcement, not native installation or release acceptance.)*
- [x] At least one complete local-first creator journey passes automatically or by a scripted
  acceptance harness. *(2026-09-02, `P-046`, citing `P-016`: `tests/acceptance/` — a real 9-step
  creator journey against live Postgres/Redis/MinIO/FastAPI, run in CI via `make test-acceptance`;
  first green run 33452956159 (private development evidence; not distributed))*
- [ ] All release-scope TODO/placeholder paths are implemented or feature-flagged as unavailable. *(2026-10-23, `P-075`: open; P-001 and P-003.)*
  *(2026-10-12 reconciliation: P-054/P-055 replaced the ComfyUI/OBS command stubs; P-003 owns
  shared readiness. Full release-scope inventory and live acceptance still apply. Recording
  inbox Start editing/Mark published change metadata only; provider/push and other unfinished
  paths must not acquire completion claims through those labels.)*
- [x] `.env.example` covers every required variable without real values. *(2026-09-02, `P-046`,
  citing `P-016`+`P-035`: every `${VAR}` in both `docker-compose.yml` and
  `docker-compose.digitalocean.yml` diffed against `.env.example` directly, all present)*
- [x] Production configuration refuses weak/default secrets. *(2026-09-02, `P-050`, `P-001` WP-2:
  the cloud relay now fails closed at startup — in production — on a placeholder/empty
  `RELAY_JWT_SECRET` or a default/`localhost` `RELAY_DATABASE_URL`, verified live against the real
  app both ways, not just unit-tested)*
- [x] Database, Redis, and internal metrics ports are not publicly exposed by default. *(2026-09-02,
  `P-046`: every `ports:` entry in `docker-compose.yml` is `127.0.0.1`-bound. **Extended 2026-09-02,
  `P-050`:** `cloud/docker-compose.relay.yml`'s Postgres/Redis ports were still publicly exposed
  until this pass — the earlier check only covered the root compose file, not this one — now fixed
  and bound `127.0.0.1` too; `relay-api`'s own port stays public by design, it's the actual API
  surface)*
- [ ] CORS and WebSocket origins follow the documented trust boundary. *(2026-10-23, `P-075`: still open; `OSS-D12` asks the owner to set a CSP in both legacy apps before a public alpha.)* *(2026-10-12
  reconciliation: P-050 added relay CORS origin allowlisting, and P-053 records authenticated
  WebSocket/tenant decisions in `API_ROUTE_AUDIT_LEDGER.md`. Full release-origin/capability
  review remains open; both desktop CSP values are still null.)*

## P0 security and privacy

- [ ] Working tree and full Git history pass secret scanning. *(2026-10-23, `P-075`: `gitleaks` 8.30.1 over all refs and the
  tree, plus a keyword scan of 177,047 added history lines: **no live credential**; four findings, all test fixtures, recorded
  by fingerprint in `.gitleaksignore` and still reported raw above. Unticked until the owner signs them off, `OSS-D05`;
  history policy is `OSS-D06`.)*
- [ ] Route/command authorization decisions are complete. *(2026-10-23, `P-075`: open; P-001 and P-053.)*
- [ ] Uploads, dynamic paths, script launches, and sync keys have validation and limits. *(2026-10-23, `P-075`: open; P-001.)*
- [ ] Data-flow document identifies what stays local and what can enter cloud services. *(2026-10-23, `P-075`: not started; `AUDIT.md` recommends it, and it is one small documentation change.)*
- [ ] Vulnerability reporting contact and response policy are published. *(2026-10-23, `P-075`: the policy is rewritten; the channel is `OSS-D04`, so it carries an `OWNER-SET` placeholder.)*
- [x] No `visibility: private` row remains in the published tree. *(2026-10-23, `P-075`: both private rows, their two subject
  files and the private target are removed. Confirm with `rg -n 'visibility: private' modules/marketing-crosswalk/crosswalk/modules.yml
  modules/marketing-crosswalk/crosswalk/targets.yml`, which finds nothing; `scripts/testing/public_release_guard.py` and
  `test_no_private_row_ships` now hold it. The subject files still carry a subject-level `visibility: private`, a different
  key that only marks a private upstream link. The rows remain in the history of the commit that added them: `OSS-D06`.)*

## Release evidence

The critical source snapshot has a generated SPDX inventory and redacted Gitleaks reports:
three history findings/one current-source finding, reviewed as invalid JWT/PEM test fixtures and
a fixed mock OBS challenge response. Raw findings remain retained, not marked as a zero-findings
scanner pass. Package inventory is not dependency-license approval or an artifact/container SBOM.
Local reports are under `output/release-evidence/p001-critical-2026-10-12/`; no public release
or existing database/deployment change occurred.

The private collector accounts for each recognized CI command and records every skipped
release gate; it is a repeatable evidence aid, not the sign-off record. Its Python-only clone
run proves that existing commit's local checks with prepared tooling. The collector change is
verified separately in the working checkout; no installer is claimed to have been built from it.

- [ ] Version/tag, changelog, compatibility matrix, SBOM, checksums, and rollback instructions exist. *(2026-10-23, `P-075`: `OSS-D15`.)*
- [ ] Container/Tauri artifacts are reproducibly associated with the tag. *(2026-10-23, `P-075`: `OSS-D15`.)*
- [ ] Backup/restore and dependency-outage scenarios pass. *(2026-10-23, `P-075`: open; P-001 live acceptance.)*
- [ ] Known limitations use plain language in the release notes. *(2026-10-23, `P-075`: the README's status note and `SECURITY.md` state them today; release notes are `OSS-D15`.)*

## Sign-off record

Record owner, date, evidence link, and exception for every checked item. Exceptions need expiry dates; P0 security/legal exceptions cannot be waived by documentation alone.

| Item | Verified by | Date | Evidence | Exception |
|---|---|---|---|---|
| Governance docs exist | Agent (`P-046`) | 2026-09-02 | `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` at root | None — engineering fact only, not legal review of their content |
| Acceptance harness proves a creator journey | Agent (`P-046`, citing `P-016`) | 2026-09-02 | CI run 33452956159 (private development evidence; not distributed) | None |
| `.env.example` complete | Agent (`P-046`, citing `P-016`+`P-035`) | 2026-09-02 | Direct `${VAR}` diff against both compose files | None |
| Internal ports not exposed | Agent (`P-046`; extended `P-050`) | 2026-09-02 | Direct read of every `ports:` entry in both `docker-compose.yml` and `cloud/docker-compose.relay.yml` | None |
| Production config refuses weak secrets | Agent (`P-050`) | 2026-09-02 | `tests/cloud_relay/test_startup_security.py` (mutation-verified) + live import of the real app both ways (weak secret raises, real secret succeeds) | None |
| No private row in the published tree | Agent (`P-075`) | 2026-10-23 | `public_release_guard.py` hygiene check; `test_no_private_row_ships`; the `rg` above finds nothing in the registry data files | History still holds the rows (`OSS-D06`) |
| Secret scan evidence | Agent (`P-075`) | 2026-10-23 | `gitleaks` 8.30.1, all refs and tree: four fixture findings; keyword scan of 177,047 added lines; no live credential | Four findings await owner sign-off (`OSS-D05`) |
| Root license prepared, manifests reconciled | Agent (`P-075`) | 2026-10-23 | `LICENSE` (MIT); ten `Cargo.toml` and six `package.json`; guard | **Not a legal sign-off**; `OSS-D01`, `D02` open |
| Dependency licenses walked | Agent (`P-075`) | 2026-10-23 | [`THIRD_PARTY_PROVENANCE.md`](THIRD_PARTY_PROVENANCE.md) | Flags await owner review (`OSS-D07` to `D10`) |
| Blocking lint/test/desktop-build CI enforcement | Agent (`P-001` reconciliation) | 2026-10-12 | P-049/P-052/P-054 and current `.github/workflows/ci.yml`; fresh clone `718240e` generated-doc/Ruff/offline checks passed | Native, Docker and public-release checks not run by the Python-only collector |

These are engineering-verified facts, not the legal/security sign-off this section otherwise
means — no P0 legal box may be checked on an agent's say-so, per this file's own rule.
