"""Seed CP Histoire — se repérer dans le temps (programme officiel).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction ;
notions simples et concrètes pour des enfants de CP (~6 ans).

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_histoire.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "histoire"


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
        # 1 — Le jour et la nuit (tier 1, level 1)
        L(
            1,
            1,
            "CP — Le jour et la nuit ☀️🌙",
            "Reconnaître le jour et la nuit.",
            [
                mcq("Quel astre brille dans le ciel le jour ?", ["Le soleil", "La lune", "Les étoiles"], 0, emoji="☀️"),
                mcq("Quand fait-il tout noir dehors ?", ["Le jour", "La nuit", "À midi"], 1, emoji="🌙"),
                mcq("Quand est-ce que l'on dort, en général ?", ["Le jour", "La nuit", "Le matin"], 1, emoji="😴"),
                mcq(
                    "Quand voit-on les étoiles briller dans le ciel ?",
                    ["Le jour", "La nuit", "À l'heure du déjeuner"],
                    1,
                    emoji="⭐",
                ),
            ],
        ),
        # 2 — Les moments de la journée (tier 2, level 1)
        L(
            2,
            1,
            "CP — Les moments de la journée 🕐",
            "Matin, midi, après-midi, soir : ranger la journée.",
            [
                mcq(
                    "Quel est le premier moment de la journée, quand on se réveille ?",
                    ["Le matin", "Le soir", "La nuit"],
                    0,
                    emoji="🌅",
                ),
                mcq("À quel moment prend-on le déjeuner ?", ["Le matin tôt", "À midi", "La nuit"], 1, emoji="🍽️"),
                mcq(
                    "Comment appelle-t-on le moment après le déjeuner ?",
                    ["Le matin", "L'après-midi", "La nuit"],
                    1,
                    emoji="🕑",
                ),
                mcq(
                    "Quel moment vient juste avant la nuit, quand le soleil se couche ?",
                    ["Le matin", "Le midi", "Le soir"],
                    2,
                    emoji="🌇",
                ),
            ],
        ),
        # 3 — Les jours de la semaine (tier 3, level 1)
        L(
            3,
            1,
            "CP — Les jours de la semaine 📅",
            "Les 7 jours de la semaine et leur ordre.",
            [
                mcq("Combien y a-t-il de jours dans une semaine ?", ["5", "7", "10"], 1, emoji="📅"),
                mcq("Quel jour vient juste après lundi ?", ["Mardi", "Mercredi", "Dimanche"], 0),
                mcq("Quel jour vient juste avant samedi ?", ["Jeudi", "Vendredi", "Dimanche"], 1),
                mcq(
                    "Quel est le premier jour de la semaine ?",
                    ["Dimanche", "Lundi", "Mercredi"],
                    1,
                    explanation="En France, on commence la semaine par lundi.",
                ),
            ],
        ),
        # 4 — Hier, aujourd'hui, demain (tier 4, level 1)
        L(
            4,
            1,
            "CP — Hier, aujourd'hui, demain ⏩",
            "Se repérer entre hier, aujourd'hui et demain.",
            [
                mcq(
                    "Le jour où nous sommes, en ce moment, c'est…",
                    ["hier", "aujourd'hui", "demain"],
                    1,
                    emoji="📆",
                ),
                mcq("Le jour qui vient de passer, c'était…", ["hier", "demain", "aujourd'hui"], 0),
                mcq("Le jour qui va bientôt arriver, ce sera…", ["hier", "demain", "aujourd'hui"], 1),
                mcq(
                    "Si aujourd'hui c'est mardi, quel jour était-ce hier ?",
                    ["Lundi", "Mercredi", "Dimanche"],
                    0,
                    explanation="Hier, c'est le jour d'avant : avant mardi, il y a lundi.",
                ),
            ],
        ),
        # 5 — Les mois de l'année (tier 5, level 1)
        L(
            5,
            1,
            "CP — Les mois de l'année 🗓️",
            "Les 12 mois de l'année et leur ordre.",
            [
                mcq("Combien y a-t-il de mois dans une année ?", ["10", "12", "7"], 1, emoji="🗓️"),
                mcq("Quel est le premier mois de l'année ?", ["Janvier", "Mars", "Décembre"], 0),
                mcq("Quel est le dernier mois de l'année ?", ["Novembre", "Décembre", "Janvier"], 1),
                mcq("Quel mois vient juste après janvier ?", ["Février", "Mars", "Avril"], 0),
            ],
        ),
        # 6 — Les quatre saisons (tier 6, level 1)
        L(
            6,
            1,
            "CP — Les quatre saisons 🍂",
            "Printemps, été, automne, hiver.",
            [
                mcq("Combien y a-t-il de saisons dans l'année ?", ["2", "4", "7"], 1, emoji="🍂"),
                mcq("Pendant quelle saison fait-il très chaud ?", ["L'hiver", "L'été", "L'automne"], 1, emoji="☀️"),
                mcq(
                    "Pendant quelle saison fait-il très froid et parfois il neige ?",
                    ["L'été", "Le printemps", "L'hiver"],
                    2,
                    emoji="❄️",
                ),
                mcq(
                    "Pendant quelle saison les feuilles des arbres tombent ?",
                    ["L'automne", "L'été", "Le printemps"],
                    0,
                    emoji="🍁",
                ),
            ],
        ),
        # 7 — Avant / pendant / après (tier 7, level 1)
        L(
            7,
            1,
            "CP — Avant, pendant, après ➡️",
            "Mettre les actions dans l'ordre.",
            [
                mcq(
                    "Que fait-on d'abord quand on prépare un gâteau ?",
                    ["On mange le gâteau", "On mélange les ingrédients", "On lave l'assiette vide"],
                    1,
                    emoji="🎂",
                ),
                mcq(
                    "Avant de manger, il faut d'abord…",
                    ["débarrasser la table", "se laver les mains", "faire la sieste"],
                    1,
                    emoji="🧼",
                ),
                mcq(
                    "Après avoir mangé, on…",
                    ["met la table", "débarrasse la table", "sort les ingrédients"],
                    1,
                ),
                mcq(
                    "Pour t'habiller, que mets-tu en premier ?",
                    ["Les chaussures", "Les chaussettes", "Le manteau par-dessus tout"],
                    1,
                    emoji="🧦",
                    explanation="On met les chaussettes avant les chaussures.",
                ),
            ],
        ),
        # 8 — Lire un calendrier simple (tier 8, level 1)
        L(
            8,
            1,
            "CP — Lire un calendrier 📆",
            "Retrouver un jour et un mois sur le calendrier.",
            [
                mcq(
                    "À quoi sert un calendrier ?",
                    ["À dessiner", "À voir les jours et les mois", "À écouter"],
                    1,
                    emoji="📆",
                ),
                mcq("Sur le calendrier, combien y a-t-il de mois en tout ?", ["7", "12", "30"], 1),
                mcq(
                    "Environ combien de jours y a-t-il dans un mois ?",
                    ["Environ 30 jours", "Environ 3 jours", "Environ 100 jours"],
                    0,
                ),
                mcq(
                    "Sur un calendrier, une semaine contient combien de jours ?",
                    ["7 jours", "5 jours", "12 jours"],
                    0,
                ),
            ],
        ),
        # 9 — L'emploi du temps de l'école (tier 9, level 1)
        L(
            9,
            1,
            "CP — La semaine d'école 🏫",
            "Se repérer dans la semaine de classe.",
            [
                mcq(
                    "Quel jour la plupart des enfants retournent-ils à l'école après le week-end ?",
                    ["Lundi", "Dimanche", "Samedi"],
                    0,
                    emoji="🏫",
                ),
                mcq(
                    "À l'école, à quel moment de la journée y a-t-il souvent la récréation ?",
                    ["Le matin", "En pleine nuit", "Quand tout le monde dort"],
                    0,
                    emoji="🤾",
                ),
                mcq(
                    "Un emploi du temps sert à savoir…",
                    ["ce qu'on fait chaque jour", "la couleur du ciel", "le prix des jouets"],
                    0,
                ),
                mcq(
                    "Pendant quels jours n'y a-t-il pas d'école, en général ?",
                    ["Le samedi et le dimanche", "Le lundi et le mardi", "Le mercredi et le jeudi"],
                    0,
                    emoji="🎉",
                ),
            ],
        ),
        # 10 — La frise du temps simple (tier 10, level 1)
        L(
            10,
            1,
            "CP — La frise du temps 📏",
            "Ranger des moments du plus ancien au plus récent.",
            [
                mcq(
                    "Sur une frise, les moments les plus anciens sont plutôt…",
                    ["à gauche", "à droite", "cachés"],
                    0,
                    emoji="📏",
                ),
                mcq(
                    "Qu'est-ce qui s'est passé en premier ?",
                    ["Ta naissance", "Ton entrée à l'école", "Aujourd'hui"],
                    0,
                    emoji="👶",
                ),
                mcq(
                    "Dans l'ordre du temps, que fait-on d'abord dans une journée ?",
                    ["Le petit-déjeuner", "Le dîner", "Le coucher"],
                    0,
                ),
                mcq(
                    "Parmi ces moments, lequel est le plus récent ?",
                    ["Quand tu étais bébé", "Quand tu marchais à peine", "Maintenant"],
                    2,
                ),
            ],
        ),
        # 11 — Les âges de la vie (tier 11, level 2)
        L(
            11,
            2,
            "CP — Les âges de la vie 👶",
            "Bébé, enfant, adulte, personne âgée.",
            [
                mcq(
                    "Quel est le tout premier âge de la vie ?",
                    ["Le bébé", "L'adulte", "La personne âgée"],
                    0,
                    emoji="👶",
                ),
                mcq(
                    "Range dans l'ordre : après le bébé vient…",
                    ["l'enfant", "la personne âgée", "le grand-parent"],
                    0,
                    emoji="🧒",
                ),
                mcq(
                    "Une grande personne qui travaille et conduit une voiture est un…",
                    ["bébé", "adulte", "nouveau-né"],
                    1,
                    emoji="🧑",
                ),
                mcq(
                    "Comment appelle-t-on une personne qui a vécu très longtemps, avec souvent des cheveux blancs ?",
                    ["Un bébé", "Un enfant", "Une personne âgée"],
                    2,
                    emoji="👵",
                ),
            ],
        ),
        # 12 — Les générations de la famille (tier 12, level 2)
        L(
            12,
            2,
            "CP — Les générations de la famille 👨‍👩‍👧",
            "Parents, enfants et grands-parents.",
            [
                mcq(
                    "Comment appelle-t-on le papa et la maman d'un enfant ?",
                    ["Les parents", "Les voisins", "Les amis"],
                    0,
                    emoji="👨‍👩‍👧",
                ),
                mcq(
                    "Comment appelle-t-on le papa de ton papa ?",
                    ["Ton grand-père", "Ton cousin", "Ton frère"],
                    0,
                    emoji="👴",
                ),
                mcq(
                    "Comment appelle-t-on la maman de ta maman ?",
                    ["Ta grand-mère", "Ta tante", "Ta sœur"],
                    0,
                    emoji="👵",
                ),
                mcq(
                    "Qui est né le plus tôt, il y a le plus longtemps ?",
                    ["Le grand-père", "Le papa", "L'enfant"],
                    0,
                    explanation="Les grands-parents sont nés avant les parents, qui sont nés avant les enfants.",
                ),
            ],
        ),
        # 13 — Autrefois et aujourd'hui (tier 13, level 2)
        L(
            13,
            2,
            "CP — Autrefois et aujourd'hui 🕯️",
            "Comparer les objets d'hier et d'aujourd'hui.",
            [
                mcq(
                    "Autrefois, pour s'éclairer la nuit, on utilisait surtout…",
                    ["une bougie", "une lampe électrique", "un téléphone"],
                    0,
                    emoji="🕯️",
                ),
                mcq(
                    "Aujourd'hui, pour s'éclairer la nuit, on allume plutôt…",
                    ["une bougie", "une lampe électrique", "un feu de cheminée"],
                    1,
                    emoji="💡",
                ),
                mcq(
                    "Autrefois, pour se déplacer sans voiture, on montait souvent sur un…",
                    ["cheval", "avion", "train à grande vitesse"],
                    0,
                    emoji="🐴",
                ),
                mcq(
                    "Aujourd'hui, pour aller vite sur la route, on prend surtout…",
                    ["une voiture", "une charrette à cheval", "un cheval"],
                    0,
                    emoji="🚗",
                ),
            ],
        ),
        # 14 — Mesurer le temps (tier 14, level 2)
        L(
            14,
            2,
            "CP — Mesurer le temps ⏰",
            "Horloge, sablier, calendrier : à quoi ça sert.",
            [
                mcq(
                    "Quel objet nous donne l'heure ?",
                    ["L'horloge", "La chaise", "Le crayon"],
                    0,
                    emoji="⏰",
                ),
                mcq(
                    "Quel objet mesure un petit temps avec du sable qui coule ?",
                    ["Le sablier", "Le ballon", "Le livre"],
                    0,
                    emoji="⏳",
                ),
                mcq(
                    "Quel objet sert à voir les jours et les mois ?",
                    ["Le calendrier", "La cuillère", "Le tabouret"],
                    0,
                    emoji="📆",
                ),
                mcq(
                    "Sur une horloge, il y a de petites aiguilles qui indiquent…",
                    ["l'heure", "la couleur", "le poids"],
                    0,
                    emoji="🕰️",
                ),
            ],
        ),
        # 15 — Les grandes fêtes de l'année (tier 15, level 2)
        L(
            15,
            2,
            "CP — Les fêtes de l'année 🎉",
            "Des repères dans l'année au fil des saisons.",
            [
                mcq(
                    "Pendant quelle saison fête-t-on Noël ?",
                    ["L'été", "L'hiver", "Le printemps"],
                    1,
                    emoji="🎄",
                    explanation="Noël, le 25 décembre, tombe en hiver.",
                ),
                mcq(
                    "Quelle fête marque le tout début d'une nouvelle année, le 1ᵉʳ janvier ?",
                    ["Le Nouvel An", "Halloween", "Pâques"],
                    0,
                    emoji="🎆",
                ),
                mcq(
                    "À quelle saison a lieu Pâques, quand on cherche des œufs en chocolat dans le jardin ?",
                    ["Au printemps", "En hiver", "En automne"],
                    0,
                    emoji="🥚",
                ),
                mcq(
                    "Quelle fête où l'on se déguise a lieu en automne, à la fin du mois d'octobre ?",
                    ["Halloween", "Noël", "Le Nouvel An"],
                    0,
                    emoji="🎃",
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-histoire")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Histoire "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
