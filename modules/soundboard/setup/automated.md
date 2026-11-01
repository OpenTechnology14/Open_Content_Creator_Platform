# soundboard — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

**There is no automated setup for this module.** `obs-soundboard` is a third-party OBS plugin
installed via its own installer/package, and OBS's Docks menu and per-sound configuration are
GUI-only. Initial setup is not automated.

**Playback integration is now available:** [P-056's stream director](../../automation-control/stream_director/README.md)
can discover OBS hotkeys and invoke exact operator-configured names for already-loaded clips.
It reuses this module's manifest slots and reports unbound/missing hotkeys. This does not expose
the plugin's sound-list editing API or automate loading files into the dock.

## What exists

The starter pack itself: [`sounds/manifest.yaml`](../sounds/manifest.yaml) plus 8 bundled CC0
audio files under `sounds/stingers/` and `sounds/ui/`. No service, no container, no Make target —
these are plain files a human loads into the Soundboard dock one at a time (see
[manual.md](manual.md)).

## What automation would take

OBS's own scripting API (`obs.obs_hotkey_*`) could in principle drive sound-loading
programmatically, but `obs-soundboard` doesn't expose its sound list through OBS's WebSocket API —
confirmed by reading its source, not assumed. Automating "load the whole starter pack in one
click" would mean either a companion OBS Lua/Python script reading `manifest.yaml` and calling
this plugin's internal functions directly (fragile — breaks on any internal refactor of a plugin
this repo doesn't maintain), or asking upstream to expose one. Neither is in scope here; loading
8 starter sounds by hand takes a few minutes once.
