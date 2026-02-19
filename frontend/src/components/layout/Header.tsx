"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
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
import { LogOut, User, ArrowLeft } from "lucide-react";

export function Header() {
  const {
    user,
    logout,
    isAuthenticated,
    impersonatedChild,
    stopImpersonation,
  } = useAuth();

  const getInitials = (name?: string) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <>
      {impersonatedChild && (
        <div className="bg-candy-yellow-light text-candy-text px-4 py-2 text-center border-b-2 border-candy-yellow">
          <div className="container mx-auto flex items-center justify-center gap-4">
            <span className="font-semibold">
              Mode enfant: {impersonatedChild.name}
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

      <header className="bg-white/80 backdrop-blur-sm border-b-2 border-candy-border sticky top-0 z-40">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <Link href="/" className="text-2xl font-extrabold text-candy-purple">
            Explorito
          </Link>

          <nav className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="hidden md:block text-sm font-semibold text-candy-text hover:text-candy-purple transition-colors"
                >
                  Dashboard
                </Link>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="relative h-10 w-10 rounded-full"
                    >
                      <Avatar>
                        <AvatarFallback className="bg-candy-purple-light text-candy-purple font-bold">
                          {getInitials(user?.profile?.display_name)}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">
                          {user?.profile?.display_name || user?.email}
                        </p>
                        <p className="text-xs leading-none text-muted-foreground">
                          {user?.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>
                      <User className="mr-2 h-4 w-4" />
                      <span>Profil</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={logout}>
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Déconnexion</span>
                    </DropdownMenuItem>
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
