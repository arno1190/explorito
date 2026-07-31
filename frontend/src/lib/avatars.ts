/** Avatars proposés (emoji) — adaptés aux enfants, sans upload ni modération. */
export const AVATAR_OPTIONS = [
  "🦊",
  "🐼",
  "🐸",
  "🐧",
  "🦁",
  "🐯",
  "🐨",
  "🐰",
  "🐶",
  "🐱",
  "🦄",
  "🐲",
  "🦉",
  "🐢",
  "🦕",
  "🐙",
  "🐝",
  "🦋",
  "🐬",
  "🐳",
  "🦖",
  "🐹",
  "🐮",
  "🐷",
] as const;

/** Un avatar stocké est une URL d'image si c'est un chemin/URL, sinon un emoji. */
export function isImageAvatar(avatar?: string | null): boolean {
  return !!avatar && (avatar.startsWith("http") || avatar.startsWith("/"));
}

export function initialsOf(name?: string | null): string {
  if (!name) return "U";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}
