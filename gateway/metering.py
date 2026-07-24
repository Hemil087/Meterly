import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from common.db import get_pool


@dataclass
class UsageEvent:
    occurred_at: datetime
    provider_id: int
    consumer_id: int
    api_id: int
    subscription_id: int
    endpoint_id: int | None
    method: str
    path: str
    status_code: int
    outcome: str          # forwarded | rate_limited | quota_blocked | auth_failed
    latency_ms: int
    upstream_ms: int
    request_bytes: int | None
    response_bytes: int | None


_queue: asyncio.Queue[UsageEvent] = asyncio.Queue()
_flush_task: asyncio.Task | None = None

BATCH_SIZE  = 100
FLUSH_EVERY = 2.0   # seconds


async def record(event: UsageEvent) -> None:
    """Fire-and-forget — caller never waits for DB write."""
    await _queue.put(event)


async def _flush_loop() -> None:
    """Background task: drain queue and INSERT in batches."""
    pool = await get_pool()

    while True:
        await asyncio.sleep(FLUSH_EVERY)
        batch: list[UsageEvent] = []

        while not _queue.empty() and len(batch) < BATCH_SIZE:
            batch.append(_queue.get_nowait())

        if not batch:
            continue

        try:
            await pool.executemany(
                """
                INSERT INTO usage_events (
                    occurred_at, provider_id, consumer_id, api_id,
                    subscription_id, endpoint_id,
                    method, path, status_code, outcome,
                    latency_ms, upstream_ms,
                    request_bytes, response_bytes
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6,
                    $7, $8, $9, $10,
                    $11, $12,
                    $13, $14
                )
                """,
                [
                    (
                        e.occurred_at, e.provider_id, e.consumer_id, e.api_id,
                        e.subscription_id, e.endpoint_id,
                        e.method, e.path, e.status_code, e.outcome,
                        e.latency_ms, e.upstream_ms,
                        e.request_bytes, e.response_bytes,
                    )
                    for e in batch
                ],
            )
        except Exception as ex:
            # Never crash the gateway over a metering write
            print(f"[metering] flush error: {ex}")


async def start_flush_task() -> None:
    global _flush_task
    _flush_task = asyncio.create_task(_flush_loop())


async def stop_flush_task() -> None:
    if _flush_task:
        _flush_task.cancel()