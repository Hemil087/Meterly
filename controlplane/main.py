from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.db import close_pool, get_pool
from controlplane.routers import providers, consumers, apis, plans, subscriptions, keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(title="Meterly Control Plane", lifespan=lifespan)

app.include_router(providers.router)
app.include_router(consumers.router)
app.include_router(apis.router)
app.include_router(plans.router)
app.include_router(subscriptions.router)
app.include_router(keys.router)