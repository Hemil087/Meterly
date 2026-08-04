import hashlib
import json

from common.db import get_pool
from common.redis_client import get_redis
from common.auth_cache import AUTH_BUNDLE_TTL, bundle_key


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def resolve_auth(raw_key: str, api_id: int) -> dict | None:
    """
    Returns the full auth bundle the gateway needs for enforcement,
    or None if the key is invalid / not subscribed to this API.

    Flow: Redis hit → return immediately
          Redis miss → Postgres query → cache result → return

    Cached per (key, api): the bundle carries THIS api's subscription,
    quota, and rate limits. Invalidation lives in common.auth_cache
    and is triggered by the control plane on revoke / plan change.
    """
    key_hash = hash_key(raw_key)
    redis = await get_redis()

    # ── 1. Redis cache lookup ────────────────────────────────────────────
    cached = await redis.get(bundle_key(key_hash, api_id))
    if cached:
        return json.loads(cached)

    # ── 2. Postgres fallback ─────────────────────────────────────────────
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT
            ak.consumer_id,
            s.id                  AS subscription_id,
            s.api_id,
            a.provider_id,
            p.monthly_quota,
            p.overage_allowed,
            rl.requests           AS rl_requests,
            rl.window_seconds     AS rl_window_seconds,
            rl.burst              AS rl_burst,
            rl.algorithm          AS rl_algorithm
        FROM api_keys ak
        JOIN consumers        c  ON c.id  = ak.consumer_id
        JOIN subscriptions    s  ON s.consumer_id = ak.consumer_id
                                AND s.api_id      = $2
                                AND s.status      = 'active'
        JOIN plans            p  ON p.id  = s.plan_id
        JOIN rate_limit_policies rl ON rl.id = p.rate_limit_policy_id
        JOIN apis             a  ON a.id  = s.api_id
        WHERE ak.key_hash = $1
          AND ak.status   = 'active'
          AND (ak.expires_at IS NULL OR ak.expires_at > now())
          AND c.status    = 'active'
        """,
        key_hash,
        api_id,
    )

    if not row:
        return None

    bundle = dict(row)

    # ── 3. Cache for next request ────────────────────────────────────────
    await redis.set(bundle_key(key_hash, api_id), json.dumps(bundle), ex=AUTH_BUNDLE_TTL)

    return bundle