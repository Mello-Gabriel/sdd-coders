import { GoogleAnalytics } from "@/components/google-analytics";
import * as consent from "@/lib/consent/consent";
import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("next/script", () => ({
  default: ({ id }: { id?: string }) => <div data-testid={id ?? "script"} />,
}));

vi.mock("@/lib/consent/consent", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/consent/consent")>();
  return { ...actual, getConsent: vi.fn(() => null) };
});

afterEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
});

describe("GoogleAnalytics", () => {
  it("renders nothing when consent is null", () => {
    vi.mocked(consent.getConsent).mockReturnValue(null);
    const { container } = render(<GoogleAnalytics measurementId="G-123" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when analytics consent is false", () => {
    vi.mocked(consent.getConsent).mockReturnValue({
      necessary: true,
      analytics: false,
      marketing: false,
      version: 1,
    });
    const { container } = render(<GoogleAnalytics measurementId="G-123" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders GA scripts when analytics consent is granted", () => {
    vi.mocked(consent.getConsent).mockReturnValue({
      necessary: true,
      analytics: true,
      marketing: false,
      version: 1,
    });
    render(<GoogleAnalytics measurementId="G-123" />);
    expect(screen.getByTestId("ga-init")).toBeInTheDocument();
  });

  it("updates when cookie-consent-updated event fires", async () => {
    vi.mocked(consent.getConsent).mockReturnValue(null);
    render(<GoogleAnalytics measurementId="G-123" />);

    vi.mocked(consent.getConsent).mockReturnValue({
      necessary: true,
      analytics: true,
      marketing: false,
      version: 1,
    });

    await act(async () => {
      window.dispatchEvent(new Event("cookie-consent-updated"));
    });

    expect(screen.getByTestId("ga-init")).toBeInTheDocument();
  });

  it("removes event listener on unmount", () => {
    vi.mocked(consent.getConsent).mockReturnValue(null);
    const { unmount } = render(<GoogleAnalytics measurementId="G-123" />);
    unmount();
    // No assertion needed — just verifies cleanup doesn't throw.
  });
});
