from datetime import datetime
from pydantic import BaseModel


class ConsumerCreate(BaseModel):
    name: str
    email: str
    contact_name: str | None = None


class ConsumerOut(BaseModel):
    id: int
    provider_id: int
    name: str
    email: str
    contact_name: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}