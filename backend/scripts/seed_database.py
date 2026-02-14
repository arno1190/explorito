"""
Script de seed de la base de données Explorito

Ce script crée:
- Les matières (Français, Mathématiques, etc.)
- Le parcours "Lecture Ratus" dans Français
- Les 24 leçons Ratus avec leurs images
- 3-5 exercices par leçon (types variés)
- Les achievements de base
- Un utilisateur admin
- Copie les images Ratus vers uploads/ratus/

Le script est idempotent: il peut être exécuté plusieurs fois sans créer de doublons.
"""

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.content import Subject, LearningPath, Lesson, Exercise, LevelEnum, DifficultyEnum
from app.models.gamification import Achievement, AchievementRarity
from app.models.user import User, Profile, UserRole
from app.core.database import Base


# Configuration
MANIFEST_PATH = Path(__file__).parent.parent / "extracted_content" / "ratus_manifest.json"
SOURCE_IMAGES_DIR = Path(__file__).parent.parent / "extracted_content" / "images"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
RATUS_UPLOADS_DIR = UPLOADS_DIR / "ratus"


def load_manifest() -> Dict[str, Any]:
    """Charge le manifest Ratus"""
    print(f"📖 Chargement du manifest depuis {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_uploads_directory():
    """Crée le répertoire uploads/ratus/ s'il n'existe pas"""
    print(f"📁 Configuration du répertoire uploads")
    UPLOADS_DIR.mkdir(exist_ok=True)
    RATUS_UPLOADS_DIR.mkdir(exist_ok=True)
    print(f"   ✓ {RATUS_UPLOADS_DIR} créé/vérifié")


def copy_ratus_images():
    """Copie les images Ratus vers le répertoire uploads"""
    print(f"🖼️  Copie des images Ratus...")

    if not SOURCE_IMAGES_DIR.exists():
        print(f"   ⚠️  Répertoire source {SOURCE_IMAGES_DIR} introuvable")
        return

    # Copier les images de scènes (principales)
    scenes_dir = SOURCE_IMAGES_DIR / "scenes"
    if scenes_dir.exists():
        target_scenes = RATUS_UPLOADS_DIR / "scenes"
        target_scenes.mkdir(exist_ok=True)

        image_files = list(scenes_dir.glob("*.jpeg")) + list(scenes_dir.glob("*.jpg")) + list(scenes_dir.glob("*.png"))
        print(f"   Copie de {len(image_files)} images de scènes...")

        for img in image_files:
            target = target_scenes / img.name
            if not target.exists():
                shutil.copy2(img, target)

        print(f"   ✓ {len(image_files)} images copiées dans {target_scenes}")

    # Copier les autres catégories si elles existent
    for category in ["characters", "syllables", "words"]:
        cat_dir = SOURCE_IMAGES_DIR / category
        if cat_dir.exists():
            target_cat = RATUS_UPLOADS_DIR / category
            target_cat.mkdir(exist_ok=True)
            files = list(cat_dir.glob("*"))
            for f in files:
                if f.is_file():
                    target = target_cat / f.name
                    if not target.exists():
                        shutil.copy2(f, target)
            if files:
                print(f"   ✓ {len(files)} fichiers copiés dans {target_cat}")


def create_subjects(session) -> Dict[str, Subject]:
    """Crée toutes les matières du CP"""
    print("📚 Création des matières...")

    subjects_data = [
        {
            "name": "Français",
            "slug": "francais",
            "description": "Lecture, compréhension et expression en français",
            "icon": "📖",
            "color": "#3B82F6",
            "order_index": 1
        },
        {
            "name": "Mathématiques",
            "slug": "mathematiques",
            "description": "Nombres, calculs et géométrie",
            "icon": "🔢",
            "color": "#10B981",
            "order_index": 2
        },
        {
            "name": "Écriture & Orthographe",
            "slug": "ecriture-orthographe",
            "description": "Apprendre à écrire et orthographier les mots",
            "icon": "✍️",
            "color": "#8B5CF6",
            "order_index": 3
        },
        {
            "name": "Questionner le Monde",
            "slug": "questionner-le-monde",
            "description": "Découverte du monde vivant, de la matière et de l'espace",
            "icon": "🌍",
            "color": "#F59E0B",
            "order_index": 4
        },
        {
            "name": "Arts Visuels",
            "slug": "arts-visuels",
            "description": "Découvrir les couleurs, les formes et les artistes",
            "icon": "🎨",
            "color": "#EC4899",
            "order_index": 5
        },
        {
            "name": "Éducation Musicale",
            "slug": "education-musicale",
            "description": "Sons, rythmes et instruments",
            "icon": "🎵",
            "color": "#EF4444",
            "order_index": 6
        },
    ]

    subjects = {}
    for subject_data in subjects_data:
        # Vérifier si existe déjà
        existing = session.query(Subject).filter_by(slug=subject_data["slug"]).first()
        if existing:
            print(f"   ↪ {subject_data['name']} existe déjà")
            subjects[subject_data["slug"]] = existing
        else:
            subject = Subject(**subject_data)
            session.add(subject)
            subjects[subject_data["slug"]] = subject
            print(f"   ✓ {subject_data['name']} créée")

    session.commit()
    return subjects


def create_learning_path(session, subject: Subject) -> LearningPath:
    """Crée le parcours 'Lecture Ratus' dans Français"""
    print("🎯 Création du parcours 'Lecture Ratus'...")

    # Vérifier si existe déjà
    existing = session.query(LearningPath).filter_by(
        subject_id=subject.id,
        name="Lecture Ratus"
    ).first()

    if existing:
        print("   ↪ Parcours 'Lecture Ratus' existe déjà")
        return existing

    path = LearningPath(
        subject_id=subject.id,
        name="Lecture Ratus",
        description="Apprendre à lire avec Ratus et ses amis - Méthode syllabique progressive",
        level=LevelEnum.CP,
        order_index=1,
        prerequisites=[]
    )
    session.add(path)
    session.commit()
    print("   ✓ Parcours 'Lecture Ratus' créé")
    return path


def create_ratus_lessons(session, path: LearningPath, manifest: Dict[str, Any]) -> List[Lesson]:
    """Crée les 24 leçons Ratus depuis le manifest"""
    print("📝 Création des leçons Ratus...")

    structured_lessons = manifest.get("structured_lessons", [])
    print(f"   {len(structured_lessons)} leçons trouvées dans le manifest")

    lessons = []
    for idx, lesson_data in enumerate(structured_lessons):
        # Vérifier si existe déjà
        existing = session.query(Lesson).filter_by(
            path_id=path.id,
            order_index=idx
        ).first()

        if existing:
            print(f"   ↪ Leçon {idx + 1}: {lesson_data['title']} existe déjà")
            lessons.append(existing)
            continue

        # Extraire les infos
        title = lesson_data.get("title", f"Leçon {lesson_data['number']}")
        sounds = lesson_data.get("sounds", [])
        key_words = lesson_data.get("key_words", [])
        images = lesson_data.get("images", [])

        # Construire la description
        description_parts = []
        if sounds:
            description_parts.append(f"Sons étudiés: {', '.join(sounds)}")
        if key_words:
            description_parts.append(f"Mots clés: {', '.join(key_words)}")

        description = "\n".join(description_parts) if description_parts else "Leçon de lecture"

        # Image de couverture (première image de la leçon)
        cover_image = None
        if images:
            first_image = images[0]
            # Chemin relatif depuis uploads/
            cover_image = f"/uploads/ratus/scenes/{first_image['filename']}"

        # Créer la leçon
        lesson = Lesson(
            path_id=path.id,
            name=title,
            description=description,
            order_index=idx,
            unlock_criteria={},  # Déverrouillé par défaut pour la première leçon
            xp_reward=50,
            estimated_duration=15,
            cover_image=cover_image,
            is_published=True
        )
        session.add(lesson)
        lessons.append(lesson)
        print(f"   ✓ Leçon {idx + 1}: {title}")

    session.commit()
    return lessons


def create_exercises_for_lesson(session, lesson: Lesson, lesson_data: Dict[str, Any], lesson_index: int):
    """Crée 3-5 exercices variés pour une leçon"""

    # Vérifier si des exercices existent déjà
    existing_count = session.query(Exercise).filter_by(lesson_id=lesson.id).count()
    if existing_count > 0:
        return

    sounds = lesson_data.get("sounds", [])
    key_words = lesson_data.get("key_words", [])
    images = lesson_data.get("images", [])

    # Liste des exercices à créer
    exercises = []

    # 1. QCM - Identifier le son
    if sounds:
        sound = sounds[0]
        exercises.append({
            "type": "mcq",
            "question": f"Quel mot contient le son [{sound}] ?",
            "content": {
                "options": [
                    {"id": "a", "text": key_words[0] if key_words else "rat", "image": None},
                    {"id": "b", "text": "maison" if sound != "a" else "voiture", "image": None},
                    {"id": "c", "text": "arbre" if sound == "a" else "pomme", "image": None}
                ]
            },
            "correct_answer": {"answer": "a"},
            "difficulty": DifficultyEnum.EASY,
            "explanation": f"Le mot '{key_words[0] if key_words else 'rat'}' contient bien le son [{sound}]."
        })

    # 2. Vrai/Faux - Reconnaissance de mot
    if key_words:
        word = key_words[0]
        exercises.append({
            "type": "true_false",
            "question": f"Le mot écrit est-il '{word}' ?",
            "content": {
                "statement": word.upper(),
                "image": f"/uploads/ratus/scenes/{images[0]['filename']}" if images else None
            },
            "correct_answer": {"answer": True},
            "difficulty": DifficultyEnum.EASY,
            "explanation": f"Oui, c'est bien le mot '{word}'."
        })

    # 3. Fill Blanks - Compléter un mot avec une syllabe
    if sounds and key_words:
        sound = sounds[0]
        word = key_words[0] if len(key_words[0]) > 2 else (key_words[1] if len(key_words) > 1 else "ratus")

        # Trouver où placer le blanc
        if sound in word:
            word_with_blank = word.replace(sound, "{blank}", 1)
        else:
            word_with_blank = f"{{blank}}{word[1:]}" if len(word) > 1 else "{blank}"

        exercises.append({
            "type": "fill_blanks",
            "question": f"Complète le mot avec la syllabe manquante",
            "content": {
                "sentence": word_with_blank,
                "blanks": [
                    {
                        "id": "1",
                        "correctAnswer": sound,
                        "alternatives": [],
                        "hint": f"C'est le son [{sound}]"
                    }
                ],
                "image": f"/uploads/ratus/scenes/{images[1]['filename']}" if len(images) > 1 else None
            },
            "correct_answer": {"blanks": {"1": sound}},
            "difficulty": DifficultyEnum.MEDIUM,
            "explanation": f"Le mot complet est '{word}'."
        })

    # 4. Image Selection - Cliquer sur la bonne image
    if len(images) >= 2:
        exercises.append({
            "type": "image_selection",
            "question": f"Clique sur l'image qui correspond au mot '{key_words[0] if key_words else 'rat'}'",
            "content": {
                "images": [
                    {
                        "id": "img1",
                        "url": f"/uploads/ratus/scenes/{images[0]['filename']}",
                        "alt": key_words[0] if key_words else "Image 1"
                    },
                    {
                        "id": "img2",
                        "url": f"/uploads/ratus/scenes/{images[1]['filename']}",
                        "alt": "Image 2"
                    }
                ]
            },
            "correct_answer": {"selected": "img1"},
            "difficulty": DifficultyEnum.EASY,
            "explanation": f"C'est bien l'image du mot '{key_words[0] if key_words else 'rat'}'."
        })

    # 5. Multiple Choice avec images - Identifier une syllabe
    if sounds and len(images) >= 1:
        sound = sounds[0]
        exercises.append({
            "type": "mcq",
            "question": f"Quelle syllabe entends-tu dans ce mot ?",
            "content": {
                "options": [
                    {"id": "a", "text": sound, "image": None},
                    {"id": "b", "text": "mo" if sound != "mo" else "pi", "image": None},
                    {"id": "c", "text": "lu" if sound != "lu" else "te", "image": None}
                ],
                "image": f"/uploads/ratus/scenes/{images[0]['filename']}"
            },
            "correct_answer": {"answer": "a"},
            "difficulty": DifficultyEnum.MEDIUM,
            "explanation": f"La syllabe [{sound}] est présente dans ce mot."
        })

    # Créer les exercices dans la base
    for idx, ex_data in enumerate(exercises):
        exercise = Exercise(
            lesson_id=lesson.id,
            type=ex_data["type"],
            question=ex_data["question"],
            content=ex_data["content"],
            correct_answer=ex_data["correct_answer"],
            hints=[],
            explanation=ex_data.get("explanation", ""),
            order_index=idx,
            difficulty=ex_data.get("difficulty", DifficultyEnum.EASY),
            media_urls={}
        )
        session.add(exercise)

    session.commit()


def create_all_exercises(session, lessons: List[Lesson], manifest: Dict[str, Any]):
    """Crée les exercices pour toutes les leçons"""
    print("✏️  Création des exercices...")

    structured_lessons = manifest.get("structured_lessons", [])

    for idx, lesson in enumerate(lessons):
        if idx < len(structured_lessons):
            lesson_data = structured_lessons[idx]
            create_exercises_for_lesson(session, lesson, lesson_data, idx)

            # Compter les exercices créés
            count = session.query(Exercise).filter_by(lesson_id=lesson.id).count()
            print(f"   ✓ {count} exercices pour '{lesson.name}'")


def create_achievements(session):
    """Crée les achievements de base"""
    print("🏆 Création des achievements...")

    achievements_data = [
        {
            "name": "Première leçon",
            "description": "Termine ta première leçon",
            "icon": "🎯",
            "criteria": {"type": "lessons_completed", "value": 1},
            "rarity": AchievementRarity.COMMON,
            "category": "reading"
        },
        {
            "name": "Série de 3 jours",
            "description": "Travaille 3 jours d'affilée",
            "icon": "🔥",
            "criteria": {"type": "streak", "value": 3},
            "rarity": AchievementRarity.COMMON,
            "category": "global"
        },
        {
            "name": "Expert en lecture",
            "description": "Termine 10 leçons de lecture",
            "icon": "📚",
            "criteria": {"type": "lessons_completed", "value": 10, "subject": "francais"},
            "rarity": AchievementRarity.RARE,
            "category": "reading"
        },
        {
            "name": "Champion Ratus",
            "description": "Termine toutes les 24 leçons Ratus",
            "icon": "👑",
            "criteria": {"type": "lessons_completed", "value": 24, "path": "lecture-ratus"},
            "rarity": AchievementRarity.EPIC,
            "category": "reading"
        },
        {
            "name": "Mathématicien Junior",
            "description": "Termine 5 leçons de mathématiques",
            "icon": "🔢",
            "criteria": {"type": "lessons_completed", "value": 5, "subject": "mathematiques"},
            "rarity": AchievementRarity.RARE,
            "category": "math"
        },
        {
            "name": "Série de 7 jours",
            "description": "Travaille 7 jours d'affilée",
            "icon": "⭐",
            "criteria": {"type": "streak", "value": 7},
            "rarity": AchievementRarity.EPIC,
            "category": "global"
        },
        {
            "name": "100 Exercices",
            "description": "Réussis 100 exercices",
            "icon": "💯",
            "criteria": {"type": "exercises_completed", "value": 100},
            "rarity": AchievementRarity.RARE,
            "category": "global"
        },
        {
            "name": "Perfectionniste",
            "description": "Obtiens 3 étoiles sur 10 leçons",
            "icon": "⭐⭐⭐",
            "criteria": {"type": "perfect_lessons", "value": 10},
            "rarity": AchievementRarity.LEGENDARY,
            "category": "global"
        }
    ]

    for ach_data in achievements_data:
        # Vérifier si existe déjà
        existing = session.query(Achievement).filter_by(name=ach_data["name"]).first()
        if existing:
            print(f"   ↪ {ach_data['name']} existe déjà")
            continue

        achievement = Achievement(**ach_data)
        session.add(achievement)
        print(f"   ✓ {ach_data['name']}")

    session.commit()


def create_admin_user(session):
    """Crée un utilisateur admin"""
    print("👤 Création de l'utilisateur admin...")

    # Vérifier si existe déjà
    existing = session.query(User).filter_by(email="admin@explorito.fr").first()
    if existing:
        print("   ↪ Utilisateur admin existe déjà")
        return

    # Créer l'utilisateur
    user = User(
        email="admin@explorito.fr",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    session.add(user)
    session.commit()

    # Créer le profil
    profile = Profile(
        user_id=user.id,
        display_name="Administrateur",
        avatar_url=None,
        date_of_birth=None,
        is_child=False,
        parent_id=None,
        settings={}
    )
    session.add(profile)
    session.commit()

    print("   ✓ Admin créé (email: admin@explorito.fr, password: admin123)")


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🚀 SEED DATABASE - Explorito")
    print("=" * 60)
    print()

    # Vérifier que le manifest existe
    if not MANIFEST_PATH.exists():
        print(f"❌ Erreur: Manifest introuvable à {MANIFEST_PATH}")
        return

    # Charger le manifest
    manifest = load_manifest()

    # Configuration du répertoire uploads
    setup_uploads_directory()

    # Copier les images
    copy_ratus_images()

    # Connexion à la base de données
    print("\n🔌 Connexion à la base de données...")
    engine = create_engine(str(settings.DATABASE_URL))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Créer les tables si elles n'existent pas
        print("   ✓ Connexion établie")

        # 1. Créer les matières
        print()
        subjects = create_subjects(session)

        # 2. Créer le parcours Ratus
        print()
        francais = subjects.get("francais")
        if not francais:
            print("❌ Erreur: Matière Français introuvable")
            return

        ratus_path = create_learning_path(session, francais)

        # 3. Créer les leçons Ratus
        print()
        lessons = create_ratus_lessons(session, ratus_path, manifest)

        # 4. Créer les exercices
        print()
        create_all_exercises(session, lessons, manifest)

        # 5. Créer les achievements
        print()
        create_achievements(session)

        # 6. Créer l'utilisateur admin
        print()
        create_admin_user(session)

        print()
        print("=" * 60)
        print("✅ SEED TERMINÉ AVEC SUCCÈS!")
        print("=" * 60)
        print()
        print("📊 Résumé:")
        print(f"   - {len(subjects)} matières créées")
        print(f"   - 1 parcours 'Lecture Ratus'")
        print(f"   - {len(lessons)} leçons Ratus")

        total_exercises = session.query(Exercise).count()
        print(f"   - {total_exercises} exercices")

        total_achievements = session.query(Achievement).count()
        print(f"   - {total_achievements} achievements")

        print(f"   - 1 utilisateur admin")
        print()
        print("🔐 Connexion admin:")
        print("   Email: admin@explorito.fr")
        print("   Password: admin123")
        print()

    except Exception as e:
        print(f"\n❌ Erreur lors du seed: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
