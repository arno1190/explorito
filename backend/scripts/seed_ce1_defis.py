"""Seed CE1 — Défis (exercices plus difficiles) pour chaque matière (hors maths).

Ajoute une leçon « Défi » par matière au niveau CE1, composée d'exercices plus
exigeants (``difficulty_level`` 4-5, donc XP plus élevée) : raisonnement en deux
étapes, distracteurs subtils, vocabulaire/orthographe plus fine, analogies…

Les maths sont volontairement exclus (déjà bien pourvus en difficulté). Les
réponses restent correctes par construction. La correction des textes à trous est
insensible à la casse mais **sensible aux accents** (``strip().lower()``) : on
réserve donc les ``fill_blanks`` aux réponses sans accent et on passe par des QCM
pour les pièges d'orthographe accentués.

Idempotent par (parcours, nom de leçon). Chaque défi est placé juste après la
dernière leçon existante de la matière (pas de trou dans la progression).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_defis.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce1"

# Tier du défi par matière = (dernière tier existante) + 1, pour l'afficher en fin
# de parcours sans laisser de tier vide.
DEFI_TIER = {
    "arts": 6,
    "francais": 9,
    "orthographe": 7,
    "histoire": 8,
    "geo": 7,
    "monde": 7,
    "logique": 6,
}


def defis() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    # ---------------------------------------------------------------- Arts
    themes.append(
        theme(
            "arts",
            LEVEL,
            DEFI_TIER["arts"],
            "Défi — Les arts 🎨🏆",
            "Des questions d'art plus difficiles.",
            60,
            [
                mcq(
                    "En mélangeant les trois couleurs primaires, on obtient…",
                    ["du marron", "du blanc", "du jaune vif"],
                    0,
                    level=4,
                ),
                mcq(
                    "Le violon et la guitare appartiennent à la famille des instruments à…",
                    ["cordes", "vent", "percussion"],
                    0,
                    level=4,
                ),
                mcq(
                    "Avec quoi fait-on vibrer les cordes du violon ?",
                    ["un archet", "une baguette", "un marteau"],
                    0,
                    level=5,
                ),
                mcq(
                    "L'orange est une couleur chaude. Laquelle est AUSSI une couleur chaude ?",
                    ["le rouge", "le bleu", "le vert"],
                    0,
                    level=4,
                ),
                mcq(
                    "Le peintre Claude Monet a souvent peint…",
                    ["des jardins et des nénuphars", "des voitures", "des fusées"],
                    0,
                    level=5,
                ),
            ],
        )
    )

    # ------------------------------------------------------------- Français
    themes.append(
        theme(
            "francais",
            LEVEL,
            DEFI_TIER["francais"],
            "Défi — Français 🏝️🏆",
            "Vocabulaire et grammaire plus difficiles.",
            65,
            [
                mcq("Quel est le contraire de « rapide » ?", ["lent", "vite", "grand"], 0, level=4),
                mcq("Quel mot veut dire la même chose que « content » ?", ["joyeux", "triste", "fatigué"], 0, level=4),
                mcq("Complète : « Hier, j'ai ___ une pomme. »", ["mangé", "manger", "mangez"], 0, level=5),
                mcq(
                    "Quelle phrase est correctement écrite ?",
                    ["Les enfants jouent dehors.", "Les enfant joue dehors.", "les enfants joue dehors"],
                    0,
                    level=5,
                ),
                mcq("Le féminin de « un acteur » est…", ["une actrice", "une acteur", "une acteuse"], 0, level=4),
            ],
        )
    )

    # ---------------------------------------------------------- Orthographe
    themes.append(
        theme(
            "orthographe",
            LEVEL,
            DEFI_TIER["orthographe"],
            "Défi — Orthographe ✏️🏆",
            "Pluriels et homophones plus difficiles.",
            65,
            [
                fill_blanks("Au pluriel : un cheval → des…", "des ___", ["chevaux"], level=5),
                mcq("Le pluriel de « un gâteau » est…", ["des gâteaux", "des gâteaus", "des gâteau"], 0, level=4),
                mcq("Le pluriel de « un journal » est…", ["des journaux", "des journals", "des journal"], 0, level=4),
                mcq("Complète : « Il met ___ chaussures. » (les siennes)", ["ses", "ces", "c'est"], 0, level=5),
                mcq("Complète : « Regarde ___ belles fleurs ! » (celles-là)", ["ces", "ses", "s'est"], 0, level=5),
            ],
        )
    )

    # -------------------------------------------------------------- Histoire
    themes.append(
        theme(
            "histoire",
            LEVEL,
            DEFI_TIER["histoire"],
            "Défi — Histoire ⏳🏆",
            "Se repérer dans le temps, en plus difficile.",
            65,
            [
                mcq(
                    "Range du plus jeune au plus âgé :",
                    ["bébé, enfant, adulte", "adulte, enfant, bébé", "enfant, bébé, adulte"],
                    0,
                    level=4,
                ),
                mcq("Combien de mois y a-t-il dans une demi-année ?", ["6", "12", "3"], 0, level=4),
                mcq(
                    "Nos arrière-grands-parents ont vécu…",
                    ["il y a très longtemps", "dans le futur", "demain"],
                    0,
                    level=4,
                ),
                mcq(
                    "Les hommes préhistoriques vivaient avant l'invention de…",
                    ["l'écriture", "le feu", "la parole"],
                    0,
                    level=5,
                ),
                mcq(
                    "Une frise du temps se lit…",
                    ["du passé vers le futur", "du futur vers le passé", "de bas en haut"],
                    0,
                    level=5,
                ),
            ],
        )
    )

    # ------------------------------------------------------------ Géographie
    themes.append(
        theme(
            "geo",
            LEVEL,
            DEFI_TIER["geo"],
            "Défi — Géographie 🗼🏆",
            "Mieux connaître la France et le monde.",
            65,
            [
                mcq(
                    "Quel océan borde la France à l'ouest ?",
                    ["l'océan Atlantique", "l'océan Pacifique", "l'océan Indien"],
                    0,
                    level=5,
                ),
                mcq("Quel pays est un voisin de la France ?", ["l'Espagne", "le Canada", "la Chine"], 0, level=4),
                mcq("Sur une carte, la mer est le plus souvent coloriée en…", ["bleu", "vert", "rouge"], 0, level=4),
                mcq(
                    "La plus haute montagne de France s'appelle le…",
                    ["mont Blanc", "mont d'Or", "mont Rose"],
                    0,
                    level=5,
                ),
                mcq("Combien y a-t-il de continents sur la Terre ?", ["6", "2", "10"], 0, level=4),
            ],
        )
    )

    # ------------------------------------------------- Questionner le monde
    themes.append(
        theme(
            "monde",
            LEVEL,
            DEFI_TIER["monde"],
            "Défi — Questionner le monde 🚀🏆",
            "Des sciences un peu plus difficiles.",
            65,
            [
                mcq(
                    "L'eau bout et devient vapeur. En refroidissant, la vapeur redevient…",
                    ["de l'eau liquide", "du sable", "de la pierre"],
                    0,
                    level=5,
                ),
                mcq(
                    "Un animal qui ne mange que des plantes est un…", ["herbivore", "carnivore", "minéral"], 0, level=4
                ),
                mcq("Le papillon sort d'une…", ["chenille", "graine", "fourmi"], 0, level=5),
                mcq("Quel astre tourne autour de la Terre ?", ["la Lune", "le Soleil", "Mars"], 0, level=4),
                mcq(
                    "Pour pousser, une plante a besoin de lumière, d'eau et…",
                    ["d'air", "de bruit", "de neige"],
                    0,
                    level=4,
                ),
            ],
        )
    )

    # --------------------------------------------------------------- Logique
    themes.append(
        theme(
            "logique",
            LEVEL,
            DEFI_TIER["logique"],
            "Défi — Logique 🧩🏆",
            "Suites, analogies et raisonnement difficiles.",
            60,
            [
                mcq("2, 4, 8, 16, … Quel nombre vient après ?", ["32", "20", "24"], 0, level=5),
                mcq("5, 10, 15, 20, … Quel nombre vient après ?", ["25", "21", "30"], 0, level=4),
                mcq("Chaton est à chat ce que chiot est à…", ["chien", "souris", "cheval"], 0, level=4),
                mcq(
                    "Tom est plus grand que Léa. Léa est plus grande que Zoé. Qui est le plus grand ?",
                    ["Tom", "Léa", "Zoé"],
                    0,
                    level=5,
                ),
                mcq("Il y a 3 chats et 2 chiens. Combien de pattes en tout ?", ["20", "10", "14"], 0, level=5),
            ],
        )
    )

    return themes


def main(dry_run: bool = False) -> int:
    themes = defis()
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} défis CE1 "
            f"({total_ex} exercices, niveau 4-5) — créés: {created}, déjà présents: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
