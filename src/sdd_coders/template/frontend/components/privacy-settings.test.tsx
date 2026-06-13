import { PrivacySettings } from "@/components/privacy-settings";
import { api } from "@/lib/api/client";
import { getConsent } from "@/lib/consent/consent";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", () => ({ api: { saveConsentRecord: vi.fn() } }));

beforeEach(() => {
  vi.mocked(api.saveConsentRecord).mockResolvedValue({
    id: "1",
    version: 1,
    analytics: true,
    marketing: false,
    created_at: "2026-01-01T00:00:00Z",
  });
});

afterEach(() => {
  window.localStorage.clear();
  vi.clearAllMocks();
});

describe("PrivacySettings", () => {
  it("defaults to unchecked when no consent is stored", () => {
    render(<PrivacySettings />);
    expect(screen.getByRole("checkbox", { name: /Analytics/ })).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Marketing/ })).not.toBeChecked();
  });

  it("loads stored consent values on mount", () => {
    window.localStorage.setItem(
      "cookie-consent",
      JSON.stringify({ necessary: true, analytics: true, marketing: false, version: 1 }),
    );
    render(<PrivacySettings />);
    expect(screen.getByRole("checkbox", { name: /Analytics/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Marketing/ })).not.toBeChecked();
  });

  it("saves consent and shows success message on submit", async () => {
    const user = userEvent.setup();
    render(<PrivacySettings />);

    await user.click(screen.getByRole("checkbox", { name: /Analytics/ }));
    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));

    expect(getConsent()?.analytics).toBe(true);
    expect(screen.getByRole("status")).toHaveTextContent("Preferências salvas.");
  });

  it("dispatches cookie-consent-updated on save", async () => {
    const user = userEvent.setup();
    const handler = vi.fn();
    window.addEventListener("cookie-consent-updated", handler);
    render(<PrivacySettings />);

    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));

    expect(handler).toHaveBeenCalledTimes(1);
    window.removeEventListener("cookie-consent-updated", handler);
  });

  it("hides the success message after a checkbox change", async () => {
    const user = userEvent.setup();
    render(<PrivacySettings />);

    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));
    expect(screen.getByRole("status")).toBeInTheDocument();

    await user.click(screen.getByRole("checkbox", { name: /Marketing/ }));
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("records the consent server-side on save", async () => {
    const user = userEvent.setup();
    render(<PrivacySettings />);

    await user.click(screen.getByRole("checkbox", { name: /Analytics/ }));
    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));

    expect(api.saveConsentRecord).toHaveBeenCalledWith(true, false);
  });

  it("still saves locally when the server call fails (e.g. logged out)", async () => {
    vi.mocked(api.saveConsentRecord).mockRejectedValue(new Error("401"));
    const user = userEvent.setup();
    render(<PrivacySettings />);

    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));

    expect(getConsent()).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("Preferências salvas.");
  });
});
