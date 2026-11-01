# relay-client

Shared Rust client used by Stream Extend and Creator Extend for hosted or self-hosted WebSocket
relay connections.

`control.rs` owns the remote-control contract: public settings, OS-backed credential storage,
stable device identities, connection state, action validation, target filtering, the bounded local
approval queue, and correlated command results. App-specific modules execute the approved local
OBS or ComfyUI action.

Run its offline and loopback WebSocket tests with:

```bash
cargo test --manifest-path apps/shared/relay-client/Cargo.toml
```

The relay carries control messages only. Webcam, game capture, OBS rendering, and ComfyUI execution
stay on the target workstation.
