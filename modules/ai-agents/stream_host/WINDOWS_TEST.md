# Stream Autopilot: Windows and Mac test

The first Windows target is Windows 11 x64 with Python 3.12 x64 and an installed Windows
speech voice. This is a native Python rehearsal, separate from the Tauri desktop apps.
It exercises the host, director preview, native speech export, show calendar and Shorts.
Windows native acceptance is pending until this runs successfully on a Windows device.

## Start on Windows

Copy the current working tree to the device, or extract the supplied Stream Autopilot test
kit ZIP. Open PowerShell in that folder. These changes are local and uncommitted; cloning the
remote repository alone will not include them yet. Install Python 3.12 if `py -3.12 --version`
is unavailable, then run:

```powershell
py -3.12 scripts/setup/stream_autopilot.py install
.\.venv-stream-autopilot\Scripts\python.exe scripts/setup/stream_autopilot.py doctor
.\.venv-stream-autopilot\Scripts\python.exe scripts/setup/stream_autopilot.py smoke
```

Installation downloads Python dependencies and bundled FFmpeg from PyPI into the local
`.venv-stream-autopilot` folder. No environment activation, PowerShell execution-policy change,
Bash, Make, Docker, capture card, dedicated GPU, game account or model download is required.
Run all commands from the extracted folder, not from inside the ZIP. Keep the full folder
structure. Existing test output is preserved; each run gets a new output folder.

`doctor` must report `ready: true`. OBS/Ollama PATH checks are informational and may say false
even when an app is installed elsewhere. `smoke` verifies the actual installed speech voice.
It produces `output/stream-autopilot/local-test-.../report.json` with `status: passed`, plus:

- `reply.wav`: real system speech from one Nova rehearsal reply.
- `calendar.json`: 28 draft daily shows with game personalities and project metadata.
- `source.mp4`: a synthetic 90-second test video with a tone.
- `review.html` and `clip-plan.json`: open the review page and select `source.mp4` to scrub it.
- `shorts/`: three verified 720 × 1280 MP4s and their manifest (7, 10 and 10 seconds).
- Stage JSON/log files, including DJ Soundbox/OBS integration previews.

If a stage fails, keep its `.log` and `report.json`. Send the report back for diagnosis.
If Python dependencies are missing, repeat `install`. A failed speech stage can mean no
usable Windows voice, unavailable Windows PowerShell/System.Speech, or a system restriction;
use a standard Windows desktop account with a working installed speech voice. Do not change
security policy to bypass restrictions. The speech exporter accepts an optional installed
voice name through `--voice`; logical Nova profile IDs are not installed voice names.

## First OBS recording

After the rehearsal passes, install/open OBS manually on the same device. Create a test scene
and add `source.mp4` as a Media Source. Check the preview and audio meters, record about 30
seconds locally, then inspect the recording. Test `reply.wav` as a Media Source separately.
Start with low monitoring volume because the synthetic video has a continuous test tone.
This step verifies your OBS installation and recording/audio path. A capture card is only
needed later for bringing external console HDMI into the computer.

For live bindings, use the [director guide](../../automation-control/stream_director/README.md)
to discover your actual OBS scene/input/hotkey names. Configure `stream-director.yaml` for that
device and verify each binding locally. DJ Soundbox plugin installation, scene setup, audio
routing, OBS credentials and stream accounts remain manual. This rehearsal does not connect
to OBS or test an audible Soundbox reaction.

## Same test on Mac

```bash
python3.12 scripts/setup/stream_autopilot.py install
.venv-stream-autopilot/bin/python scripts/setup/stream_autopilot.py doctor
.venv-stream-autopilot/bin/python scripts/setup/stream_autopilot.py smoke
```

The runner uses macOS `say` or Windows PowerShell `System.Speech` and shares the remaining
Python pipeline. `tzdata` supplies the show planner's IANA timezone database on Windows.
The same logical host/show identity applies on both operating systems.

## What a passing test proves

A passing report proves this scripted local pipeline on the recorded OS. It does not prove
live chat ingestion, Ollama/model quality, avatar rendering, continuous voice playback,
automated gameplay, device-level human/agent takeover or a complete unattended broadcast.
The director uses preview mode, and the calendar is a draft, not a scheduler. Games, GPUs,
plugins, editor tools and Tauri desktop bundles each need their own OS acceptance tests.

The repository includes a Windows/macOS GitHub Actions smoke workflow; it has not been run
remotely as part of this local change. A Mac pass or mocked Windows contract test does not
count as native Windows evidence.
