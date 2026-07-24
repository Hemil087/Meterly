import calendar
from datetime import date

from common.redis_client import get_redis


def _billing_period(cycle_anchor: int | None = None) -> tuple[str, str]:
    """
    Returns (period_start, period_end) as YYYY-MM-DD strings.
    For simplicity in v1: period = current calendar month.
    """
    today = date.today()
    start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = today.replace(day=last_day)
    return str(start), str(end)


def _quota_key(subscription_id: int, period_start: str) -> str:
    return f"quota:{subscription_id}:{period_start}"


async def check_and_increment_quota(
    subscription_id: int,
    monthly_quota: int,
    overage_allowed: bool,
) -> tuple[bool, int]:
    """
    Atomically increments the quota counter and checks against the limit.
    Returns (allowed, calls_used_after_increment).
    """
    period_start, _ = _billing_period()
    key = _quota_key(subscription_id, period_start)

    redis = await get_redis()

    # INCR is atomic — no race condition
    calls_used = await redis.incr(key)

    # Set expiry on first call of the month (INCR returns 1)
    if calls_used == 1:
        # Expire key after ~35 days so it self-cleans
        await redis.expire(key, 35 * 24 * 3600)

    if overage_allowed:
        return True, calls_used

    if calls_used > monthly_quota:
        return False, calls_used

    return True, calls_used