"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Ancienne route : le Pokédex fait désormais partie des « Collections ». */
export default function PokedexRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/collection/pokemon");
  }, [router]);
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
    </div>
  );
}
