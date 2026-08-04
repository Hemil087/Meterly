from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.consumers import PostgresConsumerRepository
from controlplane.schemas.consumers import ConsumerCreate, ConsumerOut
from controlplane.services import AuditWriter, ConsumerService
from controlplane.services.errors import NotFoundError

router = APIRouter(prefix="/providers/{provider_id}/consumers", tags=["consumers"])

# Actor is a placeholder until control-plane auth (users/members) lands.
ACTOR = "dashboard"


async def get_repo() -> PostgresConsumerRepository:
    return PostgresConsumerRepository(await get_pool())


async def get_service() -> ConsumerService:
    pool = await get_pool()
    return ConsumerService(PostgresConsumerRepository(pool), AuditWriter(pool))


@router.post("/", response_model=ConsumerOut, status_code=201)
async def onboard_consumer(
    provider_id: int,
    body: ConsumerCreate,
    svc: ConsumerService = Depends(get_service),
):
    return await svc.onboard(provider_id, ACTOR, body.name, body.email, body.contact_name)


@router.get("/", response_model=list[ConsumerOut])
async def list_consumers(
    provider_id: int,
    repo: PostgresConsumerRepository = Depends(get_repo),
):
    return await repo.list_by_provider(provider_id)


@router.get("/{consumer_id}", response_model=ConsumerOut)
async def get_consumer(
    provider_id: int,
    consumer_id: int,
    repo: PostgresConsumerRepository = Depends(get_repo),
):
    consumer = await repo.get(consumer_id)
    if not consumer or consumer["provider_id"] != provider_id:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return consumer


@router.post("/{consumer_id}/suspend", status_code=204)
async def suspend_consumer(
    provider_id: int,
    consumer_id: int,
    svc: ConsumerService = Depends(get_service),
):
    try:
        await svc.suspend(provider_id, ACTOR, consumer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{consumer_id}/reactivate", status_code=204)
async def reactivate_consumer(
    provider_id: int,
    consumer_id: int,
    svc: ConsumerService = Depends(get_service),
):
    try:
        await svc.reactivate(provider_id, ACTOR, consumer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))