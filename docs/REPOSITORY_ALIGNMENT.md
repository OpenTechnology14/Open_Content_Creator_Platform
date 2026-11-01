# Repository Alignment and Export Policy

**Status:** Initial policy for the private canonical repository
**Date:** 2026-07-13

## Purpose

`OpenTechnology14/Open_Content_Creator_Platform` is the canonical combined integration repository. `ContentExtend` and `StreamExtend` are standalone product repositories. This policy prevents the same code and documentation from being edited independently in three places.

## Ownership

| Surface | Canonical owner | Standalone treatment |
|---|---|---|
| Shared setup engine and readiness schema | Open_Content_Creator_Platform | Versioned dependency or generated export |
| Shared relay client/protocol | Open_Content_Creator_Platform | Versioned dependency or generated export |
| Combined cloud relay, mobile bridges, plugins | Open_Content_Creator_Platform | Referenced; exported only by explicit manifest |
| Stream desktop application | Open_Content_Creator_Platform `apps/stream-extend` | Export to StreamExtend after its build/release gates pass |
| Content desktop application | Open_Content_Creator_Platform `apps/creator-extend` during migration | Export to ContentExtend as `apps/content-extend` after naming decision |
| Stream-only modules/guides | StreamExtend | Combined repository consumes a pinned version/export |
| Content-only modules/guides | ContentExtend | Combined repository consumes a pinned version/export |
| Cross-product integration scenarios | Open_Content_Creator_Platform | Results linked from standalone release evidence |
| Product-specific release notes | Corresponding standalone repository | Linked from combined release manifest |

## Naming decision

The product and GitHub repository are **ContentExtend**. The combined workspace currently uses `Creator Extend`, `creator-extend`, and `creatorextend.com` in code, configuration, documentation, and identifiers.

Until a migration proposal is approved:

- `apps/creator-extend` is a documented legacy/internal alias for ContentExtend;
- no mechanical directory/package/bundle-ID rename is performed;
- new product-facing documentation uses ContentExtend and calls out the alias where paths matter;
- export tooling maps the legacy source path to the ContentExtend destination explicitly.

A rename must inventory Cargo package/crate names, npm names, Tauri identifiers, relay product enums/issuers, desktop/mobile bundle IDs, URLs, config keys, persisted settings, update channels, documentation, and OpenTech templates. It requires compatibility and rollback rules.

## Export contract

Manual copying is prohibited after the initial alignment. Add a repository-controlled manifest such as:

```yaml
schema_version: 1
products:
  contentextend:
    repository: OpenTechnology14/ContentExtend
    mappings:
      - from: apps/creator-extend
        to: apps/content-extend
      - from: modules/content-creation
        to: modules/content-creation
      - from: modules/image-editing
        to: modules/image-editing
  streamextend:
    repository: OpenTechnology14/StreamExtend
    mappings:
      - from: apps/stream-extend
        to: apps/stream-extend
      - from: modules/creator-experience
        to: modules/creator-experience
      - from: modules/realtime-ai
        to: modules/realtime-ai
```

The final manifest must include every owned module, guide, shared dependency, exclusion, and generated file. Export automation must:

1. start from a tagged/identified canonical commit;
2. copy only allow-listed paths into a clean checkout;
3. reject secrets, local settings, outputs, media, weights, and files over policy limits;
4. run the standalone repository's link, lint, test, Compose, and build checks;
5. produce a machine-readable source commit/export manifest;
6. open a reviewable pull request rather than force-pushing;
7. refuse export when the destination contains unrepresented manual changes.

## Change rules

- Shared protocol/setup changes begin here and include compatibility tests for both products.
- Product-only module/guide fixes begin in the standalone repository and are consumed here through the documented synchronization method.
- Emergency fixes made in a standalone repository must be backported before the next combined release.
- Documentation must link to the authoritative repository rather than duplicate a mutable contract.
- No repository may claim a feature is Implemented or Production solely because another repository contains a proposal or scaffold.

## Initial alignment backlog

1. Decide whether to retain or migrate the `creator-extend` code identifier.
2. Create the full export manifest from the actual module ownership maps in the ContentExtend and StreamExtend `CLAUDE.md` files.
3. Reconcile the combined README's availability/pricing/setup claims with release evidence.
4. Align OpenTechApp templates from `creator-extend` to ContentExtend naming and the versioned readiness schema.
5. Add CI drift checks comparing exportable source hashes to the latest standalone export manifest.
6. Decide and publish the root license before making the repository public or accepting outside contributions.

## Release gate

A standalone release derived from this repository must record the canonical source commit, export manifest version, destination commit, deviations, test evidence, and rollback. A combined release must record the ContentExtend and StreamExtend versions it integrates.
