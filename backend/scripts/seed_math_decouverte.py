"""
Seed Mathematiques et Questionner le Monde

Cree les parcours, lecons et exercices pour:
- Mathematiques: 12 lecons x 6 exercices = 72 exercices
- Questionner le Monde: 10 lecons x 6 exercices = 60 exercices

Idempotent: peut etre execute plusieurs fois sans doublons.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.content import (
    DifficultyEnum,
    Exercise,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def mcq(q: str, opts: list[str], correct: int, expl: str, diff: str = "easy", order: int = 0) -> dict[str, Any]:
    return {
        "type": "mcq",
        "question": q,
        "difficulty": diff,
        "order": order,
        "explanation": expl,
        "content": {"options": [{"id": str(i), "text": t} for i, t in enumerate(opts)]},
        "correct_answer": {"answer": str(correct)},
    }


def true_false(q: str, answer: bool, expl: str, diff: str = "easy", order: int = 0) -> dict[str, Any]:
    return {
        "type": "true_false",
        "question": q,
        "difficulty": diff,
        "order": order,
        "explanation": expl,
        "content": {"statement": q},
        "correct_answer": {"answer": answer},
    }


def fill(
    q: str, sentence: str, blank_answer: str, hint: str, expl: str, diff: str = "medium", order: int = 0
) -> dict[str, Any]:
    return {
        "type": "fill_blanks",
        "question": q,
        "difficulty": diff,
        "order": order,
        "explanation": expl,
        "content": {
            "sentence": sentence,
            "blanks": [{"id": "1", "correctAnswer": blank_answer, "alternatives": [], "hint": hint}],
        },
        "correct_answer": {"blanks": {"1": blank_answer}},
    }


def insert_exercises(session: Session, lesson: Lesson, exercises: list[dict[str, Any]]) -> int:
    existing = session.query(Exercise).filter_by(lesson_id=lesson.id).count()
    if existing > 0:
        return existing
    for i, ex in enumerate(exercises):
        session.add(
            Exercise(
                lesson_id=lesson.id,
                type=ex["type"],
                question=ex["question"],
                content=ex["content"],
                correct_answer=ex["correct_answer"],
                explanation=ex.get("explanation", ""),
                difficulty=DifficultyEnum(ex.get("difficulty", "easy")),
                order_index=i,
                hints=[],
                media_urls={},
            )
        )
    session.flush()
    return len(exercises)


def find_or_create_path(session: Session, subject: Subject, name: str, desc: str, order: int = 1) -> LearningPath:
    existing = session.query(LearningPath).filter_by(subject_id=subject.id, name=name).first()
    if existing:
        print(f"   ↪ Parcours '{name}' existe deja")
        return existing
    path = LearningPath(
        subject_id=subject.id,
        name=name,
        description=desc,
        level=LevelEnum.CP,
        order_index=order,
        prerequisites=[],
    )
    session.add(path)
    session.commit()
    print(f"   ✓ Parcours '{name}' cree")
    return path


def create_lessons_with_exercises(
    session: Session,
    path: LearningPath,
    lessons_data: list[dict[str, Any]],
) -> int:
    total_ex = 0
    for idx, ld in enumerate(lessons_data):
        existing = session.query(Lesson).filter_by(path_id=path.id, order_index=idx).first()
        if existing:
            lesson = existing
            print(f"   ↪ Lecon {idx + 1}: {ld['name']} existe deja")
        else:
            lesson = Lesson(
                path_id=path.id,
                name=ld["name"],
                description=ld["desc"],
                order_index=idx,
                unlock_criteria={},
                xp_reward=50,
                estimated_duration=15,
                is_published=True,
            )
            session.add(lesson)
            session.flush()
            print(f"   ✓ Lecon {idx + 1}: {ld['name']}")
        n = insert_exercises(session, lesson, ld["exercises"])
        total_ex += n
    session.commit()
    return total_ex


# ---------------------------------------------------------------------------
# MATHEMATIQUES - 12 lecons x 6 exercices
# ---------------------------------------------------------------------------

MATH_LESSONS: list[dict[str, Any]] = [
    # 1. Nombres 0-5
    {
        "name": "Les nombres de 0 a 5 🔢",
        "desc": "Decouvrir et reconnaitre les nombres de 0 a 5",
        "exercises": [
            mcq("Quel est ce nombre ? 3️⃣", ["2", "3", "4"], 1, "C'est le nombre 3 ! Trois comme 3 doigts."),
            mcq("Combien y a-t-il d'etoiles ? ⭐⭐⭐⭐⭐", ["4", "5", "6"], 1, "Il y a 5 etoiles ! ⭐⭐⭐⭐⭐"),
            true_false("Le nombre 0 veut dire 'rien du tout'.", True, "Oui ! 0 signifie qu'il n'y a rien. 🫙"),
            mcq("Quel nombre vient apres 2 ?", ["1", "3", "4"], 1, "Apres 2, c'est 3 ! On compte : 1, 2, 3.", "medium"),
            fill(
                "Complete : 1, 2, ___, 4, 5",
                "1, 2, {blank}, 4, 5",
                "3",
                "C'est entre 2 et 4",
                "La suite est 1, 2, 3, 4, 5 !",
                "medium",
            ),
            mcq("Montre le nombre 1 🖐️", ["0", "1", "5"], 1, "1, c'est un seul doigt leve ! ☝️"),
        ],
    },
    # 2. Nombres 6-10
    {
        "name": "Les nombres de 6 a 10 🔟",
        "desc": "Apprendre les nombres de 6 a 10",
        "exercises": [
            mcq("Quel nombre vient apres 7 ?", ["6", "8", "9"], 1, "Apres 7, c'est 8 !"),
            mcq("Combien de pommes ? 🍎🍎🍎🍎🍎🍎🍎🍎🍎", ["8", "9", "10"], 1, "Il y a 9 pommes ! 🍎"),
            true_false("10, c'est pareil que dix.", True, "Oui ! 10 s'ecrit aussi 'dix'. 🔟"),
            fill(
                "Complete : 6, 7, ___, 9, 10",
                "6, 7, {blank}, 9, 10",
                "8",
                "C'est entre 7 et 9",
                "La suite est 6, 7, 8, 9, 10 !",
            ),
            mcq(
                "Quel est le plus grand : 6 ou 9 ?",
                ["6", "9", "Ils sont egaux"],
                1,
                "9 est plus grand que 6 ! 9 > 6",
                "medium",
            ),
            mcq("Combien de doigts sur deux mains ? 🖐️🖐️", ["5", "8", "10"], 2, "On a 10 doigts sur deux mains !"),
        ],
    },
    # 3. Compter des objets
    {
        "name": "Compter des objets 🧸",
        "desc": "Apprendre a compter des collections d'objets",
        "exercises": [
            mcq("Combien de ballons ? 🎈🎈🎈", ["2", "3", "4"], 1, "Il y a 3 ballons ! 🎈🎈🎈"),
            mcq("Combien de bonbons ? 🍬🍬🍬🍬🍬🍬🍬", ["6", "7", "8"], 1, "Il y a 7 bonbons !"),
            true_false("Il y a 4 coeurs : ❤️❤️❤️❤️", True, "Oui ! On compte : 1, 2, 3, 4 coeurs. ❤️"),
            mcq("Combien de fleurs ? 🌸🌸", ["1", "2", "3"], 1, "Il y a 2 fleurs ! 🌸🌸"),
            true_false("Il y a 5 etoiles : ⭐⭐⭐", False, "Non ! Il y a seulement 3 etoiles, pas 5.", "medium"),
            fill(
                "J'ai {blank} crayons : ✏️✏️✏️✏️✏️✏️",
                "J'ai {blank} crayons : ✏️✏️✏️✏️✏️✏️",
                "6",
                "Compte les crayons un par un",
                "Il y a 6 crayons ! ✏️",
                "medium",
            ),
        ],
    },
    # 4. Plus grand / Plus petit
    {
        "name": "Plus grand, plus petit 📏",
        "desc": "Comparer des nombres avec > et <",
        "exercises": [
            mcq("Quel nombre est le plus grand ?", ["3", "7", "2"], 1, "7 est le plus grand ! 7 > 3 > 2"),
            mcq("Quel nombre est le plus petit ?", ["9", "1", "5"], 1, "1 est le plus petit nombre !"),
            true_false("5 est plus grand que 8.", False, "Non ! 5 est plus petit que 8. 5 < 8."),
            mcq(
                "Range du plus petit au plus grand : 3, 1, 2",
                ["1, 2, 3", "3, 2, 1", "2, 1, 3"],
                0,
                "Du plus petit au plus grand : 1, 2, 3 !",
                "medium",
            ),
            true_false("4 est plus petit que 6.", True, "Oui ! 4 < 6. Quatre est plus petit que six."),
            mcq("Quel nombre est entre 3 et 5 ?", ["2", "4", "6"], 1, "4 est entre 3 et 5 !", "medium"),
        ],
    },
    # 5. Addition avec les doigts
    {
        "name": "Additionner avec les doigts ✋",
        "desc": "Premiers calculs d'addition avec les doigts",
        "exercises": [
            mcq("1 + 1 = ? ☝️☝️", ["1", "2", "3"], 1, "1 + 1 = 2 ! Un doigt plus un doigt font deux doigts."),
            mcq("2 + 1 = ? ✌️☝️", ["2", "3", "4"], 1, "2 + 1 = 3 !"),
            mcq("1 + 2 = ?", ["2", "3", "4"], 1, "1 + 2 = 3 ! C'est pareil que 2 + 1."),
            fill("2 + 2 = {blank}", "2 + 2 = {blank}", "4", "Leve 2 doigts sur chaque main", "2 + 2 = 4 ! ✌️✌️"),
            mcq("3 + 1 = ?", ["3", "4", "5"], 1, "3 + 1 = 4 ! On ajoute un doigt.", "medium"),
            true_false("1 + 3 = 4", True, "Oui ! 1 + 3 = 4. ☝️🤟", "medium"),
        ],
    },
    # 6. Addition simple
    {
        "name": "Additions simples ➕",
        "desc": "Additions avec des nombres jusqu'a 10",
        "exercises": [
            mcq("3 + 2 = ?", ["4", "5", "6"], 1, "3 + 2 = 5 !"),
            mcq("4 + 3 = ?", ["6", "7", "8"], 1, "4 + 3 = 7 !"),
            fill(
                "5 + ___ = 8",
                "5 + {blank} = 8",
                "3",
                "Combien faut-il ajouter a 5 pour faire 8 ?",
                "5 + 3 = 8 !",
                "medium",
            ),
            mcq("2 + 5 = ?", ["6", "7", "8"], 1, "2 + 5 = 7 !"),
            true_false("6 + 2 = 9", False, "Non ! 6 + 2 = 8, pas 9.", "medium"),
            mcq("4 + 4 = ?", ["6", "7", "8"], 2, "4 + 4 = 8 ! C'est le double de 4.", "medium"),
        ],
    },
    # 7. Soustraction avec les doigts
    {
        "name": "Soustraire avec les doigts 🖐️",
        "desc": "Premiers calculs de soustraction",
        "exercises": [
            mcq("3 - 1 = ? 🤟 → baisse 1 doigt", ["1", "2", "3"], 1, "3 - 1 = 2 ! On baisse un doigt."),
            mcq("2 - 1 = ?", ["0", "1", "2"], 1, "2 - 1 = 1 !"),
            true_false("4 - 2 = 2", True, "Oui ! 4 - 2 = 2. ✌️"),
            mcq("5 - 3 = ?", ["1", "2", "3"], 1, "5 - 3 = 2 !", "medium"),
            fill(
                "3 - {blank} = 1",
                "3 - {blank} = 1",
                "2",
                "Combien faut-il enlever a 3 pour avoir 1 ?",
                "3 - 2 = 1 !",
                "medium",
            ),
            mcq("4 - 4 = ?", ["0", "1", "4"], 0, "4 - 4 = 0 ! Il ne reste rien."),
        ],
    },
    # 8. Soustraction simple
    {
        "name": "Soustractions simples ➖",
        "desc": "Soustractions avec des nombres jusqu'a 10",
        "exercises": [
            mcq("7 - 3 = ?", ["3", "4", "5"], 1, "7 - 3 = 4 !"),
            mcq("9 - 5 = ?", ["3", "4", "5"], 1, "9 - 5 = 4 !"),
            true_false("8 - 6 = 3", False, "Non ! 8 - 6 = 2, pas 3.", "medium"),
            fill(
                "10 - {blank} = 7",
                "10 - {blank} = 7",
                "3",
                "Combien faut-il enlever a 10 pour avoir 7 ?",
                "10 - 3 = 7 !",
                "medium",
            ),
            mcq("6 - 4 = ?", ["1", "2", "3"], 1, "6 - 4 = 2 !"),
            mcq("10 - 5 = ?", ["4", "5", "6"], 1, "10 - 5 = 5 ! C'est la moitie de 10.", "medium"),
        ],
    },
    # 9. Nombres 11-20
    {
        "name": "Les nombres de 11 a 20 🔢",
        "desc": "Decouvrir les nombres de 11 a 20",
        "exercises": [
            mcq("Quel nombre vient apres 10 ?", ["9", "11", "20"], 1, "Apres 10, c'est 11 !"),
            mcq("Comment ecrit-on 'quinze' ?", ["13", "14", "15"], 2, "Quinze s'ecrit 15 !"),
            true_false("17 est plus grand que 12.", True, "Oui ! 17 > 12."),
            fill(
                "Complete : 14, 15, ___, 17",
                "14, 15, {blank}, 17",
                "16",
                "C'est entre 15 et 17",
                "La suite est 14, 15, 16, 17 !",
                "medium",
            ),
            mcq(
                "Combien y a-t-il dans 18 ?",
                ["1 dizaine et 8 unites", "8 dizaines et 1 unite", "18 dizaines"],
                0,
                "18 = 1 dizaine + 8 unites. C'est 10 + 8 !",
                "hard",
            ),
            mcq("Quel est le plus grand : 13 ou 19 ?", ["13", "19", "Ils sont egaux"], 1, "19 est plus grand que 13 !"),
        ],
    },
    # 10. Addition avec retenue
    {
        "name": "Additions jusqu'a 20 🧮",
        "desc": "Additions avec des resultats jusqu'a 20",
        "exercises": [
            mcq("8 + 3 = ?", ["10", "11", "12"], 1, "8 + 3 = 11 ! On depasse 10."),
            mcq("7 + 5 = ?", ["11", "12", "13"], 1, "7 + 5 = 12 !", "medium"),
            true_false("9 + 4 = 13", True, "Oui ! 9 + 4 = 13.", "medium"),
            fill(
                "6 + {blank} = 14",
                "6 + {blank} = 14",
                "8",
                "Combien faut-il ajouter a 6 pour faire 14 ?",
                "6 + 8 = 14 !",
                "hard",
            ),
            mcq("9 + 9 = ?", ["17", "18", "19"], 1, "9 + 9 = 18 ! C'est le double de 9.", "hard"),
            mcq("5 + 7 = ?", ["11", "12", "13"], 1, "5 + 7 = 12 !"),
        ],
    },
    # 11. Formes geometriques
    {
        "name": "Les formes geometriques 🔷",
        "desc": "Reconnaitre les formes : carre, cercle, triangle, rectangle",
        "exercises": [
            mcq("Quelle forme a 3 cotes ? 🔺", ["Carre", "Triangle", "Cercle"], 1, "Le triangle a 3 cotes ! 🔺"),
            mcq(
                "Quelle forme est toute ronde ? ⭕", ["Carre", "Triangle", "Cercle"], 2, "Le cercle est tout rond ! ⭕"
            ),
            true_false("Un carre a 4 cotes egaux.", True, "Oui ! Le carre a 4 cotes de la meme longueur. 🟦"),
            mcq(
                "Combien de cotes a un rectangle ?",
                ["3", "4", "5"],
                1,
                "Le rectangle a 4 cotes ! Comme le carre, mais plus long.",
                "medium",
            ),
            true_false("Un cercle a des cotes.", False, "Non ! Le cercle n'a aucun cote, il est tout rond. ⭕"),
            mcq(
                "Quelle forme ressemble a une porte ?",
                ["Triangle", "Cercle", "Rectangle"],
                2,
                "La porte a la forme d'un rectangle ! 🚪",
                "medium",
            ),
        ],
    },
    # 12. Mesurer et comparer
    {
        "name": "Mesurer et comparer 📐",
        "desc": "Comparer des longueurs, des tailles et des poids",
        "exercises": [
            mcq(
                "Qu'est-ce qui est le plus long ?",
                ["Un crayon ✏️", "Un bus 🚌", "Une gomme"],
                1,
                "Le bus est beaucoup plus long qu'un crayon !",
            ),
            true_false(
                "Une fourmi est plus grande qu'un elephant.",
                False,
                "Non ! L'elephant est bien plus grand que la fourmi ! 🐘🐜",
            ),
            mcq(
                "Qu'est-ce qui est le plus lourd ?",
                ["Une plume 🪶", "Un livre 📖", "Une voiture 🚗"],
                2,
                "La voiture est la plus lourde !",
            ),
            mcq(
                "Quel objet est le plus court ?",
                ["Un stylo ✏️", "Une regle de 30 cm 📏", "Un cheveu 💇"],
                2,
                "Un cheveu est tres court !",
                "medium",
            ),
            true_false("1 metre, c'est 100 centimetres.", True, "Oui ! 1 m = 100 cm. 📏", "medium"),
            mcq(
                "Qu'est-ce qui est le plus leger ?",
                ["Un sac a dos 🎒", "Une feuille de papier 📄", "Une brique 🧱"],
                1,
                "La feuille de papier est tres legere !",
                "medium",
            ),
        ],
    },
]


# ---------------------------------------------------------------------------
# QUESTIONNER LE MONDE - 10 lecons x 6 exercices
# ---------------------------------------------------------------------------

DECOUVERTE_LESSONS: list[dict[str, Any]] = [
    # 1. Animaux de la ferme
    {
        "name": "Les animaux de la ferme 🐔",
        "desc": "Decouvrir les animaux qui vivent a la ferme",
        "exercises": [
            mcq(
                "Quel animal fait 'Meuh' ? 🐄",
                ["Le chat", "La vache", "Le chien"],
                1,
                "C'est la vache qui fait 'Meuh' ! 🐄",
            ),
            mcq("Que donne la poule ? 🐔", ["Du lait", "De la laine", "Des oeufs"], 2, "La poule donne des oeufs ! 🥚"),
            true_false("Le cochon vit a la ferme.", True, "Oui ! Le cochon est un animal de la ferme. 🐷"),
            mcq(
                "Quel animal donne de la laine ?",
                ["La chevre", "Le mouton", "Le canard"],
                1,
                "Le mouton donne de la laine ! 🐑",
            ),
            true_false("Le lion vit a la ferme.", False, "Non ! Le lion est un animal sauvage, pas de la ferme. 🦁"),
            fill(
                "La vache donne du {blank}.",
                "La vache donne du {blank}.",
                "lait",
                "On le boit le matin",
                "La vache donne du lait ! 🥛",
            ),
        ],
    },
    # 2. Animaux sauvages
    {
        "name": "Les animaux sauvages 🦁",
        "desc": "Decouvrir les animaux de la savane et de la foret",
        "exercises": [
            mcq(
                "Quel est le plus grand animal terrestre ?",
                ["Le lion 🦁", "L'elephant 🐘", "Le loup 🐺"],
                1,
                "L'elephant est le plus grand animal terrestre ! 🐘",
            ),
            mcq(
                "Ou vit le singe ? 🐒",
                ["Dans l'eau", "Dans les arbres", "Sous terre"],
                1,
                "Le singe vit dans les arbres ! 🌳",
            ),
            true_false("Le tigre a des rayures.", True, "Oui ! Le tigre a de belles rayures noires et orange. 🐯"),
            mcq(
                "Quel animal a un tres long cou ?",
                ["Le crocodile", "La girafe", "Le serpent"],
                1,
                "La girafe a un tres long cou pour manger les feuilles ! 🦒",
            ),
            true_false("Le poisson vit sur la terre.", False, "Non ! Le poisson vit dans l'eau. 🐟"),
            mcq(
                "Quel animal est le roi de la savane ?",
                ["L'elephant", "Le singe", "Le lion"],
                2,
                "Le lion est appele le roi de la savane ! 🦁",
                "medium",
            ),
        ],
    },
    # 3. Les saisons
    {
        "name": "Les 4 saisons 🍂",
        "desc": "Decouvrir le printemps, l'ete, l'automne et l'hiver",
        "exercises": [
            mcq(
                "En quelle saison les feuilles tombent ?",
                ["Printemps 🌸", "Automne 🍂", "Ete ☀️"],
                1,
                "Les feuilles tombent en automne ! 🍂",
            ),
            mcq("En quelle saison il neige ? ❄️", ["Hiver", "Ete", "Printemps"], 0, "Il neige en hiver ! ❄️⛄"),
            true_false("En ete, il fait chaud.", True, "Oui ! L'ete est la saison la plus chaude. ☀️"),
            mcq(
                "En quelle saison les fleurs poussent ?",
                ["Hiver ❄️", "Automne 🍂", "Printemps 🌸"],
                2,
                "Les fleurs poussent au printemps ! 🌸🌷",
            ),
            true_false("Il y a 5 saisons.", False, "Non ! Il y a 4 saisons : printemps, ete, automne, hiver."),
            fill(
                "Apres l'automne, c'est l'{blank}.",
                "Apres l'automne, c'est l'{blank}.",
                "hiver",
                "La saison ou il fait froid",
                "Apres l'automne vient l'hiver ! ❄️",
                "medium",
            ),
        ],
    },
    # 4. Le corps humain
    {
        "name": "Mon corps 🦴",
        "desc": "Connaitre les parties du corps humain",
        "exercises": [
            mcq("Avec quoi on voit ? 👀", ["Les oreilles", "Les yeux", "Le nez"], 1, "On voit avec les yeux ! 👀"),
            mcq("Combien de doigts a une main ?", ["4", "5", "10"], 1, "Une main a 5 doigts ! 🖐️"),
            true_false("Le coeur est dans notre poitrine.", True, "Oui ! Le coeur bat dans notre poitrine. ❤️"),
            mcq(
                "Avec quoi on entend ?",
                ["Les yeux", "La bouche", "Les oreilles"],
                2,
                "On entend avec les oreilles ! 👂",
            ),
            true_false("On a 3 bras.", False, "Non ! On a 2 bras. Un a droite et un a gauche. 💪"),
            mcq(
                "Que protege le crane ?",
                ["Le coeur", "Le cerveau", "Les poumons"],
                1,
                "Le crane protege le cerveau ! 🧠",
                "medium",
            ),
        ],
    },
    # 5. Les 5 sens
    {
        "name": "Les 5 sens 👃",
        "desc": "Decouvrir la vue, l'ouie, l'odorat, le gout et le toucher",
        "exercises": [
            mcq(
                "Quel sens utilise le nez ?",
                ["La vue", "L'odorat", "Le gout"],
                1,
                "Le nez sert a l'odorat, pour sentir les odeurs ! 👃",
            ),
            mcq(
                "Avec quoi goute-t-on les aliments ?",
                ["Les doigts", "Les yeux", "La langue"],
                2,
                "On goute avec la langue ! 👅",
            ),
            true_false("Les yeux servent a voir.", True, "Oui ! La vue, c'est le sens des yeux. 👁️"),
            mcq(
                "Quel sens utilise-t-on pour ecouter de la musique ?",
                ["Le toucher", "L'ouie", "L'odorat"],
                1,
                "L'ouie est le sens de l'ecoute ! 🎵👂",
            ),
            true_false("Il y a 3 sens.", False, "Non ! Il y a 5 sens : vue, ouie, odorat, gout, toucher. 🖐️"),
            fill(
                "Pour sentir une fleur, j'utilise mon {blank}.",
                "Pour sentir une fleur, j'utilise mon {blank}.",
                "nez",
                "L'organe au milieu du visage",
                "On sent les odeurs avec le nez ! 👃🌹",
                "medium",
            ),
        ],
    },
    # 6. Le jour et la nuit
    {
        "name": "Le jour et la nuit 🌙",
        "desc": "Comprendre l'alternance jour/nuit",
        "exercises": [
            mcq(
                "Qu'est-ce qui eclaire le jour ?",
                ["La Lune 🌙", "Le Soleil ☀️", "Les etoiles ⭐"],
                1,
                "C'est le Soleil qui eclaire la journee ! ☀️",
            ),
            true_false("La nuit, on voit la Lune.", True, "Oui ! La Lune brille dans le ciel la nuit. 🌙"),
            mcq("Que fait-on la nuit ?", ["On va a l'ecole", "On dort", "On dejeune"], 1, "La nuit, on dort ! 😴💤"),
            true_false(
                "Le Soleil brille la nuit.", False, "Non ! Le Soleil brille le jour. La nuit, il fait sombre. 🌑"
            ),
            mcq(
                "Quand voit-on les etoiles ?",
                ["Le matin", "L'apres-midi", "La nuit"],
                2,
                "Les etoiles sont visibles la nuit ! ⭐🌃",
            ),
            fill(
                "Le matin, le soleil se {blank}.",
                "Le matin, le soleil se {blank}.",
                "leve",
                "Le contraire de 'coucher'",
                "Le matin, le soleil se leve ! 🌅",
                "medium",
            ),
        ],
    },
    # 7. Les plantes
    {
        "name": "Les plantes 🌱",
        "desc": "Comprendre comment poussent les plantes",
        "exercises": [
            mcq(
                "De quoi a besoin une plante pour pousser ?",
                ["De chocolat 🍫", "D'eau 💧", "De musique 🎵"],
                1,
                "Les plantes ont besoin d'eau pour pousser ! 💧🌱",
            ),
            true_false(
                "Une graine peut devenir un arbre.", True, "Oui ! Un grand arbre commence par une petite graine. 🌰🌳"
            ),
            mcq(
                "Quelle partie de la plante est sous la terre ?",
                ["Les feuilles", "La fleur", "Les racines"],
                2,
                "Les racines sont sous la terre ! Elles aspirent l'eau.",
            ),
            mcq(
                "De quoi les plantes ont besoin en plus de l'eau ?",
                ["De lumiere ☀️", "De vent 💨", "De bruit 🔊"],
                0,
                "Les plantes ont besoin de lumiere pour grandir ! ☀️",
                "medium",
            ),
            true_false(
                "Les feuilles sont toujours vertes.", False, "Non ! En automne, les feuilles changent de couleur. 🍂🍁"
            ),
            fill(
                "La plante pousse a partir d'une {blank}.",
                "La plante pousse a partir d'une {blank}.",
                "graine",
                "C'est tout petit et on le met en terre",
                "Tout commence par une graine ! 🌰",
                "medium",
            ),
        ],
    },
    # 8. L'eau
    {
        "name": "L'eau dans tous ses etats 💧",
        "desc": "Decouvrir les differents etats de l'eau",
        "exercises": [
            mcq(
                "Quand l'eau gele, elle devient...",
                ["De la vapeur", "De la glace", "Du jus"],
                1,
                "L'eau gelee devient de la glace ! 🧊",
            ),
            true_false(
                "La pluie, c'est de l'eau qui tombe du ciel.", True, "Oui ! Les gouttes de pluie sont de l'eau. 🌧️"
            ),
            mcq(
                "Ou trouve-t-on de l'eau ?",
                ["Dans les livres 📚", "Dans la mer 🌊", "Dans le soleil ☀️"],
                1,
                "La mer est pleine d'eau ! 🌊",
            ),
            true_false(
                "On peut boire l'eau de mer.", False, "Non ! L'eau de mer est trop salee. On boit de l'eau douce. 🚰"
            ),
            mcq(
                "Quand on chauffe l'eau tres fort, elle devient...",
                ["De la glace", "De la vapeur", "Du lait"],
                1,
                "L'eau tres chaude se transforme en vapeur ! 💨",
                "medium",
            ),
            fill(
                "Les nuages sont faits de petites gouttes d'{blank}.",
                "Les nuages sont faits de petites gouttes d'{blank}.",
                "eau",
                "C'est liquide et transparent",
                "Les nuages contiennent de minuscules gouttes d'eau ! ☁️",
                "medium",
            ),
        ],
    },
    # 9. Les aliments
    {
        "name": "Bien manger 🥗",
        "desc": "Connaitre les familles d'aliments",
        "exercises": [
            mcq(
                "Quel aliment est un fruit ?",
                ["Le pain 🍞", "La pomme 🍎", "Le fromage 🧀"],
                1,
                "La pomme est un fruit ! 🍎",
            ),
            mcq(
                "Quel aliment donne des forces ?",
                ["Les bonbons 🍬", "La viande 🥩", "Le soda 🥤"],
                1,
                "La viande donne des proteines pour etre fort ! 💪",
            ),
            true_false(
                "Les legumes sont bons pour la sante.", True, "Oui ! Il faut manger des legumes chaque jour. 🥦🥕"
            ),
            mcq(
                "Quel repas prend-on le matin ?",
                ["Le diner", "Le gouter", "Le petit-dejeuner"],
                2,
                "Le matin, c'est le petit-dejeuner ! 🥐",
            ),
            true_false("Le chocolat est un legume.", False, "Non ! Le chocolat est une friandise, pas un legume. 🍫"),
            fill(
                "Pour grandir, il faut boire du {blank}.",
                "Pour grandir, il faut boire du {blank}.",
                "lait",
                "La vache en donne",
                "Le lait contient du calcium pour les os ! 🥛",
                "medium",
            ),
        ],
    },
    # 10. La meteo
    {
        "name": "La meteo ☀️🌧️",
        "desc": "Observer et decrire le temps qu'il fait",
        "exercises": [
            mcq(
                "Quel vetement met-on quand il pleut ?",
                ["Des lunettes 🕶️", "Un imperméable 🧥", "Un maillot 👙"],
                1,
                "On met un impermeable pour ne pas etre mouille ! 🧥☔",
            ),
            true_false("Quand il y a du soleil, il fait beau.", True, "Oui ! Le soleil = beau temps ! ☀️"),
            mcq(
                "Que voit-on dans le ciel quand il pleut ?",
                ["Le soleil ☀️", "Des nuages gris 🌧️", "La lune 🌙"],
                1,
                "Quand il pleut, il y a des nuages gris ! 🌧️",
            ),
            mcq(
                "Apres la pluie et le soleil, que peut-on voir ?",
                ["De la neige", "Un arc-en-ciel", "La lune"],
                1,
                "Un arc-en-ciel apparait apres la pluie ! 🌈",
            ),
            true_false(
                "La neige tombe quand il fait tres chaud.",
                False,
                "Non ! La neige tombe quand il fait froid, en hiver. ❄️",
            ),
            fill(
                "Le vent fait bouger les {blank} des arbres.",
                "Le vent fait bouger les {blank} des arbres.",
                "feuilles",
                "Elles sont vertes sur les branches",
                "Le vent souffle sur les feuilles ! 🍃",
                "medium",
            ),
        ],
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("🚀 SEED MATH + DECOUVERTE - Explorito")
    print("=" * 60)

    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # --- Find existing subjects ---
        math_subject = session.query(Subject).filter_by(slug="mathematiques").first()
        decouverte_subject = session.query(Subject).filter_by(slug="questionner-le-monde").first()

        if not math_subject:
            print("❌ Matiere 'Mathematiques' introuvable. Lancez d'abord seed_database.py.")
            return
        if not decouverte_subject:
            print("❌ Matiere 'Questionner le Monde' introuvable. Lancez d'abord seed_database.py.")
            return

        print(f"\n✓ Matieres trouvees: {math_subject.name}, {decouverte_subject.name}")

        # --- Math path + lessons ---
        print("\n📐 MATHEMATIQUES")
        math_path = find_or_create_path(
            session,
            math_subject,
            "Nombres et Calculs CP",
            "Apprendre les nombres, additions et soustractions au CP",
        )
        create_lessons_with_exercises(session, math_path, MATH_LESSONS)

        # --- Decouverte path + lessons ---
        print("\n🌍 QUESTIONNER LE MONDE")
        decouverte_path = find_or_create_path(
            session,
            decouverte_subject,
            "Decouverte du Monde CP",
            "Explorer le vivant, la matiere et les objets au CP",
        )
        create_lessons_with_exercises(session, decouverte_path, DECOUVERTE_LESSONS)

        # --- Summary ---
        total_math_lessons = session.query(Lesson).filter_by(path_id=math_path.id).count()
        total_math_exercises = session.query(Exercise).join(Lesson).filter(Lesson.path_id == math_path.id).count()
        total_dec_lessons = session.query(Lesson).filter_by(path_id=decouverte_path.id).count()
        total_dec_exercises = session.query(Exercise).join(Lesson).filter(Lesson.path_id == decouverte_path.id).count()

        print("\n" + "=" * 60)
        print("✅ SEED TERMINE AVEC SUCCES!")
        print("=" * 60)
        print("\n📊 Resume:")
        print(f"   Mathematiques:        {total_math_lessons} lecons, {total_math_exercises} exercices")
        print(f"   Questionner le Monde: {total_dec_lessons} lecons, {total_dec_exercises} exercices")
        print(
            f"   Total:                {total_math_lessons + total_dec_lessons} lecons, {total_math_exercises + total_dec_exercises} exercices"
        )
        print()

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
