"""
Configuration de la base de données SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Créer l'engine SQLAlchemy
engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True, echo=settings.DEBUG)

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """
    Dependency pour obtenir une session de base de données

    Yields:
        Session SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
