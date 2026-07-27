"""add pythagore_sessions

Revision ID: 8b3c1d2e4f5a
Revises: 690997aaf476
Create Date: 2026-07-27 20:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b3c1d2e4f5a"
down_revision: str | Sequence[str] | None = "690997aaf476"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pythagore_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("longest_streak", sa.Integer(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pythagore_sessions_id"), "pythagore_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_pythagore_sessions_user_id"), "pythagore_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_pythagore_sessions_user_id"), table_name="pythagore_sessions")
    op.drop_index(op.f("ix_pythagore_sessions_id"), table_name="pythagore_sessions")
    op.drop_table("pythagore_sessions")
