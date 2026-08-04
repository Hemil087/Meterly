from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from common.db import get_pool
from common.redis_client import get_redis
from common.route_cache import invalidate_provider
from controlplane.services import AuditWriter

# Actor is a placeholder until control-plane auth (users/members) lands.
ACTOR = "dashboard"
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
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await repo.set_status(provider_id, "suspended")
    # Cached routes still say "active" — drop them all so suspension
    # is enforced on the next request, not at TTL expiry.
    await invalidate_provider(await get_redis(), provider["slug"])
    await AuditWriter(await get_pool()).log(provider_id, ACTOR,
        "provider.suspended", "provider", provider_id)


@router.post("/{provider_id}/reactivate", status_code=204)
async def reactivate_provider(
    provider_id: int,
    repo: PostgresProviderRepository = Depends(get_repo),
):
    provider = await repo.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await repo.set_status(provider_id, "active")
    # Mirror of suspend: cached "suspended" routes must not linger.
    await invalidate_provider(await get_redis(), provider["slug"])
    await AuditWriter(await get_pool()).log(provider_id, ACTOR,
        "provider.reactivated", "provider", provider_id)


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
    # Every cached route under this provider carries the OLD secret —
    # drop them so the rotated credential is injected immediately.
    await invalidate_provider(await get_redis(), provider["slug"])
    # Secret VALUE never goes in the audit detail — only the fact.
    await AuditWriter(await get_pool()).log(provider_id, ACTOR,
        "provider.secret_rotated", "provider", provider_id)
    return dict(row)