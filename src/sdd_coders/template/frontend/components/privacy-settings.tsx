"use client";

import { CONSENT_VERSION, type Consent, getConsent, saveConsent } from "@/lib/consent/consent";
import { type FormEvent, useEffect, useState } from "react";

export function PrivacySettings() {
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = getConsent();
    if (stored !== null) {
      setAnalytics(stored.analytics);
      setMarketing(stored.marketing);
    }
  }, []);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    const consent: Consent = { necessary: true, analytics, marketing, version: CONSENT_VERSION };
    saveConsent(consent);
    window.dispatchEvent(new Event("cookie-consent-updated"));
    setSaved(true);
  };

  return (
    <form onSubmit={onSubmit}>
      <fieldset>
        <legend className="text-sm font-medium text-foreground">Cookies não essenciais</legend>
        <label className="flex items-center gap-2 mt-2">
          <input
            type="checkbox"
            checked={analytics}
            onChange={(e) => {
              setAnalytics(e.target.checked);
              setSaved(false);
            }}
          />
          Analytics
        </label>
        <label className="flex items-center gap-2 mt-2">
          <input
            type="checkbox"
            checked={marketing}
            onChange={(e) => {
              setMarketing(e.target.checked);
              setSaved(false);
            }}
          />
          Marketing
        </label>
      </fieldset>
      {saved && <output>Preferências salvas.</output>}
      <button
        type="submit"
        className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
      >
        Salvar preferências
      </button>
    </form>
  );
}
