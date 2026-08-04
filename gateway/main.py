import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from common.db import close_pool, get_pool
from common.redis_client import get_redis, close_redis
from gateway.auth import resolve_auth
from gateway.ratelimit import check_rate_limit
from gateway.quota import check_and_increment_quota
from gateway.metering import UsageEvent, record, start_flush_task, stop_flush_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()   # warm up pool on startup
    await get_redis()
    await start_flush_task()
    yield
    await close_pool()  # clean shutdown
    await close_redis()
    await stop_flush_task()


app = FastAPI(lifespan=lifespan)


# Headers that must not be forwarded (hop-by-hop)
_HOP_BY_HOP = {
    "connection", "keep-alive", "transfer-encoding",
    "te", "trailer", "upgrade", "proxy-authorization",
    "proxy-authenticate", "host",
}


async def _reject(
    *,
    outcome: str,
    status_code: int,
    detail: str,
    provider_id: int,
    api_id: int,
    method: str,
    path: str,
    t_start: float,
    consumer_id: int | None = None,
    subscription_id: int | None = None,
    headers: dict | None = None,
) -> Response:
    """
    D-008: every blocked request is metered, not dropped.
    Records the event, then returns the error response.
    auth_failed events carry no consumer/subscription — identity was
    never established. provider/api are always known (resolved from URL).
    """
    await record(UsageEvent(
        occurred_at=datetime.now(timezone.utc),
        provider_id=provider_id,
        consumer_id=consumer_id,
        api_id=api_id,
        subscription_id=subscription_id,
        endpoint_id=None,
        method=method,
        path=path,
        status_code=status_code,
        outcome=outcome,
        latency_ms=int((time.monotonic() - t_start) * 1000),
        upstream_ms=0,
        request_bytes=None,
        response_bytes=None,
    ))
    response_headers = {"Content-Type": "application/json"}
    if headers:
        response_headers.update(headers)
    return Response(
        content=f'{{"detail":"{detail}"}}',
        status_code=status_code,
        headers=response_headers,
    )


@app.api_route(
    "/{provider_slug}/{api_slug}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def gateway(
    provider_slug: str,
    api_slug: str,
    path: str,
    request: Request,
) -> Response:
    t_start = time.monotonic()
    pool = await get_pool()

    # ── 1. Resolve provider ──────────────────────────────────────────────
    provider = await pool.fetchrow(
        "SELECT id, status, shared_secret FROM providers WHERE slug = $1",
        provider_slug,
    )
    if not provider:
        # Unknown provider — nothing to attribute the event to; not metered.
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider["status"] != "active":
        raise HTTPException(status_code=403, detail="Provider suspended")

    # ── 2. Resolve API ───────────────────────────────────────────────────
    api = await pool.fetchrow(
        "SELECT id, status, upstream_url FROM apis WHERE provider_id = $1 AND slug = $2",
        provider["id"],
        api_slug,
    )
    if not api:
        raise HTTPException(status_code=404, detail="API not found")
    if api["status"] != "active":
        raise HTTPException(status_code=403, detail="API not active")

    # ── 3. Key auth ──────────────────────────────────────────────────────
    raw_key = request.headers.get("X-API-Key")
    if not raw_key:
        return await _reject(
            outcome="auth_failed", status_code=401,
            detail="Missing X-API-Key header",
            provider_id=provider["id"], api_id=api["id"],
            method=request.method, path=f"/{path}", t_start=t_start,
        )

    bundle = await resolve_auth(raw_key, api["id"])
    if not bundle:
        return await _reject(
            outcome="auth_failed", status_code=401,
            detail="Invalid or inactive key",
            provider_id=provider["id"], api_id=api["id"],
            method=request.method, path=f"/{path}", t_start=t_start,
        )

    # ── 4. Rate limit ────────────────────────────────────────────────────
    allowed, remaining, retry_after_ms = await check_rate_limit(
        subscription_id=bundle["subscription_id"],
        requests=bundle["rl_requests"],
        window_seconds=bundle["rl_window_seconds"],
        burst=bundle["rl_burst"],
    )

    if not allowed:
        retry_after_secs = max(1, retry_after_ms // 1000)
        return await _reject(
            outcome="rate_limited", status_code=429,
            detail="Rate limit exceeded",
            provider_id=bundle["provider_id"], api_id=bundle["api_id"],
            consumer_id=bundle["consumer_id"],
            subscription_id=bundle["subscription_id"],
            method=request.method, path=f"/{path}", t_start=t_start,
            headers={
                "Retry-After": str(retry_after_secs),
                "X-RateLimit-Limit": str(bundle["rl_requests"]),
                "X-RateLimit-Remaining": "0",
            },
        )

    # ── 5. Quota ─────────────────────────────────────────────────────────
    quota_allowed, calls_used = await check_and_increment_quota(
        subscription_id=bundle["subscription_id"],
        monthly_quota=bundle["monthly_quota"],
        overage_allowed=bundle["overage_allowed"],
    )

    if not quota_allowed:
        return await _reject(
            outcome="quota_blocked", status_code=429,
            detail="Monthly quota exceeded",
            provider_id=bundle["provider_id"], api_id=bundle["api_id"],
            consumer_id=bundle["consumer_id"],
            subscription_id=bundle["subscription_id"],
            method=request.method, path=f"/{path}", t_start=t_start,
            headers={
                "X-Quota-Limit": str(bundle["monthly_quota"]),
                "X-Quota-Used": str(calls_used),
            },
        )

    # ── 6. Forward ───────────────────────────────────────────────────────
    upstream_url = f"{api['upstream_url'].rstrip('/')}/{path}"

    forward_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    # Inject the provider's upstream credential — consumers never see it
    if provider["shared_secret"]:
        forward_headers["Authorization"] = f"Bearer {provider['shared_secret'].strip()}"

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            upstream = await client.request(
                method=request.method,
                url=upstream_url,
                headers=forward_headers,
                content=body,
                params=dict(request.query_params),
            )
    except httpx.TimeoutException:
        return await _reject(
            outcome="upstream_error", status_code=504,
            detail="Upstream timed out",
            provider_id=bundle["provider_id"], api_id=bundle["api_id"],
            consumer_id=bundle["consumer_id"],
            subscription_id=bundle["subscription_id"],
            method=request.method, path=f"/{path}", t_start=t_start,
        )
    except httpx.RequestError:
        return await _reject(
            outcome="upstream_error", status_code=502,
            detail="Upstream unreachable",
            provider_id=bundle["provider_id"], api_id=bundle["api_id"],
            consumer_id=bundle["consumer_id"],
            subscription_id=bundle["subscription_id"],
            method=request.method, path=f"/{path}", t_start=t_start,
        )

    latency_ms = int((time.monotonic() - t_start) * 1000)
    upstream_ms = latency_ms  # simplified for now

    await record(UsageEvent(
        occurred_at=datetime.now(timezone.utc),
        provider_id=bundle["provider_id"],
        consumer_id=bundle["consumer_id"],
        api_id=bundle["api_id"],
        subscription_id=bundle["subscription_id"],
        endpoint_id=None,
        method=request.method,
        path=f"/{path}",
        status_code=upstream.status_code,
        outcome="forwarded",
        latency_ms=latency_ms,
        upstream_ms=upstream_ms,
        request_bytes=len(body),
        response_bytes=len(upstream.content),
    ))

    response_headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    response_headers["X-RateLimit-Limit"]     = str(bundle["rl_requests"])
    response_headers["X-RateLimit-Remaining"] = str(remaining)
    response_headers["X-Quota-Limit"]         = str(bundle["monthly_quota"])
    response_headers["X-Quota-Used"]          = str(calls_used)

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )