const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/**
 * Résout une ressource média servie par le backend. Les chemins relatifs
 * (`/uploads/...`, audio TTS ou pictogrammes) sont préfixés par l'URL de l'API ;
 * les URLs absolues sont renvoyées telles quelles.
 */
export function resolveMediaSrc(path?: string | null): string | undefined {
  if (!path) return undefined;
  return path.startsWith("/") ? `${API_BASE}${path}` : path;
}
