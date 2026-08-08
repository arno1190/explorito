"""Seed CE1 — Histoire & Géographie (programme officiel, cycle 2).

Couvre les deux grands domaines du programme de CE1 :
- **Histoire** — « Se situer dans le temps » : jours, mois, saisons, calendrier,
  lire l'heure, avant/maintenant (objets, école), générations, frise du temps,
  premiers repères (la Préhistoire).
- **Géographie** — « Se situer dans l'espace » : gauche/droite, l'école et la
  classe, plan & maquette, ville/campagne, paysages, points cardinaux, la Terre
  (continents & océans), se déplacer, repères de la France.

Contenu rédigé (faits simples, grand public, corrects par construction). Chaque
exercice porte un ``difficulty_level`` (1-5) qui pilote l'XP (issue #6), donc pas
besoin de ``assess_backfill.py`` pour ces leçons.

Idempotent par (parcours, nom de leçon) — complète, sans les dupliquer, les
leçons « La France » et « Hier, aujourd'hui, demain » de ``seed_ce1_extra.py``.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_hist_geo.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "ce1"
LIRE = "Lis le texte, puis réponds aux questions."


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    """Stampe le ``difficulty_level`` (1-5) sur chaque exercice de la leçon.

    Les blocs de lecture (``reading``) n'ont pas de bonne réponse et ne
    rapportent pas d'XP : on ne leur affecte pas de difficulté.
    """
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


# --------------------------------------------------------------------------- #
# HISTOIRE — Se situer dans le temps
# --------------------------------------------------------------------------- #
def histoire() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    themes.append(
        theme(
            "histoire",
            LEVEL,
            2,
            "Les jours de la semaine 📅",
            "Connaître et ranger les jours de la semaine.",
            45,
            _lvl(
                [
                    mcq("Combien y a-t-il de jours dans une semaine ?", ["Cinq", "Sept", "Douze"], 1),
                    mcq("Quel jour vient juste après lundi ?", ["Mardi", "Dimanche", "Jeudi"], 0),
                    mcq("Quel jour vient juste avant samedi ?", ["Vendredi", "Dimanche", "Mercredi"], 0),
                    fill_blanks(
                        "Complète : le premier jour de la semaine est le…",
                        "Le premier jour de la semaine est ___",
                        ["lundi"],
                    ),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            3,
            "Les mois et les saisons 🗓️",
            "Connaître les mois de l'année et les quatre saisons.",
            50,
            _lvl(
                [
                    mcq("Combien y a-t-il de mois dans une année ?", ["Dix", "Douze", "Sept"], 1),
                    mcq("Quel est le premier mois de l'année ?", ["Décembre", "Janvier", "Mars"], 1),
                    mcq("Combien y a-t-il de saisons ?", ["Deux", "Quatre", "Six"], 1),
                    mcq(
                        "En quelle saison tombent les feuilles des arbres ?",
                        ["Le printemps", "L'automne", "L'hiver"],
                        1,
                    ),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            3,
            "Lire le calendrier 📆",
            "Se repérer dans le mois et l'année.",
            50,
            _lvl(
                [
                    mcq(
                        "Sur un calendrier, on peut lire…", ["les jours et les mois", "les couleurs", "les animaux"], 0
                    ),
                    mcq("Le jour qui vient après aujourd'hui s'appelle…", ["hier", "demain", "avant-hier"], 1),
                    mcq("Le jour qui était avant aujourd'hui s'appelle…", ["hier", "demain", "bientôt"], 0),
                    mcq("Une année, c'est à peu près…", ["365 jours", "100 jours", "10 jours"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            4,
            "Lire l'heure ⏰",
            "Découvrir l'heure et les moments de la journée.",
            50,
            _lvl(
                [
                    mcq("Combien y a-t-il d'heures dans une journée ?", ["12", "24", "60"], 1),
                    mcq("Combien y a-t-il de minutes dans une heure ?", ["30", "60", "100"], 1),
                    mcq("Le matin, on prend le…", ["dîner", "petit-déjeuner", "goûter"], 1),
                    mcq("Vers midi, on prend le…", ["déjeuner", "petit-déjeuner", "goûter"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            4,
            "Avant et maintenant : l'école 🏫",
            "Comparer l'école d'autrefois et l'école d'aujourd'hui.",
            55,
            [
                reading(
                    LIRE,
                    "Autrefois, les élèves écrivaient avec une plume et de l'encre sur une "
                    "ardoise. Les garçons et les filles n'étaient pas dans la même classe. "
                    "Aujourd'hui, on écrit avec un stylo ou sur un ordinateur, et tous les "
                    "enfants apprennent ensemble.",
                ),
                *_lvl(
                    [
                        mcq(
                            "Avec quoi écrivait-on autrefois ?",
                            ["Une plume et de l'encre", "Un stylo", "Un clavier"],
                            0,
                        ),
                        mcq(
                            "Sur quoi écrivaient les élèves d'autrefois ?",
                            ["Une ardoise", "Un cahier neuf", "Un écran"],
                            0,
                        ),
                        mcq(
                            "Aujourd'hui, dans la classe, il y a…",
                            ["que des garçons", "que des filles", "des garçons et des filles"],
                            2,
                        ),
                    ],
                    2,
                ),
            ],
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            5,
            "Les objets d'hier et d'aujourd'hui 📻",
            "Voir comment les objets ont changé avec le temps.",
            55,
            _lvl(
                [
                    mcq(
                        "Autrefois, pour s'éclairer, on utilisait…",
                        ["une bougie", "une ampoule", "une lampe de poche"],
                        0,
                    ),
                    mcq(
                        "Aujourd'hui, pour s'éclairer, on utilise surtout…",
                        ["une bougie", "une ampoule électrique", "le feu"],
                        1,
                    ),
                    mcq(
                        "Autrefois, pour voyager loin, on utilisait souvent…", ["le cheval", "l'avion", "la voiture"], 0
                    ),
                    fill_blanks(
                        "Complète : aujourd'hui, pour laver le linge, on utilise une machine à…",
                        "une machine à ___",
                        ["laver"],
                    ),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            5,
            "Les générations : la famille 👵",
            "Comprendre le passé de sa famille.",
            55,
            _lvl(
                [
                    mcq("Les parents de tes parents, ce sont tes…", ["cousins", "grands-parents", "voisins"], 1),
                    mcq("Qui est né en premier ?", ["Toi", "Tes parents", "Tes grands-parents"], 2),
                    mcq("Qui est le plus jeune ?", ["Toi", "Ton papa", "Ta mamie"], 0),
                    mcq(
                        "Quand tes grands-parents étaient petits, c'était…",
                        ["dans le futur", "il y a longtemps", "aujourd'hui"],
                        1,
                    ),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            6,
            "La frise du temps ⏳",
            "Ranger le passé, le présent et le futur.",
            55,
            _lvl(
                [
                    mcq("Ce qui s'est déjà passé, c'est le…", ["passé", "présent", "futur"], 0),
                    mcq("Ce qui se passe en ce moment, c'est le…", ["passé", "présent", "futur"], 1),
                    mcq("Ce qui n'est pas encore arrivé, c'est le…", ["passé", "présent", "futur"], 2),
                    mcq(
                        "Sur une frise du temps, on range les événements…",
                        ["dans l'ordre du temps", "par couleur", "par taille"],
                        0,
                    ),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "histoire",
            LEVEL,
            7,
            "Les premiers hommes 🦴",
            "Découvrir la Préhistoire.",
            60,
            [
                reading(
                    LIRE,
                    "Il y a très très longtemps, les premiers hommes vivaient dans des "
                    "grottes. Ils ne savaient pas encore écrire. Ils ont appris à faire du "
                    "feu, à chasser les animaux et à fabriquer des outils en pierre. Sur les "
                    "murs des grottes, ils dessinaient des animaux.",
                ),
                *_lvl(
                    [
                        mcq(
                            "Où vivaient souvent les premiers hommes ?",
                            ["Dans des grottes", "Dans des maisons", "Dans des immeubles"],
                            0,
                        ),
                        mcq("Qu'ont-ils appris à faire ?", ["Le feu", "La télévision", "La voiture"], 0),
                        mcq(
                            "Avec quoi fabriquaient-ils leurs outils ?", ["De la pierre", "Du plastique", "Du métal"], 0
                        ),
                        mcq(
                            "Que dessinaient-ils sur les murs des grottes ?",
                            ["Des animaux", "Des voitures", "Des lettres"],
                            0,
                        ),
                    ],
                    3,
                ),
            ],
        )
    )

    return themes


# --------------------------------------------------------------------------- #
# GÉOGRAPHIE — Se situer dans l'espace
# --------------------------------------------------------------------------- #
def geographie() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    themes.append(
        theme(
            "geo",
            LEVEL,
            2,
            "Ma gauche et ma droite 👋",
            "Se repérer dans l'espace autour de soi.",
            45,
            _lvl(
                [
                    mcq(
                        "Avec quelle main écris-tu le plus souvent ?",
                        ["La main gauche ou droite", "Le pied", "Le nez"],
                        0,
                    ),
                    mcq("Le contraire de « à gauche », c'est…", ["à droite", "en haut", "devant"], 0),
                    mcq("Le contraire de « devant », c'est…", ["derrière", "à côté", "dessus"], 0),
                    mcq("Ce qui est tout en haut, c'est le contraire de…", ["en bas", "à droite", "devant"], 0),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            2,
            "L'école et la classe 🏫",
            "Connaître les espaces proches de l'enfant.",
            45,
            _lvl(
                [
                    mcq(
                        "Où ranges-tu tes affaires en classe ?",
                        ["Dans mon casier ou mon cartable", "Sur le toit", "Dans la cour"],
                        0,
                    ),
                    mcq("Où joues-tu pendant la récréation ?", ["Dans la cour", "Dans la classe", "Sur le tableau"], 0),
                    mcq(
                        "Qui t'apprend à lire et à compter à l'école ?",
                        ["Le maître ou la maîtresse", "Le boulanger", "Le pompier"],
                        0,
                    ),
                    mcq("La pièce où l'on mange à l'école s'appelle…", ["la cantine", "la piscine", "la gare"], 0),
                ],
                1,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            3,
            "Le plan et la maquette 🗺️",
            "Représenter un lieu vu d'en haut.",
            50,
            _lvl(
                [
                    mcq("Un plan, c'est un dessin vu…", ["d'en haut", "de côté", "de dessous"], 0),
                    mcq("À quoi sert un plan ?", ["À se repérer", "À manger", "À dormir"], 0),
                    mcq(
                        "Sur un plan de la classe, on peut voir…",
                        ["les tables et le tableau", "les nuages", "la mer"],
                        0,
                    ),
                    mcq("Une petite copie d'un lieu en volume s'appelle une…", ["maquette", "photo", "chanson"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            3,
            "La ville et la campagne 🏙️",
            "Comparer la ville et la campagne.",
            50,
            _lvl(
                [
                    mcq(
                        "Où y a-t-il beaucoup d'immeubles et de voitures ?",
                        ["À la ville", "À la campagne", "Dans la mer"],
                        0,
                    ),
                    mcq("Où voit-on des champs et des fermes ?", ["À la campagne", "En ville", "Sur un bateau"], 0),
                    mcq(
                        "En ville, pour se déplacer, on peut prendre…", ["le métro ou le bus", "le tracteur", "rien"], 0
                    ),
                    mcq(
                        "À la campagne, on trouve souvent…",
                        ["des animaux de ferme", "beaucoup de gratte-ciels", "le métro"],
                        0,
                    ),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            4,
            "Les paysages 🏔️",
            "Reconnaître différents paysages.",
            55,
            [
                reading(
                    LIRE,
                    "Autour de nous, il y a différents paysages. Au bord de la mer, il y a "
                    "des plages et des bateaux. À la montagne, il y a de hauts sommets "
                    "couverts de neige. À la campagne, il y a des champs et des forêts. En "
                    "ville, il y a des rues et des immeubles.",
                ),
                *_lvl(
                    [
                        mcq(
                            "Où trouve-t-on des plages et des bateaux ?",
                            ["Au bord de la mer", "À la montagne", "En ville"],
                            0,
                        ),
                        mcq(
                            "Où trouve-t-on de hauts sommets enneigés ?",
                            ["À la montagne", "à la mer", "à la campagne"],
                            0,
                        ),
                        mcq(
                            "Où trouve-t-on des champs et des forêts ?",
                            ["À la campagne", "En ville", "Sur un bateau"],
                            0,
                        ),
                    ],
                    2,
                ),
            ],
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            4,
            "Les points cardinaux 🧭",
            "Découvrir le nord, le sud, l'est et l'ouest.",
            55,
            _lvl(
                [
                    mcq("Combien y a-t-il de points cardinaux ?", ["Deux", "Quatre", "Huit"], 1),
                    mcq("Le matin, le soleil se lève à l'…", ["est", "ouest", "nord"], 0),
                    mcq("Le soir, le soleil se couche à l'…", ["est", "ouest", "sud"], 1),
                    mcq("Quel objet aide à trouver le nord ?", ["une boussole", "une règle", "un ballon"], 0),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            5,
            "La Terre : continents et océans 🌍",
            "Découvrir la planète Terre.",
            55,
            _lvl(
                [
                    mcq("Sur quelle planète vivons-nous ?", ["La Terre", "La Lune", "Le Soleil"], 0),
                    mcq("Les grandes étendues d'eau salée s'appellent les…", ["océans", "déserts", "montagnes"], 0),
                    mcq("Sur quel continent se trouve la France ?", ["L'Europe", "L'Afrique", "L'Asie"], 0),
                    mcq("Un objet rond qui représente la Terre s'appelle un…", ["globe", "cube", "livre"], 0),
                ],
                3,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            5,
            "Se déplacer : les transports 🚗",
            "Classer les moyens de transport.",
            55,
            _lvl(
                [
                    mcq("Quel transport roule sur la route ?", ["La voiture", "Le bateau", "L'avion"], 0),
                    mcq("Quel transport vole dans le ciel ?", ["L'avion", "Le train", "Le bateau"], 0),
                    mcq("Quel transport navigue sur l'eau ?", ["Le bateau", "Le vélo", "Le bus"], 0),
                    mcq("Quel transport roule sur des rails ?", ["Le train", "L'avion", "La voiture"], 0),
                ],
                2,
            ),
        )
    )

    themes.append(
        theme(
            "geo",
            LEVEL,
            6,
            "La France : villes et fleuves 🗼",
            "Mieux connaître la France.",
            60,
            _lvl(
                [
                    mcq("Quelle est la capitale de la France ?", ["Marseille", "Paris", "Lille"], 1),
                    mcq("Quel grand fleuve traverse Paris ?", ["La Seine", "La Loire", "Le Rhône"], 0),
                    mcq(
                        "Comment appelle-t-on la forme de la France sur la carte ?",
                        ["l'Hexagone", "le carré", "le rond"],
                        0,
                    ),
                    mcq(
                        "Où trouve-t-on de hautes montagnes en France ?",
                        ["Les Alpes", "au bord de la mer", "à Paris"],
                        0,
                    ),
                ],
                3,
            ),
        )
    )

    return themes


def curriculum() -> list[dict[str, Any]]:
    return histoire() + geographie()


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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE1 Histoire/Géo "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
