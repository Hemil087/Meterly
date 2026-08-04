"""
The enforcement pipeline: every request passes an ordered list of
checks before it may be forwarded. Each check answers one question:

    KeyAuthCheck   — is this key valid AND subscribed to this API?
    RateLimitCheck — is this subscription within its per-window rate?
    QuotaCheck     — is this subscription within its monthly quota?

Checks share one interface (RequestCheck) and communicate through the
RequestContext they progressively enrich: KeyAuthCheck resolves the
auth bundle that RateLimitCheck and QuotaCheck then read. The pipeline
runs them in order and stops at the first failure — order is therefore
part of the contract, not an implementation detail (a rate-limited
request must never consume quota).

Adding a check (e.g. an IP allowlist) = one new class + one line in
the pipeline list. Nothing else changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from gateway.auth import resolve_auth
from gateway.quota import check_and_increment_quota
from gateway.ratelimit import check_rate_limit


@dataclass
class RequestContext:
    """Everything known about the request so far; checks enrich it."""
    provider_id: int
    api_id: int
    method: str
    path: str
    raw_key: str | None
    # filled by KeyAuthCheck:
    bundle: dict | None = None
    # filled by RateLimitCheck / QuotaCheck (for success headers):
    rl_remaining: int = 0
    quota_used: int = 0


@dataclass
class CheckResult:
    allowed: bool
    outcome: str = "forwarded"       # outcome recorded if this check fails
    http_status: int = 200
    detail: str = ""
    headers: dict = field(default_factory=dict)

    @staticmethod
    def ok() -> "CheckResult":
        return CheckResult(allowed=True)


class RequestCheck(ABC):
    @abstractmethod
    async def check(self, ctx: RequestContext) -> CheckResult: ...


class KeyAuthCheck(RequestCheck):
    """
    Key validity and subscription in ONE check: the authorization join
    (D-002) resolves both in a single cached query, so splitting them
    into two checks would double the Redis reads for no gain.
    On success, stores the auth bundle on the context for later checks.
    """

    async def check(self, ctx: RequestContext) -> CheckResult:
        if not ctx.raw_key:
            return CheckResult(False, "auth_failed", 401, "Missing X-API-Key header")

        bundle = await resolve_auth(ctx.raw_key, ctx.api_id)
        if not bundle:
            return CheckResult(False, "auth_failed", 401, "Invalid or inactive key")

        ctx.bundle = bundle
        return CheckResult.ok()


class RateLimitCheck(RequestCheck):
    async def check(self, ctx: RequestContext) -> CheckResult:
        b = ctx.bundle
        allowed, remaining, retry_after_ms = await check_rate_limit(
            subscription_id=b["subscription_id"],
            requests=b["rl_requests"],
            window_seconds=b["rl_window_seconds"],
            burst=b["rl_burst"],
        )
        if not allowed:
            return CheckResult(
                False, "rate_limited", 429, "Rate limit exceeded",
                headers={
                    "Retry-After": str(max(1, retry_after_ms // 1000)),
                    "X-RateLimit-Limit": str(b["rl_requests"]),
                    "X-RateLimit-Remaining": "0",
                },
            )
        ctx.rl_remaining = remaining
        return CheckResult.ok()


class QuotaCheck(RequestCheck):
    async def check(self, ctx: RequestContext) -> CheckResult:
        b = ctx.bundle
        allowed, calls_used = await check_and_increment_quota(
            subscription_id=b["subscription_id"],
            monthly_quota=b["monthly_quota"],
            overage_allowed=b["overage_allowed"],
        )
        ctx.quota_used = calls_used
        if not allowed:
            return CheckResult(
                False, "quota_blocked", 429, "Monthly quota exceeded",
                headers={
                    "X-Quota-Limit": str(b["monthly_quota"]),
                    "X-Quota-Used": str(calls_used),
                },
            )
        return CheckResult.ok()


class CheckPipeline:
    def __init__(self, checks: list[RequestCheck]) -> None:
        self._checks = checks

    async def run(self, ctx: RequestContext) -> CheckResult:
        """Runs checks in order; returns the first failure, or ok."""
        for check in self._checks:
            result = await check.check(ctx)
            if not result.allowed:
                return result
        return CheckResult.ok()


def default_pipeline() -> CheckPipeline:
    # Order is a contract: auth before limits (unidentified requests
    # must not touch counters), rate limit before quota (a rate-limited
    # request must not consume monthly quota).
    return CheckPipeline([KeyAuthCheck(), RateLimitCheck(), QuotaCheck()])