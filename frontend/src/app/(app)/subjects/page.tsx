"use client";

import { useRouter } from "next/navigation";
import { BookOpen } from "lucide-react";

import { Card } from "@/components/ui/card";
import { useListSubjectsApiV1SubjectsGet as useSubjects } from "@/lib/api/generated/subjects/subjects";

export default function SubjectsPage() {
  const router = useRouter();
  const { data: subjects, isLoading, isError, refetch } = useSubjects();

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-12 w-12 animate-[candy-spin-slow_1s_linear_infinite] rounded-full border-4 border-fun-green-light border-t-fun-green" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="font-semibold text-fun-red">
            Impossible de charger les matières
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 text-fun-sky hover:underline"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl p-6 pb-24">
      <div className="mb-8">
        <h1 className="mb-2 text-4xl font-extrabold text-fun-text">Matières</h1>
        <p className="text-fun-text-muted">
          Choisis une matière pour commencer à apprendre
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {(subjects ?? []).map((subject) => (
          <Card
            key={subject.id}
            className="cursor-pointer rounded-2xl border-2 candy-shadow transition-all hover:scale-[1.02] hover:candy-shadow-lg"
            style={{ borderColor: subject.color ?? undefined }}
            onClick={() => router.push(`/subjects/${subject.id}`)}
          >
            <div className="flex flex-col items-center gap-4 p-6 text-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-fun-sky-light text-4xl">
                {subject.icon ?? (
                  <BookOpen className="h-10 w-10 text-fun-sky" />
                )}
              </div>
              <div>
                <h2 className="mb-2 text-2xl font-bold text-fun-text">
                  {subject.name}
                </h2>
                <p className="text-sm text-fun-text-muted">
                  {subject.description}
                </p>
              </div>
              <div className="rounded-full bg-fun-green-light px-4 py-2 text-sm font-semibold text-fun-green-dark">
                {subject.lesson_count ?? 0} leçon
                {(subject.lesson_count ?? 0) !== 1 ? "s" : ""}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
