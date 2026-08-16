"""Seed CE2 Géographie — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_geo.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "geo"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 55 if level == 3 else 60
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # 1 — Lire un plan et une carte (la légende)
        L(
            10,
            3,
            "CE2 — Lire un plan et sa légende 🗺️",
            "Comprendre la légende, les couleurs et les symboles d'une carte.",
            [
                mcq(
                    "À quoi sert la légende d'une carte ?",
                    [
                        "À expliquer ce que veulent dire les symboles et les couleurs",
                        "À dessiner des animaux",
                        "À raconter une histoire",
                    ],
                    0,
                ),
                mcq(
                    "Sur une carte, de quelle couleur sont souvent la mer et les océans ?",
                    ["En bleu", "En rouge", "En jaune"],
                    0,
                ),
                mcq(
                    "Sur une carte, les forêts sont souvent représentées en...",
                    ["vert", "bleu", "noir"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on la vue d'un lieu dessinée comme si on le regardait d'en haut ?",
                    ["Un plan", "Une photo de vacances", "Un dessin animé"],
                    0,
                ),
            ],
        ),
        # 2 — Les points cardinaux et la boussole
        L(
            11,
            3,
            "CE2 — Les points cardinaux et la boussole 🧭",
            "Se repérer avec le Nord, le Sud, l'Est et l'Ouest.",
            [
                mcq(
                    "Quels sont les quatre points cardinaux ?",
                    ["Nord, Sud, Est, Ouest", "Haut, Bas, Gauche, Droite", "Rouge, Vert, Bleu, Jaune"],
                    0,
                ),
                mcq(
                    "À quoi sert une boussole ?",
                    ["À indiquer les directions, surtout le Nord", "À mesurer la température", "À donner l'heure"],
                    0,
                ),
                mcq(
                    "Le matin, de quel côté le Soleil se lève-t-il ?",
                    ["À l'est", "À l'ouest", "Au nord"],
                    0,
                ),
                mcq(
                    "Sur une carte, où se trouve généralement le Nord ?",
                    ["En haut", "En bas", "À droite"],
                    0,
                ),
            ],
        ),
        # 3 — Le planisphère et l'équateur
        L(
            12,
            3,
            "CE2 — Le planisphère et l'équateur 🌍",
            "Découvrir la carte du monde, l'équateur et les continents.",
            [
                mcq(
                    "Qu'est-ce qu'un planisphère ?",
                    ["Une carte de toute la Terre à plat", "Une carte d'une seule ville", "Un livre de recettes"],
                    0,
                ),
                mcq(
                    "L'équateur est une ligne imaginaire qui partage la Terre en deux...",
                    ["hémisphères (Nord et Sud)", "océans", "montagnes"],
                    0,
                ),
                mcq(
                    "Près de l'équateur, le climat est généralement...",
                    ["chaud", "très froid", "enneigé toute l'année"],
                    0,
                ),
                mcq(
                    "Combien y a-t-il de continents sur Terre ?",
                    ["6", "3", "10"],
                    0,
                ),
            ],
        ),
        # 4 — Les paysages de montagne
        L(
            13,
            3,
            "CE2 — Les paysages de montagne ⛰️",
            "Reconnaître les sommets, les vallées et la vie en montagne.",
            [
                mcq(
                    "Qu'est-ce qui recouvre souvent le sommet des hautes montagnes ?",
                    ["De la neige", "Du sable", "Des vagues"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on le point le plus haut d'une montagne ?",
                    ["Le sommet", "La vallée", "La plage"],
                    0,
                ),
                mcq(
                    "Quelle activité pratique-t-on à la montagne en hiver ?",
                    ["Le ski", "La plongée sous-marine", "La pêche en mer"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on l'espace bas situé entre deux montagnes ?",
                    ["Une vallée", "Un sommet", "Une île"],
                    0,
                ),
            ],
        ),
        # 5 — Les paysages de bord de mer
        L(
            14,
            3,
            "CE2 — Les paysages de bord de mer 🏖️",
            "Découvrir la côte, les plages et les marées.",
            [
                mcq(
                    "Comment appelle-t-on l'endroit où la terre rencontre la mer ?",
                    ["La côte", "La forêt", "La montagne"],
                    0,
                ),
                mcq(
                    "Sur une plage, on trouve surtout...",
                    ["du sable ou des galets", "de la neige", "des champs de blé"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on le mouvement de la mer qui monte puis descend ?",
                    ["Les marées", "Les nuages", "Le vent"],
                    0,
                ),
                mcq(
                    "Un bateau qui attrape des poissons est un bateau de...",
                    ["pêche", "course automobile", "pompiers"],
                    0,
                ),
            ],
        ),
        # 6 — Les paysages de campagne
        L(
            15,
            3,
            "CE2 — Les paysages de campagne 🌾",
            "Découvrir les champs, les fermes et le travail agricole.",
            [
                mcq(
                    "À la campagne, on trouve surtout...",
                    ["des champs et des fermes", "de grands gratte-ciels", "beaucoup de métros"],
                    0,
                ),
                mcq(
                    "Qui cultive les champs et élève les animaux à la campagne ?",
                    ["L'agriculteur", "Le pilote d'avion", "Le marin"],
                    0,
                ),
                mcq(
                    "Que peut-on faire pousser dans un champ ?",
                    ["Du blé", "Du béton", "Des voitures"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on l'endroit où vivent des vaches, des poules et des cochons ?",
                    ["Une ferme", "Un aéroport", "Un supermarché"],
                    0,
                ),
            ],
        ),
        # 7 — Les paysages de ville
        L(
            16,
            4,
            "CE2 — Les paysages de ville 🏙️",
            "Comprendre la ville : immeubles, transports et habitants.",
            [
                mcq(
                    "En ville, on trouve beaucoup de...",
                    ["immeubles et de rues", "champs de blé", "vagues"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on un très grand et très haut immeuble ?",
                    ["Un gratte-ciel", "Une grange", "Une cabane"],
                    0,
                ),
                mcq(
                    "Quel moyen de transport trouve-t-on souvent dans les grandes villes ?",
                    ["Le métro", "Le tracteur", "Le télésiège"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on une personne qui habite dans une ville ?",
                    ["Un citadin", "Un marin", "Un montagnard"],
                    0,
                ),
            ],
        ),
        # 8 — Les fleuves de France
        L(
            17,
            4,
            "CE2 — Les fleuves de France 🌊",
            "Reconnaître la Seine, la Loire, le Rhône et la Garonne.",
            [
                mcq(
                    "Quel est le plus long fleuve de France ?",
                    ["La Loire", "La Seine", "La Garonne"],
                    0,
                ),
                mcq(
                    "Quel fleuve traverse Paris ?",
                    ["La Seine", "Le Rhône", "La Garonne"],
                    0,
                ),
                mcq(
                    "Quel fleuve traverse Lyon et se jette dans la mer Méditerranée ?",
                    ["Le Rhône", "La Loire", "La Seine"],
                    0,
                ),
                mcq(
                    "Quel fleuve arrose la ville de Bordeaux ?",
                    ["La Garonne", "La Seine", "Le Rhin"],
                    0,
                ),
            ],
        ),
        # 9 — Les montagnes de France
        L(
            18,
            4,
            "CE2 — Les montagnes de France 🏔️",
            "Situer les Alpes, les Pyrénées et le Massif central.",
            [
                mcq(
                    "Quel est le plus haut sommet des Alpes et de France ?",
                    ["Le mont Blanc", "Le puy de Dôme", "Le Vignemale"],
                    0,
                ),
                mcq(
                    "Quelle chaîne de montagnes sépare la France de l'Espagne ?",
                    ["Les Pyrénées", "Les Alpes", "Les Vosges"],
                    0,
                ),
                mcq(
                    "Où se trouve le Massif central ?",
                    ["Au centre de la France", "Au bord de la mer", "Au pôle Nord"],
                    0,
                ),
                mcq(
                    "Dans quelle partie de la France se trouvent les Alpes ?",
                    ["À l'est (au sud-est)", "À l'ouest", "Au nord"],
                    0,
                ),
            ],
        ),
        # 10 — Les mers et l'océan autour de la France
        L(
            19,
            4,
            "CE2 — Les mers autour de la France 🌊",
            "Identifier l'Atlantique, la Méditerranée et la Manche.",
            [
                mcq(
                    "Quel grand océan borde la France à l'ouest ?",
                    ["L'océan Atlantique", "L'océan Pacifique", "L'océan Indien"],
                    0,
                ),
                mcq(
                    "Quelle mer se trouve au sud de la France ?",
                    ["La mer Méditerranée", "La mer du Nord", "La mer Rouge"],
                    0,
                ),
                mcq(
                    "Quelle mer sépare la France du sud de l'Angleterre ?",
                    ["La Manche", "La mer Noire", "La mer Baltique"],
                    0,
                ),
                mcq(
                    "Quel goût a l'eau de mer ?",
                    ["Salé", "Sucré", "Acide comme le citron"],
                    0,
                ),
            ],
        ),
        # 11 — Se déplacer : les moyens de transport
        L(
            20,
            3,
            "CE2 — Se déplacer : les transports 🚆",
            "Reconnaître les moyens de transport et où ils circulent.",
            [
                mcq(
                    "Quel moyen de transport vole dans le ciel ?",
                    ["L'avion", "Le bateau", "Le train"],
                    0,
                ),
                mcq(
                    "Quel moyen de transport se déplace sur des rails ?",
                    ["Le train", "L'avion", "Le vélo"],
                    0,
                ),
                mcq(
                    "Pour traverser la mer, on peut prendre...",
                    ["un bateau", "un tracteur", "un métro"],
                    0,
                ),
                mcq(
                    "Quel moyen de transport ne pollue pas et avance grâce à la force des jambes ?",
                    ["Le vélo", "La voiture", "L'avion"],
                    0,
                ),
            ],
        ),
        # 12 — L'Europe et l'euro
        L(
            21,
            4,
            "CE2 — L'Europe et l'euro 🇪🇺",
            "Situer la France en Europe et connaître sa monnaie.",
            [
                mcq(
                    "Sur quel continent se trouve la France ?",
                    ["L'Europe", "L'Afrique", "L'Asie"],
                    0,
                ),
                mcq(
                    "Quelle monnaie utilise-t-on en France ?",
                    ["L'euro", "Le dollar", "Le yen"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on le groupe de pays d'Europe qui coopèrent ensemble ?",
                    ["L'Union européenne", "L'équateur", "Le planisphère"],
                    0,
                ),
                mcq(
                    "Quel pays est un voisin de la France ?",
                    ["L'Espagne", "Le Japon", "Le Brésil"],
                    0,
                ),
            ],
        ),
        # 13 — Les grandes villes de France
        L(
            22,
            4,
            "CE2 — Les grandes villes de France 🗼",
            "Découvrir Paris, Marseille et Lyon.",
            [
                mcq(
                    "Quelle est la capitale de la France ?",
                    ["Paris", "Marseille", "Lyon"],
                    0,
                ),
                mcq(
                    "Quelle grande ville française se trouve au bord de la mer Méditerranée ?",
                    ["Marseille", "Paris", "Lille"],
                    0,
                ),
                mcq(
                    "Quel monument célèbre se trouve à Paris ?",
                    ["La tour Eiffel", "Le Mont-Saint-Michel", "Le pont du Gard"],
                    0,
                ),
                mcq(
                    "Quelle est la ville la plus peuplée de France ?",
                    ["Paris", "Lyon", "Marseille"],
                    0,
                ),
            ],
        ),
        # 14 — Le climat et les saisons
        L(
            23,
            3,
            "CE2 — Le climat et les saisons 🍂",
            "Comprendre les quatre saisons et le temps qu'il fait.",
            [
                mcq(
                    "Combien y a-t-il de saisons dans une année ?",
                    ["4", "2", "6"],
                    0,
                ),
                mcq(
                    "Pendant quelle saison fait-il le plus froid en France ?",
                    ["L'hiver", "L'été", "Le printemps"],
                    0,
                ),
                mcq(
                    "Pendant quelle saison les feuilles des arbres tombent-elles ?",
                    ["L'automne", "L'été", "L'hiver"],
                    0,
                ),
                mcq(
                    "Pendant quelle saison fait-il généralement le plus chaud en France ?",
                    ["L'été", "L'hiver", "L'automne"],
                    0,
                ),
            ],
        ),
        # 15 — Habiter la ville / habiter la campagne
        L(
            24,
            4,
            "CE2 — Habiter la ville ou la campagne 🏡",
            "Comparer la vie en ville et la vie à la campagne.",
            [
                mcq(
                    "À la campagne, il y a généralement...",
                    ["moins d'habitants et plus de nature", "beaucoup de gratte-ciels", "beaucoup de métros"],
                    0,
                ),
                mcq(
                    "En ville, pour aller à l'école, on peut souvent prendre...",
                    ["le bus ou le métro", "le tracteur", "le télésiège"],
                    0,
                ),
                mcq(
                    "Où trouve-t-on le plus de champs et de fermes ?",
                    ["À la campagne", "En centre-ville", "Dans le métro"],
                    0,
                ),
                mcq(
                    "En ville, les habitations sont surtout des...",
                    ["immeubles et des appartements", "fermes isolées", "cabanes dans les arbres"],
                    0,
                ),
            ],
        ),
    ]


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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Géographie "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
