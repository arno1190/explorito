"""Ajoute Exercise.difficulty_level (difficulté fine 1-5 par exercice, issue #6).

Colonne nullable : les exercices non évalués retombent sur l'ancienne
``difficulty`` puis sur XP_PER_EXERCISE (voir gamification.xp_for_exercise).
Le remplissage des valeurs est fait par ``scripts/assess_backfill.py``.

Revision ID: a1f7c93b2d84
Revises: 9c4d2e6f1a7b
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1f7c93b2d84"
down_revision: str | Sequence[str] | None = "9c4d2e6f1a7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("difficulty_level", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "difficulty_level")
