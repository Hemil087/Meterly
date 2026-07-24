from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.plans import PostgresPlanRepository
from controlplane.schemas.plans import PlanCreate, PlanOut

router = APIRouter(prefix="/providers/{provider_id}/apis/{api_id}/plans", tags=["plans"])


async def get_repo() -> PostgresPlanRepository:
    return PostgresPlanRepository(await get_pool())


@router.post("/", response_model=PlanOut, status_code=201)
async def create_plan(
    provider_id: int,
    api_id: int,
    body: PlanCreate,
    repo: PostgresPlanRepository = Depends(get_repo),
):
    return await repo.insert(
        api_id, body.rate_limit_policy_id, body.name,
        body.monthly_quota, body.overage_allowed,
        body.overage_price, body.price_monthly,
    )


@router.get("/", response_model=list[PlanOut])
async def list_plans(
    provider_id: int,
    api_id: int,
    repo: PostgresPlanRepository = Depends(get_repo),
):
    return await repo.list_by_api(api_id)


@router.post("/{plan_id}/retire", status_code=204)
async def retire_plan(
    provider_id: int,
    api_id: int,
    plan_id: int,
    repo: PostgresPlanRepository = Depends(get_repo),
):
    plan = await repo.get(plan_id)
    if not plan or plan["api_id"] != api_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    await repo.retire(plan_id)