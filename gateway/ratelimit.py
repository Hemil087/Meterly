import time
from pathlib import Path

from common.redis_client import get_redis

_LUA = (Path(__file__).parent / "lua" / "token_bucket.lua").read_text()


async def check_rate_limit(
    subscription_id: int,
    requests: int,
    window_seconds: int,
    burst: int | None,
) -> tuple[bool, int, int]:
    """
    Returns (allowed, remaining_tokens, retry_after_ms).
    Atomic — the Lua script runs as a single Redis transaction.
    """
    redis = await get_redis()
    now_ms = int(time.time() * 1000)

    result = await redis.eval(
        _LUA,
        1,                       # number of KEYS
        f"rl:{subscription_id}", # KEYS[1]
        requests,                # ARGV[1]
        window_seconds,          # ARGV[2]
        burst or 0,              # ARGV[3]
        now_ms,                  # ARGV[4]
    )

    return bool(result[0]), int(result[1]), int(result[2])