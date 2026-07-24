from pydantic import BaseModel


class ConsumerUsageSummary(BaseModel):
    consumer_id: int
    consumer_name: str
    calls_forwarded: int
    calls_blocked: int
    rate_limited: int
    quota_blocked: int
    avg_latency_ms: float | None


class ProviderOverview(BaseModel):
    total_calls: int
    forwarded: int
    rate_limited: int
    quota_blocked: int
    auth_failed: int
    upstream_errors: int


class RecentEvent(BaseModel):
    occurred_at: str
    consumer_id: int
    method: str
    path: str
    status_code: int
    outcome: str
    latency_ms: int