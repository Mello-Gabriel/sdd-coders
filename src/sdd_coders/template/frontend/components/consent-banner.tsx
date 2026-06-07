"use client";

import {
  CONSENT_VERSION,
  type Consent,
  DEFAULT_CONSENT,
  getConsent,
  saveConsent,
} from "@/lib/consent/consent";
import { useEffect, useState } from "react";

/** LGPD cookie banner. Shows until a decision is stored; gates non-essential cookies. */
export function ConsentBanner() {
  const [visible, setVisible] = useState(false);
  const [customizing, setCustomizing] = useState(false);
  const [analytics, setAnalytics] = useState(false);
  const [marketing, setMarketing] = useState(false);

  useEffect(() => {
    setVisible(getConsent() === null);
  }, []);

  if (!visible) {
    return null;
  }

  const decide = (consent: Consent) => {
    saveConsent(consent);
    setVisible(false);
  };

  return (
    <dialog
      open
      aria-label="Consentimento de cookies"
      className="fixed inset-x-0 bottom-0 border-t bg-white p-4"
    >
      <p>Usamos cookies. Você controla as categorias não essenciais.</p>
      {customizing ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            decide({ necessary: true, analytics, marketing, version: CONSENT_VERSION });
          }}
        >
          <label>
            <input
              type="checkbox"
              checked={analytics}
              onChange={(event) => setAnalytics(event.target.checked)}
            />
            Analytics
          </label>
          <label>
            <input
              type="checkbox"
              checked={marketing}
              onChange={(event) => setMarketing(event.target.checked)}
            />
            Marketing
          </label>
          <button type="submit">Salvar preferências</button>
        </form>
      ) : (
        <div>
          <button
            type="button"
            onClick={() =>
              decide({
                necessary: true,
                analytics: true,
                marketing: true,
                version: CONSENT_VERSION,
              })
            }
          >
            Aceitar tudo
          </button>
          <button type="button" onClick={() => decide(DEFAULT_CONSENT)}>
            Recusar
          </button>
          <button type="button" onClick={() => setCustomizing(true)}>
            Personalizar
          </button>
        </div>
      )}
    </dialog>
  );
}
