"""
Route cache: (provider_slug, api_slug) → routing bundle.

Same contract as common.auth_cache: the gateway WRITES entries on
cache miss (gateway/routing.py); the control plane INVALIDATES them
when the underlying rows change (provider suspended/reactivated,
upstream secret rotated, api disabled). One module owns the key
format so writer and invalidator can never drift.

Cache key: route:{provider_slug}:{api_slug}
The bundle carries both statuses, so suspended/disabled routes ARE
cached — the gateway re-checks status on every read, and control
plane invalidation makes status changes take effect immediately.
Only "row does not exist" is never cached (no negative caching),
which is why registering a new API needs no invalidation.
"""

import asyncpg
import redis.asyncio as aioredis

ROUTE_TTL = 300  # seconds


def route_key(provider_slug: str, api_slug: str) -> str:
    return f"route:{provider_slug}:{api_slug}"


async def invalidate_provider(redis: aioredis.Redis, provider_slug: str) -> None:
    """
    Drop every cached route under one provider (all its APIs).
    Used on suspend / reactivate / shared-secret rotation — all three
    change fields that live in every one of the provider's bundles.
    """
    to_delete = [k async for k in redis.scan_iter(match=f"route:{provider_slug}:*")]
    if to_delete:
        await redis.delete(*to_delete)


async def invalidate_api(
    redis: aioredis.Redis,
    pool: asyncpg.Pool,
    api_id: int,
) -> None:
    """
    Drop the single cached route for one API, resolving both slugs
    from the id (the control plane addresses APIs by id, the cache
    by slugs).
    """
    row = await pool.fetchrow(
        """
        SELECT p.slug AS provider_slug, a.slug AS api_slug
        FROM apis a JOIN providers p ON p.id = a.provider_id
        WHERE a.id = $1
        """,
        api_id,
    )
    if row:
        await redis.delete(route_key(row["provider_slug"], row["api_slug"]))