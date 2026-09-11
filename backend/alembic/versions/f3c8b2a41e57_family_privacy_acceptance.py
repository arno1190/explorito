"""politique de confidentialité famille : version acceptée + horodatage sur users

Revision ID: f3c8b2a41e57
Revises: e2b6f4c81d37
Create Date: 2026-09-10

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3c8b2a41e57"
down_revision: str | None = "e2b6f4c81d37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable et sans valeur par défaut : les comptes existants n'ont
    # justement *pas* accepté la politique, et la case leur sera présentée à
    # leur prochaine visite. Les remplir d'office fabriquerait un consentement.
    op.add_column("users", sa.Column("privacy_version", sa.String(), nullable=True))
    op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "privacy_accepted_at")
    op.drop_column("users", "privacy_version")
