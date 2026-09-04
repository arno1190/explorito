import Link from "next/link";
import type { Metadata } from "next";

/**
 * Tutoriel public « créer ses propres leçons avec son IA ».
 *
 * Volontairement **hors du groupe `(app)`** : c'est la page vers laquelle
 * pointe l'email d'annonce, elle doit s'ouvrir sans connexion et sans passer
 * par la garde de route.
 */
export const metadata: Metadata = {
  title: "Créer ses leçons avec son IA — Explorito",
  description:
    "Comment créer un pack de leçons pour votre enfant avec votre assistant IA, et le proposer à toute la communauté Explorito.",
};

const STEPS = [
  {
    n: 1,
    title: "Connectez votre assistant : un code, lu à voix haute",
    body: (
      <>
        Dans Explorito, ouvrez <strong>Mes leçons</strong> depuis votre espace
        parent, puis <strong>« Connecter mon assistant »</strong>. Un code de 8
        caractères s&apos;affiche : lisez-le à votre assistant, il se configure
        tout seul. Rien à installer, rien à recopier.
        <br />
        Le code vaut 15 minutes et ne sert qu&apos;une fois. Ce qu&apos;il donne
        à votre assistant ne sait faire qu&apos;<strong>une</strong> chose :
        déposer un brouillon. Ni publier, ni supprimer, ni lire quoi que ce soit
        d&apos;autre — et vous le révoquez d&apos;un clic depuis la même page.
      </>
    ),
  },
  {
    n: 2,
    title: "Demandez un pack à votre IA",
    body: (
      <>
        Une phrase suffit :{" "}
        <em>« Fais-moi un pack Explorito sur les dinosaures pour un CE1 »</em>.
        Votre assistant écrit plusieurs leçons qui montent en difficulté,
        vérifie ses propres calculs, puis envoie le tout à Explorito.
        <br />
        Explorito n&apos;appelle jamais d&apos;IA lui-même : c&apos;est
        <strong> votre</strong> assistant qui écrit, et vous gardez la main sur
        ce qu&apos;il produit.
      </>
    ),
  },
  {
    n: 3,
    title: "Relisez l'aperçu, puis soumettez",
    body: (
      <>
        Vous recevez un lien d&apos;aperçu. Vous y voyez chaque leçon et chaque
        exercice exactement comme votre enfant les verra, avec les remarques
        automatiques (courbe de difficulté plate, exercices tous identiques…).
        Corrigez directement dans la page si besoin, puis soumettez.
      </>
    ),
  },
];

const CHECKLIST = [
  "Plusieurs leçons, de la découverte au défi — pas un sac d'exercices.",
  "Un mélange de types : QCM, texte à trous, problème, carte à lire.",
  "Des nombres et des phrases adaptés au niveau visé.",
  "Chaque calcul revérifié : une mauvaise réponse enseigne une erreur.",
  "Aucune donnée personnelle : ni prénom réel, ni école, ni ville, ni photo.",
];

export default function TutorielLeconsCommunautairesPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-fun-sky-light via-fun-surface to-fun-accent-light">
      <div className="container mx-auto max-w-3xl px-4 py-10">
        <p className="mb-2 text-sm font-bold uppercase tracking-wide text-fun-green-dark">
          Nouveau dans Explorito
        </p>
        <h1 className="mb-4 text-3xl font-extrabold text-fun-text sm:text-4xl">
          Créez vos propres leçons avec votre IA 🦊
        </h1>
        <p className="mb-8 text-lg text-fun-text-muted">
          Votre enfant s&apos;est passionné pour les volcans, les dinosaures ou
          la Coupe du monde&nbsp;? Vous pouvez désormais fabriquer un pack de
          leçons sur ce thème, l&apos;utiliser tout de suite pour lui, et — si
          vous le souhaitez — l&apos;offrir aux autres familles.
        </p>

        <section className="mb-10 rounded-2xl border-2 border-fun-green bg-fun-card p-6 candy-shadow">
          <h2 className="mb-2 text-xl font-bold text-fun-text">
            En trois étapes
          </h2>
          <ol className="space-y-5">
            {STEPS.map((step) => (
              <li key={step.n} className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-fun-green text-lg font-extrabold text-white">
                  {step.n}
                </span>
                <div>
                  <h3 className="font-bold text-fun-text">{step.title}</h3>
                  <p className="text-sm text-fun-text-muted">{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="mb-10">
          <h2 className="mb-3 text-2xl font-bold text-fun-text">
            Avec Claude Code (ou un agent équivalent)
          </h2>
          <p className="mb-3 text-fun-text-muted">
            Installez la compétence d&apos;écriture et demandez votre pack :
            elle vous réclamera le code d&apos;appariement la première fois, et
            plus rien ensuite. Elle connaît le programme de chaque niveau, du PS
            au CM2, vérifie ses calculs et corrige elle-même si Explorito refuse
            l&apos;envoi.
          </p>
          <pre className="overflow-x-auto rounded-2xl bg-fun-text p-4 text-sm text-fun-surface">
            <code>{`« Utilise la compétence explorito-pack-author :
  un pack sur les dinosaures pour un CE1. »

# la première fois, elle demande :
#   « lis-moi le code affiché dans Mes leçons »
# puis elle garde l'accès dans ~/.explorito/credentials.json`}</code>
          </pre>
        </section>

        <section className="mb-10">
          <h2 className="mb-3 text-2xl font-bold text-fun-text">
            Sans agent, avec n&apos;importe quel assistant
          </h2>
          <p className="mb-3 text-fun-text-muted">
            Copiez ce message dans ChatGPT, Claude, Gemini ou autre. Vous
            récupérez un fichier, que vous déposez ensuite dans Explorito via
            <strong> Contributions → Déposer un pack</strong>.
          </p>
          <pre className="overflow-x-auto rounded-2xl bg-fun-text p-4 text-sm text-fun-surface">
            <code>{`Tu écris un pack de leçons pour l'application Explorito
(enfants, programme français). Thème : LES DINOSAURES. Niveau : CE1.

Rends un seul fichier JSON, sans commentaire, de cette forme :
{
  "format_version": 1,
  "pack": {"title": "...", "emoji": "🦕", "description": "...",
           "tags": ["dinosaures"]},
  "lessons": [
    {"subject_slug": "monde", "level": "ce1", "tier": 1,
     "name": "...", "description": "...",
     "exercises": [
       {"type": "multiple_choice", "question": "...", "difficulty_level": 1,
        "content": {"options": [{"id": "a", "text": "..."}]},
        "correct_answer": {"option_ids": ["a"]}}
     ]}
  ],
  "self_check": {"math_verified": true, "notes": "..."}
}

Règles :
- 3 leçons : découverte, entraînement, défi (difficulté croissante).
- "difficulty_level" obligatoire sur chaque exercice, de 1 à 5.
- Mélange les types : multiple_choice, fill_blanks, math_problem, reading.
- Recalcule chaque réponse numérique avant de répondre.
- Aucune donnée personnelle : pas de prénom réel, d'école ni de ville.
- Français correct, phrases courtes, vocabulaire du niveau visé.`}</code>
          </pre>
        </section>

        <section className="mb-10 rounded-2xl border-2 border-fun-accent bg-fun-card p-6 candy-shadow">
          <h2 className="mb-2 text-xl font-bold text-fun-text">
            Ce qui se passe après l&apos;envoi
          </h2>
          <ul className="space-y-2 text-sm text-fun-text-muted">
            <li>
              <strong className="text-fun-text">
                Votre enfant y a accès tout de suite.
              </strong>{" "}
              Pas d&apos;attente, pas de validation : c&apos;est votre contenu,
              pour votre famille.
            </li>
            <li>
              <strong className="text-fun-text">
                La communauté, plus tard.
              </strong>{" "}
              Je relis chaque pack — calculs, faits, ton, titre — avant
              qu&apos;il apparaisse au catalogue des autres parents.
            </li>
            <li>
              <strong className="text-fun-text">
                Et chez les autres, c&apos;est au choix.
              </strong>{" "}
              Un pack approuvé n&apos;arrive jamais tout seul chez un enfant :
              son parent doit l&apos;activer, enfant par enfant.
            </li>
            <li>
              <strong className="text-fun-text">
                L&apos;XP ne se déclare pas.
              </strong>{" "}
              Les points sont calculés par Explorito d&apos;après le contenu, et
              restent au tarif de base jusqu&apos;à la relecture — inutile
              d&apos;essayer de gonfler les récompenses.
            </li>
          </ul>
        </section>

        <section className="mb-10">
          <h2 className="mb-3 text-2xl font-bold text-fun-text">
            Ce qui fait un bon pack
          </h2>
          <ul className="space-y-2">
            {CHECKLIST.map((item) => (
              <li key={item} className="flex gap-2 text-fun-text-muted">
                <span aria-hidden className="text-fun-green">
                  ✓
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-12 rounded-2xl border-2 border-fun-red bg-fun-red-light p-6">
          <h2 className="mb-2 text-xl font-bold text-fun-text">
            Une règle non négociable : aucune donnée personnelle
          </h2>
          <p className="text-sm text-fun-text-muted">
            L&apos;accident typique n&apos;est pas malveillant : c&apos;est un
            pack intitulé « Les vacances d&apos;Arthur à Biarritz ». Le prénom
            réel d&apos;un enfant et le nom de sa ville, publiés à des inconnus.
            Nommez vos personnages autrement, restez sur des lieux publics, et
            n&apos;utilisez ni photo de famille ni nom d&apos;école.
          </p>
        </section>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/contributions"
            className="flex min-h-12 flex-1 items-center justify-center rounded-xl bg-fun-green px-6 font-bold text-white transition-transform active:scale-95"
          >
            Créer mon premier pack
          </Link>
          <Link
            href="/bibliotheque"
            className="flex min-h-12 flex-1 items-center justify-center rounded-xl border-2 border-fun-green bg-fun-card px-6 font-bold text-fun-green-dark transition-transform active:scale-95"
          >
            Voir le catalogue
          </Link>
        </div>

        <p className="mt-8 text-center text-sm text-fun-text-muted">
          Une question, une idée, un pack qui coince&nbsp;? Écrivez-moi à{" "}
          <a
            className="font-semibold text-fun-green-dark underline"
            href="mailto:arnaud@pascalfamily.fr"
          >
            arnaud@pascalfamily.fr
          </a>
          .
        </p>
      </div>
    </main>
  );
}
