"use client";

import { useAuth } from "@/lib/auth";
import { subjectsApi, gamificationApi } from "@/lib/api";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Subject, GamificationStats } from "@/types";

export default function PlayPage() {
  const { user, impersonatedChild } = useAuth();
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [stats, setStats] = useState<GamificationStats | null>(null);
  const [loading, setLoading] = useState(true);

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
        const subjectsData = await subjectsApi.getAll();
        setSubjects(subjectsData.filter((s) => s.is_active));

        // Load stats separately (non-critical - don't block subjects)
        if (childId) {
          try {
            const statsData = await gamificationApi.getStats(childId);
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
      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-purple-50 p-4">
        {/* Header skeleton */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-white rounded-3xl shadow-lg p-6 flex items-center justify-between">
            <div>
              <div className="h-8 w-48 bg-gray-200 animate-pulse rounded-lg mb-2" />
              <div className="h-5 w-64 bg-gray-200 animate-pulse rounded-lg" />
            </div>
            <div className="flex gap-4">
              <div className="h-16 w-20 bg-yellow-100 animate-pulse rounded-2xl" />
              <div className="h-16 w-20 bg-orange-100 animate-pulse rounded-2xl" />
            </div>
          </div>
        </div>
        {/* Mascot skeleton */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="bg-gradient-to-r from-purple-300 to-pink-300 rounded-3xl shadow-lg p-6 h-28 animate-pulse" />
        </div>
        {/* Subjects grid skeleton */}
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-white rounded-3xl shadow-lg p-8 animate-pulse"
              >
                <div className="h-14 w-14 bg-gray-200 rounded-full mx-auto mb-3" />
                <div className="h-6 w-24 bg-gray-200 rounded-lg mx-auto mb-2" />
                <div className="h-4 w-16 bg-gray-200 rounded-lg mx-auto" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-purple-50 p-4">
      {/* Header with stats */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-white rounded-3xl shadow-lg p-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              🌟 Bonjour {childName}!
            </h1>
            <p className="text-gray-600 mt-1">
              Prêt à apprendre aujourd&apos;hui?
            </p>
          </div>
          <div className="flex gap-4">
            <div className="text-center bg-yellow-100 rounded-2xl px-4 py-2">
              <div className="text-2xl font-bold text-yellow-600">
                ⚡ {stats?.total_xp || 0}
              </div>
              <div className="text-xs text-gray-600">XP</div>
            </div>
            <div className="text-center bg-orange-100 rounded-2xl px-4 py-2">
              <div className="text-2xl font-bold text-orange-600">
                🔥 {stats?.current_streak || 0}
              </div>
              <div className="text-xs text-gray-600">Jours</div>
            </div>
          </div>
        </div>
      </div>

      {/* Mascot/Encouragement */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-gradient-to-r from-purple-400 to-pink-400 rounded-3xl shadow-lg p-6 text-center">
          <div className="text-6xl mb-2">🦉</div>
          <p className="text-white text-xl font-semibold">
            Choisis une matière pour commencer!
          </p>
        </div>
      </div>

      {/* Subjects Grid */}
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {subjects.map((subject) => (
            <button
              key={subject.id}
              onClick={() => router.push(`/subjects/${subject.id}`)}
              className="bg-white rounded-3xl shadow-lg p-8 hover:scale-105 transition-transform active:scale-95"
              style={{ borderColor: subject.color, borderWidth: 4 }}
            >
              <div className="text-6xl mb-3">{subject.icon}</div>
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                {subject.name}
              </h3>
              <div className="flex justify-center gap-1">
                {[1, 2, 3].map((star) => (
                  <span key={star} className="text-2xl">
                    {star <= (subject.lesson_count > 0 ? 1 : 0) ? "⭐" : "☆"}
                  </span>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {subject.lesson_count} leçons
              </p>
            </button>
          ))}
        </div>

        {subjects.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-xl">Aucune matière disponible pour le moment</p>
            <p className="text-sm mt-2">Reviens plus tard!</p>
          </div>
        )}
      </div>

      {/* Recent Badges */}
      {stats && stats.achievements.length > 0 && (
        <div className="max-w-4xl mx-auto mt-8">
          <div className="bg-white rounded-3xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              🏆 Badges récents
            </h2>
            <div className="flex gap-4 overflow-x-auto">
              {stats.achievements.slice(0, 5).map((ua) => (
                <div
                  key={ua.id}
                  className="flex-shrink-0 text-center bg-yellow-50 rounded-2xl p-4 min-w-[100px]"
                >
                  <div className="text-4xl mb-2">{ua.achievement.icon}</div>
                  <p className="text-xs font-semibold text-gray-700">
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
