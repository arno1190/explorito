# Solfège CE1 / 1C1

Utilise ce guide quand le parent demande du solfège, une lecture de notes,
une lecture rythmique ou une dictée musicale. Lis aussi
[pack-author.md]({{API_BASE}}/api/v1/agent/pack-author.md) pour l'authentification,
le format du pack et son dépôt en brouillon.

## Préparer le parcours

La cible actuelle est **CE1 / 1C1**, première année du premier cycle musical.
Ce rapprochement avec CE1 est un choix Explorito ; l'âge d'entrée et les
attentes varient selon les écoles de musique. Garde level: "ce1",
subject_slug: "musique" et les tags solfege, 1c1, ce1.
La progression CE2 et les années suivantes restent à préparer.

Télécharge le [pack de départ]({{API_BASE}}/api/v1/agent/solfege-1c1.explorito).
Il contient huit leçons originales prêtes à adapter. Télécharger ce fichier
ne crée et ne publie rien. Envoie le JSON complet à l'endpoint de contribution
du guide principal pour créer le brouillon à relire par le parent.

Progression proposée :

| Étape | Objectif | Activités |
|---|---|---|
| 1 | Portée, lignes et interlignes ; pulsation régulière | Carte de cours courte, QCM, notes repères |
| 2 | Premières notes en clé de sol | music_note : nommer et placer ; music_sequence : lire |
| 3 | Ronde, blanche, noire et croche | music_rhythm : compter, écouter et comparer |
| 4 | Silences et mesures simples | Soupir, demi-pause, deux puis quatre temps ; compter les silences |
| 5 | Lecture rythmique | Frappes au tempo, petites formules avec deux croches |
| 6 | Premiers repères en clé de fa | Nommer puis lire de petites suites |
| 7 | Oreille et mémoire | Dictées de 2 à 4 notes préparées ; comparaison de rythmes |
| 8 | Réinvestissement | Lecture, écoute, rythmes et vocabulaire, avec explication après chaque réponse |

Commence avec do–ré–mi, puis ajoute sol et fa ; élargis aux sept noms
quand les repères sont acquis. Vise 60–80 pulsations par minute, 2 à 4 notes
par suite et un ou deux petits fragments rythmiques. La clé d'ut 3 reste
disponible pour un instrumentiste, mais le parcours de départ utilise sol/fa.
Les gammes altérées, rythmes pointés, triolets et mesures composées restent
hors de ce premier ensemble d'exercices.

Les cartes reading et les QCM permettent aussi d'aborder les nuances,
l'aigu et le grave, les reprises, les familles d'instruments et le chant.
Pour chanter, propose une consigne de pratique avec un adulte : l'application
ne corrige ni microphone ni justesse vocale. Une synthèse de notes à hauteur
fixe ne remplace pas une reconnaissance de timbres instrumentaux.

## Lecture de notes isolées : music_note

Reprends le contrat du guide principal : clef vaut sol, fa ou ut3,
mode vaut name ou place, pitch est naturel (C4, jamais C#4).
Bornes : sol A3–C6, fa C2–E4, ut3 B2–D5. La réponse
{"name": "ré"} doit correspondre au pitch. Le mode place accepte
chaque octave du bon nom ; il sert aux noms et repères, pas à une dictée
d'octave précise. Pour imposer une hauteur précise, préfère la lecture
d'une note affichée.

## Suites de notes : music_sequence

Chaque note dure une noire, soit un temps. Les noms se saisissent dans l'ordre
avec les boutons ; l'écoute synthétique respecte bpm (50–120, défaut 72).
Le mode read affiche la portée ; listen la cache jusqu'à la correction.
Prépare les hauteurs par lecture puis par écoute avant une dictée : aucun
diapason absolu n'est présupposé. Pour une première dictée, limite les choix
pédagogiques à des notes déjà entendues, en proposant une carte de préparation.

~~~json
{
  "type": "music_sequence",
  "question": "Lis les trois notes de gauche à droite.",
  "content": {"clef": "sol", "mode": "read", "pitches": ["C4", "D4", "E4"], "bpm": 72},
  "correct_answer": {"names": ["do", "ré", "mi"]},
  "difficulty_level": 2,
  "explanation": "Les notes montent : do, ré, mi."
}
~~~

Pour une dictée, remplace read par listen et adapte la question.
pitches contient 2 à 8 notes, toutes dans la portée de la clé choisie.
La correction vérifie tous les noms, dans l'ordre ; re est accepté pour ré.
Le clavier permet de corriger la dernière note avant validation.

## Lecture rythmique : music_rhythm

Une noire vaut toujours un temps. Les mesures sont à 2/4, 3/4 ou 4/4 ;
beats_per_bar vaut 2, 3 ou 4 (défaut 4). events contient 1 à 16
figures, pour au plus 16 temps au total. Une figure ne traverse jamais une
barre de mesure ; un fragment peut finir sur une mesure incomplète.
Chaque fragment contient au moins une note.

| Figure dans events | Durée |
|---|---|
| ronde | 4 temps |
| blanche | 2 temps |
| noire | 1 temps |
| croche | 0,5 temps |
| demi_pause | 2 temps de silence |
| soupir | 1 temps de silence |
| demi_soupir | 0,5 temps de silence |

### Compter : count

Le lecteur affiche les figures et propose des durées. Compte les silences.

~~~json
{
  "type": "music_rhythm",
  "question": "Combien de temps dure ce rythme, silence compris ?",
  "content": {"mode": "count", "events": ["noire", "soupir", "blanche"], "beats_per_bar": 4, "bpm": 72},
  "correct_answer": {"beats": 4},
  "difficulty_level": 2,
  "explanation": "Un temps de note, un temps de silence et deux temps de blanche : quatre temps."
}
~~~

### Reconnaître à l'oreille : listen

Le modèle sonore joue des notes de même hauteur et garde les silences.
L'enfant choisit entre 2 à 4 partitions, dont une seule reproduit exactement
events. Tous les choix ont la même durée ; leurs identifiants et leurs
figures sont distincts.

~~~json
{
  "type": "music_rhythm",
  "question": "Quelle partition correspond au rythme entendu ?",
  "content": {
    "mode": "listen",
    "events": ["croche", "croche", "noire"],
    "beats_per_bar": 2,
    "bpm": 72,
    "choices": [
      {"id": "a", "events": ["croche", "croche", "noire"]},
      {"id": "b", "events": ["noire", "croche", "croche"]}
    ]
  },
  "correct_answer": {"option_id": "a"},
  "difficulty_level": 3,
  "explanation": "Tu entends deux sons courts, puis un son plus long."
}
~~~

### Frapper : tap

L'enfant écoute, puis frappe sur le bouton ou avec le clavier, à la pulsation
indiquée. Sa première frappe sert de départ : aucun alignement avec une
horloge extérieure n'est demandé. Le serveur compare les instants suivants,
silences compris, au tempo du modèle ; la tolérance est au moins 180 ms
et sinon un quart de temps. Chaque frappe correspond au début d'une note.

~~~json
{
  "type": "music_rhythm",
  "question": "Frappe les deux noires avec un temps de silence entre elles.",
  "content": {"mode": "tap", "events": ["noire", "soupir", "noire"], "beats_per_bar": 4, "bpm": 72},
  "correct_answer": {},
  "difficulty_level": 3,
  "explanation": "Frappe, attends un temps de silence, puis frappe de nouveau."
}
~~~

Le fragment commence par une note et contient au moins deux attaques.
Le navigateur envoie {"taps": [0.0, 1.67]} (secondes) ; l'agent ne fournit
aucun instant attendu. Le serveur calcule tout depuis events et bpm.
La durée tenue de la dernière note et le silence final ne se mesurent pas
par les attaques : utilise count pour évaluer les durées.

## Vérifier avant le dépôt

Pour chaque exercice, refais les noms ou les durées depuis le contenu, puis
compare avec correct_answer. Vérifie les barres de mesure, la durée égale
des distracteurs et la présence d'une seule bonne réponse. Relis toutes les
questions comme des consignes à un enfant de CE1. Garde tier entre 1 et 3
et une difficulté fine croissante de 1 à 3 pour ce parcours débutant.
Dépose le fichier seulement après avoir vérifié l'ensemble.

Référence pédagogique consultée pour le périmètre (les exercices et la
progression ci-dessus sont propres à Explorito) :
[Conservatoire de la Creuse, programme de formation musicale, premier cycle](https://www.conservatoire-creuse.fr/IMG/pdf/programme_fm_cycle_i_ci_1_a_ci_4_mise_a_jour_2021_.pdf).
