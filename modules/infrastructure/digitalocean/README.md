# DigitalOcean deployment

This folder is for DO-specific provisioning (Terraform, Helm, manifests). It
is intentionally sparse — we deploy via `scripts/deploy/deploy-do.sh` against
an already-provisioned droplet today.

## Recommended droplet

- **Region:** closest to your audience (latency for viewers, not for OBS).
- **Size:** start at `s-2vcpu-4gb`; upgrade when Loki + Grafana start
  saturating memory.
- **OS:** Ubuntu 22.04 LTS.
- **Networking:** join Tailscale immediately, disable password SSH, enable
  UFW with only Tailscale tagged traffic allowed by default.

## Managed services (cheaper than self-hosting)

- **Postgres:** DO Managed PostgreSQL 16. Use the SQL `postgresql://` DSN
  in `.env` as `DATABASE_URL`.
- **Redis:** DO Managed Redis (or run in-droplet for cost — Redis is light).
- **Spaces (S3):** for the `backups/`, `recordings/`, `models/` buckets when
  you outgrow on-droplet MinIO.

## Migration order (when you decide to go cloud)

1. Spin up the droplet, install docker, join tailnet.
2. Create Spaces buckets matching the local MinIO bucket names.
3. Provision Managed PG; run migrations from your laptop.
4. Copy `.env` over (use `scp` over tailnet).
5. `./scripts/deploy/deploy-do.sh` — this uses the `digitalocean.yml` overlay
   that swaps the embedded Postgres/Redis/MinIO for the managed equivalents.

## Future

Helm charts and Terraform live here after [`infrastructure`](../setup/manual.md) is complete. See
`docs/architecture/k8s-decision.md` for criteria.
