# Loki — Common LogQL Queries

Saved as Grafana Explore links. Copy these into the Explore panel (datasource: Loki).

## General

```logql
# All errors in the last hour
{job=~".+"} |= "error" | logfmt

# All warnings + errors
{job=~".+"} |~ "(?i)(error|warn|fatal|panic)"
```

## FastAPI

```logql
# 5xx responses
{container_name="hcp-fastapi"} | json | status_code >= 500

# Slow requests (> 500ms)
{container_name="hcp-fastapi"} | json | duration > 500

# Requests by endpoint
sum by (path) (rate({container_name="hcp-fastapi"} | json [5m]))
```

## ComfyUI / AI Pipelines

```logql
# OOM events
{job=~"comfyui.*"} |= "OutOfMemoryError"

# Workflow completion times
{job=~"comfyui.*"} |= "Prompt executed in"
```

## Agent Service

```logql
# Messages by persona
{container_name=~"hcp-agent.*"} | json | line_format "{{.persona}}: {{.message}}"

# Agent errors
{container_name=~"hcp-agent.*"} |= "error" | logfmt
```

## Infrastructure

```logql
# Container restarts
{job="docker"} |= "container restart"

# Postgres slow queries (if log_min_duration_statement is set)
{container_name="hcp-postgres"} |= "duration:" | logfmt | duration > 100
```

## OBS / Streaming

```logql
# Dropped frames events (from source-health exporter logs)
{container_name="hcp-source-health"} |= "dropped_frames"

# Stream state changes
{container_name="hcp-source-health"} |= "StreamState"
```
