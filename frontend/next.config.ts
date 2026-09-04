import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Sortie autonome : image de production minimale (pas de node_modules complet),
  // ce qui réduit fortement la taille d'image et l'empreinte disque au build.
  output: "standalone",

  // Ces chemins ne sont pas inventés : ce sont ceux qu'un assistant « à froid »
  // a réellement essayés (puis 404) quand la phrase à copier ne nommait pas
  // encore l'URL des instructions. Les rabattre sur le tutoriel vaut toujours
  // mieux qu'une page d'erreur, pour l'agent comme pour le parent.
  async redirects() {
    return ["/device", "/code", "/connect", "/mcp", "/agent", "/api/agent"].map(
      (source) => ({
        source,
        destination: "/tutoriel/lecons-communautaires",
        permanent: true,
      })
    );
  },
};

export default nextConfig;
