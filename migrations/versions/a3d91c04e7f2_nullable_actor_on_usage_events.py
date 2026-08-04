"""nullable actor columns on usage_events

auth_failed events have no known consumer or subscription — the request
was rejected before identity was established. provider_id and api_id
stay NOT NULL: they are resolved from the URL path before auth, so every
event is always attributable to a provider (dashboard scoping intact).

Revision ID: a3d91c04e7f2
Revises: f6bf5a0729bb
Create Date: 2026-08-04
"""

from alembic import op

revision = "a3d91c04e7f2"
down_revision = "f6bf5a0729bb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER on the partitioned parent propagates to all partitions
    op.execute("ALTER TABLE usage_events ALTER COLUMN consumer_id DROP NOT NULL")
    op.execute("ALTER TABLE usage_events ALTER COLUMN subscription_id DROP NOT NULL")


def downgrade() -> None:
    # Would fail if auth_failed rows with NULLs exist — delete them first
    op.execute("DELETE FROM usage_events WHERE consumer_id IS NULL OR subscription_id IS NULL")
    op.execute("ALTER TABLE usage_events ALTER COLUMN consumer_id SET NOT NULL")
    op.execute("ALTER TABLE usage_events ALTER COLUMN subscription_id SET NOT NULL")