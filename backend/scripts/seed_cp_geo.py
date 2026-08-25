"""Seed CP Géographie — se repérer dans l'espace (programme officiel).

Première année (CP, ~6 ans). Idempotent par (parcours, nom de leçon).
Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_geo.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "geo"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 30 if level == 1 else 35
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # 1 — Gauche et droite
        L(
            1,
            1,
            "CP — Gauche et droite 👈",
            "Reconnaître sa main gauche et sa main droite.",
            [
                mcq(
                    "Avec quelle main écris-tu le plus souvent ? (pour la plupart des enfants)",
                    ["La main droite", "Le pied", "Le nez"],
                    0,
                    emoji="✍️",
                ),
                mcq(
                    "Le cœur bat surtout du côté...",
                    ["gauche", "droit", "du dos"],
                    0,
                    emoji="❤️",
                ),
                mcq(
                    "Tu lèves ta main droite. De l'autre côté, c'est ta main...",
                    ["gauche", "droite aussi", "du milieu"],
                    0,
                    emoji="🙌",
                ),
                mcq(
                    "En France, on lit une ligne de gauche...",
                    ["à droite", "vers le haut", "vers le bas"],
                    0,
                    emoji="📖",
                ),
            ],
        ),
        # 2 — Devant / derrière / à côté
        L(
            2,
            1,
            "CP — Devant, derrière, à côté 🧸",
            "Situer un objet devant, derrière ou à côté.",
            [
                mcq(
                    "Le maître est au tableau et te regarde. Le tableau est...",
                    ["devant toi", "derrière toi", "sous toi"],
                    0,
                    emoji="🧑‍🏫",
                ),
                mcq(
                    "Tu portes ton sac sur le dos. Le sac est...",
                    ["derrière toi", "devant toi", "à côté de toi"],
                    0,
                    emoji="🎒",
                ),
                mcq(
                    "Deux amis se tiennent la main l'un près de l'autre. Ils sont...",
                    ["l'un à côté de l'autre", "l'un derrière l'autre", "l'un sous l'autre"],
                    0,
                    emoji="👫",
                ),
                mcq(
                    "Contraire de « devant » ?",
                    ["derrière", "à côté", "dedans"],
                    0,
                    emoji="🔄",
                ),
            ],
        ),
        # 3 — Sur / sous / dans / entre
        L(
            3,
            1,
            "CP — Sur, sous, dans, entre 📦",
            "Comprendre les mots qui disent où sont les objets.",
            [
                mcq(
                    "Le chat dort sur le canapé. Le chat est...",
                    ["sur le canapé", "sous le canapé", "dans le canapé"],
                    0,
                    emoji="🐱",
                ),
                mcq(
                    "Les chaussures sont rangées sous le lit. Elles sont...",
                    ["sous le lit", "sur le lit", "à côté du toit"],
                    0,
                    emoji="👟",
                ),
                mcq(
                    "Les crayons sont rangés dans la trousse. Ils sont...",
                    ["dans la trousse", "sur la trousse", "sous la trousse"],
                    0,
                    emoji="✏️",
                ),
                mcq(
                    "Léo est assis entre Papa et Maman. Il est...",
                    ["au milieu, entre les deux", "tout devant", "tout au fond"],
                    0,
                    emoji="👨‍👩‍👦",
                ),
            ],
        ),
        # 4 — Se repérer dans la classe
        L(
            4,
            1,
            "CP — Se repérer dans la classe 🏫",
            "Connaître les objets et les coins de la classe.",
            [
                mcq(
                    "Sur quoi le maître écrit-il pour toute la classe ?",
                    ["Le tableau", "La poubelle", "La fenêtre"],
                    0,
                    emoji="📋",
                ),
                mcq(
                    "Où poses-tu ton cahier pour travailler ?",
                    ["Sur le bureau", "Dans la poubelle", "Sous le tapis"],
                    0,
                    emoji="📓",
                ),
                mcq(
                    "Où range-t-on les livres de la classe ?",
                    ["Dans la bibliothèque", "Dans le lavabo", "Dans le cartable du maître"],
                    0,
                    emoji="📚",
                ),
                mcq(
                    "Par où entre-t-on dans la classe ?",
                    ["Par la porte", "Par la cheminée", "Par le plafond"],
                    0,
                    emoji="🚪",
                ),
            ],
        ),
        # 5 — Se repérer dans l'école
        L(
            5,
            1,
            "CP — Se repérer dans l'école 🎒",
            "Connaître les lieux de l'école.",
            [
                mcq(
                    "Où joues-tu pendant la récréation ?",
                    ["Dans la cour", "Dans le bureau du directeur", "Sur le toit"],
                    0,
                    emoji="⚽",
                ),
                mcq(
                    "Où mange-t-on le midi à l'école ?",
                    ["À la cantine", "Dans la classe de sport", "Dans la cour"],
                    0,
                    emoji="🍽️",
                ),
                mcq(
                    "Qui est le chef de l'école ?",
                    ["Le directeur ou la directrice", "Le boulanger", "Le facteur"],
                    0,
                    emoji="🧑‍💼",
                ),
                mcq(
                    "Pour aller d'un étage à l'autre à pied, on prend...",
                    ["l'escalier", "le toboggan", "la balançoire"],
                    0,
                    emoji="🪜",
                ),
            ],
        ),
        # 6 — La maison et ses pièces
        L(
            6,
            1,
            "CP — La maison et ses pièces 🏠",
            "Connaître les pièces de la maison.",
            [
                mcq(
                    "Dans quelle pièce dort-on ?",
                    ["La chambre", "La cuisine", "Le garage"],
                    0,
                    emoji="🛏️",
                ),
                mcq(
                    "Dans quelle pièce prépare-t-on les repas ?",
                    ["La cuisine", "La chambre", "Le salon"],
                    0,
                    emoji="🍳",
                ),
                mcq(
                    "Dans quelle pièce prend-on son bain ?",
                    ["La salle de bain", "Le grenier", "La cuisine"],
                    0,
                    emoji="🛁",
                ),
                mcq(
                    "Où gare-t-on souvent la voiture ?",
                    ["Dans le garage", "Dans la chambre", "Sur le lit"],
                    0,
                    emoji="🚗",
                ),
            ],
        ),
        # 7 — Le quartier / le village
        L(
            7,
            1,
            "CP — Le quartier et le village 🏘️",
            "Découvrir les lieux autour de chez soi.",
            [
                mcq(
                    "Où achète-t-on le pain ?",
                    ["À la boulangerie", "À la pharmacie", "À la piscine"],
                    0,
                    emoji="🥖",
                ),
                mcq(
                    "Où va-t-on chercher des médicaments ?",
                    ["À la pharmacie", "À la boulangerie", "Au stade"],
                    0,
                    emoji="💊",
                ),
                mcq(
                    "Où joue-t-on avec des balançoires et un toboggan ?",
                    ["Au parc", "À la banque", "À la poste"],
                    0,
                    emoji="🛝",
                ),
                mcq(
                    "Comment appelle-t-on le chemin bordé de maisons où l'on marche ?",
                    ["La rue", "Le nuage", "La rivière"],
                    0,
                    emoji="🛣️",
                ),
            ],
        ),
        # 8 — La ville : les lieux
        L(
            8,
            1,
            "CP — La ville et ses lieux 🏙️",
            "Reconnaître les grands lieux d'une ville.",
            [
                mcq(
                    "Où va-t-on pour apprendre à lire et à compter ?",
                    ["À l'école", "Au marché", "À la piscine"],
                    0,
                    emoji="🏫",
                ),
                mcq(
                    "Dans quel bâtiment travaille le maire de la ville ?",
                    ["La mairie", "La gare", "Le cinéma"],
                    0,
                    emoji="🏛️",
                ),
                mcq(
                    "Où achète-t-on des fruits et des légumes sur des étals ?",
                    ["Au marché", "À la mairie", "À l'école"],
                    0,
                    emoji="🍎",
                ),
                mcq(
                    "Où soigne-t-on les personnes malades ou blessées ?",
                    ["À l'hôpital", "À la boulangerie", "Au parc"],
                    0,
                    emoji="🏥",
                ),
            ],
        ),
        # 9 — Lire un plan simple
        L(
            9,
            1,
            "CP — Lire un plan simple 🗺️",
            "Découvrir ce qu'est un plan.",
            [
                mcq(
                    "Un plan sert à...",
                    [
                        "montrer où sont les choses et trouver son chemin",
                        "faire cuire un gâteau",
                        "raconter une histoire",
                    ],
                    0,
                    emoji="🗺️",
                ),
                mcq(
                    "Un plan est dessiné comme si on regardait...",
                    ["d'en haut", "de côté", "les yeux fermés"],
                    0,
                    emoji="👀",
                ),
                mcq(
                    "Sur un plan, un petit dessin qui représente un lieu s'appelle...",
                    ["un symbole", "une chanson", "une odeur"],
                    0,
                    emoji="🔷",
                ),
                mcq(
                    "Sur un plan, la mer et les rivières sont souvent en...",
                    ["bleu", "rouge", "noir"],
                    0,
                    emoji="🌊",
                ),
            ],
        ),
        # 10 — La maquette et la vue de dessus
        L(
            10,
            1,
            "CP — La maquette et la vue de dessus 🧱",
            "Comprendre la vue de dessus avec une maquette.",
            [
                mcq(
                    "Une maquette, c'est...",
                    ["un petit modèle qui ressemble au vrai lieu", "un vrai bâtiment", "un livre d'images"],
                    0,
                    emoji="🧱",
                ),
                mcq(
                    "La « vue de dessus », c'est quand on regarde un objet...",
                    ["d'en haut", "d'en bas", "de derrière"],
                    0,
                    emoji="⬆️",
                ),
                mcq(
                    "Vu de dessus, un ballon rond ressemble à...",
                    ["un rond", "un carré", "un triangle"],
                    0,
                    emoji="⚽",
                ),
                mcq(
                    "Vu de dessus, une table carrée ressemble à...",
                    ["un carré", "un rond", "une étoile"],
                    0,
                    emoji="🟦",
                ),
            ],
        ),
        # 11 — La France : l'Hexagone et le drapeau
        L(
            11,
            2,
            "CP — La France : l'Hexagone et le drapeau 🇫🇷",
            "Reconnaître la forme de la France et son drapeau.",
            [
                mcq(
                    "Comment appelle-t-on souvent la France à cause de sa forme à six côtés ?",
                    ["l'Hexagone", "le Carré", "le Rond"],
                    0,
                    emoji="🗺️",
                ),
                mcq(
                    "Quelles sont les couleurs du drapeau français ?",
                    ["bleu, blanc, rouge", "vert, blanc, rouge", "bleu, jaune, rouge"],
                    0,
                    emoji="🇫🇷",
                ),
                mcq(
                    "Dans quel pays habites-tu si tu parles français à l'école en France ?",
                    ["La France", "L'Espagne", "L'Italie"],
                    0,
                    emoji="🏫",
                ),
                mcq(
                    "Combien de côtés a un hexagone ?",
                    ["6", "4", "3"],
                    0,
                    emoji="⬡",
                ),
            ],
        ),
        # 12 — Paris, la capitale
        L(
            12,
            2,
            "CP — Paris, la capitale de la France 🗼",
            "Découvrir Paris et ses monuments.",
            [
                mcq(
                    "Quelle est la capitale de la France ?",
                    ["Paris", "Lyon", "Marseille"],
                    0,
                    emoji="🗼",
                ),
                mcq(
                    "Quel grand monument en fer se trouve à Paris ?",
                    ["La tour Eiffel", "Le mont Blanc", "Le phare de la mer"],
                    0,
                    emoji="🗼",
                ),
                mcq(
                    "Quel fleuve traverse Paris ?",
                    ["La Seine", "Le Rhône", "La Garonne"],
                    0,
                    emoji="🌊",
                ),
                mcq(
                    "La capitale, c'est la ville où se trouve le gouvernement du pays. Pour la France, c'est...",
                    ["Paris", "Nice", "Bordeaux"],
                    0,
                    emoji="🏛️",
                ),
            ],
        ),
        # 13 — Les paysages
        L(
            13,
            2,
            "CP — La mer, la montagne, la campagne, la ville 🏞️",
            "Reconnaître les grands types de paysages.",
            [
                mcq(
                    "Où trouve-t-on une plage et de l'eau salée ?",
                    ["Au bord de la mer", "À la montagne", "au centre-ville"],
                    0,
                    emoji="🏖️",
                ),
                mcq(
                    "Où trouve-t-on de très hauts sommets, parfois couverts de neige ?",
                    ["À la montagne", "Au bord de la mer", "Dans le désert de sable"],
                    0,
                    emoji="⛰️",
                ),
                mcq(
                    "Où trouve-t-on beaucoup de champs et de fermes ?",
                    ["À la campagne", "En haut de la tour Eiffel", "sous la mer"],
                    0,
                    emoji="🌾",
                ),
                mcq(
                    "Où trouve-t-on beaucoup d'immeubles et de rues ?",
                    ["En ville", "À la campagne", "au sommet de la montagne"],
                    0,
                    emoji="🏙️",
                ),
            ],
        ),
        # 14 — Les points cardinaux
        L(
            14,
            2,
            "CP — Les points cardinaux 🧭",
            "Découvrir le Nord, le Sud, l'Est et l'Ouest.",
            [
                mcq(
                    "Quels sont les quatre points cardinaux ?",
                    ["Nord, Sud, Est, Ouest", "Haut, Bas, Devant, Derrière", "Lundi, Mardi, Mercredi, Jeudi"],
                    0,
                    emoji="🧭",
                ),
                mcq(
                    "Le matin, de quel côté se lève le Soleil ?",
                    ["À l'est", "À l'ouest", "au nord"],
                    0,
                    emoji="🌅",
                ),
                mcq(
                    "Sur une carte, où est presque toujours le Nord ?",
                    ["En haut", "En bas", "à droite tout en bas"],
                    0,
                    emoji="⬆️",
                ),
                mcq(
                    "Quel objet a une aiguille qui montre toujours le Nord ?",
                    ["La boussole", "La montre", "le crayon"],
                    0,
                    emoji="🧭",
                ),
            ],
        ),
        # 15 — La Terre : continents et océans
        L(
            15,
            2,
            "CP — La Terre : continents et océans 🌍",
            "Découvrir la planète Terre en douceur.",
            [
                mcq(
                    "Quelle est la forme de la Terre ?",
                    ["Une boule (une sphère)", "Un carré", "un triangle"],
                    0,
                    emoji="🌍",
                ),
                mcq(
                    "Comment appelle-t-on les grandes étendues d'eau salée sur la Terre ?",
                    ["Les océans", "Les montagnes", "les forêts"],
                    0,
                    emoji="🌊",
                ),
                mcq(
                    "Comment appelle-t-on les grandes étendues de terre où vivent les gens ?",
                    ["Les continents", "Les nuages", "les bateaux"],
                    0,
                    emoji="🗺️",
                ),
                mcq(
                    "Sur un globe ou une carte, les océans sont dessinés en...",
                    ["bleu", "rouge", "noir"],
                    0,
                    emoji="🔵",
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-geo")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Géographie "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
