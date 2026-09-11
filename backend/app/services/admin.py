"""Service d'administration : journal de connexion, métriques d'usage, gestion des comptes.

Contient aussi le **chemin unique de suppression d'un compte**
(:func:`delete_child_account`, :func:`delete_user`). La politique de
confidentialité promet un effacement complet et immédiat : un seul chemin, qui
nettoie la base *et* les fichiers, est la seule façon de tenir cette promesse
depuis toutes les surfaces (tableau de bord parent, console admin).
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.admin import LoginEvent
from app.models.guardianship import CoParentLink, Guardianship, Invitation
from app.models.progress import ExerciseResult
from app.models.user import Profile, User, UserRole
from app.services.uploads import delete_upload

logger = logging.getLogger("explorito.admin")

RETENTION_DAYS = 90


def record_login(db: Session, user: User) -> None:
    """Enregistre une connexion (parent/admin) : event + compteur + dernière date.

    Purge opportuniste des events au-delà de la rétention (90 j).
    """
    now = datetime.utcnow()
    db.add(LoginEvent(user_id=user.id, created_at=now))
    user.login_count = (user.login_count or 0) + 1
    user.last_login_at = now
    db.query(LoginEvent).filter(LoginEvent.created_at < now - timedelta(days=RETENTION_DAYS)).delete(
        synchronize_session=False
    )
    db.commit()


def _active_count(db: Session, model_ts, model_uid, since: datetime) -> int:
    return db.query(func.count(func.distinct(model_uid))).filter(model_ts >= since).scalar() or 0


def overview(db: Session) -> dict:
    """Métriques opérationnelles pour le tableau de bord admin."""
    now = datetime.utcnow()
    d7, d30 = now - timedelta(days=7), now - timedelta(days=30)

    parents_total = db.query(func.count(User.id)).filter(User.role.in_([UserRole.PARENT, UserRole.ADMIN])).scalar() or 0
    children_total = db.query(func.count(User.id)).filter(User.role == UserRole.CHILD).scalar() or 0
    families_total = db.query(func.count(func.distinct(Guardianship.child_id))).scalar() or 0

    active_parents_7d = _active_count(db, LoginEvent.created_at, LoginEvent.user_id, d7)
    active_parents_30d = _active_count(db, LoginEvent.created_at, LoginEvent.user_id, d30)
    active_children_7d = _active_count(db, ExerciseResult.timestamp, ExerciseResult.user_id, d7)
    active_children_30d = _active_count(db, ExerciseResult.timestamp, ExerciseResult.user_id, d30)

    exercises_total = db.query(func.count(ExerciseResult.id)).scalar() or 0
    exercises_7d = db.query(func.count(ExerciseResult.id)).filter(ExerciseResult.timestamp >= d7).scalar() or 0
    exercises_30d = db.query(func.count(ExerciseResult.id)).filter(ExerciseResult.timestamp >= d30).scalar() or 0

    # Activité récente : fusionne les connexions parents et les sessions
    # d'exercices des enfants (les enfants n'ont pas de connexion — sans cela
    # l'activité d'un enfant « disparaîtrait » derrière la connexion du parent).
    logins = (
        db.query(LoginEvent.created_at, User.email)
        .join(User, User.id == LoginEvent.user_id)
        .order_by(LoginEvent.created_at.desc())
        .limit(12)
        .all()
    )
    activity: list[dict] = [
        {"kind": "login", "label": email or "—", "detail": "Connexion", "at": at} for at, email in logins
    ]
    # Sessions d'exercices agrégées par (enfant, jour).
    day = func.date(ExerciseResult.timestamp)
    sessions = (
        db.query(Profile.display_name, func.max(ExerciseResult.timestamp), func.count(ExerciseResult.id))
        .join(Profile, Profile.user_id == ExerciseResult.user_id)
        .group_by(Profile.display_name, day)
        .order_by(func.max(ExerciseResult.timestamp).desc())
        .limit(12)
        .all()
    )
    for name, last, cnt in sessions:
        activity.append(
            {"kind": "exercise", "label": name or "—", "detail": f"{cnt} exercice{'s' if cnt > 1 else ''}", "at": last}
        )
    activity.sort(key=lambda a: a["at"], reverse=True)
    recent_activity = activity[:12]

    return {
        "parents_total": parents_total,
        "children_total": children_total,
        "families_total": families_total,
        "active_parents_7d": active_parents_7d,
        "active_parents_30d": active_parents_30d,
        "active_children_7d": active_children_7d,
        "active_children_30d": active_children_30d,
        "exercises_total": exercises_total,
        "exercises_7d": exercises_7d,
        "exercises_30d": exercises_30d,
        "recent_activity": recent_activity,
    }


def list_users(db: Session) -> list[dict]:
    """Tous les comptes avec statut et activité, pour la gestion admin."""
    # Activité enfant : dernier exercice + total, agrégés par utilisateur.
    ex_stats = {
        uid: (last, cnt)
        for uid, last, cnt in db.query(
            ExerciseResult.user_id, func.max(ExerciseResult.timestamp), func.count(ExerciseResult.id)
        ).group_by(ExerciseResult.user_id)
    }
    profiles = {p.user_id: p for p in db.query(Profile).all()}
    rows: list[dict] = []
    for u in db.query(User).order_by(User.created_at.asc()).all():
        prof = profiles.get(u.id)
        last_ex, ex_count = ex_stats.get(u.id, (None, 0))
        rows.append(
            {
                "id": u.id,
                "email": u.email,
                "name": prof.display_name if prof else (u.email or "—"),
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at,
                "last_login_at": u.last_login_at,
                "login_count": u.login_count or 0,
                "last_exercise_at": last_ex,
                "exercises_count": ex_count,
            }
        )
    return rows


def set_active(db: Session, user_id: UUID, active: bool) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None
    user.is_active = active
    db.commit()
    db.refresh(user)
    return user


def delete_child_account(db: Session, child: User) -> None:
    """Supprime définitivement un enfant : base **et** fichiers.

    Chemin unique de suppression d'un enfant, utilisé par le tableau de bord du
    parent comme par la suppression d'un compte adulte. La progression part en
    cascade par les relations du modèle ; les liens de garde et l'image
    d'avatar, eux, ne cascadent pas côté ORM et sont nettoyés ici — sans quoi
    l'avatar resterait servi par le montage statique ``/uploads`` bien après la
    disparition de l'enfant, ce que la politique de confidentialité interdit.

    Args:
        db: Session ouverte ; la transaction est validée par la fonction.
        child: Le compte enfant à effacer.
    """
    profile = db.query(Profile).filter(Profile.user_id == child.id).first()
    avatar_url = profile.avatar_url if profile else None

    db.query(Guardianship).filter(Guardianship.child_id == child.id).delete(synchronize_session=False)
    db.query(Invitation).filter(Invitation.child_id == child.id).delete(synchronize_session=False)
    db.delete(child)  # cascade ORM : profil, progression, résultats, séries, collection
    db.commit()

    # Après le commit seulement : un fichier effacé alors que la transaction
    # échoue laisserait une ligne sans image, l'inverse est rattrapable.
    if delete_upload(avatar_url):
        logger.info("Avatar supprimé du disque pour l'enfant %s", child.id)


def _children_of(db: Session, guardian_id: UUID) -> list[UUID]:
    """IDs des enfants rattachés à un adulte (garde partagée ou lien historique)."""
    by_guardianship = {
        row[0] for row in db.query(Guardianship.child_id).filter(Guardianship.guardian_id == guardian_id).all()
    }
    by_profile = {row[0] for row in db.query(Profile.user_id).filter(Profile.parent_id == guardian_id).all()}
    return sorted(by_guardianship | by_profile, key=str)


def _has_remaining_guardian(db: Session, child_id: UUID) -> bool:
    """Vrai si un adulte est encore rattaché à cet enfant."""
    if db.query(Guardianship).filter(Guardianship.child_id == child_id).count():
        return True
    profile = db.query(Profile).filter(Profile.user_id == child_id).first()
    return profile is not None and profile.parent_id is not None


def delete_user(db: Session, user_id: UUID) -> bool:
    """Suppression définitive d'un compte, de ses données et de ses enfants orphelins.

    Ce que la politique de confidentialité promet, et donc ce qui est fait ici :
    les enfants de l'adulte partent avec lui **sauf** s'il reste un autre
    responsable (garde partagée). Sans ce tri, ``profiles.parent_id`` étant
    ``ON DELETE SET NULL``, les comptes enfants et tout leur travail scolaire
    survivraient en orphelins que plus personne ne peut ni voir ni supprimer ;
    à l'inverse, tout supprimer effacerait l'enfant qu'un co-parent suit encore.

    Args:
        db: Session ouverte ; la transaction est validée par la fonction.
        user_id: Le compte à effacer.

    Returns:
        ``False`` si le compte n'existe pas, ``True`` s'il a été supprimé.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False
    # RGPD : les packs de l'auteur survivent **anonymisés**. Les supprimer
    # effacerait la progression d'enfants d'autres familles ; s'appuyer sur le
    # seul ``ON DELETE SET NULL`` perdrait l'attribution (pseudonyme) des packs
    # qui n'en portent pas encore. Import local : évite un cycle avec la
    # modération, qui dépend déjà de ce module par ailleurs.
    from app.services.moderation import anonymise_author

    anonymise_author(db, user_id=user_id)

    child_ids = _children_of(db, user.id)
    # Détacher d'abord : ce que ``ON DELETE CASCADE``/``SET NULL`` feraient de
    # toute façon, mais fait explicitement pour que le tri ci-dessous voie
    # l'état d'après-départ, y compris là où les FK ne sont pas appliquées.
    db.query(Guardianship).filter(Guardianship.guardian_id == user.id).delete(synchronize_session=False)
    db.query(CoParentLink).filter((CoParentLink.owner_id == user.id) | (CoParentLink.coparent_id == user.id)).delete(
        synchronize_session=False
    )
    db.query(Invitation).filter(Invitation.inviter_id == user.id).delete(synchronize_session=False)
    db.query(Profile).filter(Profile.parent_id == user.id).update({Profile.parent_id: None}, synchronize_session=False)
    db.flush()

    for child_id in child_ids:
        if _has_remaining_guardian(db, child_id):
            continue
        child = db.query(User).filter(User.id == child_id, User.role == UserRole.CHILD).first()
        if child is not None:
            delete_child_account(db, child)

    db.delete(user)
    db.commit()
    return True
