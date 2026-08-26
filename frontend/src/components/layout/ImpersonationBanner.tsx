"use client";

import { useEffect, useState } from "react";

/**
 * Bandeau visible sur toutes les pages (app) quand un admin observe l'app « en
 * tant que » un autre compte (clé localStorage `impersonate_user`). Le bouton
 * « Quitter » efface l'incarnation et renvoie vers l'administration.
 */
export function ImpersonationBanner() {
  const [active, setActive] = useState(false);

  useEffect(() => {
    try {
      setActive(!!localStorage.getItem("impersonate_user"));
    } catch {
      setActive(false);
    }
  }, []);

  if (!active) return null;

  const exit = () => {
    localStorage.removeItem("impersonate_user");
    window.location.href = "/admin";
  };

  return (
    <div className="flex items-center justify-center gap-3 bg-fun-violet px-4 py-2 text-sm font-bold text-white">
      <span>🕵️ Mode admin — tu regardes en tant qu&apos;un autre compte.</span>
      <button
        type="button"
        onClick={exit}
        className="rounded-lg bg-white/25 px-3 py-1 text-xs font-extrabold transition-colors hover:bg-white/40 active:scale-95"
      >
        Quitter
      </button>
    </div>
  );
}
