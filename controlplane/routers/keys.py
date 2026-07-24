import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.keys import PostgresApiKeyRepository
from controlplane.schemas.keys import KeyCreate, KeyOut, KeyCreatedOut

router = APIRouter(
    prefix="/providers/{provider_id}/consumers/{consumer_id}/keys",
    tags=["keys"],
)


async def get_repo() -> PostgresApiKeyRepository:
    return PostgresApiKeyRepository(await get_pool())


@router.post("/", response_model=KeyCreatedOut, status_code=201)
async def issue_key(
    provider_id: int,
    consumer_id: int,
    body: KeyCreate,
    repo: PostgresApiKeyRepository = Depends(get_repo),
):
    raw_key = "mk_live_" + secrets.token_urlsafe(24)
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    row = await repo.insert(consumer_id, key_hash, key_prefix, body.expires_at)
    return {**row, "raw_key": raw_key}


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
    repo: PostgresApiKeyRepository = Depends(get_repo),
):
    await repo.revoke(key_id)