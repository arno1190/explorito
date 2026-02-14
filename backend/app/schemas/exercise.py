"""
Schémas Pydantic pour les exercices
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.content import DifficultyEnum


class ExerciseBase(BaseModel):
    """Schéma de base pour les exercices"""

    type: str = Field(
        ..., description="Type d'exercice (mcq, drag_drop, fill_blanks, etc.)"
    )
    question: str = Field(..., min_length=1, description="Question de l'exercice")
    content: Dict[str, Any] = Field(
        ..., description="Contenu de l'exercice (structure dépend du type)"
    )
    correct_answer: Dict[str, Any] = Field(..., description="Réponse correcte")
    hints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Indices progressifs"
    )
    explanation: Optional[str] = Field(None, description="Explication de la réponse")
    order_index: int = Field(default=0, ge=0, description="Ordre dans la leçon")
    difficulty: DifficultyEnum = Field(
        default=DifficultyEnum.EASY, description="Niveau de difficulté"
    )
    media_urls: Dict[str, Any] = Field(
        default_factory=dict, description="URLs des médias associés"
    )


class ExerciseCreate(ExerciseBase):
    """Schéma pour la création d'un exercice"""

    lesson_id: UUID = Field(..., description="ID de la leçon")

    class Config:
        json_schema_extra = {
            "example": {
                "lesson_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": "mcq",
                "question": "Quel mot commence par le son [a] ?",
                "content": {
                    "options": [
                        {"id": "1", "text": "ananas", "image": "/uploads/ananas.png"},
                        {"id": "2", "text": "banane", "image": "/uploads/banane.png"},
                        {"id": "3", "text": "cerise", "image": "/uploads/cerise.png"},
                    ]
                },
                "correct_answer": {"option_id": "1"},
                "hints": [{"text": "Écoute bien le premier son", "delay": 10}],
                "explanation": "Ananas commence par le son [a]",
                "order_index": 1,
                "difficulty": "easy",
                "media_urls": {"audio": "/uploads/audio/ananas.mp3"},
            }
        }


class ExerciseUpdate(BaseModel):
    """Schéma pour la mise à jour d'un exercice"""

    lesson_id: Optional[UUID] = Field(None, description="ID de la leçon")
    type: Optional[str] = Field(None, description="Type d'exercice")
    question: Optional[str] = Field(
        None, min_length=1, description="Question de l'exercice"
    )
    content: Optional[Dict[str, Any]] = Field(None, description="Contenu de l'exercice")
    correct_answer: Optional[Dict[str, Any]] = Field(
        None, description="Réponse correcte"
    )
    hints: Optional[List[Dict[str, Any]]] = Field(
        None, description="Indices progressifs"
    )
    explanation: Optional[str] = Field(None, description="Explication de la réponse")
    order_index: Optional[int] = Field(None, ge=0, description="Ordre dans la leçon")
    difficulty: Optional[DifficultyEnum] = Field(
        None, description="Niveau de difficulté"
    )
    media_urls: Optional[Dict[str, Any]] = Field(
        None, description="URLs des médias associés"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Quel mot commence par le son [a] ?",
                "difficulty": "medium",
                "explanation": "Ananas commence bien par le son [a]",
            }
        }


class ExerciseResponse(ExerciseBase):
    """Schéma de réponse pour un exercice"""

    id: UUID
    lesson_id: UUID

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "lesson_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": "mcq",
                "question": "Quel mot commence par le son [a] ?",
                "content": {
                    "options": [
                        {"id": "1", "text": "ananas", "image": "/uploads/ananas.png"},
                        {"id": "2", "text": "banane", "image": "/uploads/banane.png"},
                    ]
                },
                "correct_answer": {"option_id": "1"},
                "hints": [{"text": "Écoute bien le premier son", "delay": 10}],
                "explanation": "Ananas commence par le son [a]",
                "order_index": 1,
                "difficulty": "easy",
                "media_urls": {"audio": "/uploads/audio/ananas.mp3"},
            }
        }


class ExerciseSubmit(BaseModel):
    """Schéma pour soumettre une réponse d'exercice"""

    answer: Dict[str, Any] = Field(..., description="Réponse de l'utilisateur")
    time_taken: Optional[int] = Field(None, ge=0, description="Temps pris en secondes")
    hints_used: int = Field(default=0, ge=0, description="Nombre d'indices utilisés")

    class Config:
        json_schema_extra = {
            "example": {"answer": {"option_id": "1"}, "time_taken": 15, "hints_used": 0}
        }


class ExerciseResultResponse(BaseModel):
    """Schéma de réponse pour le résultat d'un exercice"""

    id: UUID
    exercise_id: UUID
    user_id: UUID
    answer: Dict[str, Any]
    is_correct: bool
    time_taken: Optional[int]
    hints_used: int
    timestamp: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "exercise_id": "123e4567-e89b-12d3-a456-426614174002",
                "user_id": "123e4567-e89b-12d3-a456-426614174004",
                "answer": {"option_id": "1"},
                "is_correct": True,
                "time_taken": 15,
                "hints_used": 0,
                "timestamp": "2024-01-15T10:30:00",
            }
        }
