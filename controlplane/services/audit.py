import json

import asyncpg


class AuditWriter:
    """
    Append-only writer for audit_log. D-015: entity_id is a polymorphic
    reference (no FK) so audit rows outlive the entities they describe.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def log(
        self,
        provider_id: int,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: int,
        detail: dict | None = None,
    ) -> None:
        await self._pool.execute(
            """
            INSERT INTO audit_log
                (provider_id, actor, action, entity_type, entity_id, detail, occurred_at)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, now())
            """,
            provider_id, actor, action, entity_type, entity_id,
            json.dumps(detail or {}),
        )