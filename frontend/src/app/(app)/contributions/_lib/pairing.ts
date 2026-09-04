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

/**
 * Base de l'API, comme `src/lib/api/axios-instance.ts` : même variable, même
 * repli, pour que la phrase copiée désigne l'instance réellement utilisée.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

/**
 * Mode d'emploi public et complet, servi par le backend (sans authentification).
 * C'est le seul point d'entrée qu'un assistant a besoin de connaître : tout le
 * reste (appairage, format du pack, envoi) y est décrit.
 */
export const PACK_AUTHOR_DOC_URL = `${API_BASE}/api/v1/agent/pack-author.md`;

/** Thème et niveau de l'exemple, repris tels quels dans l'aide de l'interface. */
export const SENTENCE_EXAMPLE_THEME = "les dinosaures";
export const SENTENCE_EXAMPLE_LEVEL = "CE1";

/**
 * Phrase à donner à l'assistant. Elle doit se suffire à elle-même : un
 * assistant qui n'a jamais entendu parler d'Explorito ne doit rien avoir à
 * deviner. D'où l'URL des instructions en premier — sans elle, un agent neuf
 * invente des adresses et tombe sur des 404 — puis le code, puis un exemple de
 * demande qui montre au parent la forme attendue.
 */
export function pairingSentence(code: string): string {
  return `Lis ${PACK_AUTHOR_DOC_URL} et suis ces instructions : connecte-toi avec le code ${formatPairingCode(code)}, puis écris-moi un pack sur ${SENTENCE_EXAMPLE_THEME} pour un ${SENTENCE_EXAMPLE_LEVEL}.`;
}
