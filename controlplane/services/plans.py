from controlplane.repositories.interfaces import PlanRepository
from controlplane.services.audit import AuditWriter
from controlplane.services.errors import NotFoundError


class PlanService:
    def __init__(self, repo: PlanRepository, audit: AuditWriter) -> None:
        self._repo = repo
        self._audit = audit

    async def create(self, provider_id: int, actor: str, api_id: int, spec: dict) -> dict:
        plan = await self._repo.insert(
            api_id, spec["rate_limit_policy_id"], spec["name"],
            spec["monthly_quota"], spec["overage_allowed"],
            spec["overage_price"], spec["price_monthly"],
        )
        await self._audit.log(provider_id, actor, "plan.created", "plan",
                              plan["id"], {"name": spec["name"]})
        return plan

    async def change(self, provider_id: int, actor: str, api_id: int,
                     old_plan_id: int, new_spec: dict) -> dict:
        """
        D-010: plans are immutable — a change is a NEW row, the old row
        is retired, and existing subscriptions keep their FK to the old
        row (automatic grandfathering). No cache invalidation needed:
        grandfathered subscriptions genuinely keep the old terms.
        """
        old = await self._get_owned(api_id, old_plan_id)
        new = await self.create(provider_id, actor, api_id, new_spec)
        await self._repo.retire(old_plan_id)
        await self._audit.log(provider_id, actor, "plan.changed", "plan",
                              new["id"], {"supersedes": old["id"]})
        return new

    async def retire(self, provider_id: int, actor: str, api_id: int,
                     plan_id: int) -> None:
        plan = await self._get_owned(api_id, plan_id)
        await self._repo.retire(plan_id)
        await self._audit.log(provider_id, actor, "plan.retired", "plan",
                              plan_id, {"name": plan["name"]})

    async def _get_owned(self, api_id: int, plan_id: int) -> dict:
        plan = await self._repo.get(plan_id)
        if not plan or plan["api_id"] != api_id:
            raise NotFoundError("Plan not found")
        return plan