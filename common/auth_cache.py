"""
Auth-bundle cache: single source of truth for the key format.

The gateway WRITES this cache (gateway/auth.py); the control plane
INVALIDATES it when the underlying data changes (key revoked,
subscription cancelled, plan changed). Both sides import from here so
the key format can never drift between writer and invalidator.

Cache key: auth:{key_hash}:{api_id}
The bundle is per (key, API) — it contains the subscription, plan
quota, and rate limits for ONE api. Caching per key alone would serve
one API's bundle to requests for another.
"""

import asyncpg
import redis.asyncio as aioredis

AUTH_BUNDLE_TTL = 300  # seconds


def bundle_key(key_hash: str, api_id: int) -> str:
    return f"auth:{key_hash}:{api_id}"


async def invalidate_key(redis: aioredis.Redis, key_hash: str) -> None:
    """
    Drop every cached bundle for one API key (all APIs).
    Used on key revocation — the key must stop working NOW,
    not when the TTL expires.
    """
    to_delete = [k async for k in redis.scan_iter(match=f"auth:{key_hash}:*")]
    if to_delete:
        await redis.delete(*to_delete)


async def invalidate_consumer_api(
    redis: aioredis.Redis,
    pool: asyncpg.Pool,
    consumer_id: int,
    api_id: int,
) -> None:
    """
    Drop cached bundles for every key the consumer owns, for ONE api.
    Used when the (consumer, api) relationship changes: subscription
    cancelled or plan changed — the cached quota/rate-limit values
    are stale the moment the change commits.
    """
    rows = await pool.fetch(
        "SELECT key_hash FROM api_keys WHERE consumer_id = $1",
        consumer_id,
    )
    if rows:
        await redis.delete(*[bundle_key(r["key_hash"], api_id) for r in rows])