"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import {
  getOverviewApiV1AdminOverviewGet,
  getUsersApiV1AdminUsersGet,
  suspendUserApiV1AdminUsersUserIdSuspendPost,
  reactivateUserApiV1AdminUsersUserIdReactivatePost,
  removeUserApiV1AdminUsersUserIdDelete,
} from "@/lib/api/generated/admin/admin";
import type { AdminOverview, AdminUserRow } from "@/lib/api/model";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, Pause, Play, Trash2, Users } from "lucide-react";

function frDate(iso?: string | null, withTime = false): string {
  if (!iso) return "—";
  // Le backend renvoie des dates UTC naïves (sans fuseau) : sans marqueur, le
  // navigateur les interprète comme locales. On force UTC, puis on affiche dans
  // le fuseau du navigateur.
  const hasTz = /[zZ]|[+-]\d{2}:\d{2}$/.test(iso);
  const d = new Date(hasTz ? iso : `${iso}Z`);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  parent: "Parent",
  child: "Enfant",
};

function RoleBadge({ role }: { role: string }) {
  const styles: Record<string, string> = {
    admin: "bg-fun-violet-light text-fun-violet",
    parent: "bg-fun-sky-light text-fun-sky",
    child: "bg-fun-sun-light text-fun-sun",
  };
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${
        styles[role] ?? "bg-fun-border text-fun-text-muted"
      }`}
    >
      {ROLE_LABELS[role] ?? role}
    </span>
  );
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ${
        active
          ? "bg-fun-green-light text-fun-green-dark"
          : "bg-fun-red-light text-fun-red"
      }`}
    >
      {active ? "Actif" : "Suspendu"}
    </span>
  );
}

function StatCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string | number;
  subtext?: string;
}) {
  return (
    <Card className="candy-shadow">
      <CardContent className="p-5">
        <div className="text-sm font-semibold text-fun-text-muted">{label}</div>
        <div className="mt-1 text-3xl font-extrabold text-fun-text">
          {value}
        </div>
        {subtext && (
          <div className="mt-1 text-xs font-semibold text-fun-text-muted">
            {subtext}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  // Suppression : confirmation par saisie (le nom de l'utilisateur ou
  // « SUPPRIMER ») pour éviter les suppressions accidentelles.
  const [deleteTarget, setDeleteTarget] = useState<AdminUserRow | null>(null);
  const [confirmText, setConfirmText] = useState("");

  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace("/dashboard");
    }
  }, [authLoading, isAdmin, router]);

  useEffect(() => {
    if (authLoading || !isAdmin) return;
    let cancelled = false;

    getOverviewApiV1AdminOverviewGet()
      .then((data) => {
        if (!cancelled) setOverview(data);
      })
      .catch((err) => console.error("Failed to load overview:", err))
      .finally(() => {
        if (!cancelled) setOverviewLoading(false);
      });

    getUsersApiV1AdminUsersGet()
      .then((data) => {
        if (!cancelled) setUsers(data);
      })
      .catch((err) => console.error("Failed to load users:", err))
      .finally(() => {
        if (!cancelled) setUsersLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [authLoading, isAdmin]);

  const toggleActive = async (row: AdminUserRow) => {
    setBusyId(row.id);
    try {
      if (row.is_active) {
        await suspendUserApiV1AdminUsersUserIdSuspendPost(row.id);
      } else {
        await reactivateUserApiV1AdminUsersUserIdReactivatePost(row.id);
      }
      setUsers((prev) =>
        prev.map((u) =>
          u.id === row.id ? { ...u, is_active: !row.is_active } : u
        )
      );
    } catch (err) {
      console.error("Failed to toggle user status:", err);
    } finally {
      setBusyId(null);
    }
  };

  const impersonate = (row: AdminUserRow) => {
    localStorage.setItem("impersonate_user", row.id);
    window.location.href = "/dashboard";
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setBusyId(deleteTarget.id);
    try {
      await removeUserApiV1AdminUsersUserIdDelete(deleteTarget.id);
      setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id));
      setDeleteTarget(null);
      setConfirmText("");
    } catch (err) {
      console.error("Failed to delete user:", err);
    } finally {
      setBusyId(null);
    }
  };

  const canConfirmDelete =
    deleteTarget !== null &&
    (confirmText.trim() === deleteTarget.name ||
      confirmText.trim() === "SUPPRIMER");

  if (authLoading || !isAdmin) {
    return null;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-fun-text">
          Administration
        </h1>
        <p className="mt-1 text-fun-text-muted">
          Métriques opérationnelles et gestion des utilisateurs
        </p>
      </div>

      {/* ---- Vue d'ensemble ---- */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-fun-text">Vue d&apos;ensemble</h2>
        {overviewLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
          </div>
        ) : !overview ? (
          <Card className="candy-shadow">
            <CardContent className="py-8 text-center text-fun-text-muted">
              Impossible de charger les métriques.
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
              <StatCard label="Parents" value={overview.parents_total} />
              <StatCard label="Enfants" value={overview.children_total} />
              <StatCard label="Familles" value={overview.families_total} />
              <StatCard
                label="Actifs 7j"
                value={`${overview.active_parents_7d} / ${overview.active_children_7d}`}
                subtext="parents / enfants"
              />
              <StatCard
                label="Actifs 30j"
                value={`${overview.active_parents_30d} / ${overview.active_children_30d}`}
                subtext="parents / enfants"
              />
              <StatCard
                label="Exercices"
                value={overview.exercises_total}
                subtext={`7j: ${overview.exercises_7d} · 30j: ${overview.exercises_30d}`}
              />
            </div>

            <Card className="candy-shadow">
              <CardHeader>
                <CardTitle className="text-base">Activité récente</CardTitle>
              </CardHeader>
              <CardContent>
                {overview.recent_activity.length === 0 ? (
                  <p className="text-sm text-fun-text-muted">
                    Aucune activité récente.
                  </p>
                ) : (
                  <ul className="divide-y divide-fun-border">
                    {overview.recent_activity.map((act, i) => (
                      <li
                        key={`${act.label}-${act.at}-${i}`}
                        className="flex items-center justify-between gap-2 py-2 text-sm"
                      >
                        <span className="flex items-center gap-2">
                          <span aria-hidden>
                            {act.kind === "exercise" ? "✏️" : "🔑"}
                          </span>
                          <span className="font-semibold text-fun-text">
                            {act.label}
                          </span>
                          <span className="text-fun-text-muted">
                            · {act.detail}
                          </span>
                        </span>
                        <span className="shrink-0 text-fun-text-muted">
                          {frDate(act.at, true)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </section>

      {/* ---- Utilisateurs ---- */}
      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-bold text-fun-text">
          <Users className="h-5 w-5" />
          Utilisateurs
        </h2>
        {usersLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
          </div>
        ) : users.length === 0 ? (
          <Card className="candy-shadow">
            <CardContent className="py-8 text-center text-fun-text-muted">
              Aucun utilisateur.
            </CardContent>
          </Card>
        ) : (
          <Card className="candy-shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-fun-border text-left text-xs font-bold uppercase text-fun-text-muted">
                    <th className="px-4 py-3">Nom</th>
                    <th className="px-4 py-3">Email</th>
                    <th className="px-4 py-3">Rôle</th>
                    <th className="px-4 py-3">Statut</th>
                    <th className="px-4 py-3">Dern. connexion</th>
                    <th className="px-4 py-3">Dern. exercice</th>
                    <th className="px-4 py-3 text-right">Exercices</th>
                    <th className="px-4 py-3 text-right">Connexions</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((row) => (
                    <tr
                      key={row.id}
                      className="border-b border-fun-border last:border-0 hover:bg-fun-sky-light/40"
                    >
                      <td className="px-4 py-3 font-semibold text-fun-text">
                        {row.name}
                      </td>
                      <td className="px-4 py-3 text-fun-text-muted">
                        {row.email ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <RoleBadge role={row.role} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusPill active={row.is_active} />
                      </td>
                      <td className="px-4 py-3 text-fun-text-muted">
                        {frDate(row.last_login_at, true)}
                      </td>
                      <td className="px-4 py-3 text-fun-text-muted">
                        {frDate(row.last_exercise_at, true)}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-fun-text">
                        {row.exercises_count ?? 0}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-fun-text">
                        {row.login_count ?? 0}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={busyId === row.id}
                            onClick={() => toggleActive(row)}
                            title={row.is_active ? "Suspendre" : "Réactiver"}
                          >
                            {row.is_active ? (
                              <Pause className="h-4 w-4" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                            <span className="ml-1 hidden lg:inline">
                              {row.is_active ? "Suspendre" : "Réactiver"}
                            </span>
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => impersonate(row)}
                            title="Voir en tant que"
                          >
                            <Eye className="h-4 w-4" />
                            <span className="ml-1 hidden lg:inline">Voir</span>
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            disabled={busyId === row.id}
                            onClick={() => {
                              setDeleteTarget(row);
                              setConfirmText("");
                            }}
                            title="Supprimer"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </section>

      {/* ---- Dialogue de suppression (saisie de confirmation) ---- */}
      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(o) => {
          if (!o) {
            setDeleteTarget(null);
            setConfirmText("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Supprimer l&apos;utilisateur</DialogTitle>
            <DialogDescription>
              Cette action est irréversible. Toutes les données de{" "}
              <span className="font-bold text-fun-text">
                {deleteTarget?.name}
              </span>{" "}
              seront supprimées.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <Label htmlFor="confirm-delete">
              Pour confirmer, saisis{" "}
              <span className="font-bold">{deleteTarget?.name}</span> ou{" "}
              <span className="font-bold">SUPPRIMER</span>
            </Label>
            <Input
              id="confirm-delete"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={deleteTarget?.name}
              autoComplete="off"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteTarget(null);
                setConfirmText("");
              }}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              disabled={!canConfirmDelete || busyId === deleteTarget?.id}
              onClick={confirmDelete}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Supprimer définitivement
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
