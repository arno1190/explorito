#!/bin/bash
set -euo pipefail

# Coûts d'infra Explorito, lus sur le compte Scaleway PERSONNEL.
# Usage: ./scripts/infra-costs.sh
#
# Le profil est figé à `personal` : le profil par défaut de cette machine est
# un compte professionnel, qu'il ne faut jamais interroger ni facturer ici.
# Lecture seule — aucune ressource n'est créée ni modifiée.

SCW="scw --profile ${SCW_PROFILE:-personal}"

echo "=== Mois en cours (HT, consommation à date) ==="
$SCW billing consumption list -o json | python3 -c '
import json, sys
rows = json.load(sys.stdin)
by_cat = {}
for r in rows:
    v = r["value"]
    eur = int(v.get("units", 0)) + v.get("nanos", 0) / 1e9
    key = (r["category_name"], r["product_name"])
    by_cat[key] = by_cat.get(key, 0) + eur
for (cat, prod), eur in sorted(by_cat.items(), key=lambda kv: -kv[1]):
    print(f"  {eur:7.2f} €  {cat:18} {prod}")
print(f"  {sum(by_cat.values()):7.2f} €  TOTAL")
'

echo
echo "=== Factures des 6 derniers mois (TTC) ==="
$SCW billing invoice list -o json | python3 -c '
import json, sys
for inv in json.load(sys.stdin)[:6]:
    t = inv.get("total_taxed", {})
    eur = int(t.get("units", 0)) + t.get("nanos", 0) / 1e9
    month, state = inv.get("start_date", "")[:7], inv.get("state", "")
    print(f"  {month}  {eur:7.2f} €  {state}")
'

echo
echo "=== Ressources qui facturent ==="
$SCW instance server list zone=all -o human
$SCW rdb instance list region=all -o human
