"""Substrat des packs communautaires : packs, accès enfant, contribution, annonces.

Revision ID: d4a1c9e05b21
Revises: b7d1f0a9c2e4
Create Date: 2026-09-03 08:10:00.000000

Migration en gros (« wholesale ») : un pack ``official`` par couple
(matière, niveau) réellement présent dans le contenu, puis ``lessons.pack_id``
passé en ``NOT NULL``. Aucun changement visible pour l'utilisateur — juste après
la reprise, un pack *est* la totalité d'une matière+niveau, donc la portée du
verrou de progression est identique à l'ancienne portée « parcours ».

Le regroupement thématique fin viendra ensuite : c'est un simple ``UPDATE`` de
``lessons.pack_id`` qui ne touche jamais ``lessons.id``, donc ni
``user_progress`` ni ``exercise_results``.

Idempotence : les identifiants des packs officiels sont dérivés (``uuid5``) de
``official:<subject_id>:<level>``, donc rejouer la reprise ne duplique rien.
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a1c9e05b21"
down_revision: str | Sequence[str] | None = "b7d1f0a9c2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Espace de noms fixe pour dériver les identifiants des packs officiels.
PACK_NAMESPACE = uuid.UUID("6f1b2c94-8a1d-4f7e-9c3b-2f5d7a0e91c4")

# Niveau de repli si un parcours n'en déclare pas (la colonne est nullable).
FALLBACK_LEVEL = "CP"


def official_pack_id(subject_id: str, level: str) -> uuid.UUID:
    """Identifiant déterministe du pack officiel d'un couple (matière, niveau)."""
    return uuid.uuid5(PACK_NAMESPACE, f"official:{subject_id}:{level}")


def upgrade() -> None:
    """Crée le substrat des packs et rattache tout le contenu existant."""
    # ``sa.Enum(name=...)`` générique émettrait un ``CREATE TYPE levelenum AS
    # ENUM ()`` : seul le type du dialecte respecte ``create_type=False`` et
    # réutilise donc l'énumération déjà créée par la migration initiale.
    level_enum = postgresql.ENUM(name="levelenum", create_type=False)

    op.create_table(
        "packs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("emoji", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("origin", sa.String(), nullable=False, server_default="community"),
        sa.Column("author_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("author_handle", sa.String(), nullable=True),
        sa.Column("community_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("difficulty_ratified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("quality_score", sa.SmallInteger(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("level_min", level_enum, nullable=False, server_default=FALLBACK_LEVEL),
        sa.Column("level_max", level_enum, nullable=False, server_default=FALLBACK_LEVEL),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cloned_from_pack_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cloned_from_pack_id"], ["packs.id"], ondelete="SET NULL"),
        sa.CheckConstraint("origin IN ('official', 'community')", name="ck_packs_origin"),
        sa.CheckConstraint(
            "community_status IN ('draft', 'pending', 'approved', 'rejected', 'blocked')",
            name="ck_packs_community_status",
        ),
    )
    op.create_index("ix_packs_origin", "packs", ["origin"])
    op.create_index("ix_packs_community_status", "packs", ["community_status"])
    op.create_index("ix_packs_author_id", "packs", ["author_id"])

    # --- lessons.pack_id : d'abord nullable, le temps de la reprise ---
    op.add_column("lessons", sa.Column("pack_id", sa.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_lessons_pack_id",
        "lessons",
        "packs",
        ["pack_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_lessons_pack_id", "lessons", ["pack_id"])

    _backfill_official_packs()

    op.alter_column("lessons", "pack_id", existing_type=sa.UUID(as_uuid=True), nullable=False)

    # --- Accès par enfant (liste blanche) ---
    op.create_table(
        "child_pack_access",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("enabled_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pack_id"], ["packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enabled_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("child_id", "pack_id", name="uq_child_pack_access"),
    )
    op.create_index("ix_child_pack_access_child_id", "child_pack_access", ["child_id"])
    op.create_index("ix_child_pack_access_pack_id", "child_pack_access", ["pack_id"])

    # --- Demandes « Je veux ça ! » ---
    op.create_table(
        "pack_requests",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("child_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("pack_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pack_id"], ["packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_pack_requests_child_id", "pack_requests", ["child_id"])
    op.create_index("ix_pack_requests_pack_id", "pack_requests", ["pack_id"])
    op.create_index("ix_pack_requests_status", "pack_requests", ["status"])

    # --- Contributeurs : pseudonyme, conditions acceptées, palier de confiance ---
    op.create_table(
        "contributor_profiles",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("handle", sa.String(), nullable=False),
        sa.Column("terms_version", sa.String(), nullable=True),
        sa.Column("terms_accepted_at", sa.DateTime(), nullable=True),
        sa.Column("trusted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("trusted_at", sa.DateTime(), nullable=True),
        sa.Column("trusted_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trusted_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="uq_contributor_user"),
        sa.UniqueConstraint("handle", name="uq_contributor_handle"),
    )
    op.create_index("ix_contributor_profiles_handle", "contributor_profiles", ["handle"])

    # --- Jetons d'envoi (brouillons uniquement) ---
    op.create_table(
        "upload_tokens",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("prefix", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_upload_token_hash"),
    )
    op.create_index("ix_upload_tokens_user_id", "upload_tokens", ["user_id"])

    # --- Signalements ---
    op.create_table(
        "pack_reports",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("pack_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("reporter_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["pack_id"], ["packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_pack_reports_pack_id", "pack_reports", ["pack_id"])
    op.create_index("ix_pack_reports_status", "pack_reports", ["status"])

    # --- Journal d'audit des packs ---
    op.create_table(
        "pack_audit_log",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("pack_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["pack_id"], ["packs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_pack_audit_log_pack_id", "pack_audit_log", ["pack_id"])
    op.create_index("ix_pack_audit_log_action", "pack_audit_log", ["action"])
    op.create_index("ix_pack_audit_log_created_at", "pack_audit_log", ["created_at"])

    # --- Quotas d'envoi journaliers ---
    op.create_table(
        "contribution_quotas",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("day", sa.String(), nullable=False),
        sa.Column("uploads", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "day", name="uq_contribution_quota_user_day"),
    )
    op.create_index("ix_contribution_quotas_user_id", "contribution_quotas", ["user_id"])

    # --- Annonces email ---
    op.create_table(
        "announcements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("body_markdown", sa.Text(), nullable=False),
        sa.Column("from_email", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_announcements_status", "announcements", ["status"])

    op.create_table(
        "announcement_deliveries",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("announcement_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("announcement_id", "email", name="uq_delivery_announcement_email"),
    )
    op.create_index("ix_announcement_deliveries_announcement_id", "announcement_deliveries", ["announcement_id"])
    op.create_index("ix_announcement_deliveries_status", "announcement_deliveries", ["status"])

    # --- Préférences ---
    op.add_column(
        "users",
        sa.Column("email_opt_out", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "profiles",
        sa.Column("pack_lens", sa.String(), nullable=False, server_default="themes"),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "auto_enable_approved_packs",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def _backfill_official_packs() -> None:
    """Crée un pack ``official`` par (matière, niveau) et y rattache les leçons.

    Rejouable : l'identifiant de chaque pack est dérivé du couple, et les
    ``UPDATE`` ne touchent que les leçons encore sans pack.
    """
    bind = op.get_bind()
    pairs = bind.execute(
        sa.text(
            """
            SELECT DISTINCT s.id AS subject_id,
                            s.name AS subject_name,
                            s.icon AS subject_icon,
                            s.order_index AS subject_order,
                            COALESCE(CAST(lp.level AS VARCHAR), :fallback) AS level
            FROM learning_paths lp
            JOIN subjects s ON s.id = lp.subject_id
            ORDER BY s.order_index, level
            """
        ),
        {"fallback": FALLBACK_LEVEL},
    ).fetchall()

    for row in pairs:
        subject_id = str(row.subject_id)
        level = row.level or FALLBACK_LEVEL
        pack_id = official_pack_id(subject_id, level)
        title = f"{row.subject_name} — {level.upper()}"

        bind.execute(
            sa.text(
                """
                INSERT INTO packs (
                    id, title, emoji, description, origin, author_handle,
                    community_status, difficulty_ratified, locked, tags, warnings,
                    level_min, level_max, order_index
                )
                SELECT :id, :title, :emoji, :description, 'official', 'Explorito',
                       'approved', TRUE, FALSE, :tags, :warnings,
                       :level, :level, :order_index
                WHERE NOT EXISTS (SELECT 1 FROM packs WHERE id = :id)
                """
            ),
            {
                "id": pack_id,
                "title": title,
                "emoji": row.subject_icon,
                "description": f"Contenu officiel Explorito — {row.subject_name}, niveau {level.upper()}.",
                "tags": "[]",
                "warnings": "[]",
                "level": level,
                "order_index": row.subject_order or 0,
            },
        )

        bind.execute(
            sa.text(
                """
                UPDATE lessons
                SET pack_id = :pack_id
                WHERE pack_id IS NULL
                  AND path_id IN (
                      SELECT lp.id FROM learning_paths lp
                      WHERE lp.subject_id = :subject_id
                        AND COALESCE(CAST(lp.level AS VARCHAR), :fallback) = :level
                  )
                """
            ),
            {
                "pack_id": pack_id,
                "subject_id": row.subject_id,
                "level": level,
                "fallback": FALLBACK_LEVEL,
            },
        )

    orphans = bind.execute(sa.text("SELECT COUNT(*) FROM lessons WHERE pack_id IS NULL")).scalar_one()
    if orphans:
        raise RuntimeError(
            f"{orphans} leçon(s) sans pack après la reprise : la contrainte NOT NULL échouerait. "
            "Vérifier les parcours orphelins avant de rejouer la migration."
        )


def downgrade() -> None:
    """Retire le substrat des packs (le contenu et la progression sont intacts)."""
    op.drop_column("profiles", "auto_enable_approved_packs")
    op.drop_column("profiles", "pack_lens")
    op.drop_column("users", "email_opt_out")

    op.drop_table("announcement_deliveries")
    op.drop_table("announcements")
    op.drop_table("contribution_quotas")
    op.drop_table("pack_audit_log")
    op.drop_table("pack_reports")
    op.drop_table("upload_tokens")
    op.drop_table("contributor_profiles")
    op.drop_table("pack_requests")
    op.drop_table("child_pack_access")

    op.drop_index("ix_lessons_pack_id", table_name="lessons")
    op.drop_constraint("fk_lessons_pack_id", "lessons", type_="foreignkey")
    op.drop_column("lessons", "pack_id")

    op.drop_table("packs")
