"""generalize pokemon_unlocks into collectible_unlocks (multi-catalogue)

Revision ID: 9c4d2e6f1a7b
Revises: 8b3c1d2e4f5a
Create Date: 2026-08-01 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c4d2e6f1a7b"
down_revision: str | Sequence[str] | None = "8b3c1d2e4f5a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema (préserve les Pokémon déjà débloqués : catalog='pokemon')."""
    op.rename_table("pokemon_unlocks", "collectible_unlocks")
    op.add_column(
        "collectible_unlocks",
        sa.Column("catalog", sa.String(), nullable=False, server_default="pokemon"),
    )
    op.alter_column("collectible_unlocks", "pokemon_id", new_column_name="item_id")
    op.drop_constraint("uq_user_pokemon", "collectible_unlocks", type_="unique")
    op.create_unique_constraint("uq_user_catalog_item", "collectible_unlocks", ["user_id", "catalog", "item_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_user_catalog_item", "collectible_unlocks", type_="unique")
    op.alter_column("collectible_unlocks", "item_id", new_column_name="pokemon_id")
    op.drop_column("collectible_unlocks", "catalog")
    op.create_unique_constraint("uq_user_pokemon", "collectible_unlocks", ["user_id", "pokemon_id"])
    op.rename_table("collectible_unlocks", "pokemon_unlocks")
