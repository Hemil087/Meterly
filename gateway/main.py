import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response

from common.db import close_pool, get_pool
from common.redis_client import get_redis, close_redis
from gateway.routing import resolve_route
from gateway.checks import RequestContext, default_pipeline
from gateway.metering import UsageEvent, record, start_flush_task, stop_flush_task


# One shared client for all upstream calls: keeps a connection pool,
# so repeat requests to the same upstream reuse warm TCP/TLS connections
# instead of paying a fresh handshake per request.
_http: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http
    await get_pool()   # warm up pool on startup
    await get_redis()
    await start_flush_task()
    _http = httpx.AsyncClient(
        timeout=10.0,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    )
    yield
    await _http.aclose()
    await close_pool()  # clean shutdown
    await close_redis()
    await stop_flush_task()


app = FastAPI(lifespan=lifespan)

_pipeline = default_pipeline()


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

    # ── 1-2. Resolve route (provider + api) — Redis-cached ───────────────
    route = await resolve_route(provider_slug, api_slug)
    if not route:
        # Unknown provider — nothing to attribute the event to; not metered.
        raise HTTPException(status_code=404, detail="Provider not found")
    if route["provider_status"] != "active":
        raise HTTPException(status_code=403, detail="Provider suspended")
    if route["api_id"] is None:
        raise HTTPException(status_code=404, detail="API not found")
    if route["api_status"] != "active":
        raise HTTPException(status_code=403, detail="API not active")

    # ── 3-5. Enforcement pipeline: auth → rate limit → quota ─────────────
    ctx = RequestContext(
        provider_id=route["provider_id"],
        api_id=route["api_id"],
        method=request.method,
        path=f"/{path}",
        raw_key=request.headers.get("X-API-Key"),
    )
    verdict = await _pipeline.run(ctx)

    if not verdict.allowed:
        return await _reject(
            outcome=verdict.outcome,
            status_code=verdict.http_status,
            detail=verdict.detail,
            provider_id=ctx.provider_id, api_id=ctx.api_id,
            consumer_id=ctx.bundle["consumer_id"] if ctx.bundle else None,
            subscription_id=ctx.bundle["subscription_id"] if ctx.bundle else None,
            method=ctx.method, path=ctx.path, t_start=t_start,
            headers=verdict.headers,
        )

    bundle = ctx.bundle

    # ── 6. Forward ───────────────────────────────────────────────────────
    upstream_url = f"{route['upstream_url'].rstrip('/')}/{path}"

    forward_headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }
    # Inject the provider's upstream credential — consumers never see it
    if route["shared_secret"]:
        forward_headers["Authorization"] = f"Bearer {route['shared_secret'].strip()}"

    body = await request.body()

    try:
        upstream = await _http.request(
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
    response_headers["X-RateLimit-Remaining"] = str(ctx.rl_remaining)
    response_headers["X-Quota-Limit"]         = str(bundle["monthly_quota"])
    response_headers["X-Quota-Used"]          = str(ctx.quota_used)

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )