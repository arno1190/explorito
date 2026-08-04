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
  "/collection",
  "/pokedex",
  "/pythagore",
];

export function resolveActingRole(
  role: string | undefined,
  isImpersonating: boolean
): ActingRole | null {
  // Un parent OU un admin en incarnation est traité comme un enfant (il joue
  // à sa place, avec la bannière de retour protégée par PIN).
  if (isImpersonating && (role === "parent" || role === "admin"))
    return "child";
  if (role === "admin" || role === "parent" || role === "child") return role;
  return null;
}

/** Page d'accueil par défaut de chaque rôle. */
export function actingRoleHome(role: ActingRole): string {
  switch (role) {
    case "admin":
      // L'admin (parent-superset) gère aussi ses enfants : on l'amène au
      // tableau de bord d'où il lance le mode enfant.
      return "/dashboard";
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
  // L'admin est un sur-ensemble du parent : gestion de contenu (/admin) ET
  // gestion de famille (/dashboard, /progress).
  if (role === "admin")
    return (
      pathname.startsWith("/admin") ||
      pathname.startsWith("/dashboard") ||
      pathname.startsWith("/progress")
    );
  if (role === "parent")
    return (
      pathname.startsWith("/dashboard") || pathname.startsWith("/progress")
    );
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
