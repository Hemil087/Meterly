from datetime import datetime
from pydantic import BaseModel


class ProviderCreate(BaseModel):
    name: str
    slug: str
    shared_secret: str


class ProviderOut(BaseModel):
    id: int
    name: str
    slug: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}