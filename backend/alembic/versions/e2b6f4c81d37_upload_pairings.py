"""Codes d'appariement : connecter son assistant sans variable d'environnement.

Revision ID: e2b6f4c81d37
Revises: d4a1c9e05b21
Create Date: 2026-09-04 09:40:00.000000

Un parent ne configurera pas `EXPLORITO_UPLOAD_TOKEN` dans un terminal, et
recopier un secret de 43 caractères depuis un téléphone fait abandonner. Cette
table porte un code court, à usage unique et de courte durée, que le parent lit
à voix haute et que l'assistant échange lui-même contre un jeton d'envoi.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2b6f4c81d37"
down_revision: str | Sequence[str] | None = "d4a1c9e05b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée la table des codes d'appariement."""
    op.create_table(
        "upload_pairings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("token_id", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["token_id"], ["upload_tokens.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code_hash", name="uq_upload_pairing_code"),
    )
    op.create_index("ix_upload_pairings_user_id", "upload_pairings", ["user_id"])
    op.create_index("ix_upload_pairings_code_hash", "upload_pairings", ["code_hash"])


def downgrade() -> None:
    """Retire la table des codes d'appariement."""
    op.drop_index("ix_upload_pairings_code_hash", table_name="upload_pairings")
    op.drop_index("ix_upload_pairings_user_id", table_name="upload_pairings")
    op.drop_table("upload_pairings")
