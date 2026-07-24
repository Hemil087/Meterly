import asyncpg
from controlplane.repositories.interfaces import ApiRepository


class PostgresApiRepository(ApiRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, api_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, provider_id, name, slug, upstream_url, status "
            "FROM apis WHERE id = $1",
            api_id,
        )
        return dict(row) if row else None

    async def list_by_provider(self, provider_id: int) -> list[dict]:
        rows = await self._pool.fetch(
            "SELECT id, provider_id, name, slug, upstream_url, status "
            "FROM apis WHERE provider_id = $1",
            provider_id,
        )
        return [dict(r) for r in rows]

    async def insert(self, provider_id: int, name: str, slug: str,
                     upstream_url: str) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO apis (provider_id, name, slug, upstream_url, status)
            VALUES ($1, $2, $3, $4, 'active')
            RETURNING id, provider_id, name, slug, upstream_url, status
            """,
            provider_id, name, slug, upstream_url,
        )
        return dict(row)

    async def set_status(self, api_id: int, status: str) -> None:
        await self._pool.execute(
            "UPDATE apis SET status = $1 WHERE id = $2",
            status, api_id,
        )