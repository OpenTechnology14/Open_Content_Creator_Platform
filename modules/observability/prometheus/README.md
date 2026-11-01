# prometheus

Scrape and alert configuration. Setup steps live in [`../setup/manual.md`](../setup/manual.md);
`make up` brings Prometheus and Alertmanager online.

| File | Purpose |
|---|---|
| `prometheus.yml` | Scrape targets |
| `alertmanager.yml` | Notification routing |
| `rules/host.rules.yml` | CPU > 90% for 5 min, disk > 85%, RAM > 90% |
| `rules/services.rules.yml` | Service down, FastAPI p99 latency > 500 ms |
| `rules/source-health.rules.yml` | Source/bus health from `source-health-exporter` |

## Alert rules

Committed rule files cover host, service, and source health. Two rule sets described in the
original plan are **not on disk**: `streaming.rules.yml` (OBS dropped frames > 5% for 1 min) and
`ai.rules.yml` (ComfyUI fps below threshold, agent service silent > 5 min). Write them when the
modules they watch are past `scaffolded` — an alert on a service that never runs is noise.

## Notification channels

Configured in `alertmanager.yml`:

| Channel | Use |
|---|---|
| Discord webhook | Immediate, but noisy — reserve for genuinely urgent rules |
| Email | Non-urgent |
| Pushover / ntfy.sh / Slack | Optional |

Route by severity, not by rule. Every alert going to the same immediate channel trains you to
ignore all of them, which is worse than having no alerting.

## Port note

Prometheus uses **9090**, which is also NodeCG's default. This repo moves NodeCG to 9091 — see
[`broadcast-graphics/nodecg/README.md`](../../broadcast-graphics/nodecg/README.md).
