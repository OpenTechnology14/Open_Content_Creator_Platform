# Audio routing

See [../setup/manual.md](../setup/manual.md) for the full architecture. This folder
holds the per-OS routing references; preset import compatibility and live audio remain separate acceptance:

| File                          | OS       |
| ----------------------------- | -------- |
| `../voicemeeter/potato-config.xml` | Windows  |
| `blackhole-loopback.json`     | macOS    |
| `pipewire.conf`               | Linux    |

## Bus mapping (canonical)

| Bus       | Source                  | Destination                |
| --------- | ----------------------- | -------------------------- |
| MIC       | host microphone         | OBS Tracks 1 + 2 + monitor      |
| GAME      | game / app audio        | OBS Tracks 1 + 3          |
| MUSIC     | media player            | OBS Tracks 1 + 6 (copyright safe only) |
| AI-VOICE  | TTS bridge              | OBS Tracks 1 + 4 + monitor      |
| CALL-IN   | Discord / VoIP          | OBS Tracks 1 + 5 (mix-minus)    |
| MONITOR   | composite for headphones| headphones only            |

In OBS **Advanced Audio Properties**, assign each source to Track 1 (the full mix) and its
isolated track above. MONITOR stays in headphones only. In **Settings → Output**, use Advanced
mode, select the recording tracks and a container supporting multiple audio tracks, such as MKV.
Select Track 1 as the streaming audio track. The table below uses the same assignments.
See the [official OBS multi-track recording guide](https://obsproject.com/kb/multiple-audio-track-recording-guide).

Listen to the full mix and each isolated track in an editor that can select audio tracks;
a normal player may play only one track. Track configuration alone does not prove that a
source is audible or that the recording contains the intended channels.

## TTS / AI voice routing

For the [ai-agents](../../ai-agents/setup/manual.md) module and any TTS pipeline:

1. The AI/TTS process outputs to **its own** virtual device (VB-Cable B, BlackHole 2ch).
2. VoiceMeeter / Loopback picks that up as VIN2 — the AI-VOICE bus.
3. Route AI-VOICE to **B1** (stream + recording) and **A1** (your headphones).
4. **Never** route AI-VOICE into the mic-in your agent listens on. That is a feedback loop: the
   agent hears itself, responds to itself, and does not stop.

If the agent takes voice input, the mic is routed *into* the agent as a separate input-device
assignment — not part of the bus matrix.

## Podcast / multi-track recording

Recording remote guests: use the isolated tracks configured in **Advanced Audio Properties**
and enabled in **Settings → Output → Recording**. Post-production then gets isolated speakers, which is the difference between fixing
one guest's bad audio and re-recording.

OBS supports six tracks:

| Track | Content |
|---|---|
| 1 | Full mix (stream-ready) |
| 2 | Mic only |
| 3 | Desktop / game |
| 4 | AI / TTS |
| 5 | Call partners (mixed) |
| 6 | Music only |

## VST chains

Free VSTs worth considering:

| Plugin | Purpose |
|---|---|
| **TDR Nova** | Dynamic EQ |
| **TDR Kotelnikov** | Mastering compressor |
| **Voxengo Span** | Spectrum analyser — look, do not process |
| **iZotope Vocal Doubler** | Width on a talking head |

Apply sparingly. The gate → compressor → EQ → limiter chain in
[`../setup/manual.md`](../setup/manual.md) is usually enough, and stacking a VST chain on top of
it is how voices start sounding processed rather than clear.

