import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Sortie autonome : image de production minimale (pas de node_modules complet),
  // ce qui réduit fortement la taille d'image et l'empreinte disque au build.
  output: "standalone",
};

export default nextConfig;
