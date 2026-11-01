# soundboard

**Labels:** `Content` `Stream` · **Setup:** [manual](setup/manual.md) · [automated](setup/automated.md) (manual only)

A DJ-style sound bar for streaming and content recording — named audio clips triggered on
hotkeys, mixed straight into your recording or stream.

## What this actually is

[`cg2121/obs-soundboard`](https://github.com/cg2121/obs-soundboard) — an OBS Studio plugin
(GPL-2.0, actively maintained), not a separate app. It adds a Soundboard dock to OBS itself: add a
sound, name it, browse for the audio file, done. Per-sound hotkeys, plus hotkeys for
mute/pause/restart/stop the currently-playing sound. OBS filters (noise gate, compressor, gain)
apply to it like any other source.

Because it plays as a native OBS audio source, it needs **no separate virtual-audio-cable
routing** the way apps outside OBS do — see
[`../audio-production/routing/README.md`](../audio-production/routing/README.md) for why BlackHole
/ VoiceMeeter / PipeWire exist at all (getting *other* apps' audio into OBS). The soundboard is
already inside OBS's mixer; it just needs an output-track assignment (Advanced Audio Properties),
same as deciding whether your mic goes to the stream track, the recording track, or both.

## Starter pack

[`sounds/manifest.yaml`](sounds/manifest.yaml) registers every slot — `bundled` (a real file ships
here) or `placeholder` (the name and hotkey slot exist; you supply the audio). 8 bundled clips,
all [Kenney.nl](https://kenney.nl) CC0 1.0 — stingers, a record scratch, UI dings — genuinely free
to ship. The classic meme sounds (Vine Boom, Bruh, Windows Error, MLG Air Horn, "emotional
damage," etc.) are **placeholders on purpose**: every one of them is extracted from a specific
copyrighted movie, game, show, or piece of branded software. No meme-soundboard site's copy is
actually public domain, whatever the site implies — this platform doesn't ship copyrighted audio
it doesn't have rights to, the same rule `docs/IMAGE_INTAKE.md` already holds photo corpora to.
Bring your own copy (from media you own) or a properly licensed SFX library for those slots.

## Boundary with audio-production

[`audio-production`](../audio-production/README.md) owns getting audio **into and out of** OBS —
mic, game, AI voice, call-in, monitor buses, the virtual-cable routing matrix. This module owns
one OBS-native source: canned clips, triggered on demand. A soundboard clip never needs to leave
OBS to reach the stream; it only needs the routing matrix if you want it to also reach an external
app (e.g. feeding it into a Discord call via the same virtual cable the mic uses).

## AI-authored phrase path

The [prompt and audition workflow](../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md#prompt-audition-alignment-and-improvement)
now generates an editable prompt per Soundboard personality and produces audio
previews on demand. Review the prompt and sound together, record feedback, approve an exact
revision, then select it for production. Subsequent improvements remain drafts until reviewed.
P-066-UI is built at **Automated streaming → Personalities → Prompt & Voice Preview** in Stream
Extend. See the [operator guide](../automation-control/voice_studio/README.md) for review and setup.

[P-066](../../docs/proposals/PROPOSAL_ASTRA_REACTION_AUDIO.md) adds a local phrase
library: an installed Ollama model creates text and native speech renders gaming reactions;
an operator reviews and accepts the asset; then the operator loads the accepted file into this
OBS Soundboard and binds it to an exact hotkey. The Soundboard remains the playback owner. It does
not generate speech, call a model, or load files into its dock automatically.

This path is gaming-only in the first scope. OpenTech, AI, and general technology personalities
remain on approved script/outline delivery through Audio Production's AI-VOICE path and do not use
the Soundboard. The policy and fallback matrix is in
[streaming personality audio routing](../../docs/architecture/stream-personality-audio-routing.md).

An accepted spoken phrase is a distinct asset from the existing CC0/SFX starter pack. Generated
creator audio should remain local-only until the phrase library and provenance policy are accepted;
it must not be added to the shipped manifest without the same rights, checksum, and size evidence
required for every bundled file.

## Submodules

| Folder | Purpose |
|---|---|
| [`sounds/`](sounds/manifest.yaml) | Starter-pack audio + the manifest registering what's bundled vs. placeholder |

## Status

[Stream Autopilot's director](../automation-control/stream_director/README.md) can map game
reactions to these registered slots and invoke explicitly configured OBS hotkeys, with a global
cooldown and optional stop on pause. Plugin installation and clip loading remain manual; live
playback through this adapter has not been verified yet.

`scaffolded` (`CLAUDE.md` §11) — the plugin install is documented and the starter pack is real;
nothing here has been run inside a live OBS yet (`P-044`). The Astra phrase-library integration is
built under `P-066` (see the [voice studio guide](../automation-control/voice_studio/README.md)): the
studio generates, auditions and approves reviewed phrase WAVs off air, and the director plays an
accepted clip only through a manually bound hotkey. It is opt-in and off by default, and no approved
clip has been imported or played in a live OBS yet (`ST-R13`).
