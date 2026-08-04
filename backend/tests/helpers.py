"""Utilitaires de test pour le modèle d'authentification Google-only.

Les enfants n'ont plus de connexion : on s'authentifie en **parent** via
``/auth/dev-login`` (monté uniquement si DEBUG) et on « incarne » l'enfant avec
l'en-tête ``X-Acting-Child-Id``. Ces helpers factorisent ce schéma.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import LevelEnum
from app.models.user import Profile, User, UserRole

DEFAULT_PARENT_EMAIL = "parent@qa.fr"


def dev_login(client: TestClient, email: str = DEFAULT_PARENT_EMAIL) -> dict[str, str]:
    """Connexion de test (parent) → en-têtes d'autorisation."""
    r = client.post("/api/v1/auth/dev-login", json={"email": email})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def ensure_parent(db: Session, email: str = DEFAULT_PARENT_EMAIL) -> User:
    """Récupère ou crée un compte parent (avec profil)."""
    parent = db.query(User).filter(User.email == email).first()
    if parent is None:
        parent = User(email=email, role=UserRole.PARENT, is_active=True)
        db.add(parent)
        db.flush()
        db.add(Profile(user_id=parent.id, display_name="Parent", is_child=False))
        db.commit()
        db.refresh(parent)
    return parent


def make_child(
    db: Session,
    *,
    level: LevelEnum = LevelEnum.CP,
    parent_email: str = DEFAULT_PARENT_EMAIL,
    name: str = "Kid",
) -> User:
    """Crée un enfant sans connexion, rattaché à un parent (créé au besoin)."""
    parent = ensure_parent(db, parent_email)
    child = User(email=None, role=UserRole.CHILD, is_active=True)
    db.add(child)
    db.flush()
    db.add(
        Profile(
            user_id=child.id,
            display_name=name,
            is_child=True,
            parent_id=parent.id,
            level=level,
        )
    )
    db.commit()
    db.refresh(child)
    return child


def child_headers(client: TestClient, child: User, *, parent_email: str = DEFAULT_PARENT_EMAIL) -> dict[str, str]:
    """En-têtes d'un parent incarnant ``child`` (auth parent + X-Acting-Child-Id)."""
    headers = dev_login(client, parent_email)
    headers["X-Acting-Child-Id"] = str(child.id)
    return headers
