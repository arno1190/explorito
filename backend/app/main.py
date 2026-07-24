"""
Application FastAPI principale pour Explorito
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

# Le schéma est géré par les migrations Alembic (`alembic upgrade head`),
# et non plus par `Base.metadata.create_all`. Voir alembic/ et le README.
# L'import des modèles reste utile pour enregistrer les tables sur Base.metadata
# (autogénération Alembic, tests).
from app.models import (  # noqa: F401
    Achievement,
    DailyGoal,
    Exercise,
    ExerciseResult,
    LearningPath,
    Lesson,
    Media,
    Profile,
    ReviewQueue,
    Reward,
    Streak,
    Subject,
    SubjectProgress,
    User,
    UserAchievement,
    UserProgress,
)

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


# Import des routers (après la config de l'app ; import tardif volontaire)
from app.api import (  # noqa: E402
    auth,
    children,
    exercises,
    gamification,
    lessons,
    progress,
    subjects,
)

# Enregistrer les routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(children.router, prefix=f"{settings.API_PREFIX}/children", tags=["children"])
app.include_router(subjects.router, prefix=f"{settings.API_PREFIX}/subjects", tags=["subjects"])
app.include_router(lessons.router, prefix=f"{settings.API_PREFIX}/lessons", tags=["lessons"])
app.include_router(exercises.router, prefix=f"{settings.API_PREFIX}/exercises", tags=["exercises"])
app.include_router(progress.router, prefix=f"{settings.API_PREFIX}/progress", tags=["progress"])
app.include_router(
    gamification.router,
    prefix=f"{settings.API_PREFIX}/gamification",
    tags=["gamification"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
