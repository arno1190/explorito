# Rubrique par niveau — bornes de contenu, `ps` → `cm2`

Référence unique et publique des bornes de contenu par niveau scolaire, servie
par Explorito à `/api/v1/agent/rubric.md`. Elle est partagée par la rédaction
d'un pack et par sa relecture en modération. Une seule section est utile par
pack : lis **celle du niveau cible**, et recopie ses bornes avant de générer.

Chaque section est calée sur le contenu réellement présent dans Explorito, pas
sur une lecture du programme officiel : les bornes sont relevées sur les leçons
déjà publiées du niveau. En cas de doute sur une borne, imite les leçons
existantes de ce niveau dans l'application plutôt que d'extrapoler.

**Le piège que cette rubrique existe pour éviter** : sans bornes explicites, un
modèle écrit du contenu CM1 et l'étiquette `cp`. Un enfant de CP à qui l'on
demande `7 × 8` n'apprend rien, il décroche.

## Règles transverses (tous niveaux)

| Règle | Borne |
|---|---|
| Langue | Français uniquement, y compris les titres, les options et les explications. Un pack non francophone est **rejeté** par le validateur. |
| Longueur d'un énoncé | ≤ 2 000 caractères par champ (borne serveur), mais viser la borne « phrase » du niveau. |
| Réponse non entière | `math_problem` avec un résultat décimal **exige** `correct_answer.tolerance` (0.01 pour les centièmes). Sinon la bonne réponse devient inatteignable. |
| Unités | Un résultat en euros, cm, min → `content.unit`. Jamais l'unité dans la valeur. |
| Emoji | 1 emoji par exercice au plus (`media_urls.emoji`), toujours en rapport avec l'énoncé. |
| Prénoms | Uniquement des prénoms génériques déjà utilisés par le contenu existant (Léa, Tom, Zoé). Jamais le prénom d'un enfant réel — voir la règle « aucune donnée personnelle » du guide de rédaction. |

Budget de caractères par énoncé, au-delà duquel le serveur pose un
avertissement `text_too_long_for_level` :

| `ps` | `ms` | `gs` | `cp` | `ce1` | `ce2` | `cm1` | `cm2` |
|---|---|---|---|---|---|---|---|
| 60 | 60 | 80 | 120 | 180 | 240 | 320 | 400 |

## `ps` — Petite section (~3 ans, **non-lecteur**)

Calé sur les leçons de maternelle `ps` d'Explorito (dénombrement, couleurs, formes).

- **Nombres** : quantités 1 à 3, reconnues d'un coup d'œil. Aucun calcul.
- **Français** : nommer des objets familiers (animaux, fruits, parties du corps, vêtements). Aucune lettre, aucun son.
- **Autres** : couleurs de base (rouge, bleu, jaune, vert), formes rond / carré / triangle.
- **Consigne** : impérative, ≤ 6 mots, forme « Appuie sur le chat. » Elle est lue par l'adulte.
- **Types autorisés** : `multiple_choice` **uniquement**, 3 options, chacune portant un emoji ou une pastille de couleur (`content.options[].color`). L'enfant ne lit pas : l'option doit être identifiable sans texte.
- **Interdits** : `math_problem` (saisie au clavier), `fill_blanks`, `reading`, `soroban`, `pythagore`.
- **`difficulty_level`** : 1.

## `ms` — Moyenne section (~4 ans, **non-lecteur**)

Calé sur les leçons de maternelle `ms` d'Explorito.

- **Nombres** : quantités 1 à 5.
- **Français** : vocabulaire du quotidien élargi (vêtements, aliments, animaux).
- **Consigne** : ≤ 8 mots.
- **Types autorisés** : `multiple_choice` uniquement, options visuelles. Mêmes interdits que `ps`.
- **`difficulty_level`** : 1, exceptionnellement 2 sur la dernière leçon du pack.

## `gs` — Grande section (~5 ans, lecteur débutant)

Calé sur les leçons de maternelle `gs` d'Explorito : « Compter jusqu'à 10 », « Le son du début », « Les syllabes », « Les contraires », « Le temps qu'il fait ».

- **Nombres** : quantités 1 à 10, comparer « plus / moins ».
- **Français oral** : premier son d'un mot, compter les syllabes, contraires (grand/petit, chaud/froid).
- **Autres** : météo et saisons, formes.
- **Consigne** : ≤ 10 mots, un seul verbe.
- **Types autorisés** : `multiple_choice`. `reveal` accepté comme carte de récompense. Toujours pas de texte à lire, pas de `math_problem`.
- **`difficulty_level`** : 1 à 2.

## `cp` — Cours préparatoire (~6 ans, apprend à lire)

Calé sur les leçons `cp` de maths et de français d'Explorito.

- **Nombres** : 0 à 100. Dizaines et unités (« 2 dizaines et 5 unités »), avant/après, suites de 2 en 2, comparer avec `<`, `>`, `=`.
- **Opérations** : addition et soustraction **jusqu'à 20** ; addition de dizaines rondes jusqu'à 100 (`20 + 30`) ; compléments à 10 ; doubles et moitiés jusqu'à 20.
- **Interdit en maths** : la **multiplication** et la **division** comme opérations. « 3 paquets de 10 » est admis comme dénombrement, `3 × 4` ne l'est pas.
- **Mesures** : euros entiers ≤ 20, heures pile, comparaison de longueurs sans unité chiffrée, formes planes, gauche/droite.
- **Français** : voyelles ; sons simples puis complexes (`ou`, `ch`, `on`, `an`, `oi`, `in`) ; syllabes consonne+voyelle ; mots-outils fréquents (le, la, un, et, est) ; majuscule et point ; ordre alphabétique.
- **Phrase** : ≤ 10 mots par énoncé, présent de l'indicatif, vocabulaire concret du quotidien.
- **Bloc `reading`** : 2 à 3 phrases, **≤ 30 mots au total**. Repère réel du contenu existant : « Le chat de Léa est noir. Il dort sur le lit. Léa aime beaucoup son chat. » (17 mots).
- **Types autorisés** : `multiple_choice`, `math_problem` (résultat entier), `fill_blanks` (**un seul** `___`, un mot court), `reading` suivi de 2–3 questions, `reveal`, `soroban` (lire un nombre ≤ 100).
- **`difficulty_level`** : 1 à 3.

## `ce1` — Cours élémentaire 1 (~7 ans)

Calé sur les leçons `ce1` d'Explorito, y compris les séries « avancé » et « défis ».

- **Nombres** : 0 à 100 (le contenu existant ne dépasse pas 100). Pair/impair jusqu'à 50, suites de 2 en 2 et de 5 en 5, comparer, avant/après.
- **Opérations** : addition et soustraction jusqu'à 100 **avec retenue / emprunt** ; compléments à 100 ; addition de trois nombres ≤ 15 ; doubles et moitiés jusqu'à 24.
- **Multiplication** : tables de **2, 3, 5 et 10 seulement**. Les tables de 6 à 9 sont hors niveau. Problèmes multiplicatifs de la forme `a × b` avec `a ≤ 5` et `b ≤ 10`.
- **Interdit** : division posée, nombres décimaux, fractions.
- **Mesures** : euros entiers ≤ 60.
- **Français** : son `[s]` (s, ss, c, ç), son `[ch]`, accents, pluriel des noms (-s, -x, chevaux/journaux), féminin des noms, synonymes et contraires, passé / présent / futur reconnus dans une phrase, homophones `son`/`sont`, majuscule après le point.
- **Phrase** : ≤ 14 mots par énoncé.
- **Bloc `reading`** : 3 à 5 phrases, **35 à 55 mots**. Repère réel : la lecture « La ferme » fait 40 mots.
- **Types autorisés** : tous, plus `pythagore` (une seule table par exercice).
- **`difficulty_level`** : 1 à 3.

## `ce2` — Cours élémentaire 2 (~8 ans)

Calé sur les leçons `ce2` de maths et de français d'Explorito.

- **Nombres** : jusqu'à **10 000**, lire, écrire, décomposer, comparer, ranger.
- **Opérations** : addition et soustraction **posées** à 3 chiffres avec retenues (`247 + 158`, `523 - 187`) ; tables de **2 à 9** ; multiplication posée par un chiffre (`24 × 3`) ; division-partage à quotient exact (`24 ÷ 4`) ; double et moitié.
- **Interdit** : fractions, nombres décimaux, multiplication à deux chiffres, division avec reste.
- **Mesures** : longueurs m / cm / km, masses kg / g, contenances L / cL, heures **et minutes**, euros **et centimes**, carré / rectangle / triangle et angle droit.
- **Français** : nom commun et nom propre, verbe et infinitif, adjectif, déterminant, sujet du verbe, futur simple, imparfait, passé composé avec *avoir*, types de phrases, ponctuation, synonymes et contraires, familles de mots (préfixe, suffixe), féminin, ordre alphabétique et dictionnaire.
- **Phrase** : ≤ 18 mots par énoncé.
- **Bloc `reading`** : **60 à 90 mots**, un récit avec un début et une fin. Repère réel : « le petit renard » fait 71 mots.
- **`difficulty_level`** : 2 à 4.

## `cm1` — Cours moyen 1 (~9 ans)

Calé sur les leçons `cm1` de maths, de français et d'orthographe d'Explorito.

- **Nombres** : jusqu'à **1 000 000** ; multiples ; nombres décimaux aux dixièmes et centièmes (`3,7`).
- **Opérations** : toutes les tables ; `× 10`, `× 100`, `× 1000` ; multiplication posée par un nombre à **deux** chiffres (`34 × 26`) ; division posée avec **quotient et reste** (`47 ÷ 5`) ; fraction d'une quantité (`3/4 de 20`) ; comparer et ranger des fractions ; problèmes à plusieurs étapes.
- **Mesures** : périmètre et aire du carré et du rectangle, durées h / min / s.
- **Français** : trois groupes de verbes ; présent, imparfait, futur, passé composé (accord du participe), passé simple à la 3ᵉ personne ; nature *vs* fonction d'un mot ; COD et COI ; adverbes ; sens propre et figuré ; synonymes, antonymes, homonymes ; préfixes et suffixes.
- **Orthographe** : accord sujet-verbe avec sujet inversé ou éloigné ; participe passé avec *être* et avec *avoir* ; pluriels en -s, -x, -aux et noms composés ; `m` devant `m`, `b`, `p` ; sons `[s]`, `[g]`, `[j]` ; consonnes doubles ; homophones `a/à/as`, `et/est/es`, `son/sont`, `on/ont`, `ces/ses/c'est/s'est`, `la/là/l'a`, `ou/où`.
- **Phrase** : ≤ 22 mots par énoncé.
- **Bloc `reading`** : **90 à 150 mots**, avec de l'imparfait et du passé simple. Repère réel : « La cité engloutie » fait 118 mots.
- **`difficulty_level`** : 2 à 5.

## `cm2` — Cours moyen 2 (~10 ans)

Calé sur les leçons `cm2` de maths et de culture générale d'Explorito.

- **Nombres** : décimaux additionnés et soustraits (`5,7 − 2,4`, avec `tolerance: 0.01`) ; pourcentages simples (10 %, 20 %, 25 %, 50 % d'une quantité).
- **Opérations** : problèmes à plusieurs étapes mêlant `×` et `+` (« 3 cahiers à 4 € et 1 stylo à 3 € ») ; vitesse (`450 km en 5 h`) ; prix unitaire non entier (`9 € ÷ 6`, donc `tolerance`).
- **Français** : futur simple, homophones `ses/ces` et `ce/se`, compréhension d'un récit.
- **Culture** : Révolution française, énergie et électricité, continents et océans.
- **Phrase** : ≤ 25 mots par énoncé.
- **Bloc `reading`** : **120 à 200 mots**.
- **`difficulty_level`** : 3 à 5.
