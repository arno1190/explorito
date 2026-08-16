"""Seed CE2 Orthographe — couverture du programme (leçons avancées).

Idempotent par (parcours, nom de leçon). Réponses correctes par construction.

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce2_orthographe.py [--dry-run]
"""

import sys
from typing import Any

from seed_curriculum import _seed_one, fill_blanks, mcq, theme

from app.core.database import SessionLocal

LEVEL = "ce2"
SLUG = "orthographe"


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
        # ------------------------------------------------------------------ #
        # 1. L'accord sujet-verbe (level 4)
        # ------------------------------------------------------------------ #
        L(
            10,
            4,
            "CE2 — L'accord du verbe avec le sujet ✍️",
            "Accorder le verbe avec son sujet.",
            [
                mcq("Les enfants ___ dans le jardin.", ["joue", "jouent", "joues"], 1),
                mcq("Le chat ___ sur le canapé.", ["dorment", "dort", "dors"], 1),
                mcq("Tu ___ un beau dessin.", ["fais", "fait", "font"], 0),
                mcq("Mes amis et moi ___ au football.", ["joue", "jouez", "jouons"], 2),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 2. Le pluriel en -aux (mots en -al) (level 3)
        # ------------------------------------------------------------------ #
        L(
            11,
            3,
            "CE2 — Le pluriel des mots en -al 🐴",
            "Le pluriel des noms terminés par -al.",
            [
                mcq("Le pluriel de « cheval » est :", ["chevals", "chevaux", "cheveaux"], 1),
                mcq("Le pluriel de « journal » est :", ["journals", "journaux", "journeaux"], 1),
                mcq("Le pluriel de « animal » est :", ["animals", "animaux", "animeaux"], 1),
                mcq("Attention à l'exception ! Le pluriel de « bal » est :", ["baux", "bals", "balaux"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 3. m devant m, b, p (level 3)
        # ------------------------------------------------------------------ #
        L(
            12,
            3,
            "CE2 — La règle du m devant m, b, p 🔤",
            "Écrire m au lieu de n devant m, b, p.",
            [
                fill_blanks("Complète par m ou n (m devant m, b, p).", "Je to___be de sommeil.", ["m"]),
                fill_blanks("Complète par m ou n.", "Il range son pull dans la cha___bre.", ["m"]),
                fill_blanks("Complète par m ou n.", "Un gra___d cha___p de blé.", ["n", "m"]),
                mcq("Quel mot est correctement écrit ?", ["un tanbour", "un tambour"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 4. Le son [s] : s, ss, c, ç (level 4)
        # ------------------------------------------------------------------ #
        L(
            13,
            4,
            "CE2 — Le son [s] : s, ss, c, ç 🐍",
            "Écrire le son [s] selon la lettre qui suit.",
            [
                mcq("Pour écrire le son [s] dans « gar___on », il faut :", ["c", "ç", "ss"], 1),
                mcq("Pour garder le son [s] entre deux voyelles dans « pou___ette », il faut :", ["s", "ss", "c"], 1),
                mcq("Dans « le ___itron », le son [s] devant i s'écrit :", ["ss", "c", "s"], 1),
                mcq("Dans quel mot la lettre s se prononce [z] ?", ["classe", "poisson", "maison"], 2),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 5. Le son [ʒ]/[g] : g, ge, gu (level 4)
        # ------------------------------------------------------------------ #
        L(
            14,
            4,
            "CE2 — Les sons de la lettre g : g, ge, gu 🦒",
            "Choisir g, ge ou gu selon le son voulu.",
            [
                mcq("Pour écrire le son [j] dans « nous man___ons », il faut :", ["g", "ge", "gu"], 1),
                mcq("Pour écrire le son [g] dans « une ___itare », il faut :", ["g", "gu", "ge"], 1),
                mcq("Dans « la ___irafe », le son [j] devant i s'écrit :", ["g", "gu", "ge"], 0),
                mcq("Dans quel mot entend-on le son [g] comme dans « gomme » ?", ["girafe", "gâteau", "genou"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 6. Le son [k] : c, qu, k (level 3)
        # ------------------------------------------------------------------ #
        L(
            15,
            3,
            "CE2 — Le son [k] : c, qu, k 🥝",
            "Écrire le son [k] avec c, qu ou k.",
            [
                mcq("Dans « un ___amion », le son [k] s'écrit :", ["c", "qu", "k"], 0),
                mcq("Dans « une ___estion », le son [k] devant e s'écrit :", ["c", "k", "qu"], 2),
                mcq("Dans « un ___iwi », le son [k] s'écrit :", ["c", "k", "qu"], 1),
                mcq("Dans quel mot le son [k] s'écrit « qu » ?", ["carotte", "quatre", "kangourou"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 7. a ou à (level 3)
        # ------------------------------------------------------------------ #
        L(
            16,
            3,
            "CE2 — Homophones : a ou à ✏️",
            "Distinguer « a » (verbe avoir) et « à ».",
            [
                mcq("Papa ___ une voiture rouge.", ["a", "à"], 0),
                mcq("Nous allons ___ la piscine.", ["a", "à"], 1),
                mcq("Léa ___ mangé une pomme.", ["a", "à"], 0),
                mcq("Il joue ___ la balle.", ["a", "à"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 8. et ou est (level 3)
        # ------------------------------------------------------------------ #
        L(
            17,
            3,
            "CE2 — Homophones : et ou est 🔗",
            "Distinguer « et » (lien) et « est » (verbe être).",
            [
                mcq("Le chat ___ le chien jouent ensemble.", ["et", "est"], 0),
                mcq("Mon frère ___ très grand.", ["et", "est"], 1),
                mcq("J'aime les pommes ___ les poires.", ["et", "est"], 0),
                mcq("La maison ___ toute blanche.", ["et", "est"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 9. on ou ont (level 3)
        # ------------------------------------------------------------------ #
        L(
            18,
            3,
            "CE2 — Homophones : on ou ont 👥",
            "Distinguer « on » (pronom) et « ont » (verbe avoir).",
            [
                mcq("___ va jouer au parc.", ["On", "Ont"], 0),
                mcq("Les enfants ___ un nouveau ballon.", ["on", "ont"], 1),
                mcq("___ mange des gâteaux au goûter.", ["On", "Ont"], 0),
                mcq("Mes cousins ___ un grand chien.", ["on", "ont"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 10. son ou sont (level 3)
        # ------------------------------------------------------------------ #
        L(
            19,
            3,
            "CE2 — Homophones : son ou sont 🧢",
            "Distinguer « son » (le sien) et « sont » (verbe être).",
            [
                mcq("Il met ___ manteau bleu.", ["son", "sont"], 0),
                mcq("Les élèves ___ dans la classe.", ["son", "sont"], 1),
                mcq("Arthur range ___ cartable.", ["son", "sont"], 0),
                mcq("Mes parents ___ très contents.", ["son", "sont"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 11. ces ou ses (level 4)
        # ------------------------------------------------------------------ #
        L(
            20,
            4,
            "CE2 — Homophones : ces ou ses 👀",
            "Distinguer « ces » (ceux-là) et « ses » (les siens).",
            [
                mcq("Regarde ___ étoiles dans le ciel !", ["ces", "ses"], 0),
                mcq("Léa range ___ jouets (les jouets de Léa).", ["ces", "ses"], 1),
                mcq("Je n'aime pas ___ chaussures dans la vitrine.", ["ces", "ses"], 0),
                mcq("Il a retrouvé ___ clés (ses propres clés).", ["ces", "ses"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 12. ou ou où (level 3)
        # ------------------------------------------------------------------ #
        L(
            21,
            3,
            "CE2 — Homophones : ou ou où 🗺️",
            "Distinguer « ou » (choix) et « où » (lieu).",
            [
                mcq("Tu veux du thé ___ du café ?", ["ou", "où"], 0),
                mcq("___ habites-tu ?", ["Ou", "Où"], 1),
                mcq("Rouge ___ bleu, choisis une couleur !", ["ou", "où"], 0),
                mcq("Je sais ___ tu vas.", ["ou", "où"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 13. Les accents é, è, ê (level 4)
        # ------------------------------------------------------------------ #
        L(
            22,
            4,
            "CE2 — Les accents é, è, ê 🎩",
            "Choisir le bon accent sur la lettre e.",
            [
                mcq("Quel mot est correctement accentué ?", ["une fenétre", "une fenêtre", "une fenètre"], 1),
                mcq("Quel mot est correctement accentué ?", ["un élève", "un èlève", "un éléve"], 0),
                mcq(
                    "Quel accent faut-il sur « t_te » (sur les épaules) ?",
                    ["é (accent aigu)", "è (accent grave)", "ê (accent circonflexe)"],
                    2,
                ),
                mcq(
                    "Quel accent faut-il sur « m_re » (la maman) ?",
                    ["é (accent aigu)", "è (accent grave)", "ê (accent circonflexe)"],
                    1,
                ),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 14. Les lettres finales muettes (level 4)
        # ------------------------------------------------------------------ #
        L(
            23,
            4,
            "CE2 — Les lettres finales muettes 🤫",
            "Trouver la lettre muette à la fin d'un mot.",
            [
                mcq("Comment se termine « peti_ » ? Pense à « petite ».", ["petit", "petis", "peti"], 0),
                mcq("Comment se termine « bor_ » ? Pense à « border ».", ["bord", "bort", "bor"], 0),
                mcq("Comment se termine « cha_ » (l'animal) ? Pense à « chatte ».", ["chat", "cha", "chad"], 0),
                mcq("Comment se termine « gran_ » ? Pense à « grande ».", ["grant", "grand", "gran"], 1),
            ],
        ),
        # ------------------------------------------------------------------ #
        # 15. c'est ou s'est (level 4)
        # ------------------------------------------------------------------ #
        L(
            24,
            4,
            "CE2 — Homophones : c'est ou s'est 🪞",
            "Distinguer « c'est » (cela est) et « s'est » (se + est).",
            [
                mcq("___ un très beau jour.", ["C'est", "S'est"], 0),
                mcq("Il ___ lavé les mains avant de manger.", ["c'est", "s'est"], 1),
                mcq("___ mon meilleur ami.", ["C'est", "S'est"], 0),
                mcq("Le chat ___ caché sous le lit.", ["c'est", "s'est"], 1),
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons CE2 Orthographe "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
