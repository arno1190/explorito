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
      <h2 className="text-2xl font-bold text-gray-900">{question}</h2>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Items Pool */}
        <Card className="p-6 bg-blue-50">
          <h3 className="font-semibold mb-4 text-blue-900">
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
                  "bg-white border-2 border-blue-200",
                  disabled && "cursor-not-allowed opacity-60"
                )}
              >
                <div className="flex items-center gap-2">
                  <GripVertical className="h-4 w-4 text-gray-400" />
                  <span>{item.text}</span>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        {/* Target Zones */}
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-900">Zones cibles</h3>
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
                  "p-4 min-h-[100px] border-2 border-dashed transition-all",
                  "border-gray-300 bg-gray-50",
                  !disabled && "hover:border-primary hover:bg-primary/5",
                  isCorrectTarget && "border-green-500 bg-green-50",
                  hasWrongItems && "border-red-500 bg-red-50"
                )}
              >
                <div className="font-medium text-sm text-gray-600 mb-2">
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
                          isCorrectlyPlaced && "border-green-500",
                          isWronglyPlaced && "border-red-500"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{item.text}</span>
                          {isCorrectlyPlaced && (
                            <Check className="h-4 w-4 text-green-600" />
                          )}
                          {isWronglyPlaced && (
                            <X className="h-4 w-4 text-red-600" />
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
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
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
