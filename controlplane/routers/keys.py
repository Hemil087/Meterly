from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from common.redis_client import get_redis
from controlplane.repositories.postgres.keys import PostgresApiKeyRepository
from controlplane.schemas.keys import KeyCreate, KeyOut, KeyCreatedOut
from controlplane.services import AuditWriter, KeyService
from controlplane.services.errors import NotFoundError

router = APIRouter(
    prefix="/providers/{provider_id}/consumers/{consumer_id}/keys",
    tags=["keys"],
)

ACTOR = "dashboard"


async def get_repo() -> PostgresApiKeyRepository:
    return PostgresApiKeyRepository(await get_pool())


async def get_service() -> KeyService:
    pool = await get_pool()
    return KeyService(PostgresApiKeyRepository(pool), AuditWriter(pool), await get_redis())


@router.post("/", response_model=KeyCreatedOut, status_code=201)
async def issue_key(
    provider_id: int,
    consumer_id: int,
    body: KeyCreate,
    svc: KeyService = Depends(get_service),
):
    return await svc.issue(provider_id, ACTOR, consumer_id, body.expires_at)


@router.get("/", response_model=list[KeyOut])
async def list_keys(
    provider_id: int,
    consumer_id: int,
    repo: PostgresApiKeyRepository = Depends(get_repo),
):
    return await repo.list_by_consumer(consumer_id)


@router.post("/{key_id}/revoke", status_code=204)
async def revoke_key(
    provider_id: int,
    consumer_id: int,
    key_id: int,
    svc: KeyService = Depends(get_service),
):
    try:
        await svc.revoke(provider_id, ACTOR, key_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))