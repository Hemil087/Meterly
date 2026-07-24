from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from common.db import get_pool
from controlplane.repositories.postgres.providers import PostgresProviderRepository
from controlplane.schemas.providers import ProviderCreate, ProviderOut

router = APIRouter(prefix="/providers", tags=["providers"])


async def get_repo() -> PostgresProviderRepository:
    return PostgresProviderRepository(await get_pool())


@router.post("/", response_model=ProviderOut, status_code=201)
async def create_provider(
    body: ProviderCreate,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    if await repo.get_by_slug(body.slug):
        raise HTTPException(status_code=409, detail="Slug already taken")
    return await repo.insert(body.name, body.slug, body.shared_secret)


@router.get("/{provider_id}", response_model=ProviderOut)
async def get_provider(
    provider_id: int,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("/{provider_id}/suspend", status_code=204)
async def suspend_provider(
    provider_id: int,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    if not await repo.get(provider_id):
        raise HTTPException(status_code=404, detail="Provider not found")
    await repo.set_status(provider_id, "suspended")


@router.post("/{provider_id}/reactivate", status_code=204)
async def reactivate_provider(
    provider_id: int,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    if not await repo.get(provider_id):
        raise HTTPException(status_code=404, detail="Provider not found")
    await repo.set_status(provider_id, "active")


class ProviderUpdate(BaseModel):
    shared_secret: str

@router.patch("/{provider_id}", status_code=200, response_model=ProviderOut)
async def update_provider(
    provider_id: int,
    body: ProviderUpdate,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        UPDATE providers SET shared_secret = $1
        WHERE id = $2
        RETURNING id, name, slug, status, created_at
        """,
        body.shared_secret, provider_id,
    )
    return dict(row)