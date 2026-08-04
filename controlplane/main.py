from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.db import close_pool, get_pool
from common.redis_client import get_redis, close_redis
from controlplane.routers import providers, consumers, apis, plans, subscriptions, keys, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    await get_redis()
    yield
    await close_pool()
    await close_redis()


app = FastAPI(title="Meterly Control Plane", lifespan=lifespan)

app.include_router(providers.router)
app.include_router(consumers.router)
app.include_router(apis.router)
app.include_router(plans.router)
app.include_router(subscriptions.router)
app.include_router(keys.router)
app.include_router(analytics.router)
@app.get("/rate_limit_policies/")
async def list_rate_limit_policies():
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, requests, window_seconds, algorithm FROM rate_limit_policies"
    )
    return [dict(r) for r in rows]