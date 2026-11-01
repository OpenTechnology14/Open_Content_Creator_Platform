"""
Metrics persistence router.

Accepts metric batches from desktop apps and stores them in Postgres.
Enables Grafana dashboards accessible from any device.
Requires Pro tier ($12/mo) or higher.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional

from ..middleware.auth import require_pro, TokenData
from ..database import TenantConnection

router = APIRouter()

# Second, defense-in-depth layer under the global BodySizeLimitMiddleware —
# bounds batch *shape* (item count), not just total request bytes.
MAX_METRICS_PER_BATCH = 500


class MetricPoint(BaseModel):
    name: str = Field(max_length=256)
    value: float
    timestamp: int  # Unix epoch seconds
    labels: Optional[dict] = None


class MetricBatch(BaseModel):
    metrics: List[MetricPoint] = Field(max_length=MAX_METRICS_PER_BATCH)


class MetricQuery(BaseModel):
    name: str
    start: int  # Unix epoch
    end: int
    step: int = 60  # Resolution in seconds


@router.post("/push")
async def push_metrics(
    batch: MetricBatch,
    tenant: TokenData = Depends(require_pro),
):
    """Push a batch of metrics from the desktop app.

    The desktop app collects metrics locally (Prometheus scrape)
    and forwards a subset to the cloud for persistence.
    This enables Grafana dashboards accessible from mobile / any device.
    """
    if not batch.metrics:
        return {"stored": 0}

    async with TenantConnection(tenant.tenant_id) as conn:
        # Batch insert
        values = [
            (
                tenant.tenant_id,
                m.name,
                m.value,
                m.timestamp,
                str(m.labels or {}),
            )
            for m in batch.metrics
        ]

        await conn.executemany(
            """
            INSERT INTO metrics (tenant_id, name, value, timestamp, labels)
            VALUES ($1, $2, $3, to_timestamp($4), $5)
            ON CONFLICT DO NOTHING
            """,
            values,
        )

    return {"stored": len(batch.metrics)}


@router.post("/query")
async def query_metrics(
    query: MetricQuery,
    tenant: TokenData = Depends(require_pro),
):
    """Query stored metrics for Grafana.

    This endpoint is compatible with Grafana's JSON datasource plugin,
    allowing cloud Grafana to read metrics stored by the relay.
    """
    async with TenantConnection(tenant.tenant_id) as conn:
        rows = await conn.fetch(
            """
            SELECT name, value, extract(epoch from timestamp)::bigint as ts, labels
            FROM metrics
            WHERE tenant_id = $1
              AND name = $2
              AND timestamp >= to_timestamp($3)
              AND timestamp <= to_timestamp($4)
            ORDER BY timestamp ASC
            """,
            tenant.tenant_id, query.name, query.start, query.end,
        )

    return {
        "target": query.name,
        "datapoints": [
            [row["value"], row["ts"] * 1000]  # Grafana expects ms timestamps
            for row in rows
        ],
    }


@router.get("/names")
async def list_metric_names(
    tenant: TokenData = Depends(require_pro),
):
    """List all metric names for this tenant (for Grafana autocomplete)."""
    async with TenantConnection(tenant.tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT name FROM metrics WHERE tenant_id = $1 ORDER BY name",
            tenant.tenant_id,
        )

    return [row["name"] for row in rows]
