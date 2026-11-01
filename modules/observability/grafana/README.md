# grafana

Dashboards and provisioning. Setup steps live in [`../setup/manual.md`](../setup/manual.md);
`make up` brings Grafana online at http://localhost:3000 with everything below already loaded.

## Provisioning

| Path | Purpose |
|---|---|
| `provisioning/datasources/datasources.yml` | Prometheus + Loki datasources |
| `provisioning/dashboards/dashboards.yml` | Dashboard auto-load |

Because both are provisioned, a fresh `make up` arrives with dashboards in place — there is no
manual import step, and hand-edits made in the Grafana UI are not persisted back here. Change the
JSON, not the UI, or the next container rebuild discards your work.

## Dashboards on disk

| File | Covers |
|---|---|
| `dashboards/platform-overview.json` | Host CPU/RAM/GPU, container health, key API latencies |
| `dashboards/streaming-health.json` | OBS stream stats, dropped frames, bitrate |
| `dashboards/source-health.json` | Sources, audio buses, virtual cameras, NodeCG, VTube Studio, TTS |

## Planned, not built

| File | Would cover |
|---|---|
| `ai-pipelines.json` | ComfyUI / DeepFaceLive fps, latency, VRAM |
| `sports-cv.json` | Golf tracer fps, detection rate |
| `slo.json` | Stream uptime, agent response time |
| `cost.json` | DO cost rollup — Spaces usage, droplet hours, GPU hours |
| `gpu.json` | VRAM and GPU utilisation across every GPU-using service |

Referenced in places as if they exist; they do not. Build each alongside the module it watches.

## Admin password

Default `admin/admin`. Change it on first login — the container does not force it, and this is
the one credential in the stack that ends up exposed most often.
