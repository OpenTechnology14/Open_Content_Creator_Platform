# infrastructure — manual setup

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

Docker Compose plus Tailscale, so the workstation and a DigitalOcean droplet are one private
network with no public ports.

## Compose topology

Everything that is not a desktop app runs in Compose. Default profile: `postgres`, `redis`,
`minio`, `fastapi`, `prometheus`, `source-health-exporter`, `loki`, `promtail`, `grafana`.
Two opt-in profiles: `graphics` (NodeCG) and `automation` (n8n).

```bash
make up                  # default profile
make up-with-graphics    # + NodeCG
make up-with-automation  # + n8n
```

## Tailscale (hybrid networking)

Connect your workstation and your droplet privately so services discover each other by hostname.

**Install**

- Workstation: https://tailscale.com/download
- Droplet:
  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up --authkey=tskey-xxx
  ```

Auth keys are **ephemeral — regenerate per node**, and never commit one.

**Use** — set tailnet hostnames in `.env`:

```
POSTGRES_HOST=hcp-db.tailnet.ts.net
REDIS_HOST=hcp-redis.tailnet.ts.net
MINIO_ENDPOINT=hcp-minio.tailnet.ts.net:9000
```

Local FastAPI now reaches a DO-hosted Postgres without Postgres being publicly exposed.

**Tailscale Funnel (optional)** — if exactly one thing must be public (e.g. an n8n webhook
endpoint) without managing TLS or a reverse proxy. Document any use in
`modules/infrastructure/tailscale/funnel.md`.

## DigitalOcean overlay

```bash
docker compose -f docker-compose.yml -f docker-compose.digitalocean.yml up -d
```

Droplet sizing: 4 vCPU / 8 GB RAM minimum for FastAPI plus the observability stack. Add a GPU
droplet only when implementing burst rendering.

## Backups

```bash
make backup    # scripts/maintenance/backup.sh
```

## Kubernetes

**Out of scope.** `CLAUDE.md` §10 forbids introducing Kubernetes, service mesh, or distributed
workers before this module is complete, and `docs/architecture/k8s-decision.md` records the
reasoning. Do not add it without a documented deviation.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `docker compose config -q` on **both** the base file and the DO overlay
- `make healthcheck`

**Manual — nothing automates these:**

- [ ] `tailscale status` lists both nodes
- [ ] A service on the droplet is reachable from the workstation by tailnet hostname, and **not**
  reachable from the public internet

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

- **Services cannot resolve each other** — they are on different Compose networks; check `hcp-net`.
- **Tailnet hostname does not resolve** — MagicDNS is off, or the node is not `tailscale up`.
- **Compose var unset warnings** — every `${VAR}` `docker-compose.yml` references has a matching
  entry in `.env.example` (verified 2026-09-01, `tests/infrastructure/test_compose_env.py`); a
  warning means your local `.env` is missing that value, not that `.env.example` is incomplete —
  copy the missing line across and fill in a real value.
