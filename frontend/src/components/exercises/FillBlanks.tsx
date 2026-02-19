"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Check, X } from "lucide-react";

interface FillBlanksProps {
  question: string;
  text: string;
  blanks: Array<{ position: number; answer: string }>;
  onAnswer: (answers: string[]) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
}

export function FillBlanks({
  question,
  text,
  blanks,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
}: FillBlanksProps) {
  const [answers, setAnswers] = useState<string[]>(
    new Array(blanks.length).fill("")
  );

  const handleAnswerChange = (index: number, value: string) => {
    if (disabled) return;
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
    onAnswer(newAnswers);
  };

  // Split text into parts and insert blanks
  const renderTextWithBlanks = () => {
    const parts: React.ReactElement[] = [];
    let lastPosition = 0;
    const sortedBlanks = [...blanks].sort((a, b) => a.position - b.position);

    sortedBlanks.forEach((blank, index) => {
      // Add text before the blank
      if (blank.position > lastPosition) {
        parts.push(
          <span key={`text-${index}`}>
            {text.substring(lastPosition, blank.position)}
          </span>
        );
      }

      // Add the blank input
      const isCorrectAnswer =
        showResult &&
        answers[index]?.toLowerCase().trim() ===
          blank.answer.toLowerCase().trim();
      const isWrongAnswer =
        showResult &&
        answers[index] &&
        answers[index]?.toLowerCase().trim() !==
          blank.answer.toLowerCase().trim();

      parts.push(
        <span key={`blank-${index}`} className="inline-flex items-center mx-1">
          <Input
            type="text"
            value={answers[index]}
            onChange={(e) => handleAnswerChange(index, e.target.value)}
            disabled={disabled}
            className={cn(
              "w-24 sm:w-32 h-10 text-center inline-block border-2 border-candy-purple/30 rounded-lg focus:border-candy-purple focus:ring-2 focus:ring-candy-purple/20",
              isCorrectAnswer && "border-candy-green bg-candy-green-light",
              isWrongAnswer && "border-candy-red bg-candy-red-light"
            )}
            placeholder="..."
          />
          {showResult && isCorrectAnswer && (
            <Check className="h-4 w-4 text-candy-green ml-1" />
          )}
          {showResult && isWrongAnswer && (
            <X className="h-4 w-4 text-candy-red ml-1" />
          )}
        </span>
      );

      lastPosition = blank.position;
    });

    // Add remaining text
    if (lastPosition < text.length) {
      parts.push(<span key="text-end">{text.substring(lastPosition)}</span>);
    }

    return parts;
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-candy-text">{question}</h2>

      <div className="bg-white p-6 rounded-lg border-2 border-candy-border">
        <div className="text-lg leading-relaxed">{renderTextWithBlanks()}</div>
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
            ? "Bravo! Toutes les réponses sont correctes!"
            : "Quelques réponses sont incorrectes!"}
        </div>
      )}

      {showResult && !isCorrect && (
        <div className="bg-candy-purple-light p-4 rounded-lg">
          <p className="font-semibold text-candy-text mb-2">
            Réponses correctes:
          </p>
          <ul className="list-disc list-inside space-y-1">
            {blanks.map((blank, index) => (
              <li key={index} className="text-candy-text">
                Position {index + 1}: {blank.answer}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
