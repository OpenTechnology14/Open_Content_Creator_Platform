# hcp-starter (NodeCG bundle)

Starter broadcast bundle with three overlays: scoreboard, lower third,
sponsor rotator. Drive them either through the dashboard panels or
remotely through the FastAPI `/overlays/{name}` endpoint (which publishes
to Redis `overlay.<name>` and is picked up by the bridge in
`extension/redis-bridge.js`).

## Install

```bash
# from NodeCG root
cd bundles
git clone /path/to/hcp-starter   # or symlink during development
cd hcp-starter && npm install
cd ../..
nodecg start
```

NodeCG runs on `http://localhost:9090` by default. We expose it on **9091**
inside the docker-compose stack to avoid colliding with Prometheus.

## Endpoints

```http
PUT /overlays/scoreboard  { "name": "scoreboard", "payload": { "home": 1, "away": 0, "clock": "12:34" } }
PUT /overlays/lowerThird  { "name": "lowerThird", "payload": { "visible": true, "title": "Player", "subtitle": "Driver, 270y" } }
PUT /overlays/sponsor     { "name": "sponsor",    "payload": { "active": {"name": "...", "tag": "...", "logo": "..."} } }
```

Add the corresponding NodeCG graphic URL as an OBS Browser Source:

```
http://localhost:9091/bundles/hcp-starter/graphics/scoreboard.html
http://localhost:9091/bundles/hcp-starter/graphics/lower-third.html
http://localhost:9091/bundles/hcp-starter/graphics/sponsor.html
```

## Replicants

A **replicant** is a value that syncs across the extension, the dashboard, and the graphics over
WebSocket. Change it in the dashboard and the graphic updates instantly — no polling, no refresh.

| Replicant | Shape |
|---|---|
| `scoreboard` | `{ home: { name, score }, away: { name, score }, period }` |
| `lowerThird` | `{ visible, title, subtitle }` |
| `sponsor` | `{ currentIndex, sponsors: [...] }` |

Graphics subscribe; dashboard panels mutate. Never write to a replicant from the graphic side —
that is how two operators end up fighting over one value.

## Graphic recipes

### Sponsor rotator

1. Reads the `sponsor.sponsors` array from the replicant.
2. Crossfades through entries on a configurable interval (default 8 s).
3. The operator can pin a specific sponsor from the dashboard.
4. Each entry is `{ logo, name, link, impressions }`. The extension increments `impressions` and
   posts to FastAPI for analytics — see [`backend-api`](../../../../backend-api/setup/manual.md).

### Scoreboard

- Two team blocks: logo, name, score
- Period / clock display
- Dashboard with +1 / −1 score buttons and clock controls
- Optionally keyboard shortcuts on the dashboard for fast live operation

### Lower-third

- Animated slide-in / slide-out
- Bound to the `lowerThird.visible` boolean
- Dashboard: title and subtitle fields, show/hide toggle, and a "show for 5 s" button

## Animations

CSS animations plus GSAP (committed in this bundle) are the right tool. **Avoid heavy WebGL** for
ordinary lower-thirds — they must render at 60 fps inside OBS, and WebGL spikes CPU on the same
machine that is encoding your stream.

For 3D or particle work, render in Blender or After Effects → export a webm with alpha → use it as
a video overlay instead of a NodeCG graphic.

