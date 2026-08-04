"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * L'inscription se fait automatiquement à la première connexion Google
 * (inscription libre des parents) : cette page redirige vers la connexion.
 */
export default function RegisterPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/login");
  }, [router]);
  return null;
}
