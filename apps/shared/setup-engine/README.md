# Shared readiness engine

This Rust crate gives Stream Extend and Creator Extend one local capability-readiness contract.
Product manifests in `configs/setup/` declare check IDs and capability dependencies. Each app runs
its own authenticated native probes, then this crate calculates capability state, persists the
versioned evidence, expires stale observations, and returns the same shape to the shared setup UI.

OpenTechnology synchronization is optional. When enabled in Module setup, the engine posts one
sanitized `setup.check.observed` event per check to the configured project. The API key is stored
in the operating system credential manager; public settings and readiness JSON contain no key.
Retries reuse the persisted event ID so the server can deduplicate them. `not_checked` is local
state and is not published.

Run the contract and real loopback HTTP publisher tests from the repository root:

```bash
cargo test --locked --manifest-path apps/shared/setup-engine/Cargo.toml
```

The engine does not route OBS, capture, or ComfyUI traffic through the cloud. It reports only the
checks declared by the product manifest. A Ready capability does not certify unrelated modules,
physical capture stability, models, or a public broadcast.
