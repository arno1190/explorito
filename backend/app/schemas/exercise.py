"""
Schémas Pydantic pour les exercices.

Le contrat de contenu est *typé* : la colonne ``content`` / ``correct_answer``
reste du JSON en base, mais chaque type d'exercice a une forme précise validée
à l'entrée de l'API. On évite ainsi le ``Dict[str, Any]`` fourre-tout qui
imposait une couche d'adaptation côté frontend.

Types canoniques (voir :class:`app.models.content.ExerciseType`) :

- ``multiple_choice`` — QCM
    content        : {"options": [{"id", "text", "image?"}], "multiple": bool}
    correct_answer : {"option_ids": [str, ...]}
- ``fill_blanks`` — compléter les trous (marqueurs ``___``)
    content        : {"text": "le c___ mange la s___"}
    correct_answer : {"blanks": ["hat", "ouris"]}
- ``reveal`` — carte à révéler (blague), pas de bonne réponse
    content        : {"prompt": "...", "reveal": "..."}
    correct_answer : {}
- ``pythagore`` — mini-jeu de table de multiplication
    content        : {"tables": [2, 3, 4], "blanks": 5}
    correct_answer : {}
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.content import DifficultyEnum, ExerciseType


# --------------------------------------------------------------------------- #
# Formes de contenu typées par type d'exercice
# --------------------------------------------------------------------------- #
class MCQOption(BaseModel):
    """Une option de QCM."""

    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    image: str | None = None


class MultipleChoiceContent(BaseModel):
    """Contenu d'un QCM."""

    options: list[MCQOption] = Field(..., min_length=2)
    multiple: bool = False


class MultipleChoiceAnswer(BaseModel):
    """Réponse correcte d'un QCM : liste d'``id`` d'options."""

    option_ids: list[str] = Field(..., min_length=1)


class FillBlanksContent(BaseModel):
    """Contenu d'un exercice à trous. Le texte contient un ou plusieurs ``___``."""

    text: str = Field(..., min_length=1)


class FillBlanksAnswer(BaseModel):
    """Réponse correcte d'un exercice à trous, dans l'ordre des ``___``."""

    blanks: list[str] = Field(..., min_length=1)


class RevealContent(BaseModel):
    """Contenu d'une carte à révéler (blague)."""

    prompt: str = Field(..., min_length=1)
    reveal: str = Field(..., min_length=1)


class PythagoreContent(BaseModel):
    """Contenu du mini-jeu Pythagore."""

    tables: list[int] = Field(..., min_length=1)
    blanks: int = Field(default=5, ge=1, le=100)


class MathProblemContent(BaseModel):
    """Contenu d'un problème de maths (l'énoncé est dans ``question``)."""

    unit: str | None = Field(None, description="Unité affichée à côté de la réponse (€, cm…)")


class MathProblemAnswer(BaseModel):
    """Réponse correcte d'un problème de maths : une valeur numérique."""

    value: float
    tolerance: float = Field(default=0.0, ge=0.0, description="Tolérance absolue acceptée")


class ReadingContent(BaseModel):
    """Contenu d'un bloc de lecture (compréhension / leçon)."""

    text: str = Field(..., min_length=1)
    image: str | None = None


BLANK_MARKER = "___"


def validate_exercise_payload(
    exercise_type: ExerciseType,
    content: dict[str, Any],
    correct_answer: dict[str, Any],
) -> None:
    """
    Valide que ``content`` / ``correct_answer`` respectent la forme du type.

    Args:
        exercise_type: Type canonique de l'exercice.
        content: Contenu brut (JSON) de l'exercice.
        correct_answer: Réponse correcte brute (JSON).

    Raises:
        ValueError: Si la forme ne correspond pas au type.
    """
    if exercise_type == ExerciseType.MULTIPLE_CHOICE:
        mcq_content = MultipleChoiceContent.model_validate(content)
        mcq_answer = MultipleChoiceAnswer.model_validate(correct_answer)
        option_ids = {opt.id for opt in mcq_content.options}
        unknown = set(mcq_answer.option_ids) - option_ids
        if unknown:
            raise ValueError(f"correct_answer.option_ids référence des options inconnues: {sorted(unknown)}")
        if not mcq_content.multiple and len(mcq_answer.option_ids) != 1:
            raise ValueError("Un QCM à réponse unique doit avoir exactement un option_id correct")

    elif exercise_type == ExerciseType.FILL_BLANKS:
        fb_content = FillBlanksContent.model_validate(content)
        fb_answer = FillBlanksAnswer.model_validate(correct_answer)
        n_markers = fb_content.text.count(BLANK_MARKER)
        if n_markers == 0:
            raise ValueError(f"Le texte fill_blanks doit contenir au moins un marqueur '{BLANK_MARKER}'")
        if n_markers != len(fb_answer.blanks):
            raise ValueError(
                f"Le nombre de trous ({n_markers}) ne correspond pas au nombre de réponses ({len(fb_answer.blanks)})"
            )

    elif exercise_type == ExerciseType.REVEAL:
        RevealContent.model_validate(content)
        # Pas de bonne réponse : correct_answer doit être vide.

    elif exercise_type == ExerciseType.PYTHAGORE:
        PythagoreContent.model_validate(content)
        # Les produits sont calculés à la correction : pas de correct_answer stocké.

    elif exercise_type == ExerciseType.MATH_PROBLEM:
        MathProblemContent.model_validate(content)
        MathProblemAnswer.model_validate(correct_answer)

    elif exercise_type == ExerciseType.READING:
        ReadingContent.model_validate(content)
        # Bloc de lecture : pas de bonne réponse (toujours validé).


# --------------------------------------------------------------------------- #
# Schémas CRUD
# --------------------------------------------------------------------------- #
class ExerciseBase(BaseModel):
    """Schéma de base pour les exercices."""

    type: ExerciseType = Field(..., description="Type d'exercice (jeu canonique)")
    question: str = Field(..., min_length=1, description="Question de l'exercice")
    content: dict[str, Any] = Field(..., description="Contenu de l'exercice (forme dépend du type)")
    correct_answer: dict[str, Any] = Field(
        default_factory=dict, description="Réponse correcte (vide pour reveal/pythagore)"
    )
    hints: list[dict[str, Any]] = Field(default_factory=list, description="Indices progressifs")
    explanation: str | None = Field(None, description="Explication de la réponse")
    order_index: int = Field(default=0, ge=0, description="Ordre dans la leçon")
    difficulty: DifficultyEnum = Field(default=DifficultyEnum.EASY, description="Niveau de difficulté")
    media_urls: dict[str, Any] = Field(default_factory=dict, description="URLs des médias associés")

    @model_validator(mode="after")
    def _validate_content_shape(self) -> "ExerciseBase":
        validate_exercise_payload(self.type, self.content, self.correct_answer)
        return self


class ExerciseCreate(ExerciseBase):
    """Schéma pour la création d'un exercice."""

    lesson_id: UUID = Field(..., description="ID de la leçon")

    model_config = {
        "json_schema_extra": {
            "example": {
                "lesson_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": "multiple_choice",
                "question": "Quel mot commence par le son [a] ?",
                "content": {
                    "options": [
                        {"id": "1", "text": "ananas"},
                        {"id": "2", "text": "banane"},
                        {"id": "3", "text": "cerise"},
                    ],
                    "multiple": False,
                },
                "correct_answer": {"option_ids": ["1"]},
                "difficulty": "easy",
            }
        }
    }


class ExerciseUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un exercice.

    Si ``type`` est fourni, ``content`` et ``correct_answer`` doivent l'être
    aussi afin de revalider la cohérence de la forme.
    """

    lesson_id: UUID | None = Field(None, description="ID de la leçon")
    type: ExerciseType | None = Field(None, description="Type d'exercice")
    question: str | None = Field(None, min_length=1, description="Question de l'exercice")
    content: dict[str, Any] | None = Field(None, description="Contenu de l'exercice")
    correct_answer: dict[str, Any] | None = Field(None, description="Réponse correcte")
    hints: list[dict[str, Any]] | None = Field(None, description="Indices progressifs")
    explanation: str | None = Field(None, description="Explication de la réponse")
    order_index: int | None = Field(None, ge=0, description="Ordre dans la leçon")
    difficulty: DifficultyEnum | None = Field(None, description="Niveau de difficulté")
    media_urls: dict[str, Any] | None = Field(None, description="URLs des médias associés")

    @model_validator(mode="after")
    def _validate_content_shape(self) -> "ExerciseUpdate":
        if self.type is not None:
            if self.content is None or self.correct_answer is None:
                raise ValueError(
                    "Lors d'un changement de type, 'content' et 'correct_answer' doivent être fournis ensemble"
                )
            validate_exercise_payload(self.type, self.content, self.correct_answer or {})
        return self


class ExerciseResponse(ExerciseBase):
    """Schéma de réponse pour un exercice."""

    id: UUID
    lesson_id: UUID

    model_config = {"from_attributes": True}

    # La réponse ne revalide pas la forme : les données en base font foi.
    @model_validator(mode="after")
    def _validate_content_shape(self) -> "ExerciseResponse":
        return self


class ExerciseSubmit(BaseModel):
    """Schéma pour soumettre une réponse d'exercice."""

    answer: dict[str, Any] = Field(..., description="Réponse de l'utilisateur")
    time_taken: int | None = Field(None, ge=0, description="Temps pris en secondes")
    hints_used: int = Field(default=0, ge=0, description="Nombre d'indices utilisés")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": {"option_ids": ["1"]},
                "time_taken": 15,
                "hints_used": 0,
            }
        }
    }


class ExerciseResultResponse(BaseModel):
    """Schéma de réponse pour le résultat d'un exercice."""

    id: UUID
    exercise_id: UUID
    user_id: UUID
    answer: dict[str, Any]
    is_correct: bool
    time_taken: int | None
    hints_used: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class UnlockedAchievement(BaseModel):
    """Achievement nouvellement débloqué renvoyé après une soumission."""

    id: UUID
    name: str
    icon: str | None = None

    model_config = {"from_attributes": True}


class ExerciseSubmitResponse(BaseModel):
    """
    Réponse enrichie d'une soumission d'exercice.

    Regroupe la correction *et* le résumé de progression (XP, série, complétion
    de la leçon, achievements) pour que le frontend affiche le feedback en un
    seul appel.
    """

    result: ExerciseResultResponse
    is_correct: bool
    xp_awarded: int = 0
    total_xp: int = 0
    current_streak: int = 0
    lesson_completed: bool = False
    lesson_score: int | None = None
    lesson_stars: int | None = None
    new_achievements: list[UnlockedAchievement] = Field(default_factory=list)
