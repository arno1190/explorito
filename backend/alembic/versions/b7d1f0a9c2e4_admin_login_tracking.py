"""admin login tracking: login_count/last_login_at on users + login_events table

Revision ID: b7d1f0a9c2e4
Revises: a1c2e3d4f5b6
Create Date: 2026-08-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "b7d1f0a9c2e4"
down_revision: str | None = "a1c2e3d4f5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("login_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.create_table(
        "login_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_login_events_user_id", "login_events", ["user_id"])
    op.create_index("ix_login_events_created_at", "login_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_login_events_created_at", table_name="login_events")
    op.drop_index("ix_login_events_user_id", table_name="login_events")
    op.drop_table("login_events")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "login_count")
