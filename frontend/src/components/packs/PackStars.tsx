interface PackStarsProps {
  /** Étoiles gagnées. */
  earned: number;
  /** Étoiles possibles. */
  total: number;
  /**
   * Au-delà de ce nombre d'étoiles possibles, on passe en forme compacte
   * (« ⭐ 12/18 ») : un pack de 6 leçons afficherait sinon 18 glyphes, illisible
   * à 375 px.
   */
  max?: number;
  className?: string;
}

export function PackStars({
  earned,
  total,
  max = 5,
  className = "",
}: PackStarsProps) {
  if (total <= 0) return null;
  const label = `${earned} étoile${earned > 1 ? "s" : ""} sur ${total}`;

  if (total > max) {
    return (
      <span
        className={`font-bold text-fun-sun ${className}`}
        aria-label={label}
        title={label}
      >
        ⭐ {earned}/{total}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center ${className}`}
      aria-label={label}
      title={label}
    >
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          aria-hidden="true"
          className={i < earned ? "" : "opacity-25 grayscale"}
        >
          ⭐
        </span>
      ))}
    </span>
  );
}
