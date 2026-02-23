"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-fun-surface">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white/80 backdrop-blur-sm border-b-2 border-fun-border sticky top-0 z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-2xl font-extrabold text-fun-green">Explorito</h1>
          <div className="flex gap-3">
            <Link href="/login">
              <Button variant="ghost">Connexion</Button>
            </Link>
            <Link href="/register">
              <Button>Inscription</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light">
        <div className="container mx-auto px-4 py-16 text-center">
          <div
            className="text-7xl mb-6 animate-[candy-bounce_2s_ease-in-out_infinite]"
            role="img"
            aria-label="Mascotte hibou"
          >
            🦉
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold text-fun-text mb-4">
            Apprends en t&apos;amusant !
          </h1>
          <p className="text-lg md:text-xl text-fun-text-muted mb-8 max-w-2xl mx-auto">
            Explorito aide les enfants du CP à découvrir le français, les maths
            et bien plus, de manière ludique et interactive.
          </p>
          <div className="flex gap-4 justify-center flex-col sm:flex-row">
            <Link href="/register">
              <Button size="lg" className="text-lg px-8 w-full sm:w-auto">
                Commencer gratuitement
              </Button>
            </Link>
            <Link href="/login">
              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8 w-full sm:w-auto"
              >
                Se connecter
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
