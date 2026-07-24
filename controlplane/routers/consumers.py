from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.consumers import PostgresConsumerRepository
from controlplane.schemas.consumers import ConsumerCreate, ConsumerOut

router = APIRouter(prefix="/providers/{provider_id}/consumers", tags=["consumers"])


async def get_repo() -> PostgresConsumerRepository:
    return PostgresConsumerRepository(await get_pool())


@router.post("/", response_model=ConsumerOut, status_code=201)
async def onboard_consumer(
    provider_id: int,
    body: ConsumerCreate,
    repo: PostgresConsumerRepository = Depends(get_repo),
):
    return await repo.insert(provider_id, body.name, body.email, body.contact_name)


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
    repo: PostgresConsumerRepository = Depends(get_repo),
):
    consumer = await repo.get(consumer_id)
    if not consumer or consumer["provider_id"] != provider_id:
        raise HTTPException(status_code=404, detail="Consumer not found")
    await repo.set_status(consumer_id, "suspended")