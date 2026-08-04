"""Auth Google : email/password optionnels + google_sub + pin_hash.

Seuls les parents s'authentifient (via Google) ; les enfants deviennent des
comptes sans connexion. On rend donc ``email`` et ``password_hash`` nullables,
et on ajoute ``google_sub`` (identité Google stable) et ``pin_hash`` (PIN parent).

Revision ID: b2e8d4a15c3f
Revises: a1f7c93b2d84
Create Date: 2026-08-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2e8d4a15c3f"
down_revision: str | Sequence[str] | None = "a1f7c93b2d84"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(), nullable=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=True)
    op.add_column("users", sa.Column("google_sub", sa.String(), nullable=True))
    op.add_column("users", sa.Column("pin_hash", sa.String(), nullable=True))
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_column("users", "pin_hash")
    op.drop_column("users", "google_sub")
    op.alter_column("users", "password_hash", existing_type=sa.String(), nullable=False)
    op.alter_column("users", "email", existing_type=sa.String(), nullable=False)
