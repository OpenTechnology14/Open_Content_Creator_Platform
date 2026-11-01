# Stream Autopilot avatar worker

This Character / Avatar worker drives configured VTube Studio talk and idle hotkeys from the
speech worker's actual playback start, finish and cancellation events. It accepts only the
configured on-air session, current generation and bound logical avatar IDs. Stale, duplicate,
off-air and mismatched-finish events cannot animate the model.

Validate configuration without connecting to VTube Studio:

```bash
PYTHONPATH=modules/character-avatar python3 -m stream_avatar --validate
```

After loading an operator-owned model and setting the hotkey IDs in
[`configs/local/stream-avatar.yaml`](../../../configs/local/stream-avatar.yaml), connect to the
authenticated backend with `--backend`. The first connection can display VTube Studio's normal
plugin authorization prompt. The token remains in the existing local VTS token file.

This provides playback-timed talk/idle animation. It does not bundle an avatar asset, infer face
or body motion, add a browser source to OBS, or prove the configured hotkeys against a live model.
Those remain native acceptance steps.

## Owned body cue integration (P-056)

Optional `full_body_enabled` requires a `vts_model_id` plus eight distinct body-only hotkey IDs:
wave, nod, shrug, look_left, look_right, happy, surprised and neutral. `speech_cues` optionally
rotates configured cues on actual playback start; it cannot bypass talk/idle or change speech
identity/generation. The body rig/animations are operator-owned assets, not generated here.
This VTS adapter targets compatible Live2D/VTS assets; the logical name `nova-vrm` is not a
claim of VRM-format support. VRM/other rendering backends retain their separate asset/integration scope.

Operator cue events use `events.stream-avatar.cue` with schema version, event/session/avatar IDs,
one declared cue and an aware creation time. Paused, stale, duplicate, off-air, pre-resume and
wrong-active-avatar cues are dropped. The adapter verifies the bound current model and only
allows animation/expression hotkeys, excluding model switching, screenshots and downloads.
Cue API acknowledgement does not prove correct visible motion or a body-only animation.

`--idle` resets configured talk/body state using **existing** authorization. It does not request
a new VTS plugin token during emergency cleanup. The supervisor uses it after ending its avatar
worker and reports an unconfirmed reset as an error. Real rig, hotkey/mouth coexistence,
model-switch, pause and timing acceptance remain required before enabling the option.
