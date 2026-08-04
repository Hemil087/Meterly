from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.plans import PostgresPlanRepository
from controlplane.schemas.plans import PlanCreate, PlanOut
from controlplane.services import AuditWriter, PlanService
from controlplane.services.errors import NotFoundError

router = APIRouter(prefix="/providers/{provider_id}/apis/{api_id}/plans", tags=["plans"])

ACTOR = "dashboard"


async def get_repo() -> PostgresPlanRepository:
    return PostgresPlanRepository(await get_pool())


async def get_service() -> PlanService:
    pool = await get_pool()
    return PlanService(PostgresPlanRepository(pool), AuditWriter(pool))


@router.post("/", response_model=PlanOut, status_code=201)
async def create_plan(
    provider_id: int,
    api_id: int,
    body: PlanCreate,
    svc: PlanService = Depends(get_service),
):
    return await svc.create(provider_id, ACTOR, api_id, body.model_dump())


@router.get("/", response_model=list[PlanOut])
async def list_plans(
    provider_id: int,
    api_id: int,
    repo: PostgresPlanRepository = Depends(get_repo),
):
    return await repo.list_by_api(api_id)


@router.post("/{plan_id}/change", response_model=PlanOut)
async def change_plan(
    provider_id: int,
    api_id: int,
    plan_id: int,
    body: PlanCreate,
    svc: PlanService = Depends(get_service),
):
    """D-010: pricing change = new immutable row; old row retired;
    existing subscriptions grandfathered on the old row."""
    try:
        return await svc.change(provider_id, ACTOR, api_id, plan_id, body.model_dump())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{plan_id}/retire", status_code=204)
async def retire_plan(
    provider_id: int,
    api_id: int,
    plan_id: int,
    svc: PlanService = Depends(get_service),
):
    try:
        await svc.retire(provider_id, ACTOR, api_id, plan_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))