"""Environnement Alembic pour Explorito.

Câblé sur la métadonnée SQLAlchemy de l'application et sur l'URL de base de
données issue de la configuration (``settings.DATABASE_URL``). Une variable
d'environnement ``ALEMBIC_DATABASE_URL`` peut surcharger l'URL (utile pour
générer une migration contre une base jetable).
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (enregistre tous les modèles sur Base.metadata)
from alembic import context

# Importer les modèles enregistre toutes les tables sur Base.metadata.
from app.core.config import settings
from app.core.database import Base

# Objet de configuration Alembic (accès aux valeurs du .ini).
config = context.config

# URL de connexion : priorité à l'override d'environnement, sinon la config app.
database_url = os.getenv("ALEMBIC_DATABASE_URL") or str(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url)

# Logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnée cible pour l'autogénération.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline' (émission de SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online' (connexion réelle)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
