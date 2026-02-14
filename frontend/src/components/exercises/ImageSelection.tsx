"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check, X } from "lucide-react";

interface ImageSelectionProps {
  question: string;
  images: Array<{ id: string; url: string; alt: string }>;
  onAnswer: (imageId: string) => void;
  disabled?: boolean;
  showResult?: boolean;
  isCorrect?: boolean;
  correctImageId?: string;
}

export function ImageSelection({
  question,
  images,
  onAnswer,
  disabled = false,
  showResult = false,
  isCorrect,
  correctImageId,
}: ImageSelectionProps) {
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);

  const handleSelect = (imageId: string) => {
    if (disabled) return;
    setSelectedImageId(imageId);
    onAnswer(imageId);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 text-center">
        {question}
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {images.map((image) => {
          const isSelected = selectedImageId === image.id;
          const isCorrectImage = showResult && correctImageId === image.id;
          const isWrongSelection = showResult && isSelected && !isCorrect;

          return (
            <Card
              key={image.id}
              className={cn(
                "relative overflow-hidden cursor-pointer transition-all border-4",
                "hover:shadow-xl hover:scale-[1.05]",
                !disabled && "hover:border-primary",
                isSelected && !showResult && "border-primary",
                isCorrectImage && "border-green-500",
                isWrongSelection && "border-red-500",
                disabled && "cursor-not-allowed opacity-60"
              )}
              onClick={() => handleSelect(image.id)}
            >
              <div className="aspect-square relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={image.url}
                  alt={image.alt}
                  className="absolute inset-0 w-full h-full object-cover"
                  onError={(e) => {
                    // Fallback to placeholder if image fails to load
                    (e.target as HTMLImageElement).src =
                      "/placeholder-image.png";
                  }}
                />
                {showResult && isCorrectImage && (
                  <div className="absolute inset-0 bg-green-500/20 flex items-center justify-center">
                    <div className="bg-green-500 rounded-full p-3">
                      <Check className="h-8 w-8 text-white" />
                    </div>
                  </div>
                )}
                {showResult && isWrongSelection && (
                  <div className="absolute inset-0 bg-red-500/20 flex items-center justify-center">
                    <div className="bg-red-500 rounded-full p-3">
                      <X className="h-8 w-8 text-white" />
                    </div>
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
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          )}
        >
          {isCorrect
            ? "Génial! C'est la bonne image!"
            : "Non, essaie une autre image!"}
        </div>
      )}
    </div>
  );
}
