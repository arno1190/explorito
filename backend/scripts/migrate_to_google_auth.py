"""Migration des comptes vers l'authentification Google (la famille).

Consolide les données sous ``admin@example.com`` (admin) :
- crée le compte Admin s'il n'existe pas (parent/admin, sans mot de passe) ;
- rattache les enfants réels (Alice — avec toute sa progression — et Bob)
  à Admin et retire leur connexion (email/mot de passe → NULL) ;
- supprime les comptes de test/secondaires devenus inutiles
  (admin@/parent@explorito.fr, parent@example.com, parent2@example.com)
  ainsi que l'enfant vide Chloe.

Idempotent : réexécutable sans effet de bord. ``--dry-run`` pour simuler.

Usage:
    DATABASE_URL=... uv run python scripts/migrate_to_google_auth.py [--dry-run]
"""

import sys

from app.core.database import SessionLocal
from app.models.user import Profile, User, UserRole

ADMIN_EMAIL = "admin@example.com"
# Enfants (par nom d'affichage) à conserver sous Admin.
KEEP_CHILDREN = {"Alice", "Bob"}
# Comptes à supprimer (emails).
DELETE_EMAILS = {
    "admin@explorito.fr",
    "parent@explorito.fr",
    "parent@example.com",
    "parent2@example.com",
}


def main(dry_run: bool = False) -> int:
    db = SessionLocal()
    log: list[str] = []
    try:
        # 1) Compte Admin (admin, sans connexion mot de passe).
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if admin is None:
            admin = User(email=ADMIN_EMAIL, role=UserRole.ADMIN, is_active=True)
            db.add(admin)
            db.flush()
            db.add(Profile(user_id=admin.id, display_name="Admin", is_child=False, settings={}))
            log.append(f"+ créé {ADMIN_EMAIL} (admin)")
        else:
            admin.role = UserRole.ADMIN
            log.append(f"= {ADMIN_EMAIL} déjà présent (rôle → admin)")
        db.flush()

        # 2) Rattacher les enfants réels à Admin + retirer leur connexion.
        children = (
            db.query(User, Profile).join(Profile, Profile.user_id == User.id).filter(Profile.is_child.is_(True)).all()
        )
        for child, profile in children:
            if profile.display_name in KEEP_CHILDREN:
                profile.parent_id = admin.id
                child.email = None
                child.password_hash = None
                log.append(f"~ enfant {profile.display_name} → parent Admin (connexion retirée)")

        # 3) Supprimer les comptes de test/secondaires (et enfants vides orphelins).
        to_delete = db.query(User).filter(User.email.in_(DELETE_EMAILS)).all()
        # Enfants restants non conservés (ex. Chloe) → suppression.
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
