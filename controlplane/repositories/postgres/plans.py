import asyncpg
from controlplane.repositories.interfaces import PlanRepository


class PostgresPlanRepository(PlanRepository):
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get(self, plan_id: int) -> dict | None:
        row = await self._pool.fetchrow(
            "SELECT id, api_id, name, monthly_quota, overage_allowed, "
            "overage_price, price_monthly, status FROM plans WHERE id = $1",
            plan_id,
        )
        return dict(row) if row else None

    async def list_by_api(self, api_id: int) -> list[dict]:
        rows = await self._pool.fetch(
            "SELECT id, api_id, name, monthly_quota, overage_allowed, "
            "overage_price, price_monthly, status FROM plans WHERE api_id = $1",
            api_id,
        )
        return [dict(r) for r in rows]

    async def insert(self, api_id: int, rate_limit_policy_id: int, name: str,
                     monthly_quota: int, overage_allowed: bool,
                     overage_price: float, price_monthly: float) -> dict:
        row = await self._pool.fetchrow(
            """
            INSERT INTO plans
                (api_id, rate_limit_policy_id, name, monthly_quota,
                 overage_allowed, overage_price, price_monthly, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'active')
            RETURNING id, api_id, name, monthly_quota, overage_allowed,
                      overage_price, price_monthly, status
            """,
            api_id, rate_limit_policy_id, name, monthly_quota,
            overage_allowed, overage_price, price_monthly,
        )
        return dict(row)

    async def retire(self, plan_id: int) -> None:
        await self._pool.execute(
            "UPDATE plans SET status = 'retired' WHERE id = $1",
            plan_id,
        )