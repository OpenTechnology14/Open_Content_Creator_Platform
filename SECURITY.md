# Security Policy

## Support status

The project is **pre-release**. No version should be treated as a hardened public service until the P0 security gates in
[`docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`](docs/OPEN_SOURCE_RELEASE_CHECKLIST.md) are closed. The default design is local-first:
realtime media stays on the creator's workstation.

## Reporting a vulnerability

Do not open a public issue that contains exploit details, credentials, private media or personal data. Report privately using
[GitHub private vulnerability reporting](https://github.com/OpenTechnology14/Open_Content_Creator_Platform/security/advisories/new). Include the affected
commit or version, the impact, steps to reproduce with synthetic data, and a suggested mitigation if you have one.

The maintainer will acknowledge a report within 5 business days, give a triage update within 10 business days, and coordinate
disclosure after a fix or mitigation is available. These are best-effort targets while the project is pre-release.

## Security boundaries

- OBS, camera capture, realtime inference and creator media are local paths.
- The cloud relay and the OpenTechnology integration are optional. They must use explicit authentication and sanitized
  payloads, and nothing realtime passes through them.
- `.env`, tokens, stream keys, credentials, recordings, prompts, private assets and model inputs must not be committed or logged.
- Tailscale or an authentication proxy is required for remote access to services; internal databases and caches must not be
  public. Every published port in the root Compose file, and the relay's database and cache ports, is bound to
  `127.0.0.1`; the relay API's own port is public by design.
- In production the relay fails closed at startup: it refuses a placeholder or empty JWT secret and a default or
  `localhost` database URL.

## Known pre-release limitations

The audit in [`docs/AUDIT.md`](docs/AUDIT.md) and the open items in [`docs/GAP_AUDIT.md`](docs/GAP_AUDIT.md) are the record.
As of 2026-10-23:

- The relay's weak fallback credentials and public internal ports found in the first audit are fixed (production startup
  fails closed; the Compose ports are loopback-bound).
- **Open:** a full review of allowed origins and capabilities. Both desktop apps still set no Content Security Policy
  (`Extend Preview` sets one), and route and command authorization decisions are recorded in
  [`docs/API_ROUTE_AUDIT_LEDGER.md`](docs/API_ROUTE_AUDIT_LEDGER.md) but not yet complete.
- **Open:** validation and limits for uploads, dynamic paths, script launches and sync keys.
- **Secret scanning:** a scan of the working tree and every commit found no live credential. Four findings are test fixtures
  awaiting the maintainer's sign-off.

Do not deploy the cloud configuration publicly until the open items are closed.

## Secrets accidentally committed

Revoke or rotate the secret first, then remove it from current and historical content, audit access logs, and document the
incident without reproducing the value. Deleting a file in a later commit is not enough.
