import asyncpg
from controlplane.repositories.interfaces import ProviderRepository


class PostgresProviderRepository(ProviderRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, provider_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, name, slug, status, created_at FROM providers WHERE id = $1",
            provider_id,
        )
        return dict(row) if row else None

    async def get_by_slug(self, slug: str) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, name, slug, status, created_at FROM providers WHERE slug = $1",
            slug,
        )
        return dict(row) if row else None

    async def insert(self, name: str, slug: str, shared_secret: str) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO providers (name, slug, shared_secret, status)
            VALUES ($1, $2, $3, 'active')
            RETURNING id, name, slug, status, created_at
            """,
            name, slug, shared_secret,
        )
        return dict(row)

    async def set_status(self, provider_id: int, status: str) -> None:
        await self._pool.execute(
            "UPDATE providers SET status = $1 WHERE id = $2",
            status, provider_id,
        )