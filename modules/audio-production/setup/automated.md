# audio-production — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

**Audio routing has no automated setup.** Audio routing is OS-level and driver-bound —
VoiceMeeter on Windows, BlackHole/Loopback on macOS, PipeWire on Linux. None of it is
containerisable.

The [P-056 speech exporter](../tts/README.md) renders a saved reply to WAV. The
[`stream_speech`](../stream_speech/README.md) worker adds bounded continuous synthesis/playback,
generation-safe cancellation and exact start/finish events for the avatar. Module setup installs
both dependency sets. Voice selection and OBS audio routing remain manual.

## What exists — committed configuration

| File | Platform |
|---|---|
| `voicemeeter/potato-config.xml` | Windows — VoiceMeeter Potato bus-matrix reference |
| `routing/blackhole-loopback.json` | macOS |
| `routing/pipewire.conf` | Linux |

These are **reference configuration, not installer scripts**. The macOS JSON is not a Loopback
preset, and the custom VoiceMeeter XML has not been accepted as a native import format. Configure
and save an actual tool-generated preset against your hardware; review PipeWire configuration
before applying it.

## In-app read-only checks

Both apps bundle these references and a platform recipe in `configs/local/audio-setup.json`.
Selecting Audio Production or Soundboard exposes **Check audio routing tools**, which checks
standard filesystem locations without starting a process, opening audio devices or changing
routing. Presence and absence are reported separately from operation; custom-path installations
may be missed. Off-air level, mix-minus, recording and hotkey acceptance stays manual. This is
local workstation assistance and does not run on DigitalOcean.

## What automation would take

PipeWire is the one platform where routing could genuinely be scripted — `pw-link` calls in a
shell script would do it. VoiceMeeter and macOS aggregate devices are GUI-bound.

## Phone monitoring (the app path)

Stream Extend is specified to surface live audio levels per bus on a phone, so you can catch a
dead mic or a clipping bus without alt-tabbing off a live stream.

**Specified, not shipped** — `CLAUDE.md` §11 has this module at `scaffolded`.

What *is* real today: `observability`'s `source-health-exporter` polls audio buses and exposes
them to Prometheus, and the `source-health` Grafana dashboard renders them. That works now via
`make up` — see [observability](../../observability/setup/automated.md).
