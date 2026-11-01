# NodeCG — Broadcast Graphics Engine

Runs the NodeCG server and hosts overlay bundles consumed by OBS as Browser Sources.

## Quick start

```bash
# Docker (recommended — matches rest of platform)
docker compose --profile graphics up -d nodecg

# Or npm
cd modules/broadcast-graphics/nodecg
npm install --global nodecg-cli
nodecg setup
nodecg start
```

Dashboard: http://localhost:9091

## Bundles

| Bundle | Purpose | Status |
|--------|---------|--------|
| `hcp-starter` | Scoreboard, lower-third, sponsor rotator | scaffolded |
| `hcp-alerts` | Donation / follow / subscription alerts via webhook | scaffolded |

## Adding a new bundle

```bash
cd bundles/
mkdir my-bundle && cd my-bundle
npm init -y
mkdir -p extension dashboard graphics
```

Layout:
```
bundles/my-bundle/
├── package.json
├── extension/        # Node-side logic (replicants, API calls)
│   └── index.js
├── dashboard/        # Operator UI panels
│   └── panels/
└── graphics/         # HTML/CSS/JS consumed by OBS Browser Source
    └── overlay.html
```

Each bundle is an independent npm project. NodeCG auto-discovers bundles in
this directory on startup.

## Redis bridge

`hcp-starter/extension/redis-bridge.js` subscribes to Redis pub/sub channels
and writes incoming data into NodeCG replicants. This lets FastAPI push
real-time updates to overlays without NodeCG needing to poll.

Channels consumed — verified against `redis-bridge.js`'s actual subscribe pattern
(`pSubscribe('overlay.*', ...)`) and `extension/index.js`'s replicant keys, 2026-09-01
(the previous list here didn't match either — wrong casing and an extra `.update` suffix that
would have made the bridge silently drop every message):
- `overlay.scoreboard`
- `overlay.lowerThird` (camelCase — matches the replicant key exactly; `overlay.lowerthird` will
  not match)
- `overlay.sponsor`

FastAPI's `PUT /overlays/{name}` publishes to `overlay.{name}` with no suffix — `name` here must
be exactly the replicant key.

## OBS integration

Add a Browser Source per graphic in OBS:
- URL: `http://localhost:9091/bundles/<bundle>/graphics/<file>.html`
- Width: 1920, Height: 1080
- Enable "Shutdown source when not visible"

See [`broadcast-graphics`](../setup/manual.md) for full setup.

## Why NodeCG

| Option | Verdict |
|---|---|
| **NodeCG** | Battle-tested in esports broadcasting; bundle architecture; operator dashboards built in. **Recommended.** |
| **CasparCG** | Broadcast TV-grade, heavyweight, separate template language. Overkill for most creators. |
| **Custom HTML + WebSocket** | Fine for a one-off graphic; does not scale to a graphics package. |

The deciding factor is the operator dashboard. A graphic you cannot drive live is a video file,
and every alternative here makes you build that dashboard yourself.

## Port

NodeCG's own default is **9090**, which collides with Prometheus. This repo runs it on **9091** —
the Compose stanza handles it, but a manual `nodecg setup` install will default back and silently
fight the observability stack.

