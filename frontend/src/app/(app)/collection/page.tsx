"use client";

import { useRouter } from "next/navigation";
import { Star } from "lucide-react";

import { useGetWalletApiV1CollectionMeGet as useWallet } from "@/lib/api/generated/collection/collection";

export default function CollectionHubPage() {
  const router = useRouter();
  const walletQuery = useWallet();
  const wallet = walletQuery.data;

  if (walletQuery.isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  const balance = wallet?.balance ?? 0;
  const catalogs = wallet?.catalogs ?? [];

  return (
    <div className="container mx-auto max-w-4xl p-4 pb-24 sm:p-6">
      {/* Wallet header */}
      <div className="mb-6 rounded-3xl bg-white p-6 candy-shadow">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-fun-text sm:text-3xl">
              🎁 Mes collections
            </h1>
            <p className="mt-1 text-fun-text-muted">
              Dépense ton XP pour débloquer des trésors&nbsp;!
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-2xl bg-fun-sun-light px-5 py-3">
            <Star className="h-6 w-6 fill-fun-sun text-fun-sun" />
            <div>
              <div className="text-2xl font-extrabold text-fun-text">
                {balance}
              </div>
              <div className="text-xs font-semibold text-fun-text-muted">
                XP à dépenser
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Catalog cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {catalogs.map((c) => {
          const pct = c.total ? (c.unlocked / c.total) * 100 : 0;
          const complete = c.total > 0 && c.unlocked >= c.total;
          return (
            <button
              key={c.slug}
              onClick={() => router.push(`/collection/${c.slug}`)}
              className="flex flex-col rounded-3xl border-2 border-fun-border bg-white p-5 text-left candy-shadow transition-all hover:scale-[1.02] hover:border-fun-green active:scale-95"
            >
              <div className="flex items-center gap-3">
                <span className="text-5xl">{c.icon}</span>
                <div>
                  <div className="text-xl font-extrabold text-fun-text">
                    {c.name}
                  </div>
                  <div className="text-sm font-semibold text-fun-text-muted">
                    {c.unlocked} / {c.total}
                    {complete && " · Complet ! 🏆"}
                  </div>
                </div>
              </div>
              <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-fun-green-light">
                <div
                  className="h-3 rounded-full bg-fun-green transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
