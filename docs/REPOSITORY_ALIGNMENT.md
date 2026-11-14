# Repository Alignment and Export Policy

> **Status:** Living · **Last reviewed:** 2026-11-12 · **Owner:** OpenTechnology14

The July 2026 version of this policy assumed two standalone product repositories that would own product-only modules and receive exports. They never took a change, and on 2026-11-10 the owner archived them. This version records the arrangement that actually exists.

## Purpose

There are two repositories for the Content Creator Platform:

- the **private development repository**, `OpenTechnology14/Open_Content_Creator_Platform`, where all development, review, CI and account operations happen; and
- the **public source edition**, `OpenTechnology14/Open_Content_Creator_Platform`, a reviewed snapshot published from the private one.

Two earlier repositories, `ContentExtend` and `StreamExtend`, were created in June 2026 as standalone scaffolds. Each has two commits, the last on 2026-07-14, and no fix was ever made in either. They are **archived** (read-only, private) and are not a place to change code or documents. This policy keeps the same code and documentation from being edited independently in more than one place.

## Ownership

| Surface | Canonical owner | Treatment elsewhere |
|---|---|---|
| Both desktop apps, the combined Extend preview, shared crates, setup engine and readiness schema | The private development repository | Part of the public edition only through the exporter |
| Modules, guides, cloud relay, mobile bridges, plugins | The private development repository | Same |
| Proposals, decision lanes, verification matrix | The private development repository | Exported; private-only sections are removed |
| Public README, `LICENSE` and community files | The private development repository | Edited here, then re-exported; never edited in the public edition |
| The private account matrix and operating records | The private development repository, under `private/` | Never exported |
| `ContentExtend`, `StreamExtend` | None (archived) | Read-only history; reviving one needs an approved proposal |

## Naming decision

The June version of this document said the product and its GitHub repository were to be named **ContentExtend**. That repository was archived without becoming the product's home, and the combined workspace still says `Creator Extend`, `creator-extend` and `creatorextend.com` in code, configuration, documentation and identifiers. **Which name published copy may use is still an open owner decision** (`CT-D12` and `PL-D07`; `P-023` is Deferred).

Until a migration proposal is approved:

- `apps/creator-extend` stays as it is, and ContentExtend is the candidate public name;
- no mechanical directory, package or bundle-ID rename is performed;
- external copy is treated as draft and is not published under either name.

A rename must inventory Cargo package/crate names, npm names, Tauri identifiers, relay product enums/issuers, desktop/mobile bundle IDs, URLs, config keys, persisted settings (the OS data directory and credential service names), the Compose project, update channels, documentation, and OpenTech templates. It requires compatibility and rollback rules.

## Names that stay

The project is called the Content Creator Platform in everything a person reads. The name it was developed under before is retired as a display name, and `tests/docs/test_terminology.py` fails if it comes back. Some identifiers keep the original spelling **on purpose**, because the apps store data and credentials under them and renaming one orphans what users already have. A wording pass must not change them.

| Identifier | Where it lives | Why it stays |
|---|---|---|
| `HybridCreatorPlatform` | The OS application-data directory and the OS credential-manager service names used by `apps/` and `modules/social-management` | Settings, recordings, setup state and social tokens are stored under it |
| `hybrid-creator-platform` as the Compose project, and the `hybrid-creator-platform_hcp-net` network | `docker-compose.yml`; the setup wizard's project-label filter | A new project name creates new volumes and networks, which orphans Postgres and MinIO data |
| `~/.hybrid-creator-platform/social` | `modules/social-management` | Local profile, editorial and connection state |
| `hybrid-creator-platform` as the crosswalk target key | `crosswalk/targets.yml`, `modules.yml`, the subjects, design-system `repo:` keys, show profiles | Other repositories read the key |
| `HCP_*` variables, `HCP-nnn` and `GAP-HCP-nn` IDs, `hcp-*` container and bundle names, `HCP-Bridge`, `HCP Default` | The environment contract, the gap ledger, Compose, VTube Studio, the OBS scene collection | They are persisted in user data or in other tools' settings; a new VTube Studio plugin name needs a new authorization |
| `hybrid-platform` as the platform brand ID, and `assets/brands/hybrid-platform.svg` | `modules/social-management/catalog.yaml`, the design tokens, saved profiles | Profiles and tests refer to the ID |
| `com.hybridcreator.extend.preview` | `apps/extend/src-tauri/tauri.conf.json` | A bundle identifier; changing it makes a different app to the operating system |
| Dated historical records | Entries dated before 2026-11-10 in `docs/proposals/PROPOSAL_DOCUMENT_GAPS.md` | They record what was true and said when they were written; owner decision 2026-11-12. Living documents are renamed, and an entry dated on or after the rename is checked like any other text |
| The word hybrid in its technical sense | `Hybrid TTS` (`CT-D04`), the `Hybrid Networking` subject, `Full Hybrid Stack Architecture` | They describe a local-plus-cloud arrangement, not the name |

Renaming any identifier above is an owner decision (`PL-D17`) and needs the compatibility and rollback rules the Naming decision lists.

## Export contract

The only export is the public source snapshot, made by [`scripts/release/public_snapshot.py`](../scripts/release/public_snapshot.py) and described in [`scripts/release/README.md`](../scripts/release/README.md). It exports committed blobs only, excludes `private/`, removes `private-only` sections, rewrites own-repository links, rejects credential-like files, symlinks and files over 5 MB, and is followed by a reviewed publication with fresh history. It is never a mirror or a fork.

- Manual copying of private content into the public edition is prohibited.
- A problem found in the public edition is fixed in the private repository and re-exported.
- Any other export needs an approved proposal, a repository-controlled manifest, and the same boundaries.

## Change rules

- All changes begin in the private development repository.
- Documentation links to the authoritative file rather than duplicating a mutable contract.
- No repository may claim a feature is Implemented or Production solely because another repository, or the public edition, contains a proposal or scaffold.

## Alignment backlog (state on 2026-11-10)

1. Decide whether to retain or migrate the `creator-extend` code identifier. **Open**, with the naming decision above.
2. Build an export manifest for the standalone repositories. **Obsolete**: they are archived.
3. Reconcile the README's availability, pricing and setup claims with release evidence. **Ongoing**; the README was rewritten for the public edition under `P-075`.
4. Align OpenTechApp templates from `creator-extend` to the final product name. **Open**, follows the naming decision.
5. Add CI drift checks against a standalone export manifest. **Obsolete**; the public snapshot is covered by `tests/release/test_public_snapshot.py` and the public-release guard.
6. Publish a root license before making the source public. **Done**: an MIT `LICENSE` is in the tree (`P-075`) and the public edition carries it; the owner's confirmation of the license gate is tracked with the open-source gates.

## Release gate

A public source release records the private commit it was exported from, the exporter's inventory output, who reviewed the exported tree, the checks run in it, and how to roll back (re-publish or delete the public repository; the private one is unchanged). Source publication is distinct from a production release: native, provider and security acceptance limits still apply.
