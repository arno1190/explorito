"""Seed CE1 — Leçons plus avancées pour les matières déjà complètes (hors maths).

Ajoute, pour chaque matière non-mathématique déjà bien fournie, deux leçons plus
avancées (``difficulty_level`` 3) : un cran au-dessus des bases, mais distinctes
des « Défis » (niveau 4-5). Placées après les leçons existantes (max_tier + 1/2),
sans trou de progression.

Maths exclues (déjà couvertes). Réponses correctes par construction ; correction
des textes à trous insensible à la casse mais sensible aux accents → ``fill_blanks``
réservés aux réponses sans accent.

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_avance.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce1"
LVL = 3  # niveau de difficulté « avancé » (au-dessus des bases, sous les défis)

# Tier de départ par matière = (dernière tier existante) + 1.
BASE_TIER = {
    "arts": 7,
    "francais": 10,
    "geo": 8,
    "histoire": 9,
    "logique": 7,
    "monde": 8,
    "orthographe": 8,
}


def _lvl(exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = LVL
    return exercises


def _lesson(slug: str, offset: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    return theme(slug, LEVEL, BASE_TIER[slug] + offset, name, desc, 55, _lvl(exercises))


def curriculum() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    # ------------------------------------------------------------- Français
    themes.append(
        _lesson(
            "francais",
            0,
            "Passé, présent, futur ⏱️",
            "Reconnaître le temps d'une phrase.",
            [
                mcq("« Hier » indique le…", ["passé", "présent", "futur"], 0),
                mcq("« Demain » indique le…", ["futur", "passé", "présent"], 0),
                mcq("Dans quelle phrase le verbe est au passé ?", ["J'ai mangé.", "Je mange.", "Je mangerai."], 0),
                mcq("« Je joue » est au…", ["présent", "passé", "futur"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "francais",
            1,
            "Synonymes et contraires 🔁",
            "Trouver des mots de sens proche ou opposé.",
            [
                mcq("Quel mot veut dire la même chose que « content » ?", ["joyeux", "triste", "petit"], 0),
                mcq("Quel est le contraire de « grand » ?", ["petit", "gros", "haut"], 0),
                mcq("Quel mot veut dire la même chose que « beau » ?", ["joli", "laid", "vieux"], 0),
                mcq("Quel est le contraire de « chaud » ?", ["froid", "tiède", "doux"], 0),
            ],
        )
    )

    # ---------------------------------------------------------- Orthographe
    themes.append(
        _lesson(
            "orthographe",
            0,
            "Le son [s] : s, ss, c, ç 🐍",
            "Écrire le son [s] de plusieurs façons.",
            [
                fill_blanks("Complète : un poi___on nage dans l'eau.", "un poi___on", ["ss"]),
                mcq("Quel mot s'écrit avec « ç » ?", ["garçon", "garson", "garcon"], 0),
                mcq("Entre deux voyelles, pour le son [s] on écrit souvent…", ["ss", "s", "z"], 0),
                mcq("Le groupe « ci » se prononce…", ["si", "ki", "chi"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "orthographe",
            1,
            "Les accents : é, è, ê",
            "Reconnaître les trois accents.",
            [
                mcq("L'accent dans « école » est un accent…", ["aigu (é)", "grave (è)", "circonflexe (ê)"], 0),
                mcq("Quel mot a un accent grave ?", ["mère", "été", "idée"], 0),
                mcq("Le petit chapeau « ^ » s'appelle l'accent…", ["circonflexe", "aigu", "grave"], 0),
                mcq("« forêt » porte un accent…", ["circonflexe", "aigu", "grave"], 0),
            ],
        )
    )

    # -------------------------------------------------------------- Histoire
    themes.append(
        _lesson(
            "histoire",
            0,
            "Les grandes périodes 🏛️",
            "Découvrir les grandes périodes de l'Histoire.",
            [
                mcq("Quelle est la période la plus ancienne ?", ["la Préhistoire", "le Moyen Âge", "aujourd'hui"], 0),
                mcq("Au Moyen Âge, les seigneurs vivaient dans des…", ["châteaux forts", "gratte-ciels", "usines"], 0),
                mcq("Les chevaliers du Moyen Âge portaient une…", ["armure", "casquette", "cravate"], 0),
                mcq("Quelle invention est la plus récente ?", ["l'ordinateur", "la roue", "le feu"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "histoire",
            1,
            "Lire une frise et les dates 📅",
            "Se repérer avec des dates.",
            [
                mcq("Sur une frise du temps, le passé lointain est plutôt…", ["à gauche", "à droite", "en bas"], 0),
                mcq("L'an 100 vient ___ l'an 200.", ["avant", "après", "pendant"], 0),
                mcq("Quelle date est la plus ancienne ?", ["1500", "1900", "2000"], 0),
                mcq("Une durée de cent ans s'appelle un…", ["siècle", "mois", "jour"], 0),
            ],
        )
    )

    # ------------------------------------------------------------ Géographie
    themes.append(
        _lesson(
            "geo",
            0,
            "Lire une carte et sa légende 🗺️",
            "Comprendre une carte.",
            [
                mcq("À quoi sert la légende d'une carte ?", ["expliquer les symboles", "décorer", "rien"], 0),
                mcq("Sur une carte, les forêts sont souvent coloriées en…", ["vert", "bleu", "rouge"], 0),
                mcq("La rose des vents indique les…", ["directions (nord, sud…)", "couleurs", "animaux"], 0),
                mcq("Une carte représente un lieu vu…", ["d'en haut", "de côté", "de dessous"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "geo",
            1,
            "L'Europe et les pays 🌍",
            "Situer la France en Europe.",
            [
                mcq("La France se trouve sur le continent…", ["Europe", "Afrique", "Asie"], 0),
                mcq("Quel pays voisin de la France est aussi en Europe ?", ["l'Allemagne", "le Brésil", "le Japon"], 0),
                mcq("La monnaie utilisée en France est…", ["l'euro", "le dollar", "le yen"], 0),
                mcq("Les étoiles du drapeau de l'Europe sont de couleur…", ["jaune", "rouge", "verte"], 0),
            ],
        )
    )

    # ------------------------------------------------- Questionner le monde
    themes.append(
        _lesson(
            "monde",
            0,
            "Le cycle de l'eau 💧",
            "Comprendre le voyage de l'eau.",
            [
                mcq("Sous l'effet du soleil, l'eau des mers…", ["s'évapore", "gèle", "disparaît"], 0),
                mcq("La vapeur d'eau forme dans le ciel des…", ["nuages", "étoiles", "cailloux"], 0),
                mcq("Quand il fait froid, l'eau des nuages retombe en…", ["pluie", "fumée", "sable"], 0),
                mcq("L'eau des rivières finit par rejoindre…", ["la mer", "le ciel", "le feu"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "monde",
            1,
            "La chaîne alimentaire 🦊",
            "Qui mange qui dans la nature.",
            [
                mcq("Un animal qui mange d'autres animaux est un…", ["carnivore", "herbivore", "végétal"], 0),
                mcq("La souris peut être mangée par le…", ["chat", "lapin", "mouton"], 0),
                mcq(
                    "À la base de la chaîne alimentaire, il y a souvent…", ["les plantes", "les lions", "les aigles"], 0
                ),
                mcq("Un animal qui mange des plantes ET de la viande est…", ["omnivore", "herbivore", "carnivore"], 0),
            ],
        )
    )

    # ----------------------------------------------------------------- Arts
    themes.append(
        _lesson(
            "arts",
            0,
            "Clair et foncé : les nuances 🎨",
            "Éclaircir et foncer une couleur.",
            [
                mcq("Pour éclaircir une couleur, on ajoute du…", ["blanc", "noir", "bleu"], 0),
                mcq("Pour foncer une couleur, on ajoute du…", ["noir", "blanc", "jaune"], 0),
                mcq("Le rose est un rouge…", ["clair", "foncé", "froid"], 0),
                mcq("Plusieurs tons d'une même couleur, ce sont des…", ["nuances", "formes", "sons"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "arts",
            1,
            "Le rythme en musique 🥁",
            "Écouter et suivre le rythme.",
            [
                mcq("Taper dans les mains en mesure suit le…", ["rythme", "dessin", "goût"], 0),
                mcq("Une musique peut être rapide ou…", ["lente", "rouge", "carrée"], 0),
                mcq("Un son peut être fort ou…", ["doux", "grand", "long"], 0),
                mcq("Quel instrument donne surtout le rythme ?", ["la batterie", "la flûte", "la harpe"], 0),
            ],
        )
    )

    # --------------------------------------------------------------- Logique
    themes.append(
        _lesson(
            "logique",
            0,
            "Les tableaux à double entrée 📊",
            "Lire un tableau.",
            [
                mcq(
                    "Dans un tableau à double entrée, on croise…",
                    ["une ligne et une colonne", "deux dessins", "rien"],
                    0,
                ),
                mcq("Un tableau sert surtout à…", ["ranger des informations", "jouer de la musique", "peindre"], 0),
                mcq("Combien de cases dans un tableau de 2 lignes et 3 colonnes ?", ["6", "5", "2"], 0),
                mcq("Pour lire une case, je regarde sa ligne et sa…", ["colonne", "couleur", "taille"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "logique",
            1,
            "Suites et régularités 🔢",
            "Continuer une suite.",
            [
                mcq("1, 3, 5, 7, … Quel nombre vient après ?", ["9", "8", "10"], 0),
                mcq("20, 18, 16, … Quel nombre vient après ?", ["14", "15", "22"], 0),
                mcq("Rond, carré, rond, carré, … Quelle forme vient après ?", ["rond", "carré", "triangle"], 0),
                mcq("A, B, C, D, … Quelle lettre vient après ?", ["E", "F", "A"], 0),
            ],
        )
    )

    return themes


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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE1 avancées "
            f"({total_ex} exercices, niveau {LVL}) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
