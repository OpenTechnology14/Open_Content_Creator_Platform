# Extend Preview

Private P-072 shell preview, authorized by the owner on 2026-10-12. The existing Stream Extend
and Creator Extend apps remain the workflow surfaces while parity/migration reach acceptance.

The preview combines Home, Stream, Create, Library and Settings; labelled task folders and
compact navigation; persisted Stream/Create/both choices; the shared profile switcher, setup
plugin, recording inbox and read-only OBS/ComfyUI readiness. Native commands enforce disabled
packs. OBS credential failure does not block Create checks. Original settings/vault identities
are not imported. Source adapters are reused instead of replacing their command implementations.

Broadcast control, recording, editing/export, rendering, OAuth, remote control, publishing,
cloud sync and credential/device migration stay in their existing apps/proposals. The preview
cannot start/stop broadcasts or mark a recording edited/published. Permissions grant only the
local window, shared setup/profile selection and a video picker. CSP is configured separately;
its native enforcement and OS-vault acceptance remain manual checks.

## Build and check locally

```bash
cd apps/extend
npm ci
npm run check
npm test
npm run build
cargo test --locked --manifest-path src-tauri/Cargo.toml
npm run tauri build -- --debug --bundles app,dmg -- --locked
```

Mac outputs are `src-tauri/target/debug/bundle/macos/Extend Preview.app` and
`src-tauri/target/debug/bundle/dmg/Extend Preview_0.1.0_aarch64.dmg`. These are private unsigned
development artifacts. Opening setup does not require OBS, Python, Docker, models or a cloud
account; selected installs and live checks have their own prerequisites. No DigitalOcean
runtime is required or deployed.

Preferences/readiness use the isolated OS-local-data `HybridCreatorPlatform/extend-preview`
namespace; OBS secrets use the preview OS-vault identity. Setup environments, profiles and the
recording ledger reuse existing shared contracts. Video stays in its original folder. Uninstall
must preserve shared stores/environments/media; public upgrade/uninstall acceptance is open.

## Testing handoff

Run U-01/U-02/U-07 from [P-072](../../docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md):
open with prerequisites absent, select each pack, restart, toggle layout, navigate by keyboard
at 320/736/1100px, inspect unrelated-warning isolation, import/reveal an owned synthetic recording,
verify separate profiles and denied crafted invokes/remote content. Keep legacy settings/vault
entries unchanged. Mac acceptance does not establish Windows acceptance. Full parity, migration,
real cross-workspace outputs, two-device approval, budgets and legacy replacement stay gated.
