# backend-api — manual setup

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

FastAPI is the single ASGI app every overlay, mobile client, and automation reads from — one
contract instead of an integration per consumer.

## Prerequisites

Redis must be running; the WebSocket endpoint uses it for fanout.

```bash
docker compose up -d redis
```

## Run the app

Lives at `modules/backend-api/fastapi/`. Routers:

| Route | Purpose |
|---|---|
| `/health` | liveness + readiness |
| `/streams` | start/stop, metadata |
| `/overlays` | overlay state, consumed by NodeCG |
| `/ws` | WebSocket endpoint, Redis-backed fanout |
| `/events` | generic event ingestion |

```bash
# container
docker compose up -d fastapi

# or dev with reload
cd modules/backend-api/fastapi
uvicorn app.main:app --reload --port 8000
```

## Auth

- **Local dev:** API key in the `X-API-Key` header, value from `.env`.
- **Production:** the same API key, or Tailscale-network-only with no public exposure.
- **`/ws`:** same key, either the `X-API-Key` header (native clients) or a `?api_key=` query
  param (browser `WebSocket` clients can't set custom headers). A connection with neither closes
  immediately with WS code 1008. `/ws` fans out the same event/overlay data the REST writes
  require the key for — it isn't a lower-trust endpoint just because it's a socket.

Never expose this service publicly without one of the two. `docs/AUDIT.md` flags broad CORS and
weak fallback secrets as open P0 gates.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `make healthcheck` — `/health` returns 200

**Manual — nothing automates these:**

- [ ] `curl http://localhost:8000/docs` renders the OpenAPI UI
- [ ] A mutating route rejects a request with no `X-API-Key`
- [ ] A `/ws` connection with no key (and no `?api_key=`) is closed immediately, not left hanging
- [ ] A message published to Redis reaches an authenticated `/ws` subscriber — the fanout this
      module exists for

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

- **WebSocket connects then drops** — Redis is not reachable; check `REDIS_HOST` in `.env`.
- **401 on every route** — `X-API-Key` missing or does not match `.env`.
- **Port 8000 in use** — another ASGI app is running; change the port in the uvicorn command
  or the Compose stanza.
