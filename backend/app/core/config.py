"""
Configuration de l'application
Gère toutes les variables d'environnement et paramètres globaux
"""

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings

# Valeur par défaut volontairement non sécurisée : elle ne doit JAMAIS servir
# en production. Le validateur ci-dessous fait échouer le démarrage si elle
# reste en place hors mode DEBUG.
INSECURE_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"


class Settings(BaseSettings):
    """Configuration globale de l'application"""

    # Application
    APP_NAME: str = "Explorito - Application Éducative"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = INSECURE_DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 heures
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: PostgresDsn = "postgresql://explorito:explorito123@localhost:5432/explorito"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Gamification
    XP_PER_EXERCISE: int = 10
    XP_PER_LESSON: int = 50
    XP_LEVEL_MULTIPLIER: int = 100  # Level N = N * 100 XP
    # Anti-farm : refaire un exercice déjà raté ne rapporte qu'une fraction de
    # l'XP (0.0–1.0) ; un exercice déjà réussi ne rapporte plus rien.
    XP_REDO_DISCOUNT: float = 0.5
    # Défi Pythagore : XP de base par bonne réponse selon la difficulté, bonus de
    # série, pénalité par erreur, et plafond quotidien anti-farm.
    PYTHAGORE_BASE_XP_EASY: int = 2
    PYTHAGORE_BASE_XP_MEDIUM: int = 3
    PYTHAGORE_BASE_XP_HARD: int = 4
    PYTHAGORE_STREAK_BONUS: int = 1  # +XP par bonne réponse au-delà de 2 d'affilée
    PYTHAGORE_FAILURE_PENALTY: int = 1  # −XP par erreur (payout planché à 0)
    PYTHAGORE_DAILY_XP_CAP: int = 100  # XP max/jour gagnable via les défis Pythagore

    @model_validator(mode="after")
    def _enforce_secure_secret_key(self) -> "Settings":
        """Refuse de démarrer en production avec la clé secrète par défaut."""
        if not self.DEBUG and self.SECRET_KEY == INSECURE_DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY doit être défini via l'environnement en production "
                "(DEBUG=false). Générez-en une avec `openssl rand -hex 32`."
            )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
