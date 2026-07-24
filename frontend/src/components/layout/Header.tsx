"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  actingRoleHome,
  useActingRole,
  type ActingRole,
} from "@/lib/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LogOut, ArrowLeft } from "lucide-react";

const NAV_LINKS: Record<ActingRole, { href: string; label: string }[]> = {
  child: [
    { href: "/play", label: "Jouer" },
    { href: "/subjects", label: "Matières" },
    { href: "/pokedex", label: "Pokédex" },
  ],
  parent: [{ href: "/dashboard", label: "Tableau de bord" }],
  admin: [
    { href: "/admin", label: "Contenu" },
    { href: "/admin/users", label: "Utilisateurs" },
  ],
};

export function Header() {
  const {
    user,
    logout,
    isAuthenticated,
    impersonatedChild,
    stopImpersonation,
  } = useAuth();
  const actingRole = useActingRole();
  const pathname = usePathname();

  const getInitials = (name?: string) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const homeHref = actingRole ? actingRoleHome(actingRole) : "/";
  const links = actingRole ? NAV_LINKS[actingRole] : [];

  return (
    <>
      {impersonatedChild && (
        <div className="bg-fun-sun-light text-fun-text px-4 py-2 text-center border-b-2 border-fun-sun">
          <div className="container mx-auto flex items-center justify-center gap-4">
            <span className="font-semibold">
              Mode enfant&nbsp;: {impersonatedChild.name}
            </span>
            <Button
              size="sm"
              variant="secondary"
              onClick={stopImpersonation}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Retour au mode parent
            </Button>
          </div>
        </div>
      )}

      <header className="bg-white/80 backdrop-blur-sm border-b-2 border-fun-border sticky top-0 z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            href={homeHref}
            className="text-2xl font-extrabold text-fun-green"
          >
            Explorito
          </Link>

          <nav className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                {links.map((link) => {
                  const isActive =
                    pathname === link.href ||
                    pathname.startsWith(link.href + "/");
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      className={`hidden md:block text-sm font-semibold transition-colors ${
                        isActive
                          ? "text-fun-green"
                          : "text-fun-text hover:text-fun-green"
                      }`}
                    >
                      {link.label}
                    </Link>
                  );
                })}

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="relative h-10 w-10 rounded-full"
                    >
                      <Avatar>
                        <AvatarFallback className="bg-fun-green-light text-fun-green font-bold">
                          {getInitials(
                            impersonatedChild?.name ||
                              user?.profile?.display_name
                          )}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">
                          {impersonatedChild?.name ||
                            user?.profile?.display_name ||
                            user?.email}
                        </p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {user?.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {impersonatedChild ? (
                      <DropdownMenuItem onClick={stopImpersonation}>
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        <span>Retour au mode parent</span>
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem onClick={logout}>
                        <LogOut className="mr-2 h-4 w-4" />
                        <span>Déconnexion</span>
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost">Connexion</Button>
                </Link>
                <Link href="/register">
                  <Button>Inscription</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
    </>
  );
}
