"""Seed CE2 — Leçons avancées dans toutes les matières.

Deux leçons par matière (français, orthographe, maths, histoire, géo, monde,
arts, logique) : la première en ``difficulty_level`` 3, la seconde en 4 (la plus
exigeante). Contenu de niveau CE2, pensé pour des enfants à l'aise.

Placées après les leçons CE2 existantes (max_tier + 1/2), sans trou. Réponses
correctes par construction ; ``fill_blanks`` sans accent (correction sensible aux
accents).

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, math_problem, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"

# Tier de départ par matière = (dernière tier CE2 existante) + 1.
BASE_TIER = {
    "francais": 4,
    "orthographe": 3,
    "maths": 4,
    "histoire": 2,
    "geo": 2,
    "monde": 2,
    "arts": 1,
    "logique": 1,
}


def _lesson(
    slug: str, offset: int, level: int, name: str, desc: str, exercises: list[dict[str, Any]]
) -> dict[str, Any]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = level
    xp = 55 if level == 3 else 60
    return theme(slug, LEVEL, BASE_TIER[slug] + offset, name, desc, xp, exercises)


def curriculum() -> list[dict[str, Any]]:
    themes: list[dict[str, Any]] = []

    # ------------------------------------------------------------- Français
    themes.append(
        _lesson(
            "francais",
            0,
            3,
            "CE2 — Le présent des verbes 🔤",
            "Conjuguer au présent.",
            [
                mcq("« Je (chanter) » au présent :", ["chante", "chanter", "chanté"], 0),
                mcq("« Nous (finir) » au présent :", ["finissons", "finir", "finit"], 0),
                mcq("« Ils (être) » au présent :", ["sont", "est", "être"], 0),
                mcq("« Tu (avoir) » au présent :", ["as", "a", "avoir"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "francais",
            1,
            4,
            "CE2 — Les homophones (a/à, et/est, on/ont)",
            "Choisir le bon homophone.",
            [
                mcq("« Il ___ mangé une pomme. »", ["a", "à"], 0),
                mcq("« Papa ___ maman sont là. »", ["et", "est"], 0),
                mcq("« Le ciel ___ bleu. »", ["est", "et"], 0),
                mcq("« Les enfants ___ des jouets. »", ["ont", "on"], 0),
            ],
        )
    )

    # ---------------------------------------------------------- Orthographe
    themes.append(
        _lesson(
            "orthographe",
            0,
            3,
            "CE2 — L'accord dans le groupe du nom",
            "Accorder l'adjectif avec le nom.",
            [
                mcq("« des fleurs ___ »", ["rouges", "rouge"], 0),
                mcq("« une voiture ___ »", ["neuve", "neuf", "neuves"], 0),
                fill_blanks("Complète : « les petit___ chats »", "les petit___ chats", ["s"]),
                mcq("Au pluriel, l'adjectif prend le plus souvent un…", ["s", "x uniquement", "rien"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "orthographe",
            1,
            4,
            "CE2 — Le pluriel en -x",
            "Les pluriels particuliers.",
            [
                mcq("un jeu → des…", ["jeux", "jeus", "jeu"], 0),
                mcq("un bateau → des…", ["bateaux", "bateaus", "bateau"], 0),
                mcq("un cheveu → des…", ["cheveux", "cheveus", "cheveu"], 0),
                mcq("Les mots en -eau et -eu font leur pluriel en…", ["-x", "-s", "rien"], 0),
            ],
        )
    )

    # ----------------------------------------------------------------- Maths
    themes.append(
        _lesson(
            "maths",
            0,
            3,
            "CE2 — Les nombres jusqu'à 1000",
            "Lire et décomposer les grands nombres.",
            [
                mcq("Dans 347, le chiffre des centaines est…", ["3", "4", "7"], 0),
                mcq("Quel nombre vient juste après 199 ?", ["200", "100", "210"], 0),
                math_problem("Combien font 250 + 300 ?", 550),
                mcq("456 se lit…", ["quatre cent cinquante-six", "quarante-cinq six", "quatre cinquante six"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "maths",
            1,
            4,
            "CE2 — Multiplication et problèmes",
            "Résoudre des problèmes de multiplication.",
            [
                math_problem("6 × 7 = ?", 42),
                math_problem("Un paquet contient 8 gâteaux. Combien dans 4 paquets ?", 32),
                math_problem("8 × 9 = ?", 72),
                math_problem("Il y a 5 boîtes de 6 œufs. Combien d'œufs en tout ?", 30),
            ],
        )
    )

    # -------------------------------------------------------------- Histoire
    themes.append(
        _lesson(
            "histoire",
            0,
            3,
            "CE2 — La Préhistoire",
            "La vie des premiers hommes.",
            [
                mcq("Les premiers hommes ont appris à maîtriser…", ["le feu", "l'électricité", "la voiture"], 0),
                mcq("À la Préhistoire, on ne savait pas encore…", ["écrire", "marcher", "manger"], 0),
                mcq(
                    "Les peintures de la grotte de Lascaux montrent surtout des…", ["animaux", "voitures", "maisons"], 0
                ),
                mcq("Les premiers outils étaient taillés dans la…", ["pierre", "plastique", "vitre"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "histoire",
            1,
            4,
            "CE2 — Le Moyen Âge",
            "Châteaux, chevaliers et cathédrales.",
            [
                mcq("Au Moyen Âge, on construisait des châteaux…", ["forts", "gonflables", "en verre"], 0),
                mcq("Le seigneur vivait dans son château avec des…", ["chevaliers", "astronautes", "pompiers"], 0),
                mcq("Une grande église du Moyen Âge s'appelle une…", ["cathédrale", "usine", "gare"], 0),
                mcq("Le roi Charlemagne a encouragé la création des…", ["écoles", "voitures", "avions"], 0),
            ],
        )
    )

    # ------------------------------------------------------------ Géographie
    themes.append(
        _lesson(
            "geo",
            0,
            3,
            "CE2 — Continents et océans",
            "Se repérer sur la Terre.",
            [
                mcq("Sur quel continent vivons-nous ?", ["l'Europe", "l'Asie", "l'Afrique"], 0),
                mcq("Le plus grand océan est le…", ["Pacifique", "Atlantique", "Arctique"], 0),
                mcq("Le plus grand désert chaud est le…", ["Sahara", "Gobi", "pôle Nord"], 0),
                mcq("Le continent le plus froid est…", ["l'Antarctique", "l'Afrique", "l'Europe"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "geo",
            1,
            4,
            "CE2 — La France : reliefs et fleuves",
            "Montagnes, fleuves et mers de France.",
            [
                mcq("Le plus long fleuve de France est la…", ["Loire", "Seine", "Marne"], 0),
                mcq("Les Alpes sont des…", ["montagnes", "fleuves", "mers"], 0),
                mcq("À l'ouest de la France se trouve l'océan…", ["Atlantique", "Pacifique", "Indien"], 0),
                mcq("Le plus haut sommet des Alpes est le…", ["mont Blanc", "Vésuve", "Kilimandjaro"], 0),
            ],
        )
    )

    # ------------------------------------------------- Questionner le monde
    themes.append(
        _lesson(
            "monde",
            0,
            3,
            "CE2 — Le corps humain : la digestion",
            "Le voyage des aliments.",
            [
                mcq("La digestion commence dans la…", ["bouche", "main", "jambe"], 0),
                mcq("Les aliments descendent jusqu'à l'estomac par…", ["l'œsophage", "le nez", "l'oreille"], 0),
                mcq("L'estomac sert surtout à…", ["digérer les aliments", "respirer", "voir"], 0),
                mcq("On mange pour donner de l'___ à notre corps.", ["énergie", "eau", "air"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "monde",
            1,
            4,
            "CE2 — Le vivant : les cycles de vie",
            "Naître, grandir, se reproduire.",
            [
                mcq("La grenouille commence sa vie sous forme de…", ["têtard", "papillon", "graine"], 0),
                mcq("La chenille se transforme en…", ["papillon", "oiseau", "poisson"], 0),
                mcq("Une plante à fleurs commence par une…", ["graine", "fleur", "racine"], 0),
                mcq(
                    "Tous les êtres vivants naissent, grandissent, se reproduisent et…",
                    ["meurent", "volent", "brillent"],
                    0,
                ),
            ],
        )
    )

    # ----------------------------------------------------------------- Arts
    themes.append(
        _lesson(
            "arts",
            0,
            3,
            "CE2 — Le cercle chromatique 🎨",
            "Primaires, secondaires, chaudes et froides.",
            [
                mcq("Les trois couleurs primaires sont rouge, jaune et…", ["bleu", "vert", "orange"], 0),
                mcq("Rouge + jaune donne…", ["orange", "violet", "vert"], 0),
                mcq("Les couleurs froides sont le bleu, le vert et le…", ["violet", "rouge", "orange"], 0),
                mcq("Ajouter du blanc à une couleur la rend plus…", ["claire", "foncée", "froide"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "arts",
            1,
            4,
            "CE2 — Les grands artistes 🖼️",
            "Peintres et œuvres célèbres.",
            [
                mcq("« La Joconde » a été peinte par…", ["Léonard de Vinci", "Picasso", "Monet"], 0),
                mcq("Claude Monet est un peintre…", ["impressionniste", "préhistorique", "romain"], 0),
                mcq("Vincent van Gogh a peint « La Nuit ___ ».", ["étoilée", "noire", "blanche"], 0),
                mcq("Une œuvre en volume, taillée dans la pierre, est une…", ["sculpture", "chanson", "photo"], 0),
            ],
        )
    )

    # --------------------------------------------------------------- Logique
    themes.append(
        _lesson(
            "logique",
            0,
            3,
            "CE2 — Suites de nombres",
            "Trouver la règle d'une suite.",
            [
                mcq("2, 4, 8, 16, … Quel nombre vient après ?", ["32", "24", "20"], 0),
                mcq("100, 90, 80, … Quel nombre vient après ?", ["70", "75", "110"], 0),
                mcq("1, 4, 9, 16, … (les carrés) Quel nombre vient après ?", ["25", "20", "24"], 0),
                mcq("5, 10, 20, 40, … Quel nombre vient après ?", ["80", "60", "50"], 0),
            ],
        )
    )
    themes.append(
        _lesson(
            "logique",
            1,
            4,
            "CE2 — Énigmes logiques 🧠",
            "Raisonner et calculer.",
            [
                mcq("Tom a le double de billes que Léa, qui en a 4. Tom en a…", ["8", "6", "2"], 0),
                mcq("Si aujourd'hui c'est mardi, dans 3 jours ce sera…", ["vendredi", "jeudi", "samedi"], 0),
                mcq("Un fermier a 3 poules et 2 vaches. Combien de pattes en tout ?", ["14", "10", "20"], 0),
                mcq("Je partage 12 bonbons entre 3 enfants. Chacun en a…", ["4", "3", "6"], 0),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
