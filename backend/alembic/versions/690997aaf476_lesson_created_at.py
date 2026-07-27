"""lesson created_at

Revision ID: 690997aaf476
Revises: 7de9283d40b8
Create Date: 2026-07-27 14:31:26.112028

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "690997aaf476"
down_revision: str | Sequence[str] | None = "7de9283d40b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ajoute lessons.created_at (server_default now() pour backfiller l'existant)."""
    op.add_column(
        "lessons",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Retire lessons.created_at."""
    op.drop_column("lessons", "created_at")
