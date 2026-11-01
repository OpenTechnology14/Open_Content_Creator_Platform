# audio-production — manual setup

P-056 adds [a local host speech exporter](../tts/README.md) for macOS/Windows WAV generation. It does
not configure the live routing described below or provide continuous AI voice playback.

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

Routing and processing committed as configuration, instead of rebuilt from a tutorial each time.

## Hardware

- **A real USB or XLR mic.** Blue Yeti, Shure MV7, Rode NT-USB are fine starting points. Anything
  that ships as part of a webcam is not.
- **Closed-back headphones.** Open-backs leak into the mic, and no amount of gating fixes that.
- **A pop filter.**
- Optional but recommended: a small audio interface (Focusrite Scarlett 2i2 or similar) for XLR.

## Software by OS

**Windows**
- **VoiceMeeter Potato** — virtual mixer + routing matrix (donate-ware)
- **VB-Cable** (multiple instances) — extra virtual cables for app-specific routing
- **EQ-APO + Peace** — system-wide EQ if your interface lacks one

**macOS**
- **BlackHole** (2ch / 16ch) — virtual audio device, replaces VB-Cable
- **Loopback** (paid) — graphical routing, replaces VoiceMeeter; or **SoundSource** for cheaper
  per-app routing

**Linux**
- **PipeWire** — solves the whole problem natively on modern distros
- `pw-loopback` + `pw-link` for virtual cables and routing
- LSP plugins (LADSPA/LV2) for processing

## Bus architecture

Aim for at least these logical buses:

| Bus | Sources | Goes to |
|---|---|---|
| MIC | Your microphone | Stream, recording, call apps |
| GAME | Game / desktop audio | Stream, recording, headphones |
| MUSIC | Background music | Stream (optional), recording, headphones |
| AI-VOICE | TTS / agent voices | Stream, recording — **not** back into the AI's own mic-in |
| CALL-IN | Discord / Zoom partners | Headphones + stream, **not** back to themselves |
| MONITOR | What you hear | Headphones only |

The "not back to themselves" constraint is **mix-minus**, and it is the entire reason virtual
routing exists. Without it, call partners hear their own echo.

## VoiceMeeter Potato — Windows reference

Use `modules/audio-production/voicemeeter/potato-config.xml` as a routing reference. Its custom
XML format has not been verified against VoiceMeeter **Load Settings**. Configure your actual
devices in VoiceMeeter and save a working preset there before attempting any import.

- **Hardware input** — HW1: mic (interface input)
- **Virtual inputs** — VIN1 desktop (set Windows default playback to "VoiceMeeter Input"),
  VIN2 AI/TTS (AI app output → "VoiceMeeter AUX Input"), VIN3 call (Discord output →
  "VoiceMeeter VAIO3 Input")
- **Hardware output** — A1: headphones
- **Virtual outputs** — B1 → OBS (OBS captures "VoiceMeeter Output"), B2 → Discord mic-in
  (Discord input = "VoiceMeeter AUX Output", carrying mix-minus)

Per-channel routing:

| Channel | A1 | B1 | B2 |
|---|---|---|---|
| Mic | ✓ | ✓ | ✓ |
| Desktop | ✓ | ✓ | ✗ |
| AI voice | ✓ | ✓ | ✗ |
| Call audio | ✓ | ✓ | ✗ — otherwise echo |

## Mic processing chain

Same order as the OBS chain in
[creator-experience](../../creator-experience/setup/manual.md): noise suppression → gate →
compressor → limiter. Apply it once, in one place — doing it in both VoiceMeeter and OBS
double-processes and sounds worse.

## In-app routing check

In either app's **Module setup**, select Audio Production or Soundboard and click
**Check audio routing tools**. This read-only native check needs no Python. It checks standard
locations for the platform's tools and displays a bundled routing reference plus off-air
level, mix-minus and hotkey acceptance steps. A tool may be installed elsewhere; finding it
proves presence only. Use **Read audio setup guide** or **Read soundboard and hotkey guide**
for the full bundled instructions. The macOS JSON is guidance, not an importable Loopback preset.

## Recording tracks

In OBS **Advanced Audio Properties**, send each intended stream source to Track 1 for the
full mix. Also send mic to Track 2, desktop/game to Track 3, AI voice to Track 4, call partners
to Track 5 and music to Track 6. Keep the headphone MONITOR bus out of recording to avoid
capturing the mix twice. Enable those recording tracks in **Settings → Output → Recording**
(Advanced mode) and use a multi-track container such as MKV. Select Track 1 for streaming.
Listen to Track 1 and each isolated track in an editor that can select audio tracks.

On macOS, Discord's **Input Device** should be the physical microphone for a mic-only send,
or a dedicated virtual mix-minus input that excludes CALL-IN. **Built-in Output** is a
playback device, not the call microphone. Verify the selected input and output separately.

The [routing guide](../routing/README.md) uses the same track assignments. The
[official OBS guide](https://obsproject.com/kb/multiple-audio-track-recording-guide) explains
source assignment and recording-track enablement; the actual recording still needs a listening check.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test` — the repo-wide offline suite (docs integrity, script portability)

**Manual — nothing automates these:**

- [ ] A call partner cannot hear themselves
- [ ] Stream captures mic + desktop + AI voice at correct relative levels
- [ ] You hear everything in your headphones
- [ ] Recording levels peak below −1 dB

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

- **Call partners hear an echo** — B2 is receiving call audio; remove that route.
- **AI voice feeds back into itself** — AI-VOICE is routed into the bus the AI listens on.
- **Crackling / dropouts** — sample rates differ between the interface and the virtual device.
  Set everything to 48 kHz.
