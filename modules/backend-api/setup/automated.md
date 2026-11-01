# backend-api — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

Fully automated for the container path.

After selecting this module, either Extend app can also start the bundled local storage services
and `fastapi` from **Module setup**. The app resolves the dependency plan from the catalog and
starts only the compiled allowlist. Existing source-checkout projects are left untouched when the
app has not previously created their private local environment.

## One command

```bash
make up
```

Starts `fastapi` (default Compose profile) along with its dependencies — `redis` for pub/sub
fanout and `postgres` for persistence.

## Verify

```bash
curl http://localhost:8000/health   # expect 200
```

OpenAPI docs at http://localhost:8000/docs.

## Not automated

- **External auth handoff.** The app-owned local Compose path generates `HCP_API_KEY` privately;
  source-checkout and cloud deployments still require their own `.env` value. Provider clients
  must receive that key through their own credential flow before authenticated routes are usable.
- **Dev reload.** Use the manual uvicorn command when you want hot reload.

Starting the container and reaching its Compose health state does not prove every authenticated
route or downstream integration behaves correctly; use the module and acceptance suites too.
