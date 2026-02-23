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
          !isSelected &&
            !showResult &&
            (value
              ? "border-fun-green hover:bg-fun-green-light"
              : "border-fun-red hover:bg-fun-red-light"),
          // Selected state - very visible!
          isSelected &&
            !showResult &&
            "border-fun-sky bg-fun-sky-light ring-4 ring-fun-sky/20 scale-[1.02] shadow-lg",
          // Correct answer revealed
          isCorrectOption &&
            "border-fun-green bg-fun-green-light ring-4 ring-fun-green/20",
          // Wrong selection revealed
          isWrongSelection &&
            "border-fun-red bg-fun-red-light ring-4 ring-fun-red/20",
          // Disabled
          disabled && "cursor-not-allowed opacity-60"
        )}
        onClick={() => handleSelect(value)}
      >
        {/* Selection indicator badge */}
        {isSelected && !showResult && (
          <div className="absolute -top-3 -right-3 bg-fun-sky rounded-full p-2 shadow-lg">
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
                (value ? "bg-fun-green-light" : "bg-fun-red-light"),
              // Selected icon background - brighter
              isSelected &&
                !showResult &&
                (value ? "bg-fun-green-light" : "bg-fun-red-light"),
              // Result states
              isCorrectOption && "bg-fun-green-light",
              isWrongSelection && "bg-fun-red-light"
            )}
          >
            {icon}
          </div>
          <span
            className={cn(
              "text-2xl font-bold",
              isSelected && !showResult && "text-fun-sky"
            )}
          >
            {label}
          </span>
          {showResult && isCorrectOption && (
            <Check className="h-8 w-8 text-fun-green" />
          )}
          {showResult && isWrongSelection && (
            <X className="h-8 w-8 text-fun-red" />
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-fun-text text-center">
        {question}
      </h2>

      {/* Display statement (the word to evaluate) */}
      {statement && (
        <div className="flex justify-center">
          <div className="bg-fun-sun-light border-2 border-fun-sun rounded-2xl px-12 py-6">
            <span className="text-5xl font-bold text-fun-text tracking-wider">
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
          <ThumbsUp className="h-12 w-12 text-fun-green" />
        )}
        {renderButton(
          false,
          "Faux",
          <ThumbsDown className="h-12 w-12 text-fun-red" />
        )}
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
          {isCorrect ? "Parfait! C'est exact!" : "Non, réessaie!"}
        </div>
      )}
    </div>
  );
}
