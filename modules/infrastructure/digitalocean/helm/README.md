# Helm Charts (Deferred)

This directory will contain Helm charts for Kubernetes deployment when
the platform moves past Docker Compose.

## Status

**Explicitly deferred** until all four criteria from [`infrastructure`](../../setup/manual.md) are met:

1. More than one GPU worker with scheduling needs
2. Distinct services with different scaling requirements
3. A second person deploying without knowing the compose setup
4. Zero-downtime deployments required

See `docs/architecture/k8s-decision.md` for the decision log.

## Planned charts

| Chart | Services |
|-------|----------|
| `hcp-backend` | FastAPI, Redis, Postgres (or managed DB reference) |
| `hcp-observability` | Prometheus, Grafana, Loki, Alertmanager |
| `hcp-comfyui-worker` | Burst render worker (GPU node pool) |
| `hcp-n8n` | n8n automation |

## Target platform

- **DigitalOcean DOKS** (managed Kubernetes) — lowest operational overhead
- **Argo CD** for GitOps deployment (charts auto-deploy on push to main)
