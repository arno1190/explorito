"""
Seed d'une progression lente de mathématiques CE1 (générée par calcul).

~24 leçons réparties sur des paliers croissants (additions → soustractions →
compléments → suites → doubles/moitiés → tables → problèmes → monnaie…). Toutes
les réponses sont calculées en Python (correctes par construction). Nombres
déterministes (random ensemencé) pour un contenu identique dev/prod.

Idempotent par (parcours, nom de leçon).

Usage:
    DATABASE_URL=... uv run python scripts/seed_ce1_maths.py [--dry-run]
"""

import random
import sys
from typing import Any

from seed_curriculum import _seed_one, math_problem, mcq, pythagore, theme

from app.core.database import SessionLocal

random.seed(20260801)
LEVEL = "ce1"


def _mp(a: int, op: str, b: int) -> dict[str, Any]:
    val = a + b if op == "+" else a - b
    return math_problem(f"Calcule : {a} {op} {b}", val)


def add_no_carry(count: int, hi: int) -> list[dict[str, Any]]:
    out = []
    while len(out) < count:
        a, b = random.randint(1, hi), random.randint(1, hi)
        if (a % 10) + (b % 10) <= 9 and a + b <= hi * 2:
            out.append(_mp(a, "+", b))
    return out


def add_carry(count: int, hi: int) -> list[dict[str, Any]]:
    out = []
    while len(out) < count:
        a, b = random.randint(6, hi), random.randint(6, hi)
        if (a % 10) + (b % 10) >= 10:
            out.append(_mp(a, "+", b))
    return out


def sub_no_borrow(count: int, hi: int) -> list[dict[str, Any]]:
    out = []
    while len(out) < count:
        a, b = random.randint(2, hi), random.randint(1, hi)
        if a >= b and (a % 10) >= (b % 10):
            out.append(_mp(a, "-", b))
    return out


def sub_borrow(count: int, hi: int) -> list[dict[str, Any]]:
    out = []
    while len(out) < count:
        a, b = random.randint(11, hi), random.randint(2, hi)
        if a > b and (a % 10) < (b % 10):
            out.append(_mp(a, "-", b))
    return out


def complements(count: int, target: int) -> list[dict[str, Any]]:
    out = []
    seen = set()
    step = 10 if target == 100 else 1
    while len(out) < count:
        a = random.randrange(0, target + 1, step)
        if a in seen:
            continue
        seen.add(a)
        out.append(math_problem(f"Complète : {a} + ? = {target}", target - a))
    return out


def count_by(step: int) -> list[dict[str, Any]]:
    out = []
    for _ in range(5):
        start = random.randint(0, 8) * step
        seq = [start + i * step for i in range(4)]
        out.append(math_problem(f"Continue la suite : {seq[0]}, {seq[1]}, {seq[2]}, ?", seq[3]))
    return out


def doubles() -> list[dict[str, Any]]:
    return [math_problem(f"Quel est le double de {n} ?", n * 2) for n in random.sample(range(2, 25), 5)]


def halves() -> list[dict[str, Any]]:
    return [math_problem(f"Quelle est la moitié de {n} ?", n // 2) for n in random.sample(range(2, 25, 2), 5)]


def compare(count: int, hi: int) -> list[dict[str, Any]]:
    out = []
    for _ in range(count):
        nums = random.sample(range(1, hi), 3)
        out.append(mcq("Quel est le plus grand nombre ?", [str(n) for n in nums], nums.index(max(nums))))
    return out


def table(t: int) -> list[dict[str, Any]]:
    ks = random.sample(range(1, 11), 4)
    ex = [math_problem(f"Calcule : {t} × {k}", t * k) for k in ks]
    ex.append(pythagore(f"Complète la table de {t}.", [t], blanks=5))
    return ex


def word_add() -> list[dict[str, Any]]:
    scenes = [
        ("Léa a {a} billes, elle en gagne {b}. Combien en a-t-elle ?", "🔵"),
        ("Il y a {a} oiseaux, {b} arrivent. Combien d'oiseaux ?", "🐦"),
        ("Tom lit {a} pages lundi et {b} mardi. Combien de pages ?", "📖"),
    ]
    out = []
    for _ in range(5):
        tpl, emo = random.choice(scenes)
        a, b = random.randint(5, 40), random.randint(5, 40)
        out.append(math_problem(tpl.format(a=a, b=b), a + b, emoji=emo))
    return out


def word_sub() -> list[dict[str, Any]]:
    scenes = [
        ("Il y a {a} bonbons, on en mange {b}. Combien reste-t-il ?", "🍬"),
        ("Zoé a {a} images, elle en donne {b}. Combien lui reste-t-il ?", "🖼️"),
        ("Un bus a {a} places, {b} sont prises. Combien de places libres ?", "🚌"),
    ]
    out = []
    for _ in range(5):
        tpl, emo = random.choice(scenes)
        a = random.randint(20, 60)
        b = random.randint(3, a - 1)
        out.append(math_problem(tpl.format(a=a, b=b), a - b, emoji=emo))
    return out


def money() -> list[dict[str, Any]]:
    out = []
    for _ in range(5):
        a, b = random.randint(2, 30), random.randint(2, 30)
        out.append(
            math_problem(f"Un jouet coûte {a} € et un autre {b} €. Combien en tout ?", a + b, unit="€", emoji="🧸")
        )
    return out


def word_mult() -> list[dict[str, Any]]:
    scenes = [
        ("{a} sachets de {b} bonbons. Combien de bonbons ?", "🍬"),
        ("{a} boîtes de {b} œufs. Combien d'œufs ?", "🥚"),
        ("{a} paquets de {b} stylos. Combien de stylos ?", "🖊️"),
    ]
    out = []
    for _ in range(5):
        tpl, emo = random.choice(scenes)
        a, b = random.randint(2, 5), random.randint(2, 10)
        out.append(math_problem(tpl.format(a=a, b=b), a * b, emoji=emo))
    return out


def even_odd() -> list[dict[str, Any]]:
    out = []
    for _ in range(5):
        n = random.randint(1, 50)
        out.append(mcq(f"Le nombre {n} est…", ["pair", "impair"], 0 if n % 2 == 0 else 1))
    return out


def before_after() -> list[dict[str, Any]]:
    out = []
    for _ in range(5):
        n = random.randint(1, 98)
        if random.random() < 0.5:
            out.append(math_problem(f"Quel nombre vient juste après {n} ?", n + 1))
        else:
            out.append(math_problem(f"Quel nombre vient juste avant {n + 1} ?", n))
    return out


def three_add() -> list[dict[str, Any]]:
    out = []
    for _ in range(5):
        a, b, c = (random.randint(1, 15) for _ in range(3))
        out.append(math_problem(f"Calcule : {a} + {b} + {c}", a + b + c))
    return out


# (palier, nom, description, xp, exercices)
LESSONS: list[tuple[int, str, str, int, list[dict[str, Any]]]] = [
    (1, "Additions jusqu'à 20", "Additionner de petits nombres.", 40, add_no_carry(5, 12)),
    (1, "Compléments à 10", "Trouver ce qu'il manque pour faire 10.", 40, complements(5, 10)),
    (2, "Additions sans retenue", "Additionner jusqu'à 100 sans retenue.", 45, add_no_carry(5, 40)),
    (2, "Soustractions jusqu'à 20", "Soustraire de petits nombres.", 45, sub_no_borrow(5, 20)),
    (3, "Additions avec retenue", "Additionner avec une retenue.", 50, add_carry(5, 40)),
    (3, "Soustractions sans retenue", "Soustraire jusqu'à 100.", 50, sub_no_borrow(5, 80)),
    (4, "Soustractions avec retenue", "Soustraire avec un emprunt.", 55, sub_borrow(5, 60)),
    (4, "Compléments à 100", "Trouver ce qu'il manque pour faire 100.", 55, complements(5, 100)),
    (5, "Compter de 2 en 2", "Suites de 2 en 2.", 45, count_by(2)),
    (5, "Compter de 5 en 5", "Suites de 5 en 5.", 45, count_by(5)),
    (6, "Les doubles", "Calculer le double d'un nombre.", 50, doubles()),
    (6, "Les moitiés", "Calculer la moitié d'un nombre.", 50, halves()),
    (7, "Comparer les nombres", "Trouver le plus grand.", 45, compare(5, 100)),
    (7, "Pair ou impair", "Reconnaître les nombres pairs et impairs.", 45, even_odd()),
    (8, "La table de 2", "Multiplier par 2.", 55, table(2)),
    (8, "La table de 5", "Multiplier par 5.", 55, table(5)),
    (9, "La table de 3", "Multiplier par 3.", 55, table(3)),
    (9, "La table de 10", "Multiplier par 10.", 55, table(10)),
    (10, "Avant et après", "Le nombre juste avant / juste après.", 45, before_after()),
    (10, "Additions à trois nombres", "Additionner trois nombres.", 55, three_add()),
    (11, "Problèmes d'addition", "Résoudre des problèmes (+).", 60, word_add()),
    (11, "Problèmes de soustraction", "Résoudre des problèmes (−).", 60, word_sub()),
    (12, "La monnaie (euros)", "Additionner des prix en euros.", 60, money()),
    (12, "Problèmes de multiplication", "Résoudre des problèmes (×).", 60, word_mult()),
]


def main(dry_run: bool = False) -> int:
    themes = [theme("maths", LEVEL, tier, name, desc, xp, exercises) for tier, name, desc, xp, exercises in LESSONS]
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
            f"\n{'(dry-run) ' if dry_run else ''}{len(themes)} leçons maths CE1 "
            f"({total_ex} exercices) — créées: {created}, déjà présentes: {skipped}."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--dry-run" in sys.argv))
