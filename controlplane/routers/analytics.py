from fastapi import APIRouter, Depends, Query
from common.db import get_pool

router = APIRouter(prefix="/providers/{provider_id}/analytics", tags=["analytics"])


async def get_pool_dep():
    return await get_pool()


@router.get("/overview", response_model=dict)
async def provider_overview(
    provider_id: int,
    days: int = Query(default=30, ge=1, le=90),
    pool=Depends(get_pool_dep),
):
    """Total calls by outcome for the provider over the last N days."""
    row = await pool.fetchrow(
        """
        SELECT
            COUNT(*)                                            AS total_calls,
            COUNT(*) FILTER (WHERE outcome = 'forwarded')      AS forwarded,
            COUNT(*) FILTER (WHERE outcome = 'rate_limited')   AS rate_limited,
            COUNT(*) FILTER (WHERE outcome = 'quota_blocked')  AS quota_blocked,
            COUNT(*) FILTER (WHERE outcome = 'auth_failed')    AS auth_failed,
            COUNT(*) FILTER (WHERE outcome = 'upstream_error') AS upstream_errors,
            ROUND(AVG(latency_ms), 2)                          AS avg_latency_ms
        FROM usage_events
        WHERE provider_id = $1
          AND occurred_at >= now() - ($2 || ' days')::interval
        """,
        provider_id, str(days),
    )
    return dict(row)


@router.get("/consumers", response_model=list[dict])
async def consumers_breakdown(
    provider_id: int,
    days: int = Query(default=30, ge=1, le=90),
    pool=Depends(get_pool_dep),
):
    """Per-consumer usage breakdown — the core upsell dashboard."""
    rows = await pool.fetch(
        """
        SELECT
            ue.consumer_id,
            c.name                                                  AS consumer_name,
            COUNT(*)                                                AS total_calls,
            COUNT(*) FILTER (WHERE ue.outcome = 'forwarded')       AS calls_forwarded,
            COUNT(*) FILTER (WHERE ue.outcome = 'rate_limited')    AS rate_limited,
            COUNT(*) FILTER (WHERE ue.outcome = 'quota_blocked')   AS quota_blocked,
            ROUND(AVG(ue.latency_ms), 2)                           AS avg_latency_ms
        FROM usage_events ue
        JOIN consumers c ON c.id = ue.consumer_id
        WHERE ue.provider_id = $1
          AND ue.occurred_at >= now() - ($2 || ' days')::interval
        GROUP BY ue.consumer_id, c.name
        ORDER BY total_calls DESC
        """,
        provider_id, str(days),
    )
    return [dict(r) for r in rows]


@router.get("/events", response_model=list[dict])
async def recent_events(
    provider_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    pool=Depends(get_pool_dep),
):
    """Most recent N raw events for the provider — live feed view."""
    rows = await pool.fetch(
        """
        SELECT
            occurred_at,
            consumer_id,
            api_id,
            method,
            path,
            status_code,
            outcome,
            latency_ms,
            upstream_ms
        FROM usage_events
        WHERE provider_id = $1
        ORDER BY occurred_at DESC
        LIMIT $2
        """,
        provider_id, limit,
    )
    return [dict(r) for r in rows]


@router.get("/consumers/{consumer_id}/hourly", response_model=list[dict])
async def consumer_hourly(
    provider_id: int,
    consumer_id: int,
    days: int = Query(default=7, ge=1, le=30),
    pool=Depends(get_pool_dep),
):
    """Hourly call volume for one consumer — sparkline data."""
    rows = await pool.fetch(
        """
        SELECT
            date_trunc('hour', occurred_at) AS hour,
            COUNT(*)                         AS total_calls,
            COUNT(*) FILTER (WHERE outcome = 'forwarded')    AS forwarded,
            COUNT(*) FILTER (WHERE outcome != 'forwarded')   AS blocked,
            ROUND(AVG(latency_ms), 2)        AS avg_latency_ms
        FROM usage_events
        WHERE provider_id  = $1
          AND consumer_id  = $2
          AND occurred_at >= now() - ($3 || ' days')::interval
        GROUP BY date_trunc('hour', occurred_at)
        ORDER BY hour ASC
        """,
        provider_id, consumer_id, str(days),
    )
    return [dict(r) for r in rows]