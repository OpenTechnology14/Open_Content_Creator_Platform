# broadcast-graphics — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

Automated via a Compose profile — NodeCG is not in the default profile, so it needs its own target.

After selecting this module, either Extend app can also start the bundled local storage, API and
`nodecg` services from **Module setup**. The app resolves those dependencies from the catalog and
does not start unrelated services. Browser-source configuration and live overlay acceptance stay
with the operator.

## One command

```bash
make up-with-graphics
```

Equivalent to `docker compose --profile graphics up -d` — core stack plus `nodecg`.

## Verify

NodeCG dashboard at http://localhost:9091.

> **Port note:** NodeCG's own default is 9090, which collides with Prometheus. This repo runs it
> on **9091**; the Compose stanza already handles it. If you install NodeCG outside Compose you
> must set the port yourself.

## Not automated

- **Bundle dependencies.** Each bundle under `nodecg/bundles/` is its own npm project; `npm install`
  per bundle is manual.
- **Adding graphics to OBS.** Creating the Browser Sources is a manual OBS step — see
  [manual.md](manual.md).
- **Bundle content.** The shipped `hcp-starter` bundle has scoreboard, lower-third, and sponsor
  graphics plus operator panels. Anything beyond that you author yourself.

## Overlay control from anywhere (the app path)

Stream Extend is specified to drive these overlays remotely — update a scoreboard or fire a
lower-third from a phone, without an operator at the desk.

**Specified, not shipped** — `CLAUDE.md` §11 has this module at `scaffolded`.

The mechanism it would use already exists: replicants sync over WebSocket, and the FastAPI bridge
in `hcp-starter/extension/redis-bridge.js` lets anything publishing to Redis mutate overlay state.
A script hitting FastAPI today gets remote control without the app.
