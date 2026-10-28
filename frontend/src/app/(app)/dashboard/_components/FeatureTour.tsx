"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";

const SEEN_KEY = "explorito_tour_seen";

/**
 * Au-delà de cet âge de compte, la visite ne s'ouvre plus d'elle-même : une
 * famille installée depuis des mois n'a pas besoin qu'on lui présente
 * l'application. Elle reste accessible depuis le bouton « Visite guidée ».
 */
const AUTO_OPEN_MAX_ACCOUNT_AGE_MS = 30 * 24 * 60 * 60 * 1000;

/** La visite doit-elle s'ouvrir seule pour ce compte ? */
export function shouldAutoOpenTour(createdAt: string | undefined): boolean {
  if (!createdAt) return false;
  if (Date.now() - new Date(createdAt).getTime() > AUTO_OPEN_MAX_ACCOUNT_AGE_MS)
    return false;
  try {
    return !localStorage.getItem(SEEN_KEY);
  } catch {
    return false;
  }
}

function markTourSeen(): void {
  try {
    localStorage.setItem(SEEN_KEY, new Date().toISOString());
  } catch {
    // Navigation privée : la visite se reproposera, sans autre conséquence.
  }
}

interface Slide {
  emoji: string;
  title: string;
  points: React.ReactNode[];
  link?: { href: string; label: string };
}

/**
 * Une diapositive par fonctionnalité, dans l'ordre où un parent les rencontre :
 * lancer l'enfant, le contenu, le suivi, les récompenses, puis ce qu'on peut
 * construire soi-même. Trois lignes au plus chacune — tout le détail vit déjà
 * dans les écrans eux-mêmes.
 */
const SLIDES: Slide[] = [
  {
    emoji: "👋",
    title: "Explorito en une minute",
    points: [
      <>
        Votre enfant n&apos;a <strong>pas de compte</strong> : c&apos;est vous
        qui le lancez avec <strong>« Jouer comme… »</strong> sur sa carte.
      </>,
      <>
        Votre <strong>code parent</strong> à 4 chiffres l&apos;empêche de
        revenir seul sur ce tableau de bord.
      </>,
    ],
  },
  {
    emoji: "📚",
    title: "Des matières, des thèmes, des paliers",
    points: [
      <>
        Chaque enfant voit les matières de <strong>sa classe</strong> : maths,
        français, sciences, musique…
      </>,
      <>
        Les leçons se débloquent pas à pas :{" "}
        <strong>Découverte → Entraînement → Défi</strong>.
      </>,
      <>
        Changez sa classe à tout moment avec le <strong>crayon ✏️</strong> de sa
        carte.
      </>,
    ],
  },
  {
    emoji: "📈",
    title: "Suivre ses progrès",
    points: [
      <>
        <strong>« Voir les progrès »</strong> montre ses leçons réussies, son XP
        par matière et sa série de jours 🔥.
      </>,
      <>
        Chaque exercice réussi rapporte de l&apos;XP : plus il est dur, plus il
        rapporte.
      </>,
    ],
  },
  {
    emoji: "🎁",
    title: "Deux sortes de points",
    points: [
      <>
        <strong>⭐ Points</strong> : gagnés en jouant, et ceux que vous donnez
        pour une dictée ou des lacets bien faits.
      </>,
      <>
        <strong>💚 Comportement</strong> : une bonne action (+5), une bêtise
        (−3). Ceux-là ne comptent que pour la maison.
      </>,
      <>
        Bouton <strong>« 🎁 Attribuer des points »</strong> sur la carte de
        l&apos;enfant.
      </>,
    ],
  },
  {
    emoji: "🃏",
    title: "Des collections à compléter",
    points: [
      <>
        Les points s&apos;échangent contre des cartes : Pokémon, dinosaures,
        planètes, Super Mario, Harry Potter…
      </>,
      <>
        Vous choisissez <strong>quelles collections</strong> votre enfant voit,
        depuis le <strong>crayon ✏️</strong> de sa carte.
      </>,
    ],
  },
  {
    emoji: "🤖",
    title: "Créez vos leçons avec votre IA",
    points: [
      <>
        Dans <strong>Mes leçons</strong>, « Connecter mon assistant » donne une
        phrase à coller dans ChatGPT, Claude ou autre.
      </>,
      <>
        Demandez <em>« un pack sur les volcans pour un CE1 »</em> : vous relisez
        l&apos;aperçu, et votre enfant y a accès tout de suite.
      </>,
      <>
        La <strong>Bibliothèque</strong> rassemble les packs relus des autres
        familles.
      </>,
    ],
    link: {
      href: "/tutoriel/lecons-communautaires",
      label: "Voir le tutoriel",
    },
  },
  {
    emoji: "👨‍👩‍👧",
    title: "À plusieurs, c'est mieux",
    points: [
      <>
        <strong>« Inviter un parent »</strong> : l&apos;autre parent voit et
        lance tous vos enfants.
      </>,
      <>
        <strong>« Partager »</strong> sur une carte : une mamie ou une nounou
        suit un seul enfant.
      </>,
      <>
        Cette visite reste disponible avec le bouton{" "}
        <strong>« Visite guidée »</strong>.
      </>,
    ],
  },
];

/**
 * Visite guidée des fonctionnalités, pour le parent qui vient d'arriver.
 *
 * Elle complète le parcours d'accueil (`OnboardingFlow`) sans le rallonger :
 * celui-ci installe un enfant, celle-ci explique ce qu'on peut en faire. Toute
 * fermeture — fin, « Passer » ou clic extérieur — vaut « vue » : une visite
 * qui revient après avoir été écartée est un reproche, pas une aide.
 */
export function FeatureTour({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [index, setIndex] = useState(0);
  const slide = SLIDES[index];
  const isLast = index === SLIDES.length - 1;

  const close = () => {
    markTourSeen();
    setIndex(0);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent className="max-w-md rounded-2xl">
        <div className="space-y-5 pt-2">
          <div
            key={index}
            className="animate-[candy-pop_0.4s_ease-out] space-y-3 text-center"
          >
            <div className="text-6xl" aria-hidden>
              {slide.emoji}
            </div>
            <DialogTitle className="text-2xl font-extrabold text-fun-text">
              {slide.title}
            </DialogTitle>
            <DialogDescription className="sr-only">
              Étape {index + 1} sur {SLIDES.length} de la visite guidée
            </DialogDescription>
            <ul className="space-y-2 text-left text-base text-fun-text">
              {slide.points.map((point, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-fun-green" aria-hidden>
                    •
                  </span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
            {slide.link && (
              <Link
                href={slide.link.href}
                onClick={close}
                className="inline-block font-semibold text-fun-sky underline"
              >
                {slide.link.label}
              </Link>
            )}
          </div>

          <div className="flex justify-center gap-2" aria-hidden>
            {SLIDES.map((_, i) => (
              <span
                key={i}
                className={`h-2 rounded-full transition-all ${
                  i === index ? "w-6 bg-fun-green" : "w-2 bg-fun-green-light"
                }`}
              />
            ))}
          </div>

          <div className="flex gap-2">
            {index > 0 && (
              <Button
                variant="outline"
                className="min-h-12"
                onClick={() => setIndex(index - 1)}
                aria-label="Précédent"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
            )}
            <Button
              className="min-h-12 flex-1"
              onClick={() => (isLast ? close() : setIndex(index + 1))}
            >
              {isLast ? "C'est parti !" : "Suivant"}
              {!isLast && <ArrowRight className="ml-2 h-5 w-5" />}
            </Button>
          </div>
          {!isLast && (
            <button
              type="button"
              onClick={close}
              className="min-h-12 w-full text-sm text-fun-text-muted underline"
            >
              Passer la visite
            </button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
