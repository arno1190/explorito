"""
Logique de verrouillage/déverrouillage des leçons — source de vérité unique.

La progression par paliers (« tiers ») est libre au sein d'un palier (order_index
identique, choisis dans n'importe quel ordre) mais un palier ne se déverrouille
que lorsque toutes les leçons publiées des paliers inférieurs **du même pack**
sont terminées (``UserProgress.status == COMPLETED``).

La portée est le pack, et non le parcours, pour deux raisons :

* un auteur a séquencé *son* pack du plus facile au plus difficile, donc l'ordre
  y est un vrai signal pédagogique ; ordonner deux thèmes sans rapport l'un
  contre l'autre (« Coupe du Monde » avant « Les Dinosaures ») serait un tirage
  au sort déguisé en progression ;
* à l'échelle du parcours, le verrou dépend du **volume de contenu** : un enfant
  ne pourrait atteindre le palier 2 qu'après avoir terminé toutes les leçons de
  palier 1 déposées par des inconnus. Coupler les déverrouillages à ce que la
  communauté téléverse ne survit pas à la contribution ouverte.

Ce module est consommé à la fois par le fil « Nouveautés » (``/lessons/recent``),
la liste des leçons d'une matière (``/subjects/{id}/lessons``) et l'application du
verrou côté serveur (soumission d'exercice), afin qu'aucune logique dupliquée ne
puisse diverger.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.content import Lesson, LevelEnum
from app.models.progress import ProgressStatus, UserProgress


def lesson_locked(user_id: UUID, lesson: Lesson, level: LevelEnum | None, db: Session) -> bool:
    """
    Indique si une leçon est verrouillée pour l'utilisateur.

    Verrouillée si, dans le même **pack**, une leçon publiée de palier inférieur
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
            Lesson.pack_id == lesson.pack_id,
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
    """Variante par ID : charge la leçon puis délègue à :func:`lesson_locked`."""
    if level is None:
        return False
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        return False
    return lesson_locked(user_id, lesson, level, db)
