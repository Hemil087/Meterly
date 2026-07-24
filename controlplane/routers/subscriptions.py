from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.subscriptions import PostgresSubscriptionRepository
from controlplane.repositories.postgres.plans import PostgresPlanRepository
from controlplane.schemas.subscriptions import SubscriptionCreate, SubscriptionOut, PlanChange

router = APIRouter(
    prefix="/providers/{provider_id}/consumers/{consumer_id}/subscriptions",
    tags=["subscriptions"],
)


async def get_sub_repo() -> PostgresSubscriptionRepository:
    return PostgresSubscriptionRepository(await get_pool())


async def get_plan_repo() -> PostgresPlanRepository:
    return PostgresPlanRepository(await get_pool())


@router.post("/", response_model=SubscriptionOut, status_code=201)
async def subscribe(
    provider_id: int,
    consumer_id: int,
    body: SubscriptionCreate,
    sub_repo: PostgresSubscriptionRepository = Depends(get_sub_repo),
    plan_repo: PostgresPlanRepository = Depends(get_plan_repo),
):
    # Guard: plan must exist and belong to the requested api
    plan = await plan_repo.get(body.plan_id)
    if not plan or plan["api_id"] != body.api_id:
        raise HTTPException(status_code=400, detail="Plan does not belong to this API")

    # Guard: no duplicate active subscription (partial index enforces at DB level too)
    existing = await sub_repo.get_active(consumer_id, body.api_id)
    if existing:
        raise HTTPException(status_code=409, detail="Active subscription already exists")

    return await sub_repo.insert(consumer_id, body.api_id, body.plan_id)


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
    sub_repo: PostgresSubscriptionRepository = Depends(get_sub_repo),
):
    sub = await sub_repo.get(subscription_id)
    if not sub or sub["consumer_id"] != consumer_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await sub_repo.set_status(subscription_id, "cancelled")


@router.post("/{subscription_id}/change_plan", response_model=SubscriptionOut)
async def change_plan(
    provider_id: int,
    consumer_id: int,
    subscription_id: int,
    body: PlanChange,
    sub_repo: PostgresSubscriptionRepository = Depends(get_sub_repo),
    plan_repo: PostgresPlanRepository = Depends(get_plan_repo),
):
    sub = await sub_repo.get(subscription_id)
    if not sub or sub["consumer_id"] != consumer_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub["status"] != "active":
        raise HTTPException(status_code=400, detail="Subscription is not active")

    plan = await plan_repo.get(body.new_plan_id)
    if not plan or plan["api_id"] != sub["api_id"]:
        raise HTTPException(status_code=400, detail="Plan does not belong to this API")

    # Cancel old, create new — both in same api_id scope
    await sub_repo.set_status(subscription_id, "cancelled")
    return await sub_repo.insert(consumer_id, sub["api_id"], body.new_plan_id)