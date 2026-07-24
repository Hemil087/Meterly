import asyncpg
from controlplane.repositories.interfaces import ConsumerRepository


class PostgresConsumerRepository(ConsumerRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, consumer_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, provider_id, name, email, contact_name, status, created_at "
            "FROM consumers WHERE id = $1",
            consumer_id,
        )
        return dict(row) if row else None

    async def list_by_provider(self, provider_id: int) -> list[dict]:
        rows = await self._pool.fetch(
            "SELECT id, provider_id, name, email, contact_name, status, created_at "
            "FROM consumers WHERE provider_id = $1 ORDER BY created_at DESC",
            provider_id,
        )
        return [dict(r) for r in rows]

    async def insert(self, provider_id: int, name: str, email: str,
                     contact_name: str | None) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO consumers (provider_id, name, email, contact_name, status)
            VALUES ($1, $2, $3, $4, 'active')
            RETURNING id, provider_id, name, email, contact_name, status, created_at
            """,
            provider_id, name, email, contact_name,
        )
        return dict(row)

    async def set_status(self, consumer_id: int, status: str) -> None:
        await self._pool.execute(
            "UPDATE consumers SET status = $1 WHERE id = $2",
            status, consumer_id,
        )