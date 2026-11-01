# Loki Pipeline Configurations

Promtail pipeline stages for parsing structured logs from specific modules.

## How it works

Promtail ships container stdout/stderr to Loki by default. Pipeline stages
add structure: they extract fields, parse JSON, drop noise, and add labels
so LogQL queries are faster and cleaner.

## Files

| File | Module | Parses |
|------|--------|--------|
| `fastapi.yml` | backend-api | JSON access logs → method, path, status, duration |
| `comfyui.yml` | realtime-ai/comfyui | Workflow start/complete/error events |
| `agent.yml` | ai-agents | Persona, message type, token count |

## Adding a pipeline

1. Create a YAML file in this directory
2. Reference it in `promtail-config.yml` under the relevant job's `pipeline_stages`
3. Test with `promtail --dry-run --config.file=promtail-config.yml`

## Status

Scaffolded — add pipeline configs as modules mature beyond scaffold stage.
