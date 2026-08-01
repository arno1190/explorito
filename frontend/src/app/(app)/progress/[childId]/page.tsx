"use client";

import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, CheckCircle, BookOpen, XCircle } from "lucide-react";

import { useGetChildHistoryApiV1GamificationChildIdHistoryGet as useHistory } from "@/lib/api/generated/gamification/gamification";
import { useGetChildApiV1ChildrenChildIdGet as useChild } from "@/lib/api/generated/children/children";
import { UserAvatar } from "@/components/profile/UserAvatar";

function frDate(iso?: string | null, withTime = false): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

export default function ChildProgressPage() {
  const router = useRouter();
  const params = useParams();
  const childId = params.childId as string;

  const historyQuery = useHistory(childId);
  const childQuery = useChild(childId);
  const history = historyQuery.data;
  const child = childQuery.data;

  if (historyQuery.isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  const daily = history?.daily ?? [];
  const lessons = history?.lessons ?? [];
  const errors = history?.errors ?? [];
  const bySubject = history?.by_subject ?? [];
  const maxEx = Math.max(1, ...daily.map((d) => d.exercises));

  return (
    <div className="container mx-auto max-w-4xl space-y-6 p-4 pb-24 sm:p-6">
      <button
        onClick={() => router.push("/dashboard")}
        className="inline-flex items-center gap-1 font-semibold text-fun-text-muted hover:text-fun-green"
      >
        <ChevronLeft className="h-5 w-5" /> Tableau de bord
      </button>

      <div className="flex items-center gap-3">
        <UserAvatar
          avatar={child?.avatar_url}
          name={child?.name}
          className="h-12 w-12"
          textClassName="text-2xl"
        />
        <h1 className="text-3xl font-extrabold text-fun-text">
          Progrès de {child?.name ?? "l'enfant"}
        </h1>
      </div>

      {/* Résumé quotidien + activité (14 derniers jours) */}
      <section className="rounded-3xl bg-white p-6 candy-shadow">
        <h2 className="mb-4 text-xl font-extrabold text-fun-text">
          📅 Activité (14 derniers jours)
        </h2>
        {daily.length === 0 ? (
          <p className="text-fun-text-muted">Pas encore d'activité.</p>
        ) : (
          <>
            <div className="flex items-end gap-2 overflow-x-auto pb-2">
              {daily.map((d) => {
                const h = (d.exercises / maxEx) * 100;
                const okH = d.exercises ? (d.correct / d.exercises) * h : 0;
                return (
                  <div
                    key={d.date}
                    className="flex min-w-[34px] flex-1 flex-col items-center gap-1"
                    title={`${d.exercises} exercices · ${d.correct} justes · ${d.minutes} min`}
                  >
                    <div className="flex h-28 w-6 flex-col justify-end overflow-hidden rounded-lg bg-fun-border/40">
                      <div
                        className="w-full bg-fun-red"
                        style={{ height: `${h - okH}%` }}
                      />
                      <div
                        className="w-full bg-fun-green"
                        style={{ height: `${okH}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-semibold text-fun-text-muted">
                      {frDate(d.date)}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="mt-3 flex flex-wrap gap-4 text-sm font-semibold text-fun-text-muted">
              <span>
                <span className="mr-1 inline-block h-3 w-3 rounded bg-fun-green align-middle" />
                Justes
              </span>
              <span>
                <span className="mr-1 inline-block h-3 w-3 rounded bg-fun-red align-middle" />
                Erreurs
              </span>
            </div>
            {/* Détail chiffré */}
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-fun-text-muted">
                  <tr>
                    <th className="py-1 pr-4">Jour</th>
                    <th className="py-1 pr-4">Leçons</th>
                    <th className="py-1 pr-4">Exercices</th>
                    <th className="py-1 pr-4">Réussite</th>
                    <th className="py-1">Temps</th>
                  </tr>
                </thead>
                <tbody className="font-semibold text-fun-text">
                  {[...daily].reverse().map((d) => (
                    <tr key={d.date} className="border-t border-fun-border">
                      <td className="py-1 pr-4">{frDate(d.date)}</td>
                      <td className="py-1 pr-4">{d.lessons_completed}</td>
                      <td className="py-1 pr-4">{d.exercises}</td>
                      <td className="py-1 pr-4">
                        {d.exercises
                          ? Math.round((d.correct / d.exercises) * 100)
                          : 0}
                        %
                      </td>
                      <td className="py-1">{d.minutes} min</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      {/* Réussite par matière */}
      {bySubject.length > 0 && (
        <section className="rounded-3xl bg-white p-6 candy-shadow">
          <h2 className="mb-4 text-xl font-extrabold text-fun-text">
            🎯 Réussite par matière
          </h2>
          <div className="space-y-3">
            {bySubject.map((s) => (
              <div key={s.subject_name}>
                <div className="mb-1 flex justify-between text-sm font-semibold text-fun-text">
                  <span>
                    {s.subject_icon} {s.subject_name}
                  </span>
                  <span className="text-fun-text-muted">
                    {s.accuracy}% · {s.correct}/{s.attempts}
                  </span>
                </div>
                <div className="h-3 w-full overflow-hidden rounded-full bg-fun-red-light">
                  <div
                    className="h-3 rounded-full bg-fun-green transition-all"
                    style={{ width: `${s.accuracy}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Historique des leçons */}
      <section className="rounded-3xl bg-white p-6 candy-shadow">
        <h2 className="mb-4 text-xl font-extrabold text-fun-text">
          📚 Historique des leçons
        </h2>
        {lessons.length === 0 ? (
          <p className="text-fun-text-muted">Aucune leçon commencée.</p>
        ) : (
          <ul className="divide-y divide-fun-border">
            {lessons.map((l) => {
              const done = l.status === "completed";
              return (
                <li
                  key={l.lesson_id + (l.completed_at ?? "")}
                  className="flex items-center gap-3 py-3"
                >
                  {done ? (
                    <CheckCircle className="h-5 w-5 shrink-0 text-fun-green" />
                  ) : (
                    <BookOpen className="h-5 w-5 shrink-0 text-fun-sky" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-bold text-fun-text">
                      {l.subject_icon} {l.lesson_name}
                    </div>
                    <div className="text-xs text-fun-text-muted">
                      {l.subject_name}
                      {l.completed_at && ` · ${frDate(l.completed_at, true)}`}
                      {(l.attempts ?? 0) > 1 && ` · ${l.attempts} essais`}
                    </div>
                  </div>
                  {done && (
                    <div className="shrink-0 text-right text-sm font-bold text-fun-text">
                      {"⭐".repeat(l.stars ?? 0)}
                      <div className="text-xs text-fun-text-muted">
                        {l.score ?? 0}%
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Journal des erreurs */}
      <section className="rounded-3xl bg-white p-6 candy-shadow">
        <h2 className="mb-4 text-xl font-extrabold text-fun-text">
          ✏️ Journal des erreurs
        </h2>
        {errors.length === 0 ? (
          <p className="text-fun-text-muted">
            Aucune erreur récente — bravo&nbsp;! 🎉
          </p>
        ) : (
          <ul className="divide-y divide-fun-border">
            {errors.map((e, i) => (
              <li
                key={e.exercise_id + i}
                className="flex items-start gap-3 py-3"
              >
                <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-fun-red" />
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-fun-text">
                    {e.question}
                  </div>
                  <div className="text-xs text-fun-text-muted">
                    {e.subject_name} · {e.lesson_name} ·{" "}
                    {frDate(e.timestamp, true)}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
