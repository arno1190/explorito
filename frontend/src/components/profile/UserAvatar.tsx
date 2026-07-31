"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { initialsOf, isImageAvatar } from "@/lib/avatars";

/**
 * Avatar d'un utilisateur : image si `avatar` est une URL, emoji s'il en est un,
 * sinon initiales du nom.
 */
export function UserAvatar({
  avatar,
  name,
  className,
  textClassName,
}: {
  avatar?: string | null;
  name?: string | null;
  className?: string;
  textClassName?: string;
}) {
  if (isImageAvatar(avatar)) {
    return (
      <Avatar className={className}>
        <AvatarImage src={avatar!} alt={name ?? ""} />
        <AvatarFallback className="bg-fun-green-light font-bold text-fun-green">
          {initialsOf(name)}
        </AvatarFallback>
      </Avatar>
    );
  }
  return (
    <Avatar className={className}>
      <AvatarFallback
        className={cn(
          "bg-fun-green-light font-bold text-fun-green",
          avatar && "text-xl",
          textClassName
        )}
      >
        {avatar || initialsOf(name)}
      </AvatarFallback>
    </Avatar>
  );
}
