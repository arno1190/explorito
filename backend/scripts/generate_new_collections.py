"""Génère les catalogues de collection Dragon Ball / Harry Potter / Mario.

Sources :
- Dragon Ball : API publique dragonball-api.com (58 personnages).
- Harry Potter : API publique hp-api.onrender.com (personnages avec image).
- Mario : API communautaire super-mario-bros-character-api (roster fixe de 15),
  complétée par quelques personnages clés absents (Peach, Daisy, Boo) avec
  illustration officielle.

Les images sont **téléchargées** sous ``uploads/img/collectibles/<slug>/`` (servies
par ``/uploads`` ; hors dépôt Git — usage personnel, pas de redistribution) et le
JSON du catalogue est écrit dans ``app/data/<slug>.json``. Les « facts » sont en
français (construits à partir de champs structurés, pas de texte inventé).

Usage :
    uv run python scripts/generate_new_collections.py [--only dragon_ball,harry_potter,mario]
"""

from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from app.core.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
IMG_ROOT = Path(settings.UPLOAD_DIR) / "img" / "collectibles"

# TLS vérifié par défaut ; repli non vérifié UNIQUEMENT si le certificat échoue
# (ex. chaîne de certificats incomplète de mario.nintendo.com). Ce script est un
# outil de génération local qui ne récupère que des images publiques.
_INSECURE = ssl.create_default_context()
_INSECURE.check_hostname = False
_INSECURE.verify_mode = ssl.CERT_NONE


def _open(url: str, timeout: int = 45):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), ssl.SSLError) or isinstance(e, ssl.SSLError):
            return urllib.request.urlopen(req, context=_INSECURE, timeout=timeout)
        raise


def _get(url: str) -> Any:
    with _open(url) as r:
        return json.loads(r.read())


def _download(url: str, slug: str, item_id: int) -> str | None:
    """Télécharge l'image et renvoie l'URL locale ``/uploads/...`` (idempotent)."""
    if not url:
        return None
    url = url.replace(" ", "%20")  # certaines URLs DBZ contiennent des espaces
    ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
    if ext not in {"png", "jpg", "jpeg", "webp", "gif"}:
        ext = "png"
    out_dir = IMG_ROOT / slug
    out = out_dir / f"{item_id}.{ext}"
    rel = f"/uploads/img/collectibles/{slug}/{item_id}.{ext}"
    if out.exists() and out.stat().st_size > 0:
        return rel
    try:
        with _open(url, timeout=60) as r:
            data = r.read()
    except Exception as e:  # noqa: BLE001 - on log et on continue
        print(f"  ! image KO {url}: {e}")
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return rel


def _price_curve(n: int) -> list[int]:
    """Prix décroissants 200 -> 10 (exponentiel), arrondis à 5. rank 0 = le + cher."""
    lo, hi = 10, 200
    if n == 1:
        return [hi]
    out = []
    for i in range(n):
        t = i / (n - 1)
        val = hi * ((lo / hi) ** t)
        out.append(max(lo, round(val / 5) * 5))
    return out


def _assign_prices(items: list[dict[str, Any]], legendary_keys: list[str]) -> None:
    """Ordonne par notoriété (légendaires d'abord) puis applique la courbe de prix."""

    def score(it: dict[str, Any]) -> tuple[int, int]:
        name = it["name_fr"].lower()
        for rank, key in enumerate(legendary_keys):
            if key.lower() in name:
                return (0, rank)
        return (1, it["id"])

    order = sorted(items, key=score)
    prices = _price_curve(len(order))
    for it, p in zip(order, prices, strict=True):
        it["price"] = p


# --------------------------------------------------------------------------- #
# Dragon Ball
# --------------------------------------------------------------------------- #
DBZ_RACE = {
    "Saiyan": "Saïyan",
    "Namekian": "Namek",
    "Human": "Humain",
    "Frieza Race": "Race de Freezer",
    "Android": "Cyborg",
    "Majin": "Majin",
    "God": "Dieu",
    "Angel": "Ange",
    "Unknown": "Inconnue",
    "Jiren Race": "Race de Jiren",
    "Nucleico benigno": "Nucléico bénin",
    "Evil": "Maléfique",
    "Nucleico": "Nucléico",
}
DBZ_AFF = {
    "Z Fighter": "Guerrier Z",
    "Army of Frieza": "Armée de Freezer",
    "Freelancer": "Indépendant",
    "Other": "Autre",
    "Villain": "Méchant",
    "Assistant of Beerus": "Assistant de Beerus",
    "Pride Troopers": "Pride Troopers",
    "Assistant of Vermoud": "Assistant de Vermoud",
}
DBZ_LEGENDARY = [
    "Goku",
    "Vegeta",
    "Gohan",
    "Piccolo",
    "Freezer",
    "Frieza",
    "Cell",
    "Buu",
    "Broly",
    "Beerus",
    "Whis",
    "Trunks",
    "Gogeta",
    "Vegetto",
]


def build_dragon_ball() -> list[dict[str, Any]]:
    raw = _get("https://dragonball-api.com/api/characters?page=1&limit=100")["items"]
    items = []
    for i, c in enumerate(sorted(raw, key=lambda x: x["id"]), start=1):
        race = DBZ_RACE.get(c.get("race"), c.get("race") or "Inconnue")
        aff = DBZ_AFF.get(c.get("affiliation"), c.get("affiliation") or "Autre")
        maxki = (c.get("maxKi") or "").strip()
        fact = f"Race : {race}. Camp : {aff}."
        if maxki and maxki.lower() != "unknown":
            fact += f" Puissance maximale : {maxki}."
        img = _download(c.get("image"), "dragon_ball", i)
        items.append({"id": i, "name_fr": c["name"], "image_url": img, "fact": fact})
    _assign_prices(items, DBZ_LEGENDARY)
    return items


# --------------------------------------------------------------------------- #
# Harry Potter
# --------------------------------------------------------------------------- #
HP_HOUSE = {
    "Gryffindor": "Gryffondor",
    "Slytherin": "Serpentard",
    "Hufflepuff": "Poufsouffle",
    "Ravenclaw": "Serdaigle",
}
HP_SPECIES = {
    "human": "humain",
    "half-giant": "demi-géant",
    "werewolf": "loup-garou",
    "cat": "chat",
    "ghost": "fantôme",
    "giant": "géant",
    "goblin": "gobelin",
}
HP_PATRONUS = {
    "stag": "cerf",
    "otter": "loutre",
    "doe": "biche",
    "hare": "lièvre",
    "horse": "cheval",
    "lynx": "lynx",
    "persian cat": "chat persan",
    "swan": "cygne",
    "tabby cat": "chat tigré",
    "weasel": "belette",
    "wolf": "loup",
    "Jack Russell terrier": "Jack Russell",
}
HP_NAME = {"Harry Potter": "Harry Potter", "Hermione Granger": "Hermione Granger"}
HP_LEGENDARY = [
    "Harry Potter",
    "Hermione",
    "Ron Weasley",
    "Dumbledore",
    "Snape",
    "Voldemort",
    "Riddle",
    "Hagrid",
    "Draco",
    "Sirius",
    "McGonagall",
]


def build_harry_potter() -> list[dict[str, Any]]:
    raw = [c for c in _get("https://hp-api.onrender.com/api/characters") if c.get("image")]
    items = []
    for i, c in enumerate(raw, start=1):
        parts = []
        house = HP_HOUSE.get(c.get("house"))
        if house:
            parts.append(f"Maison : {house}")
        species = HP_SPECIES.get(c.get("species"), c.get("species"))
        if species:
            parts.append(f"Espèce : {species}")
        pat = c.get("patronus")
        if pat and pat.lower() != "non-corporeal":
            parts.append(f"Patronus : {HP_PATRONUS.get(pat, pat)}")
        fact = ". ".join(parts) + "." if parts else "Personnage du monde des sorciers."
        img = _download(c.get("image"), "harry_potter", i)
        items.append({"id": i, "name_fr": HP_NAME.get(c["name"], c["name"]), "image_url": img, "fact": fact})
    _assign_prices(items, HP_LEGENDARY)
    return items


# --------------------------------------------------------------------------- #
# Mario
# --------------------------------------------------------------------------- #
MARIO_STRENGTH = {
    "Jumping ability": "Saut prodigieux",
    "Jumping ability, speed": "Saut et vitesse",
    "Agility, cartwheeling": "Agilité et roulades",
    "Low-level enemy": "Petit ennemi",
    "Magic, flight": "Magie et vol",
    "Shell, high defense": "Carapace et grande défense",
    "Speed, agility": "Vitesse et agilité",
    "Speed, digging": "Vitesse et creusage",
    "Strength, fire breath": "Force et souffle de feu",
    "Strength, flatulence": "Force (et quelques pets !)",
    "Strength, throwing barrels": "Force, lance des tonneaux",
    "Swallowing enemies, long tongue": "Gobe les ennemis, longue langue",
}
MARIO_NAME = {
    "rosalina": "Harmonie",
    "bowser jr": "Bowser Jr.",
    "shy Guy": "Maskass",
    "koopa troopa": "Koopa Troopa",
    "goomba": "Goomba",
    "toadette": "Toadette",
    "diddy kong": "Diddy Kong",
    "waluigi": "Waluigi",
}
MARIO_NAMES = [
    "mario",
    "luigi",
    "rosalina",
    "bowser",
    "bowser jr",
    "wario",
    "waluigi",
    "yoshi",
    "toad",
    "toadette",
    "donkey kong",
    "diddy kong",
    "koopa troopa",
    "goomba",
    "shy guy",
]
# Personnages clés absents de l'API communautaire, complétés avec l'art officiel.
MARIO_EXTRA = [
    {
        "name_fr": "Princesse Peach",
        "image": "https://mario.nintendo.com/static/43a96c1d5b681d338864aac15cd391b9/004f3/peach.png",
        "fact": "Apparue dans Super Mario Bros. (1985). Princesse du Royaume Champignon.",
    },
    {
        "name_fr": "Daisy",
        "image": "https://mario.nintendo.com/static/b625bdf51061d55b220d82eb9b61442c/9b369/daisy.png",
        "fact": "Apparue dans Super Mario Land (1989). Princesse de Sarasaland, pleine d'énergie.",
    },
    {
        "name_fr": "Boo",
        "image": "https://mario.nintendo.com/static/07969e5525c53ae6c17bd8c2661c459d/d4091/boo.png",
        "fact": "Apparu dans Super Mario Bros. 3 (1988). Un fantôme timide qui se cache quand on le regarde.",
    },
]
MARIO_LEGENDARY = ["Mario", "Luigi", "Peach", "Bowser", "Yoshi", "Donkey Kong"]


def build_mario() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    idx = 1
    seen = set()
    for n in MARIO_NAMES:
        try:
            d = _get("https://super-mario-bros-character-api.onrender.com/api/" + urllib.parse.quote(n))
        except Exception:  # noqa: BLE001
            d = None
        if not d or not d.get("name") or "unlisted" in d.get("name", "").lower():
            continue
        key = d["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        name_fr = MARIO_NAME.get(d["name"], d["name"])
        strength = MARIO_STRENGTH.get(d.get("strength"), d.get("strength") or "")
        fact = f"Apparu dans {d.get('origin')}."
        if strength:
            fact += f" Pouvoir : {strength}."
        img = _download(d.get("image"), "mario", idx)
        items.append({"id": idx, "name_fr": name_fr, "image_url": img, "fact": fact})
        idx += 1
    for extra in MARIO_EXTRA:
        img = _download(extra["image"], "mario", idx)
        items.append({"id": idx, "name_fr": extra["name_fr"], "image_url": img, "fact": extra["fact"]})
        idx += 1
    _assign_prices(items, MARIO_LEGENDARY)
    return items


BUILDERS = {
    "dragon_ball": build_dragon_ball,
    "harry_potter": build_harry_potter,
    "mario": build_mario,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="sous-ensemble de slugs séparés par des virgules")
    args = ap.parse_args()
    slugs = [s.strip() for s in args.only.split(",") if s.strip()] or list(BUILDERS)
    for slug in slugs:
        print(f"== {slug} ==")
        items = BUILDERS[slug]()
        missing = [it["id"] for it in items if not it["image_url"]]
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / f"{slug}.json").write_text(json.dumps(items, ensure_ascii=False, indent=2))
        print(f"  {len(items)} items écrits dans app/data/{slug}.json (images manquantes : {missing or 'aucune'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
