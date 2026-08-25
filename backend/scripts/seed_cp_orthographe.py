"""Seed CP Orthographe — écrire les sons et les mots (programme officiel).

Première année (CP, ~6 ans). Les enfants ne tapent pas les accents et la
correction est sensible aux accents : on privilégie donc le choix de la bonne
écriture parmi des options (mcq), et on n'utilise ``fill_blanks`` que pour des
réponses en minuscules et sans accent.

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_cp_orthographe.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, shuffle_options, theme

from app.core.database import SessionLocal

LEVEL = "cp"
SLUG = "orthographe"


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
        # ------------------------------------------------------------------ #
        # 1. Écrire les syllabes simples (level 1)
        # ------------------------------------------------------------------ #
        L(
            1,
            1,
            "CP — 🔤 Les syllabes simples",
            "Écrire des syllabes simples : ma, ri, lo…",
            [
                mcq("Comment écrit-on la syllabe [ma] ?", ["ma", "am", "na"], 0),
                mcq("Comment écrit-on la syllabe [ri] ?", ["ir", "ri", "li"], 1),
                mcq("Comment écrit-on la syllabe [lo] ?", ["ol", "do", "lo"], 2),
                fill_blanks(
                    "Écris la syllabe que tu entends au début de « moto ».",
                    "___to",
                    ["mo"],
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 2. Le son [s] : s / ss (level 1)
        # ------------------------------------------------------------------ #
        L(
            2,
            1,
            "CP — 🐍 Le son [s] : s ou ss",
            "Écrire le son [s] avec s ou ss.",
            [
                mcq("Comment écrit-on ce mot ? 🎒", ["sac", "ssac", "zac"], 0, emoji="🎒"),
                mcq("Comment écrit-on ce mot ? 🐟", ["poison", "poisson", "poisonn"], 1, emoji="🐟"),
                mcq(
                    "Entre deux voyelles, pour faire le son [s], on écrit :",
                    ["s", "ss", "z"],
                    1,
                    explanation="Entre deux voyelles, un seul s se dit [z] (rose). On double : ss (tasse).",
                ),
                mcq("Comment écrit-on ce mot ? ☕", ["tase", "tasse", "tace"], 1, emoji="☕"),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 3. Le son [k] : c / k / qu (level 1)
        # ------------------------------------------------------------------ #
        L(
            3,
            1,
            "CP — 🥝 Le son [k] : c, k ou qu",
            "Écrire le son [k] avec c, k ou qu.",
            [
                mcq("Comment écrit-on ce mot ? 🐨", ["coala", "koala", "qoala"], 1, emoji="🐨"),
                mcq("Comment écrit-on ce mot ? 🥝", ["kiwi", "quiwi", "ciwi"], 0, emoji="🥝"),
                mcq("Comment écrit-on le mot « quatre » ?", ["catre", "quatre", "katre"], 1),
                mcq(
                    "Devant e et i, le son [k] s'écrit souvent :",
                    ["c", "qu", "k"],
                    1,
                    explanation="Devant e et i, on écrit qu : qui, que, quille.",
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 4. Le son [ε] : è / ê / ai (mcq only — pas de saisie d'accents) (level 1)
        # ------------------------------------------------------------------ #
        L(
            4,
            1,
            "CP — 🎩 Le son [è] : è, ê ou ai",
            "Écrire le son [è] avec è, ê ou ai.",
            [
                mcq("Comment écrit-on ce mot ? 🥛", ["lait", "lé", "lè"], 0, emoji="🥛"),
                mcq("Comment écrit-on le mot pour la maman ?", ["mère", "mere", "maire"], 0),
                mcq("Comment écrit-on ce mot ? 🎉", ["fete", "fête", "faite"], 1, emoji="🎉"),
                mcq("Comment écrit-on ce mot ? 🌲", ["foret", "forè", "forêt"], 2, emoji="🌲"),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 5. m devant m, b, p (level 1)
        # ------------------------------------------------------------------ #
        L(
            5,
            1,
            "CP — 🔡 La règle du m devant m, b, p",
            "Écrire m au lieu de n devant m, b, p.",
            [
                mcq("Comment écrit-on ce mot ? 🦵", ["janbe", "jambe"], 1, emoji="🦵"),
                mcq(
                    "Devant les lettres m, b et p, on écrit :",
                    ["n", "m"],
                    1,
                    explanation="Devant m, b, p on met un m : jambe, pompier, tomber.",
                ),
                fill_blanks(
                    "Complète par m ou n : c'est la pièce où l'on dort.",
                    "la cha___bre",
                    ["m"],
                ),
                mcq("Comment écrit-on ce mot ? 🚒", ["ponpier", "pompier"], 1, emoji="🚒"),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 6. Le son [ʒ] : g / j (level 1)
        # ------------------------------------------------------------------ #
        L(
            6,
            1,
            "CP — 🦒 Le son [j] : g ou j",
            "Écrire le son [j] avec g ou j.",
            [
                mcq("Comment écrit-on ce mot ? 🦒", ["girafe", "jirafe"], 0, emoji="🦒"),
                mcq("Comment écrit-on ce mot ? 🌳", ["gardin", "jardin"], 1, emoji="🌳"),
                mcq("Comment écrit-on ce mot ? 🧸", ["gouet", "jouet"], 1, emoji="🧸"),
                mcq(
                    "Devant e et i, la lettre g fait le son [j], comme dans :",
                    ["gomme", "girafe", "gâteau"],
                    1,
                    explanation="g devant e ou i fait [j] : girafe, genou. Sinon g dit [g] : gomme.",
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 7. Le son [g] dur : g / gu (level 1)
        # ------------------------------------------------------------------ #
        L(
            7,
            1,
            "CP — 🎸 Le son [g] : g ou gu",
            "Écrire le son [g] dur avec g ou gu.",
            [
                mcq("Comment écrit-on ce mot ? 🎂", ["jateau", "gateau", "gâteau"], 2, emoji="🎂"),
                mcq("Comment écrit-on ce mot ? 🎸", ["gitare", "guitare"], 1, emoji="🎸"),
                mcq(
                    "Devant e et i, pour garder le son [g] dur, on écrit :",
                    ["g", "gu"],
                    1,
                    explanation="Devant e ou i, on écrit gu pour dire [g] : guitare, guépard, bague.",
                ),
                mcq("Comment écrit-on ce mot ? 🐆", ["gépard", "guépard"], 1, emoji="🐆"),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 8. Le pluriel des noms : ajouter -s (level 1)
        # ------------------------------------------------------------------ #
        L(
            8,
            1,
            "CP — 🐈 Le pluriel : j'ajoute un -s",
            "Former le pluriel des noms en ajoutant -s.",
            [
                mcq("Quel est le pluriel de « un chat » ?", ["des chats", "des chatx", "des chates"], 0),
                mcq("Quel est le pluriel de « une fleur » ?", ["des fleur", "des fleurs"], 1),
                fill_blanks(
                    "Mets au pluriel : un chien → des …",
                    "des ___",
                    ["chiens"],
                ),
                mcq(
                    "Pour former le pluriel de la plupart des noms, on ajoute :",
                    ["-s", "-t", "-x"],
                    0,
                    explanation="Le plus souvent, le pluriel se forme en ajoutant un s : un ami → des amis.",
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 9. Le / la / les — le bon déterminant (level 1)
        # ------------------------------------------------------------------ #
        L(
            9,
            1,
            "CP — 📘 Le, la ou les",
            "Choisir le bon déterminant : le, la ou les.",
            [
                mcq("Complète : ___ soleil ☀️", ["le", "la"], 0),
                mcq("Complète : ___ lune 🌙", ["le", "la"], 1),
                mcq("Complète : ___ enfants (plusieurs)", ["le", "les"], 1),
                mcq("Complète : ___ maison 🏠", ["le", "la", "les"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 10. Un / une — masculin / féminin (level 1)
        # ------------------------------------------------------------------ #
        L(
            10,
            1,
            "CP — ⚖️ Un ou une",
            "Choisir un (masculin) ou une (féminin).",
            [
                mcq("Complète : ___ chat 🐱", ["un", "une"], 0),
                mcq("Complète : ___ pomme 🍎", ["un", "une"], 1),
                mcq("Complète : ___ ballon 🎈", ["un", "une"], 0),
                mcq("Complète : ___ voiture 🚗", ["un", "une"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 11. Les mots outils fréquents (level 2)
        # ------------------------------------------------------------------ #
        L(
            11,
            2,
            "CP — 🔗 Les petits mots : et, est, dans, avec",
            "Écrire les mots outils les plus fréquents.",
            [
                mcq("Complète : Papa ___ maman sont là.", ["et", "est"], 0),
                mcq("Complète : Le chat ___ noir.", ["et", "est"], 1),
                mcq("Complète : Le jouet est ___ la boîte.", ["dans", "avec"], 0),
                mcq("Complète : Je joue ___ mon ami.", ["dans", "avec"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 12. La lettre finale muette simple (level 2)
        # ------------------------------------------------------------------ #
        L(
            12,
            2,
            "CP — 🤫 La lettre muette à la fin",
            "Trouver la lettre muette à la fin d'un mot.",
            [
                mcq("Comment écrit-on « petit » ? (pense à « petite »)", ["peti", "petis", "petit"], 2),
                mcq("Comment écrit-on « grand » ? (pense à « grande »)", ["gran", "grant", "grand"], 2),
                mcq("Comment écrit-on « chat » ? (pense à « chatte »)", ["cha", "chat", "chad"], 1),
                mcq("Comment écrit-on « lit » ? 🛏️ (pense à « literie »)", ["li", "lis", "lit"], 2, emoji="🛏️"),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 13. Le son [f] : f / ph (level 2, simple)
        # ------------------------------------------------------------------ #
        L(
            13,
            2,
            "CP — 📷 Le son [f] : f ou ph",
            "Écrire le son [f] avec f ou ph.",
            [
                mcq("Comment écrit-on ce mot ? 📷", ["foto", "photo"], 1, emoji="📷"),
                mcq("Comment écrit-on ce mot ? 🐘", ["éléfant", "éléphant"], 1, emoji="🐘"),
                mcq("Comment écrit-on ce mot ? 🌸", ["fleur", "phleur"], 0, emoji="🌸"),
                mcq(
                    "Dans quel mot le son [f] s'écrit « ph » ?",
                    ["farine", "photo", "fille"],
                    1,
                    explanation="Certains mots s'écrivent avec ph : photo, téléphone, éléphant.",
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 14. Écrire une phrase : majuscule + point + espaces (level 2)
        # ------------------------------------------------------------------ #
        L(
            14,
            2,
            "CP — ✍️ Bien écrire une phrase",
            "Majuscule au début, point à la fin, espaces entre les mots.",
            [
                mcq("Une phrase commence toujours par :", ["une majuscule", "une virgule", "un chiffre"], 0),
                mcq("Une phrase se termine par :", ["un point", "une majuscule", "rien"], 0),
                mcq(
                    "Quelle phrase est bien écrite ?",
                    ["le chat dort.", "Le chat dort", "Le chat dort."],
                    2,
                ),
                mcq("Entre deux mots, on laisse :", ["rien", "un espace", "un point"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 15. Copier / écrire des mots courants sans erreur (level 2)
        # ------------------------------------------------------------------ #
        L(
            15,
            2,
            "CP — 🏫 Écrire les mots courants",
            "Écrire sans erreur des mots de tous les jours.",
            [
                mcq("Comment écrit-on ce mot ? 🏫", ["école", "écolle", "ecole"], 0, emoji="🏫"),
                mcq("Comment écrit-on ce mot ? 👦", ["garson", "garçon", "garcon"], 1, emoji="👦"),
                mcq("Comment écrit-on ce mot ? 🍞", ["pin", "pain", "pein"], 1, emoji="🍞"),
                fill_blanks(
                    "Recopie le mot sans erreur.",
                    "___",
                    ["maman"],
                ),
            ],
        ),
    ]


def main(dry_run: bool = False) -> int:
    themes = shuffle_options(curriculum(), salt="cp-orthographe")
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CP Orthographe "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
