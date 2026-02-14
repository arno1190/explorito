"""
Application FastAPI principale pour Explorito
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base

# Import models BEFORE create_all so they're registered with Base.metadata
from app.models import (  # noqa: F401
    User,
    Profile,
    Subject,
    LearningPath,
    Lesson,
    Exercise,
    Media,
    UserProgress,
    ExerciseResult,
    SubjectProgress,
    Achievement,
    UserAchievement,
    DailyGoal,
    Streak,
    Reward,
    FamilyGroup,
    FamilyMember,
    ReviewQueue,
)

# Créer toutes les tables
Base.metadata.create_all(bind=engine)

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": f"Bienvenue sur {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Endpoint de santé"""
    return {"status": "ok"}


# Import des routers
from app.api import auth, subjects, lessons, exercises, progress, gamification, children

# Enregistrer les routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(
    children.router, prefix=f"{settings.API_PREFIX}/children", tags=["children"]
)
app.include_router(
    subjects.router, prefix=f"{settings.API_PREFIX}/subjects", tags=["subjects"]
)
app.include_router(
    lessons.router, prefix=f"{settings.API_PREFIX}/lessons", tags=["lessons"]
)
app.include_router(
    exercises.router, prefix=f"{settings.API_PREFIX}/exercises", tags=["exercises"]
)
app.include_router(
    progress.router, prefix=f"{settings.API_PREFIX}/progress", tags=["progress"]
)
app.include_router(
    gamification.router,
    prefix=f"{settings.API_PREFIX}/gamification",
    tags=["gamification"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
