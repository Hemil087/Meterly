from datetime import datetime
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    api_id: int
    plan_id: int


class SubscriptionOut(BaseModel):
    id: int
    consumer_id: int
    api_id: int
    plan_id: int
    status: str
    cycle_anchor: str
    created_at: datetime

    model_config = {"from_attributes": True}

class PlanChange(BaseModel):
    new_plan_id: int