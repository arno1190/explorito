"""levels ps-cm2 and profile level

Revision ID: 7de9283d40b8
Revises: 2f655a5969cd
Create Date: 2026-07-24 14:50:54.842835

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7de9283d40b8"
down_revision: str | Sequence[str] | None = "2f655a5969cd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Ajoute les niveaux PS/MS/GS/CM1/CM2 à l'enum et la colonne profiles.level."""
    # Les labels de l'enum sont les NOMS de membres (CP, CE1, ...) — cf. SQLAlchemy.
    for label in ("PS", "MS", "GS", "CM1", "CM2"):
        op.execute(f"ALTER TYPE levelenum ADD VALUE IF NOT EXISTS '{label}'")

    # La colonne réutilise le type enum existant (ne pas le recréer).
    level_enum = sa.Enum(name="levelenum", create_type=False)
    op.add_column("profiles", sa.Column("level", level_enum, nullable=True))


def downgrade() -> None:
    """Retire la colonne profiles.level (les valeurs d'enum ne sont pas retirées)."""
    op.drop_column("profiles", "level")
    # PostgreSQL ne permet pas de retirer proprement des valeurs d'enum ; on les laisse.
