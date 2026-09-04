# Explorito — rédiger un pack de leçons

Explorito est une application éducative pour enfants, calée sur le programme
scolaire français de la petite section au CM2 (`ps ms gs cp ce1 ce2 cm1 cm2`).
Ce document est ta procédure complète : tu vas rédiger un **pack de leçons** et
le déposer en **brouillon** sur le compte d'un parent, à partir d'un thème, d'un
niveau et du code de connexion à 8 caractères que ce parent t'a donné.

Tu n'as besoin de rien d'autre que ce document. Il est autoportant : tout ce qui
te manque (bornes du niveau, format de fichier, adresses d'API) est décrit ici ou
téléchargeable depuis les adresses indiquées.

Un **pack** est l'unité d'auteur, de thème et de publication : plusieurs leçons
qui tiennent ensemble (« Les volcans », « Les additions du T-Rex »), avec une
progression interne. Ce que tu produis est un fichier `.explorito` (du JSON) que
tu envoies au compte du parent. L'enfant du parent y a accès immédiatement ; la
communauté ne le voit qu'après relecture humaine.

Explorito n'appelle jamais de modèle de langage : **tu es le seul générateur de
contenu**, et le serveur ne peut vérifier que la forme. Un calcul faux, un fait
inventé ou un niveau mal calibré passera la validation. La relecture de l'étape 4
n'est pas une formalité, c'est le seul filet.

## Aucune donnée personnelle — règle absolue

Un pack peut finir publié à des inconnus. Écris donc du contenu **anonyme par
construction** :

- Des prénoms génériques et uniquement eux : Léa, Tom, Zoé, Nina, Sami.
- Des lieux publics et génériques : « la forêt », « le marché », « la mer ».
- Des situations universelles : l'école, le jardin, les animaux, les vacances « à
  la montagne ».

L'incident réaliste n'est pas malveillant, c'est un parent enthousiaste qui
demande « un pack sur les vacances d'Arthur à Biarritz » : le prénom réel de son
enfant et la ville où il passe l'été, publiés à des étrangers. **Si le thème
demandé contient un prénom, une école, une ville, une date de naissance, un
club ou une photo de la famille, remplace-les par des équivalents génériques et
dis-le au parent en une phrase.** Le thème reste le même (les vacances à la mer
sont un excellent thème), seules les données identifiantes disparaissent.

Cette règle s'applique aussi au **titre, à la description et aux tags** du pack :
ils s'affichent aux enfants avant toute activation.

## 0. S'authentifier avec le code de connexion

Le parent t'a lu un code de 8 caractères du type `Q97E-89JJ`, obtenu dans
Explorito par « Mes leçons » → carte « Connecter mon assistant » → bouton
« Afficher mon code ». Échange-le une fois contre un jeton d'envoi :

```bash
curl -sS -X POST "{{API_BASE}}/api/v1/contributions/pairing/claim" \
  -H "Content-Type: application/json" -d '{"code": "Q97E-89JJ"}'
```

Réponse :

```json
{"token": "…", "prefix": "…", "handle": "PapaRenard",
 "terms_accepted": true, "terms_version": "…", "app_url": "{{APP_URL}}"}
```

Écris-la immédiatement, le jeton ne se réaffiche jamais :

```bash
mkdir -p ~/.explorito
cat > ~/.explorito/credentials.json <<'JSON'
{"url": "{{API_BASE}}", "token": "<token reçu>", "handle": "PapaRenard"}
JSON
chmod 600 ~/.explorito/credentials.json
```

Si ce fichier existe déjà et porte un `token`, **n'utilise pas le code** : tu es
déjà connecté, ne parle pas d'identifiants et enchaîne sur le pack. C'est l'état
normal des sessions suivantes, et il doit être silencieux.

Après un premier échange réussi, dis trois choses au parent, une phrase chacune :
ce fichier contient un **secret** et reste sur cette machine ; ce jeton ne sait
créer que des **brouillons** sur son compte ; il se **révoque** depuis « Mes
leçons », bouton « Révoquer » dans la liste dépliée par « Je préfère gérer un
jeton moi-même ».

**Le code est à usage unique et vaut 15 minutes.** Son alphabet exclut tous les
caractères ambigus — ni `O` ni `0`, ni `I` ni `1` ni `L`, ni `U` ni `V` : si le
parent t'en dicte un, c'est une erreur de lecture, fais-lui relire le caractère
plutôt que de deviner. Casse, espaces et tirets sont sans importance.
`404 {"detail": {"code": "pairing_invalid"}}` veut dire expiré, déjà utilisé ou
mal noté — demande un code frais, ne rejoue jamais le même.

**Les conditions de contribution s'acceptent dans le navigateur, jamais par
toi.** Si la réponse porte `"terms_accepted": false`, demande au parent de les
accepter sur « Mes leçons » ; sans ça l'envoi de l'étape 5 repartira en `428`.

### Si tu n'as pas de shell

Sans exécution de commandes (chat web sans outil réseau), tu ne peux pas échanger
le code ni envoyer le pack — dis-le franchement au parent au lieu d'essayer. Le
code ne sert alors à rien : **rédige quand même le pack en entier**, rends le
JSON complet dans un fichier nommé `<theme>.explorito`, et donne cette consigne
au parent :

> Enregistre ce contenu dans un fichier `volcans.explorito`, puis dans Explorito
> va sur « Mes leçons » → « Déposer un pack » et dépose ce fichier.

Le dépôt manuel produit exactement le même brouillon que l'envoi par API. Un code
non utilisé expire tout seul au bout de 15 minutes, sans dommage.

## 1. Cadrer (ne demande que ce qui manque)

- **Thème** — libre (« les dinosaures », « les additions jusqu'à 20 »).
- **Niveau** — un seul parmi `ps ms gs cp ce1 ce2 cm1 cm2`. Un pack peut mélanger
  les niveaux, mais un pack mono-niveau est plus facile à activer pour un enfant.
- **Matière(s)** — un slug par leçon : `maths`, `francais`, `orthographe`,
  `histoire`, `geo`, `monde`, `arts`, `logique`. Un slug inconnu est un refus dur.

Si le parent a donné un thème et un niveau, tu as tout : ne pose aucune autre
question, choisis les matières toi-même d'après le thème.

## 2. Lire la rubrique du niveau

La rubrique des bornes par niveau n'est **pas** recopiée ici, elle vit à une seule
adresse pour ne jamais diverger. Télécharge-la et lis **la section du niveau
cible** :

```bash
curl -sS "{{API_BASE}}/api/v1/agent/rubric.md"
```

Puis **écris noir sur blanc les bornes retenues** (plage de nombres, opérations
permises, longueur de phrase, types d'exercices autorisés) avant de générer quoi
que ce soit.

C'est l'étape la plus rentable du processus. Sans elle, le contenu produit dérive
d'un à deux niveaux vers le haut : un pack étiqueté `cp` qui demande `7 × 8` est
inutilisable, et c'est l'erreur par défaut, pas un cas rare.

## 3. Rédiger le pack

Structure obligatoire :

- **3 à 6 leçons** (maximum serveur : 12). Une leçon unique déclenche un
  avertissement : il n'y a rien à débloquer.
- **Une vraie courbe** via `tier` : `1` Découverte (reconnaître, avec l'aide de
  l'énoncé), `2` Entraînement (appliquer seul), `3` Défi (transférer, problème à
  plusieurs étapes). Un pack de 4 leçons typique : tiers 1, 1, 2, 3. Le verrou de
  progression joue **à l'intérieur du pack** : l'enfant doit finir les tiers
  inférieurs pour ouvrir le suivant, donc l'ordre est réellement vécu.
- **4 à 6 exercices par leçon** (maximum serveur : 20), d'au moins **deux types
  différents** — 15 QCM identiques sont un avertissement et coûtent des points de
  qualité.
- **`difficulty_level` sur CHAQUE exercice**, de 1 (très facile pour ce niveau) à
  5 (très difficile pour ce niveau). Absent ⇒ **refus dur**. Ces valeurs sont
  relatives au niveau scolaire, pas à l'âge : un exercice `cp` en difficulté 5
  reste un exercice de CP.
- **L'XP est calculée par le serveur** depuis les `difficulty_level`. Déclarer
  `xp_reward` ne fait rien du tout, à part un avertissement : ne l'écris pas.

Deux motifs pédagogiques déjà en place dans Explorito, à réutiliser :

- **Lecture puis compréhension, dans la même leçon** : un exercice `reading` en
  premier, puis 2 ou 3 `multiple_choice` / `fill_blanks` qui portent sur ce
  texte. C'est la forme de toutes les leçons de lecture et d'histoire existantes.
- **Carte `reveal` en récompense** : une devinette ou une blague sur le thème,
  placée en dernier dans une leçon d'entraînement. Sans bonne réponse, elle
  ponctue l'effort.

### Format `.explorito`

```json
{
  "format_version": 1,
  "pack": {
    "title": "Les volcans 🌋",
    "emoji": "🌋",
    "description": "Comprendre comment naît une éruption.",
    "tags": ["sciences", "volcans"]
  },
  "lessons": [
    {
      "subject_slug": "monde",
      "level": "ce2",
      "tier": 1,
      "name": "Qu'est-ce qu'un volcan ? 🌋",
      "description": "Découvrir le cratère, le magma et la lave.",
      "exercises": [ /* formes ci-dessous */ ]
    }
  ],
  "self_check": {"math_verified": true, "facts_checked": true, "no_personal_data": true, "notes": "…"}
}
```

`tier` vaut 1, 2 ou 3 — pas davantage. `tags` : 8 au maximum. Le fichier entier
doit rester sous 512 kio, et chaque champ texte sous 2 000 caractères.

### Formes d'exercices

Un exercice = `type`, `question` (la consigne lue par l'enfant), `content`,
`correct_answer`, `difficulty_level`, plus les optionnels `explanation`,
`media_urls` (`{"emoji": "🌋"}`) et `order_index` (l'ordre du tableau suffit).

| `type` | `content` | `correct_answer` |
|---|---|---|
| `multiple_choice` | `{"options": [{"id": "1", "text": "lave", "color": "#e11d48"}, …], "multiple": false}` | `{"option_ids": ["1"]}` — exactement un `id` si `multiple` est faux |
| `fill_blanks` | `{"text": "Le c___ du volcan"}` (marqueurs `___`) | `{"blanks": ["ratère"]}` — un mot par marqueur, dans l'ordre |
| `math_problem` | `{"unit": "€"}` (facultatif) — l'énoncé est dans `question` | `{"value": 12, "tolerance": 0}` |
| `reading` | `{"text": "…le passage…", "image": "url"}` | `{}` |
| `reveal` | `{"prompt": "Pourquoi…", "reveal": "Parce que…"}` | `{}` |
| `soroban` | `{"mode": "read", "value": 42, "columns": 3}` | `{"value": 42}` — doit égaler `content.value` |
| `pythagore` | `{"tables": [3], "blanks": 5}` | `{}` |

`color` sur une option sert aux non-lecteurs (maternelle) : une pastille de
couleur au lieu d'un mot.

## 4. Relire le pack (passe obligatoire)

Reprends le pack **entier**, de haut en bas, et coche chaque point. Cette passe
attrape des erreurs que rien d'autre n'attrapera :

1. **Recalcule chaque `math_problem`** un par un, en posant l'opération, et
   compare au `correct_answer.value` écrit. C'est la première source d'erreur, et
   le serveur ne peut pas la voir. Résultat décimal ⇒ `tolerance: 0.01`.
2. **QCM** : la bonne option est bien celle que `option_ids` désigne ; les
   distracteurs sont plausibles mais faux ; aucune option n'est vraie « aussi ».
3. **`fill_blanks`** : autant de `___` que de `blanks`, et la réponse attendue
   est la seule graphie acceptable.
4. **Faits** : chaque affirmation d'histoire, de géographie ou de sciences est
   grand public et vérifiable. Dans le doute, supprime l'exercice.
5. **Niveau** : chaque énoncé tient dans les bornes de la rubrique relues à
   l'étape 2 (nombres, opérations, longueur de phrase).
6. **Courbe** : les `difficulty_level` montent à travers le pack ; deux types
   d'exercices au moins ; `difficulty_level` présent partout.
7. **Français** : orthographe et accords corrects, ton bienveillant, aucune
   moquerie, aucune peur.
8. **Données personnelles** : aucun prénom réel, aucune ville de résidence,
   aucune école, aucune date de naissance — titre, description et tags compris.
   Le titre et la description du pack sont visibles par les enfants **avant**
   toute activation.

Puis écris le bloc `self_check` en fin de fichier : `math_verified`,
`facts_checked`, `no_personal_data` et un `notes` d'une phrase disant ce que tu
as effectivement recalculé. Le serveur ne bloque pas sur son absence — il te
laisse volontairement libre de mentir, ce qui n'a aucun intérêt : ce bloc est là
pour te forcer à faire la passe, et il est relu par un humain à la modération.

## 5. Envoyer (brouillon)

Écris le pack dans un fichier `*.explorito`, puis envoie-le avec le jeton du
fichier d'identifiants :

```bash
URL=$(jq -r .url ~/.explorito/credentials.json)
TOKEN=$(jq -r .token ~/.explorito/credentials.json)
curl -sS -X POST "$URL/api/v1/contributions" \
  -H "X-Upload-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @volcans.explorito
```

Rien d'autre à passer : le pseudonyme public et les conditions de contribution
sont réglés dans l'application avant le premier envoi. Un `428 terms_required`
veut dire que le parent doit les accepter — première fois, ou nouvelle version
publiée depuis son dernier envoi — et la réparation est un clic de sa part sur
« Mes leçons », jamais un paramètre d'URL : l'endpoint d'envoi n'accepte plus
rien en ligne. Attends son feu vert, puis renvoie le même fichier.

Réponse `201` :

```json
{"pack_id": "…", "preview_url": "{{APP_URL}}/contributions/…",
 "community_status": "draft", "quality_score": 85, "warnings": [], "flags": []}
```

Le jeton d'envoi ne peut créer que des **brouillons**. Proposer le pack à la
communauté est un geste que le parent fait lui-même depuis l'aperçu : n'essaie
jamais de publier.

## 6. Corriger un refus

Le validateur est ta boucle de rétroaction : ses messages nomment la leçon,
l'exercice et le champ fautifs.

| Code HTTP | Corps | Que faire |
|---|---|---|
| `422` | `{"detail": {"code": "pack_invalid", "issues": [{"severity": "error", "code": "difficulty_level_missing", "message": "…", "lesson_index": 0, "exercise_index": 2, "field": "difficulty_level"}]}}` | Lis chaque `issue`, corrige exactement ce qu'elle nomme (`lesson_index` et `exercise_index` sont des index de tableau, base 0), renvoie. |
| `428` | `{"detail": {"code": "terms_required", "terms_version": "…", "terms": "…"}}` | Le parent accepte sur « Mes leçons » : la modale s'ouvre d'elle-même, et le bandeau « Cette page est inactive » la rouvre autrement. Une nouvelle `terms_version` reverrouille la page pour un parent déjà contributeur — même remède. Puis renvoie le pack tel quel. N'accepte jamais à sa place. |
| `429` | `{"detail": {"code": "quota_exceeded", …}}` | Quota d'envois du jour atteint : garde le fichier, réessaie demain. |
| `413` | — | Fichier trop gros : réduis le nombre de leçons ou la longueur des textes. |

Les `warnings` et les `flags` ne bloquent rien : ils baissent le score de
qualité. Si le score revient bas, la cause est presque toujours l'une de ces
trois-là — courbe de difficulté plate, un seul type d'exercice, `self_check`
absent. Corrige-les et renvoie : c'est un pack nettement meilleur pour l'enfant.

## 7. Ce que tu rends au parent

Trois choses, en quelques lignes, sans recopier le JSON :

1. **Le `preview_url`** renvoyé par l'envoi — c'est le lien à ouvrir pour voir le
   pack, l'activer pour son enfant, ou le proposer à la communauté.
2. **Le `quality_score`** (0–100), avec une phrase sur ce qui le retient s'il est
   bas.
3. **Les `warnings` et les `flags`** s'il y en a, cités tels quels et traduits en
   une phrase chacun.

Ajoute, si c'est le cas, la phrase sur les données personnelles génériques que tu
as substituées. Rien d'autre : le pack est un brouillon sur son compte, la suite
lui appartient.
