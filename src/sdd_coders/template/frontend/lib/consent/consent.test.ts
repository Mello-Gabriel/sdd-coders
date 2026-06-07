import {
  CONSENT_VERSION,
  type Consent,
  DEFAULT_CONSENT,
  getConsent,
  isAllowed,
  saveConsent,
} from "@/lib/consent/consent";
import { afterEach, describe, expect, it } from "vitest";

afterEach(() => {
  window.localStorage.clear();
});

describe("consent storage", () => {
  it("returns null when nothing is stored", () => {
    expect(getConsent()).toBeNull();
  });

  it("saves and reads a decision", () => {
    saveConsent({ ...DEFAULT_CONSENT, analytics: true });
    expect(getConsent()?.analytics).toBe(true);
  });

  it("ignores a stored decision from a different version", () => {
    const stale: Consent = { ...DEFAULT_CONSENT, version: CONSENT_VERSION + 1 };
    window.localStorage.setItem("cookie-consent", JSON.stringify(stale));
    expect(getConsent()).toBeNull();
  });

  it("returns null on corrupt json", () => {
    window.localStorage.setItem("cookie-consent", "{not json");
    expect(getConsent()).toBeNull();
  });
});

describe("isAllowed", () => {
  it("always allows necessary", () => {
    expect(isAllowed("necessary", null)).toBe(true);
  });

  it("blocks non-essential without consent", () => {
    expect(isAllowed("analytics", null)).toBe(false);
  });

  it("respects the stored decision", () => {
    expect(isAllowed("analytics", { ...DEFAULT_CONSENT, analytics: true })).toBe(true);
    expect(isAllowed("marketing", DEFAULT_CONSENT)).toBe(false);
  });
});
