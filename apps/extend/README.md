# Extend Preview

Private P-072 combined desktop development app. Owner v6 (2026-11-01) authorizes desktop parity development beyond the 2026-10-12 preview. The existing Stream Extend
and Creator Extend apps remain the workflow surfaces while parity/migration reach acceptance.

The preview uses expandable Workspace, Production and Studio feature groups, pinned profile/setup/help
utilities and section shortcuts that expand and focus advanced settings. Existing native page IDs and
pack admission remain unchanged. Features marked Later are disabled, and Media Library still requires
the Content pack. Sidebar expansion is remembered in browser-local presentation storage; it contains
only group IDs and booleans. The preview combines setup, profiles, readiness and the library; labelled task folders and
compact navigation; persisted Stream/Create/both choices; the shared profile switcher, setup
plugin, recording inbox and read-only OBS/ComfyUI readiness. Native commands enforce disabled
packs. OBS credential failure does not block Create checks. Original settings/vault identities
are not imported. Source adapters are reused instead of replacing their command implementations.

Existing-scene switching, per-input mute and real OBS status are operational. **Managed
recording Start and destructive Stop are blocked in native code.** Standard OBS `StopRecord`
targets the current output without an atomic expected-generation condition. Continuous lifecycle
observations cannot prevent an external replacement after admission. The tested witness candidate
is retained for engineering evidence, not exposed as a managed recording feature.

The native root controller preserves pinned connection/profile/generation semantics for recovery
and finalized handoff retry. Status and automatic safety audio use the native pin without reading
broken preferences or the vault, including webview reload. Scene/audio inspection uses independent
sockets and short snapshots; stale completions are rejected. Scene and mute actions carry their actual observation context and session; stale/missing context is rejected before settings/vault/network access. Relevant endpoint/credential/pack saves clear idle controls immediately, including failed/ambiguous responses, until fresh observations arrive. Presentation changes and safe pinned settings preserve safety controls. A finalized missing-file handoff can
be explicitly left for validated manual import, only while outputs are inactive; no file is registered,
deleted or changed. New managed starts need an OBS-side atomic ownership contract before admission.
Legacy live-session code is unchanged and is not evidence of combined managed-recording safety.

Go Live, editing/export, rendering, OAuth, remote control, publishing, cloud sync and credential/device
migration remain later slices/gates. The app cannot mark a recording edited/published. Explicit app
command permissions grant the local main window only, alongside shared setup/profile selection and
a video picker. Operational commands also verify the local main origin. CSP is configured separately;
its native enforcement and OS-vault acceptance remain manual checks.

## Observe OBS and import recordings

1. Configure OBS WebSocket, scene/audio and recording folder in OBS. Save the isolated app
   connection under Setup & Settings; credentials use the preview OS-vault identity.
2. Enable Stream to observe real status. Safety audio loads automatically on every page. Inspect
   scenes to switch an existing scene, or mute a specific input. These operations affect OBS directly.
3. Start and finish recording **in OBS**. Managed Start/Stop are unavailable in this build; the app
   does not adopt that output. Enable Content and use Media Library's validated manual import.
4. For an existing pinned/unknown session, finish output in OBS, refresh and recover only when
   inactive. A finalized inbox failure offers retry or **Leave handoff for manual import**. The latter
   releases only memory and shows original profile IDs; no successful registration is implied.
5. Connection/password changes and disabling Stream remain blocked while a native pin needs recovery.

P072-R1-01 remains unresolved. The [proposal's atomic-generation design](../../docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md#obs-side-completion-contract-required) names the required proof.
No actual OBS output, encoder quality, vault or Windows acceptance is claimed by offline tests.

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

The recording-first native Mac unavailable-service/navigation/profile smoke passes; no actual OBS
recording is claimed. After the atomic contract is implemented/reviewed, add U-04 playable local recording/handoff and safety checks to the existing
U-01/U-02/U-07 runs from [P-072](../../docs/proposals/PROPOSAL_UNIFIED_DESKTOP_AND_CLOUD_SCOPE.md):
open with prerequisites absent, select each pack, restart, toggle layout, navigate by keyboard
at 320/736/1100px, inspect unrelated-warning isolation, import/reveal an owned synthetic recording,
verify separate profiles and denied crafted invokes/remote content. Keep legacy settings/vault
entries unchanged. Mac acceptance does not establish Windows acceptance. Full parity, migration,
real cross-workspace outputs, two-device approval, budgets and legacy replacement stay gated.

## Sidebar verification fixture

For frontend-only keyboard, pack-isolation and narrow-width checks with synthetic data:

```bash
npm run dev -- --config tests/browser.config.ts --host 127.0.0.1 --port 4179 --strictPort
```

The explicit test config injects the official Tauri IPC mock and a visible fixture banner.
It performs no native operations and is not included by the production build configuration.
A fixture pass does not establish OS-vault, OBS, recording, installation or native acceptance.
