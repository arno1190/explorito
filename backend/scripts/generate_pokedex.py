"""
Génère ``app/data/pokedex.json`` depuis PokéAPI (one-time / rejouable).

Pour chaque Pokémon (IDs 1..251) :
- nom français via ``pokemon-species/{id}`` (names[] langue "fr")
- BST (somme des stats) + artwork officiel via ``pokemon/{id}``
- prix en XP via une courbe adoucie (la plupart bon marché, seuls les plus
  forts approchent ~200).

Usage:
    uv run python scripts/generate_pokedex.py
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

MAX_ID = 251
API = "https://pokeapi.co/api/v2"
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "pokedex.json"

# Courbe de prix adoucie : price = PRICE_MIN + (PRICE_MAX-PRICE_MIN) * t**EXP
# où t = (bst - BST_MIN) / (BST_MAX - BST_MIN), borné à [0, 1].
BST_MIN, BST_MAX = 180, 680
PRICE_MIN, PRICE_MAX = 10, 200
EXP = 2.2


def price_from_bst(bst: int) -> int:
    """Convertit un BST en prix XP (courbe adoucie, arrondi à 5)."""
    t = (bst - BST_MIN) / (BST_MAX - BST_MIN)
    t = max(0.0, min(1.0, t))
    raw = PRICE_MIN + (PRICE_MAX - PRICE_MIN) * (t**EXP)
    return max(PRICE_MIN, round(raw / 5) * 5)


def fetch_one(client: httpx.Client, pid: int) -> dict:
    species = client.get(f"{API}/pokemon-species/{pid}").raise_for_status().json()
    name_fr = next(
        (n["name"] for n in species["names"] if n["language"]["name"] == "fr"),
        species["name"],
    )
    poke = client.get(f"{API}/pokemon/{pid}").raise_for_status().json()
    bst = sum(s["base_stat"] for s in poke["stats"])
    image_url = poke["sprites"]["other"]["official-artwork"]["front_default"]
    return {
        "id": pid,
        "name_fr": name_fr,
        "bst": bst,
        "price": price_from_bst(bst),
        "image_url": image_url,
    }


def main() -> int:
    with httpx.Client(timeout=30) as client:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda pid: fetch_one(client, pid), range(1, MAX_ID + 1)))
    results.sort(key=lambda r: r["id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    prices = [r["price"] for r in results]
    print(f"Écrit {len(results)} Pokémon -> {OUT}")
    print(f"Prix min/median/max: {min(prices)} / {sorted(prices)[len(prices) // 2]} / {max(prices)}")
    print("Exemples:", ", ".join(f"#{r['id']} {r['name_fr']} ({r['price']}XP)" for r in results[:4]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
