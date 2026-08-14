"""add sudoku_sessions

Revision ID: 6512370fd641
Revises: c3f9a7d21e08
Create Date: 2026-08-14 11:49:42.780472

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6512370fd641"
down_revision: str | Sequence[str] | None = "c3f9a7d21e08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée la table des sessions du défi Sudoku."""
    op.create_table(
        "sudoku_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("puzzle", sa.JSON(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("solved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sudoku_sessions_id"), "sudoku_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_sudoku_sessions_user_id"), "sudoku_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    """Supprime la table des sessions du défi Sudoku."""
    op.drop_index(op.f("ix_sudoku_sessions_user_id"), table_name="sudoku_sessions")
    op.drop_index(op.f("ix_sudoku_sessions_id"), table_name="sudoku_sessions")
    op.drop_table("sudoku_sessions")
