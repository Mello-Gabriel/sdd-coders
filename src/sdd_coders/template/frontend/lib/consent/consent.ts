/** LGPD cookie-consent state. Non-essential scripts must check isAllowed(). */

export type ConsentCategory = "necessary" | "analytics" | "marketing";

export interface Consent {
  necessary: true;
  analytics: boolean;
  marketing: boolean;
  version: number;
}

export const CONSENT_VERSION = 1;
const STORAGE_KEY = "cookie-consent";

export const DEFAULT_CONSENT: Consent = {
  necessary: true,
  analytics: false,
  marketing: false,
  version: CONSENT_VERSION,
};

/** Read the stored decision, or null if absent / outdated / corrupt. */
export function getConsent(): Consent | null {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (raw === null) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as Consent;
    return parsed.version === CONSENT_VERSION ? parsed : null;
  } catch {
    return null;
  }
}

export function saveConsent(consent: Consent): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
}

/** Whether a category may run. "necessary" is always allowed. */
export function isAllowed(category: ConsentCategory, consent: Consent | null): boolean {
  if (category === "necessary") {
    return true;
  }
  if (consent === null) {
    return false;
  }
  return consent[category];
}
