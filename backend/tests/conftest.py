"""
Fixtures partagées pour les tests.

Base SQLite en mémoire (partagée via ``StaticPool`` entre la session de test et
l'application), créée/détruite par test. SQLAlchemy 2.0 compile ``postgresql.UUID``
et ``JSON`` vers des équivalents SQLite, ce qui permet des tests rapides sans
serveur Postgres.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (enregistre tous les modèles sur Base.metadata)
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Session isolée sur une base SQLite en mémoire, recréée à chaque test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """Client HTTP de test, câblé sur la session de test."""

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
