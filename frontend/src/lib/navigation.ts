"use client";

import { useAuth } from "@/lib/auth";

/**
 * Rôle "effectif" qui pilote la navigation et les gardes de route.
 *
 * Un parent en mode "incarnation" (impersonation) d'un enfant est traité comme
 * un enfant : il parcourt le jeu comme lui, avec la bannière de retour.
 */
export type ActingRole = "admin" | "parent" | "child";

const CHILD_PREFIXES = [
  "/play",
  "/subjects",
  "/lessons",
  "/exercises",
  "/pokedex",
];

export function resolveActingRole(
  role: string | undefined,
  isImpersonating: boolean
): ActingRole | null {
  if (isImpersonating && role === "parent") return "child";
  if (role === "admin" || role === "parent" || role === "child") return role;
  return null;
}

/** Page d'accueil par défaut de chaque rôle. */
export function actingRoleHome(role: ActingRole): string {
  switch (role) {
    case "admin":
      return "/admin";
    case "parent":
      return "/dashboard";
    case "child":
      return "/play";
  }
}

/** Un chemin est-il autorisé pour ce rôle ? */
export function isPathAllowedForRole(
  pathname: string,
  role: ActingRole
): boolean {
  if (role === "admin") return pathname.startsWith("/admin");
  if (role === "parent") return pathname.startsWith("/dashboard");
  // child (ou parent en incarnation)
  return CHILD_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

/** Hook pratique : rôle effectif de l'utilisateur courant. */
export function useActingRole(): ActingRole | null {
  const { user, impersonatedChild } = useAuth();
  return resolveActingRole(user?.role, !!impersonatedChild);
}
