"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

// Google Identity Services est injecté globalement par le script gsi/client.
type GoogleId = {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (resp: { credential: string }) => void;
      }) => void;
      renderButton: (
        parent: HTMLElement,
        options: Record<string, unknown>
      ) => void;
    };
  };
};
declare global {
  interface Window {
    google?: GoogleId;
  }
}

export default function LoginPage() {
  const { googleLogin, devLogin } = useAuth();
  const [error, setError] = useState("");
  const [devEmail, setDevEmail] = useState("");
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const handleCredential = async (resp: { credential: string }) => {
      setError("");
      try {
        await googleLogin(resp.credential);
      } catch {
        setError("Connexion Google échouée. Réessaie.");
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
        text: "continue_with",
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

  const handleDevLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await devLogin(devEmail);
    } catch {
      setError("Connexion de développement échouée.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-fun-sky-light via-white to-fun-violet-light px-4">
      <Card className="w-full max-w-md rounded-3xl candy-shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="text-5xl mb-2">🦉</div>
          <CardTitle className="text-2xl font-extrabold text-fun-text">
            Bienvenue sur Explorito
          </CardTitle>
          <CardDescription>
            Connexion des parents avec un compte Google
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-4">
          {error && (
            <div className="w-full bg-fun-red-light text-fun-red p-3 rounded-xl text-sm border border-fun-red/20">
              {error}
            </div>
          )}

          {GOOGLE_CLIENT_ID ? (
            <div ref={buttonRef} className="flex justify-center" />
          ) : (
            <form onSubmit={handleDevLogin} className="w-full space-y-3">
              <p className="text-xs text-fun-text-muted text-center">
                Mode développement — connexion par email (Google désactivé).
              </p>
              <Input
                type="email"
                placeholder="parent@exemple.fr"
                value={devEmail}
                onChange={(e) => setDevEmail(e.target.value)}
                required
              />
              <Button type="submit" className="w-full">
                Se connecter (dev)
              </Button>
            </form>
          )}

          <p className="text-xs text-fun-text-muted text-center pt-2">
            Les enfants n&apos;ont pas de compte : le parent lance l&apos;app
            pour eux depuis le tableau de bord.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
