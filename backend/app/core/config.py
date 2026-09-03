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

    # Authentification Google (Google Identity Services, flux id_token).
    # Client ID OAuth « Web » public ; sert d'audience à la vérification du jeton.
    GOOGLE_CLIENT_ID: str = ""
    # Emails (séparés par des virgules) promus au rôle admin à la connexion.
    ADMIN_EMAILS: str = ""

    @property
    def admin_emails_set(self) -> set[str]:
        """Ensemble normalisé (minuscules) des emails administrateurs."""
        return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}

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
    XP_PER_EXERCISE: int = 10  # tarif par défaut / repli (difficulté « easy »)
    XP_PER_LESSON: int = 50
    XP_LEVEL_MULTIPLIER: int = 100  # Level N = N * 100 XP
    # XP de base par bonne réponse selon la difficulté fine de l'exercice
    # (difficulty_level 1→5, évalué par exercice, relatif au niveau scolaire).
    # Source de vérité de l'XP par exercice (issue #6).
    XP_BY_LEVEL: dict[int, int] = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}
    # Repli hérité : ancienne difficulté à 3 niveaux, utilisée uniquement si
    # difficulty_level n'est pas renseignée. Repli final : XP_PER_EXERCISE.
    XP_BY_DIFFICULTY: dict[str, int] = {"easy": 10, "medium": 20, "hard": 30}
    # Bonus forfaitaire à la complétion d'une leçon (lesson.xp_reward). Désactivé
    # par défaut (issue #6) : l'XP provient uniquement des exercices, pondérée par
    # la difficulté. Passer à True restaure l'ancien comportement.
    AWARD_LESSON_COMPLETION_BONUS: bool = False
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

    # ----------------------------------------------------------------- #
    # Packs communautaires (issues #7–#20)
    # ----------------------------------------------------------------- #
    # Version du format `.explorito` produite et acceptée. Une version inconnue
    # est refusée proprement plutôt que devinée.
    PACK_FORMAT_VERSION: int = 1
    # Plafonds durs, appliqués côté serveur (refus). Ils bornent le coût d'un
    # envoi hostile ou simplement délirant ; ce ne sont pas des règles de qualité.
    PACK_MAX_LESSONS: int = 12
    PACK_MAX_EXERCISES_PER_LESSON: int = 20
    PACK_MAX_TEXT_LENGTH: int = 2000
    PACK_MAX_FILE_SIZE: int = 512 * 1024
    PACK_MAX_TAGS: int = 8
    # Limitation de débit par compte.
    PACK_MAX_UPLOADS_PER_DAY: int = 5
    PACK_MAX_PENDING: int = 3
    # Demandes « Je veux ça ! » par enfant et par jour (sinon trente en attente).
    PACK_MAX_REQUESTS_PER_CHILD_PER_DAY: int = 3
    # Nombre de packs approuvés à partir duquel un auteur devient « de confiance »
    # (publication directe, contrôle a posteriori). Promotion explicite et révocable.
    PACK_TRUST_THRESHOLD: int = 3
    # Version des conditions de contribution acceptées au premier envoi.
    CONTRIBUTOR_TERMS_VERSION: str = "2026-09-01"
    # Jeton de modération : porte d'entrée *uniquement* sur /moderation/*, jamais
    # sur la suppression d'utilisateur ni l'incarnation. Vide = surface désactivée.
    MODERATION_TOKEN: str = ""

    # ----------------------------------------------------------------- #
    # Email (annonces produit)
    # ----------------------------------------------------------------- #
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    MAIL_FROM: str = "arnaud@pascalfamily.fr"
    MAIL_FROM_NAME: str = "Explorito"
    MAIL_REPLY_TO: str = "arnaud@pascalfamily.fr"
    # URL publique de l'application, utilisée dans les liens des emails et les
    # URLs d'aperçu renvoyées aux outils d'envoi.
    PUBLIC_APP_URL: str = "http://localhost:3005"

    @property
    def mail_configured(self) -> bool:
        """Vrai si un serveur SMTP est configuré (sinon l'envoi est refusé net)."""
        return bool(self.SMTP_HOST and self.MAIL_FROM)

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
