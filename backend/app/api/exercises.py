"""
Endpoints de gestion des exercices
"""

from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_active_user
from app.api.subjects import acting_child, child_content_level, require_admin
from app.core.database import get_db
from app.models.content import Exercise, ExerciseType, Lesson
from app.models.progress import ExerciseResult
from app.models.user import User
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseResponse,
    ExerciseResultResponse,
    ExerciseSubmit,
    ExerciseSubmitResponse,
    ExerciseUpdate,
    UnlockedAchievement,
)
from app.services.gamification import process_exercise_result
from app.services.progression import lesson_locked

router = APIRouter()


def check_answer_correctness(exercise: Exercise, user_answer: dict[str, Any]) -> bool:
    """
    Vérifie si la réponse de l'utilisateur est correcte.

    Aligné sur le jeu de types canonique (:class:`ExerciseType`) et sur les
    formes typées définies dans ``app.schemas.exercise``.

    Args:
        exercise: Exercice concerné.
        user_answer: Réponse de l'utilisateur (dict).

    Returns:
        True si la réponse est correcte, False sinon. Les exercices ``reveal``
        (blagues) sont toujours considérés corrects (étoile garantie).
    """
    correct_answer = cast("dict[str, Any]", exercise.correct_answer) or {}

    if exercise.type == ExerciseType.MULTIPLE_CHOICE.value:
        # QCM : comparaison ensembliste des id d'options (réponse unique ou multiple)
        user_ids = user_answer.get("option_ids")
        if not isinstance(user_ids, list) or not user_ids:
            return False
        correct_ids = correct_answer.get("option_ids")
        if not isinstance(correct_ids, list) or not correct_ids:
            return False
        user_set = {str(a).strip() for a in user_ids}
        correct_set = {str(a).strip() for a in correct_ids}
        return user_set == correct_set

    if exercise.type == ExerciseType.FILL_BLANKS.value:
        # Trous : comparaison ordonnée, insensible à la casse et aux espaces
        user_blanks = user_answer.get("blanks")
        correct_blanks = correct_answer.get("blanks")
        if not isinstance(user_blanks, list) or not isinstance(correct_blanks, list):
            return False
        if len(user_blanks) != len(correct_blanks):
            return False
        return all(
            str(u).strip().lower() == str(c).strip().lower() for u, c in zip(user_blanks, correct_blanks, strict=True)
        )

    if exercise.type in (ExerciseType.REVEAL.value, ExerciseType.READING.value):
        # Blague / bloc de lecture : pas de bonne réponse, on valide toujours.
        return True

    if exercise.type == ExerciseType.MATH_PROBLEM.value:
        # Problème : réponse numérique comparée avec tolérance (défaut ~épsilon).
        try:
            user_value = float(str(user_answer.get("value")).replace(",", "."))
        except (TypeError, ValueError):
            return False
        correct_value = correct_answer.get("value")
        if correct_value is None:
            return False
        tolerance = float(correct_answer.get("tolerance", 0.0)) + 1e-9
        return abs(user_value - float(correct_value)) <= tolerance

    if exercise.type == ExerciseType.SOROBAN.value:
        # Boulier : le nombre lu ou construit doit être exactement le nombre attendu.
        try:
            user_value = int(float(str(user_answer.get("value"))))
        except (TypeError, ValueError):
            return False
        correct_value = correct_answer.get("value")
        return correct_value is not None and user_value == int(correct_value)

    if exercise.type == ExerciseType.PYTHAGORE.value:
        # Mini-jeu : chaque case "AxB" doit valoir A*B ; toutes correctes -> gagné
        cells = user_answer.get("cells")
        if not isinstance(cells, dict) or not cells:
            return False
        for key, value in cells.items():
            try:
                a_str, b_str = str(key).lower().split("x")
                expected = int(a_str) * int(b_str)
                if int(value) != expected:
                    return False
            except (ValueError, AttributeError):
                return False
        return True

    # Type inconnu : refus explicite plutôt que faux positif
    return False


@router.get("", response_model=list[ExerciseResponse])
async def list_exercises(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"),
    lesson_id: UUID | None = Query(None, description="Filtrer par leçon"),
) -> list[Exercise]:
    """
    Liste les exercices avec filtres optionnels

    Args:
        db: Session de base de données
        skip: Nombre d'éléments à ignorer pour la pagination
        limit: Nombre maximum d'éléments à retourner
        lesson_id: Filtrer par ID de leçon (optionnel)

    Returns:
        Liste des exercices
    """
    query = db.query(Exercise).order_by(Exercise.order_index)

    if lesson_id:
        query = query.filter(Exercise.lesson_id == lesson_id)

    exercises = query.offset(skip).limit(limit).all()
    return exercises


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Exercise:
    """
    Crée un nouvel exercice (admin uniquement)

    Args:
        exercise_data: Données de l'exercice à créer
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Exercice créé

    Raises:
        HTTPException: Si la leçon n'existe pas
    """
    # Vérifier que la leçon existe
    lesson = db.query(Lesson).filter(Lesson.id == exercise_data.lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Créer l'exercice (le type enum est stocké comme sa valeur string)
    data = exercise_data.model_dump()
    data["type"] = exercise_data.type.value
    new_exercise = Exercise(**data)
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)

    return new_exercise


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(exercise_id: UUID, db: Annotated[Session, Depends(get_db)]) -> Exercise:
    """
    Récupère les détails d'un exercice

    Args:
        exercise_id: ID de l'exercice
        db: Session de base de données

    Returns:
        Détails de l'exercice

    Raises:
        HTTPException: Si l'exercice n'existe pas
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé")

    return exercise


@router.put("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    exercise_id: UUID,
    exercise_data: ExerciseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Exercise:
    """
    Met à jour un exercice (admin uniquement)

    Args:
        exercise_id: ID de l'exercice
        exercise_data: Données de mise à jour
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        Exercice mis à jour

    Raises:
        HTTPException: Si l'exercice ou la leçon n'existe pas
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé")

    # Vérifier la leçon si modifiée
    if exercise_data.lesson_id and exercise_data.lesson_id != exercise.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == exercise_data.lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée")

    # Mettre à jour les champs (le type enum est stocké comme sa valeur string)
    update_data = exercise_data.model_dump(exclude_unset=True)
    if "type" in update_data and exercise_data.type is not None:
        update_data["type"] = exercise_data.type.value
    for field, value in update_data.items():
        setattr(exercise, field, value)

    db.commit()
    db.refresh(exercise)

    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """
    Supprime un exercice (admin uniquement)

    Args:
        exercise_id: ID de l'exercice
        db: Session de base de données
        current_user: Utilisateur administrateur authentifié

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: Si l'exercice n'existe pas
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé")

    db.delete(exercise)
    db.commit()


@router.post(
    "/{exercise_id}/submit",
    response_model=ExerciseSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_exercise(
    exercise_id: UUID,
    submission: ExerciseSubmit,
    db: Annotated[Session, Depends(get_db)],
    acting: Annotated[User, Depends(acting_child)],
) -> ExerciseSubmitResponse:
    """
    Soumet une réponse pour un exercice

    Args:
        exercise_id: ID de l'exercice
        submission: Réponse de l'utilisateur
        db: Session de base de données
        current_user: Utilisateur authentifié

    Returns:
        Résultat de l'exercice avec correction et résumé de progression
        (XP gagné, série, complétion de leçon, achievements débloqués).

    Raises:
        HTTPException: Si l'exercice n'existe pas
    """
    # Vérifier que l'exercice existe
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé")

    # Verrou côté serveur : un enfant ne peut pas valider un exercice d'une leçon
    # verrouillée (palier inférieur non terminé), même via un lien direct.
    level = child_content_level(acting, db)
    if level is not None and lesson_locked(acting.id, exercise.lesson, level, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette leçon est verrouillée : termine d'abord le niveau précédent.",
        )

    # Vérifier la réponse
    is_correct = check_answer_correctness(exercise, submission.answer)

    # Enregistrer le résultat AVANT le calcul de progression : la détection de
    # complétion de leçon compte les ExerciseResult déjà persistés.
    result = ExerciseResult(
        user_id=acting.id,
        exercise_id=exercise_id,
        answer=submission.answer,
        is_correct=is_correct,
        time_taken=submission.time_taken,
        hints_used=submission.hints_used,
        timestamp=datetime.utcnow(),
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    # Mettre à jour la progression (UserProgress), l'XP, la série, la complétion
    # de la leçon et débloquer les achievements éligibles.
    summary = process_exercise_result(
        user_id=acting.id,
        exercise=exercise,
        is_correct=is_correct,
        time_taken=submission.time_taken,
        db=db,
    )

    return ExerciseSubmitResponse(
        result=ExerciseResultResponse.model_validate(result),
        is_correct=is_correct,
        xp_awarded=summary["xp_awarded"],
        total_xp=summary["total_xp"],
        current_streak=summary["current_streak"],
        lesson_completed=summary["lesson_completed"],
        lesson_score=summary["lesson_score"],
        lesson_stars=summary["lesson_stars"],
        new_achievements=[UnlockedAchievement.model_validate(a) for a in summary["new_achievements"]],
    )


@router.get("/{exercise_id}/results", response_model=list[ExerciseResultResponse])
async def get_exercise_results(
    exercise_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de résultats"),
) -> list[ExerciseResult]:
    """
    Récupère les résultats de l'utilisateur pour cet exercice

    Args:
        exercise_id: ID de l'exercice
        db: Session de base de données
        current_user: Utilisateur authentifié
        limit: Nombre maximum de résultats à retourner

    Returns:
        Liste des résultats de l'utilisateur pour cet exercice

    Raises:
        HTTPException: Si l'exercice n'existe pas
    """
    # Vérifier que l'exercice existe
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé")

    # Récupérer les résultats de l'utilisateur
    results = (
        db.query(ExerciseResult)
        .filter(
            ExerciseResult.exercise_id == exercise_id,
            ExerciseResult.user_id == current_user.id,
        )
        .order_by(ExerciseResult.timestamp.desc())
        .limit(limit)
        .all()
    )

    return results
