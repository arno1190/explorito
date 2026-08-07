"""Migration ponctuelle des comptes vers l'authentification Google.

Consolide les données sous un compte admin et nettoie les comptes obsolètes.
Entièrement paramétré par variables d'environnement (aucune donnée personnelle
en dur) :

- ``MIGRATE_ADMIN_EMAIL``   : email du compte admin cible (créé si absent).
- ``MIGRATE_ADMIN_NAME``    : nom d'affichage de l'admin (défaut "Admin").
- ``MIGRATE_KEEP_CHILDREN`` : noms d'enfants à conserver (séparés par des virgules) ;
                              ils sont rattachés à l'admin et rendus sans-connexion.
- ``MIGRATE_DELETE_EMAILS`` : emails de comptes à supprimer (séparés par des virgules).

Les enfants non listés dans KEEP_CHILDREN sont supprimés. Idempotent ;
``--dry-run`` pour simuler sans écrire.

Usage:
    MIGRATE_ADMIN_EMAIL=admin@example.com MIGRATE_KEEP_CHILDREN="Alice,Bob" \\
    DATABASE_URL=... uv run python scripts/migrate_to_google_auth.py [--dry-run]
"""

import os
import sys

from app.core.database import SessionLocal
from app.models.user import Profile, User, UserRole


def _csv_env(name: str) -> set[str]:
    return {v.strip() for v in os.environ.get(name, "").split(",") if v.strip()}


ADMIN_EMAIL = os.environ.get("MIGRATE_ADMIN_EMAIL", "admin@example.com")
ADMIN_NAME = os.environ.get("MIGRATE_ADMIN_NAME", "Admin")
KEEP_CHILDREN = _csv_env("MIGRATE_KEEP_CHILDREN")
DELETE_EMAILS = _csv_env("MIGRATE_DELETE_EMAILS")


def main(dry_run: bool = False) -> int:
    db = SessionLocal()
    log: list[str] = []
    try:
        # 1) Compte admin (sans connexion mot de passe).
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if admin is None:
            admin = User(email=ADMIN_EMAIL, role=UserRole.ADMIN, is_active=True)
            db.add(admin)
            db.flush()
            db.add(Profile(user_id=admin.id, display_name=ADMIN_NAME, is_child=False, settings={}))
            log.append(f"+ créé {ADMIN_EMAIL} (admin)")
        else:
            admin.role = UserRole.ADMIN
            log.append(f"= {ADMIN_EMAIL} déjà présent (rôle → admin)")
        db.flush()

        # 2) Rattacher les enfants conservés à l'admin + retirer leur connexion.
        children = (
            db.query(User, Profile).join(Profile, Profile.user_id == User.id).filter(Profile.is_child.is_(True)).all()
        )
        for child, profile in children:
            if profile.display_name in KEEP_CHILDREN:
                profile.parent_id = admin.id
                child.email = None
                child.password_hash = None
                log.append(f"~ enfant {profile.display_name} → parent admin (connexion retirée)")

        # 3) Supprimer les comptes listés (et les enfants non conservés).
        to_delete = db.query(User).filter(User.email.in_(DELETE_EMAILS)).all()
        orphan_children = [child for child, profile in children if profile.display_name not in KEEP_CHILDREN]
        for user in {u.id: u for u in [*to_delete, *orphan_children]}.values():
            label = user.email or f"enfant:{user.id}"
            log.append(f"- suppression {label}")
            if not dry_run:
                db.delete(user)  # cascade : profil + progression liés

        if dry_run:
            db.rollback()
        else:
            db.commit()

        print("\n".join(log))
        print(f"\n{'(dry-run) ' if dry_run else ''}Migration terminée : {len(log)} opérations.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
