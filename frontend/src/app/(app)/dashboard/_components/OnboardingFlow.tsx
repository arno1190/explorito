"use client";

import { useEffect, useState } from "react";
import { Rocket, Sparkles, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createChildApiV1ChildrenPost,
  updateChildApiV1ChildrenChildIdPut,
} from "@/lib/api/generated/children/children";
import { useListCatalogsApiV1CollectionCatalogsGet as useCatalogs } from "@/lib/api/generated/collection/collection";
import type { ChildResponse, LevelEnum } from "@/lib/api/model";
import { useAuth } from "@/lib/auth";
import { useAvailableLevels } from "@/lib/levels";

/** Étapes du parcours, dans l'ordre. */
type Step = "child" | "interest" | "pin" | "launch";

const STORAGE_KEY = "explorito_onboarding";

/**
 * Reprise du parcours : l'étape atteinte, rattachée à l'enfant créé.
 *
 * Stockée côté navigateur parce que « j'ai sauté cette étape » n'existe pas en
 * base — un centre d'intérêt non choisi et un centre d'intérêt refusé y sont la
 * même absence. La reprise est donc fidèle sur la machine où le parcours a
 * commencé, et un retour depuis un autre appareil retombe simplement sur le
 * tableau de bord normal, jamais sur une étape fausse.
 */
type Saved = { childId: string; step: Step };

function readSaved(): Saved | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

function writeSaved(saved: Saved | null): void {
  if (typeof window === "undefined") return;
  if (saved === null) window.localStorage.removeItem(STORAGE_KEY);
  else window.localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
}

/** Vrai s'il reste un parcours à reprendre pour l'un des enfants existants. */
export function resumableOnboarding(
  children: ChildResponse[]
): ChildResponse | null {
  const saved = readSaved();
  if (!saved) return null;
  return children.find((c) => c.id === saved.childId) ?? null;
}

function StepDots({ current }: { current: Step }) {
  const order: Step[] = ["child", "interest", "pin", "launch"];
  const index = order.indexOf(current);
  return (
    <div className="flex justify-center gap-2 pb-1">
      {order.map((step, i) => (
        <span
          key={step}
          className={`h-2 rounded-full transition-all ${
            i <= index ? "w-6 bg-fun-green" : "w-2 bg-fun-green-light"
          }`}
        />
      ))}
    </div>
  );
}

/**
 * Parcours d'accueil : de l'inscription au premier exercice (issue #24).
 *
 * Un parent qui s'inscrivait atterrissait sur un tableau de bord vide, sans
 * rien qui mène au premier exercice joué. Trois écrans au plus, tous en
 * français, tous quittables : seul le premier est obligatoire — sans enfant, il
 * n'y a rien à lancer.
 */
export function OnboardingFlow({
  resumeChild,
  onChildCreated,
  onFinished,
}: {
  /** Enfant d'un parcours interrompu, s'il y en a un. */
  resumeChild?: ChildResponse | null;
  /** Appelé après création, pour que le tableau de bord recharge sa liste. */
  onChildCreated: () => void;
  /** Appelé quand le parcours est terminé ou abandonné. */
  onFinished: () => void;
}) {
  const { user, impersonateChild, setPin } = useAuth();
  const [step, setStep] = useState<Step>("child");
  const [child, setChild] = useState<ChildResponse | null>(resumeChild ?? null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Reprise : on repart à l'étape enregistrée pour cet enfant.
  useEffect(() => {
    if (!resumeChild) return;
    const saved = readSaved();
    if (saved && saved.childId === resumeChild.id) setStep(saved.step);
  }, [resumeChild]);

  const goTo = (next: Step, forChild: ChildResponse | null) => {
    setStep(next);
    // Une fois au bouton de lancement, il n'y a plus rien à reprendre.
    writeSaved(
      forChild && next !== "launch"
        ? { childId: forChild.id, step: next }
        : null
    );
  };

  // ---- Étape 1 : ajouter un enfant -------------------------------------- //
  const [name, setName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [level, setLevel] = useState<LevelEnum | "">("");
  const { levels } = useAvailableLevels();
  const effectiveLevel = level || levels[0]?.value || "";

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const created = await createChildApiV1ChildrenPost({
        name,
        birth_date: birthDate || undefined,
        level: (effectiveLevel || undefined) as LevelEnum | undefined,
      });
      setChild(created);
      onChildCreated();
      goTo("interest", created);
    } catch {
      setError("L'enfant n'a pas pu être créé. Réessayez dans un instant.");
    } finally {
      setBusy(false);
    }
  };

  // ---- Étape 2 : un premier centre d'intérêt ---------------------------- //
  const { data: catalogs } = useCatalogs({
    query: { enabled: step === "interest" },
  });

  const chooseInterest = async (slug: string) => {
    if (!child) return;
    setError("");
    setBusy(true);
    try {
      // Mettre en avant une collection = masquer les autres pour cet enfant.
      // Réversible depuis la fiche de l'enfant, où le même réglage est exposé.
      await updateChildApiV1ChildrenChildIdPut(child.id, {
        disabled_collections: (catalogs ?? [])
          .map((c) => c.slug)
          .filter((s) => s !== slug),
      });
      goTo("pin", child);
    } catch {
      setError(
        "Le choix n'a pas pu être enregistré. Vous pourrez le faire depuis la fiche de l'enfant."
      );
      goTo("pin", child);
    } finally {
      setBusy(false);
    }
  };

  // ---- Étape 3 : le code PIN parent ------------------------------------- //
  const [pin, setPinValue] = useState("");

  const handlePin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await setPin(pin);
      goTo("launch", child);
    } catch {
      setError(
        "Le code n'a pas pu être enregistré. Il doit contenir 4 chiffres."
      );
    } finally {
      setBusy(false);
    }
  };

  // ---- Rendu ------------------------------------------------------------ //
  const quit = () => {
    writeSaved(null);
    onFinished();
  };

  return (
    <Card className="mx-auto max-w-xl rounded-3xl candy-shadow-lg">
      <CardContent className="space-y-5 p-6 md:p-8">
        <StepDots current={step} />

        {error && (
          <div className="rounded-xl border border-fun-red/20 bg-fun-red-light p-3 text-sm text-fun-red">
            {error}
          </div>
        )}

        {step === "child" && (
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="text-center">
              <UserPlus className="mx-auto mb-2 h-10 w-10 text-fun-green" />
              <h2 className="text-2xl font-extrabold text-fun-text">
                Qui va apprendre&nbsp;?
              </h2>
              <p className="mt-1 text-sm text-fun-text-muted">
                Votre enfant n&apos;a pas de compte : c&apos;est vous qui lancez
                l&apos;application pour lui.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="onb-name">Son prénom</Label>
              <Input
                id="onb-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Louise"
                minLength={2}
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="onb-birth">Sa date de naissance</Label>
              <Input
                id="onb-birth"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="onb-level">Sa classe</Label>
              <select
                id="onb-level"
                value={effectiveLevel}
                onChange={(e) => setLevel(e.target.value as LevelEnum)}
                className="h-12 w-full rounded-xl border-2 border-fun-border bg-white px-3 text-fun-text outline-none focus:border-fun-sky"
              >
                {levels.map((l) => (
                  <option key={l.value} value={l.value}>
                    {l.label}
                  </option>
                ))}
              </select>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={busy || !name || levels.length === 0}
            >
              {busy ? "Création…" : "Continuer"}
            </Button>
          </form>
        )}

        {step === "interest" && child && (
          <div className="space-y-4">
            <div className="text-center">
              <Sparkles className="mx-auto mb-2 h-10 w-10 text-fun-violet" />
              <h2 className="text-2xl font-extrabold text-fun-text">
                Qu&apos;est-ce qui plaît à {child.name}&nbsp;?
              </h2>
              <p className="mt-1 text-sm text-fun-text-muted">
                Les exercices réussis rapportent des points, à dépenser dans une
                collection. Vous pourrez en ajouter d&apos;autres plus tard.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {(catalogs ?? []).map((catalog) => (
                <button
                  key={catalog.slug}
                  type="button"
                  disabled={busy}
                  onClick={() => chooseInterest(catalog.slug)}
                  className="flex min-h-[96px] flex-col items-center justify-center gap-1 rounded-2xl border-2 border-fun-border bg-white p-3 transition-all hover:border-fun-violet hover:candy-shadow active:scale-95"
                >
                  <span className="text-3xl">{catalog.icon}</span>
                  <span className="text-sm font-semibold text-fun-text">
                    {catalog.name}
                  </span>
                </button>
              ))}
            </div>

            <Button
              variant="ghost"
              className="w-full"
              onClick={() => goTo("pin", child)}
            >
              Passer cette étape
            </Button>
          </div>
        )}

        {step === "pin" && child && (
          <form onSubmit={handlePin} className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-extrabold text-fun-text">
                Votre code parent
              </h2>
              <p className="mt-1 text-sm text-fun-text-muted">
                Quatre chiffres qui protègent le retour au tableau de bord :{" "}
                {child.name} ne peut pas quitter le mode enfant sans vous.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="onb-pin">Code à 4 chiffres</Label>
              <Input
                id="onb-pin"
                inputMode="numeric"
                pattern="[0-9]{4}"
                maxLength={4}
                value={pin}
                onChange={(e) =>
                  setPinValue(e.target.value.replace(/\D/g, "").slice(0, 4))
                }
                placeholder="••••"
                className="text-center text-2xl tracking-[0.5em]"
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={busy || pin.length !== 4}
            >
              {busy ? "Enregistrement…" : "Enregistrer le code"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => goTo("launch", child)}
            >
              Plus tard
            </Button>
          </form>
        )}

        {step === "launch" && child && (
          <div className="space-y-4 text-center">
            <Rocket className="mx-auto h-12 w-12 text-fun-green" />
            <h2 className="text-2xl font-extrabold text-fun-text">
              Tout est prêt&nbsp;!
            </h2>
            <p className="text-sm text-fun-text-muted">
              {child.name} arrive directement sur sa première leçon.
              {!user?.has_pin &&
                " Vous pourrez définir votre code parent plus tard depuis le tableau de bord."}
            </p>
            <Button
              size="lg"
              className="w-full text-lg"
              onClick={() => {
                writeSaved(null);
                impersonateChild(child);
              }}
            >
              Lancer {child.name}
            </Button>
            <Button variant="ghost" className="w-full" onClick={quit}>
              Retour au tableau de bord
            </Button>
          </div>
        )}

        {step !== "launch" && (
          <button
            type="button"
            onClick={quit}
            className="w-full text-xs text-fun-text-muted underline"
          >
            Quitter — vous retrouverez cette étape plus tard
          </button>
        )}
      </CardContent>
    </Card>
  );
}
