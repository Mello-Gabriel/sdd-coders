import { ConsentBanner } from "@/components/consent-banner";
import { getConsent } from "@/lib/consent/consent";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

afterEach(() => {
  window.localStorage.clear();
});

describe("ConsentBanner", () => {
  it("stores full consent when accepting all, then hides", async () => {
    const user = userEvent.setup();
    render(<ConsentBanner />);
    await screen.findByRole("dialog");

    await user.click(screen.getByRole("button", { name: "Aceitar tudo" }));

    expect(getConsent()?.analytics).toBe(true);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("stores default (essential-only) consent when rejecting", async () => {
    const user = userEvent.setup();
    render(<ConsentBanner />);
    await screen.findByRole("dialog");

    await user.click(screen.getByRole("button", { name: "Recusar" }));

    expect(getConsent()?.analytics).toBe(false);
  });

  it("lets the user opt in per category when customizing", async () => {
    const user = userEvent.setup();
    render(<ConsentBanner />);
    await screen.findByRole("dialog");

    await user.click(screen.getByRole("button", { name: "Personalizar" }));
    await user.click(screen.getByRole("checkbox", { name: /Analytics/ }));
    await user.click(screen.getByRole("checkbox", { name: /Marketing/ }));
    await user.click(screen.getByRole("button", { name: "Salvar preferências" }));

    const consent = getConsent();
    expect(consent?.analytics).toBe(true);
    expect(consent?.marketing).toBe(true);
  });

  it("stays hidden when a decision already exists", async () => {
    window.localStorage.setItem(
      "cookie-consent",
      JSON.stringify({ necessary: true, analytics: false, marketing: false, version: 1 }),
    );
    render(<ConsentBanner />);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });
});
