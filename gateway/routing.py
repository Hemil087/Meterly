import json

from common.db import get_pool
from common.redis_client import get_redis
from common.route_cache import ROUTE_TTL, route_key


async def resolve_route(provider_slug: str, api_slug: str) -> dict | None:
    """
    Resolves the URL path segments to a routing bundle:

        { provider_id, provider_status, shared_secret,
          api_id, api_status, upstream_url }

    api_id / api_status / upstream_url are None when the provider
    exists but the API slug doesn't (lets the caller 404 precisely).
    Returns None when the provider itself doesn't exist.

    Flow: Redis hit → return immediately
          Redis miss → ONE Postgres query (LEFT JOIN) → cache → return

    Status checks are the CALLER's job on every request — suspended
    providers and disabled APIs are cached too, so that a status flip
    (plus control-plane invalidation) is enforced immediately without
    per-request DB reads.
    """
    redis = await get_redis()

    # ── 1. Redis cache lookup ────────────────────────────────────────────
    cached = await redis.get(route_key(provider_slug, api_slug))
    if cached:
        return json.loads(cached)

    # ── 2. Postgres fallback: one LEFT JOIN instead of two queries ──────
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT
            p.id            AS provider_id,
            p.status        AS provider_status,
            p.shared_secret,
            a.id            AS api_id,
            a.status        AS api_status,
            a.upstream_url
        FROM providers p
        LEFT JOIN apis a ON a.provider_id = p.id AND a.slug = $2
        WHERE p.slug = $1
        """,
        provider_slug,
        api_slug,
    )

    if not row:
        return None  # unknown provider — never cached (no negative caching)

    bundle = dict(row)

    # ── 3. Cache only fully-resolved routes ──────────────────────────────
    # Provider-exists-but-api-missing is NOT cached: registering that API
    # a second later must work without any invalidation step.
    if bundle["api_id"] is not None:
        await redis.set(
            route_key(provider_slug, api_slug), json.dumps(bundle), ex=ROUTE_TTL
        )

    return bundle