"""
Logique de verrouillage/déverrouillage des leçons — source de vérité unique.

La progression par paliers (« tiers ») est libre au sein d'un palier (order_index
identique, choisis dans n'importe quel ordre) mais un palier ne se déverrouille
que lorsque toutes les leçons publiées des paliers inférieurs (même parcours) sont
terminées (``UserProgress.status == COMPLETED``).

Ce module est consommé à la fois par le fil « Nouveautés » (``/lessons/recent``),
la liste des leçons d'une matière (``/subjects/{id}/lessons``) et l'application du
verrou côté serveur (soumission d'exercice), afin qu'aucune logique dupliquée ne
puisse diverger.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.content import LearningPath, Lesson, LevelEnum
from app.models.progress import ProgressStatus, UserProgress


def lesson_locked(user_id: UUID, lesson: Lesson, level: LevelEnum | None, db: Session) -> bool:
    """
    Indique si une leçon est verrouillée pour l'utilisateur.

    Verrouillée si, dans le même parcours, une leçon publiée de palier inférieur
    (``order_index`` strictement plus petit) n'est pas encore terminée. Le palier
    le plus bas, ainsi que les parents/admins (``level`` à ``None``), ne sont
    jamais verrouillés.

    Args:
        user_id: ID de l'utilisateur.
        lesson: Leçon dont on évalue le verrou.
        level: Niveau de contenu de l'utilisateur (``None`` = pas de filtrage).
        db: Session de base de données.

    Returns:
        ``True`` si la leçon est verrouillée, ``False`` sinon.
    """
    if level is None:
        return False
    lower_ids = {
        row[0]
        for row in db.query(Lesson.id).filter(
            Lesson.path_id == lesson.path_id,
            Lesson.order_index < lesson.order_index,
            Lesson.is_published.is_(True),
        )
    }
    if not lower_ids:
        return False
    completed_ids = {
        row[0]
        for row in db.query(UserProgress.lesson_id).filter(
            UserProgress.user_id == user_id,
            UserProgress.lesson_id.in_(lower_ids),
            UserProgress.status == ProgressStatus.COMPLETED,
        )
    }
    return not lower_ids.issubset(completed_ids)


def lesson_locked_by_id(user_id: UUID, lesson_id: UUID, level: LevelEnum | None, db: Session) -> bool:
    """Variante par ID : charge la leçon (+ parcours) puis délègue à :func:`lesson_locked`."""
    if level is None:
        return False
    lesson = (
        db.query(Lesson).join(LearningPath, Lesson.path_id == LearningPath.id).filter(Lesson.id == lesson_id).first()
    )
    if lesson is None:
        return False
    return lesson_locked(user_id, lesson, level, db)
