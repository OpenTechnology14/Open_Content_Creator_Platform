# automation-control — manual setup

**Labels:** `Content` `Stream` · Automated path: [automated.md](automated.md)

Two halves: OBS WebSocket (so anything can drive OBS) and n8n (cross-system workflows where
writing a service would be overkill).

## OBS WebSocket — enable and secure

In OBS: **Tools → WebSocket Server Settings**.

1. Enable the server.
2. Set a password. Do not leave it blank — anything on your network could otherwise drive your scenes.
3. Note the port (default 4455).
4. Put the password in `.env` as the value the platform reads; never commit it.

Verify from the repo root. The check needs an OBS WebSocket client that no Compose service provides, so
install it once into a virtual environment (Homebrew and many Linux Pythons refuse a bare `pip install`)
and keep that environment active when you run it:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r scripts/setup/requirements-obs.txt
make test-obs                      # or: python scripts/setup/test_obs_websocket.py
```

It reads `OBS_WEBSOCKET_HOST`, `OBS_WEBSOCKET_PORT` and `OBS_WEBSOCKET_PASSWORD` from the environment, then
from the repo-root `.env` (see `.env.example`) for anything unset.

> **Corrected 2026-10-05.** An earlier version of this step ran `make test-obs` with no install step, and the
> script only saw variables exported in the shell — so the password from step 4 never reached it. The script
> now uses `obsws-python` (pinned in `scripts/setup/requirements-obs.txt`; the observability exporter uses
> the same client) and loads the repo-root `.env` itself.

## n8n

Lives at `modules/automation-control/n8n/`, Docker service in `docker-compose.yml` under the
`automation` profile.

```bash
make up-with-automation
./scripts/setup/n8n_import.sh
```

n8n is the glue for workflows that do not justify a service:

- **On stream start, post to social.** Trigger: OBS WebSocket `StreamStateChanged` → HTTP to
  FastAPI → parallel branches (Twitter, Mastodon, Discord) → log to Postgres.
- **VOD post-processing.** Trigger: new file in MinIO `recordings/` → ffmpeg job → thumbnail to
  `thumbnails/` → row in Postgres `vods` → notify creator.
- **Sponsor impression rollup.** Cron at 23:55 → query Postgres → email summary.

After import, open each workflow and fill in its credentials — the export carries the graph, not
the secrets.

**Production note:** n8n needs persistent storage for workflow definitions (`/home/node/.n8n`).
The volume mount is already configured in `docker-compose.yml`.

## Advanced Scene Switcher

An OBS plugin, installed and configured inside OBS. Use it for scene logic that should survive
n8n being down.

## Remote control

Both Extend desktop apps now include a **Remote control** tab.

1. Choose hosted or self-hosted relay mode. For self-hosting, enter the base HTTP(S) URL; the app
   checks `/api/v1/health` and derives the `/ws` endpoint.
2. Enter the relay access token and save. The token goes to Keychain on macOS or Credential
   Manager on Windows; the public JSON stores only the mode, URL, and stable device identity.
3. Enable remote requests and connect. Copy the target workstation's displayed device ID to the
   controlling device.
4. Send a request from the controller panel. The target queues it and runs nothing until **Approve
   and run** is clicked locally.

Stream Extend accepts only OBS scene changes and stream start/stop requests. Creator Extend accepts
only committed ComfyUI workflow paths. Remote start/stop is never used as a setup test.

For a no-cost local acceptance relay:

```bash
python3 scripts/testing/fake_relay.py --port 8765 --token local-test-token
```

Use `http://127.0.0.1:8765` in two app instances. The harness binds only to loopback and is for
testing; it is not an internet-facing relay.

## Personality prompt, reaction audio and scripted Q&A

P-066's [voice studio guide](../voice_studio/README.md) covers Stream Extend's prompt/revision UI,
installed Ollama/native voice requirements, isolated off-air audition, approval, manual OBS
Soundbox imports/hotkeys and the paired director/speech settings. Scripted OpenTech/AI/technology
personas use its separate reviewed script, boundary pause and one-question flow, never Soundboard.
Do not enable a production manifest until the intended WAV, Stop All and recording track are
verified locally. Native Windows and the full OBS recording pass remain release gates.

## Stream Autopilot lifecycle

The committed policy keeps broadcast start and gameplay disabled. Validate it and rehearse the
durable lifecycle before binding live services:

```bash
PYTHONPATH=modules/automation-control python3 -m stream_autopilot status
PYTHONPATH=modules/automation-control python3 -m stream_autopilot rehearse
```

The same rehearsal is available in Stream Extend under **Automated streaming**. It exercises
preflight, preview, pause, restart-safe state and stop without contacting OBS, chat, a model,
audio, an avatar or a game.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `make up-with-automation`
- `make test-obs`

**Manual — nothing automates these:**

- [ ] n8n UI lists the imported workflow **and** its credentials are filled in
- [ ] Triggering a stream start fires the workflow end to end
- [ ] OBS WebSocket has a password set — not left blank

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

- **`make test-obs` fails to connect** — WebSocket server disabled in OBS, wrong port, or the
  password in `.env` does not match.
- **`make test-obs` says to install OBS dependencies** — the client library is missing from the Python that
  ran it. Activate the venv from the verify step, or install `scripts/setup/requirements-obs.txt` into it.
- **Workflow imported but never fires** — credentials not filled in after import.
- **n8n loses workflows on restart** — the `/home/node/.n8n` volume is not mounted.

## Stream Autopilot production controls (P-056)

Open Stream Extend → Automated streaming. The production owner uses the shared setup
Python environment and fixed bundled workers. Its initial private operator copies live under
`HybridCreatorPlatform/stream-autopilot-production/operator` in the OS application-data folder.
Close the production owner before editing its runtime/supervisor/worker policies or saved
Connections. Backend API key and OBS credentials stay in the native vault/settings path.
Use Check production readiness; a missing check blocks preview. Default Run and game input
remain locked. Preview is an explicit effect-worker start after readiness passes. Stop and
Emergency stop cancel owned workers; owned OBS sessions finalize into the shared Creator inbox.
A recording-handoff error requires manual import before deleting any recording.

For the first game acceptance, name an owned private Minecraft test world and its permission
in `minecraft-gameplay.json`, prepare the pinned SDK through the optional dependency control,
and bind a dedicated `hcp_` bot. Only bounded forward/back/jump are supported; no account login,
public game automation or OS input. Observe the bot in the game client while testing pause,
release, disconnect and manual takeover. VTube gestures need an authorized compatible licensed
rig and eight exact animation/expression hotkey IDs; the logical avatar name does not imply
VRM-format rendering. Follow the [runtime guide](../stream_autopilot/README.md) and record the
real timing/60-minute gates before claiming a phase complete.
