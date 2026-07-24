"""initial_schema

Revision ID: f6bf5a0729bb
Revises:
Create Date: 2026-07-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "f6bf5a0729bb"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # TIER 1 — no foreign-key dependencies
    # =========================================================================

    op.create_table(
        "providers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("shared_secret", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("slug", name="uq_providers_slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "rate_limit_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("burst", sa.Integer(), nullable=True),
        sa.Column("algorithm", sa.Text(), nullable=False),
    )

    # =========================================================================
    # TIER 2 — depend on providers / users
    # =========================================================================

    op.create_table(
        "consumers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "provider_id",
            sa.BigInteger(),
            sa.ForeignKey("providers.id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("contact_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "provider_id", "email", name="uq_consumers_provider_email"
        ),
    )

    op.create_table(
        "apis",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "provider_id",
            sa.BigInteger(),
            sa.ForeignKey("providers.id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("upstream_url", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.UniqueConstraint("provider_id", "slug", name="uq_apis_provider_slug"),
    )

    op.create_table(
        "provider_members",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "provider_id",
            sa.BigInteger(),
            sa.ForeignKey("providers.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column(
            "added_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "consumer_members",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "consumer_id",
            sa.BigInteger(),
            sa.ForeignKey("consumers.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column(
            "added_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # =========================================================================
    # TIER 3 — depend on apis / rate_limit_policies
    # =========================================================================

    op.create_table(
        "api_endpoints",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "api_id", sa.BigInteger(), sa.ForeignKey("apis.id"), nullable=False
        ),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.UniqueConstraint(
            "api_id", "method", "path", name="uq_api_endpoints_api_method_path"
        ),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "api_id", sa.BigInteger(), sa.ForeignKey("apis.id"), nullable=False
        ),
        sa.Column(
            "rate_limit_policy_id",
            sa.BigInteger(),
            sa.ForeignKey("rate_limit_policies.id"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("monthly_quota", sa.BigInteger(), nullable=False),
        sa.Column(
            "overage_allowed", sa.Boolean(), nullable=False, server_default="false"
        ),
        # overage_price: price per single call — needs 6 decimal places
        sa.Column(
            "overage_price",
            sa.Numeric(14, 6),
            nullable=False,
            server_default="0",
        ),
        sa.Column("price_monthly", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.UniqueConstraint("api_id", "name", name="uq_plans_api_name"),
    )

    # =========================================================================
    # TIER 4 — subscriptions + api_keys
    # =========================================================================

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "consumer_id",
            sa.BigInteger(),
            sa.ForeignKey("consumers.id"),
            nullable=False,
        ),
        sa.Column(
            "api_id", sa.BigInteger(), sa.ForeignKey("apis.id"), nullable=False
        ),
        sa.Column(
            "plan_id", sa.BigInteger(), sa.ForeignKey("plans.id"), nullable=False
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("cycle_anchor", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    # D-004: partial unique — only one ACTIVE subscription per (consumer, api)
    op.create_index(
        "uq_subscriptions_active_consumer_api",
        "subscriptions",
        ["consumer_id", "api_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "consumer_id",
            sa.BigInteger(),
            sa.ForeignKey("consumers.id"),
            nullable=False,
        ),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("key_prefix", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
    )
    # D-014: partial index — hot path only looks up active keys
    op.create_index(
        "ix_api_keys_active_hash",
        "api_keys",
        ["key_hash"],
        postgresql_where=sa.text("status = 'active'"),
    )

    # =========================================================================
    # TIER 5 — usage_events (partitioned — must use raw SQL)
    # D-009: PARTITION BY RANGE (occurred_at), monthly partitions
    # SQLAlchemy/Alembic do not emit PARTITION BY in create_table, so we use
    # op.execute() here. The PK includes occurred_at because Postgres requires
    # the partition key to be part of every unique/PK constraint.
    # =========================================================================

    op.execute("""
        CREATE TABLE usage_events (
            id              BIGSERIAL,
            occurred_at     TIMESTAMPTZ         NOT NULL,
            provider_id     BIGINT              NOT NULL REFERENCES providers(id),
            consumer_id     BIGINT              NOT NULL REFERENCES consumers(id),
            api_id          BIGINT              NOT NULL REFERENCES apis(id),
            subscription_id BIGINT              NOT NULL REFERENCES subscriptions(id),
            endpoint_id     BIGINT              REFERENCES api_endpoints(id),
            method          TEXT                NOT NULL,
            path            TEXT                NOT NULL,
            status_code     INTEGER             NOT NULL,
            outcome         TEXT                NOT NULL,
            latency_ms      INTEGER             NOT NULL,
            upstream_ms     INTEGER             NOT NULL,
            request_bytes   BIGINT,
            response_bytes  BIGINT,
            idempotency_key TEXT,
            PRIMARY KEY (id, occurred_at)
        ) PARTITION BY RANGE (occurred_at);
    """)

    # Seed partitions: current month + 2 months ahead
    # Add new ones via a separate migration or a scheduled job in production
    op.execute("""
        CREATE TABLE usage_events_y2026m07
            PARTITION OF usage_events
            FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
    """)
    op.execute("""
        CREATE TABLE usage_events_y2026m08
            PARTITION OF usage_events
            FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
    """)
    op.execute("""
        CREATE TABLE usage_events_y2026m09
            PARTITION OF usage_events
            FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
    """)

    # D-014: composite indexes on the hot dashboard access paths
    op.execute(
        "CREATE INDEX ix_usage_events_provider_time "
        "ON usage_events (provider_id, occurred_at);"
    )
    op.execute(
        "CREATE INDEX ix_usage_events_subscription_time "
        "ON usage_events (subscription_id, occurred_at);"
    )
    op.execute(
        "CREATE INDEX ix_usage_events_api_time "
        "ON usage_events (api_id, occurred_at);"
    )

    # =========================================================================
    # usage_hourly — D-006/D-007: derived rollup, NO FK constraints declared
    # =========================================================================

    op.create_table(
        "usage_hourly",
        sa.Column("consumer_id", sa.BigInteger(), nullable=False, primary_key=True),
        sa.Column("api_id", sa.BigInteger(), nullable=False, primary_key=True),
        sa.Column(
            "hour", sa.TIMESTAMP(timezone=True), nullable=False, primary_key=True
        ),
        # provider_id denormalized — NOT in PK (api already determines provider)
        sa.Column("provider_id", sa.BigInteger(), nullable=False),
        sa.Column("calls_forwarded", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("calls_blocked", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("rate_limited", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("upstream_errors", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("p95_latency_ms", sa.Integer(), nullable=True),
        sa.Column("total_upstream_ms", sa.BigInteger(), nullable=False, server_default="0"),
    )

    # =========================================================================
    # statements
    # =========================================================================

    op.create_table(
        "statements",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "subscription_id",
            sa.BigInteger(),
            sa.ForeignKey("subscriptions.id"),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("calls_included", sa.BigInteger(), nullable=False),
        sa.Column("calls_used", sa.BigInteger(), nullable=False),
        sa.Column(
            "overage_calls", sa.BigInteger(), nullable=False, server_default="0"
        ),
        sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "overage_amount", sa.Numeric(12, 2), nullable=False, server_default="0"
        ),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.UniqueConstraint(
            "subscription_id",
            "period_start",
            name="uq_statements_subscription_period",
        ),
    )

    # =========================================================================
    # audit_log — D-015: entity_id is polymorphic, no FK declared
    # =========================================================================

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "provider_id",
            sa.BigInteger(),
            sa.ForeignKey("providers.id"),
            nullable=False,
        ),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),  # no FK — D-015
        sa.Column("detail", JSONB(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_audit_log_provider_time", "audit_log", ["provider_id", "occurred_at"]
    )


def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("audit_log")
    op.drop_table("statements")
    op.drop_table("usage_hourly")
    op.execute("DROP TABLE IF EXISTS usage_events CASCADE;")
    op.drop_index("ix_api_keys_active_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(
        "uq_subscriptions_active_consumer_api", table_name="subscriptions"
    )
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("api_endpoints")
    op.drop_table("consumer_members")
    op.drop_table("provider_members")
    op.drop_table("apis")
    op.drop_table("consumers")
    op.drop_table("rate_limit_policies")
    op.drop_table("users")
    op.drop_table("providers")