# broadcast-graphics — manual setup

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

NodeCG lower-thirds and scoreboards driven from live data, reusable across events.

## Prerequisites

Redis and FastAPI must be running — overlays are reactive and need a data source.

```bash
make up
curl http://localhost:8000/health   # expect 200
```

See [backend-api setup](../../backend-api/setup/manual.md).

## Install NodeCG

Lives at `modules/broadcast-graphics/nodecg/`.

```bash
# Option A — npm
npm install --global nodecg-cli
cd modules/broadcast-graphics/nodecg
nodecg setup

# Option B — docker, recommended for parity with the rest of the platform
docker compose --profile graphics up -d nodecg
```

Dashboard at http://localhost:9091 (**not** 9090 — that is Prometheus).

## Bundle structure

Bundles are folders under `nodecg/bundles/`, each its own npm project:

```
bundles/<bundle-name>/
├── package.json
├── extension/        # Node-side logic (replicants, API calls)
│   └── index.js
├── dashboard/        # operator UI
└── graphics/         # what OBS shows
```

A starter bundle ships at `nodecg/bundles/hcp-starter/` with a scoreboard, a lower-third, a
sponsor rotator, and an operator panel for each. A second bundle, `hcp-alerts/`, is present.

```bash
cd modules/broadcast-graphics/nodecg/bundles/hcp-starter
npm install
```

## Bridge to FastAPI

`hcp-starter/extension/redis-bridge.js` subscribes to Redis pub/sub so overlay state changes
published by FastAPI reach the graphics without polling.

## Add to OBS

For each graphic, add a **Browser Source** in OBS pointing at the NodeCG graphics URL
(`http://localhost:9091/bundles/hcp-starter/graphics/<name>.html`). Set width/height to match
your canvas, and tick **Shutdown source when not visible** to save GPU when the scene is inactive.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `make up-with-graphics` — NodeCG on 9091

**Manual — nothing automates these:**

- [ ] NodeCG dashboard lists `hcp-starter`
- [ ] Changing a value in an operator panel updates the graphic live
- [ ] The graphic renders in OBS as a Browser Source with a transparent background

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

- **Dashboard 404s on the bundle** — `npm install` was not run inside the bundle directory.
- **Graphic renders but never updates** — the Redis bridge is not connected; check `REDIS_URL` is
  set on the `nodecg` container (`docker-compose.yml`) and that the channel name you're publishing
  to matches a replicant key exactly — see `nodecg/README.md`'s Redis bridge section.
- **Port conflict on startup** — something else holds 9091, or you installed outside Compose and
  NodeCG defaulted back to 9090 against Prometheus.
