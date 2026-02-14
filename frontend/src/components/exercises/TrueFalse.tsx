"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X, ThumbsUp, ThumbsDown } from "lucide-react";
import Image from "next/image";

interface TrueFalseProps {
  question: string;
  statement?: string; // The word/text to evaluate
  image?: string; // Optional image to display
  onAnswer: (answer: boolean) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
  correctAnswer?: boolean;
}

export function TrueFalse({
  question,
  statement,
  image,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
  correctAnswer,
}: TrueFalseProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<boolean | null>(null);

  const handleSelect = (answer: boolean) => {
    if (disabled) return;
    setSelectedAnswer(answer);
    onAnswer(answer);
  };

  const renderButton = (
    value: boolean,
    label: string,
    icon: React.ReactElement
  ) => {
    const isSelected = selectedAnswer === value;
    const isCorrectOption = showResult && correctAnswer === value;
    const isWrongSelection = showResult && isSelected && !isCorrect;

    return (
      <Card
        className={cn(
          "p-8 cursor-pointer transition-all border-4 relative",
          "hover:shadow-lg hover:scale-[1.02]",
          // Default state
          !isSelected && !showResult && "border-gray-200 hover:border-blue-400",
          // Selected state - very visible!
          isSelected &&
            !showResult &&
            "border-blue-500 bg-blue-50 ring-4 ring-blue-200 scale-[1.02] shadow-lg",
          // Correct answer revealed
          isCorrectOption &&
            "border-green-500 bg-green-50 ring-4 ring-green-200",
          // Wrong selection revealed
          isWrongSelection && "border-red-500 bg-red-50 ring-4 ring-red-200",
          // Disabled
          disabled && "cursor-not-allowed opacity-60"
        )}
        onClick={() => handleSelect(value)}
      >
        {/* Selection indicator badge */}
        {isSelected && !showResult && (
          <div className="absolute -top-3 -right-3 bg-blue-500 rounded-full p-2 shadow-lg">
            <Check className="h-5 w-5 text-white" />
          </div>
        )}
        <div className="flex flex-col items-center gap-4">
          <div
            className={cn(
              "p-4 rounded-full transition-all",
              // Default icon background
              !isSelected &&
                !showResult &&
                (value ? "bg-green-100" : "bg-red-100"),
              // Selected icon background - brighter
              isSelected &&
                !showResult &&
                (value ? "bg-green-200" : "bg-red-200"),
              // Result states
              isCorrectOption && "bg-green-200",
              isWrongSelection && "bg-red-200"
            )}
          >
            {icon}
          </div>
          <span
            className={cn(
              "text-2xl font-bold",
              isSelected && !showResult && "text-blue-700"
            )}
          >
            {label}
          </span>
          {showResult && isCorrectOption && (
            <Check className="h-8 w-8 text-green-600" />
          )}
          {showResult && isWrongSelection && (
            <X className="h-8 w-8 text-red-600" />
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-gray-900 text-center">
        {question}
      </h2>

      {/* Display statement (the word to evaluate) */}
      {statement && (
        <div className="flex justify-center">
          <div className="bg-yellow-100 border-4 border-yellow-400 rounded-xl px-12 py-6">
            <span className="text-5xl font-bold text-gray-900 tracking-wider">
              {statement}
            </span>
          </div>
        </div>
      )}

      {/* Display image if provided */}
      {image && (
        <div className="flex justify-center">
          <div className="relative w-64 h-48 rounded-lg overflow-hidden shadow-lg">
            <Image
              src={image}
              alt="Image de l'exercice"
              fill
              className="object-contain"
              unoptimized
            />
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {renderButton(
          true,
          "Vrai",
          <ThumbsUp className="h-12 w-12 text-green-600" />
        )}
        {renderButton(
          false,
          "Faux",
          <ThumbsDown className="h-12 w-12 text-red-600" />
        )}
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
          {isCorrect ? "Parfait! C'est exact!" : "Non, réessaie!"}
        </div>
      )}
    </div>
  );
}
