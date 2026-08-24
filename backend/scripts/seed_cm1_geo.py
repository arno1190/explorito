"""Seed CM1 Géographie — programme avancé (niveau élevé).

Idempotent par (parcours, nom de leçon). Faits établis.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_geo.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "geo"


def _lvl(exercises: list[dict[str, Any]], level: int) -> list[dict[str, Any]]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    return exercises


def L(tier: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    xp = 60 if level == 4 else 70
    return theme(SLUG, LEVEL, tier, name, desc, xp, _lvl(exercises, level))


def curriculum() -> list[dict[str, Any]]:
    return [
        # 1 — Se repérer : carte, échelle, légende
        L(
            10,
            4,
            "CM1 — Lire une carte : échelle et légende 🗺️",
            "Comprendre l'échelle, la légende et les symboles d'une carte.",
            [
                mcq(
                    "À quoi sert l'échelle d'une carte ?",
                    [
                        "À connaître la distance réelle entre deux lieux",
                        "À colorier la carte",
                        "À indiquer l'heure",
                    ],
                    0,
                ),
                mcq(
                    "Sur une carte à l'échelle 1/100 000, 1 cm représente...",
                    ["1 kilomètre", "100 mètres", "100 kilomètres"],
                    0,
                    explanation="1 cm sur la carte = 100 000 cm dans la réalité = 1 km.",
                ),
                mcq(
                    "À quoi sert la légende d'une carte ?",
                    [
                        "À expliquer ce que signifient les symboles et les couleurs",
                        "À raconter une histoire",
                        "À décorer la carte",
                    ],
                    0,
                ),
                mcq(
                    "Une carte à grande échelle (par exemple 1/25 000) montre...",
                    [
                        "un petit territoire avec beaucoup de détails",
                        "le monde entier",
                        "seulement les océans",
                    ],
                    0,
                ),
            ],
        ),
        # 2 — Points cardinaux et planisphère
        L(
            11,
            4,
            "CM1 — Points cardinaux et planisphère 🧭",
            "S'orienter avec les points cardinaux et lire un planisphère.",
            [
                mcq(
                    "Quels sont les quatre points cardinaux ?",
                    [
                        "Nord, Sud, Est, Ouest",
                        "Haut, Bas, Gauche, Droite",
                        "Avant, Arrière, Côté, Milieu",
                    ],
                    0,
                ),
                mcq(
                    "Le matin, le Soleil se lève à peu près à l'...",
                    ["Est", "Ouest", "Nord"],
                    0,
                ),
                mcq(
                    "Sur un planisphère, la ligne horizontale qui partage la Terre en deux moitiés s'appelle...",
                    ["l'équateur", "le méridien de Greenwich", "le tropique du Nord"],
                    0,
                ),
                mcq(
                    "Un instrument dont l'aiguille indique le Nord s'appelle...",
                    ["une boussole", "une règle", "un thermomètre"],
                    0,
                ),
            ],
        ),
        # 3 — Le relief de la France
        L(
            12,
            5,
            "CM1 — Le relief de la France 🏔️",
            "Montagnes, sommets et plaines de la France.",
            [
                reading(
                    "Lis ce texte sur le relief français.",
                    "La France possède plusieurs massifs montagneux. Les Alpes, à l'est, abritent "
                    "le mont Blanc, le plus haut sommet des Alpes (environ 4 809 m). Les Pyrénées "
                    "forment une frontière naturelle entre la France et l'Espagne. Le Massif central, "
                    "au centre, est plus ancien et ses sommets sont plus arrondis.",
                ),
                mcq(
                    "Quel est le plus haut sommet des Alpes ?",
                    ["Le mont Blanc", "Le puy de Dôme", "Le pic du Midi"],
                    0,
                    explanation="Le mont Blanc culmine à environ 4 809 mètres.",
                ),
                mcq(
                    "Quelles montagnes forment une frontière entre la France et l'Espagne ?",
                    ["Les Pyrénées", "Les Alpes", "Les Vosges"],
                    0,
                ),
                mcq(
                    "Le Massif central se caractérise par...",
                    [
                        "des montagnes anciennes aux sommets arrondis",
                        "les plus hauts sommets d'Europe",
                        "l'absence totale de relief",
                    ],
                    0,
                ),
            ],
        ),
        # 4 — Les fleuves de France
        L(
            13,
            5,
            "CM1 — Les fleuves de France 🌊",
            "Les quatre grands fleuves et leur parcours.",
            [
                mcq(
                    "Quel est le plus long fleuve de France ?",
                    ["La Loire", "La Seine", "La Garonne"],
                    0,
                    explanation="La Loire mesure environ 1 000 km, c'est le plus long fleuve de France.",
                ),
                mcq(
                    "Quels sont les quatre grands fleuves de France ?",
                    [
                        "La Seine, la Loire, la Garonne et le Rhône",
                        "Le Nil, l'Amazone, le Rhin et la Tamise",
                        "La Loire, le Danube, la Volga et le Pô",
                    ],
                    0,
                ),
                mcq(
                    "Quel fleuve traverse Paris ?",
                    ["La Seine", "Le Rhône", "La Garonne"],
                    0,
                ),
                mcq(
                    "L'endroit où un fleuve se jette dans la mer s'appelle...",
                    ["l'embouchure", "la source", "le méandre"],
                    0,
                ),
            ],
        ),
        # 5 — Les climats en France
        L(
            14,
            4,
            "CM1 — Les climats en France ☀️",
            "Les grands types de climats du territoire français.",
            [
                reading(
                    "Lis ce texte sur les climats.",
                    "En France métropolitaine, on distingue plusieurs climats. Le climat océanique, à "
                    "l'ouest, est doux et pluvieux. Le climat méditerranéen, dans le Sud, est chaud et "
                    "sec en été. Le climat de montagne est froid avec beaucoup de neige en hiver. Le "
                    "climat continental, à l'est, connaît des hivers froids et des étés chauds.",
                ),
                mcq(
                    "Quel climat est chaud et sec en été, dans le Sud de la France ?",
                    ["Le climat méditerranéen", "Le climat océanique", "Le climat de montagne"],
                    0,
                ),
                mcq(
                    "Le climat océanique, à l'ouest, est plutôt...",
                    ["doux et pluvieux", "très sec toute l'année", "glacé en été"],
                    0,
                ),
                mcq(
                    "En montagne, l'hiver est marqué par...",
                    ["le froid et la neige", "la chaleur et la sécheresse", "des vents chauds"],
                    0,
                ),
            ],
        ),
        # 6 — Les grandes villes et métropoles
        L(
            15,
            4,
            "CM1 — Les grandes villes de France 🏙️",
            "Paris et les principales métropoles françaises.",
            [
                mcq(
                    "Quelle est la capitale de la France ?",
                    ["Paris", "Lyon", "Marseille"],
                    0,
                ),
                mcq(
                    "Quelle est la ville la plus peuplée de France ?",
                    ["Paris", "Bordeaux", "Nice"],
                    0,
                    explanation="Paris est à la fois la capitale et la ville la plus peuplée de France.",
                ),
                mcq(
                    "Quelle grande ville est un port important sur la mer Méditerranée ?",
                    ["Marseille", "Lille", "Strasbourg"],
                    0,
                ),
                mcq(
                    "Une très grande ville qui rayonne sur toute une région s'appelle une...",
                    ["métropole", "commune isolée", "hameau"],
                    0,
                ),
            ],
        ),
        # 7 — Habiter en ville
        L(
            16,
            4,
            "CM1 — Habiter en ville 🚇",
            "La vie et l'organisation dans les espaces urbains.",
            [
                mcq(
                    "En ville, les habitants vivent souvent dans...",
                    ["des immeubles et des appartements", "uniquement des fermes", "des igloos"],
                    0,
                ),
                mcq(
                    "Le centre-ville d'une grande ville se reconnaît souvent à...",
                    [
                        "ses nombreux commerces et ses transports",
                        "l'absence totale de magasins",
                        "ses champs de blé",
                    ],
                    0,
                ),
                mcq(
                    "Les zones autour des grandes villes où l'on habite s'appellent...",
                    ["les banlieues", "les déserts", "les montagnes"],
                    0,
                ),
                mcq(
                    "Un avantage de la ville est...",
                    [
                        "beaucoup de services proches (écoles, hôpitaux, transports)",
                        "l'absence de voisins",
                        "aucun magasin",
                    ],
                    0,
                ),
            ],
        ),
        # 8 — Habiter à la campagne
        L(
            17,
            4,
            "CM1 — Habiter à la campagne 🚜",
            "La vie dans les espaces ruraux et l'agriculture.",
            [
                mcq(
                    "À la campagne, une grande partie de l'espace est occupée par...",
                    ["les champs, les prairies et les forêts", "les gratte-ciels", "les métros"],
                    0,
                ),
                mcq(
                    "L'activité qui consiste à cultiver la terre et élever des animaux s'appelle...",
                    ["l'agriculture", "l'industrie", "le tourisme"],
                    0,
                ),
                mcq(
                    "Un petit groupe de maisons à la campagne s'appelle un...",
                    ["village ou hameau", "quartier d'affaires", "aéroport"],
                    0,
                ),
                mcq(
                    "À la campagne, on doit souvent se déplacer davantage en voiture car...",
                    [
                        "les services sont plus éloignés les uns des autres",
                        "il n'y a pas de routes",
                        "les distances sont toujours très courtes",
                    ],
                    0,
                ),
            ],
        ),
        # 9 — Se déplacer en France
        L(
            18,
            5,
            "CM1 — Se déplacer en France 🚄",
            "Les transports et les réseaux qui relient le territoire.",
            [
                mcq(
                    "Le train à grande vitesse français s'appelle le...",
                    ["TGV", "RER", "TER"],
                    0,
                ),
                mcq(
                    "Pour transporter des marchandises très loin d'un continent à l'autre, on utilise surtout...",
                    ["le bateau et l'avion", "le vélo", "la trottinette"],
                    0,
                ),
                mcq(
                    "Les grandes routes gratuites ou payantes qui relient les villes rapidement sont...",
                    ["les autoroutes", "les sentiers", "les chemins de campagne"],
                    0,
                ),
                mcq(
                    "Un avantage des transports en commun (train, bus, métro) est...",
                    [
                        "transporter beaucoup de personnes en polluant moins par voyageur",
                        "qu'ils ne servent à rien",
                        "qu'ils sont interdits en ville",
                    ],
                    0,
                ),
            ],
        ),
        # 10 — Les pays voisins de la France
        L(
            19,
            5,
            "CM1 — Les pays voisins de la France 🌍",
            "Les États frontaliers de la France métropolitaine.",
            [
                reading(
                    "Lis ce texte sur les frontières.",
                    "La France métropolitaine partage ses frontières avec plusieurs pays : la Belgique "
                    "et le Luxembourg au nord, l'Allemagne, la Suisse et l'Italie à l'est, l'Espagne et "
                    "Andorre au sud, et Monaco au sud-est. Certaines frontières suivent des reliefs, "
                    "comme les Pyrénées avec l'Espagne ou les Alpes avec l'Italie.",
                ),
                mcq(
                    "Quel pays est séparé de la France par les Pyrénées ?",
                    ["L'Espagne", "L'Allemagne", "La Belgique"],
                    0,
                ),
                mcq(
                    "Lequel de ces pays est un voisin de la France ?",
                    ["L'Allemagne", "Le Portugal", "La Grèce"],
                    0,
                ),
                mcq(
                    "Quel petit pays se trouve au nord-est, entre la France, la Belgique et l'Allemagne ?",
                    ["Le Luxembourg", "La Norvège", "L'Autriche"],
                    0,
                ),
            ],
        ),
        # 11 — L'Europe et l'Union européenne
        L(
            20,
            5,
            "CM1 — L'Europe et l'Union européenne 🇪🇺",
            "Le continent européen et l'Union européenne.",
            [
                mcq(
                    "L'Union européenne est...",
                    [
                        "une union de pays européens qui coopèrent ensemble",
                        "un seul très grand pays",
                        "un océan",
                    ],
                    0,
                ),
                mcq(
                    "Quelle monnaie est utilisée en France et dans de nombreux pays de l'Union européenne ?",
                    ["L'euro", "Le dollar", "La livre"],
                    0,
                ),
                mcq(
                    "Le drapeau de l'Union européenne est bleu avec...",
                    ["un cercle de douze étoiles jaunes", "trois bandes rouges", "un soleil"],
                    0,
                ),
                mcq(
                    "La France fait partie...",
                    ["du continent européen", "du continent africain", "du continent asiatique"],
                    0,
                ),
            ],
        ),
        # 12 — Les continents et les océans
        L(
            21,
            5,
            "CM1 — Les continents et les océans 🌏",
            "Les grands ensembles de la planète Terre.",
            [
                mcq(
                    "Combien y a-t-il de continents sur Terre ?",
                    ["6", "3", "10"],
                    0,
                    explanation="On compte généralement 6 continents.",
                ),
                mcq(
                    "Combien y a-t-il d'océans sur Terre ?",
                    ["5", "2", "8"],
                    0,
                ),
                mcq(
                    "Quel est le plus grand océan du monde ?",
                    ["L'océan Pacifique", "L'océan Atlantique", "L'océan Indien"],
                    0,
                ),
                mcq(
                    "Sur quel continent se trouve la France ?",
                    ["L'Europe", "L'Amérique", "L'Océanie"],
                    0,
                ),
            ],
        ),
        # 13 — Les grands paysages du monde
        L(
            22,
            5,
            "CM1 — Les grands paysages du monde 🏜️",
            "Déserts, forêts, banquises et autres milieux.",
            [
                mcq(
                    "Un vaste espace très sec, chaud et couvert de sable s'appelle un...",
                    ["désert", "glacier", "marais"],
                    0,
                ),
                mcq(
                    "La grande forêt très humide autour de l'équateur s'appelle la...",
                    ["forêt tropicale", "toundra", "steppe"],
                    0,
                ),
                mcq(
                    "Aux pôles Nord et Sud, on trouve surtout...",
                    ["de la glace et du froid", "des plages chaudes", "des déserts de sable"],
                    0,
                ),
                mcq(
                    "Une très haute chaîne de montagnes en Asie, avec le plus haut sommet du monde, est...",
                    ["l'Himalaya", "les Vosges", "le Jura"],
                    0,
                    explanation="L'Everest, dans l'Himalaya, est le plus haut sommet du monde.",
                ),
            ],
        ),
        # 14 — Le tourisme en France
        L(
            23,
            4,
            "CM1 — Le tourisme en France 🗼",
            "Pourquoi la France attire de nombreux visiteurs.",
            [
                reading(
                    "Lis ce texte sur le tourisme.",
                    "La France est l'un des pays les plus visités au monde. Les touristes viennent "
                    "admirer des monuments comme la tour Eiffel à Paris, profiter des plages de la "
                    "Méditerranée, faire du ski dans les Alpes ou visiter des châteaux comme ceux de "
                    "la Loire. Le tourisme fait travailler beaucoup de personnes : hôtels, restaurants, "
                    "musées et transports.",
                ),
                mcq(
                    "Quel monument célèbre se trouve à Paris ?",
                    ["La tour Eiffel", "La statue de la Liberté", "Le Colisée"],
                    0,
                ),
                mcq(
                    "En hiver, on peut faire du ski dans...",
                    ["les Alpes", "le désert", "la mer"],
                    0,
                ),
                mcq(
                    "Le tourisme est important car il...",
                    [
                        "fait travailler beaucoup de gens (hôtels, restaurants, musées)",
                        "empêche les gens de voyager",
                        "ne rapporte rien du tout",
                    ],
                    0,
                ),
            ],
        ),
        # 15 — Population et densité
        L(
            24,
            5,
            "CM1 — Population et densité 👥",
            "Comprendre où vivent les habitants et la densité.",
            [
                mcq(
                    "La densité de population, c'est...",
                    [
                        "le nombre d'habitants pour un espace donné (par km²)",
                        "la taille des maisons",
                        "la hauteur des montagnes",
                    ],
                    0,
                ),
                mcq(
                    "Un espace où vivent beaucoup d'habitants au km² est dit...",
                    ["densément peuplé", "désert", "inhabité"],
                    0,
                ),
                mcq(
                    "En France, les habitants sont plus nombreux...",
                    [
                        "dans les grandes villes et leurs alentours",
                        "au sommet des montagnes",
                        "au milieu des forêts",
                    ],
                    0,
                ),
                mcq(
                    "Une région de montagne isolée est généralement...",
                    ["peu peuplée", "la plus peuplée du pays", "sans aucun relief"],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Géographie "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
