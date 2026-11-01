# Local host speech export

P-056's first audio adapter renders **one saved host reply** to a PCM WAV using an installed
macOS or Windows system voice. It does not play audio, route an OBS bus, clone voices, or drive lip sync.
Voice IDs in host profiles are logical future bindings; use `--voice` to select an installed
system voice. No model download or network service is needed.

From the repository root, with Python 3.11+ and Loguru installed:

```bash
python3 modules/audio-production/tts/render_reply.py --help
python3 modules/audio-production/tts/render_reply.py \
  --reply /tmp/host-reply.json --session minecraft-main --output /tmp/host-reply.wav
```

The input is a single `stream_host` reply object or an existing backend `/events` envelope
whose source is `stream-host`. Rejects a different session, non-replies, oversized inputs and
existing output files. Text goes to the speech executable via stdin without a shell.

Verification: inspect the resulting WAV's frame count and duration, then listen during a local
preview. Offline tests verify session selection and that viewer text cannot become CLI options.
Windows uses its installed Windows PowerShell `System.Speech` engine with JSON on stdin;
macOS uses `say`. Windows native acceptance is pending. Linux speech is not implemented. A Piper
adapter and actual playback/cancellation are later work; the exported file can be inspected
with any WAV player.

Use the [Windows/Mac test guide](../../ai-agents/stream_host/WINDOWS_TEST.md) for dependency installation and a complete local rehearsal. Windows viewer text is passed as JSON data to fixed repository-owned PowerShell code, without changing execution policy.

## Blind voice audition (P-068 slice 2)

[`audition.py`](audition.py) is the rig [P-068 section 6.1](../../../docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md)
and `P-067` section 7.5 call for: the same script in several voices, so you can rank them by ear
without knowing which is which. It removes the three biases that most distort that kind of test.
Standard library only; candidates must be 16-bit PCM WAV.

```bash
# the script, spoken by the installed OS voice (the incumbent) plus two WAVs you rendered elsewhere
python3 modules/audio-production/tts/audition.py build --out audition --text-file script.txt \
  --native nova-local --candidate local-clone=clone.wav --candidate dave=dave.wav

# listen to audition/take-1.wav ... take-3.wav, then rank them, best first (1=3 means a tie)
python3 modules/audio-production/tts/audition.py reveal audition --rank 2 3 1 --subject local-clone
```

- **Order:** takes are shuffled with a recorded seed (`--seed` to repeat a shuffle).
- **Labels:** files are neutral `take-N.wav`; the answer key is `key.reveal-after-ranking.json`; `build`
  prints only take paths, and no warning it prints names a voice.
- **Loudness:** louder candidates are attenuated to the quietest's level (attenuation only, so nothing
  clips; the quietest is copied byte for byte). `--no-match-level` copies everything unchanged and
  warns when levels differ by more than 1 dB, because louder voices are rated higher.
- **The rule:** `reveal` records your ranking once in `result.json`. With `--subject` it reports
  whether that voice ranked first (a tie for first counts) and, if the incumbent (`--incumbent`,
  default `nova-local`) is in the test, whether it ranked below it. Below the incumbent, section 6.1
  says to abandon local voice for that account.

`--native LABEL[=VOICE]` renders `--text-file` with the installed macOS or Windows voice (at most 500
characters, the limit `render_reply.py` applies). Convert anything else first, for example an
ElevenLabs download: `ffmpeg -i in.mp3 -c:a pcm_s16le out.wav`.

Limits: sample rate and channel count are visible in the files and can reveal a voice to someone who
looks, so `build` warns instead of resampling (a crude resampler would colour the comparison). The
mid-clip voice switch of `P-067` section 7.5 is not covered, and ElevenLabs is not called. The rig makes
the listening fair; it does not do the listening.

## Checking a clone-source recording (P-068 slice 3)

[`check_voice_sample.py`](check_voice_sample.py) measures what can be measured objectively about a
recording you mean to clone from ([P-068 section 5.4](../../../docs/proposals/PROPOSAL_LOCAL_TTS_STACK.md)),
so a bad take is caught before it is baked into a voice. Standard library only; it reads 16, 24 and 32-bit
PCM and float WAV, in blocks, so a 10-minute stereo 24-bit file takes about five seconds.

```bash
python3 modules/audio-production/tts/check_voice_sample.py ~/nova-voice/owner-measured.wav
python3 modules/audio-production/tts/check_voice_sample.py recording.wav --json --strict
```

| Check | Fails when | Warns when |
|---|---|---|
| format | not 48 kHz, or not mono/stereo | |
| length | under 6 s (the XTTS v2 minimum) | under 3 min or over 10 min |
| clipping | 3 or more consecutive full-scale samples | peak above -1 dBFS |
| level | no speech found, or speech under -45 dBFS RMS | speech under -35 or over -9 |
| noise | speech under 30 dB above the noise floor | under 40 dB |
| silence | | 40 ms or more of exact digital silence inside the recording: edits, gating, noise reduction |
| dc | | DC offset beyond 0.5% of full scale |
| drift | | speech level varies by over 6 dB between 30 s sections: mic distance or gain moved |
| bandwidth | | a sharp low-pass below 17 kHz, the signature of an MP3/AAC or low-rate source |

Exit status is 0 when ready (warnings allowed; `--strict` makes them count), 1 when not ready and 2 when
the file cannot be read. Every measured number is printed, because the thresholds are **starting values
for the first real recording, not measurements of a good one**; tune them in the script once you have one.

- **Leave a few seconds of room tone at the start.** The noise floor is the quietest tenth of the
  recording, so continuous speech with no pauses makes it read too high.
- **The bandwidth check closes a hole in section 5.4's own pass condition.** An MP3 converted to 48 kHz
  PCM passes the `ffprobe` check yet clones the artifacts; the cutoff it leaves is what this looks for.
  It cannot prove a source was lossless: a high-bitrate MP3 cuts off above the 17 kHz scan.
- **Not covered:** room reflections and reverb, mains hum, register, varied content, splices that leave
  no digital silence, and consistency between takes. A pass means the recording is not obviously
  broken, not that it will clone well; judge the rest by ear and by the section 6 tests.
- Level, noise and spectrum use the first channel; clipping is checked on every channel.
