from controlplane.repositories.interfaces import ConsumerRepository
from controlplane.services.audit import AuditWriter
from controlplane.services.errors import NotFoundError


class ConsumerService:
    def __init__(self, repo: ConsumerRepository, audit: AuditWriter) -> None:
        self._repo = repo
        self._audit = audit

    async def onboard(self, provider_id: int, actor: str, name: str,
                      email: str, contact_name: str | None) -> dict:
        consumer = await self._repo.insert(provider_id, name, email, contact_name)
        await self._audit.log(provider_id, actor, "consumer.onboarded",
                              "consumer", consumer["id"], {"name": name})
        return consumer

    async def suspend(self, provider_id: int, actor: str, consumer_id: int) -> None:
        consumer = await self._get_owned(provider_id, consumer_id)
        await self._repo.set_status(consumer_id, "suspended")
        # D-021: no cache invalidation — suspension propagates via
        # AUTH_BUNDLE_TTL. Revoke keys if immediacy is required.
        await self._audit.log(provider_id, actor, "consumer.suspended",
                              "consumer", consumer_id, {"name": consumer["name"]})

    async def reactivate(self, provider_id: int, actor: str, consumer_id: int) -> None:
        consumer = await self._get_owned(provider_id, consumer_id)
        await self._repo.set_status(consumer_id, "active")
        await self._audit.log(provider_id, actor, "consumer.reactivated",
                              "consumer", consumer_id, {"name": consumer["name"]})

    async def _get_owned(self, provider_id: int, consumer_id: int) -> dict:
        consumer = await self._repo.get(consumer_id)
        if not consumer or consumer["provider_id"] != provider_id:
            raise NotFoundError("Consumer not found")
        return consumer