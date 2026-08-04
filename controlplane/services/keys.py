import hashlib
import secrets

import redis.asyncio as aioredis

from common.auth_cache import invalidate_key
from controlplane.repositories.interfaces import ApiKeyRepository
from controlplane.services.audit import AuditWriter
from controlplane.services.errors import NotFoundError


class KeyService:
    def __init__(self, repo: ApiKeyRepository, audit: AuditWriter,
                 redis: aioredis.Redis) -> None:
        self._repo = repo
        self._audit = audit
        self._redis = redis

    async def issue(self, provider_id: int, actor: str, consumer_id: int,
                    expires_at=None) -> dict:
        """
        Generates the raw key, stores only its hash, returns the raw key
        exactly once. Generation lives HERE, not in the HTTP layer —
        it is business logic, not request parsing.
        """
        raw_key = "mk_live_" + secrets.token_urlsafe(24)
        key_prefix = raw_key[:12]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        row = await self._repo.insert(consumer_id, key_hash, key_prefix, expires_at)
        await self._audit.log(provider_id, actor, "key.issued", "api_key",
                              row["id"], {"key_prefix": key_prefix})
        return {**row, "raw_key": raw_key}

    async def revoke(self, provider_id: int, actor: str, key_id: int) -> None:
        key_hash = await self._repo.revoke(key_id)
        if key_hash is None:
            raise NotFoundError("Key not found")
        # D-020: revocation takes effect NOW — drop every cached bundle.
        await invalidate_key(self._redis, key_hash)
        await self._audit.log(provider_id, actor, "key.revoked", "api_key", key_id)