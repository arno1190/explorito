"""Seed CP Français — apprentissage de la lecture (programme officiel).

Enfants de ~6 ans qui apprennent à lire. Contenu très simple, majorité de QCM
(les questions peuvent être lues à voix haute par un parent). Réponses correctes
par construction. Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_francais.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, reading, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "francais"


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
        # 1. Les voyelles a, e, i, o, u
        L(
            1,
            1,
            "CP — Les voyelles a, e, i, o, u 🅰️",
            "Reconnaître les voyelles.",
            [
                mcq("Quelle lettre est une voyelle ?", ["b", "a", "t"], 1),
                mcq("Combien y a-t-il de voyelles : a, e, i, o, u ?", ["3", "5", "7"], 1),
                mcq("Laquelle n'est PAS une voyelle ?", ["e", "o", "m"], 2),
                mcq("Quelle est la première voyelle de l'alphabet ?", ["a", "e", "i"], 0),
            ],
        ),
        # 2. Le son [a] et le son [i]
        L(
            2,
            1,
            "CP — Le son [a] et le son [i] 🍎",
            "Entendre les sons [a] et [i].",
            [
                mcq("Dans quel mot entends-tu le son [a] ?", ["chat", "lit", "riz"], 0, emoji="🐱"),
                mcq("Dans quel mot entends-tu le son [i] ?", ["souris", "papa", "porte"], 0, emoji="🐭"),
                mcq("Quel mot commence par le son [a] ?", ["avion", "moto", "vélo"], 0, emoji="✈️"),
                mcq("Dans quel mot entends-tu le son [i] ?", ["lit", "sac", "pot"], 0, emoji="🛏️"),
            ],
        ),
        # 3. Le son [o] et le son [u]
        L(
            3,
            1,
            "CP — Le son [o] et le son [u] 🌙",
            "Entendre les sons [o] et [u].",
            [
                mcq("Dans quel mot entends-tu le son [o] ?", ["moto", "lit", "riz"], 0, emoji="🏍️"),
                mcq("Dans quel mot entends-tu le son [u] (comme lune) ?", ["lune", "chat", "moto"], 0, emoji="🌙"),
                mcq("Quel mot commence par le son [o] ?", ["olive", "banane", "tomate"], 0, emoji="🫒"),
                mcq("Dans quel mot entends-tu le son [u] (comme lune) ?", ["mur", "chat", "porte"], 0, emoji="🧱"),
            ],
        ),
        # 4. Combiner consonne + voyelle : les syllabes
        L(
            4,
            1,
            "CP — Les syllabes : ma, mi, mo… 🧩",
            "Combiner une consonne et une voyelle.",
            [
                mcq("M + A, quelle syllabe ?", ["ma", "mo", "mi"], 0),
                mcq("L + I, quelle syllabe ?", ["la", "lo", "li"], 2),
                mcq("P + O, quelle syllabe ?", ["pa", "po", "pi"], 1),
                fill_blanks("Complète la syllabe.", "m + a = ___", ["ma"]),
            ],
        ),
        # 5. Le son [ou]
        L(
            5,
            1,
            "CP — Le son [ou] 🐺",
            "Entendre le son [ou].",
            [
                mcq("Dans quel mot entends-tu le son [ou] ?", ["loup", "chat", "lune"], 0, emoji="🐺"),
                mcq("Dans quel mot entends-tu le son [ou] ?", ["hibou", "papa", "moto"], 0, emoji="🦉"),
                mcq("Dans quel mot entends-tu le son [ou] ?", ["roue", "lit", "sac"], 0, emoji="🛞"),
                mcq("Dans quel mot entends-tu le son [ou] ?", ["mouton", "chien", "table"], 0, emoji="🐑"),
            ],
        ),
        # 6. Le son [ch]
        L(
            6,
            1,
            "CP — Le son [ch] 🐱",
            "Entendre le son [ch].",
            [
                mcq("Dans quel mot entends-tu le son [ch] ?", ["chat", "rat", "table"], 0, emoji="🐱"),
                mcq("Dans quel mot entends-tu le son [ch] ?", ["vache", "lune", "moto"], 0, emoji="🐄"),
                mcq("Dans quel mot entends-tu le son [ch] ?", ["niche", "papa", "sac"], 0, emoji="🏠"),
                mcq("Dans quel mot entends-tu le son [ch] ?", ["chien", "lit", "riz"], 0, emoji="🐶"),
            ],
        ),
        # 7. Le son [on]
        L(
            7,
            1,
            "CP — Le son [on] 🎈",
            "Entendre le son [on].",
            [
                mcq("Dans quel mot entends-tu le son [on] ?", ["rond", "chat", "lune"], 0, emoji="⭕"),
                mcq("Dans quel mot entends-tu le son [on] ?", ["pont", "papa", "lit"], 0, emoji="🌉"),
                mcq("Dans quel mot entends-tu le son [on] ?", ["maison", "moto", "sac"], 0, emoji="🏡"),
                mcq("Dans quel mot entends-tu le son [on] ?", ["ballon", "vélo", "table"], 0, emoji="🎈"),
            ],
        ),
        # 8. Le son [an] / [en]
        L(
            8,
            1,
            "CP — Le son [an] / [en] 🦷",
            "Entendre le son [an].",
            [
                mcq("Dans quel mot entends-tu le son [an] ?", ["dent", "chat", "lune"], 0, emoji="🦷"),
                mcq("Dans quel mot entends-tu le son [an] ?", ["enfant", "moto", "lit"], 0, emoji="🧒"),
                mcq("Dans quel mot entends-tu le son [an] ?", ["maman", "papi", "sac"], 0, emoji="👩"),
                mcq("Dans quel mot entends-tu le son [an] ?", ["vent", "vélo", "riz"], 0, emoji="💨"),
            ],
        ),
        # 9. Le son [oi]
        L(
            9,
            1,
            "CP — Le son [oi] 👑",
            "Entendre le son [oi].",
            [
                mcq("Dans quel mot entends-tu le son [oi] ?", ["roi", "chat", "lune"], 0, emoji="👑"),
                mcq("Dans quel mot entends-tu le son [oi] ?", ["toit", "papa", "lit"], 0, emoji="🏠"),
                mcq("Dans quel mot entends-tu le son [oi] ?", ["poire", "moto", "sac"], 0, emoji="🍐"),
                mcq("Dans quel mot entends-tu le son [oi] ?", ["bois", "vélo", "riz"], 0, emoji="🌳"),
            ],
        ),
        # 10. Le son [in]
        L(
            10,
            1,
            "CP — Le son [in] 🐰",
            "Entendre le son [in].",
            [
                mcq("Dans quel mot entends-tu le son [in] ?", ["lapin", "chat", "lune"], 0, emoji="🐰"),
                mcq("Dans quel mot entends-tu le son [in] ?", ["main", "papa", "lit"], 0, emoji="✋"),
                mcq("Dans quel mot entends-tu le son [in] ?", ["sapin", "moto", "sac"], 0, emoji="🌲"),
                mcq("Dans quel mot entends-tu le son [in] ?", ["pain", "vélo", "riz"], 0, emoji="🍞"),
            ],
        ),
        # 11. Reconnaître des mots simples (image ↔ mot)
        L(
            11,
            2,
            "CP — Lire des mots simples 🖼️",
            "Associer une image et son mot.",
            [
                mcq("Quel mot va avec l'image ? 🐱", ["chat", "chien", "vache"], 0, emoji="🐱"),
                mcq("Quel mot va avec l'image ? ☀️", ["soleil", "lune", "étoile"], 0, emoji="☀️"),
                mcq("Quel mot va avec l'image ? 🍎", ["pomme", "poire", "banane"], 0, emoji="🍎"),
                fill_blanks("Écris le mot de l'animal. 🐱", "Le ___ miaule.", ["chat"]),
            ],
        ),
        # 12. La phrase : majuscule au début, point à la fin
        L(
            12,
            2,
            "CP — La phrase : majuscule et point 📝",
            "Une phrase commence par une majuscule et finit par un point.",
            [
                mcq("Par quoi commence une phrase ?", ["une majuscule", "une minuscule", "un chiffre"], 0),
                mcq("Comment se termine une phrase ?", ["par un point", "par une virgule", "par rien"], 0),
                mcq("Quelle phrase est bien écrite ?", ["Le chat dort.", "le chat dort", "le chat dort"], 0),
                mcq("Où met-on la majuscule ?", ["au début de la phrase", "à la fin", "au milieu"], 0),
            ],
        ),
        # 13. L'ordre alphabétique
        L(
            13,
            2,
            "CP — L'ordre alphabétique 🔤",
            "Ranger les lettres dans l'ordre.",
            [
                mcq("Quelle lettre vient après « a » ?", ["b", "c", "d"], 0),
                mcq("Quelle lettre vient avant « d » ?", ["c", "e", "b"], 0),
                mcq("Quel mot vient en premier dans l'alphabet ?", ["arbre", "banane", "chat"], 0),
                mcq("Quelle lettre est la première de l'alphabet ?", ["a", "z", "m"], 0),
            ],
        ),
        # 14. Comprendre une phrase courte (lecture-compréhension)
        L(
            14,
            2,
            "CP — Je comprends ce que je lis 📖",
            "Lire de courtes phrases et répondre.",
            [
                reading(
                    "Lis cette petite histoire.",
                    "Le chat de Léa est noir. Il dort sur le lit. Léa aime beaucoup son chat.",
                ),
                mcq("De quelle couleur est le chat ?", ["noir", "blanc", "roux"], 0),
                mcq("Où dort le chat ?", ["sur le lit", "sous la table", "dans le jardin"], 0),
                mcq("À qui est le chat ?", ["à Léa", "à Tom", "à papa"], 0),
            ],
        ),
        # 15. Petits mots outils fréquents
        L(
            15,
            2,
            "CP — Les petits mots : le, la, un, et, est 🔑",
            "Reconnaître les petits mots fréquents.",
            [
                mcq("Complète : ___ chat dort.", ["le", "la", "les"], 0),
                mcq("Complète : ___ lune brille.", ["la", "le", "un"], 0),
                mcq("Complète : papa ___ maman.", ["et", "est", "es"], 0),
                mcq("Complète : le ciel ___ bleu.", ["est", "et", "es"], 0),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-francais")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Français "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
