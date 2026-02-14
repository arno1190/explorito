"""
Endpoints de gestion des exercices
"""

from typing import Annotated, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.content import Exercise, Lesson
from app.models.progress import ExerciseResult
from app.schemas.exercise import (
    ExerciseCreate,
    ExerciseUpdate,
    ExerciseResponse,
    ExerciseSubmit,
    ExerciseResultResponse,
)
from app.api.auth import get_current_active_user
from app.api.subjects import require_admin

router = APIRouter()


def check_answer_correctness(exercise: Exercise, user_answer: dict) -> bool:
    """
    Vérifie si la réponse de l'utilisateur est correcte

    Args:
        exercise: Exercice concerné
        user_answer: Réponse de l'utilisateur (dict)

    Returns:
        True si la réponse est correcte, False sinon
    """
    correct_answer = exercise.correct_answer

    # Logique de vérification selon le type d'exercice
    if exercise.type == "mcq":
        # Choix multiple : support single and multiple answers
        # Single: {"answer": "a"} or {"option_id": "a"}
        # Multiple: {"answers": ["a", "c"]} or answer is array

        # Get user answers (can be single or array)
        user_answers = user_answer.get("answers") or user_answer.get("answer") or user_answer.get("option_id")
        if not user_answers:
            return False

        # Normalize to list
        if not isinstance(user_answers, list):
            user_answers = [user_answers]

        # Get correct answers (can be single or array)
        correct_answers = correct_answer.get("answers") or correct_answer.get("answer") or correct_answer.get("option_id")
        if not correct_answers:
            return False

        # Normalize to list
        if not isinstance(correct_answers, list):
            correct_answers = [correct_answers]

        # Normalize all values to lowercase strings
        user_set = set(str(a).lower().strip() for a in user_answers)
        correct_set = set(str(a).lower().strip() for a in correct_answers)

        # Must match exactly (same answers, no extra, no missing)
        return user_set == correct_set

    elif exercise.type == "fill_blanks":
        # Remplir les blancs : comparer les réponses (insensible à la casse)
        user_blanks = user_answer.get("blanks", [])
        correct_blanks = correct_answer.get("blanks", {})

        # Handle both list and dict format for correct_blanks
        if isinstance(correct_blanks, dict):
            # Format: {"1": "a", "2": "b"}
            correct_values = list(correct_blanks.values())
        else:
            # Format: ["a", "b"]
            correct_values = correct_blanks

        if len(user_blanks) != len(correct_values):
            return False
        return all(
            str(u).strip().lower() == str(c).strip().lower()
            for u, c in zip(user_blanks, correct_values)
        )

    elif exercise.type == "drag_drop":
        # Glisser-déposer : comparer les positions
        return user_answer.get("positions") == correct_answer.get("positions")

    elif exercise.type == "true_false":
        # Vrai/Faux - support both boolean and string
        user_val = user_answer.get("answer")
        correct_val = correct_answer.get("answer")
        # Normalize to boolean
        if isinstance(user_val, str):
            user_val = user_val.lower() in ("true", "1", "yes", "vrai")
        if isinstance(correct_val, str):
            correct_val = correct_val.lower() in ("true", "1", "yes", "vrai")
        return user_val == correct_val

    elif exercise.type == "image_selection":
        # Selection d'image : comparer l'id sélectionné
        user_sel = user_answer.get("selected") or user_answer.get("image_id")
        correct_sel = correct_answer.get("selected") or correct_answer.get("image_id")
        return user_sel == correct_sel

    elif exercise.type == "matching":
        # Associations : comparer les paires
        return user_answer.get("pairs") == correct_answer.get("pairs")

    # Par défaut, comparaison stricte
    return user_answer == correct_answer


@router.get("", response_model=List[ExerciseResponse])
async def list_exercises(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(
        100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"
    ),
    lesson_id: UUID | None = Query(None, description="Filtrer par leçon"),
) -> List[Exercise]:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée"
        )

    # Créer l'exercice
    new_exercise = Exercise(**exercise_data.model_dump())
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)

    return new_exercise


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> Exercise:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé"
        )

    # Vérifier la leçon si modifiée
    if exercise_data.lesson_id and exercise_data.lesson_id != exercise.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == exercise_data.lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Leçon non trouvée"
            )

    # Mettre à jour les champs
    update_data = exercise_data.model_dump(exclude_unset=True)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé"
        )

    db.delete(exercise)
    db.commit()


@router.post(
    "/{exercise_id}/submit",
    response_model=ExerciseResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_exercise(
    exercise_id: UUID,
    submission: ExerciseSubmit,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ExerciseResult:
    """
    Soumet une réponse pour un exercice

    Args:
        exercise_id: ID de l'exercice
        submission: Réponse de l'utilisateur
        db: Session de base de données
        current_user: Utilisateur authentifié

    Returns:
        Résultat de l'exercice avec correction

    Raises:
        HTTPException: Si l'exercice n'existe pas
    """
    # Vérifier que l'exercice existe
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé"
        )

    # Vérifier la réponse
    is_correct = check_answer_correctness(exercise, submission.answer)

    # Créer le résultat
    result = ExerciseResult(
        user_id=current_user.id,
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

    return result


@router.get("/{exercise_id}/results", response_model=List[ExerciseResultResponse])
async def get_exercise_results(
    exercise_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de résultats"),
) -> List[ExerciseResult]:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exercice non trouvé"
        )

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
