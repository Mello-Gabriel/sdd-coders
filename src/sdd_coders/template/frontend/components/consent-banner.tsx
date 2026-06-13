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

  const primaryBtn =
    "rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90";
  const outlineBtn =
    "rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted";

  return (
    <dialog
      open
      aria-label="Consentimento de cookies"
      className="fixed inset-x-0 bottom-0 border-t border-border bg-card p-4 text-card-foreground shadow-lg"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          Usamos cookies. Você controla as categorias não essenciais.
        </p>
        {customizing ? (
          <form
            className="flex flex-wrap items-center gap-4"
            onSubmit={(event) => {
              event.preventDefault();
              decide({ necessary: true, analytics, marketing, version: CONSENT_VERSION });
            }}
          >
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={analytics}
                onChange={(event) => setAnalytics(event.target.checked)}
              />
              Analytics
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={marketing}
                onChange={(event) => setMarketing(event.target.checked)}
              />
              Marketing
            </label>
            <button type="submit" className={primaryBtn}>
              Salvar preferências
            </button>
          </form>
        ) : (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={primaryBtn}
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
            <button type="button" className={outlineBtn} onClick={() => decide(DEFAULT_CONSENT)}>
              Recusar
            </button>
            <button type="button" className={outlineBtn} onClick={() => setCustomizing(true)}>
              Personalizar
            </button>
          </div>
        )}
      </div>
    </dialog>
  );
}
