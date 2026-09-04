<!-- URL publique canonique : {PUBLIC_APP_URL}/tutoriel/lecons-communautaires
     C'est l'adresse envoyée par l'e-mail d'annonce (backend/scripts/announcements/
     community_lessons.md), et un lien parti par e-mail ne se corrige plus : la
     route front doit servir CE fichier sous ce chemin. -->

# Créer vos propres leçons Explorito

Vous pouvez fabriquer des leçons sur mesure pour votre enfant — ses dinosaures, sa
passion pour les volcans, les additions qui coincent — et les partager avec les
autres familles si vous le souhaitez.

Explorito ne génère rien tout seul : **c'est votre assistant IA qui écrit les
leçons**, et vous les envoyez ensuite à Explorito. Comptez dix minutes la
première fois, deux minutes les suivantes.

## Ce qui se passe après l'envoi

| Étape | Qui le voit |
|---|---|
| Vous envoyez le pack | Il arrive en **brouillon** sur votre compte. |
| Vous l'activez pour votre enfant | Votre enfant, **immédiatement**. Pas d'attente, pas de validation. |
| Vous le proposez à la communauté (facultatif) | Il passe en relecture. Une personne vérifie les calculs, les faits, le niveau et le ton. |
| Il est approuvé | Les autres familles peuvent l'activer pour leurs enfants. |

Deux choses à retenir : **rien ne vous oblige à partager** (un pack gardé pour
vous fonctionne parfaitement), et un pack refusé pour la communauté **reste chez
vous**, avec la progression et les points que votre enfant a gagnés.

## Une règle avant de commencer : aucune donnée personnelle

Si vous partagez un pack, il sera lu par des inconnus. Ne mettez donc **jamais**
dans les leçons :

- le prénom de votre enfant ou de ses camarades,
- le nom de son école, de sa ville ou de son club,
- sa date de naissance, une photo, une adresse.

Ce n'est pas une précaution théorique : demander « un pack sur les vacances
d'Arthur à Biarritz » publie le prénom d'un enfant et l'endroit où il passe
l'été. Le thème est excellent — gardez « les vacances à la mer » et remplacez
Arthur par Tom. Les leçons n'y perdent rien, et votre enfant reste invisible.

La relecture attrape ces cas, mais autant ne pas les écrire.

## Connecter votre assistant : un code, lu à voix haute

Dans Explorito : **Mes leçons** dans la barre de navigation — la page s'intitule
« Mes contributions » — puis, sur la carte **« Connecter mon assistant »**,
cliquez **« Afficher mon code »**. Un code de huit caractères
s'affiche, du type `K7QF-3M2P`, avec le compte à rebours « Valable encore
mm:ss ». Vous le **lisez à votre assistant**, et c'est tout : il s'en sert pour
récupérer son jeton d'envoi et le ranger lui-même sur votre ordinateur. Rien à
copier, rien à coller, rien à retenir.

La même page s'ouvre aussi depuis la Bibliothèque, bouton
**« Créer ou envoyer des leçons »**.

Si vous préférez ne rien dicter, **« Copier la phrase »** met dans votre
presse-papiers une demande complète, code compris, à coller dans votre
assistant : « Connecte-toi à Explorito avec le code K7QF-3M2P, puis fais-moi un
pack sur les dinosaures pour un CE1. » **« Copier le code »** ne copie que le
code.

Le code vaut **15 minutes** et ne sert **qu'une fois**. Passé ce délai, ou s'il a
déjà servi, le bouton devient **« Afficher un nouveau code »** : reprenez-en un
neuf. Ces codes n'emploient aucun caractère prêtant à confusion — ni `O` ni `0`,
ni `I` ni `1` ni `L`, ni `U` ni `V`. Si vous croyez lire un « O », c'est un `Q` :
relisez le caractère plutôt que de laisser votre assistant deviner.

Le jeton que votre assistant obtient est *limité* : il ne peut que déposer des
brouillons sur votre compte — il ne peut rien publier, rien supprimer, ni
toucher au compte de votre enfant. Pour le couper, dépliez **« Je préfère gérer
un jeton moi-même »** sur cette même page et cliquez **« Révoquer »** (ou
**« Tout révoquer »**) : l'assistant perd l'accès immédiatement.

### Les conditions et votre pseudonyme, dans l'application

À votre première arrivée sur **Mes contributions**, une fenêtre
**« Conditions de contribution »** s'ouvre d'elle-même : cochez « J'ai lu et
j'accepte les conditions de contribution. », choisissez votre **pseudonyme
public** (3 à 24 caractères) — c'est lui qui apparaîtra comme auteur des packs,
ni votre nom, ni votre e-mail, ni votre photo ne sont montrés — puis
**« Accepter et activer la page »**. Si vous répondez « Plus tard », la page
reste inerte derrière le bandeau « Cette page est inactive », et
**« Lire et accepter les conditions »** rouvre la fenêtre quand vous voulez.

Votre assistant ne peut pas accepter à votre place : c'est le seul geste qui
n'appartient qu'à vous. S'il vous dit que les conditions manquent, c'est là qu'il
faut cliquer. Il arrive aussi qu'une nouvelle version des conditions soit
publiée : la page se reverrouille derrière la même fenêtre, vous acceptez, et
votre assistant renvoie son pack tel quel.

### Si vous préférez tenir le jeton vous-même

Voie secondaire, pour qui aime voir ses secrets : sur la même page, dépliez
**« Je préfère gérer un jeton moi-même »**, section **« Jeton d'envoi »**, puis
**« Créer un jeton »**. Il s'affiche en clair une seule fois (43 caractères) —
copiez-le tout de suite. Il se révoque (**« Révoquer »**) et se recrée au même
endroit. Vous le
collez ensuite dans le fichier `~/.explorito/credentials.json` — celui-là même
que votre assistant écrit tout seul par la voie du code :

```json
{"url": "https://explorito.fr", "token": "votre-jeton", "handle": "VotrePseudo"}
```

---

## Voie A — avec Claude Code (ou un agent qui peut lire des fichiers)

C'est la voie la plus simple : l'agent connaît le format, les bornes de chaque
niveau scolaire, et il envoie le pack lui-même.

**1. Installez la compétence.** Copiez le dossier
`.claude/skills/explorito-pack-author/` du dépôt Explorito dans votre projet ou
dans `~/.claude/skills/`.

**2. Demandez le pack en une phrase :**

> Fais-moi un pack Explorito sur les volcans, niveau CE2, et envoie-le.

La première fois, l'agent vous demandera le code de « Connecter mon assistant » :
lisez-le-lui, il se configure seul. Les fois suivantes, il ne vous demande plus
rien et envoie directement.

L'agent vous rendra un lien d'aperçu, du type
`https://explorito.fr/contributions/…`.

**3. Relisez l'aperçu.** Vous y voyez chaque leçon et chaque exercice comme votre
enfant les verra, et vous pouvez corriger un mot sur place. C'est le bon moment
pour vérifier les calculs et le ton — vous connaissez votre enfant mieux que
n'importe quel modèle.

**4. Activez pour votre enfant**, et si le pack vous plaît, proposez-le à la
communauté depuis ce même écran.

Si l'envoi est refusé, l'agent lit le message d'erreur (il nomme la leçon et
l'exercice fautifs), corrige et renvoie tout seul. Laissez-le faire.

---

## Voie B — sans Claude Code, avec n'importe quel assistant

Fonctionne avec ChatGPT, Claude, Gemini, Mistral : vous copiez une consigne,
l'assistant vous rend un fichier, vous le déposez dans Explorito.

**1. Collez cette consigne** dans votre assistant, en remplaçant les deux
premières lignes :

```
Thème : les volcans
Niveau : ce2      (parmi ps, ms, gs, cp, ce1, ce2, cm1, cm2)

Rédige un pack de leçons pour l'application Explorito, en français, au format
JSON exact ci-dessous. Contraintes impératives :

- 3 à 6 leçons. Chaque leçon a un "tier" : 1 = Découverte (on reconnaît),
  2 = Entraînement (on applique seul), 3 = Défi (problème à plusieurs étapes).
  Répartis-les pour former une vraie progression.
- 4 à 6 exercices par leçon, d'au moins deux types différents.
- "difficulty_level" OBLIGATOIRE sur chaque exercice, de 1 (très facile pour ce
  niveau) à 5 (très difficile pour ce niveau).
- N'écris pas de points d'expérience : ils sont calculés par le serveur.
- Contenu calibré pour le niveau demandé : au CP, nombres jusqu'à 100, additions
  et soustractions jusqu'à 20, aucune multiplication ; au CE1, tables de 2, 3, 5
  et 10 seulement ; au CE2, tables jusqu'à 9 et opérations posées ; au CM1,
  fractions et décimaux. En maternelle (ps, ms, gs) l'enfant ne lit pas : que des
  QCM à images ou à couleurs, consignes de six mots.
- AUCUNE donnée personnelle : prénoms génériques uniquement (Léa, Tom, Zoé),
  aucun nom d'école, de ville de résidence, de club, aucune date de naissance.
- Avant de me répondre, recalcule chaque exercice de type "math_problem" et
  vérifie que "correct_answer.value" est juste. Si le résultat est décimal,
  ajoute "tolerance": 0.01. Vérifie aussi que chaque QCM a une seule bonne
  réponse et que les faits énoncés sont grand public.

Format (matières possibles : maths, francais, orthographe, histoire, geo, monde,
arts, logique) :

{
  "format_version": 1,
  "pack": {"title": "Les volcans 🌋", "emoji": "🌋",
           "description": "Comprendre comment naît une éruption.",
           "tags": ["sciences"]},
  "lessons": [
    {"subject_slug": "monde", "level": "ce2", "tier": 1,
     "name": "Qu'est-ce qu'un volcan ? 🌋",
     "description": "Le cratère, le magma, la lave.",
     "exercises": [
       {"type": "multiple_choice", "question": "Comment appelle-t-on la roche en fusion ?",
        "content": {"options": [{"id": "1", "text": "le magma"},
                                {"id": "2", "text": "le sable"},
                                {"id": "3", "text": "la craie"}], "multiple": false},
        "correct_answer": {"option_ids": ["1"]}, "difficulty_level": 1,
        "explanation": "Sous terre c'est le magma ; en surface, la lave."},
       {"type": "math_problem", "question": "Un volcan crache 12 blocs, puis 9. Combien en tout ?",
        "content": {}, "correct_answer": {"value": 21}, "difficulty_level": 2},
       {"type": "fill_blanks", "question": "Complète.",
        "content": {"text": "La lave sort par le c___."},
        "correct_answer": {"blanks": ["ratère"]}, "difficulty_level": 2},
       {"type": "reading", "question": "Lis ce texte, puis réponds aux questions.",
        "content": {"text": "…"}, "correct_answer": {}, "difficulty_level": 1},
       {"type": "reveal", "question": "Pourquoi les volcans sont-ils bavards ?",
        "content": {"prompt": "Pourquoi les volcans sont-ils bavards ?",
                    "reveal": "Parce qu'ils crachent tout ce qu'ils ont sur le cœur !"},
        "correct_answer": {}, "difficulty_level": 1}
     ]}
  ],
  "self_check": {"math_verified": true, "facts_checked": true, "no_personal_data": true,
                 "notes": "Calculs recalculés un par un."}
}

Réponds uniquement par le JSON, sans commentaire autour.
```

**2. Enregistrez la réponse** dans un fichier nommé par exemple
`volcans.explorito` (l'extension compte peu, c'est du JSON).

**3. Déposez-le** dans Explorito : **Mes leçons → Déposer un pack → Un
fichier**, choisissez le fichier puis **« Envoyer le brouillon »**. Vous obtenez
le même aperçu que dans la voie A.

Si le fichier est refusé, l'écran affiche exactement ce qui cloche et où
(« leçon 2, exercice 3 : difficulty_level manquant »). Recollez ce message à
votre assistant en lui demandant de corriger, et redéposez le fichier.

### Variante en ligne de commande

Si vous êtes à l'aise avec un terminal :

```bash
curl -X POST "https://explorito.fr/api/v1/contributions" \
  -H "X-Upload-Token: VOTRE_JETON" \
  -H "Content-Type: application/json" \
  --data-binary @volcans.explorito
```

La réponse contient `preview_url` : ouvrez-la dans votre navigateur. Le
pseudonyme et les conditions étant réglés dans l'application, il n'y a aucun
paramètre à ajouter ; une réponse `428 terms_required` signifie simplement qu'il
reste à les accepter sur « Mes leçons ».

---

## Ce qui fait un bon pack

Les packs qui marchent vraiment auprès des enfants se ressemblent :

- **Un thème, pas une matière.** « Les volcans » plutôt que « Sciences CE2 ».
  C'est le thème qui donne envie de cliquer.
- **Une progression sensible.** La première leçon doit être gagnable du premier
  coup ; la dernière doit demander un effort. Un enfant qui échoue à la première
  leçon abandonne le pack.
- **Des types d'exercices variés.** Quinze QCM d'affilée lassent. Alternez QCM,
  calcul, texte à trous, et glissez un texte de lecture suivi de ses questions.
- **Des calculs justes.** C'est l'erreur la plus fréquente des assistants IA, et
  la plus décourageante pour un enfant qui a bon et se voit compter faux.
  Vérifiez-en trois ou quatre au hasard dans l'aperçu.
- **Une carte-blague pour finir.** Une devinette en fin de leçon
  (type `reveal`) ne rapporte rien, et c'est souvent l'exercice préféré.
- **Le bon niveau.** Le réflexe des assistants est d'écrire un peu trop
  difficile. Si un exercice vous paraît dur, il l'est.

Les points d'expérience sont calculés par Explorito à partir de la difficulté de
chaque exercice : inutile d'essayer d'en déclarer, et un pack « facile mais très
rémunérateur » n'existe pas.

## Questions fréquentes

**Mon enfant peut-il utiliser un pack avant qu'il soit relu ?** Oui, tout de
suite. La relecture ne concerne que le partage avec les autres familles.

**Que se passe-t-il si mon pack est refusé ?** Il sort du catalogue
communautaire, et c'est tout : vous le gardez, votre enfant le garde, ses points
aussi.

**Puis-je corriger un pack déjà approuvé ?** Un pack approuvé est verrouillé
pour que les familles qui l'ont activé ne voient pas le contenu changer sous
leurs pieds. Vous en faites une copie, vous la corrigez et vous la proposez à
nouveau.

**Combien de packs par jour ?** Cinq envois par jour et trois packs en attente de
relecture en même temps. De quoi rédiger tranquillement, pas de quoi inonder la
file.

**Comment supprimer un pack ?** Écrivez-nous. Rien n'est effacé
automatiquement : supprimer une leçon effacerait la progression des enfants qui
l'ont faite, la vôtre comprise. Un pack se masque, il ne se détruit pas.
