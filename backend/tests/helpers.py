"""Utilitaires de test : authentification Google-only et fabriques de contenu.

Les enfants n'ont plus de connexion : on s'authentifie en **parent** via
``/auth/dev-login`` (monté uniquement si DEBUG) et on « incarne » l'enfant avec
l'en-tête ``X-Acting-Child-Id``. Ces helpers factorisent ce schéma.

Les fabriques ``make_subject`` / ``make_pack`` / ``make_lesson`` /
``make_exercise`` reproduisent exactement ce que font les seeders (un parcours
par couple matière+niveau, ``order_index`` = palier, pack propriétaire) : sans
elles chaque test réinventerait le câblage et divergerait de la production —
notamment ``Lesson.pack_id`` qui est NOT NULL et porte la portée du verrou.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.content import DifficultyEnum, Exercise, LearningPath, Lesson, LevelEnum, Subject
from app.models.pack import CommunityStatus, Pack, PackOrigin
from app.models.user import Profile, User, UserRole

DEFAULT_PARENT_EMAIL = "parent@qa.fr"


def dev_login(client: TestClient, email: str = DEFAULT_PARENT_EMAIL) -> dict[str, str]:
    """Connexion de test (parent) → en-têtes d'autorisation."""
    r = client.post("/api/v1/auth/dev-login", json={"email": email})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def ensure_parent(db: Session, email: str = DEFAULT_PARENT_EMAIL) -> User:
    """Récupère ou crée un compte parent (avec profil)."""
    parent = db.query(User).filter(User.email == email).first()
    if parent is None:
        parent = User(email=email, role=UserRole.PARENT, is_active=True)
        db.add(parent)
        db.flush()
        db.add(Profile(user_id=parent.id, display_name="Parent", is_child=False))
        db.commit()
        db.refresh(parent)
    return parent


def make_child(
    db: Session,
    *,
    level: LevelEnum = LevelEnum.CP,
    parent_email: str = DEFAULT_PARENT_EMAIL,
    name: str = "Kid",
) -> User:
    """Crée un enfant sans connexion, rattaché à un parent (créé au besoin)."""
    parent = ensure_parent(db, parent_email)
    child = User(email=None, role=UserRole.CHILD, is_active=True)
    db.add(child)
    db.flush()
    db.add(
        Profile(
            user_id=child.id,
            display_name=name,
            is_child=True,
            parent_id=parent.id,
            level=level,
        )
    )
    db.flush()
    # Garde partagée : le parent créateur devient propriétaire (comme l'API).
    from app.services.guardianship import on_child_created

    on_child_created(child.id, parent.id, db)
    db.commit()
    db.refresh(child)
    return child


def child_headers(client: TestClient, child: User, *, parent_email: str = DEFAULT_PARENT_EMAIL) -> dict[str, str]:
    """En-têtes d'un parent incarnant ``child`` (auth parent + X-Acting-Child-Id)."""
    headers = dev_login(client, parent_email)
    headers["X-Acting-Child-Id"] = str(child.id)
    return headers


def make_subject(db: Session, *, slug: str = "maths", name: str = "Mathématiques", icon: str = "🔢") -> Subject:
    """Récupère ou crée une matière (le ``slug`` est unique en base)."""
    subject = db.query(Subject).filter(Subject.slug == slug).first()
    if subject is None:
        subject = Subject(name=name, slug=slug, icon=icon, is_active=True)
        db.add(subject)
        db.flush()
    return subject


def make_pack(
    db: Session,
    *,
    title: str = "Pack",
    origin: PackOrigin = PackOrigin.OFFICIAL,
    community_status: CommunityStatus = CommunityStatus.APPROVED,
    level: LevelEnum = LevelEnum.CP,
    level_max: LevelEnum | None = None,
    author: User | None = None,
    difficulty_ratified: bool = True,
    locked: bool = False,
    handle: str | None = None,
) -> Pack:
    """Crée un pack. Par défaut : officiel, approuvé, difficulté ratifiée (état du contenu existant)."""
    pack = Pack(
        title=title,
        origin=origin.value,
        community_status=community_status.value,
        author_id=author.id if author else None,
        author_handle=handle,
        difficulty_ratified=difficulty_ratified,
        locked=locked,
        level_min=level,
        level_max=level_max or level,
        tags=[],
        warnings=[],
    )
    db.add(pack)
    db.flush()
    return pack


def make_lesson(
    db: Session,
    *,
    pack: Pack,
    subject: Subject | None = None,
    level: LevelEnum = LevelEnum.CP,
    tier: int = 1,
    name: str = "Leçon",
    published: bool = True,
) -> Lesson:
    """Crée une leçon rattachée à ``pack``, dans le parcours (matière, niveau) des seeders.

    ``order_index`` porte le palier : c'est lui que compare le verrou de
    progression, désormais à l'échelle du pack (cf. services/progression.py).
    """
    if subject is None:
        subject = make_subject(db)
    path = db.query(LearningPath).filter(LearningPath.subject_id == subject.id, LearningPath.level == level).first()
    if path is None:
        path = LearningPath(subject_id=subject.id, name=f"{subject.name} — {level.name}", level=level)
        db.add(path)
        db.flush()
    lesson = Lesson(
        path_id=path.id,
        pack_id=pack.id,
        name=name,
        order_index=tier,
        is_published=published,
        xp_reward=0,
    )
    db.add(lesson)
    db.flush()
    return lesson


def make_exercise(
    db: Session,
    *,
    lesson: Lesson,
    order_index: int = 0,
    difficulty_level: int | None = 1,
    question: str = "1+1 ?",
) -> Exercise:
    """Crée un QCM à deux options ; la bonne réponse est ``{"option_ids": ["a"]}``."""
    exercise = Exercise(
        lesson_id=lesson.id,
        type="multiple_choice",
        question=question,
        content={"options": [{"id": "a", "text": "2"}, {"id": "b", "text": "3"}], "multiple": False},
        correct_answer={"option_ids": ["a"]},
        order_index=order_index,
        difficulty=DifficultyEnum.EASY,
        difficulty_level=difficulty_level,
    )
    db.add(exercise)
    db.flush()
    return exercise
