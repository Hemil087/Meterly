import asyncpg
import redis.asyncio as aioredis

from common.auth_cache import invalidate_consumer_api
from controlplane.repositories.interfaces import PlanRepository, SubscriptionRepository
from controlplane.services.audit import AuditWriter
from controlplane.services.errors import ConflictError, NotFoundError, ValidationError


class SubscriptionService:
    def __init__(self, sub_repo: SubscriptionRepository, plan_repo: PlanRepository,
                 audit: AuditWriter, redis: aioredis.Redis, pool: asyncpg.Pool) -> None:
        self._subs = sub_repo
        self._plans = plan_repo
        self._audit = audit
        self._redis = redis
        self._pool = pool

    async def subscribe(self, provider_id: int, actor: str, consumer_id: int,
                        api_id: int, plan_id: int) -> dict:
        plan = await self._plans.get(plan_id)
        if not plan or plan["api_id"] != api_id:
            raise ValidationError("Plan does not belong to this API")

        if await self._subs.get_active(consumer_id, api_id):
            raise ConflictError("Active subscription already exists")

        # No invalidation on subscribe: negative auth results are never
        # cached, so there is no stale "not subscribed" entry to purge.
        sub = await self._subs.insert(consumer_id, api_id, plan_id)
        await self._audit.log(provider_id, actor, "subscription.created",
                              "subscription", sub["id"],
                              {"consumer_id": consumer_id, "plan_id": plan_id})
        return sub

    async def cancel(self, provider_id: int, actor: str, consumer_id: int,
                     subscription_id: int) -> None:
        sub = await self._get_owned(consumer_id, subscription_id)
        await self._subs.set_status(subscription_id, "cancelled")
        # D-020: cached bundles still authorize this (consumer, api).
        await invalidate_consumer_api(self._redis, self._pool,
                                      consumer_id, sub["api_id"])
        await self._audit.log(provider_id, actor, "subscription.cancelled",
                              "subscription", subscription_id)

    async def change_plan(self, provider_id: int, actor: str, consumer_id: int,
                          subscription_id: int, new_plan_id: int) -> dict:
        sub = await self._get_owned(consumer_id, subscription_id)
        if sub["status"] != "active":
            raise ValidationError("Subscription is not active")

        plan = await self._plans.get(new_plan_id)
        if not plan or plan["api_id"] != sub["api_id"]:
            raise ValidationError("Plan does not belong to this API")

        # Cancel old, create new — both in same api_id scope
        await self._subs.set_status(subscription_id, "cancelled")
        new_sub = await self._subs.insert(consumer_id, sub["api_id"], new_plan_id)

        # D-020: cached bundles carry the OLD plan's quota/rate limits.
        await invalidate_consumer_api(self._redis, self._pool,
                                      consumer_id, sub["api_id"])
        await self._audit.log(provider_id, actor, "subscription.plan_changed",
                              "subscription", new_sub["id"],
                              {"from_plan": sub["plan_id"], "to_plan": new_plan_id})
        return new_sub

    async def _get_owned(self, consumer_id: int, subscription_id: int) -> dict:
        sub = await self._subs.get(subscription_id)
        if not sub or sub["consumer_id"] != consumer_id:
            raise NotFoundError("Subscription not found")
        return sub