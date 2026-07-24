from datetime import datetime
from pydantic import BaseModel


class KeyCreate(BaseModel):
    expires_at: datetime | None = None


class KeyOut(BaseModel):
    id: int
    key_prefix: str
    status: str
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KeyCreatedOut(KeyOut):
    raw_key: str  # only returned once at creation, never stored