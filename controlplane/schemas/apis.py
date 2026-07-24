from pydantic import BaseModel


class ApiCreate(BaseModel):
    name: str
    slug: str
    upstream_url: str


class ApiOut(BaseModel):
    id: int
    provider_id: int
    name: str
    slug: str
    upstream_url: str
    status: str

    model_config = {"from_attributes": True}