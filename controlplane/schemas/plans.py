from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    rate_limit_policy_id: int
    monthly_quota: int
    overage_allowed: bool = False
    overage_price: float = 0.0
    price_monthly: float


class PlanOut(BaseModel):
    id: int
    api_id: int
    name: str
    monthly_quota: int
    overage_allowed: bool
    overage_price: float
    price_monthly: float
    status: str

    model_config = {"from_attributes": True}