"""Seed CE2 Histoire — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction ;
faits historiques simples et grand public.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_histoire.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "histoire"


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
        # 1 — Siècle et millénaire (tier 10, level 3)
        L(
            10,
            3,
            "CE2 — Le siècle et le millénaire ⏳",
            "Se repérer dans le temps : compter en siècles et en millénaires.",
            [
                mcq("Combien d'années y a-t-il dans un siècle ?", ["10 ans", "100 ans", "1000 ans"], 1),
                mcq("Combien d'années y a-t-il dans un millénaire ?", ["100 ans", "1000 ans", "2000 ans"], 1),
                mcq("Combien de siècles y a-t-il dans un millénaire ?", ["5 siècles", "10 siècles", "100 siècles"], 1),
                mcq(
                    "La Révolution française de 1789 appartient à quel siècle ?",
                    ["Le XVIIe siècle", "Le XVIIIe siècle", "Le XIXe siècle"],
                    1,
                ),
            ],
        ),
        # 2 — Lire une frise chronologique (tier 11, level 3)
        L(
            11,
            3,
            "CE2 — Lire une frise chronologique 📏",
            "Comprendre comment le temps est représenté sur une frise.",
            [
                reading(
                    "Lis ce texte.",
                    "Une frise chronologique est une longue ligne qui représente le temps. "
                    "Les événements les plus anciens sont placés à gauche, les plus récents à droite. "
                    "Sur une frise, on peut repérer les grandes périodes de l'histoire.",
                ),
                mcq(
                    "Sur une frise, où place-t-on les événements les plus anciens ?",
                    ["À gauche", "À droite", "Au milieu"],
                    0,
                ),
                mcq(
                    "Sur une frise, où place-t-on les événements les plus récents ?",
                    ["À gauche", "À droite", "En bas"],
                    1,
                ),
                mcq(
                    "Parmi ces périodes, laquelle est la plus ancienne ?",
                    ["La Préhistoire", "Le Moyen Âge", "Aujourd'hui"],
                    0,
                ),
            ],
        ),
        # 3 — Le Paléolithique (tier 12, level 3)
        L(
            12,
            3,
            "CE2 — Le Paléolithique 🔥",
            "Les premiers hommes : chasseurs-cueilleurs, le feu et les grottes.",
            [
                mcq(
                    "Au Paléolithique, comment les hommes se nourrissaient-ils ?",
                    ["En chassant et en cueillant", "En cultivant des champs", "En achetant au marché"],
                    0,
                ),
                mcq(
                    "Quelle grande découverte a permis de se réchauffer et de cuire les aliments ?",
                    ["Le feu", "L'électricité", "La roue"],
                    0,
                ),
                mcq(
                    "Où les hommes préhistoriques faisaient-ils des peintures ?",
                    ["Dans les grottes", "Sur du papier", "Sur les murs des maisons"],
                    0,
                ),
                mcq(
                    "Les hommes du Paléolithique se déplaçaient souvent : ils étaient…",
                    ["nomades", "sédentaires", "des marchands en ville"],
                    0,
                ),
            ],
        ),
        # 4 — Le Néolithique (tier 13, level 3)
        L(
            13,
            3,
            "CE2 — Le Néolithique 🌾",
            "La naissance de l'agriculture, de l'élevage et des premiers villages.",
            [
                mcq(
                    "Quelle grande nouveauté apparaît au Néolithique ?",
                    ["L'agriculture", "L'écriture", "La voiture"],
                    0,
                ),
                mcq(
                    "Au Néolithique, les hommes commencent à garder des animaux : c'est…",
                    ["l'élevage", "la chasse", "la pêche"],
                    0,
                ),
                mcq(
                    "Grâce à l'agriculture, les hommes cessent de se déplacer : ils deviennent…",
                    ["sédentaires", "nomades", "invisibles"],
                    0,
                ),
                mcq(
                    "Au Néolithique, les hommes se regroupent pour vivre dans des…",
                    ["villages", "grottes", "châteaux forts"],
                    0,
                ),
            ],
        ),
        # 5 — Les Gaulois (tier 14, level 3)
        L(
            14,
            3,
            "CE2 — La vie des Gaulois 🛡️",
            "Le peuple gaulois, ses druides et sa vie quotidienne.",
            [
                mcq("Les Gaulois vivaient dans un pays appelé…", ["la Gaule", "l'Italie", "l'Égypte"], 0),
                mcq("Comment appelait-on les prêtres gaulois ?", ["Les druides", "Les chevaliers", "Les pharaons"], 0),
                mcq("Quelle langue parlaient les Gaulois ?", ["Le gaulois", "Le français", "L'anglais"], 0),
                mcq(
                    "Les Gaulois n'avaient pas un seul roi : ils étaient divisés en de nombreux…",
                    ["peuples (tribus)", "pays", "continents"],
                    0,
                ),
            ],
        ),
        # 6 — Vercingétorix et Jules César (tier 15, level 4)
        L(
            15,
            4,
            "CE2 — Vercingétorix et Jules César ⚔️",
            "La guerre des Gaules et la défaite d'Alésia.",
            [
                mcq(
                    "Quel chef gaulois a réuni les tribus pour combattre les Romains ?",
                    ["Vercingétorix", "Astérix", "Charlemagne"],
                    0,
                ),
                mcq(
                    "Qui commandait l'armée romaine qui a conquis la Gaule ?",
                    ["Jules César", "Napoléon", "Louis XIV"],
                    0,
                ),
                mcq(
                    "En 52 avant Jésus-Christ, Vercingétorix est vaincu lors de la bataille de…",
                    ["Alésia", "Waterloo", "Marignan"],
                    0,
                ),
                mcq(
                    "Après cette défaite, la Gaule devient…",
                    ["romaine (conquise par Rome)", "grecque", "égyptienne"],
                    0,
                ),
            ],
        ),
        # 7 — La Gaule romaine (tier 16, level 4)
        L(
            16,
            4,
            "CE2 — La Gaule romaine 🏛️",
            "Les villes, les routes et les aqueducs à l'époque gallo-romaine.",
            [
                mcq(
                    "Après la conquête, les Romains construisent partout de grandes…",
                    ["routes", "voies ferrées", "pistes cyclables"],
                    0,
                ),
                mcq(
                    "Quels monuments les Romains construisaient-ils pour amener l'eau dans les villes ?",
                    ["Des aqueducs", "Des gratte-ciels", "Des ponts-levis"],
                    0,
                ),
                mcq(
                    "Le Pont du Gard, près de Nîmes, est un célèbre…",
                    ["aqueduc romain", "château fort", "cathédrale"],
                    0,
                ),
                mcq(
                    "Le mélange des cultures gauloise et romaine s'appelle la civilisation…",
                    ["gallo-romaine", "préhistorique", "gréco-égyptienne"],
                    0,
                ),
            ],
        ),
        # 8 — Les grandes invasions (tier 17, level 4)
        L(
            17,
            4,
            "CE2 — La fin de l'Empire romain 🐎",
            "Les grandes invasions et l'effondrement de l'Empire romain.",
            [
                mcq(
                    "À partir du IVe siècle, des peuples venus de l'est entrent dans l'Empire romain : ce sont les grandes…",
                    ["invasions", "inventions", "récoltes"],
                    0,
                ),
                mcq(
                    "Comment les Romains appelaient-ils ces peuples étrangers ?",
                    ["Les barbares", "Les citoyens", "Les empereurs"],
                    0,
                ),
                mcq(
                    "En l'an 476, l'Empire romain d'Occident…",
                    ["prend fin (s'effondre)", "devient plus grand", "découvre l'Amérique"],
                    0,
                ),
                mcq(
                    "Un de ces peuples, les Francs, s'installe en Gaule. Leur roi célèbre s'appelle…",
                    ["Clovis", "Jules César", "Vercingétorix"],
                    0,
                ),
            ],
        ),
        # 9 — Charlemagne (tier 18, level 4)
        L(
            18,
            4,
            "CE2 — Charlemagne 👑",
            "Le roi des Francs devenu empereur en l'an 800.",
            [
                mcq("Charlemagne était le roi des…", ["Francs", "Gaulois", "Romains"], 0),
                mcq("En l'an 800, Charlemagne est couronné…", ["empereur", "pharaon", "président"], 0),
                mcq(
                    "On raconte que Charlemagne a favorisé la création d'…",
                    ["écoles", "usines", "voitures"],
                    0,
                ),
                mcq(
                    "Charlemagne a gouverné un très vaste…",
                    ["empire", "petit village", "château"],
                    0,
                ),
            ],
        ),
        # 10 — Le château fort (tier 19, level 3)
        L(
            19,
            3,
            "CE2 — Le château fort 🏰",
            "La demeure fortifiée du seigneur au Moyen Âge.",
            [
                mcq(
                    "Au Moyen Âge, dans quelle sorte de demeure habitait le seigneur ?",
                    ["Un château fort", "Un gratte-ciel", "Un immeuble"],
                    0,
                ),
                mcq(
                    "Comment appelle-t-on le fossé rempli d'eau qui entoure le château ?",
                    ["Les douves", "Les escaliers", "Les tours"],
                    0,
                ),
                mcq(
                    "Pour entrer dans le château au-dessus des douves, on franchissait le…",
                    ["pont-levis", "ascenseur", "toboggan"],
                    0,
                ),
                mcq(
                    "À quoi servaient surtout les hauts murs du château fort ?",
                    ["À se protéger des ennemis", "À décorer le jardin", "À faire du sport"],
                    0,
                ),
            ],
        ),
        # 11 — Les chevaliers (tier 20, level 3)
        L(
            20,
            3,
            "CE2 — Les chevaliers 🐴",
            "Les combattants du Moyen Âge, leur armure et leurs tournois.",
            [
                mcq("Le chevalier partait au combat à…", ["cheval", "pied uniquement", "vélo"], 0),
                mcq(
                    "Pour se protéger pendant les combats, le chevalier portait une…", ["armure", "robe", "couronne"], 0
                ),
                mcq(
                    "Comment appelle-t-on la cérémonie où un jeune homme devient chevalier ?",
                    ["L'adoubement", "Le baptême", "Le couronnement"],
                    0,
                ),
                mcq(
                    "Les chevaliers s'affrontaient dans des combats sportifs appelés…",
                    ["tournois", "récréations", "examens"],
                    0,
                ),
            ],
        ),
        # 12 — La vie des paysans (tier 21, level 3)
        L(
            21,
            3,
            "CE2 — Les paysans au Moyen Âge 🌾",
            "Le travail de la terre et la vie sous l'autorité du seigneur.",
            [
                mcq(
                    "Au Moyen Âge, la plupart des habitants étaient des…",
                    ["paysans", "rois", "chevaliers"],
                    0,
                ),
                mcq(
                    "Comment appelait-on les paysans qui appartenaient au seigneur ?",
                    ["Les serfs", "Les nobles", "Les druides"],
                    0,
                ),
                mcq(
                    "Les paysans travaillaient surtout…",
                    ["la terre (les champs)", "la mer", "la forge"],
                    0,
                ),
                mcq(
                    "Les paysans devaient donner une partie de leur récolte au…",
                    ["seigneur", "boulanger", "voisin"],
                    0,
                ),
            ],
        ),
        # 13 — Les cathédrales (tier 22, level 4)
        L(
            22,
            4,
            "CE2 — Les cathédrales du Moyen Âge ⛪",
            "Ces immenses églises construites pendant des dizaines d'années.",
            [
                mcq("Une cathédrale est une très grande…", ["église", "école", "maison"], 0),
                mcq(
                    "Comment appelle-t-on les grandes fenêtres en verre coloré des cathédrales ?",
                    ["Les vitraux", "Les tableaux", "Les miroirs"],
                    0,
                ),
                mcq(
                    "Combien de temps pouvait durer la construction d'une cathédrale ?",
                    ["Plusieurs dizaines d'années", "Une seule semaine", "Une seule journée"],
                    0,
                ),
                mcq(
                    "Notre-Dame de Paris est une célèbre…",
                    ["cathédrale", "château fort", "gare"],
                    0,
                ),
            ],
        ),
        # 14 — Les grandes inventions (tier 23, level 4)
        L(
            23,
            4,
            "CE2 — Les grandes inventions 💡",
            "Des découvertes qui ont changé la vie à travers le temps.",
            [
                mcq(
                    "Quelle invention très ancienne a permis de déplacer de lourdes charges ?",
                    ["La roue", "L'ordinateur", "L'avion"],
                    0,
                ),
                mcq(
                    "Au XVe siècle, Gutenberg met au point une machine pour reproduire des textes : l'…",
                    ["imprimerie", "télévision", "photographie"],
                    0,
                ),
                mcq(
                    "Grâce à l'imprimerie, on peut fabriquer beaucoup plus de…",
                    ["livres", "voitures", "fusées"],
                    0,
                ),
                mcq(
                    "Quelle invention permet de parler avec une personne qui est loin ?",
                    ["Le téléphone", "Le marteau", "Le tonneau"],
                    0,
                ),
            ],
        ),
        # 15 — Quelques rois de France (tier 24, level 4)
        L(
            24,
            4,
            "CE2 — Quelques rois de France 🤴",
            "Des repères simples : Clovis, Louis XIV et la fin de la royauté.",
            [
                mcq(
                    "Clovis, roi des Francs, est l'un des premiers rois de…",
                    ["France", "Espagne", "Chine"],
                    0,
                ),
                mcq("Quel était le surnom du roi Louis XIV ?", ["Le Roi-Soleil", "Le Roi-Lune", "Le Roi-Étoile"], 0),
                mcq(
                    "Louis XIV a fait construire un immense château à…",
                    ["Versailles", "Marseille", "Lyon"],
                    0,
                ),
                mcq(
                    "Après la Révolution française de 1789, la France finit par ne plus avoir de roi et devient une…",
                    ["république", "forêt", "planète"],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Histoire "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
