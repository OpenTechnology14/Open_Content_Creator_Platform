# Shared setup UI

`ModuleSetup.svelte` is imported by both desktop apps. It takes the app's Tauri invoke function
and a readiness-update callback; it has no separate npm runtime or network service. The component
uses Svelte 5 runes and is checked/built as part of each consuming application.

It saves module choices, expands dependencies for display, starts the catalog-limited installer,
polls durable progress and shows current dependency evidence. It also runs the fixed local capture
scanner, displays video/audio devices and platform driver evidence, and persists only a choice
returned by the latest scan. It does not open the device or mark capture ready without the separate
OBS recording acceptance step. It renders the versioned shared readiness snapshot and the optional
OpenTechnology synchronization form. API keys never enter the component again after save; only an
`api_key_set` boolean returns. Manual guides are bundled text and rendered as text, not injected
HTML. Selections or successful installation never mark whole modules ready. Parent app dashboards
remain accessible, while controls backed by a declared capability stay locked until current native
evidence passes.

App-specific **Connections** forms remain in each product route because Stream Extend configures
OBS while Creator Extend configures ComfyUI/MinIO and desktop tool paths. Both use the shared
`apps/shared/local-settings` persistence and secret-store contract.

`SocialManagement.svelte` is also shared by both apps. It renders the compiled profile/provider
catalog and bundled logo data directly in the Tauri webview. Its fixed native bridge starts the
loopback OAuth service and opens provider consent in the system browser; tokens and webhook secrets
never cross into the webview. `ProfileSwitcher.svelte` keeps the active Stream or Content workspace
available from every app view; Social Management remembers the detailed account route per profile.
`RecordingLibrary.svelte` is the Creator Extend view over the shared private local recording inbox.

`AudioSetup.svelte` appears for Audio Production or Soundboard selections. Its explicit read-only
check shows platform routing-tool presence, a bundled reference and four off-air acceptance steps.
Both guide buttons reuse the bundled text viewer. It keeps audio operation unverified regardless
of tool presence and does not modify the shared capability snapshot.
