"""Seed CE1 — Arts & Logique.

Deux matières complémentaires, adaptées au cycle 2 (CE1) :
- **Arts** — arts plastiques & éducation musicale : couleurs primaires et
  mélanges, couleurs chaudes/froides, formes, familles d'instruments, écouter
  la musique (fort/doux, vite/lent), grands peintres (œuvres du domaine public),
  techniques (collage, modelage, découpage).
- **Logique** — raisonnement : suites logiques, intrus, rangement/ordre,
  catégories, pareil/différent & symétrie, déduction simple (si… alors),
  chemins, codage par symboles.

Contenu rédigé (faits simples, grand public, corrects par construction ; œuvres
d'art citées dans le domaine public). Chaque exercice porte un
``difficulty_level`` (1-5) qui pilote l'XP (issue #6).

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_arts_logique.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce1"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    """Stampe le ``difficulty_level`` (1-5) sur chaque exercice noté de la leçon."""
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


# --------------------------------------------------------------------------- #
# ARTS — arts plastiques & musique
# --------------------------------------------------------------------------- #
def arts() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    themes.append(
        theme(
            "arts",
            LEVEL,
            1,
            "Les couleurs primaires 🎨",
            "Connaître les trois couleurs primaires.",
            45,
            _lvl(
                [
                    mcq("Combien y a-t-il de couleurs primaires ?", ["Deux", "Trois", "Six"], 1),
                    mcq("Laquelle est une couleur primaire ?", ["Le vert", "Le rouge", "L'orange"], 1),
                    mcq("Laquelle n'est PAS une couleur primaire ?", ["Le bleu", "Le jaune", "Le violet"], 2),
                    fill_blanks(
                        "Complète : les trois couleurs primaires sont le rouge, le jaune et le…",
                        "le rouge, le jaune et le ___",
                        ["bleu"],
                    ),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            2,
            "Mélanger les couleurs 🖌️",
            "Découvrir les couleurs obtenues par mélange.",
            50,
            _lvl(
                [
                    mcq("Bleu + jaune donne du…", ["vert", "orange", "violet"], 0),
                    mcq("Rouge + jaune donne de l'…", ["orange", "vert", "violet"], 0),
                    mcq("Rouge + bleu donne du…", ["violet", "vert", "marron"], 0),
                    mcq(
                        "Le vert, l'orange et le violet sont des couleurs…",
                        ["primaires", "secondaires", "invisibles"],
                        1,
                    ),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            2,
            "Les formes 🔺",
            "Reconnaître les formes utilisées en art.",
            45,
            _lvl(
                [
                    mcq("Combien de côtés a un carré ?", ["Trois", "Quatre", "Cinq"], 1),
                    mcq("Quelle forme n'a aucun coin ?", ["Le cercle", "Le triangle", "Le carré"], 0),
                    mcq("Un triangle a…", ["3 côtés", "4 côtés", "0 côté"], 0),
                    mcq("Quelle forme ressemble à un ballon de rugby allongé ?", ["Le rond", "L'ovale", "Le carré"], 1),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            3,
            "Couleurs chaudes et froides 🔥❄️",
            "Distinguer les couleurs chaudes et froides.",
            50,
            _lvl(
                [
                    mcq("Laquelle est une couleur chaude ?", ["Le bleu", "Le rouge", "Le vert"], 1),
                    mcq("Laquelle est une couleur froide ?", ["Le bleu", "L'orange", "Le rouge"], 0),
                    mcq("Quelle couleur fait penser au feu et au soleil ?", ["Le rouge", "Le bleu", "Le violet"], 0),
                    mcq("Quelle couleur fait penser à l'eau et à la glace ?", ["Le bleu", "L'orange", "Le jaune"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            3,
            "Les instruments de musique 🎸",
            "Classer les instruments par famille.",
            50,
            _lvl(
                [
                    mcq("La guitare et le violon sont des instruments à…", ["cordes", "vent", "percussion"], 0),
                    mcq("La flûte et la trompette sont des instruments à…", ["vent", "cordes", "percussion"], 0),
                    mcq("Le tambour est un instrument de…", ["percussion", "cordes", "vent"], 0),
                    mcq("Avec quoi joue-t-on du piano ?", ["Les doigts sur les touches", "Un archet", "La bouche"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            4,
            "Écouter la musique 🎵",
            "Reconnaître le rythme et l'intensité d'un son.",
            50,
            _lvl(
                [
                    mcq("Un son très fort, c'est le contraire d'un son…", ["doux", "rapide", "long"], 0),
                    mcq("Une musique très rapide, c'est le contraire d'une musique…", ["lente", "forte", "douce"], 0),
                    mcq(
                        "Le rythme, c'est…",
                        ["la pulsation de la musique", "la couleur du son", "le nom du chanteur"],
                        0,
                    ),
                    mcq("Quand on chante tous ensemble, cela s'appelle une…", ["chorale", "peinture", "sculpture"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            4,
            "Les grands peintres 🖼️",
            "Découvrir des œuvres célèbres (domaine public).",
            55,
            _lvl(
                [
                    mcq("Qui a peint « La Joconde » ?", ["Léonard de Vinci", "Vincent van Gogh", "Claude Monet"], 0),
                    mcq("Van Gogh est célèbre pour ses tableaux de…", ["tournesols", "voitures", "ordinateurs"], 0),
                    mcq("Une personne qui peint des tableaux est un…", ["peintre", "boulanger", "pilote"], 0),
                    mcq("Sur quoi peint-on souvent un tableau ?", ["Une toile", "Une assiette", "Une fenêtre"], 0),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "arts",
            LEVEL,
            5,
            "Créer avec ses mains ✂️",
            "Connaître quelques techniques des arts plastiques.",
            55,
            _lvl(
                [
                    mcq(
                        "Coller des morceaux de papier pour faire une image s'appelle un…",
                        ["collage", "dessin", "chant"],
                        0,
                    ),
                    mcq("Avec de la pâte à modeler, on fait du…", ["modelage", "collage", "coloriage"], 0),
                    mcq("Avec quoi découpe-t-on le papier ?", ["Des ciseaux", "Un pinceau", "Une gomme"], 0),
                    mcq("Avec un pinceau et de la peinture, on fait de la…", ["peinture", "musique", "danse"], 0),
                ],
                2,
            ),
        )
    )

    return themes


# --------------------------------------------------------------------------- #
# LOGIQUE — raisonnement
# --------------------------------------------------------------------------- #
def logique() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    themes.append(
        theme(
            "logique",
            LEVEL,
            1,
            "Les suites logiques 🔢",
            "Trouver ce qui vient après dans une suite.",
            45,
            _lvl(
                [
                    mcq("2, 4, 6, 8, … Quel nombre vient après ?", ["9", "10", "12"], 1),
                    mcq("1, 2, 3, 4, … Quel nombre vient après ?", ["5", "6", "0"], 0),
                    mcq("🔴 🔵 🔴 🔵 🔴 … Quelle couleur vient après ?", ["🔴 rouge", "🔵 bleu", "🟢 vert"], 1),
                    mcq("10, 20, 30, … Quel nombre vient après ?", ["31", "40", "50"], 1),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            2,
            "Trouve l'intrus 🔍",
            "Repérer l'élément qui ne va pas avec les autres.",
            45,
            _lvl(
                [
                    mcq("Quel est l'intrus ?", ["Pomme", "Banane", "Voiture"], 2),
                    mcq("Quel est l'intrus ?", ["Chien", "Chat", "Table"], 2),
                    mcq("Quel est l'intrus ?", ["Rouge", "Bleu", "Carré"], 2),
                    mcq("Quel est l'intrus ?", ["2", "4", "chat"], 2),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            2,
            "Ranger dans l'ordre 📏",
            "Ranger du plus petit au plus grand.",
            50,
            _lvl(
                [
                    mcq("Quel est le plus petit nombre ?", ["7", "3", "9"], 1),
                    mcq("Quel est le plus grand nombre ?", ["12", "8", "20"], 2),
                    mcq("Range du plus petit au plus grand :", ["3, 5, 8", "8, 5, 3", "5, 3, 8"], 0),
                    mcq("Qui est le plus grand ?", ["Une fourmi", "Un chat", "Un éléphant"], 2),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            3,
            "Les catégories 🗂️",
            "Classer les choses par familles.",
            50,
            _lvl(
                [
                    mcq("Dans quelle famille ranger la pomme ?", ["Les fruits", "Les animaux", "Les véhicules"], 0),
                    mcq("Dans quelle famille ranger le vélo ?", ["Les véhicules", "Les fruits", "Les vêtements"], 0),
                    mcq("Lequel est un vêtement ?", ["Le pantalon", "La carotte", "Le camion"], 0),
                    mcq("Lequel est un animal ?", ["Le lapin", "La chaise", "La pomme"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            3,
            "Pareil ou différent 🔁",
            "Comparer et reconnaître la symétrie.",
            50,
            _lvl(
                [
                    mcq("Le contraire de « pareil », c'est…", ["différent", "grand", "rouge"], 0),
                    mcq(
                        "Un papillon a deux ailes qui se ressemblent : on dit qu'il est…",
                        ["symétrique", "cassé", "rond"],
                        0,
                    ),
                    mcq("Combien de bonhommes sont identiques : 😀 😀 😢 ?", ["Deux", "Trois", "Un"], 0),
                    mcq("Quelle paire est identique ?", ["chat / chat", "chat / chien", "3 / 8"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            4,
            "Je réfléchis : si… alors ✅",
            "Faire un raisonnement simple.",
            55,
            _lvl(
                [
                    mcq("S'il pleut, alors je prends mon…", ["parapluie", "maillot de bain", "ballon"], 0),
                    mcq(
                        "Tous les chats ont des moustaches. Minou est un chat, donc Minou a…",
                        ["des moustaches", "des plumes", "des écailles"],
                        0,
                    ),
                    mcq("Il fait nuit, alors dans le ciel on voit…", ["la Lune", "le Soleil", "l'arc-en-ciel"], 0),
                    mcq("J'ai 3 bonbons et j'en mange 1. Il m'en reste…", ["2", "3", "4"], 0),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            4,
            "Les chemins 🧭",
            "Suivre et décrire un déplacement.",
            50,
            _lvl(
                [
                    mcq("Pour aller tout droit, je vais…", ["devant moi", "en arrière", "sur le côté"], 0),
                    mcq("Le contraire d'avancer, c'est…", ["reculer", "sauter", "tourner"], 0),
                    mcq("Dans un labyrinthe, il faut trouver le bon…", ["chemin", "dessin", "nombre"], 0),
                    mcq("Si je tourne à gauche puis à gauche, je vais vers…", ["l'arrière", "le haut", "le ciel"], 0),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "logique",
            LEVEL,
            5,
            "Codage et symboles 🔐",
            "Comprendre un code simple.",
            55,
            _lvl(
                [
                    mcq("Si ⭐ = 1 et 🌙 = 2, alors ⭐⭐ vaut…", ["2", "3", "1"], 0),
                    mcq("Si 🍎 = 5, alors 🍎 + 🍎 vaut…", ["10", "5", "7"], 0),
                    mcq("Si A = 1, B = 2, C = 3, alors C vaut…", ["3", "2", "1"], 0),
                    mcq("Dans un code, un même symbole vaut toujours…", ["la même chose", "n'importe quoi", "zéro"], 0),
                ],
                3,
            ),
        )
    )

    return themes


def curriculum() -> list[dict[str, Any]]:
    return arts() + logique()


def main(dry_run: bool = False) -> int:
    themes = curriculum()
    db = SessionLocal()
    created = skipped = 0
    try:
        for data in themes:
            status = _seed_one(data, db, dry_run=dry_run)
            print(status)
            created += status.startswith("+")
            skipped += status.startswith("=")
        total_ex = sum(len(t["exercises"]) for t in themes)
        print(
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE1 Arts/Logique "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
