# Shared Social Management bridge

This Tauri plugin is used by Stream Extend and Creator Extend. It compiles the committed Social
Management catalog, four brand assets, and the fixed Python service into each desktop application.
The native UI can render the logos from data URLs without filesystem permission. The plugin only
starts the bundled loopback service on `127.0.0.1:8765`; it exposes no arbitrary process, path, URL,
or port control to the webview.

The Social Management module must first be selected and installed through **Module setup**. Its
isolated Python environment is shared by both apps. OAuth consent opens in the system browser because
providers can reject embedded webviews. Tokens remain in the operating system credential manager;
the Tauri surface receives only the authorization URL and redacted connection records.

The plugin also owns a shared local active workspace for Stream and Content. Brand, provider,
capability, and redacted connection ID are remembered separately for every profile, so switching
away and back restores the operator's last route without exposing OAuth tokens to the webview.

Run its focused tests with either desktop workspace:

```bash
cargo test --locked --manifest-path apps/stream-extend/src-tauri/Cargo.toml -p tauri-plugin-social-manager
```
