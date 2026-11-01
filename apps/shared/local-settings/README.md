# Local settings

Shared persistence for Stream Extend and Creator Extend. Ordinary connection endpoints are
written atomically to each app's local-data directory. Passwords and access keys use macOS
Keychain, Windows Credential Manager, or the platform credential store selected by `keyring`.

The crate does not expose secret values to the frontend and never writes them to JSON or logs.
Each app owns validation and its redacted frontend view.
