---
name: security
description: "Security rules for the Open Content Creator Platform - secrets and .env handling, what must never be committed or logged, network exposure and API-key authentication, and the sensitive paths (Tauri sources and capability files, the character-avatar module, credential configs, the shared Rust crates, the streaming and gameplay pipeline) where a wrong change compiles and passes tests. Use before editing or reviewing any of them, or anything that touches a token, a key, a port or an auth check."
when_to_use: "Examples: 'is this safe to commit?', 'add an API route', 'change a Tauri capability or entitlement', 'where does this token go?', 'expose this port', 'review this change for security'. Not for a repo-wide audit: that is the /audit command. This skill is not bound to file paths, so open it yourself before touching a sensitive path."
---

# Security

If this skill and a cited document disagree, **the document wins** - fix the skill. It summarises `CLAUDE.md` sections 7, 9, 10
and 13, `SECURITY.md` and `docs/API_ROUTE_AUDIT_LEDGER.md`; it replaces none of them. It holds no secret value and no live
endpoint, and must never gain one: if you find one here, remove it.

## It will not open itself

Claude Code can load a skill when a file matching a `paths:` pattern is opened. This skill deliberately has none: whether
sensitive paths should load it automatically is the owner's open decision
([`HYB-REDESIGN-D05`](../../../docs/proposals/PROPOSAL_REDESIGN_FROM_OPENTECHAPP_PATTERN.md)). Until it is answered nothing opens
this for you. If your change touches a row of the next table, read this first.

## Sensitive paths (`CLAUDE.md` section 13)

| Path | Why a mistake here is expensive |
|---|---|
| `apps/*/src-tauri/**` | Native code plus entitlements and capability files. A wrong capability is a security defect that compiles and passes tests |
| `modules/character-avatar/**` | The avatar pipeline: security-sensitive rendering and the VTS token path |
| `configs/local/**` when credentials are involved | Credential handling. Purely structural config is fine |
| The shared crates (`recording-library`, `local-settings`, `social-manager` under `apps/shared/`) and anything spanning both apps | The one place a local change has non-local consequences |
| Streaming and gameplay pipeline changes | The stale, duplicate, off-air and mismatched-finish guards in `modules/character-avatar/stream_avatar/runtime.py` fail silently: a rewrite that drops one leaves no failing test |

These paths are worked with the assigned Sol or Astra model, never drafted through the optional HF/OpenCode route (`CLAUDE.md`
section 13), and they keep their full verification bar with either model (section 9). A wrong capability compiles and passes
tests, so the diff is the evidence: describe every capability, entitlement or origin change, and why, under the pull request's
privacy and security impact (`CONTRIBUTING.md`; `CLAUDE.md` section 16).

## Secrets and environment (`CLAUDE.md` section 7; `SECURITY.md`)

- Never commit `.env`; commit `.env.example` with placeholder values, and update it in the same commit as any new variable.
- Modules read configuration from environment variables. Cloud secrets live in the DigitalOcean console or a sealed-secrets
  equivalent. Tailscale auth keys are ephemeral and regenerated per node.
- Tokens, stream keys, credentials, recordings, prompts, private assets and model inputs are never committed or logged - not in
  an error message, a test's output or pull-request text. Evidence records a fingerprint or a redacted report, never the value
  (`docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`, "Release evidence").
- You never type a password, key or token into a form. The owner performs the sign-in; credentials stay in environment variables
  and the OS credential manager, never in a row or a document (`docs/todo/README.md`, "Row format").
- Do not commit model weights, recordings or any binary over 5 MB (`CLAUDE.md` section 10).
- A secret that reached a commit: revoke or rotate it first, then remove it from current and historical content, audit access
  logs, and record the incident without reproducing the value. Deleting the file in a later commit is not enough (`SECURITY.md`).

## Exposure and authentication (`CLAUDE.md` section 10; `SECURITY.md`; `docs/API_ROUTE_AUDIT_LEDGER.md`)

- Do not expose a service to the public internet without an auth layer. Remote access goes through Tailscale or an
  authentication proxy; internal databases and caches are never public.
- Realtime webcam, OBS and creator media stay on the local path. The cloud relay and the OpenTech integration are optional, use
  explicit authentication and sanitized payloads, and carry nothing realtime.
- Published ports bind to `127.0.0.1`; the relay API's own port is public by design. Use compose service names or environment
  variables in module code, not a hard-coded `localhost`.
- Local API trust boundary: every mutating route requires `X-API-Key`, compared with `hmac.compare_digest` (never `!=`, which leaks
  match length through timing); read routes are public by design; `/ws` takes the same key and closes an unauthorized connection
  with code 1008 before accepting it. The route mount table is `tests/backend_api/test_routes.py`; a changed route gets a
  ledger review (`docs/CONTINUOUS_IMPROVEMENT.md`, every pull request).
- In production the relay fails closed at startup: it refuses a placeholder or empty JWT secret and a default or `localhost`
  database URL (`SECURITY.md`). A change that lets it start with one is a change to a security boundary.

## Before you finish

1. Run the row of `docs/agent/VERIFICATION-MATRIX.md` that proves the change and write its result in the pull request.
   "Not run" is acceptable; silence is not.
2. State the privacy and security impact and the rollback in the pull request (`CLAUDE.md` section 16).
3. `scripts/testing/public_release_guard.py` holds the hygiene checks: no absolute home-directory path in a tracked file, no
   tracked environment, key or certificate file, no private registry row. It does not scan for secrets; the release checklist
   records `gitleaks` for that.
4. Known open items - the missing Content Security Policy, upload and path limits, unfinished route authorization decisions -
   are recorded in `SECURITY.md` and `docs/GAP_AUDIT.md`. Read them before assuming a surface is hardened.
