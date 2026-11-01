# soundboard — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

A DJ-style sound bar inside OBS: named, hotkeyed audio clips you trigger live.

## Install the plugin

[`cg2121/obs-soundboard`](https://github.com/cg2121/obs-soundboard) — requires OBS Studio 28.0.0+.

1. Download the release matching your OS from the
   [releases page](https://github.com/cg2121/obs-soundboard/releases) (Windows x64, macOS
   arm64/x86_64, or Linux).
2. Run the installer (Windows/macOS) or follow the Linux package's own instructions.
3. Restart OBS. Open **Docks → Soundboard** to show the dock.

## Load the starter pack

1. In the Soundboard dock, click **+** in the lower-left corner.
2. Enter a name and browse to a file under [`../sounds/`](../sounds/manifest.yaml) — see
   [`manifest.yaml`](../sounds/manifest.yaml) for what's bundled vs. a placeholder you fill in
   yourself.
3. Repeat per sound. Right-click a sound to set its hotkey, duplicate it, or open Advanced Audio
   Controls.

## Route it

The soundboard plays as a native OBS audio source — no virtual-audio-cable needed just to reach
your stream or recording. Decide its **output track** in Advanced Audio Properties:

- Same track as your mic — soundboard clips are baked into whatever your mic reaches.
- A separate track — lets you keep a stream-only or VOD-only soundboard (e.g. keep sound effects
  out of a clean recording for later editing), or mute/unmute it independently in post.

Only reach for [`../../audio-production/routing/README.md`](../../audio-production/routing/README.md)
if you need a soundboard clip to reach something *outside* OBS too — e.g. feeding a sound into a
Discord call through the same virtual cable your mic already uses.

## Verification

For per-game automatic playback, follow [the director's binding instructions](../../automation-control/stream_director/README.md)
after loading clips. Discover and test exact plugin hotkey names; the manifest slot is not itself
an OBS hotkey name. Live Autopilot playback still needs verification in your OBS instance.

Two halves. Run the automated one first — it is cheap and catches the class of problem that does
not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (manifest schema, bundled-file existence, docs
  integrity)

**Manual — nothing automates these:**

- [ ] The Soundboard dock shows in OBS after install
- [ ] A bundled sound plays with no perceptible lag when its hotkey is pressed
- [ ] The sound reaches the track you assigned it to (test-record a clip and check)

### Last step — full feature test run

With setup complete, run this module's section of
[`../../../tests/ACCEPTANCE-CHECKLIST.md`](../../../tests/ACCEPTANCE-CHECKLIST.md) end to end.

**This does not block the next module.** A failing line is a finding against *this* module, not a
gate on starting another. The full checklist is a **release gate** — the platform is done when
every section passes, and not before.

Record what you ran in this module's row in [`../../../docs/PROPOSALS.md`](../../../docs/PROPOSALS.md).
[`../../../docs/agent/VERIFICATION-MATRIX.md`](../../../docs/agent/VERIFICATION-MATRIX.md) requires
the command and its result — **"not run" is an acceptable answer; silence is not.**

If you find a manual step here that could be automated, automate it and delete the step. Driving
the manual count down is the measure of progress, not adding more of them.

## Troubleshooting

- **Dock doesn't appear** — confirm OBS is 28.0.0+; older versions aren't supported.
- **Sound doesn't reach the stream** — check its output track in Advanced Audio Properties; a
  track your encoder isn't using is silent no matter how loud the source is.
- **Placeholder sound has no file** — expected; see `sounds/manifest.yaml`, `status: placeholder`
  entries need audio supplied by you.
