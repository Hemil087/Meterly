from datetime import date
import asyncpg
from controlplane.repositories.interfaces import SubscriptionRepository


class PostgresSubscriptionRepository(SubscriptionRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, subscription_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, consumer_id, api_id, plan_id, status, cycle_anchor, created_at "
            "FROM subscriptions WHERE id = $1",
            subscription_id,
        )
        return dict(row) if row else None

    async def get_active(self, consumer_id: int, api_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, consumer_id, api_id, plan_id, status, cycle_anchor, created_at "
            "FROM subscriptions "
            "WHERE consumer_id = $1 AND api_id = $2 AND status = 'active'",
            consumer_id, api_id,
        )
        return dict(row) if row else None

    async def list_by_consumer(self, consumer_id: int) -> list[dict]:
        rows = await self._pool.fetch(
            "SELECT id, consumer_id, api_id, plan_id, status, cycle_anchor, created_at "
            "FROM subscriptions WHERE consumer_id = $1 ORDER BY created_at DESC",
            consumer_id,
        )
        return [dict(r) for r in rows]

    async def insert(self, consumer_id: int, api_id: int, plan_id: int) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO subscriptions
                (consumer_id, api_id, plan_id, status, cycle_anchor)
            VALUES ($1, $2, $3, 'active', $4)
            RETURNING id, consumer_id, api_id, plan_id, status, cycle_anchor, created_at
            """,
            consumer_id, api_id, plan_id, date.today(),
        )
        return dict(row)

    async def set_status(self, subscription_id: int, status: str) -> None:
        await self._pool.execute(
            "UPDATE subscriptions SET status = $1 WHERE id = $2",
            status, subscription_id,
        )