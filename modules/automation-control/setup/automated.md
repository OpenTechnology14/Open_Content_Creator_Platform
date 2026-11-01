# automation-control — automated setup

**Labels:** `Content` `Stream` · Manual path: [manual.md](manual.md)

Automated via a Compose profile plus a workflow-import script.

After selecting this module, either Extend app can start the bundled local storage, API and `n8n`
services from **Module setup**. Once healthy, **Initialize data & workflows** applies storage
initialization and imports the stable, inactive reference workflow through a fixed helper container.
Generated n8n credentials are stored in the OS credential manager and can be copied individually
without appearing in the job log. Provider credentials inside the workflow remain a manual handoff.

P-056's [native stream director](../stream_director/README.md) also offers configuration
validation, read-only OBS discovery and event preview/application. Dependency installation,
soundboard dock loading, exact OBS bindings and startup remain manual; it has no Compose service.
The [Stream Autopilot supervisor](../stream_autopilot/README.md) has a no-effects lifecycle
rehearsal in Stream Extend and a local production CLI that composes the host, director, continuous
speech, optional VTube Studio control and optional Twitch chat ingress. The module installer adds
the supervisor's shared Python dependencies. Account secrets, OBS bindings and native app
acceptance remain manual.

P-058 adds the shared desktop relay client and approval queue. Relay connection setup remains an
explicit per-device UI step because it requires a private access token and a target device choice.
The loopback acceptance harness is `scripts/testing/fake_relay.py`.

P-066 bundles the [voice studio](../voice_studio/README.md) into Stream Extend and uses the existing
Automation / Control Python environment. Prompt assembly, render jobs, PCM checks, revision saves,
approval validation and manifest export are local code paths. Model/voice installation, human
prompt/audio approval, output routing, Soundbox file import, hotkey assignment and audible recording
acceptance are **not automated**. It adds no Compose service or cloud worker.

## Commands

```bash
make up-with-automation          # core stack + n8n (automation profile)
./scripts/setup/n8n_import.sh    # import the committed reference workflows
```

## Verify

```bash
make test-obs
```

Runs `scripts/setup/test_obs_websocket.py` — verifies OBS WebSocket connectivity, so you know
the automation side has something to talk to.

## What the import script loads

Reference workflows are committed at `modules/automation-control/n8n/workflows/` as exported
JSON. `on-stream-start.json` is present today.

## Not automated

- **OBS WebSocket itself.** Enabling and securing it is a manual step inside OBS — see
  [manual.md](manual.md).
- **Credentials inside n8n.** Each workflow's connections (social accounts, Postgres, MinIO) are
  entered in the n8n UI; the import brings the graph, not the secrets.
- **Advanced Scene Switcher.** A separate OBS plugin, configured in OBS.

P-056 Stream Extend now bundles the fixed production owner/workers and private default
policies. The optional Minecraft dependency control performs a pinned `npm ci --ignore-scripts`
without starting a client. It does not provision a world, grant game permission, install/bind
a licensed rig, authorize VTube/Twitch or pass physical/performance acceptance. See
[manual.md](manual.md#stream-autopilot-production-controls-p-056).
