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
              "w-32 h-10 text-center inline-block",
              isCorrectAnswer && "border-green-500 bg-green-50",
              isWrongAnswer && "border-red-500 bg-red-50"
            )}
            placeholder="..."
          />
          {showResult && isCorrectAnswer && (
            <Check className="h-4 w-4 text-green-600 ml-1" />
          )}
          {showResult && isWrongAnswer && (
            <X className="h-4 w-4 text-red-600 ml-1" />
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
      <h2 className="text-2xl font-bold text-gray-900">{question}</h2>

      <div className="bg-white p-6 rounded-lg border-2 border-gray-200">
        <div className="text-lg leading-relaxed">{renderTextWithBlanks()}</div>
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
            ? "Bravo! Toutes les réponses sont correctes!"
            : "Quelques réponses sont incorrectes!"}
        </div>
      )}

      {showResult && !isCorrect && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="font-semibold text-blue-900 mb-2">
            Réponses correctes:
          </p>
          <ul className="list-disc list-inside space-y-1">
            {blanks.map((blank, index) => (
              <li key={index} className="text-blue-800">
                Position {index + 1}: {blank.answer}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
