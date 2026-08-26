"""Schémas Pydantic pour l'espace d'administration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentLogin(BaseModel):
    email: str | None = None
    at: datetime


class AdminOverview(BaseModel):
    """Métriques opérationnelles du tableau de bord admin."""

    parents_total: int
    children_total: int
    families_total: int
    active_parents_7d: int
    active_parents_30d: int
    active_children_7d: int
    active_children_30d: int
    exercises_total: int
    exercises_7d: int
    exercises_30d: int
    recent_logins: list[RecentLogin]


class AdminUserRow(BaseModel):
    id: UUID
    email: str | None = None
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    login_count: int = 0
    last_exercise_at: datetime | None = None
    exercises_count: int = 0
