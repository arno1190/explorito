"""Seed CM1 Histoire — programme avancé (Préhistoire → Louis XIV).

Idempotent par (parcours, nom de leçon). Faits établis, grand public.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cm1_histoire.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, mcq, reading, theme

from app.core.database import SessionLocal

LEVEL = "cm1"
SLUG = "histoire"


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
        # 1. La Préhistoire — level 4
        L(
            10,
            4,
            "CM1 — La Préhistoire 🦣",
            "Paléolithique et Néolithique : deux grandes périodes.",
            [
                reading(
                    "Lis avant de répondre.",
                    "La Préhistoire est la très longue période avant l'invention de l'écriture. "
                    "Au Paléolithique (âge de la pierre taillée), les hommes étaient nomades : "
                    "ils se déplaçaient pour chasser et cueillir leur nourriture, et ils avaient "
                    "appris à maîtriser le feu. Au Néolithique (âge de la pierre polie), ils "
                    "sont devenus sédentaires : ils cultivaient la terre, élevaient des animaux "
                    "et vivaient dans des villages.",
                ),
                mcq(
                    "Au Paléolithique, comment vivaient les hommes ?",
                    [
                        "Ils étaient nomades, chasseurs et cueilleurs",
                        "Ils habitaient de grandes villes",
                        "Ils élevaient des vaches dans des fermes",
                    ],
                    0,
                ),
                mcq(
                    "Quelle grande nouveauté apparaît au Néolithique ?",
                    ["L'agriculture et l'élevage", "L'automobile", "L'électricité"],
                    0,
                ),
                mcq(
                    "Que faisaient les hommes préhistoriques dans certaines grottes, comme à Lascaux ?",
                    ["Des peintures d'animaux", "Des photographies", "Des films"],
                    0,
                ),
            ],
        ),
        # 2. Les Gaulois — level 4
        L(
            11,
            4,
            "CM1 — Les Gaulois ⚔️",
            "Un peuple celte partagé en de nombreuses tribus.",
            [
                mcq(
                    "Les Gaulois étaient un peuple…",
                    ["celte, vivant en Gaule", "venu d'Amérique", "vivant en Égypte"],
                    0,
                ),
                mcq(
                    "La Gaule était :",
                    ["divisée en de nombreux peuples (tribus)", "un seul grand royaume uni", "une ville unique"],
                    0,
                ),
                mcq(
                    "Chez les Gaulois, les druides étaient :",
                    ["des prêtres et des savants", "des soldats romains", "des rois d'Égypte"],
                    0,
                ),
                mcq(
                    "De quoi vivaient surtout les Gaulois ?",
                    ["De l'agriculture et de l'artisanat", "Du commerce d'automobiles", "Du tourisme"],
                    0,
                ),
            ],
        ),
        # 3. La conquête romaine — level 5
        L(
            12,
            5,
            "CM1 — Vercingétorix et Jules César 🏛️",
            "La conquête de la Gaule par Rome.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Le général romain Jules César conquit peu à peu la Gaule. Pour lui résister, "
                    "le chef gaulois Vercingétorix, un Arverne, réussit à réunir plusieurs peuples "
                    "gaulois. Mais en 52 avant Jésus-Christ, il fut vaincu et fait prisonnier à "
                    "Alésia. La Gaule devint alors romaine.",
                ),
                mcq(
                    "Quel général romain conquit la Gaule ?",
                    ["Jules César", "Napoléon", "Charlemagne"],
                    0,
                ),
                mcq(
                    "Qui fut le chef gaulois qui unit les peuples contre Rome ?",
                    ["Vercingétorix", "Clovis", "Louis XIV"],
                    0,
                ),
                mcq(
                    "En quelle année Vercingétorix fut-il vaincu à Alésia ?",
                    ["52 avant Jésus-Christ", "476 après Jésus-Christ", "1492"],
                    0,
                ),
            ],
        ),
        # 4. La Gaule romaine — level 4
        L(
            13,
            4,
            "CM1 — La Gaule romaine 🏺",
            "Les Gallo-Romains : villes, routes et monuments.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Après la conquête, les Gaulois adoptèrent peu à peu le mode de vie des "
                    "Romains : on les appelle les Gallo-Romains. Les Romains construisirent des "
                    "villes, des routes bien droites, des aqueducs pour apporter l'eau, des arènes "
                    "et des thermes. La langue latine se répandit.",
                ),
                mcq(
                    "Comment appelle-t-on les habitants de la Gaule après la conquête romaine ?",
                    ["Les Gallo-Romains", "Les Vikings", "Les Égyptiens"],
                    0,
                ),
                mcq(
                    "À quoi servait un aqueduc, comme le Pont du Gard ?",
                    ["À transporter l'eau", "À stocker de l'or", "À élever des chevaux"],
                    0,
                ),
                mcq(
                    "Quelle langue se répandit en Gaule romaine ?",
                    ["Le latin", "L'anglais", "L'arabe"],
                    0,
                ),
            ],
        ),
        # 5. La christianisation de la Gaule — level 4
        L(
            14,
            4,
            "CM1 — La christianisation de la Gaule ✝️",
            "Comment la religion chrétienne s'est répandue.",
            [
                mcq(
                    "Quelle religion se répandit peu à peu dans la Gaule romaine ?",
                    ["Le christianisme", "L'écriture des hiéroglyphes", "Le culte des pharaons"],
                    0,
                ),
                mcq(
                    "Au tout début, les premiers chrétiens de l'Empire romain étaient souvent :",
                    ["persécutés", "élus rois", "nommés empereurs"],
                    0,
                ),
                mcq(
                    "Qui dirigeait la communauté chrétienne d'une ville ?",
                    ["un évêque", "un druide", "un pharaon"],
                    0,
                ),
                mcq(
                    "Les chrétiens se réunissaient pour prier :",
                    ["dans des églises", "dans des arènes de combat", "dans des usines"],
                    0,
                ),
            ],
        ),
        # 6. Les Francs et Clovis — level 4
        L(
            15,
            4,
            "CM1 — Les Francs et Clovis 👑",
            "Clovis, premier roi franc chrétien.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Après la fin de l'Empire romain, des peuples venus de l'est s'installèrent en "
                    "Gaule. Parmi eux, les Francs. Leur roi, Clovis, les réunit et étendit son "
                    "royaume. Vers l'an 496, il se fit baptiser à Reims : il devint le premier roi "
                    "franc chrétien.",
                ),
                mcq(
                    "Comment s'appelait le célèbre roi des Francs ?",
                    ["Clovis", "Vercingétorix", "Jules César"],
                    0,
                ),
                mcq(
                    "Dans quelle ville Clovis fut-il baptisé, vers 496 ?",
                    ["Reims", "Rome", "Londres"],
                    0,
                ),
                mcq(
                    "En se faisant baptiser, Clovis devint :",
                    ["chrétien", "empereur de Rome", "pharaon d'Égypte"],
                    0,
                ),
            ],
        ),
        # 7. Charlemagne — level 5
        L(
            16,
            5,
            "CM1 — Charlemagne et son empire 📜",
            "Le roi des Francs couronné empereur en 800.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Charlemagne, roi des Francs, agrandit beaucoup son royaume par la guerre. "
                    "En l'an 800, le pape le couronna empereur à Rome. Charlemagne encouragea "
                    "l'instruction et favorisa la création d'écoles pour former les futurs "
                    "responsables de l'empire.",
                ),
                mcq(
                    "En quelle année Charlemagne fut-il couronné empereur ?",
                    ["En l'an 800", "En 1492", "En 52 avant Jésus-Christ"],
                    0,
                ),
                mcq(
                    "Qui couronna Charlemagne empereur, à Rome ?",
                    ["le pape", "Jules César", "Vercingétorix"],
                    0,
                ),
                mcq(
                    "Qu'est-ce que Charlemagne encouragea dans son empire ?",
                    ["l'instruction et les écoles", "la construction d'automobiles", "les voyages en avion"],
                    0,
                ),
            ],
        ),
        # 8. La féodalité — level 5
        L(
            17,
            5,
            "CM1 — La féodalité 🏰",
            "Seigneurs, vassaux et châteaux forts.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Au Moyen Âge, la société était organisée autour des seigneurs. Un seigneur "
                    "donnait une terre, appelée fief, à un vassal. En échange, le vassal lui jurait "
                    "fidélité et devait l'aider, notamment à la guerre. Pour se protéger, les "
                    "seigneurs faisaient bâtir des châteaux forts.",
                ),
                mcq(
                    "Comment appelle-t-on la terre qu'un seigneur donne à son vassal ?",
                    ["un fief", "une arène", "un aqueduc"],
                    0,
                ),
                mcq(
                    "Que devait le vassal à son seigneur ?",
                    ["fidélité et aide (surtout à la guerre)", "de l'argent de poche", "des vacances"],
                    0,
                ),
                mcq(
                    "Pourquoi les seigneurs construisaient-ils des châteaux forts ?",
                    ["pour se protéger et se défendre", "pour faire du tourisme", "pour cultiver du blé"],
                    0,
                ),
            ],
        ),
        # 9. Les paysans au Moyen Âge — level 4
        L(
            18,
            4,
            "CM1 — Les paysans au Moyen Âge 🌾",
            "La vie difficile de la majorité de la population.",
            [
                mcq(
                    "Au Moyen Âge, la plupart des gens étaient :",
                    ["des paysans", "des rois", "des marins explorateurs"],
                    0,
                ),
                mcq(
                    "Les paysans cultivaient surtout :",
                    ["les terres du seigneur", "le fond des océans", "des jardins sur les toits"],
                    0,
                ),
                mcq(
                    "En plus des redevances, les paysans devaient parfois des « corvées ». C'était :",
                    ["un travail gratuit pour le seigneur", "des vacances offertes", "un cadeau du roi"],
                    0,
                ),
                mcq(
                    "En général, la vie des paysans au Moyen Âge était :",
                    ["difficile", "très riche et facile", "passée à voyager"],
                    0,
                ),
            ],
        ),
        # 10. Les cathédrales et la religion — level 5
        L(
            19,
            5,
            "CM1 — Les cathédrales et la religion ⛪",
            "La place de la religion et l'art des bâtisseurs.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Au Moyen Âge, la religion chrétienne tenait une place très importante dans la "
                    "vie des gens. Dans les villes, on construisit d'immenses cathédrales, souvent "
                    "de style gothique, avec de hautes voûtes et de magnifiques vitraux colorés. "
                    "Beaucoup de chrétiens partaient aussi en pèlerinage.",
                ),
                mcq(
                    "Quelle religion était la plus importante en France au Moyen Âge ?",
                    ["le christianisme", "il n'y avait aucune religion", "le culte des pharaons"],
                    0,
                ),
                mcq(
                    "Les grandes églises construites dans les villes au Moyen Âge s'appellent :",
                    ["des cathédrales", "des arènes", "des aqueducs"],
                    0,
                ),
                mcq(
                    "Les fenêtres colorées des cathédrales s'appellent :",
                    ["des vitraux", "des fresques", "des mosaïques romaines"],
                    0,
                ),
            ],
        ),
        # 11. Les rois capétiens — level 5
        L(
            20,
            5,
            "CM1 — Les rois capétiens 🌸",
            "Hugues Capet et le renforcement du pouvoir royal.",
            [
                reading(
                    "Lis avant de répondre.",
                    "En 987, Hugues Capet fut élu roi. Il fonda la dynastie des Capétiens. Pendant "
                    "des siècles, la couronne passa de père en fils. Petit à petit, les rois de "
                    "France agrandirent leur royaume et renforcèrent leur pouvoir. Paris devint "
                    "une grande ville royale.",
                ),
                mcq(
                    "Quel roi, en 987, fonda la dynastie des Capétiens ?",
                    ["Hugues Capet", "Clovis", "Charlemagne"],
                    0,
                ),
                mcq(
                    "Comment la couronne passait-elle le plus souvent chez les Capétiens ?",
                    ["de père en fils", "par tirage au sort", "au plus riche marchand"],
                    0,
                ),
                mcq(
                    "Au fil des siècles, le pouvoir des rois de France :",
                    ["se renforça", "disparut complètement", "fut donné aux Romains"],
                    0,
                ),
            ],
        ),
        # 12. Guerre de Cent Ans et Jeanne d'Arc — level 5
        L(
            21,
            5,
            "CM1 — Jeanne d'Arc et la guerre de Cent Ans 🗡️",
            "Une longue guerre entre la France et l'Angleterre.",
            [
                reading(
                    "Lis avant de répondre.",
                    "La guerre de Cent Ans opposa la France et l'Angleterre pendant plus d'un "
                    "siècle. En 1429, une jeune fille, Jeanne d'Arc, aida l'armée française à "
                    "libérer la ville d'Orléans, alors assiégée par les Anglais. Elle contribua "
                    "ensuite à faire sacrer le roi Charles VII à Reims.",
                ),
                mcq(
                    "La guerre de Cent Ans opposait la France à :",
                    ["l'Angleterre", "l'Espagne", "l'Égypte"],
                    0,
                ),
                mcq(
                    "En 1429, quelle ville Jeanne d'Arc aida-t-elle à libérer ?",
                    ["Orléans", "Rome", "Londres"],
                    0,
                ),
                mcq(
                    "Grâce à Jeanne d'Arc, quel roi fut sacré à Reims ?",
                    ["Charles VII", "Louis XIV", "Clovis"],
                    0,
                ),
            ],
        ),
        # 13. La Renaissance — level 5
        L(
            22,
            5,
            "CM1 — La Renaissance 🎨",
            "Un renouveau des arts, des sciences et du savoir.",
            [
                reading(
                    "Lis avant de répondre.",
                    "À partir du XVe siècle, une nouvelle période s'ouvre : la Renaissance. Les "
                    "artistes et les savants s'inspirent de l'Antiquité et font de grands progrès. "
                    "L'artiste italien Léonard de Vinci en est un exemple célèbre. Au XVe siècle, "
                    "l'imprimerie mise au point par Gutenberg permet de fabriquer des livres "
                    "beaucoup plus vite et de diffuser les idées.",
                ),
                mcq(
                    "La Renaissance est une période de :",
                    ["renouveau des arts et des sciences", "guerre entre Gaulois et Romains", "chasse au mammouth"],
                    0,
                ),
                mcq(
                    "Quel artiste italien célèbre vécut à la Renaissance ?",
                    ["Léonard de Vinci", "Vercingétorix", "Hugues Capet"],
                    0,
                ),
                mcq(
                    "Quelle invention de Gutenberg, au XVe siècle, permit de diffuser les livres ?",
                    ["l'imprimerie", "le téléphone", "l'ordinateur"],
                    0,
                ),
            ],
        ),
        # 14. Les grandes découvertes — level 4
        L(
            23,
            4,
            "CM1 — Les grandes découvertes 🧭",
            "Les explorateurs partent à travers les océans.",
            [
                reading(
                    "Lis avant de répondre.",
                    "À la fin du XVe siècle, des navigateurs partent explorer le monde sur de "
                    "petits bateaux appelés caravelles, en s'aidant de la boussole. En 1492, "
                    "Christophe Colomb traverse l'océan Atlantique et atteint l'Amérique, qu'il "
                    "croyait être les Indes.",
                ),
                mcq(
                    "En 1492, quel navigateur atteignit l'Amérique ?",
                    ["Christophe Colomb", "Jules César", "Charlemagne"],
                    0,
                ),
                mcq(
                    "Comment s'appelaient les bateaux utilisés par les explorateurs ?",
                    ["des caravelles", "des sous-marins", "des paquebots"],
                    0,
                ),
                mcq(
                    "Quel instrument aidait les marins à trouver leur direction ?",
                    ["la boussole", "la télévision", "l'appareil photo"],
                    0,
                ),
            ],
        ),
        # 15. Louis XIV — level 5
        L(
            24,
            5,
            "CM1 — Louis XIV, le Roi-Soleil ☀️",
            "Un roi tout-puissant et le château de Versailles.",
            [
                reading(
                    "Lis avant de répondre.",
                    "Louis XIV régna de 1643 à 1715, ce qui fut l'un des plus longs règnes de "
                    "l'histoire de France. Il exerçait un pouvoir absolu : il décidait presque "
                    "tout seul. On le surnommait le Roi-Soleil. Il fit construire un immense et "
                    "somptueux château à Versailles, où vivait la cour.",
                ),
                mcq(
                    "Quel était le surnom de Louis XIV ?",
                    ["le Roi-Soleil", "le Roi de la Lune", "le Roi des Gaulois"],
                    0,
                ),
                mcq(
                    "Quel immense château Louis XIV fit-il construire ?",
                    ["le château de Versailles", "le Colisée de Rome", "les pyramides d'Égypte"],
                    0,
                ),
                mcq(
                    "Le pouvoir de Louis XIV était dit « absolu ». Cela signifie qu'il :",
                    ["décidait presque tout seul", "obéissait aux paysans", "partageait le pouvoir avec le peuple"],
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CM1 Histoire "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
