"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { subjectsApi } from "@/lib/api";
import type { Subject } from "@/types";
import {
  BookOpen,
  Palette,
  Calculator,
  Globe,
  Music,
  Dumbbell,
} from "lucide-react";

const iconMap: Record<string, React.ElementType> = {
  book: BookOpen,
  palette: Palette,
  calculator: Calculator,
  globe: Globe,
  music: Music,
  dumbbell: Dumbbell,
};

export default function SubjectsPage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        setLoading(true);
        const data = await subjectsApi.getAll();
        setSubjects(data);
      } catch (err) {
        setError("Impossible de charger les matières");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSubjects();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-[candy-spin-slow_1s_linear_infinite] rounded-full h-12 w-12 border-4 border-fun-green-light border-t-fun-green"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-fun-red font-semibold">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-primary hover:underline"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-fun-text mb-2">Matières</h1>
        <p className="text-fun-text-muted">
          Choisis une matière pour commencer à apprendre
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {subjects.map((subject) => {
          const IconComponent = iconMap[subject.icon] || BookOpen;

          return (
            <Card
              key={subject.id}
              className="p-6 cursor-pointer transition-all rounded-2xl candy-shadow hover:candy-shadow-lg hover:scale-[1.02] border-2"
              style={{ borderColor: subject.color }}
              onClick={() => router.push(`/subjects/${subject.id}`)}
            >
              <div className="flex flex-col items-center text-center gap-4">
                <div
                  className="p-6 rounded-full"
                  style={{ backgroundColor: `${subject.color}20` }}
                >
                  <IconComponent
                    className="h-12 w-12"
                    style={{ color: subject.color }}
                  />
                </div>

                <div>
                  <h2 className="text-2xl font-bold mb-2">{subject.name}</h2>
                  <p className="text-fun-text-muted text-sm">
                    {subject.description}
                  </p>
                </div>

                <div className="mt-2 px-4 py-2 bg-fun-green-light rounded-full text-sm font-semibold text-fun-green">
                  {subject.lesson_count} leçon
                  {subject.lesson_count !== 1 ? "s" : ""}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
