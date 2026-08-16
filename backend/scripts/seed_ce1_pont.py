"""Seed CE1 — Leçons « pont » vers le CE2 (niveau très avancé, hors maths).

Une leçon par matière non-mathématique, en ``difficulty_level`` 4 : notions qui
préparent le CE2 (classes de mots, accord sujet-verbe, Gaulois & Romains,
planisphère, états de la matière, couleurs complémentaires, déduction). Pour des
enfants à l'aise, un cran au-dessus des leçons avancées existantes.

Placées après les leçons CE1 existantes (max_tier + 1). Réponses correctes par
construction ; ``fill_blanks`` sans accent (correction sensible aux accents).

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_pont.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce1"
LVL = 4

# Tier = (dernière tier CE1 existante) + 1.
TIER = {
    "arts": 9,
    "francais": 12,
    "geo": 10,
    "histoire": 11,
    "logique": 9,
    "monde": 10,
    "orthographe": 10,
}


def _lesson(slug: str, name: str, desc: str, exercises: list[dict[str, Any]]) -> dict[str, Any]:
    for ex in exercises:
        if ex.get("type") != "reading":
            ex["level"] = LVL
    return theme(slug, LEVEL, TIER[slug], name, desc, 60, exercises)


def curriculum() -> list[dict[str, Any]]:
    return [
        _lesson(
            "francais",
            "Vers le CE2 — Les classes de mots 🔤",
            "Reconnaître nom, verbe, adjectif, déterminant.",
            [
                mcq("Dans « le chat noir », quel mot est le nom ?", ["chat", "le", "noir"], 0),
                mcq("Dans « le chat noir », « noir » est un…", ["adjectif", "verbe", "nom"], 0),
                mcq("Quel mot est un verbe ?", ["manger", "table", "rouge"], 0),
                mcq("« un, une, le, la » sont des…", ["déterminants", "verbes", "adjectifs"], 0),
            ],
        ),
        _lesson(
            "orthographe",
            "Vers le CE2 — L'accord sujet-verbe ✍️",
            "Accorder le verbe avec son sujet.",
            [
                mcq("« Les enfants ___ dans la cour. »", ["jouent", "joue", "joues"], 0),
                mcq("« Le chien ___ dans le jardin. »", ["court", "courent", "cours"], 0),
                fill_blanks("Complète : « Ils mang___ une pomme. »", "Ils mang___ une pomme", ["ent"]),
                mcq("Avec le sujet « nous », le verbe se termine souvent par…", ["-ons", "-ez", "-e"], 0),
            ],
        ),
        _lesson(
            "histoire",
            "Vers le CE2 — Gaulois et Romains 🏛️",
            "Découvrir l'Antiquité en Gaule.",
            [
                mcq("Les habitants de la Gaule étaient les…", ["Gaulois", "Égyptiens", "Vikings"], 0),
                mcq("Les Gaulois ont été conquis par les…", ["Romains", "Grecs", "Anglais"], 0),
                mcq("Les Romains ont construit des routes et des…", ["aqueducs", "gratte-ciels", "voitures"], 0),
                mcq("Un chef gaulois célèbre s'appelait…", ["Vercingétorix", "Napoléon", "Charlemagne"], 0),
            ],
        ),
        _lesson(
            "geo",
            "Vers le CE2 — Le planisphère 🌍",
            "Lire une carte du monde.",
            [
                mcq("Un planisphère représente…", ["toute la Terre à plat", "une ville", "une maison"], 0),
                mcq("Combien y a-t-il de continents ?", ["6", "3", "12"], 0),
                mcq("Le plus grand océan est l'océan…", ["Pacifique", "Atlantique", "Indien"], 0),
                mcq("L'équateur coupe la Terre en…", ["deux", "trois", "quatre"], 0),
            ],
        ),
        _lesson(
            "monde",
            "Vers le CE2 — Les états de la matière 🧊",
            "Solide, liquide, gazeux.",
            [
                mcq("La glace est de l'eau à l'état…", ["solide", "liquide", "gazeux"], 0),
                mcq("La vapeur d'eau est de l'eau à l'état…", ["gazeux", "solide", "liquide"], 0),
                mcq("Quand la glace fond, elle devient…", ["liquide", "gazeuse", "solide"], 0),
                mcq("L'eau qui bout se transforme en…", ["vapeur", "glace", "pierre"], 0),
            ],
        ),
        _lesson(
            "arts",
            "Vers le CE2 — Les couleurs complémentaires 🎨",
            "Comprendre le cercle chromatique.",
            [
                mcq("La couleur complémentaire du rouge est le…", ["vert", "bleu", "jaune"], 0),
                mcq("Les couleurs secondaires sont vert, orange et…", ["violet", "rouge", "bleu"], 0),
                mcq("Une couleur mélangée à sa complémentaire donne un ton…", ["gris/terne", "très vif", "fluo"], 0),
                mcq("Le cercle qui range les couleurs s'appelle le cercle…", ["chromatique", "carré", "magique"], 0),
            ],
        ),
        _lesson(
            "logique",
            "Vers le CE2 — Déduction et énigmes 🧠",
            "Raisonner pour trouver la réponse.",
            [
                mcq(
                    "Marie est plus âgée que Léa mais plus jeune que Tom. Le plus âgé est…", ["Tom", "Marie", "Léa"], 0
                ),
                mcq(
                    "Tous les jouets rouges sont dans la boîte. Un jouet posé dehors est donc…",
                    ["pas rouge", "rouge", "cassé"],
                    0,
                ),
                mcq("3, 6, 9, 12, … Quel nombre vient après ?", ["15", "13", "18"], 0),
                mcq("J'ai 2 pièces qui font 15 en tout : une de 10 et une de…", ["5", "2", "7"], 0),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE1 « pont vers CE2 » "
            f"({total_ex} exercices, niveau {LVL}) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
