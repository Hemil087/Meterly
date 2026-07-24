from fastapi import APIRouter, Depends, HTTPException
from common.db import get_pool
from controlplane.repositories.postgres.apis import PostgresApiRepository
from controlplane.schemas.apis import ApiCreate, ApiOut

router = APIRouter(prefix="/providers/{provider_id}/apis", tags=["apis"])


async def get_repo() -> PostgresApiRepository:
    return PostgresApiRepository(await get_pool())


@router.post("/", response_model=ApiOut, status_code=201)
async def register_api(
    provider_id: int,
    body: ApiCreate,
    repo: PostgresApiRepository = Depends(get_repo),
):
    return await repo.insert(provider_id, body.name, body.slug, body.upstream_url)


@router.get("/", response_model=list[ApiOut])
async def list_apis(
    provider_id: int,
    repo: PostgresApiRepository = Depends(get_repo),
):
    return await repo.list_by_provider(provider_id)


@router.post("/{api_id}/disable", status_code=204)
async def disable_api(
    provider_id: int,
    api_id: int,
    repo: PostgresApiRepository = Depends(get_repo),
):
    api = await repo.get(api_id)
    if not api or api["provider_id"] != provider_id:
        raise HTTPException(status_code=404, detail="API not found")
    await repo.set_status(api_id, "disabled")