"""Service d'administration : journal de connexion, métriques d'usage, gestion des comptes."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.admin import LoginEvent
from app.models.guardianship import Guardianship
from app.models.progress import ExerciseResult
from app.models.user import Profile, User, UserRole

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

    recent = (
        db.query(LoginEvent.created_at, User.email)
        .join(User, User.id == LoginEvent.user_id)
        .order_by(LoginEvent.created_at.desc())
        .limit(10)
        .all()
    )
    recent_logins = [{"email": email, "at": at} for at, email in recent]

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
        "recent_logins": recent_logins,
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


def delete_user(db: Session, user_id: UUID) -> bool:
    """Suppression définitive (cascade FK) d'un compte et de ses données."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return False
    db.delete(user)
    db.commit()
    return True
