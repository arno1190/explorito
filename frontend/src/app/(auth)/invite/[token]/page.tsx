"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UserAvatar } from "@/components/profile/UserAvatar";
import { previewApiV1InvitationsTokenGet as getPreview } from "@/lib/api/generated/invitations/invitations";
import type { InvitationPreview } from "@/lib/api/model";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const PENDING_KEY = "pending_invite";

type GoogleId = {
  accounts: {
    id: {
      initialize: (c: {
        client_id: string;
        callback: (r: { credential: string }) => void;
      }) => void;
      renderButton: (el: HTMLElement, o: Record<string, unknown>) => void;
    };
  };
};
declare global {
  interface Window {
    google?: GoogleId;
  }
}

export default function InvitePage() {
  const params = useParams();
  const token = params.token as string;
  const router = useRouter();
  const { isAuthenticated, googleLogin, devLogin } = useAuth();
  const [preview, setPreview] = useState<InvitationPreview | null>(null);
  const [error, setError] = useState("");
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getPreview(token)
      .then(setPreview)
      .catch(() => setPreview({ valid: false }));
  }, [token]);

  // Une fois connecté, l'acceptation se fait sur le tableau de bord (il lit la
  // clé PENDING_KEY). On mémorise donc le jeton avant toute connexion.
  const rememberAndGo = () => {
    localStorage.setItem(PENDING_KEY, token);
    router.push("/dashboard");
  };

  // Bouton Google (visiteurs non connectés) : on mémorise le jeton puis on
  // laisse la connexion rediriger vers le tableau de bord, qui accepte.
  useEffect(() => {
    if (isAuthenticated || !preview?.valid) return;
    if (!GOOGLE_CLIENT_ID) return;

    const handleCredential = async (resp: { credential: string }) => {
      localStorage.setItem(PENDING_KEY, token);
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
  }, [isAuthenticated, preview, token, googleLogin]);

  const body = () => {
    if (!preview) return <p className="text-fun-text-muted">Chargement…</p>;
    if (!preview.valid)
      return (
        <div className="space-y-4 text-center">
          <p className="text-fun-text-muted">
            Cette invitation n&apos;est plus valide (expirée, déjà utilisée ou
            annulée).
          </p>
          <Button variant="outline" onClick={() => router.push("/login")}>
            Aller à la connexion
          </Button>
        </div>
      );

    const who = preview.inviter_name ?? "Un parent";
    const isCoParent = preview.kind === "all";
    return (
      <div className="space-y-5 text-center">
        {!isCoParent && (
          <UserAvatar
            avatar={preview.child_avatar}
            name={preview.child_name}
            className="mx-auto h-16 w-16"
            textClassName="text-3xl"
          />
        )}
        <p className="text-lg font-semibold text-fun-text">
          {isCoParent ? (
            <>
              <b>{who}</b> vous invite à devenir parent sur Explorito.
            </>
          ) : (
            <>
              <b>{who}</b> vous invite à suivre{" "}
              <b>{preview.child_name ?? "un enfant"}</b>.
            </>
          )}
        </p>
        {isCoParent && (preview.children_names?.length ?? 0) > 0 && (
          <p className="text-sm text-fun-text-muted">
            Enfants : {preview.children_names?.join(", ")}
          </p>
        )}

        {error && (
          <div className="rounded-xl bg-fun-red-light p-3 text-sm text-fun-red">
            {error}
          </div>
        )}

        {isAuthenticated ? (
          <Button className="w-full" onClick={rememberAndGo}>
            Accepter et voir sur mon tableau de bord
          </Button>
        ) : GOOGLE_CLIENT_ID ? (
          <div className="flex flex-col items-center gap-2">
            <p className="text-sm text-fun-text-muted">
              Connecte-toi avec Google pour accepter :
            </p>
            <div ref={buttonRef} className="flex justify-center" />
          </div>
        ) : (
          <Button
            className="w-full"
            onClick={async () => {
              localStorage.setItem(PENDING_KEY, token);
              await devLogin("parent@qa.fr");
            }}
          >
            Accepter (dev)
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-fun-sky-light via-white to-fun-violet-light px-4">
      <Card className="w-full max-w-md rounded-3xl candy-shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="mb-2 text-5xl">🦊</div>
          <CardTitle className="text-2xl font-extrabold text-fun-text">
            Invitation Explorito
          </CardTitle>
          <CardDescription>Garde partagée d&apos;un enfant</CardDescription>
        </CardHeader>
        <CardContent>{body()}</CardContent>
      </Card>
    </div>
  );
}
