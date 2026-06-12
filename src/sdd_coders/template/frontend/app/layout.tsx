import { ConsentBanner } from "@/components/consent-banner";
import { GoogleAnalytics } from "@/components/google-analytics";
import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "App",
  description: "Production-grade fullstack starter",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
          <ConsentBanner />
          {process.env.NEXT_PUBLIC_GA_ID && (
            <GoogleAnalytics measurementId={process.env.NEXT_PUBLIC_GA_ID} />
          )}
        </ThemeProvider>
      </body>
    </html>
  );
}
