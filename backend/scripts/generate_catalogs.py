"""
Génère les catalogues de collection « dinosaures » et « système solaire ».

Pour chaque objet d'une liste curée (nom FR + titre d'article Wikipédia FR), on
récupère via l'API REST de Wikipédia FR une **image réelle** (miniature) et une
**anecdote en français** (résumé). On écrit ``app/data/<slug>.json`` avec la
même forme que le Pokédex (id, name_fr, price, image_url, fact).

Images : Wikimedia Commons (licences libres). Réponses en français.

Usage:
    uv run python scripts/generate_catalogs.py
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
UA = "ExploritoEdu/1.0 (family learning app; contact maintainer@example.com)"

# (nom affiché en français, titre de l'article Wikipédia FR)
DINOSAURS: list[tuple[str, str]] = [
    ("Tyrannosaure", "Tyrannosaurus"),
    ("Tricératops", "Triceratops"),
    ("Vélociraptor", "Velociraptor"),
    ("Diplodocus", "Diplodocus"),
    ("Stégosaure", "Stegosaurus"),
    ("Brachiosaure", "Brachiosaurus"),
    ("Spinosaure", "Spinosaurus"),
    ("Ankylosaure", "Ankylosaurus"),
    ("Allosaure", "Allosaurus"),
    ("Iguanodon", "Iguanodon"),
    ("Parasaurolophus", "Parasaurolophus"),
    ("Ptéranodon", "Pteranodon"),
    ("Archéoptéryx", "Archaeopteryx"),
    ("Compsognathus", "Compsognathus"),
    ("Gallimimus", "Gallimimus"),
    ("Deinonychus", "Deinonychus"),
    ("Carnotaure", "Carnotaurus"),
    ("Dilophosaure", "Dilophosaurus"),
    ("Mosasaure", "Mosasaurus"),
    ("Plésiosaure", "Plesiosaurus"),
    ("Brontosaure", "Brontosaurus"),
    ("Apatosaure", "Apatosaurus"),
    ("Ptérodactyle", "Pterodactylus"),
    ("Cératosaure", "Ceratosaurus"),
    ("Baryonyx", "Baryonyx"),
    ("Giganotosaure", "Giganotosaurus"),
    ("Thérizinosaure", "Therizinosaurus"),
    ("Pachycéphalosaure", "Pachycephalosaurus"),
    ("Styracosaure", "Styracosaurus"),
    ("Oviraptor", "Oviraptor"),
    ("Microraptor", "Microraptor"),
    ("Utahraptor", "Utahraptor"),
    ("Corythosaure", "Corythosaurus"),
    ("Edmontosaure", "Edmontosaurus"),
    ("Elasmosaure", "Elasmosaurus"),
    ("Quetzalcoatlus", "Quetzalcoatlus"),
    ("Argentinosaure", "Argentinosaurus"),
    ("Protocératops", "Protoceratops"),
    ("Maiasaura", "Maiasaura"),
    ("Pachyrhinosaure", "Pachyrhinosaurus"),
]

SOLAR_SYSTEM: list[tuple[str, str]] = [
    ("Le Soleil", "Soleil"),
    ("Mercure", "Mercure (planète)"),
    ("Vénus", "Vénus (planète)"),
    ("La Terre", "Terre"),
    ("La Lune", "Lune"),
    ("Mars", "Mars (planète)"),
    ("Jupiter", "Jupiter (planète)"),
    ("Saturne", "Saturne (planète)"),
    ("Uranus", "Uranus (planète)"),
    ("Neptune", "Neptune (planète)"),
    ("Pluton", "Pluton (planète naine)"),
    ("Cérès", "Cérès (planète naine)"),
    ("Io", "Io (lune)"),
    ("Europe", "Europe (lune)"),
    ("Ganymède", "Ganymède (lune)"),
    ("Titan", "Titan (lune)"),
    ("La comète de Halley", "Comète de Halley"),
]


def price_at(i: int, n: int, pmin: int = 20, pmax: int = 200, exp: float = 1.6) -> int:
    """Prix sur une courbe adoucie (moins cher au début), arrondi à 5."""
    t = 0.0 if n <= 1 else i / (n - 1)
    return int(round((pmin + (pmax - pmin) * (t**exp)) / 5) * 5)


def _first_sentences(text: str, limit: int = 220) -> str:
    """Tronque proprement une anecdote (fin de phrase si possible)."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    return (cut[: dot + 1] if dot > 60 else cut).rstrip() + "…"


def fetch_summary(title: str) -> dict[str, Any] | None:
    """Récupère le résumé Wikipédia FR (image + extrait) d'un article."""
    url = "https://fr.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (URL de confiance)
        return json.loads(resp.read().decode("utf-8"))


def build(slug: str, items: list[tuple[str, str]]) -> None:
    entries: list[dict[str, Any]] = []
    n = len(items)
    for i, (name_fr, title) in enumerate(items):
        try:
            data = fetch_summary(title)
        except Exception as exc:  # noqa: BLE001 (script best-effort)
            print(f"  ! {name_fr} ({title}) : échec ({exc}) — ignoré")
            continue
        thumb = (data or {}).get("thumbnail", {}).get("source")
        if not thumb:
            print(f"  ! {name_fr} : pas d'image — ignoré")
            continue
        entries.append(
            {
                "id": len(entries) + 1,
                "name_fr": name_fr,
                "price": price_at(i, n),
                "image_url": thumb,
                "fact": _first_sentences((data or {}).get("extract", "")),
            }
        )
        print(f"  ✓ {name_fr}  ({entries[-1]['price']} XP)")
        time.sleep(0.1)  # courtoisie envers l'API

    out = DATA_DIR / f"{slug}.json"
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prices = [e["price"] for e in entries]
    print(f"→ {out.name} : {len(entries)} objets, prix {min(prices)}–{max(prices)} XP\n")


def main() -> int:
    print("Dinosaures :")
    build("dinosaurs", DINOSAURS)
    print("Système solaire :")
    build("solar_system", SOLAR_SYSTEM)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
