# observability — manual setup

**Labels:** `Stream` · Automated path: [automated.md](automated.md)

The single pane of glass: is every source, bus, and AI service actually alive before you go live?

## Prometheus

Lives at `modules/observability/prometheus/`. Config committed at `prometheus.yml`.

```bash
docker compose up -d prometheus
```

UI at http://localhost:9090. Scrapes:

- FastAPI `/metrics`
- MinIO metrics (if running the content path)
- Postgres exporter, Redis exporter
- Node exporter (host CPU/disk/network)
- Optional: NVIDIA DCGM exporter for GPU metrics

## source-health-exporter

The most complete single component in this module (~750 lines). Polls OBS sources, audio buses,
virtual cameras, NodeCG, VTube Studio, and TTS output; exposes Prometheus metrics on
`:9101/metrics` and a human-readable view on `:9101/debug`.

Config at `modules/observability/source-health-exporter/config.yml`.

## Loki + Promtail

```bash
docker compose up -d loki promtail
```

Promtail ships container stdout/stderr by default. Add structured-log parsers per module in
`modules/observability/loki/pipelines/`.

LogQL queries every operator should know (saved as Grafana Explore links in
`modules/observability/loki/queries.md`):

- All errors in the last hour
- FastAPI 5xx responses
- ComfyUI OOM events
- Agent service messages by persona

Retention: Loki defaults to 7 days locally. On DigitalOcean use S3-backed Loki for cheaper
longer retention.

## Grafana

```bash
docker compose up -d grafana
```

UI at http://localhost:3000 — default `admin/admin`, **change it immediately**.

Provisioned dashboards at `modules/observability/grafana/dashboards/`:

- `platform-overview.json` — host CPU/RAM/GPU, container health, key API latencies
- `streaming.json` — OBS stream stats, dropped frames, bitrate
- `ai-pipelines.json` — ComfyUI/DeepFaceLive fps, latency, VRAM
- `sports-cv.json` — golf tracer fps, detection rate

Datasources provisioned in `modules/observability/grafana/provisioning/datasources/`.

> Verify these dashboard files exist in your checkout before relying on them — `docs/AUDIT.md`
> warns that documentation in this repo can list assets that are not on disk.

## Verification

Two halves. Run the automated one first — it is cheap and catches the class of problem that
does not need this module installed at all.

**Automated — run these:**

- `make test`
- `make up` then `make healthcheck`
- Prometheus targets page — every scrape target Up

**Manual — nothing automates these:**

- [ ] Grafana renders `platform-overview` with live data, not empty panels
- [ ] A deliberate error appears in Loki within a few seconds
- [ ] The Grafana admin password is no longer `admin`

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

- **Prometheus target Down** — the service is on a different Compose network; check `hcp-net`.
- **Grafana dashboards empty** — datasource provisioning failed; check the Grafana container logs.
- **No logs in Loki** — Promtail cannot read the Docker socket; check its volume mount.
