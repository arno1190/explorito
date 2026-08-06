"""Points attribués par le parent : table point_awards + collectible_unlocks.currency.

Deux porte-monnaies dépensables : « points » (XP + hardskill) et « behavior »
(comportement). Les achats existants sont réputés payés en « points ».

Revision ID: c3f9a7d21e08
Revises: b2e8d4a15c3f
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c3f9a7d21e08"
down_revision: str | Sequence[str] | None = "b2e8d4a15c3f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "collectible_unlocks",
        sa.Column("currency", sa.String(), nullable=False, server_default="points"),
    )
    op.create_table(
        "point_awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("wallet", sa.String(), nullable=False, server_default="points"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("awarded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["awarded_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_point_awards_created_at", "point_awards", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_point_awards_created_at", table_name="point_awards")
    op.drop_table("point_awards")
    op.drop_column("collectible_unlocks", "currency")
