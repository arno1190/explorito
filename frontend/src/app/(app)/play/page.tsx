"use client";

import { useAuth } from "@/lib/auth";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listSubjectsApiV1SubjectsGet } from "@/lib/api/generated/subjects/subjects";
import { useRecentLessonsApiV1LessonsRecentGet as useRecentLessons } from "@/lib/api/generated/lessons/lessons";
import { getChildStatsApiV1GamificationChildIdStatsGet } from "@/lib/api/generated/gamification/gamification";
import type { ChildStatsResponse, SubjectResponse } from "@/lib/api/model";

export default function PlayPage() {
  const { user, impersonatedChild } = useAuth();
  const router = useRouter();
  const [subjects, setSubjects] = useState<SubjectResponse[]>([]);
  const [stats, setStats] = useState<ChildStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const { data: recent } = useRecentLessons({ limit: 6 });

  // Determine the child ID - either from impersonation or the logged-in user
  // IMPORTANT: If user is a child, ALWAYS use their own ID (not impersonation)
  const childId =
    user?.role === "child" ? user.id : impersonatedChild?.id || null;
  const childName =
    user?.role === "child"
      ? user.profile?.display_name || "Explorer"
      : impersonatedChild?.name || "Explorer";

  useEffect(() => {
    if (user && user.role !== "child" && !impersonatedChild) {
      // Only allow child role or impersonated parent
      router.push("/dashboard");
      return;
    }

    const loadData = async () => {
      try {
        // Load subjects first (critical for the page)
        const subjectsData = await listSubjectsApiV1SubjectsGet();
        setSubjects(subjectsData.filter((s) => s.is_active));

        // Load stats separately (non-critical - don't block subjects)
        if (childId) {
          try {
            const statsData =
              await getChildStatsApiV1GamificationChildIdStatsGet(childId);
            setStats(statsData);
          } catch (statsError) {
            console.warn("Failed to load stats (non-critical):", statsError);
            // Don't block the page - show default stats
            setStats(null);
          }
        }
      } catch (error) {
        console.error("Failed to load subjects:", error);
        // Even if subjects fail, show the page with empty state
      } finally {
        setLoading(false);
      }
    };

    if (childId || user?.role === "child") {
      loadData();
    }
  }, [user, impersonatedChild, router, childId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
        {/* Header skeleton */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-white rounded-3xl candy-shadow p-6 flex items-center justify-between">
            <div>
              <div className="h-8 w-48 bg-fun-green-light animate-pulse rounded-lg mb-2" />
              <div className="h-5 w-64 bg-fun-green-light animate-pulse rounded-lg" />
            </div>
            <div className="flex gap-4">
              <div className="h-16 w-20 bg-fun-sun-light animate-pulse rounded-2xl" />
              <div className="h-16 w-20 bg-fun-sun-light animate-pulse rounded-2xl" />
            </div>
          </div>
        </div>
        {/* Mascot skeleton */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-gradient-to-r from-fun-green to-fun-sky rounded-3xl candy-shadow p-6 h-28 animate-pulse" />
        </div>
        {/* Subjects grid skeleton */}
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-white rounded-3xl candy-shadow p-8 animate-pulse"
              >
                <div className="h-14 w-14 bg-fun-green-light rounded-full mx-auto mb-3" />
                <div className="h-6 w-24 bg-fun-green-light rounded-lg mx-auto mb-2" />
                <div className="h-4 w-16 bg-fun-green-light rounded-lg mx-auto" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-fun-sky-light via-white to-fun-violet-light p-4">
      {/* Header with stats */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-white rounded-3xl candy-shadow p-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-fun-text">
              🌟 Bonjour {childName}!
            </h1>
            <p className="text-fun-text-muted mt-1">
              Prêt à apprendre aujourd&apos;hui?
            </p>
          </div>
          <div className="flex gap-4">
            <div className="text-center bg-fun-sun-light rounded-2xl px-4 py-2">
              <div className="text-2xl font-bold text-fun-sun">
                ⚡ {stats?.total_xp || 0}
              </div>
              <div className="text-xs text-fun-text-muted">XP</div>
            </div>
            <div className="text-center bg-fun-sun-light rounded-2xl px-4 py-2">
              <div className="text-2xl font-bold text-fun-sun">
                🔥 {stats?.current_streak || 0}
              </div>
              <div className="text-xs text-fun-text-muted">Jours</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mascot/Encouragement */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-gradient-to-r from-fun-green to-fun-sky rounded-3xl candy-shadow p-6 text-center">
          <div className="text-6xl mb-2">🦉</div>
          <p className="text-white text-xl font-semibold">
            Choisis une matière pour commencer!
          </p>
        </div>
      </div>

      {/* Nouveautés — leçons récemment ajoutées */}
      {recent && recent.length > 0 && (
        <div className="max-w-4xl mx-auto mb-8">
          <h2 className="text-2xl font-bold text-fun-text mb-3">
            ✨ Nouveautés
          </h2>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {recent.map((lz) => (
              <button
                key={lz.id}
                onClick={() => !lz.locked && router.push(`/lessons/${lz.id}`)}
                disabled={lz.locked}
                className={`w-44 flex-shrink-0 rounded-2xl border-2 bg-white p-4 text-left candy-shadow transition-all ${
                  lz.locked
                    ? "cursor-not-allowed opacity-60"
                    : "hover:scale-[1.02] hover:candy-shadow-lg"
                }`}
                style={{ borderColor: lz.subject_color ?? undefined }}
              >
                <div className="mb-2 text-4xl">
                  {lz.locked ? "🔒" : lz.subject_icon}
                </div>
                <div className="text-xs font-semibold text-fun-text-muted">
                  {lz.subject_name}
                </div>
                <div className="font-bold leading-tight text-fun-text">
                  {lz.name}
                </div>
                {lz.locked ? (
                  <div className="mt-2 inline-block rounded-full bg-fun-border px-2 py-0.5 text-xs font-bold text-fun-text-muted">
                    À débloquer
                  </div>
                ) : (
                  <div className="mt-2 inline-block rounded-full bg-fun-violet-light px-2 py-0.5 text-xs font-bold text-fun-violet">
                    Nouveau
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Subjects Grid */}
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {subjects.map((subject) => (
            <button
              key={subject.id}
              onClick={() => router.push(`/subjects/${subject.id}`)}
              className="bg-white rounded-3xl candy-shadow hover:candy-shadow-lg p-8 hover:scale-105 transition-transform active:scale-95"
              style={{
                borderColor: subject.color ?? undefined,
                borderWidth: 4,
              }}
            >
              <div className="text-6xl mb-3">{subject.icon}</div>
              <h3 className="text-xl font-bold text-fun-text mb-2">
                {subject.name}
              </h3>
              <div className="flex justify-center gap-1">
                {[1, 2, 3].map((star) => (
                  <span key={star} className="text-2xl">
                    {star <= ((subject.lesson_count ?? 0) > 0 ? 1 : 0)
                      ? "⭐"
                      : "☆"}
                  </span>
                ))}
              </div>
              <p className="text-sm text-fun-text-muted mt-2">
                {subject.lesson_count ?? 0} leçons
              </p>
            </button>
          ))}
        </div>

        {subjects.length === 0 && (
          <div className="text-center text-fun-text-muted mt-8">
            <p className="text-xl">Aucune matière disponible pour le moment</p>
            <p className="text-sm mt-2">Reviens plus tard!</p>
          </div>
        )}
      </div>

      {/* Recent Badges */}
      {stats && (stats.achievements?.length ?? 0) > 0 && (
        <div className="max-w-4xl mx-auto mt-8">
          <div className="bg-white rounded-3xl candy-shadow p-6">
            <h2 className="text-2xl font-bold text-fun-text mb-4">
              🏆 Badges récents
            </h2>
            <div className="flex gap-4 overflow-x-auto">
              {(stats.achievements ?? []).slice(0, 5).map((ua) => (
                <div
                  key={ua.id}
                  className="flex-shrink-0 text-center bg-fun-sun-light rounded-2xl p-4 min-w-[100px]"
                >
                  <div className="text-4xl mb-2">{ua.achievement.icon}</div>
                  <p className="text-xs font-semibold text-fun-text">
                    {ua.achievement.name}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
