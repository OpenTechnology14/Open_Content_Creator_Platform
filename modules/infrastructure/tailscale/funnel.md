# Tailscale + Funnel

We expose internal services to ourselves over Tailscale (private mesh). When
we want a *single, narrow* surface accessible to the public internet, we use
**Funnel** — never raw port-forwarding.

## Defaults

- All compose services bind to `127.0.0.1` only.
- Add `tailscale serve` for services we want on the tailnet (Grafana, n8n).
- Add `tailscale funnel` *only* for services that genuinely need public
  access (e.g. NodeCG Browser Source if you stream OBS from a different
  machine on a different network).

## Examples

```bash
# Expose Grafana to tailnet only:
sudo tailscale serve --bg --https=443 --set-path=/grafana http://127.0.0.1:3000

# Expose a single overlay graphic publicly via Funnel:
sudo tailscale funnel --bg --https=443 --set-path=/scoreboard \
    http://127.0.0.1:9091/bundles/hcp-starter/graphics/scoreboard.html
```

## Auth in front of Funneled services

Funnel does **not** add auth. Anything you funnel must either:

1. Already require an API key (FastAPI does — uses `x-api-key`).
2. Be intrinsically safe to make public (a static overlay HTML page is OK).
3. Sit behind an auth proxy (caddy + basic auth, oauth2-proxy, etc.).

Never funnel Grafana, n8n, MinIO, or NodeCG admin panels directly.
