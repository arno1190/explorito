"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X } from "lucide-react";

interface MultipleChoiceProps {
  question: string;
  options: string[];
  onAnswer: (answer: string | string[]) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
  correctAnswer?: string | string[];
  allowMultiple?: boolean; // Allow selecting multiple options
}

export function MultipleChoice({
  question,
  options,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
  correctAnswer,
  allowMultiple = false,
}: MultipleChoiceProps) {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  // Reset selection when component becomes enabled again (retry scenario)
  useEffect(() => {
    if (!disabled && !showResult) {
      setSelectedOptions([]);
    }
  }, [disabled, showResult]);

  const handleSelect = (option: string) => {
    if (disabled) return;

    let newSelection: string[];

    if (allowMultiple) {
      // Toggle selection for multiple choice
      if (selectedOptions.includes(option)) {
        newSelection = selectedOptions.filter((o) => o !== option);
      } else {
        newSelection = [...selectedOptions, option];
      }
    } else {
      // Single selection - replace previous
      newSelection = [option];
    }

    setSelectedOptions(newSelection);

    // Send answer in appropriate format
    if (allowMultiple) {
      onAnswer(newSelection);
    } else {
      onAnswer(newSelection[0] || "");
    }
  };

  const isOptionSelected = (option: string) => selectedOptions.includes(option);

  // Check if an option is a correct answer
  const isCorrectAnswer = (option: string): boolean => {
    if (!correctAnswer) return false;
    if (Array.isArray(correctAnswer)) {
      return correctAnswer.includes(option);
    }
    return correctAnswer === option;
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-candy-text">{question}</h2>

      {allowMultiple && (
        <p className="text-sm text-candy-text-muted italic">
          Plusieurs réponses possibles - sélectionne toutes les bonnes réponses
        </p>
      )}

      <div className="grid gap-4">
        {options.map((option, index) => {
          const isSelected = isOptionSelected(option);
          // When showing results:
          // - If overall answer is correct AND option is selected -> green (user got it right)
          // - If option is a correct answer (show correct answers) -> green
          // - If option is selected but answer is wrong -> red
          const isCorrectOption =
            showResult &&
            (isCorrectAnswer(option) || (isCorrect && isSelected));
          const isWrongSelection =
            showResult && isSelected && !isCorrect && !isCorrectAnswer(option);

          // Letter label (A, B, C, D...)
          const letter = String.fromCharCode(65 + index);

          return (
            <Card
              key={index}
              className={cn(
                "p-0 cursor-pointer transition-all border-3 overflow-hidden",
                "hover:shadow-lg hover:scale-[1.01]",
                // Default state
                !isSelected &&
                  !showResult &&
                  "border-candy-border hover:border-candy-purple/50",
                // Selected state (not showing result yet)
                isSelected &&
                  !showResult &&
                  "border-candy-purple bg-candy-purple-light ring-2 ring-candy-purple/30",
                // Correct answer revealed
                isCorrectOption && "border-candy-green bg-candy-green-light",
                // Wrong selection revealed
                isWrongSelection && "border-candy-red bg-candy-red-light",
                // Disabled
                disabled && "cursor-not-allowed"
              )}
              onClick={() => handleSelect(option)}
            >
              <div className="flex items-stretch">
                {/* Letter Badge */}
                <div
                  className={cn(
                    "w-14 flex items-center justify-center text-xl font-bold transition-all",
                    // Default
                    !isSelected &&
                      !showResult &&
                      "bg-candy-purple-light text-candy-purple",
                    // Selected
                    isSelected && !showResult && "bg-candy-purple text-white",
                    // Correct
                    isCorrectOption && "bg-candy-green text-white",
                    // Wrong
                    isWrongSelection && "bg-candy-red text-white"
                  )}
                >
                  {showResult && isCorrectOption ? (
                    <Check className="h-6 w-6" />
                  ) : showResult && isWrongSelection ? (
                    <X className="h-6 w-6" />
                  ) : (
                    letter
                  )}
                </div>

                {/* Option Text */}
                <div className="flex-grow p-4 flex items-center">
                  <span
                    className={cn(
                      "text-lg font-medium",
                      isSelected && !showResult && "text-candy-purple",
                      isCorrectOption && "text-candy-green",
                      isWrongSelection && "text-candy-red"
                    )}
                  >
                    {option}
                  </span>
                </div>

                {/* Selection indicator on the right */}
                {isSelected && !showResult && (
                  <div className="w-12 flex items-center justify-center bg-candy-purple">
                    <Check className="h-5 w-5 text-white" />
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {showResult && (
        <div
          className={cn(
            "p-4 rounded-lg text-center font-semibold",
            isCorrect
              ? "bg-candy-green-light text-candy-green"
              : "bg-candy-red-light text-candy-red"
          )}
        >
          {isCorrect
            ? "Excellent! C'est la bonne réponse!"
            : "Pas tout à fait, essaie encore!"}
        </div>
      )}
    </div>
  );
}
