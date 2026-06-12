"use client";

import { type Consent, getConsent, isAllowed } from "@/lib/consent/consent";
import Script from "next/script";
import { useEffect, useState } from "react";

interface GoogleAnalyticsProps {
  measurementId: string;
}

/**
 * Loads the Google Analytics script only after the user grants analytics consent.
 * Listens for consent changes via the `cookie-consent-updated` custom event so the
 * script mounts / unmounts reactively without a page reload.
 */
export function GoogleAnalytics({ measurementId }: GoogleAnalyticsProps) {
  const [consent, setConsent] = useState<Consent | null>(null);

  useEffect(() => {
    setConsent(getConsent());

    const handler = () => setConsent(getConsent());
    window.addEventListener("cookie-consent-updated", handler);
    return () => window.removeEventListener("cookie-consent-updated", handler);
  }, []);

  if (!isAllowed("analytics", consent)) {
    return null;
  }

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
        strategy="afterInteractive"
      />
      <Script id="ga-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${measurementId}');
        `}
      </Script>
    </>
  );
}
