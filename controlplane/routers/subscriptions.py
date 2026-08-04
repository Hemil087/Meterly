from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from common.redis_client import get_redis
from controlplane.repositories.postgres.subscriptions import PostgresSubscriptionRepository
from controlplane.repositories.postgres.plans import PostgresPlanRepository
from controlplane.schemas.subscriptions import SubscriptionCreate, SubscriptionOut, PlanChange
from controlplane.services import AuditWriter, SubscriptionService
from controlplane.services.errors import ConflictError, NotFoundError, ValidationError

router = APIRouter(
    prefix="/providers/{provider_id}/consumers/{consumer_id}/subscriptions",
    tags=["subscriptions"],
)

ACTOR = "dashboard"


async def get_sub_repo() -> PostgresSubscriptionRepository:
    return PostgresSubscriptionRepository(await get_pool())


async def get_service() -> SubscriptionService:
    pool = await get_pool()
    return SubscriptionService(
        PostgresSubscriptionRepository(pool),
        PostgresPlanRepository(pool),
        AuditWriter(pool),
        await get_redis(),
        pool,
    )


@router.post("/", response_model=SubscriptionOut, status_code=201)
async def subscribe(
    provider_id: int,
    consumer_id: int,
    body: SubscriptionCreate,
    svc: SubscriptionService = Depends(get_service),
):
    try:
        return await svc.subscribe(provider_id, ACTOR, consumer_id, body.api_id, body.plan_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[SubscriptionOut])
async def list_subscriptions(
    provider_id: int,
    consumer_id: int,
    sub_repo: PostgresSubscriptionRepository = Depends(get_sub_repo),
):
    return await sub_repo.list_by_consumer(consumer_id)


@router.post("/{subscription_id}/cancel", status_code=204)
async def cancel_subscription(
    provider_id: int,
    consumer_id: int,
    subscription_id: int,
    svc: SubscriptionService = Depends(get_service),
):
    try:
        await svc.cancel(provider_id, ACTOR, consumer_id, subscription_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{subscription_id}/change_plan", response_model=SubscriptionOut)
async def change_plan(
    provider_id: int,
    consumer_id: int,
    subscription_id: int,
    body: PlanChange,
    svc: SubscriptionService = Depends(get_service),
):
    try:
        return await svc.change_plan(provider_id, ACTOR, consumer_id,
                                     subscription_id, body.new_plan_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))