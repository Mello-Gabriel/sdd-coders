import { ConsentBanner } from "@/components/consent-banner";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "App",
  description: "Production-grade fullstack starter",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        {children}
        <ConsentBanner />
      </body>
    </html>
  );
}
