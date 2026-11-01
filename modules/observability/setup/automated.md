# observability — automated setup

**Labels:** `Stream` · Manual path: [manual.md](manual.md)

Fully automated. All five services are in the default Compose profile.

After selecting this module, either Extend app can also start exactly these five bundled local
services from **Module setup** and retain their Compose health states. The generated Grafana
password is stored in the OS credential manager and can be copied from the completed initialization
job; login acceptance remains manual.

## One command

```bash
make up
```

Starts `prometheus`, `source-health-exporter`, `loki`, `promtail`, and `grafana`.

## Verify

| Service | URL | Note |
|---|---|---|
| Prometheus | http://localhost:9090 | targets should be Up |
| Grafana | http://localhost:3000 | default `admin/admin` — **change immediately** |
| Loki | via Grafana Explore | Promtail ships container stdout/stderr by default |

```bash
make healthcheck
```

## What is provisioned

Grafana datasources and dashboards are provisioned from committed config, so a fresh `make up`
comes with dashboards already loaded — no manual import.

## Not automated

- **Changing the Grafana admin password.** Default `admin/admin` until you change it.
- **Alert routing.** Alert rules exist as config; destinations (email, Discord, PagerDuty) are
  yours to fill in.
- **GPU metrics.** The NVIDIA DCGM exporter is optional and not in the default profile.
