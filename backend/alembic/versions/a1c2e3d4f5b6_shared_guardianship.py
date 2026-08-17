"""shared guardianship (guardianships, co_parent_links, invitations)

Revision ID: a1c2e3d4f5b6
Revises: 6512370fd641
Create Date: 2026-08-17 09:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1c2e3d4f5b6"
down_revision: str | Sequence[str] | None = "6512370fd641"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée les tables de garde partagée et rétro-remplit les propriétaires."""
    op.create_table(
        "guardianships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=False),
        sa.Column("guardian_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("child_id", "guardian_id", name="uq_guardianship_child_guardian"),
    )
    op.create_index(op.f("ix_guardianships_id"), "guardianships", ["id"], unique=False)
    op.create_index(op.f("ix_guardianships_child_id"), "guardianships", ["child_id"], unique=False)
    op.create_index(op.f("ix_guardianships_guardian_id"), "guardianships", ["guardian_id"], unique=False)

    op.create_table(
        "co_parent_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("coparent_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["coparent_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "coparent_id", name="uq_coparent_owner_coparent"),
    )
    op.create_index(op.f("ix_co_parent_links_id"), "co_parent_links", ["id"], unique=False)
    op.create_index(op.f("ix_co_parent_links_owner_id"), "co_parent_links", ["owner_id"], unique=False)
    op.create_index(op.f("ix_co_parent_links_coparent_id"), "co_parent_links", ["coparent_id"], unique=False)

    op.create_table(
        "invitations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("inviter_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("child_id", sa.UUID(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_by", sa.UUID(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["accepted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invitations_id"), "invitations", ["id"], unique=False)
    op.create_index(op.f("ix_invitations_token"), "invitations", ["token"], unique=True)
    op.create_index(op.f("ix_invitations_inviter_id"), "invitations", ["inviter_id"], unique=False)

    # Rétro-remplissage : chaque enfant existant → garde 'owner' pour son parent_id.
    op.execute(
        """
        INSERT INTO guardianships (id, child_id, guardian_id, role, created_at)
        SELECT gen_random_uuid(), p.user_id, p.parent_id, 'owner', now()
        FROM profiles p
        WHERE p.is_child = true AND p.parent_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Supprime les tables de garde partagée."""
    op.drop_index(op.f("ix_invitations_inviter_id"), table_name="invitations")
    op.drop_index(op.f("ix_invitations_token"), table_name="invitations")
    op.drop_index(op.f("ix_invitations_id"), table_name="invitations")
    op.drop_table("invitations")
    op.drop_index(op.f("ix_co_parent_links_coparent_id"), table_name="co_parent_links")
    op.drop_index(op.f("ix_co_parent_links_owner_id"), table_name="co_parent_links")
    op.drop_index(op.f("ix_co_parent_links_id"), table_name="co_parent_links")
    op.drop_table("co_parent_links")
    op.drop_index(op.f("ix_guardianships_guardian_id"), table_name="guardianships")
    op.drop_index(op.f("ix_guardianships_child_id"), table_name="guardianships")
    op.drop_index(op.f("ix_guardianships_id"), table_name="guardianships")
    op.drop_table("guardianships")
