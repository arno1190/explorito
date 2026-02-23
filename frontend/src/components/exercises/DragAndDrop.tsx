"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X, GripVertical } from "lucide-react";

interface DragAndDropProps {
  question: string;
  items: Array<{ id: string; text: string }>;
  targets: Array<{ id: string; text: string }>;
  onAnswer: (matches: Record<string, string>) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
  correctMatches?: Record<string, string>;
}

export function DragAndDrop({
  question,
  items,
  targets,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
  correctMatches,
}: DragAndDropProps) {
  const [matches, setMatches] = useState<Record<string, string>>({});
  const [draggedItem, setDraggedItem] = useState<string | null>(null);

  const handleDragStart = (itemId: string) => {
    if (disabled) return;
    setDraggedItem(itemId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (targetId: string) => {
    if (!draggedItem || disabled) return;

    const newMatches = { ...matches, [draggedItem]: targetId };
    setMatches(newMatches);
    setDraggedItem(null);
    onAnswer(newMatches);
  };

  const getItemsForTarget = (targetId: string) => {
    return Object.entries(matches)
      .filter(([, target]) => target === targetId)
      .map(([itemId]) => items.find((item) => item.id === itemId)!);
  };

  const getUnmatchedItems = () => {
    return items.filter((item) => !matches[item.id]);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-fun-text">{question}</h2>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Items Pool */}
        <Card className="p-6 bg-fun-sky-light rounded-2xl">
          <h3 className="font-semibold mb-4 text-fun-text">
            Éléments à déplacer
          </h3>
          <div className="space-y-2">
            {getUnmatchedItems().map((item) => (
              <Card
                key={item.id}
                draggable={!disabled}
                onDragStart={() => handleDragStart(item.id)}
                className={cn(
                  "p-3 cursor-move transition-all",
                  "hover:shadow-md hover:scale-[1.02]",
                  "bg-white border-fun-border rounded-xl candy-shadow",
                  disabled && "cursor-not-allowed opacity-60"
                )}
              >
                <div className="flex items-center gap-2">
                  <GripVertical className="h-4 w-4 text-fun-text-muted" />
                  <span>{item.text}</span>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        {/* Target Zones */}
        <div className="space-y-3">
          <h3 className="font-semibold text-fun-text">Zones cibles</h3>
          {targets.map((target) => {
            const itemsInTarget = getItemsForTarget(target.id);
            const isCorrectTarget =
              showResult &&
              correctMatches &&
              itemsInTarget.every(
                (item) => correctMatches[item.id] === target.id
              );
            const hasWrongItems =
              showResult &&
              correctMatches &&
              itemsInTarget.some(
                (item) => correctMatches[item.id] !== target.id
              );

            return (
              <Card
                key={target.id}
                onDragOver={handleDragOver}
                onDrop={() => handleDrop(target.id)}
                className={cn(
                  "p-4 min-h-[100px] border-2 border-dashed transition-all rounded-2xl",
                  "border-fun-border bg-fun-surface",
                  !disabled && "hover:border-fun-sky hover:bg-fun-sky-light/50",
                  isCorrectTarget && "border-fun-green bg-fun-green-light",
                  hasWrongItems && "border-fun-red bg-fun-red-light"
                )}
              >
                <div className="font-medium text-sm text-fun-text-muted mb-2">
                  {target.text}
                </div>
                <div className="space-y-2">
                  {itemsInTarget.map((item) => {
                    const isCorrectlyPlaced =
                      showResult &&
                      correctMatches &&
                      correctMatches[item.id] === target.id;
                    const isWronglyPlaced =
                      showResult &&
                      correctMatches &&
                      correctMatches[item.id] !== target.id;

                    return (
                      <Card
                        key={item.id}
                        className={cn(
                          "p-2 bg-white border-2",
                          isCorrectlyPlaced && "border-fun-green",
                          isWronglyPlaced && "border-fun-red"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{item.text}</span>
                          {isCorrectlyPlaced && (
                            <Check className="h-4 w-4 text-fun-green" />
                          )}
                          {isWronglyPlaced && (
                            <X className="h-4 w-4 text-fun-red" />
                          )}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {showResult && (
        <div
          className={cn(
            "p-4 rounded-lg text-center font-semibold",
            isCorrect
              ? "bg-fun-green-light text-fun-green"
              : "bg-fun-red-light text-fun-red"
          )}
        >
          {isCorrect
            ? "Super! Tous les éléments sont bien placés!"
            : "Certains éléments ne sont pas au bon endroit!"}
        </div>
      )}
    </div>
  );
}
