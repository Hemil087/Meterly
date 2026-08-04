import asyncpg
from controlplane.repositories.interfaces import ApiKeyRepository


class PostgresApiKeyRepository(ApiKeyRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def insert(self, consumer_id: int, key_hash: str,
                     key_prefix: str, expires_at=None) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO api_keys
                (consumer_id, key_hash, key_prefix, status, expires_at)
            VALUES ($1, $2, $3, 'active', $4)
            RETURNING id, key_prefix, status, expires_at, created_at
            """,
            consumer_id, key_hash, key_prefix, expires_at,
        )
        return dict(row)

    async def revoke(self, key_id: int) -> str | None:
        """
        Revokes the key and returns its key_hash (or None if no such key),
        so the caller can invalidate the gateway's auth-bundle cache.
        """
        row = await self._pool.fetchrow(
            "UPDATE api_keys SET status = 'revoked', revoked_at = now() "
            "WHERE id = $1 "
            "RETURNING key_hash",
            key_id,
        )
        return row["key_hash"] if row else None

    async def list_by_consumer(self, consumer_id: int) -> list[dict]:
        rows = await self._pool.fetch(
            "SELECT id, key_prefix, status, expires_at, created_at "
            "FROM api_keys WHERE consumer_id = $1 ORDER BY created_at DESC",
            consumer_id,
        )
        return [dict(r) for r in rows]