"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({ email, password });
    } catch (err: any) {
      setError(err.response?.data?.detail || "Connexion échouée. Réessayez.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-fun-sky-light via-white to-fun-violet-light px-4">
      <Card className="w-full max-w-md rounded-3xl candy-shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="text-5xl mb-2">🦉</div>
          <CardTitle className="text-2xl font-extrabold text-fun-text">
            Connexion
          </CardTitle>
          <CardDescription>
            Entre ton email et ton mot de passe pour accéder à ton compte
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-fun-red-light text-fun-red p-3 rounded-xl text-sm border border-fun-red/20">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="toi@exemple.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Connexion..." : "Se connecter"}
            </Button>
            <div className="text-sm text-center text-muted-foreground">
              Pas encore de compte ?{" "}
              <Link
                href="/register"
                className="text-fun-green hover:underline font-semibold"
              >
                Inscription
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
