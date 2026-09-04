/**
 * Le code d'appairage se lit à voix haute : on l'affiche en deux groupes de
 * quatre pour éviter qu'un parent perde sa place au milieu des huit caractères.
 * L'API accepte ensuite n'importe quelle casse, espace ou tiret.
 */
export function formatPairingCode(code: string): string {
  const clean = code.replace(/[\s-]/g, "").toUpperCase();
  return clean.length === 8 ? `${clean.slice(0, 4)}-${clean.slice(4)}` : clean;
}

/** Compte à rebours en mm:ss, borné à zéro. */
export function formatCountdown(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

/** Phrase à dicter à l'assistant, code compris. */
export function pairingSentence(code: string): string {
  return `Connecte-toi à Explorito avec le code ${formatPairingCode(code)}, puis fais-moi un pack sur les dinosaures pour un CE1.`;
}
