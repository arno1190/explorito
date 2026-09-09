"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

/** Message du serveur (403 sur code manquant/invalide), ou repli générique. */
function signupError(failure: unknown): string {
  const detail = (
    failure as { response?: { data?: { detail?: unknown } } } | undefined
  )?.response?.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  return "L'inscription a échoué. Réessayez dans un instant.";
}

function RegisterForm() {
  const { googleLogin, devLogin } = useAuth();
  const searchParams = useSearchParams();
  // Le code passe aussi par l'URL : un lien suffit, la famille n'a rien à
  // recopier à la main.
  const [invite, setInvite] = useState(searchParams.get("invite") ?? "");
  const [error, setError] = useState("");
  const [devEmail, setDevEmail] = useState("");
  const buttonRef = useRef<HTMLDivElement>(null);
  // Le bouton Google est rendu une seule fois par le script tiers : il ne
  // re-rend pas à chaque frappe dans le champ code. On lit donc le code au
  // moment du clic, via une ref, plutôt que via la closure du callback.
  const inviteRef = useRef(invite);
  inviteRef.current = invite;

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const handleCredential = async (resp: { credential: string }) => {
      setError("");
      try {
        await googleLogin(resp.credential, inviteRef.current.trim());
      } catch (failure) {
        setError(signupError(failure));
      }
    };

    const render = () => {
      if (!window.google || !buttonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredential,
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        shape: "pill",
        text: "signup_with",
        width: 300,
      });
    };

    if (window.google) {
      render();
      return;
    }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = render;
    document.body.appendChild(script);
  }, [googleLogin]);

  const handleDevSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await devLogin(devEmail, invite.trim());
    } catch (failure) {
      setError(signupError(failure));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-fun-sky-light via-white to-fun-violet-light px-4">
      <Card className="w-full max-w-md rounded-3xl candy-shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <img
            src="/explorito-badge.png"
            alt="Explorito"
            className="mx-auto mb-3 h-20 w-20"
          />
          <CardTitle className="text-2xl font-extrabold text-fun-text">
            Créer un compte parent
          </CardTitle>
          <CardDescription>
            Explorito s&apos;ouvre famille par famille.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-4">
          {error && (
            <div className="w-full bg-fun-red-light text-fun-red p-3 rounded-xl text-sm border border-fun-red/20">
              {error}
            </div>
          )}

          <div className="w-full space-y-2">
            <Label htmlFor="invite">Code d&apos;invitation</Label>
            <Input
              id="invite"
              value={invite}
              onChange={(e) => setInvite(e.target.value)}
              placeholder="Collez ici le code reçu"
              autoComplete="off"
            />
            <p className="text-xs text-fun-text-muted">
              Si on vous a envoyé un lien d&apos;invitation, le code est déjà
              rempli. Vous n&apos;en avez pas besoin si vous avez déjà un
              compte.
            </p>
          </div>

          {GOOGLE_CLIENT_ID ? (
            <div ref={buttonRef} className="flex justify-center" />
          ) : (
            <form onSubmit={handleDevSignup} className="w-full space-y-3">
              <p className="text-xs text-fun-text-muted text-center">
                Mode développement — inscription par email (Google désactivé).
              </p>
              <Input
                type="email"
                placeholder="parent@exemple.fr"
                value={devEmail}
                onChange={(e) => setDevEmail(e.target.value)}
                required
              />
              <Button type="submit" className="w-full">
                Créer le compte (dev)
              </Button>
            </form>
          )}

          <p className="text-xs text-fun-text-muted text-center pt-2">
            Vous avez déjà un compte ?{" "}
            <Link href="/login" className="underline hover:text-fun-text">
              Se connecter
            </Link>
          </p>

          <p className="text-xs text-fun-text-muted text-center">
            En créant un compte, vous acceptez notre{" "}
            <Link
              href="/confidentialite"
              className="underline hover:text-fun-text"
            >
              politique de confidentialité
            </Link>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Inscription d'un parent.
 *
 * Le compte se crée à la première connexion Google ; cette page existe pour
 * porter le code d'invitation (issue #22), que `POST /auth/google` exige quand
 * `SIGNUP_INVITE_REQUIRED` est actif. Tant que le réglage est inactif, le champ
 * reste facultatif et l'inscription se comporte comme avant.
 */
export default function RegisterPage() {
  // `useSearchParams` impose une frontière Suspense côté App Router.
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}
