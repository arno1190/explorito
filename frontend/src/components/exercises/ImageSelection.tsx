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
      <h2 className="text-2xl font-bold text-fun-text text-center">
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
                "relative overflow-hidden cursor-pointer transition-all border-2 rounded-2xl candy-shadow",
                "hover:shadow-xl hover:scale-[1.05]",
                !disabled && "hover:border-fun-sky/50",
                !isSelected && !showResult && "border-fun-border",
                isSelected &&
                  !showResult &&
                  "border-fun-sky ring-2 ring-fun-sky/30",
                isCorrectImage && "border-fun-green",
                isWrongSelection && "border-fun-red",
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
                  <div className="absolute inset-0 bg-fun-green/20 flex items-center justify-center">
                    <div className="bg-fun-green rounded-full p-3">
                      <Check className="h-8 w-8 text-white" />
                    </div>
                  </div>
                )}
                {showResult && isWrongSelection && (
                  <div className="absolute inset-0 bg-fun-red/20 flex items-center justify-center">
                    <div className="bg-fun-red rounded-full p-3">
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
              ? "bg-fun-green-light text-fun-green"
              : "bg-fun-red-light text-fun-red"
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
