"""
Seed en masse d'un curriculum Explorito : maternelle (light) + CE2 → CM2.

Complète les niveaux manquants (PS, MS, GS, CE2, CM1, CM2) sur les matières
existantes. Les mathématiques sont **générées par calcul** (les réponses sont
donc correctes par construction) ; les contenus de connaissances/langue sont
rédigés à la main avec des faits simples et grand public.

Chaque leçon est publiée et rangée dans (matière, niveau, palier). Idempotent
par (parcours, nom de leçon) : ré-exécuter n'insère pas de doublon.

Usage:
    # dev
    DATABASE_URL=postgresql://devuser@localhost:5432/explorito_dev \\
        uv run python scripts/seed_curriculum.py
    # prod (dans le conteneur backend)
    uv run python scripts/seed_curriculum.py

Option:
    --dry-run  : valide tout le contenu sans écrire en base.
"""

import sys
from typing import Any

from app.core.database import SessionLocal
from app.models.content import (
    DifficultyEnum,
    Exercise,
    ExerciseType,
    LearningPath,
    Lesson,
    LevelEnum,
    Subject,
)
from app.schemas.exercise import validate_exercise_payload

TIER_DIFFICULTY = {1: DifficultyEnum.EASY, 2: DifficultyEnum.MEDIUM, 3: DifficultyEnum.HARD}

# Métadonnées des matières (réutilise les slugs existants ; crée au besoin).
SUBJECTS: dict[str, dict[str, str]] = {
    "maths": {"name": "Mathématiques", "icon": "🌋"},
    "francais": {"name": "Français", "icon": "🏝️"},
    "orthographe": {"name": "Orthographe", "icon": "✏️"},
    "histoire": {"name": "Histoire", "icon": "⏳"},
    "geo": {"name": "Géographie France", "icon": "🗼"},
    "monde": {"name": "Questionner le monde", "icon": "🚀"},
}


# --------------------------------------------------------------------------- #
# Constructeurs d'exercices (renvoient des dicts conformes au contrat typé)
# --------------------------------------------------------------------------- #
def mcq(
    question: str,
    options: list[str],
    correct: int | list[int],
    *,
    multiple: bool = False,
    emoji: str | None = None,
    explanation: str | None = None,
    level: int | None = None,
) -> dict[str, Any]:
    """QCM. ``correct`` = index (0-based) ou liste d'index des bonnes options."""
    opts = [{"id": str(i + 1), "text": t} for i, t in enumerate(options)]
    idx = [correct] if isinstance(correct, int) else correct
    ex: dict[str, Any] = {
        "type": "multiple_choice",
        "question": question,
        "content": {"options": opts, "multiple": multiple},
        "correct_answer": {"option_ids": [str(i + 1) for i in idx]},
    }
    if emoji:
        ex["media_urls"] = {"emoji": emoji}
    if explanation:
        ex["explanation"] = explanation
    if level is not None:
        ex["level"] = level
    return ex


def math_problem(
    question: str,
    value: float,
    *,
    unit: str | None = None,
    tolerance: float = 0.0,
    emoji: str | None = None,
    explanation: str | None = None,
    level: int | None = None,
) -> dict[str, Any]:
    """Problème à réponse numérique (la valeur est calculée en Python)."""
    content: dict[str, Any] = {}
    if unit:
        content["unit"] = unit
    ca: dict[str, Any] = {"value": value}
    if tolerance:
        ca["tolerance"] = tolerance
    ex: dict[str, Any] = {
        "type": "math_problem",
        "question": question,
        "content": content,
        "correct_answer": ca,
    }
    if emoji:
        ex["media_urls"] = {"emoji": emoji}
    if explanation:
        ex["explanation"] = explanation
    if level is not None:
        ex["level"] = level
    return ex


def fill_blanks(
    question: str,
    text: str,
    blanks: list[str],
    *,
    explanation: str | None = None,
    level: int | None = None,
) -> dict[str, Any]:
    """Texte à trous : ``text`` contient autant de ``___`` que ``blanks``."""
    ex: dict[str, Any] = {
        "type": "fill_blanks",
        "question": question,
        "content": {"text": text},
        "correct_answer": {"blanks": blanks},
    }
    if explanation:
        ex["explanation"] = explanation
    if level is not None:
        ex["level"] = level
    return ex


def reading(question: str, text: str) -> dict[str, Any]:
    """Bloc de lecture (compréhension / leçon), sans bonne réponse."""
    return {"type": "reading", "question": question, "content": {"text": text}, "correct_answer": {}}


def soroban(
    question: str,
    value: int,
    *,
    mode: str = "read",
    columns: int | None = None,
    explanation: str | None = None,
    level: int | None = None,
) -> dict[str, Any]:
    """Exercice de boulier : ``mode`` ``read`` (lire) ou ``build`` (construire) ``value``."""
    content: dict[str, Any] = {"mode": mode, "value": value}
    if columns is not None:
        content["columns"] = columns
    ex: dict[str, Any] = {
        "type": "soroban",
        "question": question,
        "content": content,
        "correct_answer": {"value": value},
    }
    if explanation:
        ex["explanation"] = explanation
    if level is not None:
        ex["level"] = level
    return ex


def pythagore(question: str, tables: list[int], blanks: int = 6, *, level: int | None = None) -> dict[str, Any]:
    """Mini-jeu de tables de multiplication (produits calculés à la correction)."""
    ex: dict[str, Any] = {
        "type": "pythagore",
        "question": question,
        "content": {"tables": tables, "blanks": blanks},
        "correct_answer": {},
    }
    if level is not None:
        ex["level"] = level
    return ex


def theme(
    slug: str,
    level: str,
    tier: int,
    name: str,
    description: str,
    xp: int,
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble une leçon thématique complète."""
    meta = SUBJECTS[slug]
    return {
        "subject_slug": slug,
        "subject_name": meta["name"],
        "subject_icon": meta["icon"],
        "level": level,
        "tier": tier,
        "lesson": {"name": name, "description": description, "xp_reward": xp},
        "exercises": exercises,
    }


# --------------------------------------------------------------------------- #
# MATERNELLE (light) — un palier par leçon
# --------------------------------------------------------------------------- #
def maternelle() -> list[dict[str, Any]]:
    return [
        theme(
            "maths",
            "ps",
            1,
            "Compter jusqu'à 3",
            "Compter les objets jusqu'à 3.",
            20,
            [
                mcq("Combien de pommes ? 🍎", ["1", "2", "3"], 0, emoji="🍎"),
                mcq("Combien de ballons ? 🎈🎈", ["1", "2", "3"], 1, emoji="🎈"),
                mcq("Combien d'étoiles ? ⭐⭐⭐", ["1", "2", "3"], 2, emoji="⭐"),
                mcq("Combien de chats ? 🐱🐱", ["2", "3", "4"], 0, emoji="🐱"),
            ],
        ),
        theme(
            "francais",
            "ps",
            1,
            "Les couleurs",
            "Reconnaître les couleurs.",
            20,
            [
                mcq("De quelle couleur est le soleil ? ☀️", ["Bleu", "Jaune", "Vert"], 1, emoji="☀️"),
                mcq("De quelle couleur est l'herbe ? 🌱", ["Vert", "Rouge", "Violet"], 0, emoji="🌱"),
                mcq("De quelle couleur est une fraise ? 🍓", ["Bleu", "Rouge", "Noir"], 1, emoji="🍓"),
                mcq("De quelle couleur est le ciel ? ☁️", ["Bleu", "Marron", "Rose"], 0, emoji="🌤️"),
            ],
        ),
        theme(
            "maths",
            "ms",
            1,
            "Compter jusqu'à 5",
            "Compter les objets jusqu'à 5.",
            25,
            [
                mcq("Combien de fleurs ? 🌸🌸🌸🌸", ["3", "4", "5"], 1, emoji="🌸"),
                mcq("Combien de poissons ? 🐟🐟🐟🐟🐟", ["4", "5", "6"], 1, emoji="🐟"),
                mcq("Quel nombre est le plus grand ?", ["2", "5", "3"], 1),
                mcq("Quel nombre est le plus petit ?", ["4", "1", "3"], 1),
            ],
        ),
        theme(
            "francais",
            "ms",
            1,
            "Les formes",
            "Reconnaître les formes simples.",
            25,
            [
                mcq("Comment s'appelle cette forme ? ⭕", ["Carré", "Rond", "Triangle"], 1, emoji="⭕"),
                mcq("Comment s'appelle cette forme ? 🔺", ["Triangle", "Rond", "Carré"], 0, emoji="🔺"),
                mcq("Comment s'appelle cette forme ? 🟦", ["Rond", "Carré", "Étoile"], 1, emoji="🟦"),
                mcq("Combien de côtés a un triangle ?", ["2", "3", "4"], 1),
            ],
        ),
        theme(
            "maths",
            "gs",
            1,
            "Compter jusqu'à 10",
            "Compter et comparer jusqu'à 10.",
            30,
            [
                mcq("Combien de billes ? 🔵🔵🔵🔵🔵🔵", ["5", "6", "7"], 1, emoji="🔵"),
                mcq("Quel nombre vient après 7 ?", ["6", "8", "9"], 1),
                mcq("Quel nombre vient avant 10 ?", ["8", "9", "11"], 1),
                math_problem("2 pommes + 3 pommes, ça fait combien de pommes ?", 2 + 3, emoji="🍎"),
                math_problem("Il y a 5 oiseaux, 2 s'envolent. Combien reste-t-il ?", 5 - 2, emoji="🐦"),
            ],
        ),
        theme(
            "francais",
            "gs",
            1,
            "La lettre du début",
            "Reconnaître la première lettre d'un mot.",
            30,
            [
                mcq("Par quelle lettre commence « ballon » ?", ["B", "D", "P"], 0),
                mcq("Par quelle lettre commence « avion » ?", ["O", "A", "E"], 1),
                mcq("Par quelle lettre commence « maison » ?", ["N", "M", "S"], 1),
                mcq("Par quelle lettre commence « soleil » ?", ["S", "C", "L"], 0),
            ],
        ),
    ]


# --------------------------------------------------------------------------- #
# Générateur de leçons de maths (réponses calculées)
# --------------------------------------------------------------------------- #
def maths_ce2() -> list[dict[str, Any]]:
    return [
        theme(
            "maths",
            "ce2",
            1,
            "Additions et soustractions posées",
            "Additionner et soustraire jusqu'à 1000.",
            50,
            [
                math_problem("Calcule : 245 + 178", 245 + 178),
                math_problem("Calcule : 512 + 289", 512 + 289),
                math_problem("Calcule : 634 − 128", 634 - 128),
                math_problem("Calcule : 900 − 356", 900 - 356),
                math_problem("Léa a 340 billes, elle en gagne 275. Combien en a-t-elle ?", 340 + 275, emoji="🔵"),
            ],
        ),
        theme(
            "maths",
            "ce2",
            2,
            "Les tables de multiplication",
            "Maîtriser les tables et multiplier.",
            55,
            [
                pythagore("Complète les tables de 2, 3, 4 et 5.", [2, 3, 4, 5], blanks=6),
                math_problem("Calcule : 6 × 7", 6 * 7),
                math_problem("Calcule : 8 × 4", 8 * 4),
                math_problem("Un sachet contient 9 bonbons. Combien dans 5 sachets ?", 9 * 5, emoji="🍬"),
            ],
        ),
        theme(
            "maths",
            "ce2",
            3,
            "Problèmes du quotidien",
            "Résoudre des problèmes à une étape.",
            60,
            [
                math_problem("Un livre coûte 12 €. Combien coûtent 4 livres ?", 12 * 4, unit="€", emoji="📚"),
                math_problem("On partage 24 gâteaux entre 6 enfants. Combien par enfant ?", 24 // 6, emoji="🍰"),
                math_problem("Il y a 7 boîtes de 8 œufs. Combien d'œufs en tout ?", 7 * 8, emoji="🥚"),
                math_problem(
                    "Un train a 5 wagons de 40 places. Combien de places ?", 5 * 40, unit="places", emoji="🚆"
                ),
            ],
        ),
    ]


def maths_cm1() -> list[dict[str, Any]]:
    return [
        theme(
            "maths",
            "cm1",
            1,
            "Multiplications posées",
            "Multiplier par un nombre à deux chiffres.",
            55,
            [
                math_problem("Calcule : 23 × 12", 23 * 12),
                math_problem("Calcule : 45 × 14", 45 * 14),
                math_problem("Calcule : 123 × 6", 123 * 6),
                math_problem("Calcule : 208 × 5", 208 * 5),
                math_problem("Un carton contient 36 stylos. Combien dans 15 cartons ?", 36 * 15, emoji="🖊️"),
            ],
        ),
        theme(
            "maths",
            "cm1",
            2,
            "La division",
            "Diviser avec des divisions exactes.",
            60,
            [
                math_problem("Calcule : 48 ÷ 6", 48 // 6),
                math_problem("Calcule : 81 ÷ 9", 81 // 9),
                math_problem("Calcule : 144 ÷ 12", 144 // 12),
                math_problem(
                    "On range 96 livres sur 8 étagères identiques. Combien par étagère ?", 96 // 8, emoji="📚"
                ),
            ],
        ),
        theme(
            "maths",
            "cm1",
            3,
            "Les fractions simples",
            "Prendre une fraction d'une quantité.",
            60,
            [
                math_problem("Combien fait la moitié (1/2) de 10 ?", 10 // 2),
                math_problem("Combien fait le quart (1/4) de 20 ?", 20 // 4),
                math_problem("Combien font les trois quarts (3/4) de 12 ?", 12 * 3 // 4),
                math_problem("Combien fait le tiers (1/3) de 18 ?", 18 // 3),
            ],
        ),
    ]


def maths_cm2() -> list[dict[str, Any]]:
    return [
        theme(
            "maths",
            "cm2",
            1,
            "Les nombres décimaux",
            "Additionner et soustraire des décimaux.",
            60,
            [
                math_problem("Calcule : 2,5 + 1,5", 2.5 + 1.5, tolerance=0.01),
                math_problem("Calcule : 3,2 + 1,8", 3.2 + 1.8, tolerance=0.01),
                math_problem("Calcule : 5,7 − 2,4", round(5.7 - 2.4, 2), tolerance=0.01),
                math_problem("Calcule : 10 − 3,5", 10 - 3.5, tolerance=0.01),
                math_problem(
                    "Un ruban de 4,5 m et un de 2,5 m : longueur totale (en m) ?", 4.5 + 2.5, unit="m", tolerance=0.01
                ),
            ],
        ),
        theme(
            "maths",
            "cm2",
            2,
            "Pourcentages et proportions",
            "Calculer un pourcentage simple.",
            65,
            [
                math_problem("Combien fait 50 % de 40 ?", 40 * 50 // 100),
                math_problem("Combien fait 10 % de 200 ?", 200 * 10 // 100),
                math_problem("Combien fait 25 % de 80 ?", 80 * 25 // 100),
                math_problem(
                    "Un jouet à 60 € a 20 % de réduction. Combien d'euros de réduction ?",
                    60 * 20 // 100,
                    unit="€",
                    emoji="🧸",
                ),
            ],
        ),
        theme(
            "maths",
            "cm2",
            3,
            "Problèmes à étapes",
            "Résoudre des problèmes à plusieurs étapes.",
            70,
            [
                math_problem("J'achète 3 cahiers à 4 € et 1 stylo à 3 €. Total ?", 3 * 4 + 3, unit="€", emoji="🛒"),
                math_problem("Une salle a 12 rangées de 15 chaises. Combien de chaises ?", 12 * 15, emoji="🪑"),
                math_problem("450 km en 5 h : combien de km par heure ?", 450 // 5, unit="km/h", emoji="🚗"),
                math_problem(
                    "Un pack de 6 bouteilles coûte 9 €. Prix d'une bouteille ?",
                    9 / 6,
                    unit="€",
                    tolerance=0.01,
                    emoji="🍶",
                ),
            ],
        ),
    ]


# --------------------------------------------------------------------------- #
# Connaissances / langue — CE2, CM1, CM2 (faits simples, grand public)
# --------------------------------------------------------------------------- #
def knowledge_ce2() -> list[dict[str, Any]]:
    return [
        theme(
            "francais",
            "ce2",
            1,
            "La nature des mots",
            "Reconnaître noms, verbes, adjectifs, déterminants.",
            45,
            [
                mcq("Dans « le chat noir », quel mot est un nom ?", ["le", "chat", "noir"], 1),
                mcq("Quel mot est un verbe ?", ["manger", "table", "rouge"], 0),
                mcq("Quel mot est un adjectif ?", ["courir", "grand", "maison"], 1),
                mcq("« le », « la », « les » sont des…", ["déterminants", "verbes", "noms"], 0),
                mcq("Dans « je cours vite », quel est le verbe ?", ["je", "cours", "vite"], 1),
            ],
        ),
        theme(
            "francais",
            "ce2",
            2,
            "Le présent de l'indicatif",
            "Conjuguer au présent.",
            50,
            [
                fill_blanks("Conjugue « chanter » : je…", "Je ___ une chanson.", ["chante"]),
                fill_blanks("Conjugue « finir » : tu…", "Tu ___ ton travail.", ["finis"]),
                fill_blanks("Conjugue « être » : il…", "Il ___ content.", ["est"]),
                fill_blanks("Conjugue « avoir » : nous…", "Nous ___ un chien.", ["avons"]),
                fill_blanks("Conjugue « aller » : vous…", "Vous ___ à l'école.", ["allez"]),
            ],
        ),
        theme(
            "francais",
            "ce2",
            3,
            "Lecture — Le renard et la cigogne",
            "Lire et comprendre un texte.",
            55,
            [
                reading(
                    "Lis attentivement.",
                    "Le renard invite la cigogne à dîner. Il sert la soupe dans une assiette plate. "
                    "La cigogne, avec son long bec, ne peut rien manger ! Plus tard, la cigogne invite "
                    "le renard et sert le repas dans un vase très étroit. Cette fois, c'est le renard "
                    "qui ne peut pas manger. La ruse se retourne contre celui qui l'a commencée.",
                ),
                mcq("Qui invite en premier ?", ["La cigogne", "Le renard", "Le loup"], 1),
                mcq(
                    "Pourquoi la cigogne ne peut pas manger la soupe ?",
                    ["Elle n'a pas faim", "L'assiette est plate", "La soupe est froide"],
                    1,
                ),
                mcq(
                    "Quelle est la morale ?",
                    ["On récolte ce que l'on sème", "Il faut manger vite", "Les renards sont gentils"],
                    0,
                ),
            ],
        ),
        theme(
            "orthographe",
            "ce2",
            1,
            "Le pluriel des noms",
            "Former le pluriel des noms.",
            45,
            [
                fill_blanks("Mets au pluriel : un chat → des…", "des ___", ["chats"]),
                fill_blanks("Mets au pluriel : un cheval → des…", "des ___", ["chevaux"]),
                fill_blanks("Mets au pluriel : un journal → des…", "des ___", ["journaux"]),
                mcq(
                    "Quel est le pluriel de « bijou » ?",
                    ["bijous", "bijoux", "bijoles"],
                    1,
                    explanation="Bijou fait partie des noms en -oux : bijoux, cailloux, choux…",
                ),
            ],
        ),
        theme(
            "orthographe",
            "ce2",
            2,
            "a ou à, et ou est",
            "Distinguer les homophones courants.",
            50,
            [
                mcq("Il ___ mangé une pomme.", ["a", "à"], 0),
                mcq("Je vais ___ Paris.", ["a", "à"], 1),
                mcq("Papa ___ maman sont là.", ["et", "est"], 0),
                mcq("Le ciel ___ bleu.", ["et", "est"], 1),
            ],
        ),
        theme(
            "histoire",
            "ce2",
            1,
            "La Préhistoire",
            "Découvrir la Préhistoire.",
            45,
            [
                reading(
                    "Lis attentivement.",
                    "La Préhistoire est la période la plus ancienne de l'histoire des humains. "
                    "Les hommes préhistoriques vivaient de la chasse et de la cueillette. Ils ont "
                    "appris à tailler des outils en pierre, puis à maîtriser le feu. La Préhistoire "
                    "se termine avec l'invention de l'écriture.",
                ),
                mcq(
                    "De quoi vivaient les hommes préhistoriques ?",
                    ["Du commerce", "De la chasse et de la cueillette", "De l'agriculture industrielle"],
                    1,
                ),
                mcq("Quelle grande découverte ont-ils faite ?", ["L'électricité", "Le feu", "La voiture"], 1),
                mcq("La Préhistoire se termine avec l'invention de…", ["l'écriture", "la roue", "internet"], 0),
            ],
        ),
        theme(
            "monde",
            "ce2",
            1,
            "Le cycle de l'eau",
            "Comprendre le cycle de l'eau.",
            45,
            [
                reading(
                    "Lis attentivement.",
                    "L'eau des mers et des rivières s'évapore avec la chaleur du soleil : elle monte "
                    "dans le ciel. En altitude, la vapeur se refroidit et forme les nuages : c'est la "
                    "condensation. Quand les nuages sont pleins, l'eau retombe en pluie ou en neige : "
                    "ce sont les précipitations. L'eau rejoint alors les rivières et recommence.",
                ),
                mcq("Qu'est-ce qui fait s'évaporer l'eau ?", ["La lune", "La chaleur du soleil", "Le vent seul"], 1),
                mcq(
                    "Comment se forment les nuages ?", ["Par condensation", "Par évaporation du sable", "Par le feu"], 0
                ),
                mcq(
                    "Comment l'eau retombe-t-elle sur Terre ?",
                    ["En précipitations (pluie, neige)", "En fumée", "En lumière"],
                    0,
                ),
            ],
        ),
        theme(
            "geo",
            "ce2",
            1,
            "La France et ses paysages",
            "Découvrir la géographie de la France.",
            45,
            [
                mcq("Quelle est la capitale de la France ?", ["Lyon", "Paris", "Marseille"], 1),
                mcq("Quel fleuve traverse Paris ?", ["La Loire", "La Seine", "Le Rhône"], 1),
                mcq(
                    "Quelle est la plus haute montagne de France ?",
                    ["Le Mont Blanc", "Le Puy de Dôme", "Le Ventoux"],
                    0,
                ),
                mcq(
                    "Quel océan borde l'ouest de la France ?",
                    ["L'océan Atlantique", "L'océan Indien", "L'océan Pacifique"],
                    0,
                ),
            ],
        ),
    ]


def knowledge_cm1() -> list[dict[str, Any]]:
    return [
        theme(
            "francais",
            "cm1",
            1,
            "Passé, présent, futur",
            "Reconnaître le temps d'une phrase.",
            50,
            [
                mcq("« Hier, j'ai joué. » Ce temps est le…", ["passé", "présent", "futur"], 0),
                mcq("« Demain, je partirai. » Ce temps est le…", ["passé", "présent", "futur"], 2),
                mcq("« Maintenant, je mange. » Ce temps est le…", ["passé", "présent", "futur"], 1),
                mcq("Quel mot indique le futur ?", ["hier", "demain", "avant"], 1),
                mcq("Quel mot indique le passé ?", ["hier", "aujourd'hui", "bientôt"], 0),
            ],
        ),
        theme(
            "francais",
            "cm1",
            2,
            "L'imparfait",
            "Conjuguer à l'imparfait.",
            55,
            [
                fill_blanks("« jouer » à l'imparfait : je…", "Quand j'étais petit, je ___ dehors.", ["jouais"]),
                fill_blanks("« finir » à l'imparfait : tu…", "Tu ___ toujours ton assiette.", ["finissais"]),
                fill_blanks("« être » à l'imparfait : il…", "Il ___ très gentil.", ["était"]),
                fill_blanks("« avoir » à l'imparfait : nous…", "Nous ___ un grand jardin.", ["avions"]),
            ],
        ),
        theme(
            "orthographe",
            "cm1",
            1,
            "Les homophones (on/ont, son/sont)",
            "Choisir le bon homophone.",
            50,
            [
                mcq("___ va au parc.", ["On", "Ont"], 0),
                mcq("Ils ___ des jouets.", ["on", "ont"], 1),
                mcq("___ vélo est rouge.", ["Son", "Sont"], 0),
                mcq("Les enfants ___ contents.", ["son", "sont"], 1),
            ],
        ),
        theme(
            "histoire",
            "cm1",
            1,
            "Le Moyen Âge",
            "Découvrir le Moyen Âge.",
            50,
            [
                reading(
                    "Lis attentivement.",
                    "Le Moyen Âge commence après la chute de l'Empire romain. Pendant cette période, "
                    "les seigneurs vivaient dans des châteaux forts, protégés par de hautes murailles. "
                    "Les chevaliers combattaient à cheval. Les paysans travaillaient la terre du seigneur. "
                    "De grandes cathédrales furent construites dans les villes.",
                ),
                mcq(
                    "Où vivaient les seigneurs ?",
                    ["Dans des châteaux forts", "Dans des usines", "Dans des gratte-ciels"],
                    0,
                ),
                mcq("Comment combattaient les chevaliers ?", ["En avion", "À cheval", "En bateau"], 1),
                mcq(
                    "Quels grands bâtiments religieux étaient construits ?",
                    ["Des cathédrales", "Des stades", "Des gares"],
                    0,
                ),
            ],
        ),
        theme(
            "monde",
            "cm1",
            1,
            "Le corps humain",
            "Découvrir le corps humain.",
            50,
            [
                mcq("Quel organe pompe le sang ?", ["Le cœur", "L'estomac", "Le cerveau"], 0),
                mcq("À quoi servent les poumons ?", ["À digérer", "À respirer", "À voir"], 1),
                mcq("Quel organe commande le corps et la pensée ?", ["Le foie", "Le cerveau", "Le muscle"], 1),
                mcq("Le squelette est fait de…", ["muscles", "os", "sang"], 1),
            ],
        ),
        theme(
            "geo",
            "cm1",
            1,
            "L'Europe",
            "Découvrir l'Europe et ses capitales.",
            50,
            [
                mcq("Quelle est la capitale de l'Italie ?", ["Madrid", "Rome", "Berlin"], 1),
                mcq("Quelle est la capitale de l'Allemagne ?", ["Berlin", "Paris", "Vienne"], 0),
                mcq("Quelle est la capitale de l'Espagne ?", ["Lisbonne", "Madrid", "Rome"], 1),
                mcq("La France se situe sur quel continent ?", ["L'Asie", "L'Europe", "L'Afrique"], 1),
            ],
        ),
    ]


def knowledge_cm2() -> list[dict[str, Any]]:
    return [
        theme(
            "francais",
            "cm2",
            1,
            "Le futur simple",
            "Conjuguer au futur simple.",
            55,
            [
                fill_blanks("« aller » au futur : je…", "Demain, j'___ à l'école.", ["irai"]),
                fill_blanks("« être » au futur : tu…", "Tu ___ grand un jour.", ["seras"]),
                fill_blanks("« avoir » au futur : il…", "Il ___ dix ans.", ["aura"]),
                fill_blanks("« manger » au futur : nous…", "Nous ___ au restaurant.", ["mangerons"]),
            ],
        ),
        theme(
            "francais",
            "cm2",
            2,
            "Lecture — comprendre un texte",
            "Lire et comprendre un récit.",
            60,
            [
                reading(
                    "Lis attentivement.",
                    "Antoine trouve une vieille carte au grenier. Une croix rouge marque un endroit "
                    "au fond du jardin, près du vieux chêne. Intrigué, il prend une pelle et se met à "
                    "creuser. Après une heure d'efforts, il découvre une petite boîte en métal. À "
                    "l'intérieur, il ne trouve pas d'or, mais de vieilles photos de famille et une "
                    "lettre de son grand-père. C'était le plus précieux des trésors.",
                ),
                mcq("Où mène la croix rouge de la carte ?", ["Au grenier", "Près du vieux chêne", "À la plage"], 1),
                mcq("Que découvre Antoine dans la boîte ?", ["De l'or", "Des photos et une lettre", "Des bonbons"], 1),
                mcq(
                    "Pourquoi est-ce « le plus précieux des trésors » ?",
                    ["Parce que c'est de l'argent", "Pour sa valeur sentimentale", "Parce que c'est lourd"],
                    1,
                ),
            ],
        ),
        theme(
            "orthographe",
            "cm2",
            1,
            "ses/ces et ce/se",
            "Choisir le bon homophone.",
            55,
            [
                mcq("Il met ___ chaussures (les siennes).", ["ses", "ces"], 0),
                mcq("Regarde ___ oiseaux là-bas.", ["ses", "ces"], 1),
                mcq("___ matin, il pleut.", ["Ce", "Se"], 0),
                mcq("Il ___ lave les mains.", ["ce", "se"], 1),
            ],
        ),
        theme(
            "histoire",
            "cm2",
            1,
            "La Révolution française",
            "Découvrir la Révolution française.",
            55,
            [
                reading(
                    "Lis attentivement.",
                    "En 1789, le peuple français se révolte contre le roi et les inégalités. Le "
                    "14 juillet 1789, les Parisiens prennent la Bastille, une prison symbole du pouvoir "
                    "du roi. La Révolution met fin à la monarchie absolue et proclame la Déclaration des "
                    "droits de l'homme et du citoyen. La devise « Liberté, Égalité, Fraternité » naît de "
                    "cette époque.",
                ),
                mcq("En quelle année commence la Révolution française ?", ["1515", "1789", "1914"], 1),
                mcq("Quel bâtiment est pris le 14 juillet 1789 ?", ["La Bastille", "Le Louvre", "Versailles"], 0),
                mcq(
                    "Quelle devise naît de la Révolution ?",
                    ["Liberté, Égalité, Fraternité", "Travail, Famille, Patrie", "Un pour tous"],
                    0,
                ),
            ],
        ),
        theme(
            "monde",
            "cm2",
            1,
            "L'énergie et l'électricité",
            "Comprendre les énergies.",
            55,
            [
                mcq("Le soleil est une source d'énergie…", ["renouvelable", "polluante", "épuisable"], 0),
                mcq("Lequel est une énergie fossile ?", ["Le vent", "Le pétrole", "Le soleil"], 1),
                mcq(
                    "Qu'est-ce qui produit de l'électricité avec le vent ?",
                    ["Une éolienne", "Un panneau solaire", "Un barrage"],
                    0,
                ),
                mcq("Un barrage utilise la force de…", ["l'eau", "l'air chaud", "la lumière"], 0),
            ],
        ),
        theme(
            "geo",
            "cm2",
            1,
            "Continents et océans",
            "Se repérer sur la planète.",
            55,
            [
                mcq("Quel est le plus grand océan ?", ["L'Atlantique", "Le Pacifique", "L'océan Indien"], 1),
                mcq("Quel est le plus grand continent ?", ["L'Afrique", "L'Asie", "L'Europe"], 1),
                mcq("Sur quel continent se trouve l'Égypte ?", ["L'Afrique", "L'Asie", "L'Amérique"], 0),
                mcq("Le désert du Sahara se trouve en…", ["Afrique", "Australie", "Europe"], 0),
            ],
        ),
    ]


def build_curriculum() -> list[dict[str, Any]]:
    """Assemble l'ensemble du curriculum à insérer."""
    themes: list[dict[str, Any]] = []
    themes += maternelle()
    themes += maths_ce2() + knowledge_ce2()
    themes += maths_cm1() + knowledge_cm1()
    themes += maths_cm2() + knowledge_cm2()
    return themes


def _seed_one(data: dict[str, Any], db: Any, *, dry_run: bool) -> str:
    """Valide et (si non dry-run) insère une leçon. Renvoie un statut lisible."""
    level = LevelEnum(data["level"])
    tier = int(data["tier"])
    lesson_spec = data["lesson"]

    # Validation de forme de tous les exercices (lève ValueError si invalide).
    for raw in data["exercises"]:
        validate_exercise_payload(ExerciseType(raw["type"]), raw.get("content", {}), raw.get("correct_answer", {}))

    label = f"{data['subject_slug']}/{level.value}/T{tier} — {lesson_spec['name']}"
    if dry_run:
        return f"✓ (dry) {label} [{len(data['exercises'])} exos]"

    subject = db.query(Subject).filter(Subject.slug == data["subject_slug"]).first()
    if subject is None:
        subject = Subject(
            name=data["subject_name"], slug=data["subject_slug"], icon=data["subject_icon"], is_active=True
        )
        db.add(subject)
        db.flush()

    path = db.query(LearningPath).filter(LearningPath.subject_id == subject.id, LearningPath.level == level).first()
    if path is None:
        path = LearningPath(subject_id=subject.id, name=f"{subject.name} — {level.value.upper()}", level=level)
        db.add(path)
        db.flush()

    existing = db.query(Lesson).filter(Lesson.path_id == path.id, Lesson.name == lesson_spec["name"]).first()
    if existing is not None:
        return f"= déjà présent : {label}"

    lesson = Lesson(
        path_id=path.id,
        name=lesson_spec["name"],
        description=lesson_spec.get("description"),
        order_index=tier,
        xp_reward=int(lesson_spec.get("xp_reward", 50)),
        is_published=True,
    )
    db.add(lesson)
    db.flush()
    for idx, raw in enumerate(data["exercises"]):
        # difficulty (enum hérité) = défaut du palier ; difficulty_level (1-5,
        # source de vérité de l'XP, issue #6) = surcharge explicite par exercice
        # si fournie, sinon renseignée plus tard par scripts/assess_backfill.py.
        db.add(
            Exercise(
                lesson_id=lesson.id,
                type=ExerciseType(raw["type"]).value,
                question=raw["question"],
                content=raw.get("content", {}),
                correct_answer=raw.get("correct_answer", {}),
                explanation=raw.get("explanation"),
                order_index=idx,
                difficulty=TIER_DIFFICULTY.get(tier, DifficultyEnum.EASY),
                difficulty_level=raw.get("level"),
                media_urls=raw.get("media_urls", {}),
            )
        )
    db.commit()
    return f"+ créé : {label} [{len(data['exercises'])} exos]"


def main(dry_run: bool = False) -> int:
    themes = build_curriculum()
    db = SessionLocal()
    created = skipped = 0
    try:
        for data in themes:
            status = _seed_one(data, db, dry_run=dry_run)
            print(status)
            if status.startswith("+"):
                created += 1
            elif status.startswith("="):
                skipped += 1
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
