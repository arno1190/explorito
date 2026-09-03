"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { Compass, Hourglass } from "lucide-react";

import { useActingRole } from "@/lib/navigation";
import {
  useDiscoverApiV1DiscoverGet as useDiscover,
  useCreateRequestApiV1DiscoverRequestsPost as useCreateRequest,
  useListRequestsApiV1DiscoverRequestsGet as useMyRequests,
  getDiscoverApiV1DiscoverGetQueryKey,
  getListRequestsApiV1DiscoverRequestsGetQueryKey,
} from "@/lib/api/generated/discover/discover";
import type { PackRequestResponse } from "@/lib/api/model";
import { DiscoverPackCard } from "./DiscoverPackCard";

/** Statut HTTP d'une erreur de requête (le client Orval rejette des AxiosError). */
function httpStatus(error: unknown): number | undefined {
  return (error as AxiosError | null | undefined)?.response?.status;
}

/** Messages d'erreur en français d'enfant pour les cas réels du backend. */
function requestErrorMessage(error: unknown): string {
  switch (httpStatus(error)) {
    case 429:
      return "Tu as déjà fait plusieurs demandes aujourd'hui, laisse le temps à un adulte de répondre 😉";
    case 409:
      return "Tu as déjà ce pack !";
    case 404:
      return "Ce pack n'est plus disponible.";
    case 400:
      return "Choisis d'abord un profil enfant pour demander un pack.";
    default:
      return "Oups, ça n'a pas marché. Réessaie dans un instant !";
  }
}

const REQUEST_STATUS_LABEL: Record<string, string> = {
  pending: "En attente d'un adulte ⏳",
  approved: "C'est oui ! 🎉 Va voir dans Jouer",
  declined: "Pas cette fois 🙂",
};

function Loader() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
    </div>
  );
}

export default function DecouvrirPage() {
  const actingRole = useActingRole();
  const queryClient = useQueryClient();
  const [flourishId, setFlourishId] = useState<string | null>(null);
  const [justRequested, setJustRequested] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pendingId, setPendingId] = useState<string | null>(null);

  // « Découvrir » est une surface d'enfant : un parent sans incarnation est
  // redirigé par le layout, on affiche le loader standard le temps du renvoi.
  const isChild = actingRole === "child";

  const {
    data: packs,
    isLoading,
    error: discoverError,
    isError: discoverFailed,
    refetch,
  } = useDiscover(undefined, { query: { enabled: isChild } });

  const { data: requests } = useMyRequests({ query: { enabled: isChild } });

  const createRequest = useCreateRequest({
    mutation: {
      onMutate: (variables) => {
        setPendingId(variables.data.pack_id);
        setErrors((prev) => {
          const next = { ...prev };
          delete next[variables.data.pack_id];
          return next;
        });
      },
      onSuccess: (_data, variables) => {
        const packId = variables.data.pack_id;
        setJustRequested((prev) =>
          prev.includes(packId) ? prev : [...prev, packId]
        );
        setFlourishId(packId);
        queryClient.invalidateQueries({
          queryKey: getDiscoverApiV1DiscoverGetQueryKey(),
        });
        queryClient.invalidateQueries({
          queryKey: getListRequestsApiV1DiscoverRequestsGetQueryKey(),
        });
      },
      onError: (error, variables) => {
        const packId = variables.data.pack_id;
        const message = requestErrorMessage(error);
        setErrors((prev) => ({ ...prev, [packId]: message }));
        // Un 409 signifie que le pack est déjà là : autant verrouiller la carte.
        if (httpStatus(error) === 409) {
          setJustRequested((prev) =>
            prev.includes(packId) ? prev : [...prev, packId]
          );
        }
      },
      onSettled: () => setPendingId(null),
    },
  });

  if (!actingRole || !isChild) {
    return <Loader />;
  }

  if (isLoading) {
    return <Loader />;
  }

  // 400 : pas d'enfant actif (parent sans profil enfant choisi, ou pas de
  // niveau) — on explique au lieu de laisser une page cassée.
  if (discoverFailed && httpStatus(discoverError) === 400) {
    return (
      <div className="mx-auto max-w-2xl p-6 pb-24 text-center">
        <div className="text-6xl" aria-hidden="true">
          🧭
        </div>
        <h1 className="mt-4 text-3xl font-extrabold text-fun-text">
          Découvrir
        </h1>
        <p className="mt-3 text-base font-semibold text-fun-text-muted">
          Cette page se consulte depuis un profil enfant. Demande à un adulte de
          choisir ton profil pour voir les packs de la communauté.
        </p>
      </div>
    );
  }

  if (discoverFailed) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="font-semibold text-fun-red">
            Impossible de charger les nouveautés
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 min-h-[48px] rounded-xl px-4 font-bold text-fun-sky hover:underline"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const requestedIds = new Set<string>([
    ...justRequested,
    ...(packs ?? []).filter((p) => p.requested).map((p) => p.id),
    ...(requests ?? [])
      .filter((r) => r.status === "pending")
      .map((r) => r.pack_id),
  ]);
  const myRequests: PackRequestResponse[] = requests ?? [];

  return (
    <div className="mx-auto max-w-6xl p-4 pb-24 sm:p-6">
      <div className="mb-6">
        <h1 className="flex items-center gap-2 text-3xl font-extrabold text-fun-text sm:text-4xl">
          <Compass className="h-8 w-8 text-fun-sky" />
          Découvrir
        </h1>
        <p className="mt-2 text-base font-semibold text-fun-text-muted">
          Des leçons créées par d'autres familles. Choisis ce qui te plaît !
        </p>
        <div className="mt-4 rounded-2xl border-2 border-fun-sun bg-fun-sun-light p-4">
          <p className="text-sm font-bold text-fun-text">
            👀 Tu peux regarder tout ce que tu veux. Quand tu appuies sur « Je
            veux ça ! », ça ne s'ouvre pas tout de suite : ça envoie une
            demande. C'est un adulte qui dit oui ou non.
          </p>
        </div>
      </div>

      {(packs ?? []).length === 0 ? (
        <div className="rounded-3xl bg-white p-8 text-center candy-shadow">
          <div className="text-6xl" aria-hidden="true">
            🌱
          </div>
          <p className="mt-4 text-xl font-extrabold text-fun-text">
            Rien de nouveau pour l'instant — reviens bientôt !
          </p>
          <p className="mt-2 text-sm font-semibold text-fun-text-muted">
            D'autres familles préparent de nouvelles leçons.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(packs ?? []).map((pack) => (
            <DiscoverPackCard
              key={pack.id}
              pack={pack}
              requested={requestedIds.has(pack.id)}
              pending={pendingId === pack.id && createRequest.isPending}
              flourish={flourishId === pack.id}
              error={errors[pack.id]}
              onRequest={() =>
                createRequest.mutate({ data: { pack_id: pack.id } })
              }
            />
          ))}
        </div>
      )}

      {myRequests.length > 0 ? (
        <section className="mt-10">
          <h2 className="flex items-center gap-2 text-2xl font-extrabold text-fun-text">
            <Hourglass className="h-6 w-6 text-fun-sun" />
            Mes demandes
          </h2>
          <p className="mt-1 text-sm font-semibold text-fun-text-muted">
            Pas besoin de redemander : un adulte va répondre.
          </p>
          <ul className="mt-4 space-y-3">
            {myRequests.map((request) => (
              <li
                key={request.id}
                className="flex items-center gap-4 rounded-2xl border-2 border-fun-sun bg-white p-4 text-left candy-shadow"
              >
                <span className="text-4xl leading-none" aria-hidden="true">
                  {request.pack_emoji || "📦"}
                </span>
                <div className="min-w-0">
                  <p className="font-extrabold text-fun-text">
                    {request.pack_title}
                  </p>
                  <p className="text-sm font-semibold text-fun-text-muted">
                    {REQUEST_STATUS_LABEL[request.status] ?? request.status}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
