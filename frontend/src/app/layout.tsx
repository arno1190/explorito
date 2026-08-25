import type { Metadata } from "next";
import { Nunito, Fredoka } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
});

// Fredoka : police d'affichage (titres, boutons, félicitations) — plus ronde et
// "bouncy" ; le corps de texte reste en Nunito pour la lisibilité.
const fredoka = Fredoka({
  variable: "--font-fredoka",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Explorito - Apprends en t'amusant !",
  description:
    "Application éducative ludique pour les enfants du CP au CM1. Apprends le français, les maths et bien plus !",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className={`${nunito.variable} ${fredoka.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
